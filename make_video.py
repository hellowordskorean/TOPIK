#!/usr/bin/env python3
"""
STEP 2: 애니메이션 영상 생성
- 단어 카드 + 예문 10개를 애니메이션 영상으로 제작
- ElevenLabs Multilingual v2 TTS로 음성 생성
- FFmpeg/MoviePy로 영상 합성

필요 패키지:
pip install moviepy pillow elevenlabs numpy
"""

import json
import os
import sys
import io
import subprocess
import tempfile
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Windows cp949 인코딩 문제 방지 (pythonw.exe는 stdout/stderr가 None)
if sys.stdout is not None and sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr is not None and sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

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

# ─── 앱 베이스 경로 (Docker: /app, 로컬: APP_BASE 환경변수) ────
_APP_BASE = os.environ.get("APP_BASE", "/app")

def _app_path(rel: str) -> str:
    """'/app/...' Docker 경로를 현재 환경에 맞게 변환"""
    return os.path.join(_APP_BASE, rel)

# ─── 설정 ───────────────────────────────────────────────────
def _detect_fonts():
    candidates = {
        "korean_bold": ["/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
                        "C:/Windows/Fonts/NanumGothic-Bold.ttf", "C:/Windows/Fonts/malgunbd.ttf"],
        "korean":      ["/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                        "C:/Windows/Fonts/NanumGothic-Regular.ttf", "C:/Windows/Fonts/malgun.ttf"],
        "english_bold":["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                        "C:/Windows/Fonts/arialbd.ttf"],
        "english":     ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                        "C:/Windows/Fonts/arial.ttf"],
        # 일본어 폰트 (히라가나·가타카나·한자)
        "jp":          ["/app/assets/fonts/NotoSansJP-Regular.otf",
                        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                        "C:/Windows/Fonts/NotoSansJP-Regular.otf",
                        "C:/Windows/Fonts/msgothic.ttc",
                        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                        "C:/Windows/Fonts/malgun.ttf"],
        # 중국어 폰트 (간체)
        "cn":          ["/app/assets/fonts/NotoSansJP-Regular.otf",
                        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                        "C:/Windows/Fonts/msyh.ttc",
                        "C:/Windows/Fonts/simsun.ttc",
                        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                        "C:/Windows/Fonts/malgun.ttf"],
    }
    result = {}
    for key, paths in candidates.items():
        result[key] = next((p for p in paths if os.path.exists(p)), paths[0])
    return result


def _lang_font(lang_code: str, size: int) -> ImageFont.FreeTypeFont:
    """언어 코드에 맞는 폰트 반환 (JP/CN → CJK 폰트, 기타 → english)"""
    if lang_code == "JP":
        return get_font("jp", size)
    elif lang_code == "CN":
        return get_font("cn", size)
    return get_font("english", size)

_fonts = _detect_fonts()

CONFIG = {
    "video": {
        "width": 1080,
        "height": 1920,
        "fps": 30,
    },
    "colors": {
        "bg":           (248, 242, 234),  # warm cream
        "card_bg":      (255, 255, 255),  # white card
        "accent":       (50,   92, 200),  # blue — word, highlight, pill
        "accent_warm":  (108,  60,  58),  # dark maroon — TOPIK header
        "accent_pink":  (220, 155, 155),  # soft pink — inactive dot
        "text_primary": (38,   32,  30),  # near-black — Korean sentence
        "text_secondary":(108,  96,  90), # medium gray — English
        "text_muted":   (158, 148, 142),  # light gray — #situation, POS
        "divider":      (215, 205, 198),  # light warm divider
    },
    "fonts": _fonts,
    "timing": {
        "intro_duration":    3.0,   # 단어 카드 첫 등장 (초)
        "word_hold":         2.0,   # 단어만 보여주는 시간
        "sentence_duration": 5.0,   # 예문당 표시 시간 (음성 포함)
        "outro_duration":    2.0,   # 아웃트로
        "fade_duration":     0.3,   # 페이드 인/아웃
    },
}

REELS_TIMING = {
    "intro_duration":    1.5,   # 릴스: 짧은 인트로
    "word_hold":         0.8,   # 릴스: 짧은 단어 홀드
    "sentence_duration": 4.0,   # 릴스: 짧은 예문 표시
    "outro_duration":    1.0,   # 릴스: 짧은 아웃트로
    "fade_duration":     0.2,   # 릴스: 빠른 전환
}

_VIDEO_FORMAT = "youtube"

W = CONFIG["video"]["width"]
H = CONFIG["video"]["height"]
FPS = CONFIG["video"]["fps"]
C = CONFIG["colors"]

# ─── 폰트 로더 ──────────────────────────────────────────────
_font_cache = {}
def get_font(key: str, size: int) -> ImageFont.FreeTypeFont:
    cache_key = (key, size)
    if cache_key not in _font_cache:
        path = CONFIG["fonts"].get(key, CONFIG["fonts"]["english"])
        try:
            _font_cache[cache_key] = ImageFont.truetype(path, size)
        except Exception as e:
            print(f"  [WARN] Font load failed: {key} @ {path} ({e})")
            _font_cache[cache_key] = ImageFont.load_default()
    return _font_cache[cache_key]

# ─── TTS (ElevenLabs Multilingual v2) ───────────────────────
# .env 에서 재정의 가능:
#   EL_VOICE_KO  = <한국어 목소리 ID>     기본: Callum (나레이터)
#   EL_VOICE_TL  = <외국어 목소리 ID>     기본: Callum (나레이터)
_EL_VOICE_KO = os.environ.get("EL_VOICE_KO", "N2lVS1w4EtoT3dr4eOWO")  # Callum
_EL_VOICE_TL = os.environ.get("EL_VOICE_TL", "N2lVS1w4EtoT3dr4eOWO")  # Callum
_el_client = None

def _get_el_client():
    global _el_client
    if _el_client is None:
        api_key = os.environ.get("ELEVENLABS_API_KEY", "")
        if not api_key:
            raise RuntimeError(".env 에 ELEVENLABS_API_KEY 가 없습니다")
        _el_client = ElevenLabs(api_key=api_key)
    return _el_client

def text_to_speech(text: str, lang: str, output_path: str, slow: bool = False):
    """ElevenLabs Multilingual v2 로 음성 파일 생성"""
    voice_id = _EL_VOICE_KO if lang.lower() == "ko" else _EL_VOICE_TL
    # slow=True: stability 높여서 더 또렷하고 차분한 발음
    stability = 0.65 if slow else 0.45
    client = _get_el_client()
    audio_gen = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
        voice_settings=VoiceSettings(
            stability=stability,
            similarity_boost=0.80,
            style=0.25,
            use_speaker_boost=True,
        ),
    )
    with open(output_path, "wb") as f:
        for chunk in audio_gen:
            if chunk:
                f.write(chunk)

