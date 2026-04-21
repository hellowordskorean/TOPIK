#!/usr/bin/env python3
"""
YouTube 썸네일 생성 (720×1280 세로)
레이아웃:
  [상단] 언어 배지 (대형, 중앙)
         TOPIK LV.X / ID
         한국어 단어 (초대형)
  [하단] 일러스트 (큰 카드)
  [최하단] TOPIK Korean Vocabulary

사용법:
  python make_thumbnail.py --db /app/data/LanguageTest/words_db.json --id 1 --output /app/output/thumbnails/
  python make_thumbnail.py --db /app/data/LanguageTest/words_db.json --all --output /app/output/thumbnails/
"""

import json
import os
import sys
import io
import argparse
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from PIL import Image, ImageDraw, ImageFont

_APP_BASE = os.environ.get("APP_BASE", str(Path(__file__).parent))

def _app_path(rel: str) -> str:
    return os.path.join(_APP_BASE, rel)

TW = 720
TH = 1280

C = {
    "bg":             (248, 242, 234),
    "card_bg":        (255, 255, 255),
    "accent":         (50,   92, 200),
    "accent_warm":    (108,  60,  58),
    "text_muted":     (158, 148, 142),
    "ill_bg":         (245, 239, 231),  # 일러스트 배경 (크림보다 살짝 어둠)
}

_LANG_COLORS = {
    "EN": (50,  92, 200),
    "JP": (219, 68,  85),
    "CN": (200, 50,  50),
    "VN": (218, 165, 32),
    "ES": (230, 126, 34),
}

_LANG_NAMES = {
    "EN": "English",
    "JP": "日本語",
    "CN": "中文",
    "VN": "Tiếng Việt",
    "ES": "Español",
}

_PILL_TEXT = {
    "EN": "KOREAN \u2192 ENGLISH",
    "JP": "\u97d3\u56fd\u8a9e \u2192 \u65e5\u672c\u8a9e",
    "CN": "\u97e9\u8bed \u2192 \u4e2d\u6587",
    "VN": "Ti\u1ebfng H\u00e0n \u2192 Ti\u1ebfng Vi\u1ec7t",
    "ES": "Coreano \u2192 Espa\u00f1ol",
}

def _lang_font(lang_code: str, size: int) -> ImageFont.FreeTypeFont:
    if lang_code == "JP":
        return get_font("jp", size)
    elif lang_code == "CN":
        return get_font("cn", size)
    return get_font("english", size)

def _detect_fonts():
    candidates = {
        "korean_bold": ["/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
                        "C:/Windows/Fonts/NanumGothic-Bold.ttf",
                        "C:/Windows/Fonts/malgunbd.ttf"],
        "korean":      ["/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                        "C:/Windows/Fonts/NanumGothic-Regular.ttf",
                        "C:/Windows/Fonts/malgun.ttf"],
        "english_bold":["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                        "C:/Windows/Fonts/arialbd.ttf"],
        "english":     ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                        "C:/Windows/Fonts/arial.ttf"],
        "jp":          ["/app/assets/fonts/NotoSansJP-Regular.otf",
                        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                        "C:/Windows/Fonts/NotoSansJP-Regular.otf",
                        "C:/Windows/Fonts/msgothic.ttc",
                        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                        "C:/Windows/Fonts/malgun.ttf"],
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

_FONT_PATHS = _detect_fonts()
_font_cache = {}

def get_font(key: str, size: int) -> ImageFont.FreeTypeFont:
    ck = (key, size)
    if ck not in _font_cache:
        path = _FONT_PATHS.get(key, _FONT_PATHS["english"])
        try:
            _font_cache[ck] = ImageFont.truetype(path, size)
        except Exception:
            _font_cache[ck] = ImageFont.load_default()
    return _font_cache[ck]

def get_illustration_path(word: dict) -> str | None:
    w  = word["word"]
    lv = word["level"]
    # 구 형식: lv{level}/{word}/word.png
    old_path = _app_path(f"assets/illustrations/lv{lv}/{w}/word.png")
    if os.path.exists(old_path):
        return old_path
    # 신 형식: lv{level}/{id}_{word}/word.png
    lv_dir = _app_path(f"assets/illustrations/lv{lv}")
    if os.path.isdir(lv_dir):
        for entry in os.listdir(lv_dir):
            parts = entry.split("_", 1)
            if len(parts) == 2 and parts[0].isdigit() and parts[1] == w:
                p = os.path.join(lv_dir, entry, "word.png")
                if os.path.exists(p):
                    return p
    for p in [_app_path(f"assets/illustrations/{w}/word.png"),
              _app_path(f"assets/illustrations/lv{lv}/{w}.png"),
              _app_path(f"assets/illustrations/{w}.png")]:
        if os.path.exists(p):
            return p
    return None

def _rounded_rect(img: Image.Image, x1, y1, x2, y2, radius, fill):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=(*fill, 255))
    img.paste(ov, mask=ov.split()[3])

