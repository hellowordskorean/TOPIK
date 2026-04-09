#!/usr/bin/env python3
"""
STEP 2 (대화편): 대화 상황 YouTube Shorts 영상 생성
- 웹툰 패널 + 말풍선 + TTS 합성
- Google Cloud TTS로 음성 생성
- FFmpeg으로 영상 합성
- 1080x1920 @ 30fps

필요 패키지:
pip install pillow google-cloud-texttospeech numpy python-dotenv

실행:
  python make_video_phrases.py --id 5
  python make_video_phrases.py --start 1 --end 10
  python make_video_phrases.py --id 5 --no-illust
"""

import json
import os
import sys
import io
import subprocess
import tempfile
import argparse
from pathlib import Path
from datetime import datetime

# Windows cp949 인코딩 문제 방지
if sys.stdout is not None and sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except AttributeError:
        pass
if sys.stderr is not None and sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except AttributeError:
        pass

# .env 로드
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

# ─── 경로 설정 ───────────────────────────────────────────────
_SCRIPT_DIR    = Path(__file__).parent
PHRASES_DB_PATH = Path("Z:/Hellowords/data/Conversation/phrases_db.json")
ILLUST_DIR     = _SCRIPT_DIR / "assets" / "phrase_illustrations"
DEFAULT_OUTPUT = _SCRIPT_DIR / "output" / "phrases"
LOGS_DIR       = _SCRIPT_DIR / "logs"

# ─── 영상 설정 ───────────────────────────────────────────────
W        = 1080
H        = 1920
FPS      = 30
HEADER_H = 120    # 헤더 (상황명 + 컨텍스트 자막)
PANEL_Y  = HEADER_H
PANEL_H  = 1060   # 패널 영역 높이
TRANS_Y  = PANEL_Y + PANEL_H  # 번역 스트립 시작 y (= 1180)
PAUSE_BETWEEN = 0.4   # my_line 끝 → response 시작 대기
PAUSE_END     = 0.4   # response 끝 → 다음 구 대기

# ─── 색상 팔레트 ─────────────────────────────────────────────
BG     = (248, 242, 234)   # warm cream
WHITE  = (255, 255, 255)
BLUE   = (50,  92,  200)   # accent (my line)
MAROON = (108,  60,  58)   # response
DARK   = (38,   32,  30)   # text
GRAY   = (108,  96,  90)
MUTED  = (158, 148, 142)
DIVIDER= (215, 205, 198)

CATEGORY_COLORS = {
    "여행":      (70,  130, 180),
    "식사":      (200, 100,  80),
    "쇼핑":      (180, 100, 180),
    "의료":      (80,  160, 120),
    "인사":      (220, 160,  60),
    "일상":      (100, 140, 200),
    "주거":      (140, 120, 100),
    "여가":      (80,  180, 160),
    "비즈니스":  (60,   80, 140),
    "K-Culture": (200,  80, 120),
}

# ─── 폰트 감지 ───────────────────────────────────────────────
def _detect_fonts() -> dict:
    candidates = {
        "korean_bold": [
            "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
            "C:/Windows/Fonts/NanumGothic-Bold.ttf",
            "C:/Windows/Fonts/malgunbd.ttf",
        ],
        "korean": [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "C:/Windows/Fonts/NanumGothic-Regular.ttf",
            "C:/Windows/Fonts/malgun.ttf",
        ],
        "english_bold": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ],
        "english": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ],
    }
    result = {}
    for key, paths in candidates.items():
        result[key] = next((p for p in paths if os.path.exists(p)), paths[0])
    return result

_fonts_map = _detect_fonts()
_font_cache: dict = {}

def get_font(key: str, size: int) -> ImageFont.FreeTypeFont:
    cache_key = (key, size)
    if cache_key not in _font_cache:
        path = _fonts_map.get(key, _fonts_map["english"])
        try:
            _font_cache[cache_key] = ImageFont.truetype(path, size)
        except Exception as e:
            print(f"  [WARN] 폰트 로드 실패: {key} @ {path} ({e})")
            _font_cache[cache_key] = ImageFont.load_default()
    return _font_cache[cache_key]


# ─── 하드웨어 인코더 감지 ────────────────────────────────────
_NVENC_AVAILABLE = None

def has_nvenc() -> bool:
    try:
        r = subprocess.run(
            ["ffmpeg", "-f", "lavfi", "-i", "nullsrc=s=64x64:d=0.1",
             "-c:v", "h264_nvenc", "-f", "null", "-"],
            capture_output=True, text=True, timeout=10,
        )
        return r.returncode == 0
    except Exception:
        return False

