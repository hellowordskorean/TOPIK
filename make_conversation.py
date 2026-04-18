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
import math
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
_APP_BASE = os.environ.get("APP_BASE", str(Path(__file__).parent))

def _app_path(rel: str) -> str:
    return os.path.join(_APP_BASE, rel)

# ─── GPU/CPU 인코더 감지 ─────────────────────────────────────
def has_nvenc() -> bool:
    try:
        r = subprocess.run(
            ["ffmpeg", "-f", "lavfi", "-i", "color=size=320x240:duration=0.1:rate=30,format=yuv420p",
             "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "22", "-f", "null", "-"],
            capture_output=True, text=True, timeout=10,
        )
        return r.returncode == 0
    except Exception:
        return False

_NVENC_AVAILABLE = None

def get_video_encoder() -> list:
    global _NVENC_AVAILABLE
    if _NVENC_AVAILABLE is None:
        _NVENC_AVAILABLE = has_nvenc()
        print("  [GPU] h264_nvenc 인코딩 활성화" if _NVENC_AVAILABLE else "  [CPU] libx264 인코딩 사용")
    if _NVENC_AVAILABLE:
        return ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "22", "-b:v", "0"]
    else:
        return ["-c:v", "libx264", "-preset", "fast", "-crf", "22"]

# ─── 비디오 설정 ──────────────────────────────────────────────
W, H, FPS = 1080, 1920, 24

# ─── 색상 팔레트 (로즈-라벤더 다크) ──────────────────────────
DARK = {
    "bg":          (20,  12,  28),   # 따뜻한 딥 플럼 블랙
    "card":        (44,  26,  56),   # 딥 로즈-플럼 카드
    "card_border": (90,  55, 110),   # 소프트 퍼플 테두리
    "korean":      (255, 255, 255),  # 한국어 (흰색)
    "roman":       (255, 150, 192),  # 버블검 핑크 (발음기호)
    "translation": (232, 215, 238),  # 라벤더 화이트 (번역)
    "muted":       (138, 100, 138),  # 뮤트 라벤더 (비활성 점)
    "header":      (218, 196, 226),  # 소프트 라벤더 (헤더)
}

# ─── 캐릭터 종 목록 (generate_phrase_illustrations.py와 동일 순서 유지) ──
_CONVO_SPECIES = [
    "gray tabby cat", "black-and-white dalmatian dog", "white fluffy rabbit",
    "blue-gray elephant", "dark brown bear", "white cat with glasses",
    "black poodle", "spotted black-and-white cow", "silver-gray wolf",
    "green frog", "cream-colored hamster", "black-and-white penguin",
    "brown-and-white owl", "brown hedgehog", "dark brown otter",
    "white fluffy lamb", "dark brown dachshund", "gray-striped raccoon",
    "gray-brown capybara", "cream siamese cat", "black-and-white husky dog",
    "gray-brown squirrel", "white persian cat", "blue-gray koala",
    "black-and-white striped zebra", "white-gray spotted snow leopard cub",
    "pink-tinted axolotl", "mint-green chameleon", "white polar bear cub",
    "gray ring-tailed lemur", "black-and-white giant panda cub",
    "pink flamingo", "dark gray gorilla", "iridescent peacock",
    "white arctic fox", "gray donkey",
    "spotted yellow-and-brown baby giraffe", "black-and-white badger",
    "blue macaw parrot", "tiny gray mouse", "dark brown beaver",
    "gray meerkat", "fluffy white alpaca", "gray chinchilla",
    "black-and-white skunk", "lilac-gray sugar glider", "dark indigo tapir",
    "silver-gray mole", "teal-blue heron", "cream-colored manatee",
]

def _species_slug(species: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", species.lower()).strip("_")

def _get_supporting_species(theme_id: int) -> str:
    return _CONVO_SPECIES[theme_id % len(_CONVO_SPECIES)]

_face_cache: dict = {}

def _load_face(slug: str, size: int = 100) -> "Image.Image | None":
    """assets/characters/faces/{slug}.png 를 원형 마스크로 로드 (캐시)"""
    key = (slug, size)
    if key in _face_cache:
        return _face_cache[key]
    path = _app_path(f"assets/characters/faces/{slug}.png")
    if not os.path.exists(path):
        _face_cache[key] = None
        return None
    try:
        face = Image.open(path).convert("RGBA")
        face = face.resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
        face.putalpha(mask)
        _face_cache[key] = face
        return face
    except Exception:
        _face_cache[key] = None
        return None


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
            _app_path("assets/fonts/NotoSansJP-Regular.otf"),   # assets 폴더 우선
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
        "vn": [
            _app_path("assets/fonts/NotoSans-Regular.ttf"),  # 베트남어 발음기호 지원
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/NotoSans-Regular.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ],
        # 한국어+일본어+중국어+베트남어+라틴 모두 지원하는 범용 폰트 (TIP 텍스트용)
        "multi": [
            "C:/Windows/Fonts/malgunbd.ttf",
            "C:/Windows/Fonts/malgun.ttf",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "C:/Windows/Fonts/msyh.ttc",
        ],
    }
    result = {}
    for key, paths in candidates.items():
        result[key] = next((p for p in paths if os.path.exists(p)), paths[0])
    return result

_fonts_map = _detect_fonts()
_font_cache = {}

# ─── 한국어 → 카타카나 변환 (일본어 학습자용) ──────────────────
_HG_BASE = 0xAC00
_CHO_L = list('ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ')
_JUNG_L = list('ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ')
_JONG_L = ['','ㄱ','ㄲ','ㄳ','ㄴ','ㄵ','ㄶ','ㄷ','ㄹ','ㄺ','ㄻ','ㄼ','ㄽ','ㄾ','ㄿ','ㅀ','ㅁ','ㅂ','ㅄ','ㅅ','ㅆ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']

# 중성 → 모음 카타카나 분류 키
_VKEY = {
    'ㅏ':'ア','ㅐ':'エ','ㅑ':'ヤ','ㅒ':'イェ','ㅓ':'オ','ㅔ':'エ',
    'ㅕ':'ヨ','ㅖ':'イェ','ㅗ':'オ','ㅘ':'ワ','ㅙ':'ウェ','ㅚ':'ウェ',
    'ㅛ':'ヨ','ㅜ':'ウ','ㅝ':'ウォ','ㅞ':'ウェ','ㅟ':'ウィ',
    'ㅠ':'ユ','ㅡ':'ウ','ㅢ':'ウィ','ㅣ':'イ',
}
# 초성 + 중성키 → 카타카나
_CJ = {
    'ㄱ':{'ア':'ガ','イ':'ギ','ウ':'グ','エ':'ゲ','オ':'ゴ','ヤ':'ギャ','ヨ':'ギョ','ユ':'ギュ','ワ':'グァ','ウォ':'グォ','ウェ':'グェ','ウィ':'グィ','イェ':'ギェ'},
    'ㄲ':{'ア':'カ','イ':'キ','ウ':'ク','エ':'ケ','オ':'コ','ヤ':'キャ','ヨ':'キョ','ユ':'キュ','ワ':'クァ','ウォ':'クォ','ウェ':'クェ','ウィ':'クィ','イェ':'キェ'},
    'ㄴ':{'ア':'ナ','イ':'ニ','ウ':'ヌ','エ':'ネ','オ':'ノ','ヤ':'ニャ','ヨ':'ニョ','ユ':'ニュ','ワ':'ナ','ウォ':'ノ','ウェ':'ネ','ウィ':'ニ','イェ':'ニェ'},
    'ㄷ':{'ア':'ダ','イ':'ディ','ウ':'ドゥ','エ':'デ','オ':'ド','ヤ':'ヂャ','ヨ':'ヂョ','ユ':'ヂュ','ワ':'ドァ','ウォ':'ドォ','ウェ':'デ','ウィ':'ディ','イェ':'デ'},
    'ㄸ':{'ア':'タ','イ':'ティ','ウ':'トゥ','エ':'テ','オ':'ト','ヤ':'チャ','ヨ':'チョ','ユ':'チュ','ワ':'タ','ウォ':'ト','ウェ':'テ','ウィ':'ティ','イェ':'テ'},
    'ㄹ':{'ア':'ラ','イ':'リ','ウ':'ル','エ':'レ','オ':'ロ','ヤ':'リャ','ヨ':'リョ','ユ':'リュ','ワ':'ラ','ウォ':'ロ','ウェ':'レ','ウィ':'リ','イェ':'レ'},
    'ㅁ':{'ア':'マ','イ':'ミ','ウ':'ム','エ':'メ','オ':'モ','ヤ':'ミャ','ヨ':'ミョ','ユ':'ミュ','ワ':'マ','ウォ':'モ','ウェ':'メ','ウィ':'ミ','イェ':'メ'},
    'ㅂ':{'ア':'バ','イ':'ビ','ウ':'ブ','エ':'ベ','オ':'ボ','ヤ':'ビャ','ヨ':'ビョ','ユ':'ビュ','ワ':'バ','ウォ':'ボ','ウェ':'ベ','ウィ':'ビ','イェ':'ベ'},
    'ㅃ':{'ア':'パ','イ':'ピ','ウ':'プ','エ':'ペ','オ':'ポ','ヤ':'ピャ','ヨ':'ピョ','ユ':'ピュ','ワ':'パ','ウォ':'ポ','ウェ':'ペ','ウィ':'ピ','イェ':'ペ'},
    'ㅅ':{'ア':'サ','イ':'シ','ウ':'ス','エ':'セ','オ':'ソ','ヤ':'シャ','ヨ':'ショ','ユ':'シュ','ワ':'サ','ウォ':'ソ','ウェ':'セ','ウィ':'シ','イェ':'シェ'},
    'ㅆ':{'ア':'ッサ','イ':'ッシ','ウ':'ッス','エ':'ッセ','オ':'ッソ','ヤ':'ッシャ','ヨ':'ッショ','ユ':'ッシュ','ワ':'ッサ','ウォ':'ッソ','ウェ':'ッセ','ウィ':'ッシ','イェ':'ッシェ'},
    'ㅇ':{'ア':'ア','イ':'イ','ウ':'ウ','エ':'エ','オ':'オ','ヤ':'ヤ','ヨ':'ヨ','ユ':'ユ','ワ':'ワ','ウォ':'ウォ','ウェ':'ウェ','ウィ':'ウィ','イェ':'イェ'},
    'ㅈ':{'ア':'ジャ','イ':'ジ','ウ':'ジュ','エ':'ジェ','オ':'ジョ','ヤ':'ジャ','ヨ':'ジョ','ユ':'ジュ','ワ':'ジャ','ウォ':'ジョ','ウェ':'ジェ','ウィ':'ジ','イェ':'ジェ'},
    'ㅉ':{'ア':'ッジャ','イ':'ッジ','ウ':'ッジュ','エ':'ッジェ','オ':'ッジョ','ヤ':'ッジャ','ヨ':'ッジョ','ユ':'ッジュ','ワ':'ッジャ','ウォ':'ッジョ','ウェ':'ッジェ','ウィ':'ッジ','イェ':'ッジェ'},
    'ㅊ':{'ア':'チャ','イ':'チ','ウ':'チュ','エ':'チェ','オ':'チョ','ヤ':'チャ','ヨ':'チョ','ユ':'チュ','ワ':'チャ','ウォ':'チョ','ウェ':'チェ','ウィ':'チ','イェ':'チェ'},
    'ㅋ':{'ア':'カ','イ':'キ','ウ':'ク','エ':'ケ','オ':'コ','ヤ':'キャ','ヨ':'キョ','ユ':'キュ','ワ':'クァ','ウォ':'クォ','ウェ':'クェ','ウィ':'クィ','イェ':'キェ'},
    'ㅌ':{'ア':'タ','イ':'ティ','ウ':'トゥ','エ':'テ','オ':'ト','ヤ':'チャ','ヨ':'チョ','ユ':'チュ','ワ':'タ','ウォ':'ト','ウェ':'テ','ウィ':'ティ','イェ':'テ'},
    'ㅍ':{'ア':'パ','イ':'ピ','ウ':'プ','エ':'ペ','オ':'ポ','ヤ':'ピャ','ヨ':'ピョ','ユ':'ピュ','ワ':'パ','ウォ':'ポ','ウェ':'ペ','ウィ':'ピ','イェ':'ペ'},
    'ㅎ':{'ア':'ハ','イ':'ヒ','ウ':'フ','エ':'ヘ','オ':'ホ','ヤ':'ヒャ','ヨ':'ヒョ','ユ':'ヒュ','ワ':'ハ','ウォ':'ホ','ウェ':'ヘ','ウィ':'ヒ','イェ':'ヘ'},
}
_JONG_K = {
    '':'','ㄱ':'ク','ㄲ':'ク','ㄳ':'ク','ㄴ':'ン','ㄵ':'ン','ㄶ':'ン','ㄷ':'ッ','ㄹ':'ル',
    'ㄺ':'ル','ㄻ':'ム','ㄼ':'ル','ㄽ':'ル','ㄾ':'ル','ㄿ':'プ','ㅀ':'ル','ㅁ':'ム',
    'ㅂ':'プ','ㅄ':'プ','ㅅ':'ッ','ㅆ':'ッ','ㅇ':'ング','ㅈ':'ッ','ㅊ':'ッ','ㅋ':'ク',
    'ㅌ':'ッ','ㅍ':'プ','ㅎ':'ッ',
}

