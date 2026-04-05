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

    lang_code  = word.get("language", "EN")
    lang_color = _LANG_COLORS.get(lang_code, C["accent"])
    lang_name  = _LANG_NAMES.get(lang_code, lang_code)
    cx         = TW // 2

    # ── 흰 카드 (전체 배경) ───────────────────────────────────
    card_x, card_y = 22, 28
    card_w = TW - card_x * 2   # 676
    card_h = 1210
    _rounded_rect(img, card_x, card_y, card_x + card_w, card_y + card_h,
                  radius=44, fill=C["card_bg"])
    draw = ImageDraw.Draw(img)

    # ── ① 언어 배지 (대형 pill, 상단 중앙) ───────────────────
    font_lang  = get_font("english_bold", 64)
    lb         = draw.textbbox((0, 0), lang_name, font=font_lang)
    lbw        = lb[2] - lb[0] + 80   # 좌우 패딩
    lbh        = lb[3] - lb[1] + 28   # 상하 패딩
    lbx        = cx - lbw // 2
    lby        = card_y + 38
    lang_ov    = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lang_ov).rounded_rectangle(
        [lbx, lby, lbx + lbw, lby + lbh],
        radius=lbh // 2, fill=(*lang_color, 255)
    )
    img.paste(lang_ov, mask=lang_ov.split()[3])
    draw = ImageDraw.Draw(img)
    draw.text((cx, lby + lbh // 2), lang_name,
              font=font_lang, fill=C["card_bg"], anchor="mm")

    # ── ② TOPIK LV.X ─────────────────────────────────────────
    font_topik = get_font("english_bold", 44)
    topik_y    = lby + lbh + 52
    draw.text((cx, topik_y), f"TOPIK  LV.{word['level']}",
              font=font_topik, fill=C["accent_warm"], anchor="mm")

    # ── ③ 단어 ID ─────────────────────────────────────────────
    font_id = get_font("english_bold", 38)
    id_y    = topik_y + 54
    draw.text((cx, id_y), f"{word['id']:04d}",
              font=font_id, fill=C["accent_warm"], anchor="mm")

    # ── ④ 한국어 단어 (초대형) ───────────────────────────────
    word_text = word["word"]
    n = len(word_text)
    if   n == 1: word_size = 280
    elif n == 2: word_size = 240
    elif n == 3: word_size = 200
    elif n == 4: word_size = 168
    elif n == 5: word_size = 140
    elif n == 6: word_size = 118
    else:        word_size = 100

    font_word = get_font("korean_bold", word_size)
    # 카드 너비 초과 시 축소
    wb = draw.textbbox((0, 0), word_text, font=font_word)
    while wb[2] - wb[0] > card_w - 50 and word_size > 60:
        word_size -= 8
        font_word = get_font("korean_bold", word_size)
        wb = draw.textbbox((0, 0), word_text, font=font_word)

    word_y = id_y + 60 + word_size // 2 + 10
    draw.text((cx, word_y), word_text,
              font=font_word, fill=C["accent"], anchor="mm")

    # ── ⑤ 일러스트 카드 ──────────────────────────────────────
    ill_margin = 26
    ill_x      = card_x + ill_margin          # 48
    ill_top    = word_y + word_size // 2 + 30  # 단어 아래 30px
    ill_w      = card_w - ill_margin * 2       # 624
    ill_bot    = card_y + card_h - 26          # 카드 하단 26px 여백
    ill_h      = ill_bot - ill_top

    # 일러스트 배경 (살짝 다른 크림)
    _rounded_rect(img, ill_x, ill_top, ill_x + ill_w, ill_bot,
                  radius=32, fill=C["ill_bg"])
    draw = ImageDraw.Draw(img)

    ill_path = get_illustration_path(word)
    if ill_path:
        try:
            ill = Image.open(ill_path).convert("RGBA")
            # 정사각형으로 크롭 후 카드에 맞게 fit
            iw, ih = ill.size
            sq     = min(iw, ih)
            left   = (iw - sq) // 2
            top    = (ih - sq) // 2
            ill    = ill.crop((left, top, left + sq, top + sq))
            # ill_h 기준으로 중앙 배치
            fit    = min(ill_w, ill_h)
            px     = ill_x + (ill_w - fit) // 2
            py     = ill_top + (ill_h - fit) // 2
            _paste_rounded(img, ill, px, py, fit, fit, radius=24)
        except Exception as e:
            print(f"  [WARN] 일러스트 로드 실패: {e}")
            _draw_placeholder(img, draw, ill_x, ill_top, ill_w, ill_h, word_text)
    else:
        _draw_placeholder(img, draw, ill_x, ill_top, ill_w, ill_h, word_text)

    draw = ImageDraw.Draw(img)

    # ── ⑥ 하단 태그라인 ──────────────────────────────────────
    font_tag = get_font("english", 22)
    tag_y    = card_y + card_h + (TH - card_y - card_h) // 2
    draw.text((cx, tag_y), "TOPIK Korean Vocabulary",
              font=font_tag, fill=C["text_muted"], anchor="mm")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    print(f"  ✓ {word['word']} ({lang_name}) → {output_path}")


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