def log_video(word: dict, output_path: str, music_src: str = None, file_size: int = 0):
    """logs/videos_log.json 에 영상 생성 기록 (음악 파일 포함)"""
    log_path = _app_path("logs/videos_log.json")
    try:
        log = []
        if os.path.exists(log_path):
            with open(log_path, encoding="utf-8") as f:
                log = json.load(f)
        _lang = word.get("language", "EN")
        _exam = word.get("exam", "TOPIK")
        entry = {
            "word_id":      word["id"],
            "word":         word["word"],
            "level":        word["level"],
            "meaning":      word["meaning"],
            "exam":         _exam,
            "language":     _lang,
            "output_path":  output_path,
            "music_file":   os.path.basename(music_src) if music_src else None,
            "file_size":    file_size,
            "generated_at": datetime.now().isoformat(),
        }
        # 같은 단어+언어+시험 항목만 교체 (다른 언어는 유지)
        log = [x for x in log if not (
            x.get("word_id") == word["id"] and
            x.get("language", "EN") == _lang and
            x.get("exam", "TOPIK") == _exam
        )]
        log.append(entry)
        log.sort(key=lambda x: x["word_id"])
        os.makedirs(_app_path("logs"), exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def write_progress(step: str, pct: int = 0, word: dict = None, status: str = "running"):
    """대시보드용 진행 상황을 logs/progress.json 에 기록"""
    data = {
        "status": status,
        "step": step,
        "pct": pct,
        "updated_at": datetime.now().isoformat(),
    }
    if word:
        data["word_id"] = word["id"]
        data["word"]    = word["word"]
        data["meaning"] = word["meaning"]
        data["level"]   = word["level"]
    try:
        os.makedirs(_app_path("logs"), exist_ok=True)
        with open(_app_path("logs/progress.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass


def has_nvenc() -> bool:
    """NVIDIA NVENC 하드웨어 인코더 사용 가능 여부 확인 (실제 인코딩 테스트)"""
    try:
        r = subprocess.run(
            ["ffmpeg", "-f", "lavfi", "-i", "nullsrc=s=64x64:d=0.1",
             "-c:v", "h264_nvenc", "-f", "null", "-"],
            capture_output=True, text=True, timeout=10,
        )
        return r.returncode == 0
    except Exception:
        return False

_NVENC_AVAILABLE = None  # 최초 1회만 검사

def get_video_encoder() -> list:
    """사용 가능한 최적 비디오 인코더 옵션 반환"""
    global _NVENC_AVAILABLE
    if _NVENC_AVAILABLE is None:
        _NVENC_AVAILABLE = has_nvenc()
        if _NVENC_AVAILABLE:
            print("  [GPU] h264_nvenc 인코딩 활성화")
        else:
            print("  [CPU] libx264 인코딩 사용")
    if _NVENC_AVAILABLE:
        # RTX 4070 Ti 최적 설정: p4=균형, cq=품질, GPU 메모리 디코딩
        return ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "22", "-b:v", "0"]
    else:
        return ["-c:v", "libx264", "-preset", "fast", "-crf", "22"]


def get_audio_duration(path: str) -> float:
    """FFprobe로 오디오 길이 반환"""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except:
        return 3.0

# ─── 이미지 렌더러 ───────────────────────────────────────────
def draw_gradient_bg(img: Image.Image):
    """크림색 단색 배경"""
    ImageDraw.Draw(img).rectangle([0, 0, W, H], fill=C["bg"])

_COMMENT_CTA = {
    "EN": "Write a sentence using today's word\nin the comments below!",
    "JP": "今日の単語を使った例文を\nコメントに書いてみよう！",
    "CN": "用今天的单词造个句子\n写在评论区吧！",
    "VN": "Hãy viết câu ví dụ với từ hôm nay\nvào phần bình luận nhé!",
    "ES": "¡Escribe una oración con\nla palabra de hoy en los comentarios!",
}

_POS_MAP = {
    "EN": {"명사": "Noun", "동사": "Verb", "형용사": "Adjective", "부사": "Adverb",
           "관형사": "Determiner", "감탄사": "Interjection", "조사": "Particle",
           "접사": "Affix", "의존명사": "Bound Noun", "대명사": "Pronoun",
           "수사": "Numeral", "보조동사": "Auxiliary Verb"},
    "JP": {"명사": "名詞", "동사": "動詞", "형용사": "形容詞", "부사": "副詞",
           "관형사": "連体詞", "감탄사": "感嘆詞", "조사": "助詞",
           "접사": "接辞", "의존명사": "形式名詞", "대명사": "代名詞",
           "수사": "数詞", "보조동사": "補助動詞"},
    "CN": {"명사": "名词", "동사": "动词", "형용사": "形容词", "부사": "副词",
           "관형사": "冠形词", "감탄사": "感叹词", "조사": "助词",
           "접사": "词缀", "의존명사": "依存名词", "대명사": "代词",
           "수사": "数词", "보조동사": "助动词"},
    "VN": {"명사": "Danh t\u1eeb", "동사": "Dong t\u1eeb", "형용사": "Tinh t\u1eeb",
           "부사": "Pho t\u1eeb"},
    "ES": {"명사": "Sustantivo", "동사": "Verbo", "형용사": "Adjetivo",
           "부사": "Adverbio"},
}

def _translate_pos(pos_ko: str, lang: str = "EN") -> str:
    return _POS_MAP.get(lang, _POS_MAP["EN"]).get(pos_ko, pos_ko)

def draw_word_card(img: Image.Image, word: dict, bg_path: str = None, progress: float = 1.0):
    """단어 카드 — 라이트 테마
    통합 카드: 텍스트(상단) + 일러스트(하단)가 하나의 흰 카드 안에
    """
    draw = ImageDraw.Draw(img)
    p = progress
    cx = W // 2

    # ── 통합 흰 카드 (텍스트 + 일러스트) ─────────────────────
    card_x  = 40
    card_y  = 55
    card_w  = W - card_x * 2   # 1000
    card_r  = 48

    ic_margin = 30              # 일러스트 좌우 내부 여백
    ic_sq = card_w - ic_margin * 2   # 940
    ic_x  = card_x + ic_margin       # 70

    text_h  = 760   # 텍스트 섹션 높이
    ic_gap  = 20    # 텍스트↔일러스트 간격
    bot_pad = 40    # 카드 하단 내부 여백
    card_h  = text_h + ic_gap + ic_sq + bot_pad   # 1760

    card_ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(card_ov).rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=card_r, fill=(*C["card_bg"], int(255 * p))
    )
    img.paste(card_ov, mask=card_ov.split()[3])
    draw = ImageDraw.Draw(img)

    # "TOPIK LV.X" + 언어 라벨
    font_topik = get_font("english_bold", 34)
    draw.text((cx, card_y + 80), f"TOPIK  LV.{word['level']}",
              font=font_topik, fill=(*C["accent_warm"], int(255 * p)), anchor="mm")

    # 언어 라벨 배지 (우상단) — 언어별 색상
    _LANG_COLORS = {
        "EN": (50, 92, 200),    # 파랑
        "JP": (219, 68, 85),    # 빨강/핑크
        "CN": (200, 50, 50),    # 빨강
        "VN": (218, 165, 32),   # 골드
        "ES": (230, 126, 34),   # 오렌지
    }
    lang_code = word.get("language", "EN")
    if lang_code:
        lang_color = _LANG_COLORS.get(lang_code, C["accent"])
        font_lang = get_font("english_bold", 28)
        lb = draw.textbbox((0, 0), lang_code, font=font_lang)
        lw, lh = lb[2] - lb[0] + 24, lb[3] - lb[1] + 14
        lx = card_x + card_w - lw - 16
        ly = card_y + 16
        badge_ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(badge_ov).rounded_rectangle(
            [lx, ly, lx + lw, ly + lh], radius=lh // 2,
            fill=(*lang_color, int(220 * p))
        )
        img.paste(badge_ov, mask=badge_ov.split()[3])
        draw = ImageDraw.Draw(img)
        draw.text((lx + lw // 2, ly + lh // 2), lang_code,
                  font=font_lang, fill=(*C["card_bg"], int(255 * p)), anchor="mm")

    # 단어 ID (001, 002 …)
    font_id = get_font("english_bold", 28)
    draw.text((cx, card_y + 124), f"{word['id']:03d}",
              font=font_id, fill=(*C["accent_warm"], int(200 * p)), anchor="mm")

    # 얇은 구분선
    div_y = card_y + 152
    draw.rectangle([cx - 120, div_y, cx + 120, div_y + 1],
                   fill=(*C["divider"], int(255 * p)))

    # 품사 (대상 언어로 표기: Noun, 名詞, etc.)
    pos_text = _translate_pos(word.get("part_of_speech", ""), word.get("language", "EN"))
    font_pos = _lang_font(lang_code, 34)
    draw.text((cx, card_y + 194), pos_text,
              font=font_pos, fill=(*C["text_muted"], int(220 * p)), anchor="mm")

    # 한국어 단어 (파란색, 굵게, 대형)
    font_word = get_font("korean_bold", 190)
    draw.text((cx, card_y + 390), word["word"],
              font=font_word, fill=(*C["accent"], int(255 * p)), anchor="mm")

    # 로마자 [ gage ] (파란색) — per-language DB에는 없을 수 있음
    roman = word.get("romanization", "")
    if roman:
        font_roman = get_font("english", 38)
        draw.text((cx, card_y + 524), f"[ {roman} ]",
                  font=font_roman, fill=(*C["accent"], int(220 * p)), anchor="mm")

    # 얇은 구분선
    div2_y = card_y + 566
    draw.rectangle([cx - 160, div2_y, cx + 160, div2_y + 1],
                   fill=(*C["divider"], int(255 * p)))

    # 뜻 (그레이, 1.5배 사이즈)
    font_meaning = _lang_font(lang_code, 72)
    draw.text((cx, card_y + 660), word["meaning"],
              font=font_meaning, fill=(*C["text_secondary"], int(230 * p)), anchor="mm")

    # ── 카드 내부 일러스트 (하단) ───────────────────────────────
    ic_y = card_y + text_h + ic_gap   # 55 + 760 + 20 = 835
    draw_illustration_in_card(img, bg_path, ic_x, ic_y, ic_sq, ic_sq,
                               radius=36, p=p)

def draw_sentence_card(img: Image.Image, word: dict, sentence: dict,
                       sentence_num: int, total: int,
                       bg_path: str = None, progress: float = 1.0):
    """예문 카드 — 상단: pill + 텍스트 / 하단: 일러스트 카드(드롭섀도우)"""
    draw = ImageDraw.Draw(img)
    cx = W // 2

    # ── Top strip: pill + LV + dots ─────────────────────────
    font_pill = get_font("korean_bold", 42)
    pad_x, pad_y = 22, 10
    pb = draw.textbbox((0, 0), word["word"], font=font_pill)
    pw = pb[2] - pb[0] + pad_x * 2
    ph = pb[3] - pb[1] + pad_y * 2
    px, py = 50, 90

    pill_ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(pill_ov).rounded_rectangle(
        [px, py, px + pw, py + ph], radius=ph // 2,
        fill=(*C["accent"], 230)
    )
    img.paste(pill_ov, mask=pill_ov.split()[3])
    draw = ImageDraw.Draw(img)
    draw.text((px + pw // 2, py + ph // 2), word["word"],
              font=font_pill, fill=C["card_bg"], anchor="mm")

    font_lv = get_font("english_bold", 26)
    draw.text((px + pw + 14, py + ph // 2),
              f"LV.{word['level']} - {word['id']:03d}",
              font=font_lv, fill=C["text_primary"], anchor="lm")

    dot_r, dot_step = 7, 22
    dot_cy = py + ph // 2
    last_cx = W - 50 - dot_r
    first_cx = last_cx - (total - 1) * dot_step
    for i in range(total):
        dcx = first_cx + i * dot_step
        fill = C["accent"] if i < sentence_num else C["accent_pink"]
        draw.ellipse([dcx-dot_r, dot_cy-dot_r, dcx+dot_r, dot_cy+dot_r], fill=fill)

    # ── 이미지 영역 계산 (하단 1:1 고정) ────────────────────
    ic_x = 40
    ic_w = W - ic_x * 2        # 1000px
    ic_h = ic_w                 # 1:1 정사각형
    ic_top = H - ic_h - 80     # 이미지 카드 시작 Y (위로 이동)

    # ── 텍스트: 상황 → 한국어 → 로마자 → 영어 (이미지 위 영역에 배치) ──
    text_y = py + ph + 60  # pill 아래 여백

    _lc_sit = word.get("language", "EN").upper()
    _sk_sit = {"EN": "en", "JP": "jp", "CN": "cn", "VN": "vn", "ES": "es"}.get(_lc_sit, "en")
    # 언어별 상황 설명 우선 (situation_jp, situation_cn 등 → 없으면 기본 situation)
    situation = sentence.get(f"situation_{_sk_sit}") or sentence.get("situation", "")
    if situation:
        font_sit = _lang_font(_lc_sit, 38)
        # 상황 텍스트 너비 확인 → 두 줄 처리
        _sit_max_w = W - 120
        sit_text = f"#{situation}"
        if draw.textbbox((0, 0), sit_text, font=font_sit)[2] > _sit_max_w:
            mid_s = len(sit_text) // 2
            split_at = sit_text.rfind(' ', 0, mid_s) if ' ' in sit_text[:mid_s+5] else mid_s
            if split_at > 0:
                sit_text = sit_text[:split_at] + '\n' + sit_text[split_at+1:]
        sit_lines = sit_text.count('\n') + 1
        for _sl, _sline in enumerate(sit_text.split('\n')):
            draw.text((cx, text_y + _sl * 46), _sline,
                      font=font_sit, fill=C["text_muted"], anchor="mm")
        text_y += sit_lines * 46 + 29

    # 한국어 예문 — 폰트·줄바꿈 자동 조절
    MAX_KO_W = W - 80   # 1000px
    ko_text  = sentence["ko"]
    ko_size  = 90

    # 1) 중간 공백에서 줄바꿈 시도 (12자 이상)
    if len(ko_text) >= 12:
        mid = len(ko_text) // 2
        for i in range(mid, len(ko_text)):
            if ko_text[i] == ' ':
                ko_text = ko_text[:i] + '\n' + ko_text[i + 1:]
                break

    # 2) 가장 긴 줄이 MAX_KO_W를 넘으면 폰트 축소
    font_ko = get_font("korean_bold", ko_size)
    while ko_size > 44:
        max_lw = max(
            draw.textbbox((0, 0), line, font=font_ko)[2]
            for line in ko_text.split('\n')
        )
        if max_lw <= MAX_KO_W:
            break
        ko_size -= 4
        font_ko = get_font("korean_bold", ko_size)

    lines_ko = len(ko_text.split('\n'))
    lh_ko    = int(ko_size * 1.22)   # 90px → 110, 비례 유지
    draw_multiline_highlighted(
        img, cx, text_y + (lines_ko * lh_ko) // 2,
        ko_text, word["word"],
        font_ko, C["text_primary"], C["accent"]
    )
    text_y += lines_ko * lh_ko + 12

    # 발음기호: 언어별 처리
    _lc_ph = word.get("language", "EN").upper()
    ko_phonetics_raw = get_phonetics(sentence["ko"])
    if ko_phonetics_raw:
        if _lc_ph == "JP":
            # 일본어: 카타카나로 변환
            ph_text = _roman_to_katakana(ko_phonetics_raw)
            font_ph = _lang_font("JP", 34)
        else:
            # EN/CN/VN/ES: 로마자 그대로
            ph_text = ko_phonetics_raw
            font_ph = get_font("english", 34)
        # 두 줄 자동 처리
        ph_max_w = W - 120
        if draw.textbbox((0, 0), ph_text, font=font_ph)[2] > ph_max_w:
            words_ph = ph_text.split() if ' ' in ph_text else list(ph_text)
            if ' ' in ph_text:
                # 공백 기준 분리
                mid_ph = len(words_ph) // 2
                for _d in range(len(words_ph)):
                    for _idx in (mid_ph - _d, mid_ph + _d):
                        if 0 < _idx < len(words_ph):
                            l1 = ' '.join(words_ph[:_idx])
                            if draw.textbbox((0, 0), l1, font=font_ph)[2] <= ph_max_w:
                                ph_text = l1 + '\n' + ' '.join(words_ph[_idx:])
                                break
                    else:
                        continue
                    break
            else:
                # 문자 기준 분리 (카타카나 등)
                for _idx in range(len(ph_text) // 2, 0, -1):
                    if draw.textbbox((0, 0), ph_text[:_idx], font=font_ph)[2] <= ph_max_w:
                        ph_text = ph_text[:_idx] + '\n' + ph_text[_idx:]
                        break
        ph_lines = ph_text.count('\n') + 1
        lh_ph = 40
        for _pl, _pline in enumerate(ph_text.split('\n')):
            draw.text((cx, text_y + 10 + _pl * lh_ph), _pline,
                      font=font_ph, fill=C["text_muted"], anchor="mm")
        text_y += 10 + ph_lines * lh_ph + 4

    text_y += 36

    # 번역 텍스트 (48px) — 긴 문장 두 줄 허용
    _lc = word.get("language", "EN").upper()
    font_en = _lang_font(_lc, 48)
    _sk = {"EN": "en", "JP": "jp", "CN": "cn", "VN": "vn", "ES": "es"}.get(_lc, "en")
    en_text = sentence.get(_sk) or sentence.get("en", "")
    en_hi = find_en_highlight(en_text, word["meaning"])

    _max_en_w = W - 120
    _tmp_draw = ImageDraw.Draw(img)
    if _tmp_draw.textbbox((0, 0), en_text, font=font_en)[2] > _max_en_w:
        if ' ' in en_text:
            # 단어 기준 분리 (EN, ES, VN)
            en_words = en_text.split()
            line1, split_idx = [], len(en_words)
            for _wi, _ew in enumerate(en_words):
                _test = ' '.join(line1 + [_ew])
                if _tmp_draw.textbbox((0, 0), _test, font=font_en)[2] > _max_en_w and line1:
                    split_idx = _wi
                    break
                line1.append(_ew)
            en_text = ' '.join(en_words[:split_idx]) + '\n' + ' '.join(en_words[split_idx:])
        else:
            # 문자 기준 분리 (JP, CN — 공백 없음)
            for _ci in range(len(en_text) // 2, 0, -1):
                if _tmp_draw.textbbox((0, 0), en_text[:_ci], font=font_en)[2] <= _max_en_w:
                    en_text = en_text[:_ci] + '\n' + en_text[_ci:]
                    break

    en_lines = len(en_text.split('\n'))
    lh_en = _tmp_draw.textbbox((0, 0), "Ag", font=font_en)[3] + 14
    draw_multiline_highlighted(
        img, cx, text_y + (en_lines * lh_en) // 2, en_text, en_hi,
        font_en, C["text_secondary"], C["accent"]
    )

    # ── 일러스트 카드 (하단 1:1, 드롭섀도우) ────────────────
    ic_r = 36
    draw_card_shadow(img, ic_x, ic_top, ic_w, ic_h, radius=ic_r)
    draw_illustration_in_card(img, bg_path, ic_x, ic_top, ic_w, ic_h, radius=ic_r)

_LANG_LABEL = {
    "EN": "English",
    "JP": "日本語",
    "CN": "中文",
    "VN": "Tiếng Việt",
    "ES": "Español",
}

_THUMB_LANG_COLORS = {
    "EN": (50,  92, 200),
    "JP": (219, 68,  85),
    "CN": (200, 50,  50),
    "VN": (218, 165, 32),
    "ES": (230, 126, 34),
}

# pill 배너 텍스트: 각 언어로 "한국어 → 대상언어"
_THUMB_PILL_TEXT = {
    "EN": "KOREAN \u2192 ENGLISH",
    "JP": "\u97d3\u56fd\u8a9e \u2192 \u65e5\u672c\u8a9e",
    "CN": "\u97e9\u8bed \u2192 \u4e2d\u6587",
    "VN": "Ti\u1ebfng H\u00e0n \u2192 Ti\u1ebfng Vi\u1ec7t",
    "ES": "Coreano \u2192 Espa\u00f1ol",
}

_THUMB_ILL_BG = (245, 239, 231)

def render_thumbnail(src_frame: str, dest_path: str, word: dict):
    """썸네일: TOPIK/ID/단어/뜻/언어pill/일러스트 레이아웃 (처음부터 생성)"""
    img = Image.new("RGBA", (W, H), (*C["bg"], 255))
    cx  = W // 2

    lang_code  = word.get("language", "EN").upper()
    lang_color = _THUMB_LANG_COLORS.get(lang_code, (50, 92, 200))
    pill_text  = _THUMB_PILL_TEXT.get(lang_code, "KOREAN \u2192 ENGLISH")

    # ── 흰 카드 ──────────────────────────────────────────────
    cx1, cy1 = 33, 42
    cw = W - cx1 * 2     # 1014
    ch = H - cy1 - 33    # 1845
    card_ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(card_ov).rounded_rectangle(
        [cx1, cy1, cx1 + cw, cy1 + ch], radius=66, fill=(*C["card_bg"], 255)
    )
    img = Image.alpha_composite(img, card_ov)
    draw = ImageDraw.Draw(img)

    # ── TOPIK LV.X ───────────────────────────────────────────
    font_topik = get_font("english_bold", 54)
    topik_cy   = cy1 + 110
    draw.text((cx, topik_cy), f"TOPIK  LV.{word['level']}",
              font=font_topik, fill=C["accent_warm"], anchor="mm")

    # ── ID ───────────────────────────────────────────────────
    font_id = get_font("english_bold", 66)
    id_cy   = topik_cy + 80
    draw.text((cx, id_cy), f"{word['id']:03d}",
              font=font_id, fill=C["accent_warm"], anchor="mm")

    # ── 한국어 단어 ──────────────────────────────────────────
    word_text = word["word"]
    n = len(word_text)
    word_size = max(120, min(300, 390 - n * 30))
    font_word = get_font("korean_bold", word_size)
    wb = draw.textbbox((0, 0), word_text, font=font_word)
    while (wb[2] - wb[0]) > cw - 90 and word_size > 100:
        word_size -= 12
        font_word = get_font("korean_bold", word_size)
        wb = draw.textbbox((0, 0), word_text, font=font_word)
    word_cy  = id_cy + 80 + word_size // 2
    draw.text((cx, word_cy), word_text,
              font=font_word, fill=C["accent"], anchor="mm")
    word_bot = word_cy + word_size // 2

    # ── 뜻 ───────────────────────────────────────────────────
    font_meaning = _lang_font(lang_code, 58)
    meaning_cy   = word_bot + 55
    draw.text((cx, meaning_cy), word["meaning"],
              font=font_meaning, fill=C["text_secondary"], anchor="mm")
    mb = draw.textbbox((0, 0), word["meaning"], font=font_meaning)
    meaning_bot = meaning_cy + (mb[3] - mb[1]) // 2

    # ── 언어 pill 배너 ────────────────────────────────────────
    pill_top = meaning_bot + 70
    pill_h   = 118
    pill_x1  = cx1 + 36
    pill_x2  = cx1 + cw - 36
    pill_ov  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(pill_ov).rounded_rectangle(
        [pill_x1, pill_top, pill_x2, pill_top + pill_h],
        radius=pill_h // 2, fill=(*lang_color, 255)
    )
    img = Image.alpha_composite(img, pill_ov)
    draw = ImageDraw.Draw(img)

    if lang_code == "JP":
        font_pill = get_font("jp", 56)
    elif lang_code == "CN":
        font_pill = get_font("cn", 56)
    else:
        font_pill = get_font("english_bold", 56)
    draw.text((cx, pill_top + pill_h // 2), pill_text,
              font=font_pill, fill=(255, 255, 255, 255), anchor="mm")

    # ── 일러스트 ──────────────────────────────────────────────
    ill_top = pill_top + pill_h + 36
    ill_x   = cx1 + 36
    ill_w   = cw - 72
    ill_bot = cy1 + ch - 33
    ill_h   = ill_bot - ill_top

    ill_bg_ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ill_bg_ov).rounded_rectangle(
        [ill_x, ill_top, ill_x + ill_w, ill_bot],
        radius=48, fill=(*_THUMB_ILL_BG, 255)
    )
    img = Image.alpha_composite(img, ill_bg_ov)

    base    = _find_illust_base(word["word"], word.get("level", 1))
    bg_path = os.path.join(base, "word.png") if base and os.path.isdir(base) else None
    if bg_path and os.path.exists(bg_path):
        try:
            sq  = min(ill_w, ill_h)
            ix  = ill_x + (ill_w - sq) // 2
            iy  = ill_top + (ill_h - sq) // 2
            ill = Image.open(bg_path).convert("RGBA").resize((sq, sq), Image.LANCZOS)
            msk = Image.new("L", (sq, sq), 0)
            ImageDraw.Draw(msk).rounded_rectangle(
                [0, 0, sq - 1, sq - 1], radius=42, fill=255
            )
            img_c = img.convert("RGBA")
            img_c.paste(ill, (ix, iy), mask=msk)
            img = img_c
        except Exception:
            pass

    img.convert("RGB").save(dest_path, "PNG")

def draw_outro(img: Image.Image, word: dict, bg_path: str = None, progress: float = 1.0):
    """아웃트로 — 라이트 테마"""
    draw = ImageDraw.Draw(img)
    p = progress
    cx = W // 2

    # 중앙 흰 카드
    card_x, card_y, card_w, card_h = 80, 480, 920, 580
    card_ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(card_ov).rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=40, fill=(*C["card_bg"], int(255 * p))
    )
    img.paste(card_ov, mask=card_ov.split()[3])
    draw = ImageDraw.Draw(img)

    # TOPIK LV.X / 00Y
    font_h = get_font("english_bold", 30)
    draw.text((cx, card_y + 80), f"TOPIK  LV.{word['level']}  ·  {word['id']:03d}",
              font=font_h, fill=(*C["accent_warm"], int(230 * p)), anchor="mm")

    div_y = card_y + 112
    draw.rectangle([cx - 100, div_y, cx + 100, div_y + 1],
                   fill=(*C["divider"], int(255 * p)))

    # 한국어 단어 (파란색)
    font_big = get_font("korean_bold", 180)
    draw.text((cx, card_y + 330), word["word"],
              font=font_big, fill=(*C["accent"], int(255 * p)), anchor="mm")

    # = meaning
    _outro_lc = word.get("language", "EN").upper()
    font_sub = _lang_font(_outro_lc, 50)
    draw.text((cx, card_y + 480), f"= {word['meaning']}",
              font=font_sub, fill=(*C["text_secondary"], int(210 * p)), anchor="mm")

    # CTA (아래) — 구독 유도
    font_cta = get_font("english", 30)
    cta_text = ("Follow for daily TOPIK vocab" if _VIDEO_FORMAT == "reels"
                else "Like & Subscribe for daily TOPIK vocab")
    draw.text((cx, card_y + card_h + 60), cta_text,
              font=font_cta, fill=(*C["text_muted"], int(160 * p)), anchor="mm")

    # 댓글 유도 CTA
    lang_code = word.get("language", "EN").upper()
    comment_text = _COMMENT_CTA.get(lang_code, _COMMENT_CTA["EN"])
    font_comment = _lang_font(lang_code, 36) if lang_code in ("JP", "CN") else get_font("english", 36)
    # 배경 박스
    cta_y = card_y + card_h + 130
    lines = comment_text.split("\n")
    line_h = 46
    box_h = line_h * len(lines) + 40
    box_x1, box_x2 = cx - 400, cx + 400
    cta_ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(cta_ov).rounded_rectangle(
        [box_x1, cta_y - 20, box_x2, cta_y + box_h],
        radius=20, fill=(*C["accent"], int(220 * p))
    )
    img.paste(cta_ov, mask=cta_ov.split()[3])
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        draw.text((cx, cta_y + i * line_h + 10), line,
                  font=font_comment, fill=(255, 255, 255, int(255 * p)), anchor="mm")

# ─── 배경 이미지 ─────────────────────────────────────────────
def _find_illust_base(korean_word: str, level: int) -> str:
    """일러스트 폴더 경로 반환 — 구 형식 {word} 또는 신 형식 {id}_{word} 모두 지원"""
    old_base = _app_path(f"assets/illustrations/lv{level}/{korean_word}")
    if os.path.isdir(old_base):
        return old_base
    # 신 형식: 숫자_단어 폴더 탐색
    lv_dir = _app_path(f"assets/illustrations/lv{level}")
    if os.path.isdir(lv_dir):
        for entry in os.listdir(lv_dir):
            parts = entry.split("_", 1)
            if len(parts) == 2 and parts[0].isdigit() and parts[1] == korean_word:
                return os.path.join(lv_dir, entry)
    return old_base  # 없어도 경로는 반환 (존재 여부는 호출부에서 확인)

def get_background(korean_word: str, meaning: str, level: int = 1, sentence_idx: int = None) -> str:
    """배경 이미지 경로 반환 (우선순위: 예문 일러스트 → 단어 일러스트 → Pexels → None)"""
    base = _find_illust_base(korean_word, level)

    # 1순위: 예문별 일러스트 (lv{level}/{word}/{idx}.png)
    if sentence_idx is not None:
        sent_path = f"{base}/{sentence_idx}.png"
        if os.path.exists(sent_path):
            return sent_path

    # 2순위: 단어 일러스트 (lv{level}/{word}/word.png)
    illust_path = f"{base}/word.png"
    if os.path.exists(illust_path):
        return illust_path

    # 2순위: Pexels 이미지 (PEXELS_API_KEY 있을 때)
    import hashlib, requests
    api_key = os.environ.get("PEXELS_API_KEY", "")
    if api_key:
        search_term = meaning.split(",")[0].strip().split()[0]
        cache_dir = _app_path("assets/backgrounds")
        os.makedirs(cache_dir, exist_ok=True)
        safe_name = hashlib.md5(search_term.encode()).hexdigest()[:10]
        cache_path = os.path.join(cache_dir, f"{safe_name}.jpg")
        if os.path.exists(cache_path):
            return cache_path
        try:
            resp = requests.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": api_key},
                params={"query": search_term, "orientation": "landscape", "per_page": 1},
                timeout=10,
            )
            photos = resp.json().get("photos", [])
            if photos:
                img_data = requests.get(photos[0]["src"]["large2x"], timeout=15).content
                with open(cache_path, "wb") as f:
                    f.write(img_data)
                return cache_path
        except Exception as e:
            print(f"  Pexels 실패 ({search_term}): {e}")

    return None  # 3순위: 그라디언트 (draw_background에서 처리)


def get_background_music(target_duration: float) -> str | None:
    """영상 길이에 가장 잘 맞는 배경음악 파일 반환.
    - target 이상인 트랙 중 가장 짧은 것 (루프 없이 딱 맞음)
    - 전부 짧으면 가장 긴 것 (루프 횟수 최소화)
    """
    music_dir = _app_path("assets/music")
    if not os.path.isdir(music_dir):
        return None
    tracks = [
        os.path.join(music_dir, f)
        for f in os.listdir(music_dir)
        if f.endswith((".mp3", ".wav", ".m4a"))
    ]
    if not tracks:
        return None

    track_durations = []
    for t in tracks:
        try:
            d = get_audio_duration(t)
            track_durations.append((t, d))
        except Exception:
            pass

    if not track_durations:
        return None

    # target 이상인 트랙 중 가장 짧은 것 (루프 없음)
    sufficient = [(t, d) for t, d in track_durations if d >= target_duration]
    if sufficient:
        best = min(sufficient, key=lambda x: x[1])
        print(f"  배경음악: {os.path.basename(best[0])} ({best[1]:.0f}초, 영상 {target_duration:.0f}초)")
        return best[0]

    # 전부 짧으면 가장 긴 것 선택 (루핑으로 채움)
    best = max(track_durations, key=lambda x: x[1])
    print(f"  배경음악: {os.path.basename(best[0])} ({best[1]:.0f}초 → 루프, 영상 {target_duration:.0f}초)")
    return best[0]


def draw_background(img: Image.Image, bg_path: str = None):
    """크림색 단색 배경 — 일러스트는 각 카드 함수에서 직접 배치"""
    draw_gradient_bg(img)


def draw_card_shadow(img: Image.Image, x: int, y: int, w: int, h: int, radius: int = 36):
    """카드 아래 부드러운 드롭 섀도우"""
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [x + 4, y + 14, x + w + 4, y + h + 14],
        radius=radius, fill=(30, 20, 15, 50)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=18))
    img.paste(shadow, mask=shadow.split()[3])


def draw_illustration_in_card(img: Image.Image, bg_path: str,
                               x: int, y: int, w: int, h: int,
                               radius: int = 32, p: float = 1.0):
    """일러스트를 rounded white card 안에 그리기 (1:1 비율 유지, 중앙 배치)"""
    # 흰 카드 배경
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle(
        [x, y, x + w, y + h], radius=radius,
        fill=(*C["card_bg"], int(255 * p))
    )
    img.paste(ov, mask=ov.split()[3])

    if bg_path and os.path.exists(bg_path):
        try:
            # 1:1 비율 유지 → 짧은 쪽에 맞춰 정사각형, 카드 중앙 배치
            sq = min(w, h)
            ix = x + (w - sq) // 2
            iy = y + (h - sq) // 2
            illust = Image.open(bg_path).convert("RGBA").resize((sq, sq), Image.LANCZOS)
            mask = Image.new("L", (sq, sq), 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                [0, 0, sq - 1, sq - 1], radius=max(radius - 4, 0), fill=255
            )
            img.paste(illust, (ix, iy), mask=mask)
        except Exception:
            pass


def _ko_extend_to_boundary(text: str, start: int, min_len: int) -> str:
    """start 위치에서 단어 경계(공백·문장부호)까지 확장"""
    _STOP = set(' .?!,。？！·…')
    end = start + min_len
    while end < len(text) and text[end] not in _STOP:
        end += 1
    return text[start:end]


def _find_ko_match(line: str, word: str):
    """한국어 문장에서 단어(활용형 포함)를 찾아 (start_idx, matched_str) 반환.
    불규칙 활용(가깝다→가까워요 등)도 음절 접두사 매칭으로 처리."""
    if not word:
        return -1, ""
    # 1. 정확히 일치
    if word in line:
        return line.index(word), word
    # 2. 어간 추출 (다 제거)
    stem = word[:-1] if word.endswith("다") else word
    if stem and stem in line:
        idx = line.index(stem)
        return idx, _ko_extend_to_boundary(line, idx, len(stem))
    # 3. 어간 앞부분 점진 축소 (불규칙 활용 대응, 최소 1음절)
    for plen in range(len(stem) - 1, 0, -1):
        prefix = stem[:plen]
        for i in range(len(line)):
            if line[i:i + plen] == prefix:
                # 단어 첫 음절인지 확인 (앞이 공백이거나 문장 시작)
                if i == 0 or line[i - 1] == ' ':
                    matched = _ko_extend_to_boundary(line, i, plen)
                    if matched:
                        return i, matched
    return -1, ""


def draw_multiline_highlighted(img: Image.Image, cx: int, cy: int,
                                text: str, target: str,
                                font: ImageFont.FreeTypeFont,
                                base_color: tuple, hi_color: tuple):
    """멀티라인 텍스트에서 target 단어를 hi_color로 강조 렌더링
    (불규칙 활용형도 음절 접두사 매칭으로 처리)"""
    draw = ImageDraw.Draw(img)
    lines = text.split('\n')
    lh = draw.textbbox((0, 0), "가나다", font=font)[3] + 14
    total_h = len(lines) * lh - 14
    start_y = cy - total_h // 2

    for li, line in enumerate(lines):
        ly = start_y + li * lh + lh // 2
        idx, matched = _find_ko_match(line, target) if target else (-1, "")
        if idx >= 0 and matched:
            before = line[:idx]
            after  = line[idx + len(matched):]
            bw = draw.textbbox((0, 0), before, font=font)[2] if before else 0
            hw = draw.textbbox((0, 0), matched, font=font)[2]
            fw = draw.textbbox((0, 0), line, font=font)[2]
            sx = cx - fw // 2
            if before:
                draw.text((sx, ly), before, font=font, fill=base_color, anchor="lm")
            draw.text((sx + bw, ly), matched, font=font, fill=hi_color, anchor="lm")
            if after:
                draw.text((sx + bw + hw, ly), after, font=font, fill=base_color, anchor="lm")
        else:
            draw.text((cx, ly), line, font=font, fill=base_color, anchor="mm")


def find_en_highlight(en_text: str, meaning: str) -> str:
    """영어 문장에서 뜻 단어 찾기 (첫 번째 매치)"""
    for m in meaning.split(","):
        m = m.strip()
        lo = en_text.lower()
        idx = lo.find(m.lower())
        if idx != -1:
            return en_text[idx: idx + len(m)]
    return ""


def get_phonetics(text: str) -> str:
    """한국어 문장 → 로마자 발음 표기"""
    try:
        from korean_romanizer.romanizer import Romanizer
        result = Romanizer(text).romanize()
        return result
    except Exception:
        return ""


def _roman_to_katakana(roman: str) -> str:
    """Korean Revised Romanization → Katakana (근사 변환)"""
    _M2 = {
        "gg": "ッ", "kk": "ッ", "dd": "ッ", "tt": "ッ", "bb": "ッ", "pp": "ッ", "ss": "ッ",
        "ch": "チ", "sh": "シ", "ng": "ン",
        "ga": "ガ", "gi": "ギ", "gu": "グ", "ge": "ゲ", "go": "ゴ",
        "ka": "カ", "ki": "キ", "ku": "ク", "ke": "ケ", "ko": "コ",
        "na": "ナ", "ni": "ニ", "nu": "ヌ", "ne": "ネ", "no": "ノ",
        "da": "ダ", "di": "ディ", "du": "ドゥ", "de": "デ", "do": "ド",
        "ta": "タ", "ti": "ティ", "tu": "トゥ", "te": "テ", "to": "ト",
        "ra": "ラ", "ri": "リ", "ru": "ル", "re": "レ", "ro": "ロ",
        "la": "ラ", "li": "リ", "lu": "ル", "le": "レ", "lo": "ロ",
        "ma": "マ", "mi": "ミ", "mu": "ム", "me": "メ", "mo": "モ",
        "ba": "バ", "bi": "ビ", "bu": "ブ", "be": "ベ", "bo": "ボ",
        "pa": "パ", "pi": "ピ", "pu": "プ", "pe": "ペ", "po": "ポ",
        "ha": "ハ", "hi": "ヒ", "hu": "フ", "he": "ヘ", "ho": "ホ",
        "sa": "サ", "si": "シ", "su": "ス", "se": "セ", "so": "ソ",
        "ja": "ジャ", "ji": "ジ", "ju": "ジュ", "je": "ジェ", "jo": "ジョ",
        "ya": "ヤ", "yu": "ユ", "yo": "ヨ",
        "wa": "ワ", "wi": "ウィ", "we": "ウェ", "wo": "ウォ",
        "ae": "エ", "eo": "オ", "eu": "ウ", "oe": "ウェ", "ui": "ウィ",
    }
    _M1 = {
        "a": "ア", "i": "イ", "u": "ウ", "e": "エ", "o": "オ",
        "n": "ン", "k": "ク", "g": "ク", "t": "ト", "d": "ド",
        "r": "ル", "l": "ル", "m": "ム", "b": "ブ", "p": "プ",
        "h": "フ", "s": "ス", "j": "ジ", "c": "ク", "w": "ウ", "y": "イ",
        "-": "・", " ": " ",
    }
    result, i, s = "", 0, roman.lower()
    while i < len(s):
        if i + 1 < len(s) and s[i:i+2] in _M2:
            result += _M2[s[i:i+2]]; i += 2
        elif s[i] in _M1:
            result += _M1[s[i]]; i += 1
        else:
            result += s[i]; i += 1
    return result


# ─── 프레임 생성기 ───────────────────────────────────────────
def fade(t: float, duration: float, fade_dur: float) -> float:
    """페이드 in/out 투명도 계산"""
    if t < fade_dur:
        return t / fade_dur
    if t > duration - fade_dur:
        return (duration - t) / fade_dur
    return 1.0

def render_frame(word: dict, sentence_idx: int, t: float, duration: float,
                 bg_path: str = None) -> np.ndarray:
    """단일 프레임 렌더링 → numpy array"""
    img = Image.new("RGBA", (W, H), (*C["bg"], 255))
    draw_background(img)

    alpha = 1.0  # fade 제거 — 즉시 전환

    if sentence_idx == -1:
        draw_word_card(img, word, bg_path=bg_path, progress=alpha)
    elif sentence_idx == -2:
        draw_outro(img, word, bg_path=bg_path, progress=alpha)
    else:
        draw_sentence_card(
            img, word,
            word["sentences"][sentence_idx],
            sentence_idx + 1,
            len(word["sentences"]),
            bg_path=bg_path,
            progress=alpha
        )
    
    return np.array(img.convert("RGB"))


# ─── 메인 영상 생성 ──────────────────────────────────────────
def create_video(word: dict, output_path: str, tmpdir: str, video_format: str = "youtube"):
    print(f"\n>> 영상 생성: {word['word']} ({word['meaning']})")
    write_progress("1/4 TTS 음성 생성 중...", pct=5, word=word)

    global _VIDEO_FORMAT
    is_reels = video_format == "reels"
    _VIDEO_FORMAT = video_format
    T = REELS_TIMING if is_reels else CONFIG["timing"]
    sentences = word["sentences"]
    if is_reels:
        sentences = sentences[:5]
        word = {**word, "sentences": sentences}

    # 대상 언어 코드 및 예문 키 결정
    _lang_code = word.get("language", "EN").upper()
    _SENT_KEY = {"EN": "en", "JP": "jp", "CN": "cn", "VN": "vn", "ES": "es"}
    _tts_lang  = _lang_code.lower()  # TTS 함수에 넘길 키
    _sent_key  = _SENT_KEY.get(_lang_code, "en")  # 예문 번역 키

    # 1. TTS 음성 파일 생성
    print("  1/4 TTS 음성 생성 중...")
    audio_files = []

    # 단어 발음 (한국어, 느리게)
    word_audio = os.path.join(tmpdir, "word_ko.mp3")
    text_to_speech(word["word"], "ko", word_audio, slow=True)

    # 뜻 (대상 언어)
    meaning_audio = os.path.join(tmpdir, "word_tl.mp3")
    text_to_speech(word["meaning"], _tts_lang, meaning_audio)

    # 예문들
    sentence_audios = []
    for i, sent in enumerate(sentences):
        ko_path = os.path.join(tmpdir, f"sent_{i}_ko.mp3")
        tl_path = os.path.join(tmpdir, f"sent_{i}_tl.mp3")
        text_to_speech(sent["ko"], "ko", ko_path)
        tl_text = sent.get(_sent_key) or sent.get("en", "")
        text_to_speech(tl_text, _tts_lang, tl_path)
        sentence_audios.append((ko_path, tl_path))
    
    # 배경 이미지: 세그먼트별 (예문별 일러스트 → 단어 일러스트 → 그라디언트)
    lv = word["level"]
    word_bg = get_background(word["word"], word["meaning"], level=lv)
    sent_bgs = [
        get_background(word["word"], word["meaning"], level=lv, sentence_idx=i)
        for i in range(len(sentences))
    ]

    write_progress("2/4 타임라인 계산 중...", pct=20, word=word)
    # 2. 타임라인 계산
    print("  2/4 타임라인 계산 중...")
    segments = []        # (type, sentence_idx, seg_start, duration) — 프레임 렌더링용
    audio_timeline = []  # (audio_path, absolute_start_time)       — 오디오 배치용

    t = 0.0
    # 인트로 (단어 카드)
    word_dur = get_audio_duration(word_audio)
    meaning_dur = get_audio_duration(meaning_audio)
    if is_reels:
        # 릴스: (영어 → 한국어) × 1, 짧은 간격
        gap1, gap2 = 0.4, 0.4
        cycle = meaning_dur + gap1 + word_dur + gap2
        audio_timeline.append((meaning_audio, t))
        audio_timeline.append((word_audio,   t + meaning_dur + gap1))
        intro_dur = max(T["intro_duration"], cycle + T["word_hold"])
    else:
        # YouTube: (영어 → 한국어) × 2
        gap1, gap2 = 0.5, 0.8
        cycle = meaning_dur + gap1 + word_dur + gap2
        audio_timeline.append((meaning_audio, t))
        audio_timeline.append((word_audio,   t + meaning_dur + gap1))
        audio_timeline.append((meaning_audio, t + cycle))
        audio_timeline.append((word_audio,   t + cycle + meaning_dur + gap1))
        intro_dur = max(T["intro_duration"], cycle * 2 + T["word_hold"])
    segments.append(("intro", -1, t, intro_dur))
    t += intro_dur

    # 예문들
    for i, (ko_path, en_path) in enumerate(sentence_audios):
        ko_dur = get_audio_duration(ko_path)
        en_dur = get_audio_duration(en_path)
        if is_reels:
            # 릴스: (영어 → 한국어) × 1, 짧은 간격
            gap_s = 0.4
            cycle = en_dur + gap_s + ko_dur + gap_s
            audio_timeline.append((en_path, t))
            audio_timeline.append((ko_path, t + en_dur + gap_s))
            sent_dur = max(T["sentence_duration"], cycle + 0.5)
        else:
            # YouTube: (영어 → 한국어) × 2
            gap_s = 0.8
            cycle = en_dur + gap_s + ko_dur + gap_s
            audio_timeline.append((en_path, t))
            audio_timeline.append((ko_path, t + en_dur + gap_s))
            audio_timeline.append((en_path, t + cycle))
            audio_timeline.append((ko_path, t + cycle + en_dur + gap_s))
            sent_dur = max(T["sentence_duration"], cycle * 2 + 1.0)
        segments.append(("sentence", i, t, sent_dur))
        t += sent_dur

    # 아웃트로
    segments.append(("outro", -2, t, T["outro_duration"]))
    t += T["outro_duration"]
    
    total_duration = t
    total_frames = int(total_duration * FPS)
    print(f"  총 길이: {total_duration:.1f}초 ({total_frames}프레임)")
    
    write_progress("3/4 프레임 렌더링 중...", pct=30, word=word)
    # 3. 프레임 렌더링 → 임시 비디오
    print("  3/4 프레임 렌더링 중...")
    frames_dir = os.path.join(tmpdir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    seg_idx = 0
    for frame_n in range(total_frames):
        t_current = frame_n / FPS
        
        # 현재 세그먼트 찾기
        while seg_idx < len(segments) - 1 and t_current >= segments[seg_idx + 1][2]:
            seg_idx += 1
        
        seg = segments[seg_idx]
        t_local = t_current - seg[2]

        # 세그먼트 타입에 따라 배경 선택
        s_idx = seg[1]
        if s_idx >= 0 and s_idx < len(sent_bgs):
            cur_bg = sent_bgs[s_idx]
        else:
            cur_bg = word_bg

        frame = render_frame(word, seg[1], t_local, seg[3], bg_path=cur_bg)
        
        # PNG 저장
        frame_path = os.path.join(frames_dir, f"frame_{frame_n:06d}.png")
        Image.fromarray(frame).save(frame_path)
        
        if frame_n % (FPS * 5) == 0:
            print(f"    {frame_n}/{total_frames} 프레임 완료 ({t_current:.1f}s)")
            pct = 30 + int((frame_n / total_frames) * 55)  # 30~85%
            write_progress(f"3/4 프레임 렌더링 중... ({frame_n}/{total_frames})", pct=pct, word=word)
    
    # 썸네일 저장 (인트로 첫 프레임) — thumbnail/ 폴더에 별도 저장
    video_dir_for_thumb = os.path.dirname(output_path)
    thumb_dir = os.path.join(os.path.dirname(video_dir_for_thumb), "thumbnail")
    os.makedirs(thumb_dir, exist_ok=True)
    thumb_name = os.path.splitext(os.path.basename(output_path))[0] + "_thumb.png"
    thumb_path = os.path.join(thumb_dir, thumb_name)
    intro_frame = os.path.join(frames_dir, "frame_000000.png")
    if os.path.exists(intro_frame):
        render_thumbnail(intro_frame, thumb_path, word)
        print(f"  [OK] 썸네일 저장: {thumb_path}")

    write_progress("4/4 FFmpeg 합성 중...", pct=88, word=word)
    print("  4/4 FFmpeg 합성 중...")

    # FFmpeg 오디오 합성
    # 입력 순서: 0=비디오프레임, 1=silence, 2~=나레이션, 마지막=배경음악(옵션)
    silence_path = os.path.join(tmpdir, "silence.mp3")
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", str(total_duration), "-q:a", "9", "-acodec", "libmp3lame",
        silence_path, "-y"
    ], capture_output=True)

    delay_filters = []
    a_idx = 0
    input_args = ["-i", silence_path]

    for ap, abs_start in audio_timeline:
        if os.path.exists(ap):
            input_args += ["-i", ap]
            delay_ms = int(abs_start * 1000)
            delay_filters.append(
                f"[{a_idx+2}:a]adelay={delay_ms}|{delay_ms}[a{a_idx}]"
            )
            a_idx += 1

    # 배경 음악 (있을 경우 마지막 입력으로 추가)
    music_src = get_background_music(total_duration)
    music_input_idx = None
    if music_src:
        input_args += ["-i", music_src]
        music_input_idx = a_idx + 2  # 0=video, 1=silence, 2..a_idx+1=narr, a_idx+2=music

    if delay_filters:
        mix_input = "".join(f"[a{i}]" for i in range(len(delay_filters)))
        if music_input_idx is not None:
            # 나레이션 믹스 → [narr], 배경음악 볼륨 12% → [bgm], 최종 합성
            filter_complex = (
                ";".join(delay_filters) +
                f";[1:a]{mix_input}amix=inputs={len(delay_filters)+1}:normalize=0[narr]"
                f";[{music_input_idx}:a]aloop=loop=-1:size=2e+09,"
                f"atrim=duration={total_duration:.3f},volume=0.12[bgm]"
                f";[narr][bgm]amix=inputs=2:normalize=0[aout]"
            )
        else:
            filter_complex = ";".join(delay_filters) + f";[1:a]{mix_input}amix=inputs={len(delay_filters)+1}:normalize=0[aout]"
        audio_map = ["-filter_complex", filter_complex, "-map", "[aout]"]
    else:
        audio_map = ["-map", "0:a"]
    
    cmd = [
        "ffmpeg",
        "-framerate", str(FPS),
        "-i", os.path.join(frames_dir, "frame_%06d.png"),
    ] + input_args + audio_map + [
        "-map", "0:v",
        *get_video_encoder(),
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
        "-y"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FFmpeg 오류: {result.stderr[-500:]}")
        raise RuntimeError("FFmpeg 실패")
    
    print(f"  [OK] 영상 저장: {output_path}")
    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    log_video(word, output_path, music_src=music_src, file_size=file_size)
    write_progress("완료", pct=100, word=word, status="idle")
    return output_path


# ─── 엔트리포인트 ────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TOPIK 단어 영상 생성")
    parser.add_argument("--db", default="../data/LanguageTest/words_db.json", help="단어 DB")
    parser.add_argument("--id", type=int, required=True, help="단어 ID")
    parser.add_argument("--output", default="output/", help="출력 루트 폴더")
    parser.add_argument("--exam", default="TOPIK", help="시험 종류")
    parser.add_argument("--lang", default="EN", help="대상 언어")
    parser.add_argument("--format", default="youtube", choices=["youtube", "reels"],
                        help="영상 포맷 (youtube: 전체, reels: 짧은 릴스)")
    args = parser.parse_args()
    
    with open(args.db, encoding="utf-8") as f:
        raw = json.load(f)

    # per-level 형식 정규화 (object with "words" → flat array)
    if isinstance(raw, dict) and "words" in raw:
        db = raw["words"]
        file_level = raw.get("level")
        for w in db:
            if "level" not in w and file_level is not None:
                w["level"] = file_level
            if "sentences" not in w and "examples" in w:
                w["sentences"] = w["examples"]
            if "part_of_speech" not in w and "pos" in w:
                w["part_of_speech"] = w["pos"]
    else:
        db = raw

    word = next((w for w in db if w["id"] == args.id), None)
    if not word:
        print(f"단어 ID {args.id}를 찾을 수 없습니다")
        sys.exit(1)

    word["language"] = args.lang
    word["exam"] = args.exam

    # 폴더 트리: output/{시험}/{언어}/lv{등급}/video/ & thumbnail/
    lv = word.get("level", 1)
    sub_dir = "reels" if args.format == "reels" else "video"
    video_dir = os.path.join(args.output, args.exam, args.lang, f"lv{lv}", sub_dir)
    os.makedirs(video_dir, exist_ok=True)

    fmt_suffix = "_reels" if args.format == "reels" else ""
    filename = f"{args.exam.lower()}_{args.id:04d}_{word['word']}_{args.lang}{fmt_suffix}"
    output_path = os.path.join(video_dir, f"{filename}.mp4")

    with tempfile.TemporaryDirectory() as tmpdir:
        create_video(word, output_path, tmpdir, video_format=args.format)
    
    print(f"\n완료! {output_path}")