def _paste_rounded(base: Image.Image, src: Image.Image,
                   x: int, y: int, w: int, h: int, radius: int):
    src_r = src.resize((w, h), Image.LANCZOS).convert("RGBA")
    mask  = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], radius=radius, fill=255)
    tmp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    tmp.paste(src_r, (0, 0))
    tmp.putalpha(mask)
    base.paste(tmp, (x, y), mask=tmp.split()[3])


def make_thumbnail(word: dict, output_path: str):
    img  = Image.new("RGB", (TW, TH), C["bg"])
    draw = ImageDraw.Draw(img)

    lang_code  = word.get("language", "EN").upper()
    lang_color = _LANG_COLORS.get(lang_code, C["accent"])
    pill_text  = _PILL_TEXT.get(lang_code, "KOREAN \u2192 ENGLISH")
    cx         = TW // 2

    # ── 흰 카드 ──────────────────────────────────────────────
    card_x, card_y = 22, 28
    card_w = TW - card_x * 2   # 676
    card_h = 1210
    _rounded_rect(img, card_x, card_y, card_x + card_w, card_y + card_h,
                  radius=44, fill=C["card_bg"])
    draw = ImageDraw.Draw(img)

    # ── ① TOPIK LV.X ─────────────────────────────────────────
    font_topik = get_font("english_bold", 36)
    topik_cy   = card_y + 75
    draw.text((cx, topik_cy), f"TOPIK  LV.{word['level']}",
              font=font_topik, fill=C["accent_warm"], anchor="mm")

    # ── ② 단어 ID ─────────────────────────────────────────────
    font_id = get_font("english_bold", 44)
    id_cy   = topik_cy + 55
    draw.text((cx, id_cy), f"{word['id']:03d}",
              font=font_id, fill=C["accent_warm"], anchor="mm")

    # ── ③ 한국어 단어 (초대형) ───────────────────────────────
    word_text = word["word"]
    n = len(word_text)
    if   n == 1: word_size = 260
    elif n == 2: word_size = 220
    elif n == 3: word_size = 190
    elif n == 4: word_size = 158
    elif n == 5: word_size = 132
    elif n == 6: word_size = 112
    else:        word_size = 96

    font_word = get_font("korean_bold", word_size)
    wb = draw.textbbox((0, 0), word_text, font=font_word)
    while wb[2] - wb[0] > card_w - 50 and word_size > 64:
        word_size -= 8
        font_word = get_font("korean_bold", word_size)
        wb = draw.textbbox((0, 0), word_text, font=font_word)

    word_cy  = id_cy + 52 + word_size // 2
    draw.text((cx, word_cy), word_text,
              font=font_word, fill=C["accent"], anchor="mm")
    word_bot = word_cy + word_size // 2

    # ── ④ 뜻 (meaning) ───────────────────────────────────────
    font_meaning = _lang_font(lang_code, 44)
    meaning_cy   = word_bot + 38
    draw.text((cx, meaning_cy), word["meaning"],
              font=font_meaning, fill=C["text_muted"], anchor="mm")
    mb = draw.textbbox((0, 0), word["meaning"], font=font_meaning)
    meaning_bot = meaning_cy + (mb[3] - mb[1]) // 2

    # ── ⑤ 언어 pill 배너 ─────────────────────────────────────
    pill_top = meaning_bot + 44
    pill_h   = 80
    pill_x1  = card_x + 22
    pill_x2  = card_x + card_w - 22
    pill_ov  = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(pill_ov).rounded_rectangle(
        [pill_x1, pill_top, pill_x2, pill_top + pill_h],
        radius=pill_h // 2, fill=(*lang_color, 255)
    )
    img.paste(pill_ov, mask=pill_ov.split()[3])
    draw = ImageDraw.Draw(img)

    if lang_code == "JP":
        font_pill = get_font("jp", 40)
    elif lang_code == "CN":
        font_pill = get_font("cn", 40)
    else:
        font_pill = get_font("english_bold", 40)
    draw.text((cx, pill_top + pill_h // 2), pill_text,
              font=font_pill, fill=(255, 255, 255, 255), anchor="mm")

    # ── ⑥ 일러스트 카드 ──────────────────────────────────────
    ill_x   = card_x + 22
    ill_top_abs = pill_top + pill_h + 24
    ill_w   = card_w - 44
    ill_bot = card_y + card_h - 22
    ill_h   = ill_bot - ill_top_abs

    _rounded_rect(img, ill_x, ill_top_abs, ill_x + ill_w, ill_bot,
                  radius=32, fill=C["ill_bg"])
    draw = ImageDraw.Draw(img)

    ill_path = get_illustration_path(word)
    if ill_path:
        try:
            ill = Image.open(ill_path).convert("RGBA")
            iw, ih = ill.size
            sq     = min(iw, ih)
            left   = (iw - sq) // 2
            top    = (ih - sq) // 2
            ill    = ill.crop((left, top, left + sq, top + sq))
            fit    = min(ill_w, ill_h)
            px     = ill_x + (ill_w - fit) // 2
            py     = ill_top_abs + (ill_h - fit) // 2
            _paste_rounded(img, ill, px, py, fit, fit, radius=24)
        except Exception as e:
            print(f"  [WARN] 일러스트 로드 실패: {e}")
            _draw_placeholder(img, draw, ill_x, ill_top_abs, ill_w, ill_h, word_text)
    else:
        _draw_placeholder(img, draw, ill_x, ill_top_abs, ill_w, ill_h, word_text)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    print(f"  \u2713 {word['word']} ({lang_code}) \u2192 {output_path}")


def _draw_placeholder(img, draw, x, y, w, h, text):
    font_ph = get_font("korean", 60)
    draw.text((x + w // 2, y + h // 2), text,
              font=font_ph, fill=C["text_muted"], anchor="mm")


def make_thumbnail_landscape(word: dict, output_path: str):
    """가로형 YouTube 썸네일 1280×720 — 좌측 텍스트 + 우측 일러스트"""
    LW, LH = 1280, 720
    img  = Image.new("RGB", (LW, LH), C["bg"])
    draw = ImageDraw.Draw(img)

    lang_code  = word.get("language", "EN").upper()
    lang_color = _LANG_COLORS.get(lang_code, C["accent"])
    pill_text  = _PILL_TEXT.get(lang_code, "KOREAN \u2192 ENGLISH")

    # ── 레이아웃 ──────────────────────────────────────────────
    MARGIN   = 52
    SPLIT_X  = 560          # 좌측 텍스트 컬럼 끝 (44%)
    ILL_PAD  = 30
    ILL_SIZE = min(LH - MARGIN * 2, LW - SPLIT_X - ILL_PAD - MARGIN)  # 최대 정사각형

    left_cx = MARGIN + (SPLIT_X - MARGIN) // 2
    right_x = SPLIT_X + ILL_PAD
    right_w = LW - right_x - MARGIN
    ill_x   = right_x + (right_w - ILL_SIZE) // 2
    ill_y   = (LH - ILL_SIZE) // 2

    # ── 일러스트 배경 카드 ────────────────────────────────────
    _rounded_rect(img, ill_x - 12, ill_y - 12,
                  ill_x + ILL_SIZE + 12, ill_y + ILL_SIZE + 12,
                  radius=44, fill=C["ill_bg"])
    draw = ImageDraw.Draw(img)

    # ── 일러스트 ──────────────────────────────────────────────
    ill_path = get_illustration_path(word)
    if ill_path:
        try:
            ill  = Image.open(ill_path).convert("RGBA")
            iw, ih = ill.size
            sq   = min(iw, ih)
            ill  = ill.crop(((iw-sq)//2, (ih-sq)//2, (iw+sq)//2, (ih+sq)//2))
            _paste_rounded(img, ill, ill_x, ill_y, ILL_SIZE, ILL_SIZE, radius=34)
        except Exception as e:
            print(f"  [WARN] 일러스트 로드 실패: {e}")
            _draw_placeholder(img, ImageDraw.Draw(img), ill_x, ill_y, ILL_SIZE, ILL_SIZE, word["word"])
    else:
        _draw_placeholder(img, ImageDraw.Draw(img), ill_x, ill_y, ILL_SIZE, ILL_SIZE, word["word"])
    draw = ImageDraw.Draw(img)

    # ── 텍스트 그룹 — 수직 중앙 정렬 ─────────────────────────
    word_text = word["word"]
    n = len(word_text)
    avail_w = SPLIT_X - MARGIN * 2
    if   n == 1: word_size = 220
    elif n == 2: word_size = 200
    elif n == 3: word_size = 172
    elif n == 4: word_size = 148
    elif n == 5: word_size = 126
    elif n == 6: word_size = 108
    else:        word_size =  92

    font_word = get_font("korean_bold", word_size)
    wb = draw.textbbox((0, 0), word_text, font=font_word)
    while (wb[2] - wb[0]) > avail_w and word_size > 64:
        word_size -= 10
        font_word = get_font("korean_bold", word_size)
        wb = draw.textbbox((0, 0), word_text, font=font_word)

    TOPIK_H   = 36
    ID_H      = 46
    MEANING_H = 42
    PILL_H    = 68
    group_h   = TOPIK_H + 12 + ID_H + 14 + word_size + 18 + MEANING_H + 28 + PILL_H
    y         = (LH - group_h) // 2

    # ① TOPIK LV.X
    draw.text((left_cx, y + TOPIK_H // 2), f"TOPIK  LV.{word['level']}",
              font=get_font("english_bold", TOPIK_H), fill=C["accent_warm"], anchor="mm")
    y += TOPIK_H + 12

    # ② ID
    draw.text((left_cx, y + ID_H // 2), f"{word['id']:03d}",
              font=get_font("english_bold", ID_H), fill=C["accent_warm"], anchor="mm")
    y += ID_H + 14

    # ③ 한국어 단어 (lang_color 적용)
    draw.text((left_cx, y + word_size // 2), word_text,
              font=font_word, fill=lang_color, anchor="mm")
    y += word_size + 18

    # ④ 뜻
    draw.text((left_cx, y + MEANING_H // 2), word["meaning"],
              font=_lang_font(lang_code, MEANING_H), fill=C["text_muted"], anchor="mm")
    y += MEANING_H + 28

    # ⑤ 언어 pill
    pill_x1 = MARGIN
    pill_x2 = SPLIT_X - MARGIN // 2
    pill_ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(pill_ov).rounded_rectangle(
        [pill_x1, y, pill_x2, y + PILL_H], radius=PILL_H // 2, fill=(*lang_color, 255)
    )
    img.paste(pill_ov, mask=pill_ov.split()[3])
    draw = ImageDraw.Draw(img)

    pill_fs = 32 if lang_code not in ("JP", "CN") else 28
    if lang_code == "JP":   font_pill = get_font("jp", pill_fs)
    elif lang_code == "CN": font_pill = get_font("cn", pill_fs)
    else:                   font_pill = get_font("english_bold", pill_fs)
    draw.text(((pill_x1 + pill_x2) // 2, y + PILL_H // 2), pill_text,
              font=font_pill, fill=(255, 255, 255), anchor="mm")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    print(f"  \u2713 {word['word']} ({lang_code}) [landscape 1280x720] \u2192 {output_path}")


def make_thumbnail_for_style(word: dict, output_path: str, style: str = "portrait"):
    """style='portrait'(기존 세로형) 또는 'landscape'(가로형 디자인 세로 변환)"""
    if style == "landscape":
        make_thumbnail_landscape(word, output_path)
    else:
        make_thumbnail(word, output_path)


_DAILY_KOREAN = {
    "EN": "Daily Korean",
    "JP": "Daily Korean",
    "CN": "Daily Korean",
    "VN": "Daily Korean",
    "ES": "Daily Korean",
}

_CONV_SUBTITLE = {
    "EN": "Today's Korean Conversation",
    "JP": "今日の韓国語会話",
    "CN": "今日韩语会话",
    "VN": "Hội Thoại Tiếng Hàn Hôm Nay",
    "ES": "Conversación Coreana de Hoy",
}


def _get_situation_title(theme: dict, lang: str) -> str:
    """언어별 상황명 반환 (줄바꿈 처리 포함)"""
    lang_up = lang.upper()
    key_map = {"JP": "situation_jp", "CN": "situation_cn",
               "VN": "situation_vn", "ES": "situation_es"}
    raw = theme.get(key_map.get(lang_up, ""), "") or theme.get("situation_en", "")
    # " — " 또는 " - " 으로 분리해 줄바꿈
    for sep in [" \u2014 ", " — ", " - "]:
        if sep in raw:
            return raw.replace(sep, "\n", 1)
    return raw


def make_conv_thumbnail(theme: dict, lang: str, output_path: str):
    """회화 YouTube 썸네일 1280×720 — 이미지 #52 디자인
    왼쪽 수직 띠 + 로고/제목/pill + 우측 일러스트 카드
    """
    LW, LH = 1280, 720

    # ── 색상 ─────────────────────────────────────────────────
    BG_BLUE    = (160, 208, 220)   # 배경 #a0d0dc
    TITLE_COL  = ( 15,  25,  55)   # 대제목 (거의 검정)
    SUBTLE_COL = ( 40,  60,  90)   # 서브타이틀
    WHITE      = (255, 255, 255)

    lang_up   = lang.upper()
    lang_color = _LANG_COLORS.get(lang_up, (42, 98, 196))  # 언어 고유 색

    img  = Image.new("RGB", (LW, LH), BG_BLUE)
    draw = ImageDraw.Draw(img)

    # ── 왼쪽 수직 띠 (언어 고유 색) ──────────────────────────
    STRIPE_W = 18
    draw.rectangle([0, 0, STRIPE_W, LH], fill=lang_color)

    # ── 레이아웃 ──────────────────────────────────────────────
    PAD_L  = STRIPE_W + 40   # 텍스트 왼쪽 여백
    SPLIT  = 590              # 좌/우 분할 X
    PAD_R  = 28               # 우측 여백

    right_w = LW - SPLIT - PAD_R
    ill_size = min(LH - 80, right_w)
    ill_x    = SPLIT + (right_w - ill_size) // 2
    ill_y    = (LH - ill_size) // 2

    # ── 일러스트 (흰 외곽 카드 없이 바로 붙이기) ─────────────
    ill_file = _app_path(f"assets/phrase_illustrations/sit_{theme['id']}/intro.png")
    if os.path.exists(ill_file):
        try:
            ill = Image.open(ill_file).convert("RGBA")
            iw, ih = ill.size
            sq  = min(iw, ih)
            ill = ill.crop(((iw-sq)//2, (ih-sq)//2, (iw+sq)//2, (ih+sq)//2))
            _paste_rounded(img, ill, ill_x, ill_y, ill_size, ill_size, radius=34)
        except Exception as e:
            print(f"  [WARN] 회화 일러스트 로드 실패: {e}")
    draw = ImageDraw.Draw(img)

    # ── 좌측 콘텐츠 수직 중앙 배치 ───────────────────────────
    avail_w  = SPLIT - PAD_L - 20   # 텍스트 가용 너비
    content_cx = PAD_L + avail_w // 2

    # ① HELLO WORDS 로고 이미지 (언어별 고유 색으로 틴팅)
    logo_path  = _app_path("assets/logos/hellowords_how_logo.png")
    LOGO_H     = 52
    logo_color = lang_color
    logo_img   = None
    if os.path.exists(logo_path):
        try:
            logo_raw = Image.open(logo_path).convert("RGBA")
            lw_orig, lh_orig = logo_raw.size
            logo_w   = int(LOGO_H * lw_orig / lh_orig)
            logo_raw = logo_raw.resize((logo_w, LOGO_H), Image.LANCZOS)
            # 알파 채널 보존 + 언어 색으로 틴팅
            _, _, _, a = logo_raw.split()
            tinted = Image.new("RGBA", logo_raw.size, (*logo_color, 255))
            tinted.putalpha(a)
            logo_img = tinted
        except Exception:
            logo_img = None

    # ② Daily Korean 서브타이틀
    DAILY_H   = 30
    font_daily = get_font("english", DAILY_H)

    # 언어별 폰트 키
    _title_fkey = {"JP": "jp", "CN": "cn"}.get(lang_up, "english_bold")
    _conv_fkey  = {"JP": "jp", "CN": "cn"}.get(lang_up, "english")

    # ③ 상황명 (큰 제목, 줄바꿈 가능)
    situation = _get_situation_title(theme, lang)
    lines     = situation.split("\n")
    TITLE_H   = 90
    font_title = get_font(_title_fkey, TITLE_H)
    for line in lines:
        wb = draw.textbbox((0, 0), line, font=font_title)
        while (wb[2] - wb[0]) > avail_w and TITLE_H > 48:
            TITLE_H   -= 6
            font_title = get_font(_title_fkey, TITLE_H)
            wb = draw.textbbox((0, 0), line, font=font_title)

    # ④ Today's Korean Conversation
    CONV_H    = 28
    font_conv = get_font(_conv_fkey, CONV_H)

    # ⑤ Pill
    PILL_H  = 62
    PILL_FS = 30

    # 전체 높이 계산 (gap 포함)
    GAP1 = 6     # 로고~Daily Korean
    GAP2 = 28    # Daily Korean~제목
    GAP3 = 20    # 제목~Today's
    GAP4 = 24    # Today's~pill
    title_block_h = TITLE_H * len(lines) + (TITLE_H * 0.15) * (len(lines) - 1)
    total_h = (LOGO_H + GAP1 + DAILY_H + GAP2
               + title_block_h + GAP3 + CONV_H + GAP4 + PILL_H)
    y = int((LH - total_h) // 2)

    # ① 로고
    if logo_img:
        lx = content_cx - logo_img.size[0] // 2
        img.paste(logo_img, (lx, y), mask=logo_img.split()[3])
    else:
        draw.text((content_cx, y + LOGO_H // 2), "HELLO WORDS",
                  font=get_font("english_bold", LOGO_H - 4), fill=logo_color, anchor="mm")
    y += LOGO_H + GAP1

    # ② Daily Korean
    draw.text((content_cx, y + DAILY_H // 2), _DAILY_KOREAN.get(lang_up, "Daily Korean"),
              font=font_daily, fill=SUBTLE_COL, anchor="mm")
    y += DAILY_H + GAP2

    # ③ 상황명 (줄별 렌더)
    for line in lines:
        draw.text((content_cx, y + TITLE_H // 2), line,
                  font=font_title, fill=TITLE_COL, anchor="mm")
        y += int(TITLE_H * 1.15)
    y += GAP3 - int(TITLE_H * 0.15)   # 마지막 줄 보정

    # ④ Today's Korean Conversation
    draw.text((content_cx, y + CONV_H // 2),
              _CONV_SUBTITLE.get(lang_up, "Today's Korean Conversation"),
              font=font_conv, fill=SUBTLE_COL, anchor="mm")
    y += CONV_H + GAP4

    # ⑤ Pill
    pill_w   = avail_w
    pill_x1  = PAD_L
    pill_x2  = PAD_L + pill_w
    pill_ov  = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(pill_ov).rounded_rectangle(
        [pill_x1, y, pill_x2, y + PILL_H],
        radius=PILL_H // 2, fill=(*lang_color, 255)
    )
    img.paste(pill_ov, mask=pill_ov.split()[3])
    draw = ImageDraw.Draw(img)

    pill_text = _PILL_TEXT.get(lang_up, "KOREAN \u2192 ENGLISH")
    if lang_up == "JP":   fp = get_font("jp", PILL_FS)
    elif lang_up == "CN": fp = get_font("cn", PILL_FS)
    else:                 fp = get_font("english_bold", PILL_FS)
    draw.text(((pill_x1 + pill_x2) // 2, y + PILL_H // 2),
              pill_text, font=fp, fill=WHITE, anchor="mm")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    print(f"  \u2713 conv sit_{theme['id']} ({lang_up}) [1280x720] \u2192 {output_path}")


def main():
    parser = argparse.ArgumentParser(description="TOPIK YouTube 썸네일 생성 (720×1280)")
    parser.add_argument("--db",     default="/app/data/LanguageTest/words_db.json")
    parser.add_argument("--id",     type=int, default=None)
    parser.add_argument("--all",    action="store_true")
    parser.add_argument("--output", default="/app/output/thumbnails/")
    parser.add_argument("--style",  default="portrait",
                        choices=["portrait", "landscape"],
                        help="portrait=기존 세로형, landscape=가로형 디자인 세로 변환")
    args = parser.parse_args()

    with open(args.db, encoding="utf-8") as f:
        db = json.load(f)
    words = db if isinstance(db, list) else db.get("words", [])

    if args.id is not None:
        words = [w for w in words if w["id"] == args.id]
        if not words:
            print(f"[ERROR] ID {args.id} 단어를 찾을 수 없습니다.")
            sys.exit(1)
    elif not args.all:
        parser.print_help()
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)
    total = len(words)
    for i, word in enumerate(words, 1):
        fname    = f"{word['id']:04d}_{word['word']}.png"
        out_path = os.path.join(args.output, fname)
        print(f"[{i:4d}/{total}] {word['word']:10s} LV.{word['level']}", end=" ")
        try:
            make_thumbnail_for_style(word, out_path, style=args.style)
        except Exception as e:
            print(f"  [FAIL] {e}")

    print(f"\n완료: {total}개 썸네일 ({args.style}) → {args.output}")


if __name__ == "__main__":
    main()
