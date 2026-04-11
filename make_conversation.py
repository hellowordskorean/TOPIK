#!/usr/bin/env python3
"""
회화 영상 생성기
- 테마별 실전 회화 구문을 다크 카드 스타일로 렌더링
- 단어 영상과 다른 스타일: 다크 배경, 대형 텍스트, 빠른 페이스
- 9:16 세로 (1080×1920) — Shorts/Reels + 일반 업로드 모두 호환

사용:
  python make_conversation.py --theme cafe --lang EN
  python make_conversation.py --theme kdrama --lang JP --format reels
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from google.cloud import texttospeech

# ─── 경로 설정 ────────────────────────────────────────────────
_APP_BASE = os.environ.get("APP_BASE", "/app")

def _app_path(rel: str) -> str:
    return os.path.join(_APP_BASE, rel)

# ─── 비디오 설정 ──────────────────────────────────────────────
W, H, FPS = 1080, 1920, 30

# ─── 색상 팔레트 (다크 모드) ──────────────────────────────────
DARK = {
    "bg":          (14,  17,  35),   # 거의 검정 (짙은 남색)
    "card":        (26,  31,  55),   # 카드 배경
    "card_border": (50,  58,  100),  # 카드 테두리
    "korean":      (255, 255, 255),  # 한국어 (흰색)
    "roman":       (130, 180, 255),  # 로마자 (하늘색)
    "translation": (200, 205, 220),  # 번역 (밝은 회색)
    "muted":       (100, 108, 140),  # 진행 점 비활성
    "header":      (180, 190, 210),  # 상단 테마명
}

# ─── 폰트 감지 ────────────────────────────────────────────────
def _detect_fonts():
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
        "bold": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ],
        "regular": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ],
        "jp": [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "C:/Windows/Fonts/NotoSansJP-Regular.otf",
            "C:/Windows/Fonts/msgothic.ttc",
            "C:/Windows/Fonts/malgun.ttf",
        ],
        "cn": [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/malgun.ttf",
        ],
    }
    result = {}
    for key, paths in candidates.items():
        result[key] = next((p for p in paths if os.path.exists(p)), paths[0])
    return result

_fonts_map = _detect_fonts()
_font_cache = {}

def get_font(key: str, size: int) -> ImageFont.FreeTypeFont:
    cache_key = (key, size)
    if cache_key not in _font_cache:
        path = _fonts_map.get(key, _fonts_map["regular"])
        try:
            _font_cache[cache_key] = ImageFont.truetype(path, size)
        except Exception:
            _font_cache[cache_key] = ImageFont.load_default()
    return _font_cache[cache_key]

def tl_font(lang: str, size: int) -> ImageFont.FreeTypeFont:
    """번역 언어에 맞는 폰트"""
    if lang == "JP":
        return get_font("jp", size)
    elif lang == "CN":
        return get_font("cn", size)
    return get_font("regular", size)

# ─── TTS ──────────────────────────────────────────────────────
_TTS_VOICES = {
    "ko": ("ko-KR", "ko-KR-Neural2-A", texttospeech.SsmlVoiceGender.FEMALE),
    "en": ("en-US", "en-US-Neural2-F", texttospeech.SsmlVoiceGender.FEMALE),
    "jp": ("ja-JP", "ja-JP-Neural2-B", texttospeech.SsmlVoiceGender.FEMALE),
    "cn": ("cmn-CN", "cmn-CN-Wavenet-A", texttospeech.SsmlVoiceGender.FEMALE),
    "vn": ("vi-VN", "vi-VN-Neural2-A", texttospeech.SsmlVoiceGender.FEMALE),
    "es": ("es-US", "es-US-Neural2-A", texttospeech.SsmlVoiceGender.FEMALE),
}

def _conv_tts_cache_path(cache_path_override: str, text: str, lang: str, slow: bool) -> str:
    """회화 TTS 캐시 경로 반환 (명시적 경로 우선, 없으면 misc MD5 폴백)"""
    if cache_path_override:
        return cache_path_override
    import hashlib
    key = hashlib.md5(f"gcp:{lang}:{slow}:{text}".encode()).hexdigest()
    d = _app_path("assets/tts_cache/misc")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{key}.mp3")

def text_to_speech(text: str, lang: str, output_path: str, slow: bool = False,
                   cache_path: str = None):
    """GCP TTS 음성 생성 (캐시 지원)"""
    cp = _conv_tts_cache_path(cache_path, text, lang, slow)
    if os.path.exists(cp) and os.path.getsize(cp) > 0:
        shutil.copy2(cp, output_path)
        return
    _sa = os.path.join(os.path.dirname(__file__), "secrets", "gcp_service_account.json")
    if os.path.exists(_sa) and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _sa
    client = texttospeech.TextToSpeechClient()
    lc, vname, gender = _TTS_VOICES.get(lang.lower(), _TTS_VOICES["en"])
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=lc, name=vname, ssml_gender=gender)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=0.85 if slow else 1.0,
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config)
    with open(output_path, "wb") as f:
        f.write(response.audio_content)
    # 캐시 저장
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        shutil.copy2(output_path, cp)

def get_audio_duration(path: str) -> float:
    if not os.path.exists(path):
        return 1.5
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 1.5

def write_progress(step: str, pct: int = 0, theme_id: str = "", lang: str = ""):
    data = {
        "status": "running" if pct < 100 else "idle",
        "step": step, "pct": pct,
        "word": theme_id, "meaning": lang,
        "updated_at": datetime.now().isoformat(),
    }
    try:
        os.makedirs(_app_path("logs"), exist_ok=True)
        with open(_app_path("logs/progress.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass

# ─── 유틸 ─────────────────────────────────────────────────────
def hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def draw_text_center(draw, x, y, text, font, color, max_width=None):
    """중앙 정렬 텍스트. max_width 초과 시 자동 줄바꿈."""
    if not text:
        return
    if max_width and draw.textbbox((0, 0), text, font=font)[2] > max_width:
        # 공백 기준으로 2줄 분리
        words = text.split()
        mid = max(1, len(words) // 2)
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    else:
        lines = [text]
    line_h = draw.textbbox((0, 0), "Ag", font=font)[3] + 8
    total_h = line_h * len(lines)
    cur_y = y - total_h // 2
    for line in lines:
        draw.text((x, cur_y + line_h // 2), line, font=font, fill=color, anchor="mm")
        cur_y += line_h

def draw_rounded_rect(img: Image.Image, x1, y1, x2, y2, radius, fill, alpha=255):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle([x1, y1, x2, y2], radius=radius,
                                          fill=(*fill, alpha))
    img.paste(ov, mask=ov.split()[3])

# ─── 프레임 렌더링 ────────────────────────────────────────────
def render_dialogue_frame(
    phrase: dict,
    phrase_idx: int,
    total: int,
    theme: dict,
    lang: str,
    progress: float = 1.0,
) -> Image.Image:
    """대화 쌍 카드: my_line(상단) + response(하단) 한 화면에 표시"""
    img = Image.new("RGBA", (W, H), (*DARK["bg"], 255))
    draw = ImageDraw.Draw(img)
    p = progress
    cx = W // 2
    theme_rgb = hex_to_rgb(theme.get("color", "#4F8EF7"))
    resp_rgb   = (80, 120, 255)   # 응답자 강조색 (파란 계열)

    # ── 배경 그라디언트 ─────────────────────────────────────
    for i in range(H):
        t = i / H
        gc = lerp_color(DARK["bg"], lerp_color(DARK["bg"], theme_rgb, 0.08), t * 0.6)
        draw.line([(0, i), (W, i)], fill=(*gc, 255))

    # ── 상단 헤더 ────────────────────────────────────────────
    header_y = 90
    emoji = theme.get("emoji", "💬")
    title  = theme.get("title", {}).get(lang.lower(),
             theme.get("title", {}).get("ko", ""))
    draw.text((cx, header_y), f"{emoji}  {title}",
              font=get_font("korean_bold", 36),
              fill=(*DARK["header"], int(180 * p)), anchor="mm")
    draw.rectangle([cx - 200, header_y + 34, cx + 200, header_y + 35],
                   fill=(*theme_rgb, int(100 * p)))

    # 번호 배지
    bs = 54
    bx, by = W - 64, header_y - bs // 2
    draw_rounded_rect(img, bx, by, bx + bs, by + bs,
                      radius=bs // 2, fill=theme_rgb, alpha=int(200 * p))
    draw = ImageDraw.Draw(img)
    draw.text((bx + bs // 2, by + bs // 2), str(phrase_idx + 1),
              font=get_font("bold", 26),
              fill=(255, 255, 255, int(255 * p)), anchor="mm")

    sent_key = lang.lower()

    # ── 학습자 버블 (상단) ────────────────────────────────────
    B_X, B_W = 40, W - 80
    b1_y, b1_h = 160, 360
    draw_rounded_rect(img, B_X, b1_y, B_X + B_W, b1_y + b1_h,
                      radius=32, fill=DARK["card"], alpha=int(245 * p))
    # 라벨
    draw = ImageDraw.Draw(img)
    draw.text((B_X + 22, b1_y + 24), "🗣 나",
              font=get_font("korean_bold", 26),
              fill=(*theme_rgb, int(220 * p)), anchor="lm")
    # 한국어
    my_ko = phrase.get("my_ko", "")
    fk = 68 if len(my_ko) <= 14 else (54 if len(my_ko) <= 22 else 42)
    draw_text_center(draw, cx, b1_y + 130, my_ko,
                     get_font("korean_bold", fk),
                     (*DARK["korean"], int(255 * p)), max_width=B_W - 40)
    # 로마자
    my_roman = phrase.get("my_roman", "")
    if my_roman:
        draw.text((cx, b1_y + 225), my_roman,
                  font=get_font("regular", 26),
                  fill=(*DARK["roman"], int(170 * p)), anchor="mm")
    # 번역
    my_tl = phrase.get(f"my_{sent_key}", phrase.get("my_en", ""))
    draw_text_center(draw, cx, b1_y + 305, my_tl,
                     tl_font(lang, 34),
                     (*DARK["translation"], int(200 * p)), max_width=B_W - 40)

    # ── 응답자 버블 (하단) ────────────────────────────────────
    b2_y, b2_h = 560, 360
    draw_rounded_rect(img, B_X, b2_y, B_X + B_W, b2_y + b2_h,
                      radius=32, fill=(22, 28, 54), alpha=int(245 * p))
    draw = ImageDraw.Draw(img)
    # 왼쪽 강조선
    draw.rectangle([B_X, b2_y + 18, B_X + 5, b2_y + b2_h - 18],
                   fill=(*resp_rgb, int(200 * p)))
    draw.text((B_X + 22, b2_y + 24), "👤 상대방",
              font=get_font("korean_bold", 26),
              fill=(*resp_rgb, int(220 * p)), anchor="lm")
    # 한국어
    resp_ko = phrase.get("resp_ko", "")
    fk2 = 68 if len(resp_ko) <= 14 else (54 if len(resp_ko) <= 22 else 42)
    draw_text_center(draw, cx, b2_y + 130, resp_ko,
                     get_font("korean_bold", fk2),
                     (*DARK["korean"], int(255 * p)), max_width=B_W - 40)
    # 로마자
    resp_roman = phrase.get("resp_roman", "")
    if resp_roman:
        draw.text((cx, b2_y + 225), resp_roman,
                  font=get_font("regular", 26),
                  fill=(*DARK["roman"], int(170 * p)), anchor="mm")
    # 번역
    resp_tl = phrase.get(f"resp_{sent_key}", phrase.get("resp_en", ""))
    draw_text_center(draw, cx, b2_y + 305, resp_tl,
                     tl_font(lang, 34),
                     (*DARK["translation"], int(200 * p)), max_width=B_W - 40)

    # ── 진행 점 ──────────────────────────────────────────────
    dot_y = H - 95
    dot_r, dot_gap = 9, 28
    total_dot_w = total * dot_r * 2 + (total - 1) * (dot_gap - dot_r * 2)
    dot_x = cx - total_dot_w // 2
    for i in range(total):
        is_active = i == phrase_idx
        color = theme_rgb if is_active else DARK["muted"]
        alpha = int(255 * p) if is_active else int(100 * p)
        r = dot_r + 2 if is_active else dot_r
        draw.ellipse([dot_x - r, dot_y - r, dot_x + r, dot_y + r],
                     fill=(*color, alpha))
        dot_x += dot_gap

    return img.convert("RGB")


# 하위 호환용 alias
render_phrase_frame = render_dialogue_frame


def render_intro_frame(theme: dict, lang: str, progress: float = 1.0) -> Image.Image:
    """인트로 프레임: 테마 제목 + 오늘 배울 구문 수"""
    img = Image.new("RGBA", (W, H), (*DARK["bg"], 255))
    draw = ImageDraw.Draw(img)
    p = progress
    cx = W // 2

    theme_rgb = hex_to_rgb(theme.get("color", "#4F8EF7"))

    # 배경 그라디언트
    for i in range(H):
        t = i / H
        gc = lerp_color(DARK["bg"], lerp_color(DARK["bg"], theme_rgb, 0.15), t * 0.8)
        draw.line([(0, i), (W, i)], fill=(*gc, 255))

    draw = ImageDraw.Draw(img)

    # 이모지 크게
    emoji = theme.get("emoji", "💬")
    font_emoji = get_font("korean_bold", 140)
    draw.text((cx, H // 2 - 220), emoji,
              font=font_emoji, fill=(255, 255, 255, int(255 * p)), anchor="mm")

    # 테마 제목
    title_ko = theme.get("title", {}).get("ko", "")
    font_title = get_font("korean_bold", 72)
    draw.text((cx, H // 2 + 0), title_ko,
              font=font_title, fill=(255, 255, 255, int(255 * p)), anchor="mm")

    # 부제: 오늘의 회화
    sub_text = "오늘의 한국어 회화"
    draw.text((cx, H // 2 + 100), sub_text,
              font=get_font("korean", 42),
              fill=(*DARK["header"], int(180 * p)), anchor="mm")

    # 테마 색상 언더라인
    draw.rectangle([cx - 160, H // 2 + 130, cx + 160, H // 2 + 133],
                   fill=(*theme_rgb, int(200 * p)))

    # 채널 브랜딩
    draw.text((cx, H - 130), "Hellowords · 매일 한국어",
              font=get_font("regular", 34),
              fill=(*DARK["muted"], int(140 * p)), anchor="mm")

    return img.convert("RGB")


def render_outro_frame(theme: dict, phrases: list, lang: str, progress: float = 1.0) -> Image.Image:
    """아웃트로: 오늘 배운 구문 목록 + 구독 유도"""
    img = Image.new("RGBA", (W, H), (*DARK["bg"], 255))
    draw = ImageDraw.Draw(img)
    p = progress
    cx = W // 2
    theme_rgb = hex_to_rgb(theme.get("color", "#4F8EF7"))

    # 배경
    for i in range(H):
        t = i / H
        gc = lerp_color(DARK["bg"], lerp_color(DARK["bg"], theme_rgb, 0.12), t)
        draw.line([(0, i), (W, i)], fill=(*gc, 255))
    draw = ImageDraw.Draw(img)

    # 제목
    draw.text((cx, 130), "오늘 배운 표현",
              font=get_font("korean_bold", 58),
              fill=(255, 255, 255, int(255 * p)), anchor="mm")
    draw.rectangle([cx - 120, 165, cx + 120, 168],
                   fill=(*theme_rgb, int(220 * p)))

    # 구문 목록
    font_ko = get_font("korean_bold", 44)
    font_tl = tl_font(lang, 32)
    sent_key = lang.lower()

    item_y = 240
    for i, ph in enumerate(phrases[:7]):
        ko = ph.get("my_ko", ph.get("ko", ""))
        tl = ph.get(f"my_{sent_key}", ph.get("my_en", ph.get(sent_key, ph.get("en", ""))))
        # 아이템 배경
        draw_rounded_rect(img, 50, item_y, W - 50, item_y + 110,
                          radius=18, fill=DARK["card"], alpha=int(200 * p))
        draw = ImageDraw.Draw(img)
        # 번호
        draw.text((90, item_y + 55), str(i + 1),
                  font=get_font("bold", 28),
                  fill=(*theme_rgb, int(200 * p)), anchor="mm")
        # 한국어
        draw.text((120, item_y + 30), ko,
                  font=font_ko, fill=(255, 255, 255, int(240 * p)), anchor="lm")
        # 번역
        draw.text((120, item_y + 80), tl,
                  font=font_tl, fill=(*DARK["translation"], int(180 * p)), anchor="lm")
        item_y += 122

    # 구독 유도 CTA
    cta_y = item_y + 30
    draw_rounded_rect(img, 60, cta_y, W - 60, cta_y + 110,
                      radius=24, fill=theme_rgb, alpha=int(220 * p))
    draw = ImageDraw.Draw(img)
    draw.text((cx, cta_y + 55), "🔔 구독하고 매일 한국어 공부!",
              font=get_font("korean_bold", 38),
              fill=(255, 255, 255, int(255 * p)), anchor="mm")

    return img.convert("RGB")


# ─── 영상 생성 메인 ───────────────────────────────────────────
def _make_silence(path: str, dur: float = 0.5):
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", str(dur), "-q:a", "9", "-acodec", "libmp3lame",
        path, "-y"
    ], capture_output=True)


def create_conversation_video(theme: dict, phrases: list, output_path: str,
                               lang: str, tmpdir: str):
    sent_key = lang.lower()
    total = len(phrases)
    lang_lower = lang.lower()

    write_progress("1/4 TTS 음성 생성 중...", pct=5, theme_id=theme["id"], lang=lang)
    print(f"  1/4 TTS 음성 생성 중... ({total}개 구문, 쌍당 4개 TTS)")

    # ── 회화 TTS 캐시 폴더 ──
    _theme_id = theme.get("id", 0)
    _cache_dir = _app_path(f"assets/tts_cache/회화/ep{_theme_id:04d}/{lang_lower}")
    os.makedirs(_cache_dir, exist_ok=True)
    def _cp(name: str) -> str:
        return os.path.join(_cache_dir, name)

    # TTS 생성 — 쌍당 4개: my_ko / my_tl / resp_ko / resp_tl
    phrase_audios = []   # list of (my_ko_path, my_tl_path, resp_ko_path, resp_tl_path)
    for i, ph in enumerate(phrases):
        my_ko_path   = os.path.join(tmpdir, f"my_ko_{i}.mp3")
        my_tl_path   = os.path.join(tmpdir, f"my_tl_{i}.mp3")
        resp_ko_path = os.path.join(tmpdir, f"resp_ko_{i}.mp3")
        resp_tl_path = os.path.join(tmpdir, f"resp_tl_{i}.mp3")

        my_ko = ph.get("my_ko", "")
        if my_ko:
            text_to_speech(my_ko, "ko", my_ko_path, slow=True,
                           cache_path=_cp(f"p{i+1:02d}_my_ko.mp3"))
        else:
            _make_silence(my_ko_path)

        my_tl = ph.get(f"my_{sent_key}", ph.get("my_en", ""))
        if my_tl:
            text_to_speech(my_tl, lang_lower, my_tl_path,
                           cache_path=_cp(f"p{i+1:02d}_my_{lang_lower}.mp3"))
        else:
            _make_silence(my_tl_path)

        resp_ko = ph.get("resp_ko", "")
        if resp_ko:
            text_to_speech(resp_ko, "ko", resp_ko_path, slow=True,
                           cache_path=_cp(f"p{i+1:02d}_resp_ko.mp3"))
        else:
            _make_silence(resp_ko_path, 0.3)

        resp_tl = ph.get(f"resp_{sent_key}", ph.get("resp_en", ""))
        if resp_tl:
            text_to_speech(resp_tl, lang_lower, resp_tl_path,
                           cache_path=_cp(f"p{i+1:02d}_resp_{lang_lower}.mp3"))
        else:
            _make_silence(resp_tl_path, 0.3)

        phrase_audios.append((my_ko_path, my_tl_path, resp_ko_path, resp_tl_path))

    write_progress("2/4 타임라인 계산 중...", pct=20, theme_id=theme["id"], lang=lang)

    # 구간 타이밍 계산
    INTRO_DUR   = 2.0
    OUTRO_DUR   = 3.5
    PRE_GAP     = 0.4   # 카드 시작 → 첫 TTS 시작
    KO_TL_GAP   = 0.5   # 한국어 → 번역 TTS 간격
    PAIR_GAP    = 0.6   # my_line 번역 끝 → resp 한국어 시작
    POST_GAP    = 0.8   # 마지막 TTS → 다음 카드
    FADE_FRAMES = 9     # 페이드 프레임 수 (0.3s)

    phrase_durations = []
    audio_timeline = []   # (path, abs_start_time)
    t = INTRO_DUR

    for i, (my_ko_p, my_tl_p, resp_ko_p, resp_tl_p) in enumerate(phrase_audios):
        my_ko_dur   = get_audio_duration(my_ko_p)
        my_tl_dur   = get_audio_duration(my_tl_p)
        resp_ko_dur = get_audio_duration(resp_ko_p)
        resp_tl_dur = get_audio_duration(resp_tl_p)

        phrase_dur = (PRE_GAP + my_ko_dur + KO_TL_GAP + my_tl_dur
                      + PAIR_GAP + resp_ko_dur + KO_TL_GAP + resp_tl_dur + POST_GAP)
        phrase_durations.append(phrase_dur)

        t_my_ko   = t + PRE_GAP
        t_my_tl   = t_my_ko + my_ko_dur + KO_TL_GAP
        t_resp_ko = t_my_tl + my_tl_dur + PAIR_GAP
        t_resp_tl = t_resp_ko + resp_ko_dur + KO_TL_GAP

        audio_timeline.append((my_ko_p,   t_my_ko))
        audio_timeline.append((my_tl_p,   t_my_tl))
        audio_timeline.append((resp_ko_p, t_resp_ko))
        audio_timeline.append((resp_tl_p, t_resp_tl))
        t += phrase_dur

    total_duration = INTRO_DUR + sum(phrase_durations) + OUTRO_DUR

    write_progress("3/4 프레임 렌더링 중...", pct=30, theme_id=theme["id"], lang=lang)
    print(f"  3/4 프레임 렌더링 중... (총 {total_duration:.1f}초)")

    # 프레임 렌더링
    frames_dir = os.path.join(tmpdir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    total_frames = int(total_duration * FPS) + 1
    frame_n = 0

    def save_frame(img_rgb):
        nonlocal frame_n
        img_rgb.save(os.path.join(frames_dir, f"frame_{frame_n:06d}.png"))
        frame_n += 1

    # 인트로 프레임
    intro_frames = int(INTRO_DUR * FPS)
    for f in range(intro_frames):
        prog = min(1.0, f / max(1, FADE_FRAMES))
        save_frame(render_intro_frame(theme, lang, progress=prog))

    # 구문 프레임
    for i, ph in enumerate(phrases):
        dur = phrase_durations[i]
        ph_frames = int(dur * FPS)
        for f in range(ph_frames):
            pct = 30 + int(60 * (i * ph_frames + f) / max(1, total * ph_frames))
            if f % 30 == 0:
                write_progress(
                    f"3/4 프레임 렌더링 중... ({i+1}/{total})",
                    pct=pct, theme_id=theme["id"], lang=lang)
            prog = min(1.0, f / max(1, FADE_FRAMES))
            save_frame(render_phrase_frame(ph, i, total, theme, lang, progress=prog))

    # 아웃트로 프레임
    outro_frames = int(OUTRO_DUR * FPS)
    for f in range(outro_frames):
        prog = min(1.0, f / max(1, FADE_FRAMES))
        save_frame(render_outro_frame(theme, phrases, lang, progress=prog))

    write_progress("4/4 FFmpeg 합성 중...", pct=88, theme_id=theme["id"], lang=lang)
    print(f"  4/4 FFmpeg 합성 중...")

    # 오디오 합성
    silence_path = os.path.join(tmpdir, "silence.mp3")
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", str(total_duration), "-q:a", "9", "-acodec", "libmp3lame",
        silence_path, "-y"
    ], capture_output=True)

    input_args = ["-i", silence_path]
    delay_filters = []
    a_idx = 0
    for ap, abs_start in audio_timeline:
        if os.path.exists(ap):
            input_args += ["-i", ap]
            delay_ms = int(abs_start * 1000)
            delay_filters.append(f"[{a_idx+2}:a]adelay={delay_ms}|{delay_ms}[a{a_idx}]")
            a_idx += 1

    mix_inputs = "".join(f"[a{j}]" for j in range(a_idx))

    # 배경 음악 (있으면)
    music_dir = _app_path("assets/music")
    music_src = None
    if os.path.isdir(music_dir):
        music_files = sorted(f for f in os.listdir(music_dir) if f.endswith((".mp3", ".wav")))
        if music_files:
            music_src = os.path.join(music_dir, music_files[0])
    has_music = bool(music_src and os.path.exists(music_src))
    if has_music:
        input_args += ["-i", music_src]
    music_idx = a_idx + 2  # 0=frames, 1=silence, 2..a_idx+1=TTS, a_idx+2=music

    # filter_complex & audio_map 결정
    if a_idx > 0 and has_music:
        # TTS 믹스 → 배경음악 합성
        fc = (
            ";".join(delay_filters) + ";" +
            f"{mix_inputs}amix=inputs={a_idx}:normalize=0:duration=longest[voice];"
            f"[voice][{music_idx}:a]amix=inputs=2:weights=1 0.08:normalize=0[aout]"
        )
        filter_complex = fc
        audio_map = ["-map", "[aout]"]
    elif a_idx > 0:
        # TTS만 믹스 (배경음악 없음)
        filter_complex = (
            ";".join(delay_filters) + ";" +
            f"{mix_inputs}amix=inputs={a_idx}:normalize=0:duration=longest[aout]"
        )
        audio_map = ["-map", "[aout]"]
    elif has_music:
        # TTS 없음, 배경음악만
        filter_complex = f"[{music_idx}:a]avolume=0.08[aout]"
        audio_map = ["-map", "[aout]"]
    else:
        # TTS도 음악도 없음 → silence 직접 매핑 (filter_complex 불필요)
        filter_complex = None
        audio_map = ["-map", "1:a"]

    # 인코더: libx264 (NAS Docker는 GPU 없음)
    enc_args = ["-c:v", "libx264", "-preset", "fast", "-crf", "22"]

    cmd = [
        "ffmpeg", "-y",
        "-start_number", "0",
        "-framerate", str(FPS),
        "-i", os.path.join(frames_dir, "frame_%06d.png"),
    ] + input_args
    if filter_complex:
        cmd += ["-filter_complex", filter_complex]
    cmd += [
        "-map", "0:v",
    ] + audio_map + enc_args + [
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]

    print(f"  FFmpeg: {len(cmd)} args, a_idx={a_idx}, music={has_music}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        print(f"  FFmpeg 오류 (returncode={result.returncode}):")
        print(f"  STDERR: {result.stderr[-1000:]}")
        raise RuntimeError(f"FFmpeg 실패 (rc={result.returncode})")

    print(f"  [OK] 저장: {output_path}")

    # 로그 저장
    log_path = _app_path("logs/conversations_log.json")
    try:
        log = []
        if os.path.exists(log_path):
            with open(log_path, encoding="utf-8") as f:
                log = json.load(f)
        log.append({
            "theme_id": theme["id"],
            "lang": lang,
            "output_path": output_path,
            "file_size": os.path.getsize(output_path) if os.path.exists(output_path) else 0,
            "generated_at": datetime.now().isoformat(),
        })
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    write_progress("완료", pct=100, theme_id=theme["id"], lang=lang)


# ─── 엔트리포인트 ─────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="한국어 회화 영상 생성")
    parser.add_argument("--db",     default=None, help="conversations_db.json 경로 (없으면 자동)")
    parser.add_argument("--theme",  required=True, help="테마 ID (예: cafe, greetings)")
    parser.add_argument("--lang",   default="EN",
                        choices=["EN", "JP", "CN", "VN", "ES"], help="번역 언어")
    parser.add_argument("--output", default="output/", help="출력 루트 폴더")
    args = parser.parse_args()

    # DB 로드
    db_path = args.db or os.path.join(os.path.dirname(__file__), "phrases_db.json")
    with open(db_path, encoding="utf-8") as f:
        db = json.load(f)

    # 리스트 형식(phrases_db.json) → 내부 형식으로 변환 (title/emoji/color 보정)
    if isinstance(db, list):
        db = {"themes": [
            {**item, "title": {
                "ko": item.get("situation", ""), "KR": item.get("situation", ""),
                "en": item.get("situation_en", ""), "EN": item.get("situation_en", ""),
            }}
            for item in db
        ]}

    themes = db.get("themes", [])
    # theme_id는 문자열/정수 모두 허용
    theme = next((t for t in themes if str(t["id"]) == str(args.theme)), None)
    if not theme:
        ids = [t["id"] for t in themes]
        print(f"테마 '{args.theme}'를 찾을 수 없습니다. 가능한 테마: {ids}")
        sys.exit(1)

    raw_phrases = theme["phrases"]

    # my_line/response 중첩 구조 → 대화 쌍 형식으로 변환
    sent_key_flat = args.lang.lower()
    pair_phrases = []
    for ph in raw_phrases:
        if "my_line" in ph or "response" in ph:
            my   = ph.get("my_line", {}) or {}
            resp = ph.get("response", {}) or {}
            pair_phrases.append({
                "my_ko":              my.get("ko", ""),
                "my_roman":           my.get("romanization", ""),
                "my_en":              my.get("en", ""),
                f"my_{sent_key_flat}": my.get(sent_key_flat, my.get("en", "")),
                "resp_ko":              resp.get("ko", ""),
                "resp_roman":           resp.get("romanization", ""),
                "resp_en":              resp.get("en", ""),
                f"resp_{sent_key_flat}": resp.get(sent_key_flat, resp.get("en", "")),
                "tip": ph.get("tip", ""),
            })
        else:
            # 레거시 평탄 형식 — my_line만 있는 쌍으로 래핑
            pair_phrases.append({
                "my_ko":              ph.get("ko", ""),
                "my_roman":           ph.get("roman", ph.get("romanization", "")),
                "my_en":              ph.get("en", ""),
                f"my_{sent_key_flat}": ph.get(sent_key_flat, ph.get("en", "")),
                "resp_ko":              "",
                "resp_roman":           "",
                "resp_en":              "",
                f"resp_{sent_key_flat}": "",
                "tip": ph.get("tip", ""),
            })
    phrases = pair_phrases

    # 출력 경로
    out_dir = os.path.join(args.output, "conversation", args.lang)
    os.makedirs(out_dir, exist_ok=True)
    filename = f"conv_{args.theme}_{args.lang}.mp4"
    output_path = os.path.join(out_dir, filename)

    print(f"\n>> 회화 영상 생성: [{args.lang}] {theme.get('title', {}).get('ko', args.theme)}")
    print(f"   구문 수: {len(phrases)}개")

    with tempfile.TemporaryDirectory() as tmpdir:
        create_conversation_video(theme, phrases, output_path, args.lang, tmpdir)

    print(f"\n완료! {output_path}")