def get_video_encoder() -> list:
    global _NVENC_AVAILABLE
    if _NVENC_AVAILABLE is None:
        _NVENC_AVAILABLE = has_nvenc()
        print("  [GPU] h264_nvenc 인코딩 활성화" if _NVENC_AVAILABLE else "  [CPU] libx264 인코딩 사용")
    if _NVENC_AVAILABLE:
        return ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "22", "-b:v", "0"]
    else:
        return ["-c:v", "libx264", "-preset", "fast", "-crf", "22"]


# ─── ElevenLabs Voice ID 설정 ────────────────────────────────
# .env 에서 재정의 가능:
#   EL_VOICE_MY       = <내 대사 목소리 ID>     기본: Rachel (여성)
#   EL_VOICE_RESP     = <상대방 목소리 ID>       기본: Antoni (남성)
#   EL_VOICE_NARRATOR = <나레이터 목소리 ID>     기본: Callum (차분하고 친근한 남성)
# ElevenLabs 대시보드 → Voice Library 에서 원하는 목소리 ID 복사
_EL_VOICE_MY       = os.environ.get("EL_VOICE_MY",       "21m00Tcm4TlvDq8ikWAM")  # Rachel
_EL_VOICE_RESP     = os.environ.get("EL_VOICE_RESP",      "ErXwobaYiN019PkySvjV")  # Antoni
_EL_VOICE_NARRATOR = os.environ.get("EL_VOICE_NARRATOR",  "N2lVS1w4EtoT3dr4eOWO")  # Callum
_el_client: ElevenLabs | None = None

def _get_el_client() -> ElevenLabs:
    global _el_client
    if _el_client is None:
        api_key = os.environ.get("ELEVENLABS_API_KEY", "")
        if not api_key:
            raise RuntimeError(".env 에 ELEVENLABS_API_KEY 가 없습니다")
        _el_client = ElevenLabs(api_key=api_key)
    return _el_client


# ─── TTS (ElevenLabs Multilingual v2) ───────────────────────
def text_to_speech(text: str, voice_id: str, output_path: str,
                   stability: float = 0.45, similarity: float = 0.80,
                   style: float = 0.30):
    """ElevenLabs Multilingual v2 로 음성 파일 생성"""
    client = _get_el_client()
    audio_gen = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
        voice_settings=VoiceSettings(
            stability=stability,
            similarity_boost=similarity,
            style=style,
            use_speaker_boost=True,
        ),
    )
    with open(output_path, "wb") as f:
        for chunk in audio_gen:
            if chunk:
                f.write(chunk)


def get_audio_duration(path: str) -> float:
    """FFprobe로 오디오 길이 반환"""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except Exception:
        return 2.0


# ─── 그라디언트 배경 (일러스트 없을 때 fallback) ─────────────
def _make_gradient_bg(category: str) -> Image.Image:
    """카테고리 색상 기반 그라디언트 배경 (1080x1100)"""
    base_color = CATEGORY_COLORS.get(category, (100, 120, 180))
    img = Image.new("RGBA", (W, PANEL_H), (*base_color, 255))
    draw = ImageDraw.Draw(img)
    r, g, b = base_color
    for y in range(PANEL_H):
        alpha_factor = 1.0 - (y / 1100) * 0.4
        alpha_factor = 1.0 - (y / PANEL_H) * 0.4
        cr = int(r + (255 - r) * (1 - alpha_factor))
        cg = int(g + (255 - g) * (1 - alpha_factor))
        cb = int(b + (255 - b) * (1 - alpha_factor))
        draw.line([(0, y), (W, y)], fill=(cr, cg, cb, 255))
    return img


def _load_panel_image(sit_id: int, key: str, category: str,
                      use_gradient: bool) -> Image.Image:
    """패널 이미지 로드 (없으면 그라디언트 fallback)"""
    if not use_gradient:
        path = ILLUST_DIR / f"sit_{sit_id}" / f"{key}.png"
        if path.exists():
            try:
                img = Image.open(str(path)).convert("RGBA")
                # 9:16 비율 → 패널 영역으로 리사이즈 (center-crop)
                target_w, target_h = W, PANEL_H
                ratio = max(target_w / img.width, target_h / img.height)
                new_w = int(img.width  * ratio)
                new_h = int(img.height * ratio)
                img = img.resize((new_w, new_h), Image.LANCZOS)
                left = (new_w - target_w) // 2
                top  = (new_h - target_h) // 2
                img = img.crop((left, top, left + target_w, top + target_h))
                return img
            except Exception as e:
                print(f"  [WARN] 패널 이미지 로드 실패: {path} ({e})")
    return _make_gradient_bg(category)


