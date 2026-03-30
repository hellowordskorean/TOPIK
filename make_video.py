#!/usr/bin/env python3
"""
STEP 2: 애니메이션 영상 생성
- 단어 카드 + 예문 10개를 애니메이션 영상으로 제작
- Google Cloud TTS로 음성 생성
- FFmpeg/MoviePy로 영상 합성

필요 패키지:
pip install moviepy pillow google-cloud-texttospeech numpy
"""

import json
import os
import sys
import subprocess
import tempfile
import argparse
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from google.cloud import texttospeech

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
    }
    result = {}
    for key, paths in candidates.items():
        result[key] = next((p for p in paths if os.path.exists(p)), paths[0])
    return result

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

# ─── TTS ────────────────────────────────────────────────────
def text_to_speech(text: str, lang: str, output_path: str, slow: bool = False):
    """Google Cloud TTS로 음성 파일 생성"""
    client = texttospeech.TextToSpeechClient()
    
    synthesis_input = texttospeech.SynthesisInput(text=text)
    
    if lang == "ko":
        voice = texttospeech.VoiceSelectionParams(
            language_code="ko-KR",
            name="ko-KR-Neural2-A",  # 자연스러운 한국어 여성 음성
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )
    else:
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-F",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=0.85 if slow else 1.0,
        pitch=0.0,
    )
    
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    
    with open(output_path, "wb") as f:
        f.write(response.audio_content)