def _hangul_to_katakana(text: str) -> str:
    """한글 텍스트 → 카타카나 발음 가이드"""
    result = []
    for ch in text:
        code = ord(ch)
        if 0xAC00 <= code <= 0xD7A3:
            off = code - _HG_BASE
            cho  = _CHO_L[off // (21 * 28)]
            jung = _JUNG_L[(off % (21 * 28)) // 28]
            jong = _JONG_L[off % 28]
            vk = _VKEY.get(jung, 'ア')
            row = _CJ.get(cho, {})
            syl = row.get(vk, row.get('ア', '') + vk)
            result.append(syl + _JONG_K.get(jong, ''))
        elif ch == ' ':
            result.append('・')
        elif ch in '?!.,~':
            result.append(ch)
        else:
            result.append(ch)
    return ''.join(result)

def _get_phonetic(ko_text: str, roman: str, lang: str) -> str:
    """언어별 발음 표기 반환. JP → 카타카나, 나머지 → 로마자"""
    if lang.upper() == "JP":
        return _hangul_to_katakana(ko_text)
    return roman

# ─── 나/상대방 라벨 (학습자 언어별) ──────────────────────────────
_SPEAKER_LABELS = {
    "EN": ("Me", "Speaker"),
    "JP": ("私", "相手"),
    "CN": ("我", "对方"),
    "VN": ("Tôi", "Đối phương"),
    "ES": ("Yo", "Tú"),
    "KO": ("나", "상대방"),
}

# ─── 언어별 UI 문자열 ─────────────────────────────────────────
_LANG_UI = {
    "EN": {
        "intro_sub":     "Today's Korean Conversation",
        "branding":      "Hellowords · Daily Korean",
        "outro_title":   "Today's Expressions",
        "outro_cta":     "Subscribe for Daily Korean!",
        "reels_more_ko": "더 많은 내용은 유튜브 본편에서 확인하세요",
        "reels_more_tl": "Watch the full video on YouTube for more!",
    },
    "JP": {
        "intro_sub":     "今日の韓国語会話",
        "branding":      "Hellowords · 毎日韓国語",
        "outro_title":   "今日の表現",
        "outro_cta":     "毎日韓国語を勉強しよう！",
        "reels_more_ko": "더 많은 내용은 유튜브 본편에서 확인하세요",
        "reels_more_tl": "もっと見たい方はYouTube本編をチェック！",
    },
    "CN": {
        "intro_sub":     "今日韩语会话",
        "branding":      "Hellowords · 每日韩语",
        "outro_title":   "今日学到的表达",
        "outro_cta":     "订阅，每天学韩语！",
        "reels_more_ko": "더 많은 내용은 유튜브 본편에서 확인하세요",
        "reels_more_tl": "更多内容请观看YouTube完整版！",
    },
    "VN": {
        "intro_sub":     "Hội thoại tiếng Hàn hôm nay",
        "branding":      "Hellowords · Tiếng Hàn mỗi ngày",
        "outro_title":   "Biểu đạt hôm nay",
        "outro_cta":     "Đăng ký để học tiếng Hàn mỗi ngày!",
        "reels_more_ko": "더 많은 내용은 유튜브 본편에서 확인하세요",
        "reels_more_tl": "Xem đầy đủ trên YouTube để học thêm!",
    },
    "ES": {
        "intro_sub":     "Conversación coreana de hoy",
        "branding":      "Hellowords · Coreano diario",
        "outro_title":   "Expresiones de hoy",
        "outro_cta":     "¡Suscríbete para aprender coreano!",
        "reels_more_ko": "더 많은 내용은 유튜브 본편에서 확인하세요",
        "reels_more_tl": "¡Mira el video completo en YouTube para más!",
    },
}

def _ui(lang: str, key: str) -> str:
    """언어별 UI 문자열 반환. 없으면 한국어 기본값."""
    _KO_FALLBACK = {
        "intro_sub":     "오늘의 한국어 회화",
        "branding":      "Hellowords · 매일 한국어",
        "outro_title":   "오늘 배운 표현",
        "outro_cta":     "구독하고 매일 한국어 공부!",
        "reels_more_ko": "더 많은 내용은 유튜브 본편에서 확인하세요",
        "reels_more_tl": "더 많은 내용은 유튜브 본편에서 확인하세요",
    }
    return _LANG_UI.get(lang.upper(), {}).get(key, _KO_FALLBACK.get(key, ""))

def get_font(key: str, size: int) -> ImageFont.FreeTypeFont:
    cache_key = (key, size)
    if cache_key not in _font_cache:
        path = _fonts_map.get(key, _fonts_map["regular"])
        try:
            _font_cache[cache_key] = ImageFont.truetype(path, size)
        except Exception:
            _font_cache[cache_key] = ImageFont.load_default()
    return _font_cache[cache_key]

def _fkey_for_char(ch: str, lang: str) -> str:
    """문자 유니코드 범위에 따른 폰트 키 (다국어 혼용 텍스트용)"""
    cp = ord(ch)
    # 한글 음절/자모
    if (0xAC00 <= cp <= 0xD7A3 or 0x1100 <= cp <= 0x11FF or
            0x3130 <= cp <= 0x318F or 0xA960 <= cp <= 0xA97F):
        return "korean_bold"
    # CJK 통합 한자 + 히라가나/가타카나
    if (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or
            0x3040 <= cp <= 0x30FF or 0xFF00 <= cp <= 0xFFEF or
            0x20000 <= cp <= 0x2A6DF):
        return "jp" if lang.upper() == "JP" else "cn"
    # 라틴 확장(베트남어 발음기호) U+00C0-U+024F, U+1E00-U+1EFF
    if lang.upper() == "VN" and (0x00C0 <= cp <= 0x024F or 0x1E00 <= cp <= 0x1EFF):
        return "vn"
    return _lang_font_key(lang, bold=False)


def _draw_tip_mixed(draw, img_ref, cx: int, top: int, bot: int,
                    text: str, lang: str, size: int, color: tuple, p: float) -> None:
    """다국어 혼용 TIP 텍스트를 박스 안에 중앙 배치. 문자별 폰트 자동 선택."""
    max_w   = W - 120       # 양쪽 60px 여백
    avail_h = bot - top

    def _ch_w(ch):
        return draw.textbbox((0, 0), ch, font=get_font(_fkey_for_char(ch, lang), size))[2]

    # ── 줄바꿈: 문장 단위 (CJK) / 단어 단위 (Latin) ─────────────────
    use_char = lang.upper() in ("JP", "CN")

    def _str_w(s: str) -> int:
        return sum(_ch_w(c) for c in s)

    tip_lines: list = []

    if use_char:
        # 먼저 문장 단위로 분리 (。！？；뒤 포함) → 문장 통째로 한 줄에 배치
        sentences = re.split(r'(?<=[。！？；])', text)
        sentences = [s for s in sentences if s]
        cur_line, cur_w = "", 0

        for sent in sentences:
            sw = _str_w(sent)
            if not cur_line:
                if sw <= max_w:
                    cur_line, cur_w = sent, sw
                else:
                    # 한 문장이 max_w 초과 → 글자 단위 강제 줄바꿈
                    for ch in sent:
                        cw = _ch_w(ch)
                        if cur_line and cur_w + cw > max_w:
                            tip_lines.append(cur_line)
                            cur_line, cur_w = ch, cw
                        else:
                            cur_line += ch
                            cur_w    += cw
            else:
                if cur_w + sw <= max_w:
                    cur_line += sent
                    cur_w    += sw
                else:
                    tip_lines.append(cur_line)
                    cur_line, cur_w = "", 0
                    if sw <= max_w:
                        cur_line, cur_w = sent, sw
                    else:
                        for ch in sent:
                            cw = _ch_w(ch)
                            if cur_line and cur_w + cw > max_w:
                                tip_lines.append(cur_line)
                                cur_line, cur_w = ch, cw
                            else:
                                cur_line += ch
                                cur_w    += cw
        if cur_line:
            tip_lines.append(cur_line)
    else:
        # 단어 단위 (EN/VN/ES 등)
        words = text.split()
        cur: list = []
        cur_w = 0
        for word in words:
            ww    = _str_w(word)
            sep_w = _ch_w(" ") if cur else 0
            if cur and cur_w + sep_w + ww > max_w:
                tip_lines.append(" ".join(cur))
                cur, cur_w = [word], ww
            else:
                cur.append(word)
                cur_w += sep_w + ww
        if cur:
            tip_lines.append(" ".join(cur))

    # 높이 기준 max_lines 계산 + 말줄임
    ref_fnt = get_font(_lang_font_key(lang, bold=False), size)
    lh      = draw.textbbox((0, 0), "Ag字가", font=ref_fnt)[3] + 8
    max_ln  = max(1, avail_h // lh)
    if len(tip_lines) > max_ln:
        tip_lines = tip_lines[:max_ln]
        last = tip_lines[-1]
        while last and sum(_ch_w(c) for c in last + "…") > max_w:
            last = last[:-1]
        tip_lines[-1] = last + "…"

    # 수직 중앙 배치 (TIP 박스 전체 기준)
    total_h = lh * len(tip_lines)
    cur_y   = top + (avail_h - total_h) // 2

    # 폰트 메트릭으로 공통 베이스라인 설정
    ref_ascent, ref_descent = ref_fnt.getmetrics()

    for line in tip_lines:
        # 같은 폰트끼리 런(run)으로 묶기
        runs: list = []
        run_fkey, run_text = None, ""
        for ch in line:
            fkey = _fkey_for_char(ch, lang)
            if fkey == run_fkey:
                run_text += ch
            else:
                if run_text:
                    runs.append((run_fkey, run_text))
                run_fkey, run_text = fkey, ch
        if run_text:
            runs.append((run_fkey, run_text))

        # 런별 사전 계산 (bbox, ascent)
        run_data = []
        for rk, rt in runs:
            fnt = get_font(rk, size)
            bb  = draw.textbbox((0, 0), rt, font=fnt)
            run_data.append((fnt, rt, bb, fnt.getmetrics()[0]))

        line_w = sum(bb[2] - bb[0] for _, _, bb, _ in run_data)
        x = cx - line_w // 2
        baseline_y = cur_y + (lh - ref_ascent - ref_descent) // 2 + ref_ascent

        for fnt, rt, bb, run_asc in run_data:
            draw.text((x, baseline_y - run_asc), rt, font=fnt, fill=color)
            x += bb[2] - bb[0]

        cur_y += lh


def _lang_font_key(lang: str, bold: bool = True) -> str:
    """언어별 폰트 키 반환.
    JP→Noto JP, CN→wqy/NotoSansCJK, VN→NotoSans(라틴 확장), EN/ES→DejaVu/Arial, KO→Nanum
    """
    _BOLD_MAP  = {"JP": "jp", "CN": "cn", "VN": "vn", "EN": "bold",    "ES": "bold"}
    _REG_MAP   = {"JP": "jp", "CN": "cn", "VN": "vn", "EN": "regular",  "ES": "regular"}
    return (_BOLD_MAP if bold else _REG_MAP).get(lang.upper(),
                                                 "korean_bold" if bold else "korean")

def tl_font(lang: str, size: int) -> ImageFont.FreeTypeFont:
    """번역 언어에 맞는 폰트"""
    return get_font(_lang_font_key(lang, bold=False), size)

# ─── TTS ──────────────────────────────────────────────────────
# 학습자(my_line) — 자연스러운 여성 목소리 (피치 조작 없음, 아티팩트 방지)
_TTS_VOICES = {
    "ko": ("ko-KR", "ko-KR-Neural2-A", texttospeech.SsmlVoiceGender.FEMALE),
    "en": ("en-US", "en-US-Neural2-F", texttospeech.SsmlVoiceGender.FEMALE),
    "jp": ("ja-JP", "ja-JP-Neural2-B", texttospeech.SsmlVoiceGender.FEMALE),
    "cn": ("cmn-CN", "cmn-CN-Wavenet-A", texttospeech.SsmlVoiceGender.FEMALE),
    "vn": ("vi-VN", "vi-VN-Neural2-A", texttospeech.SsmlVoiceGender.FEMALE),
    "es": ("es-US", "es-US-Neural2-A", texttospeech.SsmlVoiceGender.FEMALE),
}
_LEARNER_PITCH = 0.0   # 피치 고정 — Neural2 pitch shift는 아티팩트 발생

# 응답자(response) — 학습자와 다른 목소리 (성별 무관, 피치 기본값)
_TTS_VOICES_RESP = {
    "ko": ("ko-KR", "ko-KR-Neural2-C", texttospeech.SsmlVoiceGender.MALE),
    "en": ("en-US", "en-US-Neural2-D", texttospeech.SsmlVoiceGender.MALE),
    "jp": ("ja-JP", "ja-JP-Neural2-C", texttospeech.SsmlVoiceGender.MALE),
    "cn": ("cmn-CN", "cmn-CN-Wavenet-B", texttospeech.SsmlVoiceGender.MALE),
    "vn": ("vi-VN", "vi-VN-Neural2-D", texttospeech.SsmlVoiceGender.MALE),
    "es": ("es-US", "es-US-Neural2-B", texttospeech.SsmlVoiceGender.MALE),
}

def _conv_tts_cache_path(cache_path_override: str, text: str, lang: str, slow: bool,
                         voice_name: str = "", pitch: float = 0.0) -> str:
    """회화 TTS 캐시 경로 반환 (명시적 경로 우선, 없으면 misc MD5 폴백)"""
    if cache_path_override:
        return cache_path_override
    import hashlib
    key = hashlib.md5(f"gcp:{lang}:{slow}:{voice_name}:{pitch}:{text}".encode()).hexdigest()
    d = _app_path("assets/tts_cache/misc")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{key}.mp3")

def text_to_speech(text: str, lang: str, output_path: str, slow: bool = False,
                   cache_path: str = None, is_resp: bool = False):
    """GCP TTS 음성 생성 (캐시 지원).
    is_resp=False → 학습자 목소리 (여아, pitch +4)
    is_resp=True  → 응답자 목소리 (다른 목소리, pitch 기본값)"""
    voice_table = _TTS_VOICES_RESP if is_resp else _TTS_VOICES
    lc, vname, gender = voice_table.get(lang.lower(), voice_table.get("en", _TTS_VOICES["en"]))
    pitch = 0.0 if is_resp else _LEARNER_PITCH

    cp = _conv_tts_cache_path(cache_path, text, lang, slow, vname, pitch)
    if os.path.exists(cp) and os.path.getsize(cp) > 0:
        shutil.copy2(cp, output_path)
        return
    _sa = os.path.join(os.path.dirname(__file__), "secrets", "gcp_service_account.json")
    if os.path.exists(_sa) and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _sa
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=lc, name=vname, ssml_gender=gender)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=0.85 if slow else 1.0,
        pitch=pitch,
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

def write_progress(step: str, pct: int = 0, theme_id: str = "", lang: str = "",
                   frame: int = None, total_frames: int = None):
    data = {
        "status": "running" if pct < 100 else "idle",
        "step": step, "pct": pct,
        "word": theme_id, "meaning": lang,
        "updated_at": datetime.now().isoformat(),
    }
    if frame is not None:
        data["frame"] = frame
    if total_frames is not None:
        data["total_frames"] = total_frames
    try:
        os.makedirs(_app_path("logs"), exist_ok=True)
        with open(_app_path("logs/progress.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass

# ─── 이모지 제거 (PIL은 컬러 이모지 미지원) ──────────────────
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FFFF"
    "\U00002600-\U000027FF"
    "\U0000FE00-\U0000FE0F"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251]+",
    flags=re.UNICODE,
)
def strip_emoji(text: str) -> str:
    return _EMOJI_RE.sub("", text).strip()

# ─── 유틸 ─────────────────────────────────────────────────────
def hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def draw_text_center(draw, x, y, text, font, color, max_width=None, max_lines=3):
    """중앙 정렬 텍스트. max_width 초과 시 단어 단위 줄바꿈 (최대 max_lines줄)."""
    if not text:
        return
    if max_width and draw.textbbox((0, 0), text, font=font)[2] > max_width:
        words = text.split()
        lines = []
        cur = []
        for word in words:
            test = " ".join(cur + [word])
            if draw.textbbox((0, 0), test, font=font)[2] > max_width and cur:
                lines.append(" ".join(cur))
                cur = [word]
            else:
                cur.append(word)
        if cur:
            lines.append(" ".join(cur))
        # 최대 줄 수 제한 (넘으면 말줄임표)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            last = lines[-1]
            while last and draw.textbbox((0, 0), last + "…", font=font)[2] > max_width:
                last = last[:-1]
            lines[-1] = last + "…"
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


def _paste_logo(img: Image.Image, bg_rgb: tuple,
                target_w: int, center_x: int, center_y: int,
                alpha: float = 1.0) -> None:
    """배경 밝기에 따라 흰/검정 로고를 img에 합성.
    bg_rgb(R,G,B) 밝기 < 128 → 흰 로고(HOW), >= 128 → 검정 로고(HOB).
    """
    lum = 0.299 * bg_rgb[0] + 0.587 * bg_rgb[1] + 0.114 * bg_rgb[2]
    logo_file = "hellowords_how_logo.png" if lum < 128 else "hellowords_hob_logo.png"
    logo_path = _app_path(f"assets/logos/{logo_file}")
    if not os.path.exists(logo_path):
        return
    logo = Image.open(logo_path).convert("RGBA")
    lw, lh = logo.size
    new_h = int(lh * target_w / lw)
    logo = logo.resize((target_w, new_h), Image.LANCZOS)
    if alpha < 1.0:
        r, g, b, a = logo.split()
        a = a.point(lambda x: int(x * alpha))
        logo = Image.merge("RGBA", (r, g, b, a))
    paste_x = center_x - target_w // 2
    paste_y = center_y - new_h // 2
    img.paste(logo, (paste_x, paste_y), mask=logo.split()[3])


# ─── 프레임 렌더링 ────────────────────────────────────────────
def render_dialogue_frame(
    phrase: dict,
    phrase_idx: int,
    total: int,
    theme: dict,
    lang: str,
    progress: float = 1.0,
    bob_my: int = 0,
    bob_resp: int = 0,
) -> Image.Image:
    """대화 프레임 — 내용템플릿.png 기반
    헤더 / 상단 말풍선(나) / 일러스트(크로마키→삽화) / 하단 말풍선(상대방) / TIP
    """
    # ── 템플릿 좌표 (내용템플릿.png 1080×1920 기준) ──────────
    BUB1_TOP, BUB1_BOT = 118, 437    # 상단 말풍선
    BUB2_TOP, BUB2_BOT = 1318, 1637  # 하단 말풍선
    BUB_L,    BUB_R    = 37, 1043    # 양쪽 말풍선 수평 범위
    ILLUST_T, ILLUST_B = 489, 1267   # 일러스트 영역(크로마키)
    ILLUST_L, ILLUST_R = 152, 930
    ILLUST_RX          = 38          # 코너 반경
    TIP_TOP,  TIP_BOT  = 1684, 1831  # TIP 박스

    # ── 색상 ─────────────────────────────────────────────────
    TITLE_C   = (32,  28,  24)
    ROMAN_C   = (90, 110, 115)
    TRANS_C   = (50,  70,  75)
    DOT_INACT = (130, 165, 175)
    TIP_LBL_C = (80, 140, 145)

    _LANG_COLORS = {
        "EN": (50,  92, 200),
        "JP": (219, 68,  85),
        "CN": (200, 50,  50),
        "VN": (180, 140, 20),
        "ES": (230, 126, 34),
    }
    DOT_ACT = _LANG_COLORS.get(lang.upper(), (50, 120, 180))

    # ── 베이스: 템플릿 로드 ──────────────────────────────────
    tmpl_path = _app_path("assets/templates/conv_template.png")
    tmpl = Image.open(tmpl_path).convert("RGBA")
    img  = tmpl.copy()
    draw = ImageDraw.Draw(img)

    p        = progress
    cx       = W // 2
    av       = int(255 * p)
    theme_id = theme.get("id", 0)
    sent_key = lang.lower()

    # ── 일러스트 (크로마키 영역에 삽화 붙여넣기) ──────────────
    illust_path = _app_path(
        f"assets/phrase_illustrations/sit_{theme_id}/phrase_{phrase_idx + 1}.png"
    )
    iw = ILLUST_R - ILLUST_L
    ih = ILLUST_B - ILLUST_T
    if os.path.exists(illust_path):
        try:
            raw = Image.open(illust_path).convert("RGBA")
            sw, sh = raw.size
            scale  = max(iw / sw, ih / sh)
            nw, nh = int(sw * scale), int(sh * scale)
            scaled = raw.resize((nw, nh), Image.LANCZOS)
            ox = (nw - iw) // 2
            oy = (nh - ih) // 2
            crop = scaled.crop((ox, oy, ox + iw, oy + ih))
            mask_r = Image.new("L", (iw, ih), 0)
            ImageDraw.Draw(mask_r).rounded_rectangle(
                [0, 0, iw - 1, ih - 1], radius=ILLUST_RX, fill=255
            )
            if p < 1.0:
                mask_r = mask_r.point(lambda v: int(v * p))
            crop.putalpha(mask_r)
            img.paste(crop, (ILLUST_L, ILLUST_T), mask=mask_r)
            draw = ImageDraw.Draw(img)
        except Exception as e:
            print(f"  일러스트 오류: {e}")

    # ── 말풍선 텍스트 렌더 헬퍼 ──────────────────────────────
    def _draw_bubble(bub_top, bub_bot, ko_text, roman, tl_text):
        nonlocal draw
        if not ko_text:
            return
        bub_cx  = (BUB_L + BUB_R) // 2
        max_w   = BUB_R - BUB_L - 64
        pad_v   = 26
        inner_t = bub_top + pad_v
        inner_b = bub_bot - pad_v
        inner_h = inner_b - inner_t
        gap     = 10

        # ── 발음기호 폰트 자동 크기 결정 (1줄 이내, 기본 26) ──
        phonetic = _get_phonetic(ko_text, roman, lang) if roman else ""
        ph_fk    = {"JP": "jp", "CN": "cn", "VN": "vn"}.get(lang.upper(), "regular")
        ph_fs    = 26
        for _fs in (26, 23, 20, 17, 14):
            _fnt = get_font(ph_fk, _fs)
            if not phonetic or draw.textbbox((0, 0), phonetic, font=_fnt)[2] <= max_w:
                ph_fs = _fs; break
        ph_font  = get_font(ph_fk, ph_fs)
        ph_lh    = int(ph_fs * 1.4)

        # ── 번역 폰트 자동 크기 결정 (2줄 이내, 기본 39 = 26×1.5) ──
        def _count_tl_lines(fnt_obj, text):
            if not text: return 0
            if draw.textbbox((0, 0), text, font=fnt_obj)[2] <= max_w:
                return 1
            if lang.upper() in ("JP", "CN"):
                return 2
            sp_w = draw.textbbox((0, 0), " ", font=fnt_obj)[2]
            n, cur_words, cur_w = 1, [], 0
            for word in text.split():
                ww = draw.textbbox((0, 0), word, font=fnt_obj)[2]
                sep = sp_w if cur_words else 0
                if cur_words and cur_w + sep + ww > max_w:
                    n += 1; cur_words, cur_w = [word], ww
                else:
                    cur_words.append(word); cur_w += sep + ww
            return n
        tl_fs = 39
        for _fs in (39, 35, 31, 27, 23, 19):
            _fnt = tl_font(lang, _fs)
            if not tl_text or _count_tl_lines(_fnt, tl_text) <= 2:
                tl_fs = _fs; break
        tl_font_obj = tl_font(lang, tl_fs)
        tl_lh       = int(tl_fs * 1.4)

        # 1) 한국어 — 단어 단위 자연 줄바꿈 (폰트 자동 축소)
        ko_font_key = "korean_bold"
        _ph_reserve = ph_lh * 2 + gap
        _tl_reserve = tl_lh * 2 + gap
        _avail_ko   = inner_h - _ph_reserve - _tl_reserve
        _avail_ko   = max(_avail_ko, inner_h // 2)

        ko_lines = [ko_text]
        ko_fs    = 22
        for fs in (58, 50, 42, 36, 30, 26, 22):
            fnt = get_font(ko_font_key, fs)
            lh  = int(fs * 1.28)
            if draw.textbbox((0, 0), ko_text, font=fnt)[2] <= max_w:
                ko_lines = [ko_text]; ko_fs = fs; break
            words = ko_text.split()
            if len(words) <= 1:
                continue
            wrapped, cur = [], []
            for word in words:
                test = " ".join(cur + [word])
                if draw.textbbox((0, 0), test, font=fnt)[2] > max_w and cur:
                    wrapped.append(" ".join(cur)); cur = [word]
                else:
                    cur.append(word)
            if cur: wrapped.append(" ".join(cur))
            if all(draw.textbbox((0, 0), l, font=fnt)[2] <= max_w for l in wrapped):
                if lh * len(wrapped) <= _avail_ko:
                    ko_lines = wrapped; ko_fs = fs; break
                if fs == 22:
                    ko_lines = wrapped; ko_fs = fs; break
        ko_font = get_font(ko_font_key, ko_fs)
        ko_lh   = int(ko_fs * 1.28)
        ko_h    = ko_lh * len(ko_lines)

        # 2) 발음기호 줄 구성
        ph_lines: list = []
        if phonetic:
            sp_w = draw.textbbox((0, 0), " ", font=ph_font)[2]
            cur_ph, cur_ph_w = [], 0
            for w in phonetic.split():
                ww = draw.textbbox((0, 0), w, font=ph_font)[2]
                sep = sp_w if cur_ph else 0
                if cur_ph and cur_ph_w + sep + ww > max_w:
                    ph_lines.append(" ".join(cur_ph)); cur_ph, cur_ph_w = [w], ww
                else:
                    cur_ph.append(w); cur_ph_w += sep + ww
            if cur_ph: ph_lines.append(" ".join(cur_ph))
            ph_lines = ph_lines[:2]
        ph_h = ph_lh * len(ph_lines)

        # 3) 번역 줄 구성
        tl_lines: list = []
        if tl_text:
            if lang.upper() in ("JP", "CN"):
                sentences = re.split(r'(?<=[。！？；])', tl_text)
                sentences = [s for s in sentences if s]
                cur_tl = ""
                for sent in sentences:
                    test = cur_tl + sent
                    if draw.textbbox((0, 0), test, font=tl_font_obj)[2] <= max_w:
                        cur_tl = test
                    else:
                        if cur_tl: tl_lines.append(cur_tl)
                        cur_tl = sent
                        if draw.textbbox((0, 0), cur_tl, font=tl_font_obj)[2] > max_w:
                            cur_tl = ""
                            for ch in sent:
                                t2 = cur_tl + ch
                                if cur_tl and draw.textbbox((0,0), t2, font=tl_font_obj)[2] > max_w:
                                    tl_lines.append(cur_tl); cur_tl = ch
                                else:
                                    cur_tl = t2
                if cur_tl: tl_lines.append(cur_tl)
            else:
                sp_w = draw.textbbox((0, 0), " ", font=tl_font_obj)[2]
                cur_tl, cur_tl_w = [], 0
                for word in tl_text.split():
                    ww = draw.textbbox((0, 0), word, font=tl_font_obj)[2]
                    sep = sp_w if cur_tl else 0
                    if cur_tl and cur_tl_w + sep + ww > max_w:
                        tl_lines.append(" ".join(cur_tl)); cur_tl, cur_tl_w = [word], ww
                    else:
                        cur_tl.append(word); cur_tl_w += sep + ww
                if cur_tl: tl_lines.append(" ".join(cur_tl))
            tl_lines = tl_lines[:2]
        tl_h = tl_lh * len(tl_lines)

        # 4) 전체 블록 높이 → 수직 중앙 배치
        total_h = ko_h
        if ph_h:  total_h += gap + ph_h
        if tl_h:  total_h += gap + tl_h
        cur_y   = inner_t + max(0, (inner_h - total_h) // 2)

        for line in ko_lines:
            draw.text((bub_cx, cur_y + ko_lh // 2), line,
                      font=ko_font, fill=(*TITLE_C, av), anchor="mm")
            cur_y += ko_lh

        for line in ph_lines:
            cur_y += gap
            draw.text((bub_cx, cur_y + ph_lh // 2), line,
                      font=ph_font, fill=(*ROMAN_C, int(175 * p)), anchor="mm")
            cur_y += ph_lh

        for line in tl_lines:
            cur_y += gap
            draw.text((bub_cx, cur_y + tl_lh // 2), line,
                      font=tl_font_obj, fill=(*TRANS_C, int(215 * p)), anchor="mm")
            cur_y += tl_lh

        draw = ImageDraw.Draw(img)

    # ── 나 말풍선 (상단) ─────────────────────────────────────
    my_ko    = phrase.get("my_ko", "")
    my_roman = phrase.get("my_roman", "")
    my_tl    = phrase.get(f"my_{sent_key}", phrase.get("my_en", ""))
    _draw_bubble(BUB1_TOP, BUB1_BOT, my_ko, my_roman, my_tl)

    # ── 상대방 말풍선 (하단) ─────────────────────────────────
    resp_ko    = phrase.get("resp_ko", "")
    resp_roman = phrase.get("resp_roman", "")
    resp_tl    = phrase.get(f"resp_{sent_key}", phrase.get("resp_en", ""))
    _draw_bubble(BUB2_TOP, BUB2_BOT, resp_ko, resp_roman, resp_tl)

    # ── 헤더 (상황 제목 + 진행 도트 + 번호/언어 배지) ─────────
    hdr_y = 59
    _LSK  = {"EN": "situation_en", "JP": "situation_jp",
              "CN": "situation_cn", "VN": "situation_vn", "ES": "situation_es"}
    sit_disp = (theme.get(_LSK.get(lang.upper(), ""), "")
                or theme.get("situation_en", "")
                or theme.get("situation", "")).strip()
    sit_disp = re.sub(r"\s*[—–]\s*", " — ", sit_disp)

    # 상황 텍스트 (좌측, 언어별 폰트 — 볼드)
    sit_fk = _lang_font_key(lang, bold=True)
    draw.text((43, hdr_y), sit_disp,
              font=get_font(sit_fk, 36),
              fill=(*TITLE_C, int(195 * p)), anchor="lm")

    # 우측: 언어 배지 → 번호 배지 → 진행 도트
    # 언어 배지
    lang_label = lang.upper()
    lang_font_obj = get_font("bold", 26)
    lbb  = draw.textbbox((0, 0), lang_label, font=lang_font_obj)
    lbw  = lbb[2] - lbb[0] + 31
    lbh  = 49
    lbx  = W - 37 - lbw
    lby  = hdr_y - lbh // 2
    lang_ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lang_ov).rounded_rectangle(
        [lbx, lby, lbx + lbw, lby + lbh], radius=lbh // 2,
        fill=(*DOT_ACT, int(225 * p))
    )
    img.paste(lang_ov, mask=lang_ov.split()[3])
    draw = ImageDraw.Draw(img)
    draw.text((lbx + lbw // 2, hdr_y), lang_label,
              font=lang_font_obj, fill=(255, 255, 255, av), anchor="mm")

    # 번호 배지 (언어 배지 왼쪽)
    num_bs = 49
    num_bx = lbx - 10 - num_bs
    num_by = hdr_y - num_bs // 2
    num_ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(num_ov).ellipse(
        [num_bx, num_by, num_bx + num_bs, num_by + num_bs],
        fill=(*DOT_ACT, int(225 * p))
    )
    img.paste(num_ov, mask=num_ov.split()[3])
    draw = ImageDraw.Draw(img)
    draw.text((num_bx + num_bs // 2, hdr_y), str(phrase_idx + 1),
              font=get_font("bold", 25), fill=(255, 255, 255, av), anchor="mm")

    # 진행 도트 (번호 배지 왼쪽)
    dot_r   = 8
    dot_gap = 21
    dots_total_w = total * dot_r * 2 + (total - 1) * (dot_gap - dot_r * 2)
    dot_right_x  = num_bx - 16
    dot_start_x  = dot_right_x - dots_total_w + dot_r
    for i in range(total):
        col = DOT_ACT if i == phrase_idx else DOT_INACT
        r   = dot_r + 3 if i == phrase_idx else dot_r
        dx  = dot_start_x + i * dot_gap
        draw.ellipse([dx - r, hdr_y - r, dx + r, hdr_y + r],
                     fill=(*col, av))

    # ── TIP 텍스트 (문자별 폰트 자동 선택 → 한·중·일·베트남 혼용 지원) ──
    tip_text = phrase.get("tip", "").strip()
    if tip_text:
        _draw_tip_mixed(draw, img, cx,
                        TIP_TOP + 2, TIP_BOT - 14,
                        tip_text, lang, 20,
                        (*TITLE_C, int(190 * p)), p)

    # ── 하단 로고 (hob 로고 → 언어 고유색) ──────────────────────
    logo_area_top = TIP_BOT + 7   # TIP 박스 하단(y=1834) 아래부터
    logo_area_h   = H - logo_area_top
    logo_path     = _app_path("assets/logos/hellowords_hob_logo.png")
    try:
        logo_raw = Image.open(logo_path).convert("RGBA")
        lw, lh   = logo_raw.size
        logo_h   = 35
        logo_w   = int(lw * logo_h / lh)
        logo_res = logo_raw.resize((logo_w, logo_h), Image.LANCZOS)
        _, _, _, alpha = logo_res.split()
        if p < 1.0:
            alpha = alpha.point(lambda v: int(v * p))
        # 템플릿 HELLO WORDS 덮기
        bg_px = tmpl.getpixel((20, H - 10))[:3]
        cover = Image.new("RGB", (W, logo_area_h), bg_px)
        img.paste(cover, (0, logo_area_top))
        # 착색 후 중앙 배치
        colored = Image.new("RGBA", logo_res.size, (*DOT_ACT, 255))
        colored.putalpha(alpha)
        lx = cx - logo_w // 2
        ly = logo_area_top + (logo_area_h - logo_h) // 2 - 15
        img.paste(colored, (lx, ly), mask=alpha)
        draw = ImageDraw.Draw(img)
    except Exception as e:
        print(f"  로고 오류: {e}")

    return img.convert("RGB")


# 하위 호환용 alias
render_phrase_frame = render_dialogue_frame


def render_intro_frame(theme: dict, lang: str, progress: float = 1.0) -> Image.Image:
    BG      = (163, 214, 215)
    TITLE_C = (25,  20,  30)
    MUTED_C = (70,  90,  95)

    _LANG_COLORS = {
        "EN": (50,  92,  200),
        "JP": (219, 68,   85),
        "CN": (200, 50,   50),
        "VN": (180, 140,  20),
        "ES": (230, 126,  34),
    }
    LANG_C = _LANG_COLORS.get(lang.upper(), (50, 92, 200))

    # 필 텍스트 — 앞부분도 해당 언어로 표기
    _PILL_TEXT = {
        "EN": "Korean  →  English",
        "JP": "韓国語  →  日本語",
        "CN": "韩语  →  中文",
        "VN": "Tiếng Hàn  →  Tiếng Việt",
        "ES": "Coreano  →  Español",
    }
    pill_text = _PILL_TEXT.get(lang.upper(), "Korean  →  English")

    _SUBTITLES = {
        "EN": "Today's Korean Conversation",
        "JP": "今日の韓国語会話",
        "CN": "今日韩语会话",
        "VN": "Hội thoại tiếng Hàn hôm nay",
        "ES": "Conversación coreana de hoy",
    }
    subtitle = _SUBTITLES.get(lang.upper(), "Today's Korean Conversation")

    _TAGLINES = {
        "EN": "Daily Korean", "JP": "毎日韓国語",
        "CN": "每日韩语", "VN": "Tiếng Hàn mỗi ngày", "ES": "Coreano diario",
    }
    tagline = _TAGLINES.get(lang.upper(), "Daily Korean")

    img  = Image.new("RGBA", (W, H), (*BG, 255))
    draw = ImageDraw.Draw(img)
    p    = progress
    cx   = W // 2
    av   = int(255 * p)

    TOP_BAND_H = 30
    BOT_BAND_H = 30

    # ── 상단 색 띠 ────────────────────────────────────────────
    top_ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(top_ov).rectangle([0, 0, W, TOP_BAND_H], fill=(*LANG_C, av))
    img.paste(top_ov, mask=top_ov.split()[3])
    draw = ImageDraw.Draw(img)

    # ── 하단 색 띠 ────────────────────────────────────────────
    bot_band_y = H - BOT_BAND_H
    bot_ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(bot_ov).rectangle([0, bot_band_y, W, H], fill=(*LANG_C, av))
    img.paste(bot_ov, mask=bot_ov.split()[3])
    draw = ImageDraw.Draw(img)

    # ── 제목 ─────────────────────────────────────────────────
    _LANG_SIT_KEY = {"EN":"situation_en","JP":"situation_jp","CN":"situation_cn","VN":"situation_vn","ES":"situation_es"}
    sit_key   = _LANG_SIT_KEY.get(lang.upper(), "situation")
    title_raw = (theme.get(sit_key) or theme.get("situation_en") or theme.get("situation","")).strip()

    def _split_title(text):
        if re.search(r'[—–/]', text):
            parts = [x.strip() for x in re.split(r'\s*[—–/]\s*', text) if x.strip()]
            return parts[:2]
        words = text.split()
        if len(words) <= 1:
            return [text]
        mid = (len(words) + 1) // 2
        return [" ".join(words[:mid]), " ".join(words[mid:])]

    lines = _split_title(title_raw)

    title_fk    = _lang_font_key(lang, bold=True)
    max_title_w = W - 100
    font_size   = 120
    while font_size > 52:
        font_title = get_font(title_fk, font_size)
        widths = [draw.textbbox((0,0), l, font=font_title)[2] for l in lines if l]
        if max(widths, default=0) <= max_title_w:
            break
        font_size -= 8
    font_title = get_font(title_fk, font_size)

    # ── 전체 레이아웃 계산 (정사각형 일러스트 기준) ───────────
    illust_margin = 44
    iw_sq         = W - illust_margin * 2
    brand_h       = 26 + 10 + 44
    n_lines   = len([l for l in lines if l])
    title_blk = int(font_size * 1.20) * n_lines
    sub_h_est = 40
    pill_h_est = 96
    fixed = title_blk + sub_h_est + pill_h_est + iw_sq + brand_h
    pool  = H - TOP_BAND_H - BOT_BAND_H - fixed
    unit  = pool / 10.0
    g_top   = int(unit * 2)
    g_sub   = int(unit * 1.5)
    g_pill  = int(unit * 1.5)
    g_ill   = int(unit * 2)

    line_h    = int(font_size * 1.20)
    title_top = TOP_BAND_H + g_top
    cur_y     = title_top

    for i, line in enumerate(lines):
        if not line:
            continue
        bb = draw.textbbox((0, 0), line, font=font_title)
        tx = cx - (bb[2] - bb[0]) // 2
        draw.text((tx, cur_y), line, font=font_title, fill=(*TITLE_C, av))
        cur_y += line_h


    # ── 부제목 ────────────────────────────────────────────────
    sub_fk   = _lang_font_key(lang, bold=False)
    sub_font = get_font(sub_fk, 34)
    sub_y    = cur_y + g_sub
    draw.text((cx, sub_y), subtitle, font=sub_font,
              fill=(*MUTED_C, int(210 * p)), anchor="mt")
    sub_bb = draw.textbbox((0, 0), subtitle, font=sub_font)
    sub_h  = sub_bb[3] - sub_bb[1]

    # ── 필 배지 ───────────────────────────────────────────────
    pill_font = get_font(_lang_font_key(lang, bold=True), 52)
    pb        = draw.textbbox((0, 0), pill_text, font=pill_font)
    pill_th   = pb[3] - pb[1]
    pill_w    = W - 80
    pill_h    = pill_th + 36
    pill_x    = cx - pill_w // 2
    pill_y    = sub_y + sub_h + g_pill

    pill_ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(pill_ov).rounded_rectangle(
        [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
        radius=pill_h // 2, fill=(*LANG_C, int(245 * p)),
    )
    img.paste(pill_ov, mask=pill_ov.split()[3])
    draw = ImageDraw.Draw(img)
    draw.text((cx, pill_y + pill_h // 2), pill_text,
              font=pill_font, fill=(255, 255, 255, av), anchor="mm")

    # ── 일러스트 (정사각형) ───────────────────────────────────
    illust_top    = pill_y + pill_h + g_ill
    illust_left   = illust_margin
    illust_right  = W - illust_margin
    illust_radius = 32

    theme_id     = theme.get("id", 0)
    intro_illust = _app_path(f"assets/phrase_illustrations/sit_{theme_id}/intro.png")
    if os.path.exists(intro_illust):
        try:
            illust_raw = Image.open(intro_illust).convert("RGBA")
            iw_t = iw_sq
            ih_t = iw_sq
            src_w, src_h = illust_raw.size
            scale = max(iw_t / src_w, ih_t / src_h)
            nw2, nh2 = int(src_w * scale), int(src_h * scale)
            illust_scaled = illust_raw.resize((nw2, nh2), Image.LANCZOS)
            ox = (nw2 - iw_t) // 2
            oy = (nh2 - ih_t) // 2
            illust_crop = illust_scaled.crop((ox, oy, ox + iw_t, oy + ih_t))
            mask_r = Image.new("L", (iw_t, ih_t), 0)
            ImageDraw.Draw(mask_r).rounded_rectangle(
                [0, 0, iw_t - 1, ih_t - 1], radius=illust_radius, fill=255)
            if p < 1.0:
                mask_r = mask_r.point(lambda v: int(v * p))
            illust_crop.putalpha(mask_r)
            img.paste(illust_crop, (illust_left, illust_top), mask=mask_r)
            draw = ImageDraw.Draw(img)
        except Exception as e:
            print(f"  일러스트 오류: {e}")

    # ── 브랜딩: 일러스트 아래, 하단 띠 위에 수직 중앙 배치 ──
    illust_bot     = illust_top + iw_sq
    remain         = bot_band_y - illust_bot
    brand_total_h  = 26 + 10 + 44
    brand_top      = illust_bot + (remain - brand_total_h) // 2

    tag_font = get_font(sub_fk, 26)
    draw.text((cx, brand_top + 13), tagline,
              font=tag_font, fill=(*MUTED_C, int(190 * p)), anchor="mm")

    logo_path     = _app_path("assets/logos/hellowords_hob_logo.png")
    logo_h_target = 44
    try:
        logo_raw     = Image.open(logo_path).convert("RGBA")
        lw, lh       = logo_raw.size
        scale        = logo_h_target / lh
        nw           = int(lw * scale)
        logo_resized = logo_raw.resize((nw, logo_h_target), Image.LANCZOS)
        _, _, _, alpha = logo_resized.split()
        if p < 1.0:
            alpha = alpha.point(lambda v: int(v * p))
        colored = Image.new("RGBA", logo_resized.size, (*LANG_C, 255))
        colored.putalpha(alpha)
        lx = cx - nw // 2
        ly = brand_top + 26 + 10
        img.paste(colored, (lx, ly), mask=alpha)
        draw = ImageDraw.Draw(img)
    except Exception as e:
        print(f"  로고 오류: {e}")
        hw_font = get_font("bold", 38)
        draw.text((cx, brand_top + 52), "HELLO WORDS",
                  font=hw_font, fill=(*LANG_C, av), anchor="mm")

    return img.convert("RGB")

def render_outro_frame(theme: dict, phrases: list, lang: str, progress: float = 1.0) -> Image.Image:
    """아웃트로: 오늘 배운 구문 목록 + 구독 유도 (다이얼로그 프레임과 동일 팔레트)"""
    BG       = (167, 212, 215)   # #a7d4d7
    TITLE_C  = (32,  28,  24)
    GOLD_C   = (160, 132, 62)
    CARD_C   = (255, 255, 255)
    TRANS_C  = (80,  70,  54)

    # 언어별 색상 (액센트 바, 번호, CTA 버튼, 로고 공통)
    LANG_C = {
        "EN": (50,   92, 200),
        "JP": (219,  68,  85),
        "CN": (200,  50,  50),
        "VN": (180, 140,  20),
        "ES": (230, 126,  34),
    }
    lang_color = LANG_C.get(lang.upper(), GOLD_C)
    logo_color = lang_color

    img = Image.new("RGBA", (W, H), (*BG, 255))
    draw = ImageDraw.Draw(img)
    p  = progress
    cx = W // 2

    # 제목 (밑줄 없음)
    outro_title_font_key = _lang_font_key(lang, bold=True)
    draw.text((cx, 120), _ui(lang, "outro_title"),
              font=get_font(outro_title_font_key, 56),
              fill=(*TITLE_C, int(255 * p)), anchor="mm")

    # 구문 목록 — 10개, 카드 축소
    font_ko   = get_font("korean_bold", 34)
    font_tl   = tl_font(lang, 26)
    sent_key  = lang.lower()
    card_h    = 84    # 카드 높이 (기존 110 → 84)
    card_gap  = 10    # 카드 사이 간격
    card_step = card_h + card_gap

    item_y = 175
    for i, ph in enumerate(phrases[:10]):
        ko = ph.get("my_ko", ph.get("ko", ""))
        tl = ph.get(f"my_{sent_key}", ph.get("my_en", ph.get(sent_key, ph.get("en", ""))))
        # 카드
        draw_rounded_rect(img, 40, item_y, W - 40, item_y + card_h,
                          radius=14, fill=CARD_C, alpha=int(220 * p))
        draw = ImageDraw.Draw(img)
        # 왼쪽 액센트 바
        draw.rectangle([40, item_y + 12, 47, item_y + card_h - 12],
                       fill=(*lang_color, int(200 * p)))
        # 번호
        draw.text((76, item_y + card_h // 2), str(i + 1),
                  font=get_font("bold", 24),
                  fill=(*lang_color, int(200 * p)), anchor="mm")
        # 한국어
        draw.text((100, item_y + 24), ko,
                  font=font_ko, fill=(*TITLE_C, int(240 * p)), anchor="lm")
        # 번역
        draw.text((100, item_y + 60), tl,
                  font=font_tl, fill=(*TRANS_C, int(180 * p)), anchor="lm")
        item_y += card_step

    # 구독 유도 CTA
    cta_y = item_y + 16
    draw_rounded_rect(img, 60, cta_y, W - 60, cta_y + 90,
                      radius=22, fill=lang_color, alpha=int(220 * p))
    draw = ImageDraw.Draw(img)
    cta_font_key = _lang_font_key(lang, bold=True)
    draw.text((cx, cta_y + 45), _ui(lang, "outro_cta"),
              font=get_font(cta_font_key, 34),
              fill=(255, 255, 255, int(255 * p)), anchor="mm")

    # 로고 (20% 축소: 380→304, 언어별 색상)
    logo_y = cta_y + 90 + 50
    logo_path = _app_path("assets/logos/hellowords_hob_logo.png")
    if os.path.exists(logo_path) and logo_y < H - 50:
        logo_raw = Image.open(logo_path).convert("RGBA")
        lw, lh   = logo_raw.size
        target_w = 304   # 380 × 0.8
        new_h    = int(lh * target_w / lw)
        logo_res = logo_raw.resize((target_w, new_h), Image.LANCZOS)
        _, _, _, alpha_ch = logo_res.split()
        if p < 1.0:
            alpha_ch = alpha_ch.point(lambda x: int(x * p))
        colored = Image.new("RGBA", logo_res.size, (*logo_color, 255))
        colored.putalpha(alpha_ch)
        lx = cx - target_w // 2
        ly = logo_y - new_h // 2
        img.paste(colored, (lx, ly), mask=alpha_ch)

    return img.convert("RGB")


def render_reels_ending_frame(lang: str, progress: float = 1.0) -> Image.Image:
    """쇼츠 전용 엔딩: 유튜브 본편 안내"""
    BG     = (167, 212, 215)
    CARD_C = (255, 255, 255)
    _LANG_COLORS = {
        "EN": (50,   92, 200),
        "JP": (219,  68,  85),
        "CN": (200,  50,  50),
        "VN": (180, 140,  20),
        "ES": (230, 126,  34),
    }
    lang_color = _LANG_COLORS.get(lang.upper(), (100, 100, 100))

    img  = Image.new("RGBA", (W, H), (*BG, 255))
    draw = ImageDraw.Draw(img)
    p    = progress
    cx   = W // 2

    # 카드
    card_x1, card_y1, card_x2, card_y2 = 50, 380, W - 50, 720
    draw_rounded_rect(img, card_x1, card_y1, card_x2, card_y2,
                      radius=30, fill=CARD_C, alpha=int(230 * p))
    draw = ImageDraw.Draw(img)

    card_cy = (card_y1 + card_y2) // 2

    # 번역 텍스트 (해당 언어)
    tl_text = _ui(lang, "reels_more_tl")
    tl_fk   = _lang_font_key(lang, bold=True)
    for fs in (34, 30, 26, 22):
        fnt = get_font(tl_fk, fs)
        bbox = draw.textbbox((0, 0), tl_text, font=fnt)
        if bbox[2] - bbox[0] <= (card_x2 - card_x1 - 60):
            break
    draw.text((cx, card_cy - 28), tl_text, font=fnt,
              fill=(*lang_color, int(245 * p)), anchor="mm")

    # 한국어 안내
    ko_text = "더 많은 내용은 유튜브 본편에서 확인하세요"
    ko_fnt  = get_font("korean_bold", 24)
    draw.text((cx, card_cy + 30), ko_text, font=ko_fnt,
              fill=(80, 70, 60, int(170 * p)), anchor="mm")

    # HelloWords 로고
    logo_path = _app_path("assets/logos/hellowords_hob_logo.png")
    if os.path.exists(logo_path):
        logo_raw = Image.open(logo_path).convert("RGBA")
        lw, lh   = logo_raw.size
        target_w = 260
        new_h    = int(lh * target_w / lw)
        logo_res = logo_raw.resize((target_w, new_h), Image.LANCZOS)
        _, _, _, alpha_ch = logo_res.split()
        if p < 1.0:
            alpha_ch = alpha_ch.point(lambda x: int(x * p))
        colored = Image.new("RGBA", logo_res.size, (*lang_color, 255))
        colored.putalpha(alpha_ch)
        lx = cx - target_w // 2
        ly = H - 180 - new_h // 2
        img.paste(colored, (lx, ly), mask=alpha_ch)

    return img.convert("RGB")


# ─── 영상 생성 메인 ───────────────────────────────────────────
def _make_silence(path: str, dur: float = 0.5):
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", str(dur), "-q:a", "9", "-acodec", "libmp3lame",
        path, "-y"
    ], capture_output=True)


def create_conversation_video(theme: dict, phrases: list, output_path: str,
                               lang: str, tmpdir: str, fmt: str = "youtube"):
    if fmt == "reels":
        phrases = phrases[:6]
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
                           cache_path=_cp(f"p{i+1:02d}_my_ko_girl.mp3"))
        else:
            _make_silence(my_ko_path)

        my_tl = ph.get(f"my_{sent_key}", ph.get("my_en", ""))
        if my_tl:
            text_to_speech(my_tl, lang_lower, my_tl_path,
                           cache_path=_cp(f"p{i+1:02d}_my_{lang_lower}_girl.mp3"))
        else:
            _make_silence(my_tl_path)

        resp_ko = ph.get("resp_ko", "")
        if resp_ko:
            text_to_speech(resp_ko, "ko", resp_ko_path, slow=True,
                           cache_path=_cp(f"p{i+1:02d}_resp_ko.mp3"),
                           is_resp=True)
        else:
            _make_silence(resp_ko_path, 0.3)

        resp_tl = ph.get(f"resp_{sent_key}", ph.get("resp_en", ""))
        if resp_tl:
            text_to_speech(resp_tl, lang_lower, resp_tl_path,
                           cache_path=_cp(f"p{i+1:02d}_resp_{lang_lower}.mp3"),
                           is_resp=True)
        else:
            _make_silence(resp_tl_path, 0.3)

        phrase_audios.append((my_ko_path, my_tl_path, resp_ko_path, resp_tl_path))

    # 인트로 TTS — 상황 제목을 해당 언어로 읽어줌
    _LSK_INTRO = {"EN": "situation_en", "JP": "situation_jp",
                  "CN": "situation_cn", "VN": "situation_vn", "ES": "situation_es"}
    sit_title = (theme.get(_LSK_INTRO.get(lang.upper(), ""), "")
                 or theme.get("situation_en", "")
                 or theme.get("situation", "")).strip()
    intro_tts_path = os.path.join(tmpdir, "intro_tts.mp3")
    intro_tts_dur  = 0.0
    if sit_title and fmt != "reels":
        try:
            intro_cache = _cp(f"intro_{lang_lower}.mp3")
            text_to_speech(sit_title, lang_lower, intro_tts_path,
                           cache_path=intro_cache)
            intro_tts_dur = get_audio_duration(intro_tts_path)
        except Exception as e:
            print(f"  인트로 TTS 오류: {e}")
            intro_tts_dur = 0.0

    write_progress("2/4 타임라인 계산 중...", pct=20, theme_id=theme["id"], lang=lang)

    # 구간 타이밍 계산
    if fmt == "reels":
        INTRO_DUR    = 0.5
        OUTRO_DUR    = 1.0
        ENDING_DUR   = 3.0   # 쇼츠 전용 엔딩 (유튜브 본편 안내)
        PRE_GAP      = 0.2
        KO_TL_GAP    = 0.3
        PAIR_GAP     = 0.4
        POST_GAP     = 0.5
    else:
        ENDING_DUR   = 0.0
        INTRO_DUR   = max(2.0, intro_tts_dur + 0.8)  # TTS 길이 + 여유
        OUTRO_DUR   = 3.5
        PRE_GAP     = 0.4
        KO_TL_GAP   = 0.5
        PAIR_GAP    = 0.6
        POST_GAP    = 0.8
    FADE_FRAMES = 9     # 페이드 프레임 수 (0.3s)

    phrase_durations = []
    phrase_seg_durs  = []   # [(my_ko_d, my_tl_d, resp_ko_d, resp_tl_d), ...]
    audio_timeline   = []   # (path, abs_start_time)

    # 인트로 TTS를 0.4s 오프셋에 삽입
    if intro_tts_dur > 0:
        audio_timeline.append((intro_tts_path, 0.4))

    t = INTRO_DUR

    for i, (my_ko_p, my_tl_p, resp_ko_p, resp_tl_p) in enumerate(phrase_audios):
        my_ko_dur   = get_audio_duration(my_ko_p)
        my_tl_dur   = get_audio_duration(my_tl_p)
        resp_ko_dur = get_audio_duration(resp_ko_p)
        resp_tl_dur = get_audio_duration(resp_tl_p)

        phrase_dur = (PRE_GAP + my_ko_dur + KO_TL_GAP + my_tl_dur
                      + PAIR_GAP + resp_ko_dur + KO_TL_GAP + resp_tl_dur + POST_GAP)
        phrase_durations.append(phrase_dur)
        phrase_seg_durs.append((my_ko_dur, my_tl_dur, resp_ko_dur, resp_tl_dur))

        t_my_ko   = t + PRE_GAP
        t_my_tl   = t_my_ko + my_ko_dur + KO_TL_GAP
        t_resp_ko = t_my_tl + my_tl_dur + PAIR_GAP
        t_resp_tl = t_resp_ko + resp_ko_dur + KO_TL_GAP

        audio_timeline.append((my_ko_p,   t_my_ko))
        audio_timeline.append((my_tl_p,   t_my_tl))
        audio_timeline.append((resp_ko_p, t_resp_ko))
        audio_timeline.append((resp_tl_p, t_resp_tl))
        t += phrase_dur

    total_duration = INTRO_DUR + sum(phrase_durations) + OUTRO_DUR + ENDING_DUR

    write_progress("3/4 프레임 렌더링 중...", pct=30, theme_id=theme["id"], lang=lang)
    print(f"  3/4 프레임 렌더링 중... (총 {total_duration:.1f}초)")

    # 프레임 렌더링 (Pass 1: rawvideo → 인코딩된 임시 영상)
    raw_video_path = os.path.join(tmpdir, "raw_video.mp4")
    pipe_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS),
        "-i", "pipe:0",
        *get_video_encoder(),
        "-pix_fmt", "yuv420p",
        raw_video_path,
    ]
    pipe_proc = subprocess.Popen(pipe_cmd, stdin=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL)

    def save_frame(img_rgb):
        pipe_proc.stdin.write(img_rgb.tobytes())

    # ── 전체 프레임 수 사전 계산 (정확한 progress용) ─────────
    intro_frames   = int(INTRO_DUR * FPS)
    phrase_frames  = [int(d * FPS) for d in phrase_durations]
    outro_frames   = int(OUTRO_DUR * FPS)
    ending_frames  = int(ENDING_DUR * FPS)
    total_frames   = intro_frames + sum(phrase_frames) + outro_frames + ending_frames
    rendered       = 0

    def _pct(n):
        return 30 + int(55 * n / max(1, total_frames))

    # 인트로 프레임
    for f in range(intro_frames):
        rendered += 1
        if f % 30 == 0:
            write_progress("3/4 프레임 렌더링 중... (인트로)",
                           pct=_pct(rendered), theme_id=theme["id"], lang=lang,
                           frame=rendered, total_frames=total_frames)
        save_frame(render_intro_frame(theme, lang, progress=1.0))

    # 구문 프레임 (까딱 애니메이션 포함)
    BOB_AMP  = 8     # 얼굴 상하 진폭 (px)
    BOB_FREQ = 2.8   # 초당 진동 횟수 (Hz)

    for i, ph in enumerate(phrases):
        dur       = phrase_durations[i]
        ph_frames = phrase_frames[i]
        my_ko_d, my_tl_d, resp_ko_d, resp_tl_d = phrase_seg_durs[i]

        # 구문 내 발화 구간 (구문 시작 기준)
        t_my_start   = PRE_GAP
        t_my_end     = t_my_start + my_ko_d + KO_TL_GAP + my_tl_d
        t_resp_start = t_my_end + PAIR_GAP
        t_resp_end   = t_resp_start + resp_ko_d + KO_TL_GAP + resp_tl_d

        for f in range(ph_frames):
            rendered += 1
            if f % 30 == 0:
                write_progress(
                    f"3/4 프레임 렌더링 중... ({i+1}/{total})",
                    pct=_pct(rendered), theme_id=theme["id"], lang=lang,
                    frame=rendered, total_frames=total_frames)
            phrase_t = f / FPS

            # 까딱: 발화 구간에서만 사인파 오프셋
            if t_my_start <= phrase_t < t_my_end:
                bob_my   = int(BOB_AMP * math.sin(2 * math.pi * BOB_FREQ * phrase_t))
                bob_resp = 0
            elif t_resp_start <= phrase_t < t_resp_end:
                bob_my   = 0
                bob_resp = int(BOB_AMP * math.sin(2 * math.pi * BOB_FREQ * phrase_t))
            else:
                bob_my = bob_resp = 0

            save_frame(render_phrase_frame(ph, i, total, theme, lang,
                                           progress=1.0,
                                           bob_my=bob_my, bob_resp=bob_resp))

    # 아웃트로 프레임
    for f in range(outro_frames):
        rendered += 1
        if f % 30 == 0:
            write_progress("3/4 프레임 렌더링 중... (아웃트로)",
                           pct=_pct(rendered), theme_id=theme["id"], lang=lang,
                           frame=rendered, total_frames=total_frames)
        save_frame(render_outro_frame(theme, phrases, lang, progress=1.0))

    # 쇼츠 전용 엔딩 프레임 (유튜브 본편 안내)
    for f in range(ending_frames):
        rendered += 1
        if f % 30 == 0:
            write_progress("3/4 프레임 렌더링 중... (엔딩)",
                           pct=_pct(rendered), theme_id=theme["id"], lang=lang,
                           frame=rendered, total_frames=total_frames)
        save_frame(render_reels_ending_frame(lang, progress=1.0))

    # Pass 1 완료 — pipe 닫기
    pipe_proc.stdin.close()
    pipe_proc.wait()
    if pipe_proc.returncode != 0:
        raise RuntimeError("Pass 1 FFmpeg 실패 (rawvideo 인코딩)")

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
    music_idx = a_idx + 2  # 0=raw_video, 1=silence, 2..a_idx+1=TTS, a_idx+2=music

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

    # Pass 2: 인코딩된 영상 + 오디오 → 최종 출력 (영상 재인코딩 없이 copy)
    cmd = [
        "ffmpeg", "-y",
        "-i", raw_video_path,
    ] + input_args
    if filter_complex:
        cmd += ["-filter_complex", filter_complex]
    cmd += [
        "-map", "0:v",
    ] + audio_map + [
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
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

    # Windows 파일 잠금 해제: Pass 2 완료 후 임시 원본 영상 즉시 삭제
    try:
        if os.path.exists(raw_video_path):
            os.unlink(raw_video_path)
    except Exception:
        pass

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
    parser.add_argument("--format", default="youtube", choices=["youtube", "reels"])
    args = parser.parse_args()

    # DB 로드
    _base = os.environ.get("APP_BASE", os.path.join(os.path.dirname(__file__), ".."))
    db_path = args.db or os.path.join(_base, "data", "Conversation", "phrases_db.json")
    with open(db_path, encoding="utf-8") as f:
        db = json.load(f)

    # 리스트 형식(phrases_db.json) → 내부 형식으로 변환 (title/emoji/color 보정)
    _CAT_STYLE = {
        "여행":      ("#7EC8F7", "✈️"),   # 밝은 스카이 블루
        "식사":      ("#FF8C78", "🍜"),   # 살몬 코랄
        "쇼핑":      ("#FFB347", "🛍️"),   # 피치 골드
        "인사":      ("#5DDAB4", "👋"),   # 민트 그린
        "일상":      ("#C87FFF", "💬"),   # 소프트 라벤더
        "비즈니스":  ("#6ACFEE", "💼"),   # 파스텔 블루
        "K-Culture": ("#FF6BAE", "🎭"),   # 핫 핑크
        "의료":      ("#FF7F7F", "🏥"),   # 소프트 레드
        "주거":      ("#82D882", "🏠"),   # 소프트 그린
        "여가":      ("#FFB07C", "🎮"),   # 피치
    }
    if isinstance(db, list):
        db = {"themes": [
            {
                **item,
                "title": {
                    "ko": item.get("situation", ""),    "KR": item.get("situation", ""),
                    "en": item.get("situation_en", ""), "EN": item.get("situation_en", ""),
                    "jp": item.get("situation_jp", ""), "JP": item.get("situation_jp", ""),
                    "cn": item.get("situation_cn", ""), "CN": item.get("situation_cn", ""),
                    "vn": item.get("situation_vn", ""), "VN": item.get("situation_vn", ""),
                    "es": item.get("situation_es", ""), "ES": item.get("situation_es", ""),
                },
                "color": item.get("color", _CAT_STYLE.get(item.get("category", ""), ("#4F8EF7", "💬"))[0]),
                "emoji": item.get("emoji", _CAT_STYLE.get(item.get("category", ""), ("#4F8EF7", "💬"))[1]),
            }
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
                "tip": ph.get(f"tip_{sent_key_flat}", ph.get("tip_en", ph.get("tip", ""))),
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
                "tip": ph.get(f"tip_{sent_key_flat}", ph.get("tip_en", ph.get("tip", ""))),
            })
    phrases = pair_phrases

    # 출력 경로
    out_dir = os.path.join(args.output, "conversation", args.lang)
    os.makedirs(out_dir, exist_ok=True)
    fmt_suffix = "_reels" if args.format == "reels" else ""
    filename = f"conv_{args.theme}_{args.lang}{fmt_suffix}.mp4"
    output_path = os.path.join(out_dir, filename)

    print(f"\n>> 회화 영상 생성: [{args.lang}] {theme.get('title', {}).get('ko', args.theme)}")
    print(f"   구문 수: {len(phrases)}개 / 포맷: {args.format}")

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        create_conversation_video(theme, phrases, output_path, args.lang, tmpdir, fmt=args.format)

    print(f"\n완료! {output_path}")