# ─── 텍스트 줄바꿈 헬퍼 ─────────────────────────────────────
def _text_width(text: str, font: ImageFont.FreeTypeFont) -> int:
    """폰트 기준 텍스트 픽셀 너비 (draw 객체 불필요)"""
    try:
        return font.getbbox(text)[2]
    except Exception:
        return len(text) * getattr(font, "size", 20)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont,
               max_width: int, draw=None) -> list[str]:
    """텍스트를 max_width에 맞게 줄바꿈 (font.getbbox 기반)"""
    words = text.split()
    if not words:
        return [text]
    lines: list[str] = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if _text_width(test, font) > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines or [text]


# ─── 말풍선 그리기 (자동 높이) ──────────────────────────────
def _draw_speech_bubble(img: Image.Image, text: str,
                        x1: int, y1: int, x2: int,
                        tail_side: str,
                        text_color: tuple,
                        font_size: int = 36) -> Image.Image:
    """
    말풍선 그리기 — 텍스트 기반 높이 자동 계산, 넘침 없음.
    x1/y1/x2: 말풍선 왼쪽 상단 + 오른쪽 경계 (높이는 자동)
    tail_side: "left" | "right"
    """
    font   = get_font("korean_bold", font_size)
    pad_x  = 22
    pad_y  = 18
    line_h = int(font_size * 1.35)
    tail_h = 24

    # 텍스트 줄바꿈
    max_text_w = (x2 - x1) - pad_x * 2
    lines = _wrap_text(text, font, max_text_w)

    # 말풍선 높이 자동 계산
    bub_h = pad_y * 2 + len(lines) * line_h
    y2    = y1 + bub_h

    overlay  = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ov_draw  = ImageDraw.Draw(overlay)

    # 말풍선 본체
    ov_draw.rounded_rectangle(
        [x1, y1, x2, y2], radius=20,
        fill=(*WHITE, 248), outline=(*DARK, 255), width=3,
    )

    # 꼬리
    if tail_side == "right":
        pts = [(x2 - 70, y2), (x2 - 35, y2), (x2 - 15, y2 + tail_h)]
    else:
        pts = [(x1 + 35, y2), (x1 + 70, y2), (x1 + 15, y2 + tail_h)]
    ov_draw.polygon(pts, fill=(*WHITE, 248))
    ov_draw.line([pts[0], pts[2]], fill=(*DARK, 255), width=3)
    ov_draw.line([pts[1], pts[2]], fill=(*DARK, 255), width=3)

    # 텍스트 (왼쪽 정렬, 상단 기준)
    tx = x1 + pad_x
    ty = y1 + pad_y
    for line in lines:
        ov_draw.text((tx, ty), line, font=font,
                     fill=(*text_color, 255), anchor="lt")
        ty += line_h

    return Image.alpha_composite(img.convert("RGBA"), overlay)


# ─── 헤더 바 그리기 ──────────────────────────────────────────
def _draw_header(draw: ImageDraw.ImageDraw, situation: dict,
                 phrase_idx: int, total_phrases: int,
                 context_text: str = ""):
    """
    y=0-120: 헤더 바
      y=0-75:   상황 이름 + 진행 도트
      y=75-120: 컨텍스트 자막 (현재 상황 간략 설명)
    """
    cat        = situation.get("category", "여행")
    base_color = CATEGORY_COLORS.get(cat, (70, 130, 180))

    # ── 상단 바 (y=0-75) ──
    draw.rectangle([0, 0, W, 75], fill=(*base_color, 255))

    sit_ko  = situation.get("situation", "")
    sit_en  = situation.get("situation_en", "")
    font_ko = get_font("korean_bold", 32)
    font_en = get_font("english",     24)
    draw.text((44, 37), sit_ko, font=font_ko, fill=WHITE, anchor="lm")
    ko_w = draw.textbbox((0, 0), sit_ko, font=font_ko)[2]
    draw.text((44 + ko_w + 10, 37), f"({sit_en})",
              font=font_en, fill=(*WHITE, 180), anchor="lm")

    # 진행 도트
    dot_r, dot_gap = 6, 18
    total_dot_w = total_phrases * dot_r * 2 + (total_phrases - 1) * (dot_gap - dot_r * 2)
    dot_x = W - 44 - total_dot_w
    for i in range(total_phrases):
        cx = dot_x + i * dot_gap + dot_r
        fill = WHITE if i < phrase_idx else (*WHITE, 80)
        draw.ellipse([cx - dot_r, 37 - dot_r, cx + dot_r, 37 + dot_r], fill=fill)

    # ── 컨텍스트 자막 (y=75-120) ──
    r2 = tuple(max(0, c - 35) for c in base_color)
    draw.rectangle([0, 75, W, HEADER_H], fill=(*r2, 255))
    if context_text:
        font_ctx = get_font("korean", 26)
        draw.text((44, 97), context_text, font=font_ctx,
                  fill=(*WHITE, 210), anchor="lm")