def log_video(word: dict, output_path: str, music_src: str = None, file_size: int = 0):
    """logs/videos_log.json 에 영상 생성 기록 (음악 파일 포함)"""
    log_path = "/app/logs/videos_log.json"
    try:
        log = []
        if os.path.exists(log_path):
            with open(log_path, encoding="utf-8") as f:
                log = json.load(f)
        entry = {
            "word_id":      word["id"],
            "word":         word["word"],
            "level":        word["level"],
            "meaning":      word["meaning"],
            "exam":         "TOPIK",
            "language":     "EN",
            "output_path":  output_path,
            "music_file":   os.path.basename(music_src) if music_src else None,
            "file_size":    file_size,
            "generated_at": datetime.now().isoformat(),
        }
        log = [x for x in log if x.get("word_id") != word["id"]]
        log.append(entry)
        log.sort(key=lambda x: x["word_id"])
        os.makedirs("/app/logs", exist_ok=True)
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
        os.makedirs("/app/logs", exist_ok=True)
        with open("/app/logs/progress.json", "w", encoding="utf-8") as f:
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
    "SP": {"명사": "Sustantivo", "동사": "Verbo", "형용사": "Adjetivo",
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
        "SP": (230, 126, 34),   # 오렌지
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
    font_pos = get_font("english", 34)
    draw.text((cx, card_y + 194), pos_text,
              font=font_pos, fill=(*C["text_muted"], int(220 * p)), anchor="mm")

    # 한국어 단어 (파란색, 굵게, 대형)
    font_word = get_font("korean_bold", 190)
    draw.text((cx, card_y + 390), word["word"],
              font=font_word, fill=(*C["accent"], int(255 * p)), anchor="mm")

    # 로마자 [ gage ] (파란색)
    font_roman = get_font("english", 38)
    draw.text((cx, card_y + 524), f"[ {word['romanization']} ]",
              font=font_roman, fill=(*C["accent"], int(220 * p)), anchor="mm")

    # 얇은 구분선
    div2_y = card_y + 566
    draw.rectangle([cx - 160, div2_y, cx + 160, div2_y + 1],
                   fill=(*C["divider"], int(255 * p)))

    # 뜻 (그레이, 1.5배 사이즈)
    font_meaning = get_font("english", 72)
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
    px, py = 50, 142  # 전체 100px 하단 이동

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
    ic_top = H - ic_h - 40     # 이미지 카드 시작 Y

    # ── 텍스트: 상황 → 한국어 → 로마자 → 영어 (이미지 위 영역에 배치) ──
    text_y = py + ph + 50  # pill 아래 여백

    situation = sentence.get("situation", "")
    if situation:
        font_sit = get_font("english", 30)
        draw.text((cx, text_y), f"#{situation}",
                  font=font_sit, fill=C["text_muted"], anchor="mm")
        text_y += 50

    # 한국어 예문 (90px bold)
    font_ko = get_font("korean_bold", 90)
    ko_text = sentence["ko"]
    if len(ko_text) >= 12:
        mid = len(ko_text) // 2
        for i in range(mid, len(ko_text)):
            if ko_text[i] == ' ':
                ko_text = ko_text[:i] + '\n' + ko_text[i + 1:]
                break
    lines_ko = len(ko_text.split('\n'))
    lh_ko = 110
    draw_multiline_highlighted(
        img, cx, text_y + (lines_ko * lh_ko) // 2,
        ko_text, word["word"],
        font_ko, C["text_primary"], C["accent"]
    )
    text_y += lines_ko * lh_ko + 12

    # IPA 발음기호 (34px, 뮤트 컬러)
    ko_phonetics = get_phonetics(sentence["ko"])
    if ko_phonetics:
        font_ipa = get_font("english", 34)
        draw.text((cx, text_y + 10), ko_phonetics,
                  font=font_ipa, fill=C["text_muted"], anchor="mm")
        text_y += 44

    text_y += 16

    # 영어 번역 (48px)
    font_en = get_font("english", 48)
    en_text = sentence["en"]
    en_hi = find_en_highlight(en_text, word["meaning"])
    draw_multiline_highlighted(
        img, cx, text_y + 20, en_text, en_hi,
        font_en, C["text_secondary"], C["accent"]
    )

    # ── 일러스트 카드 (하단 1:1, 드롭섀도우) ────────────────
    ic_r = 36
    draw_card_shadow(img, ic_x, ic_top, ic_w, ic_h, radius=ic_r)
    draw_illustration_in_card(img, bg_path, ic_x, ic_top, ic_w, ic_h, radius=ic_r)

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
    font_sub = get_font("english", 50)
    draw.text((cx, card_y + 480), f"= {word['meaning']}",
              font=font_sub, fill=(*C["text_secondary"], int(210 * p)), anchor="mm")

    # CTA (아래)
    font_cta = get_font("english", 30)
    draw.text((cx, card_y + card_h + 60),
              "Like & Subscribe for daily TOPIK vocab",
              font=font_cta, fill=(*C["text_muted"], int(160 * p)), anchor="mm")

# ─── 배경 이미지 ─────────────────────────────────────────────
def get_background(korean_word: str, meaning: str, level: int = 1, sentence_idx: int = None) -> str:
    """배경 이미지 경로 반환 (우선순위: 예문 일러스트 → 단어 일러스트 → Pexels → None)"""
    base = f"/app/assets/illustrations/lv{level}/{korean_word}"

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
        cache_dir = "/app/assets/backgrounds"
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
    music_dir = "/app/assets/music"
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


def draw_multiline_highlighted(img: Image.Image, cx: int, cy: int,
                                text: str, target: str,
                                font: ImageFont.FreeTypeFont,
                                base_color: tuple, hi_color: tuple):
    """멀티라인 텍스트에서 target 단어를 hi_color로 강조 렌더링"""
    draw = ImageDraw.Draw(img)
    lines = text.split('\n')
    lh = draw.textbbox((0, 0), "가나다", font=font)[3] + 14
    total_h = len(lines) * lh - 14
    start_y = cy - total_h // 2

    for li, line in enumerate(lines):
        ly = start_y + li * lh + lh // 2
        if target and target in line:
            idx = line.index(target)
            before, after = line[:idx], line[idx + len(target):]
            bw = draw.textbbox((0, 0), before, font=font)[2] if before else 0
            hw = draw.textbbox((0, 0), target, font=font)[2]
            fw = draw.textbbox((0, 0), line, font=font)[2]
            sx = cx - fw // 2
            if before:
                draw.text((sx, ly), before, font=font, fill=base_color, anchor="lm")
            draw.text((sx + bw, ly), target, font=font, fill=hi_color, anchor="lm")
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
def create_video(word: dict, output_path: str, tmpdir: str):
    print(f"\n>> 영상 생성: {word['word']} ({word['meaning']})")
    write_progress("1/4 TTS 음성 생성 중...", pct=5, word=word)

    T = CONFIG["timing"]
    sentences = word["sentences"]

    # 1. TTS 음성 파일 생성
    print("  1/4 TTS 음성 생성 중...")
    audio_files = []
    
    # 단어 발음 (한국어, 느리게)
    word_audio = os.path.join(tmpdir, "word_ko.mp3")
    text_to_speech(word["word"], "ko", word_audio, slow=True)
    
    # 뜻 (영어)
    meaning_audio = os.path.join(tmpdir, "word_en.mp3")
    text_to_speech(word["meaning"], "en", meaning_audio)
    
    # 예문들
    sentence_audios = []
    for i, sent in enumerate(sentences):
        ko_path = os.path.join(tmpdir, f"sent_{i}_ko.mp3")
        en_path = os.path.join(tmpdir, f"sent_{i}_en.mp3")
        text_to_speech(sent["ko"], "ko", ko_path)
        text_to_speech(sent["en"], "en", en_path)
        sentence_audios.append((ko_path, en_path))
    
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
    # 인트로 (단어 카드): (영어 → 한국어) × 2
    word_dur = get_audio_duration(word_audio)
    meaning_dur = get_audio_duration(meaning_audio)
    cycle = meaning_dur + 0.5 + word_dur + 0.8   # 1회 사이클 길이
    audio_timeline.append((meaning_audio, t))
    audio_timeline.append((word_audio,   t + meaning_dur + 0.5))
    audio_timeline.append((meaning_audio, t + cycle))
    audio_timeline.append((word_audio,   t + cycle + meaning_dur + 0.5))
    intro_dur = max(T["intro_duration"], cycle * 2 + T["word_hold"])
    segments.append(("intro", -1, t, intro_dur))
    t += intro_dur

    # 예문들: (영어 → 한국어) × 2
    for i, (ko_path, en_path) in enumerate(sentence_audios):
        ko_dur = get_audio_duration(ko_path)
        en_dur = get_audio_duration(en_path)
        cycle = en_dur + 0.8 + ko_dur + 0.8      # 1회 사이클 길이
        audio_timeline.append((en_path, t))
        audio_timeline.append((ko_path, t + en_dur + 0.8))
        audio_timeline.append((en_path, t + cycle))
        audio_timeline.append((ko_path, t + cycle + en_dur + 0.8))
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
    
    # 썸네일 저장 (인트로 첫 프레임)
    thumb_path = output_path.rsplit(".", 1)[0] + "_thumb.png"
    intro_frame = os.path.join(frames_dir, "frame_000000.png")
    if os.path.exists(intro_frame):
        import shutil
        shutil.copy2(intro_frame, thumb_path)
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
    parser.add_argument("--db", default="data/LanguageTest/words_db.json", help="단어 DB")
    parser.add_argument("--id", type=int, required=True, help="단어 ID")
    parser.add_argument("--output", default="output/", help="출력 폴더")
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
    
    os.makedirs(args.output, exist_ok=True)
    output_path = os.path.join(args.output, f"topik_{args.id:04d}_{word['word']}.mp4")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        create_video(word, output_path, tmpdir)
    
    print(f"\n완료! {output_path}")
