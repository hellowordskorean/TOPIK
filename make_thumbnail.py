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

_APP_BASE = os.environ.get("APP_BASE", "/app")

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
    candidates = [
        _app_path(f"assets/illustrations/lv{lv}/{w}/word.png"),
        _app_path(f"assets/illustrations/{w}/word.png"),
        _app_path(f"assets/illustrations/lv{lv}/{w}.png"),
        _app_path(f"assets/illustrations/{w}.png"),
    ]
    for p in candidates:
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


def main():
    parser = argparse.ArgumentParser(description="TOPIK YouTube 썸네일 생성 (720×1280)")
    parser.add_argument("--db",     default="/app/data/LanguageTest/words_db.json")
    parser.add_argument("--id",     type=int, default=None)
    parser.add_argument("--all",    action="store_true")
    parser.add_argument("--output", default="/app/output/thumbnails/")
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
            make_thumbnail(word, out_path)
        except Exception as e:
            print(f"  [FAIL] {e}")

    print(f"\n완료: {total}개 썸네일 → {args.output}")


if __name__ == "__main__":
    main()