# ─── 번역 스트립 그리기 ──────────────────────────────────────
def _draw_translation_strip(img: Image.Image, phrase: dict):
    """
    y=TRANS_Y(1180)-1920: 번역 스트립 — 항상 완전히 표시
    emoji 없이 순수 텍스트만 사용 (폰트 깨짐 방지)
    """
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, TRANS_Y, W, H], fill=(*BG, 255))
    draw.rectangle([0, TRANS_Y, W, TRANS_Y + 3], fill=(*DIVIDER, 255))

    # ── MY LINE 섹션 ──────────────────────────────────────────
    y = TRANS_Y + 18

    font_label  = get_font("korean_bold", 26)
    font_ko_big = get_font("korean_bold", 52)
    font_roman  = get_font("english",     26)
    font_en_med = get_font("english",     32)

    draw.text((44, y), "나 (Me)", font=font_label, fill=BLUE, anchor="lt")
    y += 38

    ko_text = phrase["my_line"]["ko"]
    lines = _wrap_text(ko_text, font_ko_big, W - 88)
    for line in lines:
        draw.text((44, y), line, font=font_ko_big, fill=BLUE, anchor="lt")
        y += 62

    roman = phrase["my_line"].get("romanization", "")
    if roman:
        r_lines = _wrap_text(roman, font_roman, W - 88)
        for line in r_lines:
            draw.text((44, y), line, font=font_roman, fill=MUTED, anchor="lt")
            y += 34

    en_text = phrase["my_line"]["en"]
    en_lines = _wrap_text(en_text, font_en_med, W - 88)
    for line in en_lines:
        draw.text((44, y), line, font=font_en_med, fill=DARK, anchor="lt")
        y += 40

    # ── 구분선 ───────────────────────────────────────────────
    y += 6
    draw.rectangle([44, y, W - 44, y + 1], fill=(*DIVIDER, 255))
    y += 14

    # ── RESPONSE 섹션 ─────────────────────────────────────────
    font_ko_med = get_font("korean_bold", 46)
    font_roman2 = get_font("english",     24)
    font_en2    = get_font("english",     30)

    draw.text((44, y), "상대방", font=font_label, fill=MAROON, anchor="lt")
    y += 38

    ko_text = phrase["response"]["ko"]
    r_ko_lines = _wrap_text(ko_text, font_ko_med, W - 88)
    for line in r_ko_lines:
        draw.text((44, y), line, font=font_ko_med, fill=MAROON, anchor="lt")
        y += 56

    roman = phrase["response"].get("romanization", "")
    if roman:
        r_lines = _wrap_text(roman, font_roman2, W - 88)
        for line in r_lines:
            draw.text((44, y), line, font=font_roman2, fill=MUTED, anchor="lt")
            y += 32

    en_text = phrase["response"]["en"]
    en_lines = _wrap_text(en_text, font_en2, W - 88)
    for line in en_lines:
        draw.text((44, y), line, font=font_en2, fill=DARK, anchor="lt")
        y += 38

    # ── Tip ───────────────────────────────────────────────────
    tip = phrase.get("tip", "")
    if tip:
        y += 6
        draw.rectangle([44, y, W - 44, y + 1], fill=(*DIVIDER, 255))
        y += 12
        font_tip = get_font("korean", 26)   # 한국어 포함 → korean 폰트
        tip_lines = _wrap_text(f"TIP: {tip}", font_tip, W - 88)
        for line in tip_lines:
            draw.text((44, y), line, font=font_tip, fill=MUTED, anchor="lt")
            y += 34


# ─── 프레임 렌더링 (정적 — 애니메이션 없음) ───────────────────
def render_phrase_frame(
    situation: dict,
    phrase: dict,
    phrase_idx: int,          # 1-based
    total_phrases: int,
    panel_img: Image.Image,
    show_response: bool,      # False=내 대사만, True=두 대사 모두
    context_text: str = "",   # 상황 설명 자막
) -> Image.Image:
    """
    정적 프레임 합성:
    - 슬라이드 애니메이션 없음 (패널 즉시 표시)
    - 번역 스트립 항상 완전 표시
    - show_response=False: 내 말풍선만
    - show_response=True:  내 말풍선 + 상대 말풍선
    - 말풍선 위치: 캐릭터 위쪽 (상단) — 캐릭터 가리지 않음
    """
    img  = Image.new("RGBA", (W, H), (*BG, 255))
    draw = ImageDraw.Draw(img)

    # ── 패널 이미지 (즉시 배치, 애니메이션 없음) ──────────────
    panel = panel_img.convert("RGBA")
    img.paste(panel, (0, PANEL_Y), panel.split()[3])

    # ── 헤더 ────────────────────────────────────────────────
    draw = ImageDraw.Draw(img)
    _draw_header(draw, situation, phrase_idx, total_phrases, context_text)

    # ── 말풍선: 패널 상단 배치, 자동 높이 ────────────────────────
    # MY 말풍선: 오른쪽 (x=560-1050, y_top=PANEL_Y+55)
    img = _draw_speech_bubble(
        img, phrase["my_line"]["ko"],
        x1=560, y1=PANEL_Y + 55, x2=1052,
        tail_side="right", text_color=BLUE, font_size=36,
    )
    # RESPONSE 말풍선: 왼쪽 (x=28-520, y_top=PANEL_Y+55 기준으로 동적 배치)
    if show_response:
        # MY 말풍선이 몇 줄인지 계산해서 아래에 배치
        font36    = get_font("korean_bold", 36)
        my_lines  = _wrap_text(phrase["my_line"]["ko"], font36, 1052 - 560 - 44)
        my_bub_h  = 36 + int(36 * 1.35) * len(my_lines) + 24 + 20  # pad+lines+tail+gap
        resp_y    = PANEL_Y + 55 + my_bub_h
        img = _draw_speech_bubble(
            img, phrase["response"]["ko"],
            x1=28, y1=resp_y, x2=520,
            tail_side="left", text_color=MAROON, font_size=36,
        )

    # ── 번역 스트립 (항상 완전히 표시) ───────────────────────
    _draw_translation_strip(img, phrase)

    return img.convert("RGB")


# ─── 인트로 카드 ─────────────────────────────────────────────
def render_intro_frame(situation: dict, panel_img: Image.Image,
                       t: float, duration: float) -> Image.Image:
    """
    인트로 카드 (3초):
    - 어두운 오버레이 위에 인트로 패널
    - 상황 한국어 이름 (크게, 굵게)
    - 영어 이름
    - 카테고리 배지
    """
    img = Image.new("RGBA", (W, H), (*BG, 255))

    # 패널을 Cover 방식으로 전체 배경에 배치 (비율 유지, 중앙 크롭)
    src_w, src_h = panel_img.size
    ratio  = max(W / src_w, H / src_h)
    new_w  = int(src_w * ratio)
    new_h  = int(src_h * ratio)
    bg     = panel_img.resize((new_w, new_h), Image.LANCZOS).convert("RGBA")
    left   = (new_w - W) // 2
    top    = (new_h - H) // 2
    bg     = bg.crop((left, top, left + W, top + H))
    img    = Image.alpha_composite(img, bg)

    # 어두운 반투명 오버레이
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rectangle([0, 0, W, H], fill=(10, 8, 8, 170))
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)

    # 페이드 인 (0~0.4초)
    fade_in = min(t / 0.4, 1.0)

    # 카테고리 배지
    cat     = situation.get("category", "여행")
    base_c  = CATEGORY_COLORS.get(cat, (70, 130, 180))
    font_cat = get_font("korean_bold", 34)
    cat_bb   = draw.textbbox((0, 0), cat, font=font_cat)
    cat_w    = cat_bb[2] - cat_bb[0] + 32
    cat_h    = cat_bb[3] - cat_bb[1] + 16
    cat_x    = (W - cat_w) // 2
    cat_y    = 700

    badge = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(badge).rounded_rectangle(
        [cat_x, cat_y, cat_x + cat_w, cat_y + cat_h],
        radius=cat_h // 2,
        fill=(*base_c, int(220 * fade_in)),
    )
    img = Image.alpha_composite(img, badge)
    draw = ImageDraw.Draw(img)
    draw.text(
        (W // 2, cat_y + cat_h // 2), cat,
        font=font_cat, fill=(*WHITE, int(255 * fade_in)), anchor="mm",
    )

    # 상황 한국어 이름 (큰 텍스트)
    sit_ko   = situation.get("situation", "")
    font_big = get_font("korean_bold", 100)
    draw.text(
        (W // 2, 850), sit_ko,
        font=font_big, fill=(*WHITE, int(255 * fade_in)), anchor="mm",
    )

    # 영어 이름
    sit_en    = situation.get("situation_en", "")
    font_en   = get_font("english", 52)
    draw.text(
        (W // 2, 980), sit_en,
        font=font_en, fill=(*WHITE, int(200 * fade_in)), anchor="mm",
    )

    # 구분선
    draw.rectangle(
        [W // 2 - 200, 1030, W // 2 + 200, 1032],
        fill=(*WHITE, int(120 * fade_in)),
    )

    # 문장 수 미리보기 (한/영 분리 렌더링 — 폰트 깨짐 방지)
    n_phrases = len(situation.get("phrases", []))
    font_sub_en = get_font("english",     34)
    font_sub_ko = get_font("korean_bold", 34)
    draw.text((W // 2, 1070), f"{n_phrases} phrases",
              font=font_sub_en, fill=(*WHITE, int(160 * fade_in)), anchor="mm")
    draw.text((W // 2, 1118), "오늘의 표현",
              font=font_sub_ko, fill=(*WHITE, int(140 * fade_in)), anchor="mm")

    return img.convert("RGB")


# ─── 아웃트로 카드 ───────────────────────────────────────────
def render_outro_frame(situation: dict, t: float) -> Image.Image:
    """
    아웃트로 카드 (2초):
    - 구독 유도 CTA
    """
    img = Image.new("RGBA", (W, H), (*BG, 255))
    draw = ImageDraw.Draw(img)

    # 배경 색상 (카테고리)
    cat      = situation.get("category", "여행")
    base_c   = CATEGORY_COLORS.get(cat, (70, 130, 180))
    draw.rectangle([0, 0, W, H], fill=(*base_c, 255))

    # 어두운 오버레이
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rectangle([0, 0, W, H], fill=(0, 0, 0, 100))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # 중앙 흰 카드
    card_x, card_y, card_w, card_h = 80, 600, 920, 500
    card_ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(card_ov).rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=40, fill=(*WHITE, 240),
    )
    img = Image.alpha_composite(img, card_ov)
    draw = ImageDraw.Draw(img)

    # 상황 이름
    sit_ko   = situation.get("situation", "")
    font_big = get_font("korean_bold", 72)
    draw.text(
        (W // 2, card_y + 140), sit_ko,
        font=font_big, fill=BLUE, anchor="mm",
    )

    # 구독 유도 텍스트
    font_cta = get_font("korean_bold", 40)
    draw.text(
        (W // 2, card_y + 260),
        "구독하면 매일 한국어 10문장!",
        font=font_cta, fill=DARK, anchor="mm",
    )

    font_sub = get_font("english", 32)
    draw.text(
        (W // 2, card_y + 340),
        "Like & Subscribe for daily Korean!",
        font=font_sub, fill=GRAY, anchor="mm",
    )

    # 하단 CTA 배지
    cta_badge = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(cta_badge).rounded_rectangle(
        [200, 1400, W - 200, 1480],
        radius=40, fill=(*BLUE, 230),
    )
    img = Image.alpha_composite(img, cta_badge)
    draw = ImageDraw.Draw(img)
    font_badge = get_font("korean_bold", 38)
    draw.text(
        (W // 2, 1440), "매일 새 표현 알림 받기 🔔",
        font=font_badge, fill=WHITE, anchor="mm",
    )

    return img.convert("RGB")


# ─── 로그 기록 ───────────────────────────────────────────────
def _log_video(situation: dict, output_path: str, file_size: int = 0):
    log_path = LOGS_DIR / "phrase_videos_log.json"
    try:
        log = []
        if log_path.exists():
            with open(log_path, encoding="utf-8") as f:
                log = json.load(f)
        entry = {
            "situation_id":  situation["id"],
            "situation":     situation.get("situation", ""),
            "situation_en":  situation.get("situation_en", ""),
            "category":      situation.get("category", ""),
            "output_path":   output_path,
            "file_size":     file_size,
            "generated_at":  datetime.now().isoformat(),
        }
        log = [x for x in log if x.get("situation_id") != situation["id"]]
        log.append(entry)
        log.sort(key=lambda x: x["situation_id"])
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ─── 메인 영상 생성 ──────────────────────────────────────────
def create_video(situation: dict, output_path: str, tmpdir: str,
                 use_gradient: bool = False):
    """단일 상황 영상 생성"""
    sit_id    = situation["id"]
    sit_ko    = situation.get("situation", "")
    category  = situation.get("category", "여행")
    phrases   = situation.get("phrases", [])

    print(f"\n>> 영상 생성: {sit_ko} (sit_{sit_id}, {len(phrases)}개 대화)")

    # ─── 1. TTS 음성 생성 ──────────────────────────────────────
    print("  1/4 TTS 음성 생성 중...")

    # 나레이션: 상황 설명 (영어 — 학습자 언어)
    sit_en = situation.get("situation_en", "")
    narration_text = f"Situation: {sit_en}"
    narration_path = os.path.join(tmpdir, "narration.mp3")
    text_to_speech(narration_text, _EL_VOICE_NARRATOR, narration_path,
                   stability=0.55, similarity=0.75, style=0.20)
    narration_dur = get_audio_duration(narration_path)
    intro_dur = max(3.0, narration_dur + 0.8)  # 나레이션 끝나고 0.8초 여유

    phrase_audios = []
    for i, phrase in enumerate(phrases):
        my_path   = os.path.join(tmpdir, f"ph{i}_my.mp3")
        resp_path = os.path.join(tmpdir, f"ph{i}_resp.mp3")
        text_to_speech(phrase["my_line"]["ko"],  _EL_VOICE_MY,   my_path)
        text_to_speech(phrase["response"]["ko"], _EL_VOICE_RESP, resp_path)
        phrase_audios.append((my_path, resp_path))
        print(f"    [{i+1}/{len(phrases)}] TTS 완료")

    # ─── 2. 오디오 기반 타임라인 계산 ────────────────────────
    print("  2/4 타임라인 계산 중...")
    # 세그먼트: (type, data, abs_start, duration)
    # type: "intro" | "phrase_my" | "phrase_both" | "outro"
    segments       = []
    audio_timeline = []   # (path, abs_start_sec)
    t = 0.0

    # 인트로 (나레이션 길이에 맞춰 동적)
    segments.append(("intro", situation, t, intro_dur))
    audio_timeline.append((narration_path, t + 0.3))  # 0.3초 후 나레이션 시작
    t += intro_dur

    for i, phrase in enumerate(phrases):
        my_path, resp_path = phrase_audios[i]
        my_dur   = get_audio_duration(my_path)
        resp_dur = get_audio_duration(resp_path)

        # Phase A: 내 대사만 (my_dur + pause)
        phase_a_dur = my_dur + PAUSE_BETWEEN
        audio_timeline.append((my_path, t))
        segments.append(("phrase_my",
                          (situation, phrase, i + 1, len(phrases)),
                          t, phase_a_dur))
        t += phase_a_dur

        # Phase B: 두 대사 모두 (resp_dur + end_pause)
        phase_b_dur = resp_dur + PAUSE_END
        audio_timeline.append((resp_path, t))
        segments.append(("phrase_both",
                          (situation, phrase, i + 1, len(phrases)),
                          t, phase_b_dur))
        t += phase_b_dur

    # 아웃트로 (2초)
    segments.append(("outro", situation, t, 2.0))
    t += 2.0

    total_duration = t
    total_frames   = int(total_duration * FPS)
    print(f"  총 길이: {total_duration:.1f}초 ({total_frames}프레임)")

    # ─── 3. 패널 이미지 로드 ───────────────────────────────────
    print("  2.5/4 패널 이미지 로드 중...")
    intro_panel   = _load_panel_image(sit_id, "intro",   category, use_gradient)
    phrase_panels = [
        _load_panel_image(sit_id, f"phrase_{p['id']}", category, use_gradient)
        for p in phrases
    ]

    # ─── 4. 프레임 렌더링 (세그먼트별 정적 프레임 재사용) ──────
    print("  3/4 프레임 렌더링 중...")
    frames_dir = os.path.join(tmpdir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    # 세그먼트별 정적 프레임 사전 렌더링
    seg_frame_map: dict[int, Image.Image] = {}
    for seg in segments:
        seg_type, seg_data, seg_start, seg_dur = seg
        ctx = situation.get("situation", "")  # 상황 자막
        if seg_type == "intro":
            f = render_intro_frame(seg_data, intro_panel, 0.5, 3.0)
        elif seg_type in ("phrase_my", "phrase_both"):
            sit_obj, phrase_obj, ph_idx, total_ph = seg_data
            panel = phrase_panels[ph_idx - 1] if ph_idx - 1 < len(phrase_panels) else intro_panel
            f = render_phrase_frame(
                sit_obj, phrase_obj, ph_idx, total_ph, panel,
                show_response=(seg_type == "phrase_both"),
                context_text=ctx,
            )
        else:  # outro
            f = render_outro_frame(seg_data, 0.5)
        seg_frame_map[id(seg)] = f

    # 프레임 파일 저장 (세그먼트 구간에 맞춰 반복)
    seg_idx = 0
    for frame_n in range(total_frames):
        t_cur = frame_n / FPS
        while seg_idx < len(segments) - 1 and t_cur >= segments[seg_idx + 1][2]:
            seg_idx += 1

        frame_path = os.path.join(frames_dir, f"frame_{frame_n:04d}.png")
        seg_frame_map[id(segments[seg_idx])].save(frame_path)

        if frame_n % (FPS * 5) == 0:
            print(f"    {frame_n}/{total_frames} 프레임 ({t_cur:.1f}s)")

    # ─── 5. FFmpeg 합성 ───────────────────────────────────────
    print("  4/4 FFmpeg 합성 중...")

    # silence 생성
    silence_path = os.path.join(tmpdir, "silence.mp3")
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", str(total_duration), "-q:a", "9", "-acodec", "libmp3lame",
        silence_path, "-y",
    ], capture_output=True)

    # 오디오 딜레이 필터 구성
    delay_filters = []
    input_args    = ["-i", silence_path]
    a_idx         = 0

    for ap, abs_start in audio_timeline:
        if os.path.exists(ap):
            input_args += ["-i", ap]
            delay_ms = int(abs_start * 1000)
            delay_filters.append(
                f"[{a_idx + 2}:a]adelay={delay_ms}|{delay_ms}[a{a_idx}]"
            )
            a_idx += 1

    if delay_filters:
        mix_input      = "".join(f"[a{i}]" for i in range(len(delay_filters)))
        filter_complex = (
            ";".join(delay_filters)
            + f";[1:a]{mix_input}amix=inputs={len(delay_filters) + 1}:normalize=0[aout]"
        )
        audio_map = ["-filter_complex", filter_complex, "-map", "[aout]"]
    else:
        audio_map = ["-map", "0:a"]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cmd = [
        "ffmpeg",
        "-framerate", str(FPS),
        "-i", os.path.join(frames_dir, "frame_%04d.png"),
    ] + input_args + audio_map + [
        "-map", "0:v",
        *get_video_encoder(),
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
        "-y",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FFmpeg 오류: {result.stderr[-800:]}")
        raise RuntimeError("FFmpeg 실패")

    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    print(f"  [OK] 영상 저장: {output_path} ({file_size // 1024}KB)")
    _log_video(situation, output_path, file_size)
    return output_path


# ─── 엔트리포인트 ────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="대화 상황 YouTube Shorts 영상 생성")
    parser.add_argument("--db", default=str(PHRASES_DB_PATH), help="phrases_db.json 경로")
    parser.add_argument("--id", type=int, default=None, help="단일 상황 ID")
    parser.add_argument("--start", type=int, default=None, help="시작 상황 ID")
    parser.add_argument("--end",   type=int, default=None, help="끝 상황 ID (포함)")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="출력 폴더")
    parser.add_argument("--no-illust", action="store_true",
                        help="일러스트 무시, 그라디언트 fallback 사용 (테스트용)")
    args = parser.parse_args()

    # DB 로드
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"오류: DB 파일 없음: {db_path}")
        return
    with open(db_path, encoding="utf-8") as f:
        db = json.load(f)
    print(f"DB 로드: {len(db)}개 상황")

    # 처리 대상 필터링
    if args.id is not None:
        targets = [s for s in db if s["id"] == args.id]
        if not targets:
            print(f"오류: 상황 ID {args.id}를 찾을 수 없습니다")
            return
    elif args.start is not None or args.end is not None:
        s = args.start if args.start is not None else 1
        e = args.end   if args.end   is not None else max(x["id"] for x in db)
        targets = [x for x in db if s <= x["id"] <= e]
    else:
        print("오류: --id 또는 --start/--end 를 지정하세요")
        parser.print_help()
        return

    print(f"처리 대상: {len(targets)}개 상황")
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, situation in enumerate(targets):
        sit_id = situation["id"]
        sit_ko = situation.get("situation", "")
        filename = f"phrases_sit{sit_id:03d}_{sit_ko}.mp4"
        output_path = str(output_dir / filename)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"[{i+1}/{len(targets)}] 스킵 (이미 존재): {filename}")
            continue

        print(f"[{i+1}/{len(targets)}] 생성 중: sit_{sit_id} {sit_ko}")
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                create_video(
                    situation, output_path, tmpdir,
                    use_gradient=args.no_illust,
                )
        except SystemExit:
            raise
        except Exception as e:
            print(f"  [오류] {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\n완료! 출력 폴더: {args.output}")


if __name__ == "__main__":
    main()
