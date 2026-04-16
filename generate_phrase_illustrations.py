#!/usr/bin/env python3
"""
대화 상황별 웹툰 패널 일러스트 배치 생성
- Google Imagen 4 Fast 사용
- assets/phrase_illustrations/sit_{id}/ 에 저장 (기존 파일 스킵)
- Claude API로 각 패널 장면 설명 생성
- 비용: $0.02/장 × (상황 수 × 패널 수)

준비:
  1. .env 에 GEMINI_API_KEY=... 추가
  2. .env 에 ANTHROPIC_API_KEY=... 추가

실행:
  python generate_phrase_illustrations.py
  python generate_phrase_illustrations.py --start 1 --end 10
  python generate_phrase_illustrations.py --situation-id 5
  python generate_phrase_illustrations.py --intro-only
  python generate_phrase_illustrations.py --status
"""

import json
import os
import re
import sys
import io
import time
import argparse
from datetime import datetime
from pathlib import Path

# Windows cp949 인코딩 문제 방지
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except AttributeError:
        pass

# .env 로드
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from google import genai
from google.genai import types

# ─── 경로 설정 ───────────────────────────────────────────────
_SCRIPT_DIR     = Path(__file__).parent
OUTPUT_DIR      = _SCRIPT_DIR / "assets" / "phrase_illustrations"
_APP_BASE       = os.environ.get("APP_BASE", str(Path(__file__).parent.parent))
PHRASES_DB_PATH = Path(_APP_BASE) / "data" / "Conversation" / "phrases_db.json"
PROGRESS_FILE   = _SCRIPT_DIR / "logs" / "phrase_illust_progress.json"

# ─── 캐릭터 풀 ───────────────────────────────────────────────
# 조연 캐릭터: 주인공(래서팬더 — 주황빨간색)과 명확히 다른 색상의 동물만
# shiba inu / golden retriever 등 주황/황갈색은 래서팬더와 헷갈리므로 제외
# 의상(outfit)은 _get_supporting_char_outfit()이 상황에 맞게 동적 결정
_LOCAL_ANIMAL_SPECIES = [
    # ── 기존 10종 ─────────────────────────────────────────────
    "gray tabby cat",             # 회색
    "black-and-white dalmatian dog",  # 흑백
    "white fluffy rabbit",        # 흰색
    "blue-gray elephant",         # 회청색
    "dark brown bear",            # 짙은 갈색
    "white cat with glasses",     # 흰색
    "black poodle",               # 검정
    "spotted black-and-white cow",# 흑백 얼룩
    "silver-gray wolf",           # 은회색
    "green frog",                 # 초록
    # ── 추가 40종 ─────────────────────────────────────────────
    "cream-colored hamster",              # 크림
    "black-and-white penguin",            # 흑백
    "brown-and-white owl",                # 갈색/흰배
    "brown hedgehog",                     # 갈색/크림
    "dark brown otter",                   # 진갈색
    "white fluffy lamb",                  # 흰색
    "dark brown dachshund",               # 진갈색
    "gray-striped raccoon",               # 회색/줄무늬
    "gray-brown capybara",                # 회갈색
    "cream siamese cat",                  # 크림/갈색포인트
    "black-and-white husky dog",          # 흑백
    "gray-brown squirrel",                # 회갈색
    "white persian cat",                  # 흰색/크림
    "blue-gray koala",                    # 회청색
    "black-and-white striped zebra",      # 흑백 줄무늬
    "white-gray spotted snow leopard cub",# 흰회색+점
    "pink-tinted axolotl",                # 연분홍
    "mint-green chameleon",               # 민트초록
    "white polar bear cub",               # 흰색
    "gray ring-tailed lemur",             # 회색/흑백꼬리
    "black-and-white giant panda cub",    # 흑백
    "pink flamingo",                      # 분홍
    "dark gray gorilla",                  # 진회색
    "iridescent peacock",                 # 청록/보라
    "white arctic fox",                   # 흰색
    "gray donkey",                        # 회색
    "spotted yellow-and-brown baby giraffe",  # 황색+점
    "black-and-white badger",             # 흑백
    "blue macaw parrot",                  # 파랑
    "tiny gray mouse",                    # 회색
    "dark brown beaver",                  # 진갈색
    "gray meerkat",                       # 회갈색
    "fluffy white alpaca",                # 흰색
    "gray chinchilla",                    # 회색/연보라
    "black-and-white skunk",              # 흑백
    "lilac-gray sugar glider",            # 연보라/회색
    "dark indigo tapir",                  # 남색/회색
    "silver-gray mole",                   # 은회색
    "teal-blue heron",                    # 청록
    "cream-colored manatee",              # 크림/회색
]

# 주인공(학습자)은 래서 팬더로 고정 — 상황과 무관한 기본 의상 (가방 없음)
_LEARNER_OUTFITS = [
    "casual sweater and jeans",
    "hoodie",
    "colorful cardigan",
    "striped shirt and cap",
    "cozy knit sweater",
    "light jacket",
    "denim jacket",
    "floral blouse and skirt",
    "sporty tracksuit",
    "trench coat",
]

def _get_supporting_char_outfit(situation: dict) -> str:
    """상황에 맞는 조연 캐릭터 의상 반환 (상황별 역할 고려)."""
    sit_en = situation.get("situation_en", "").lower()

    # 공항 / 이동 — 더 구체적인 상황을 먼저 체크
    if any(k in sit_en for k in ("transit", "connecting flight")):
        return "airline gate staff uniform with an airport name badge"
    if any(k in sit_en for k in ("airport", "immigration", "customs", "boarding",
                                  "departure", "arrival", "check-in", "security check")):
        return "airline staff uniform with a name badge and scarf"
    if any(k in sit_en for k in ("train station", "ktx", "train")):
        return "train conductor uniform — dark jacket with a small cap"
    if any(k in sit_en for k in ("bus terminal", "bus station", "bus")):
        return "bus driver uniform — collared shirt with a driver's cap"
    if any(k in sit_en for k in ("taxi",)):
        return "taxi driver uniform — dark collared shirt with a small ID badge"
    if any(k in sit_en for k in ("subway", "metro", "commut")):
        return "casual everyday outfit"
    if any(k in sit_en for k in ("car rental", "rental car", "rent a car")):
        return "car rental agent uniform — smart polo shirt with a company logo"
    if any(k in sit_en for k in ("currency exchange", "exchange", "atm", "money")):
        return "bank teller uniform — neat blazer with a name badge"
    if any(k in sit_en for k in ("hotel", "accommodation", "hostel", "guesthouse", "check in")):
        return "hotel front-desk uniform — neat blazer and name badge"

    # 음식 / 카페
    if any(k in sit_en for k in ("restaurant", "dining", "meal", "eating")):
        return "restaurant server apron over a neat shirt"
    if any(k in sit_en for k in ("cafe", "coffee", "bakery")):
        return "barista apron over a casual shirt"
    if any(k in sit_en for k in ("dessert", "street food", "food stall")):
        return "casual clothes"
    if any(k in sit_en for k in ("bbq", "barbecue", "grilling", "picnic")):
        return "casual clothes with a light outdoor apron"

    # 쇼핑 / 마트
    if any(k in sit_en for k in ("shopping", "mart", "supermarket", "grocery",
                                   "market", "convenience store")):
        return "store staff vest over a casual shirt"
    if any(k in sit_en for k in ("pharmacy", "drugstore")):
        return "pharmacist white coat over casual clothes"

    # 병원 / 의료
    if any(k in sit_en for k in ("hospital", "clinic", "doctor", "medical", "emergency")):
        return "doctor white coat or nurse scrubs"

    # 학교 / 교육
    if any(k in sit_en for k in ("school", "class", "classroom", "university",
                                   "college", "lecture")):
        return "smart casual school outfit with a backpack"
    if any(k in sit_en for k in ("library", "study cafe", "study room")):
        return "casual studious outfit with a book or notebook"

    # 직장 / 오피스
    if any(k in sit_en for k in ("office", "workplace", "work", "meeting",
                                   "conference", "business", "interview", "job")):
        return "business casual — neat collared shirt and trousers"

    # 운동 / 레저
    if any(k in sit_en for k in ("gym", "fitness", "workout", "exercise", "sport")):
        return "sporty activewear with a towel"
    if any(k in sit_en for k in ("swimming", "pool")):
        return "swim casual outfit with a towel"
    if any(k in sit_en for k in ("hiking", "mountain", "camping", "outdoor")):
        return "outdoor hiking gear with a light backpack"
    if any(k in sit_en for k in ("beach", "sea", "ocean", "resort")):
        return "summer casual outfit with a sunhat"
    if any(k in sit_en for k in ("sightseeing", "tourist", "tour")):
        return "tourist casual outfit with a camera strap"

    # 뷰티 / 웰빙
    if any(k in sit_en for k in ("hair salon", "beauty salon", "barbershop", "nail", "spa")):
        return "salon staff uniform — neat apron over a smart top"
    if any(k in sit_en for k in ("sauna", "jimjilbang", "bath", "jjimjil")):
        return "cozy lounge wear or towel wrap"

    # 파티 / 이벤트
    if any(k in sit_en for k in ("party", "wedding", "ceremony", "celebration", "banquet")):
        return "smart casual party outfit"
    if any(k in sit_en for k in ("karaoke", "singing", "norebang")):
        return "fun casual outfit"

    # 집 / 동네
    if any(k in sit_en for k in ("home", "house", "apartment", "neighbor", "landlord")):
        return "cozy home casual wear"
    if any(k in sit_en for k in ("post office", "government", "service center")):
        return "office-casual neat outfit with a name badge"

    # 기본값
    return "casual everyday outfit"


def _pick_characters(sit_id: int, situation: dict | None = None,
                     phrase_idx: int = 0) -> tuple[str, str]:
    """상황 ID 기반으로 캐릭터 쌍 선택.
    같은 상황 내 모든 패널은 동일한 캐릭터/의상을 유지 (시각적 일관성).
    차별화는 동작·표정·구도로만 — phrase_idx는 캐릭터 선택에 사용하지 않음."""
    # 조연: sit_id만 사용 → 상황 내 전 패널 동일 캐릭터 유지
    species = _LOCAL_ANIMAL_SPECIES[sit_id % len(_LOCAL_ANIMAL_SPECIES)]
    if situation:
        supporting_outfit = _get_supporting_char_outfit(situation)
        main_outfit = _get_main_char_outfit(situation)
    else:
        supporting_outfit = "casual everyday outfit"
        main_outfit = _LEARNER_OUTFITS[sit_id % len(_LEARNER_OUTFITS)]
    local   = f"{species} wearing {supporting_outfit}"
    learner = f"red panda wearing {main_outfit}"
    return local, learner


# ─── 표정 어휘집 ─────────────────────────────────────────────
# 감정 → Gemini가 이해할 수 있는 구체적 얼굴/몸짓 묘사
_EXPRESSION_VOCAB = {
    "surprised":    "eyes stretched wide and round, mouth open in a small O, one paw raised to cheek in shock",
    "confused":     "head tilted 40° to one side, one eyebrow raised high, finger pressed to cheek in thought",
    "excited":      "arms thrown up joyfully, eyes squeezed into happy crescents, big open-mouth grin",
    "nervous":      "tiny sweat drop on forehead, eyes darting sideways, both paws clasped tightly together",
    "apologetic":   "head bowed low, both paws pressed together in front, round rosy blush circles on cheeks",
    "curious":      "body leaning eagerly forward, eyes wide and sparkling, one finger raised in the air",
    "relieved":     "eyes gently closed in a soft smile, one paw resting on chest, shoulders visibly relaxed",
    "embarrassed":  "one paw scratching the back of the head, gaze turned away, large pink blush circle on cheek",
    "confident":    "chin tilted up, one paw on hip, one arm extended open-palm forward, bright steady eyes",
    "thoughtful":   "finger resting on chin, eyes glancing upward to the side, slight frown of concentration",
    "grateful":     "both paws pressed to chest, eyes closed in a blissful smile, small heart near face",
    "worried":      "eyebrows pinched inward and down, one paw covering mouth, body hunched slightly",
    "determined":   "eyes narrowed in firm focus, fists clenched at sides, leaning slightly forward",
    "playful":      "winking one eye, tongue peeking out, arms spread wide with a cheeky grin",
    "disappointed": "drooping ears (if applicable), downturned mouth, one paw on forehead in resignation",
    "proud":        "chest puffed out, arms crossed, wide beaming smile, head held high",
}

# 대화 키워드 → 감정 매핑
_KEYWORD_EMOTIONS = [
    (["sorry", "apolog", "excuse me", "forgive", "my fault"],           "apologetic"),
    (["emergency", "urgent", "hurt", "sick", "pain", "help me"],        "worried"),
    (["really?", "seriously?", "what?!", "no way", "impossible"],       "surprised"),
    (["thank", "grateful", "appreciate", "wonderful", "perfect"],       "grateful"),
    (["don't understand", "what does", "pardon", "again", "repeat"],    "confused"),
    (["nervous", "scared", "afraid", "anxious", "worried"],             "nervous"),
    (["of course", "no problem", "sure", "absolutely", "definitely"],   "confident"),
    (["wow", "amazing", "incredible", "fantastic", "so good"],          "excited"),
    (["hmm", "let me think", "i'm not sure", "maybe", "perhaps"],      "thoughtful"),
    (["congratulations", "well done", "great job", "i did it"],        "proud"),
    (["haha", "funny", "joke", "play", "fun"],                          "playful"),
    (["finally", "at last", "phew", "relief"],                          "relieved"),
]

_FALLBACK_EXPRESSIONS = list(_EXPRESSION_VOCAB.keys())

# ── 패널별 배경 변주 힌트 — 같은 상황 내에서 촬영 각도·서브공간을 바꿔 단조로움 방지 ──
_PANEL_VARIATION_HINTS = [
    "front-facing medium shot at the main area of the location",
    "slightly to the side near a window or corner, different lighting",
    "over-the-shoulder angle showing the background receding into depth",
    "three-quarter view revealing a different corner of the space",
    "wider framing showing more of the surrounding environment context",
    "close medium shot with background softly blurred behind characters",
    "camera at a low angle looking slightly upward at the characters",
    "slight high angle looking down, showing table/floor surface as foreground",
    "characters near the entrance or exit area, door or threshold visible",
    "characters positioned beside a distinctive feature: counter, shelf, window display",
]


def _detect_emotion(my_en: str, resp_en: str) -> str:
    """대화 내용에서 감정 키워드 탐지 → 표정 선택"""
    text = (my_en + " " + resp_en).lower()
    for keywords, emotion in _KEYWORD_EMOTIONS:
        if any(k in text for k in keywords):
            return emotion
    return None  # Claude가 자유롭게 선택


def _inject_characters(content: str, sit_id: int, situation: dict | None = None,
                       phrase_idx: int = 0) -> str:
    """'person/people' 등 인물 표현을 해당 상황 ID의 캐릭터 설명으로 교체.
    Imagen이 사람 대신 지정된 동물 캐릭터를 그리도록 유도한다."""
    local, learner = _pick_characters(sit_id, situation, phrase_idx)
    # 복수 인물 → 주인공(learner, LEFT) + 조연(local, RIGHT)
    content = re.sub(r'\btwo people\b',      f'{learner} on the left and {local} on the right',  content, flags=re.IGNORECASE)
    content = re.sub(r'\btwo persons\b',     f'{learner} on the left and {local} on the right',  content, flags=re.IGNORECASE)
    content = re.sub(r'\btwo figures\b',     f'{learner} on the left and {local} on the right',  content, flags=re.IGNORECASE)
    content = re.sub(r'\btwo characters\b',  f'{learner} on the left and {local} on the right',  content, flags=re.IGNORECASE)
    content = re.sub(r'\bpeople\b',          f'{learner} on the left and {local} on the right',  content, flags=re.IGNORECASE)
    # 젠더 단수
    content = re.sub(r'\ba young woman\b',   f'a {learner}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\ba young man\b',     f'a {local}',              content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe young woman\b', f'the {learner}',          content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe young man\b',   f'the {local}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\ba woman\b',         f'a {learner}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\ba man\b',           f'a {local}',              content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe woman\b',       f'the {learner}',          content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe man\b',         f'the {local}',            content, flags=re.IGNORECASE)
    # 일반 단수 인물
    content = re.sub(r'\ba person\b',        f'a {local}',              content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe person\b',      f'the {local}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\ba figure\b',        f'a {local}',              content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe figure\b',      f'the {local}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\bsomeone\b',         f'{local}',                content, flags=re.IGNORECASE)
    # 역할 표현 (대화 상황 특화)
    content = re.sub(r'\ba student\b',       f'a {learner}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe student\b',     f'the {learner}',          content, flags=re.IGNORECASE)
    content = re.sub(r'\ba learner\b',       f'a {learner}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe learner\b',     f'the {learner}',          content, flags=re.IGNORECASE)
    content = re.sub(r'\ba foreigner\b',     f'a {learner}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe foreigner\b',   f'the {learner}',          content, flags=re.IGNORECASE)
    content = re.sub(r'\ba visitor\b',       f'a {learner}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe visitor\b',     f'the {learner}',          content, flags=re.IGNORECASE)
    content = re.sub(r'\ba local\b',         f'a {local}',              content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe local\b',       f'the {local}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\ba teacher\b',       f'a {local}',              content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe teacher\b',     f'the {local}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\ba customer\b',      f'a {learner}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe customer\b',    f'the {learner}',          content, flags=re.IGNORECASE)
    content = re.sub(r'\ba vendor\b',        f'a {local}',              content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe vendor\b',      f'the {local}',            content, flags=re.IGNORECASE)
    return content


# ─── 웹툰 스타일 상수 ─────────────────────────────────────────
_WEBTOON_STYLE_BASE = (
    # ── 핵심 스타일 ── pastel watercolor 동화책 톤
    # Imagen은 "NOT X" 부정어가 무효 → 긍정 묘사로만 작성
    "soft pastel watercolor illustration, "
    "Korean and Japanese children's picture book style, kawaii storybook, "
    "thin delicate hand-drawn ink outlines — soft, slightly rounded, gentle even weight, "
    "watercolor washes are airy and translucent — colors bleed softly at edges, "
    "BACKGROUND ATMOSPHERE: soft pastel gradient — light and airy, gently fading tones, "
    "background is loose watercolor wash — simplified shapes, soft blurred edges, "
    "slightly faded and secondary — foreground subjects clearly stand out, "
    "PALETTE: soft mint, pale lavender, light sky blue, blush pink, soft peach, cream — "
    "light low-saturation pastel tones like gentle watercolor pigments on paper, "
    "paper grain subtly visible in wash areas, "
    "overall mood: bright, cheerful, gentle — like a beloved picture book, "

    # ── 주인공 vs 조연 ────────────────────────────────────────────
    "TWO DISTINCT CHARACTERS — they MUST look clearly different: "
    "PROTAGONIST (LEARNER): always a RED PANDA — orange-red fur with dark brown body, "
    "white facial markings, fluffy striped tail visible — "
    "positioned on the LEFT side of the frame. "
    "SUPPORTING CHARACTER: a completely DIFFERENT animal species "
    "with clearly different fur/body color (never orange, never red, never tan), "
    "positioned on the RIGHT side of the frame. "
    "DO NOT make both characters the same species or same color. "

    # ── 캐릭터 비율 ──────────────────────────────────────────────
    "CHARACTER PROPORTIONS: soft chibi plush-toy proportions — "
    "head is large and round (roughly 40-45% of total body height), "
    "body is round and compact, arms and legs are short but clearly visible, "
    "characters fill roughly 65% of the total frame height, "
    "both characters shown full-body from head to feet, "
    "NO footwear — bare paws only, "
    "overall silhouette: soft, round, squeezable like a quality stuffed animal, "

    # ── 눈/표정 ──────────────────────────────────────────────────
    "EYES: tiny round button eyes — fully dark iris filling the entire eye area, "
    "single tiny white sparkle dot only — NO visible white sclera, eyes look like shiny black beads, "
    "EXPRESSIVE FACES: each character shows a DISTINCT readable emotion — "
    "eyes and mouth clearly convey feeling (wide eyes for surprise, "
    "crescent eyes for joy, droopy eyes for worry, raised brow for confusion). "
    "Body language reinforces emotion (raised arms, bowed head, paw on cheek, pointing, etc.). "
    "STRICTLY AVOID thumbs-up gesture. "

    # ── 구도 ─────────────────────────────────────────────────────
    "square 1:1 composition, "
    "MEDIUM SHOT: both characters centered, heads in upper half, feet in lower half of frame, "
    "camera at character eye level, "
    "background elements visible at top and sides — characters in foreground, "

    # ── 탈것 구조 정확도 ──────────────────────────────────────────
    "VEHICLE INTERIOR ACCURACY (when scene is inside a vehicle): "
    "driver ALWAYS sits on the LEFT side behind the steering wheel facing FORWARD toward the windshield, "
    "passenger ALWAYS sits on the RIGHT side or behind the driver facing FORWARD, "
    "steering wheel is ALWAYS present in front of the driver and clearly visible, "
    "seats face the direction of travel — characters sit facing FORWARD, never sideways or backward unless explicitly a rear-facing seat, "
    "bus interior: driver on LEFT with steering wheel, fare machine/card reader on driver's right side near entrance, "
    "taxi interior: driver on LEFT front seat, passenger on RIGHT rear seat or front passenger seat, "
    "train/subway: bench seats face inward toward the aisle, doors on side walls, "
    "ALL spatial relationships in vehicles must be structurally correct and physically plausible. "

    # ── 텍스트 금지 ───────────────────────────────────────────────
    "ABSOLUTE NO TEXT: zero letters, zero words, zero numbers in any language anywhere — "
    "ALL signs, labels, screens must use visual symbols and pictograms only: "
    "pharmacy→red cross symbol, salon→scissors icon, restaurant→fork icon, "
    "cafe→coffee cup icon, hospital→red cross, store→colorful shelf display, "
    "phone screens→simple icon UI only, price tags→coin icon. "
    "EXCEPTION: 'TAXI' rooftop sign is allowed. "
    "All other text must be replaced with pictogram icons. "
    "NO readable text anywhere in the image"
)

def _webtoon_style(sit_id: int) -> str:
    return _WEBTOON_STYLE_BASE

# ─── 텍스트 유발 토큰 치환 ────────────────────────────────────
# 규칙: 글씨가 생성될 수 있는 요소 → 심볼/아이콘/형태로 대체
# 예외: TAXI 등 국제적으로 통용되는 고유명사 심볼은 허용
_BANNED_SUBSTITUTIONS = [
    # 간판/표지
    (r'\bshop sign\b',          'colorful awning with a simple icon symbol'),
    (r'\bstore sign\b',         'colorful awning with a simple icon symbol'),
    (r'\bsign\b',               'blank placard with a simple pictogram'),
    (r'\bbanner\b',             'hanging colored cloth decoration'),
    (r'\bposter\b',             'framed illustration on the wall'),
    (r'\blabel\b',              'small tag with a simple icon'),
    (r'\bprice tag\b',          'small coin-stack icon'),

    # 메뉴/식당
    (r'\bmenu board\b',         'illustrated food-picture display board'),
    (r'\bmenu\b',               'illustrated food-picture board'),
    (r'\bchalkboard\b',         'blank chalkboard with chalk drawing of food'),

    # 디지털 기기
    (r'\bsmartphone\b',         'small handheld device with a glowing screen showing simple icons'),
    (r'\bcell phone\b',         'small handheld device with glowing icon screen'),
    (r'\blaptop\b',             'open portable computer with abstract icon screen'),
    (r'\bscreen\b',             'glowing surface showing simple geometric icons'),
    (r'\bdisplay\b',            'glowing panel with simple pictogram icons'),
    (r'\bmonitor\b',            'glowing rectangular screen with simple icons'),

    # 인쇄물
    (r'\bnewspaper\b',          'folded paper printed with wavy decorative lines'),
    (r'\bmagazine\b',           'colorful booklet with illustrated cover'),
    (r'\bbook\b',               'illustrated storybook with picture cover'),
    (r'\bdocument\b',           'paper sheet with wavy-line pattern'),
    (r'\breceipt\b',            'small paper strip with dotted line pattern'),
    (r'\bticket\b',             'small colored card with stripe pattern'),
    (r'\bpassport\b',           'small dark booklet with embossed emblem'),
    (r'\bform\b',               'paper sheet with checkbox symbols'),

    # 장소
    (r'\bshop\b',               'room with product shelves'),
    (r'\bstore\b',              'room with displayed items'),
    (r'\bcaf[eé]\b',            'warm counter with coffee cup icons'),
    (r'\bentrance\b',           'open decorative doorway'),
    (r'\breception\b',          'front counter with bell icon'),

    # 교통
    (r'\bbus destination\b',    'bus with colored stripe pattern on front'),
    (r'\btrain board\b',        'departure board with clock and arrow symbols'),
    (r'\bflight board\b',       'departure board with airplane and clock symbols'),
    (r'\bplatform number\b',    'platform pillar with number symbol icon'),

    # 의료/업종별 심볼로 대체
    (r'\bpharmacy sign\b',      'storefront with red cross symbol'),
    (r'\bhospital sign\b',      'building with red cross emblem'),
    (r'\bhair salon sign\b',    'storefront with scissors icon'),
    (r'\brestaurant sign\b',    'storefront with fork-and-spoon icon'),
]

def _lint_prompt(prompt: str) -> str:
    """banned 토큰을 텍스트 유발 없는 안전한 표현으로 치환"""
    for pattern, replacement in _BANNED_SUBSTITUTIONS:
        prompt = re.sub(pattern, replacement, prompt, flags=re.IGNORECASE)
    return prompt


def _apply_style(content: str, sit_id: int = 0, situation: dict | None = None,
                 phrase_idx: int = 0) -> str:
    """장면 설명 + lint + 캐릭터 교체 + 웹툰 스타일"""
    return f"{_inject_characters(_lint_prompt(content), sit_id, situation, phrase_idx)}. {_webtoon_style(sit_id)}"


# ─── 진행 상황 추적 ──────────────────────────────────────────
def _load_progress() -> dict:
    try:
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"completed": {}, "failed": {}, "updated_at": None}


def _save_progress(data: dict):
    try:
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data["updated_at"] = datetime.now().isoformat()
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  [진행 저장 실패: {e}]")


def _mark_done(progress: dict, sit_id: int, key: str):
    sit_key = str(sit_id)
    if sit_key not in progress["completed"]:
        progress["completed"][sit_key] = []
    if key not in progress["completed"][sit_key]:
        progress["completed"][sit_key].append(key)
    progress["current"] = None
    _save_progress(progress)


def _mark_failed(progress: dict, sit_id: int, key: str, reason: str):
    sit_key = str(sit_id)
    if sit_key not in progress["failed"]:
        progress["failed"][sit_key] = {}
    progress["failed"][sit_key][key] = reason
    progress["current"] = None
    _save_progress(progress)


def _mark_current(progress: dict, sit_id: int, key: str):
    """현재 생성 중인 패널을 progress 파일에 기록 (대시보드 실시간 표시용)"""
    progress["current"] = {"sit_id": sit_id, "key": key}
    _save_progress(progress)


# ─── Claude API 장면 설명 생성 ───────────────────────────────
def _build_intro_scene(situation: dict, anthropic_client) -> str:
    """상황 인트로 패널 장면 설명 생성 (설정 샷)"""
    sit_id  = situation.get("id", 0)
    sit_ko  = situation.get("situation", "")
    sit_en  = situation.get("situation_en", "")
    cat     = situation.get("category", "")
    local_char, learner_char = _pick_characters(sit_id, situation)

    # DB에 미리 생성된 scene_prompt 우선 사용
    if situation.get("scene_prompt"):
        return situation["scene_prompt"]

    if anthropic_client is None:
        return (
            f"A modern Korean {sit_en.lower()} setting. "
            f"A cute {learner_char} and a {local_char} "
            f"with chibi proportions and friendly expressions, ready to interact."
        )

    try:
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": (
                    "You are an illustration director for a Korean language learning app.\n"
                    "Write a 2-sentence establishing shot description for a cute animal character panel.\n\n"
                    f"Situation: {sit_ko} ({sit_en})\n"
                    f"Category: {cat}\n"
                    f"PROTAGONIST (red panda, LARGER, LEFT side): {learner_char}\n"
                    f"SUPPORTING character (different animal, SMALLER, RIGHT side): {local_char}\n\n"
                    "RULES:\n"
                    "1. Describe a MODERN everyday Korean location (cafe, subway, office, park, etc.).\n"
                    "   Do NOT use traditional tile-roof hanok or wooden houses.\n"
                    "2. If including characters: the red panda is on the LEFT and LARGER, "
                    "   the supporting character is on the RIGHT and clearly SMALLER.\n"
                    "   They must look visually DIFFERENT — different colors, different sizes.\n"
                    "3. NO text, signs, labels, speech bubbles anywhere.\n"
                    "4. Focus on cozy warm atmosphere.\n"
                    "5. VEHICLE ACCURACY: If inside a vehicle — "
                    "driver on LEFT with steering wheel facing FORWARD, "
                    "passenger on RIGHT facing FORWARD, "
                    "steering wheel always visible, characters never sideways or backward.\n\n"
                    "Output: 2 sentences ONLY. No preamble."
                ),
            }],
        )
        return message.content[0].text.strip()
    except Exception as e:
        print(f"  [Claude 인트로 장면 실패: {e}] fallback 사용")
        return (
            f"A cozy modern Korean {sit_en.lower()} location. "
            f"On the left, a larger red panda ({learner_char}) faces right; "
            f"on the right, a smaller {local_char} faces left, ready to interact."
        )


def _build_phrase_scene(situation: dict, phrase: dict, anthropic_client,
                        phrase_idx: int = 0,
                        prior_poses: list | None = None) -> str:
    """대화 쌍별 패널 장면 설명 생성"""
    sit_id      = situation.get("id", 0)
    sit_ko      = situation.get("situation", "")
    sit_en      = situation.get("situation_en", "")
    my_ko       = phrase.get("my_line", {}).get("ko", "")
    my_en       = phrase.get("my_line", {}).get("en", "")
    resp_ko     = phrase.get("response", {}).get("ko", "")
    resp_en     = phrase.get("response", {}).get("en", "")
    tip         = phrase.get("tip", "")
    local_char, learner_char = _pick_characters(sit_id, situation, phrase_idx)

    # 패널 인덱스로 촬영 각도/서브공간 변주 힌트 선택
    view_hint = _PANEL_VARIATION_HINTS[phrase_idx % len(_PANEL_VARIATION_HINTS)]

    # DB에 미리 생성된 scene_prompt가 있으면 배경으로 사용 + 동작 설명 추가
    base_scene = situation.get("scene_prompt", "")

    if anthropic_client is None:
        action = (
            f"The {learner_char} gestures expressively while saying '{my_en}', "
            f"and the {local_char} responds warmly."
        )
        location = base_scene if base_scene else f"Inside a modern Korean {sit_en.lower()}"
        return f"{location}, {view_hint}. {action}"

    # 키워드 기반 감정 힌트 사전 계산
    detected_emotion = _detect_emotion(my_en, resp_en)
    emotion_hint = ""
    if detected_emotion and detected_emotion in _EXPRESSION_VOCAB:
        hint_cue = _EXPRESSION_VOCAB[detected_emotion]
        emotion_hint = f"Suggested emotion for protagonist: {detected_emotion} — {hint_cue}\n"

    # 표정 어휘집 (Claude 선택용)
    vocab_str = "\n".join(f"• {k}: {v}" for k, v in _EXPRESSION_VOCAB.items())

    try:
        setting_hint = (
            f"Background setting (already established): {base_scene}\n" if base_scene
            else f"Setting: soft minimalist Korean {sit_en.lower()}\n"
        )
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=220,
            messages=[{
                "role": "user",
                "content": (
                    "You are an illustration director for a Korean language learning app.\n"
                    "Write 1-2 sentences describing the scene for this dialogue panel.\n\n"
                    f"{setting_hint}"
                    f"PANEL CAMERA/AREA: {view_hint}\n"
                    f"LEFT character — PROTAGONIST (red panda, LARGER): {learner_char} — says: '{my_en}'\n"
                    f"RIGHT character — SUPPORTING (different animal, SMALLER, clearly different color): {local_char} — responds: '{resp_en}'\n"
                    + (f"Tip: {tip}\n" if tip else "")
                    + (emotion_hint if emotion_hint else "")
                    + "\nEXPRESSION VOCABULARY — pick the most fitting emotion for each character:\n"
                    + vocab_str + "\n\n"
                    + (
                        "POSE VARIETY RULE — these poses were already used in previous panels, "
                        "choose COMPLETELY DIFFERENT body positions and gestures:\n"
                        + "\n".join(f"  - {p}" for p in prior_poses[-6:]) + "\n\n"
                        if prior_poses else ""
                    )
                    + "RULES:\n"
                    "1. CONSISTENCY: The SAME two characters appear throughout this entire scene — "
                    "same species, same fur/body color, same outfit as the intro panel. "
                    "DO NOT change species, color, or clothing between panels.\n"
                    "2. LOCATION: Keep the same background setting as the intro panel. "
                    "Vary only the camera angle/sub-area (use PANEL CAMERA/AREA hint).\n"
                    "3. DIFFERENTIATION via ACTION+EXPRESSION only: "
                    "Each panel must show a DIFFERENT body pose, gesture, and facial expression. "
                    "Describe SPECIFIC concrete visuals: eye shape, mouth, paw position, "
                    "lean direction, blush, sweat drop, item being held/handed, etc.\n"
                    "4. First sentence: camera angle + location sub-area for this panel.\n"
                    "5. Second sentence: specific actions and expressions matching the dialogue.\n"
                    "6. AVOID: repeating poses from previous panels, generic 'warm smile', "
                    "thumbs-up gesture. USE: pointing, handing item, bowing, gesturing direction, "
                    "covering mouth in shock, leaning forward, reaching out, patting shoulder.\n"
                    "7. Protagonist is LEFT and LARGER; supporting is RIGHT and SMALLER.\n"
                    "8. VEHICLE ACCURACY: If the scene is inside a vehicle — "
                    "driver ALWAYS sits on the LEFT behind the steering wheel facing FORWARD; "
                    "passenger sits on RIGHT or behind, also facing FORWARD; "
                    "steering wheel MUST be visible in front of driver; "
                    "characters NEVER sit sideways or backward; "
                    "bus fare card reader is near the entrance on driver's right; "
                    "ALL seating and spatial positions must be physically correct.\n"
                    "Output: 1-2 sentences ONLY, no preamble."
                ),
            }],
        )
        action = message.content[0].text.strip()
        return action
    except Exception as e:
        print(f"  [Claude 대화 장면 실패: {e}] fallback 사용")
        fallback_emotion = _FALLBACK_EXPRESSIONS[phrase_idx % len(_FALLBACK_EXPRESSIONS)]
        fallback_cue = _EXPRESSION_VOCAB[fallback_emotion]
        action = (
            f"The {learner_char} shows a {fallback_emotion} expression ({fallback_cue}), "
            f"while the {local_char} reacts with a complementary gesture."
        )
        location = base_scene if base_scene else f"Inside a modern Korean {sit_en.lower()}"
        return (
            f"{location}, {view_hint}. "
            + action
        )


_IMAGE_MODEL   = "gemini-3.1-flash-image-preview"
_CHARS_DIR     = _SCRIPT_DIR / "assets" / "characters"


def _load_char_refs() -> list:
    """캐릭터 레퍼런스 이미지 로드 (PIL Image 리스트)"""
    from PIL import Image as PILImage
    refs = []
    # 1) 주인공 레퍼런스 (항상 포함)
    main = _CHARS_DIR / "main_character.png"
    if main.exists():
        try:
            refs.append(PILImage.open(str(main)).convert("RGB"))
        except Exception:
            pass
    # 2) extra 캐릭터 시트 (있는 것 모두 포함)
    for extra in sorted(_CHARS_DIR.glob("extra_characters*.png")):
        try:
            refs.append(PILImage.open(str(extra)).convert("RGB"))
        except Exception:
            pass
    return refs


# ─── 상황 카테고리별 주인공 의상 ─────────────────────────────
_CATEGORY_OUTFITS = {
    # 가방 있음 — 이동/외출이 주목적인 카테고리
    "여행":       "travel outfit: light jacket with a crossbody bag",
    "쇼핑":       "casual outfit, holding a shopping bag in hand",
    "비즈니스":   "business casual — collared shirt and neat trousers, carrying a slim work bag",
    # 가방 없음 — 목적지 도착 후 활동이 주인 카테고리
    "식사":       "casual everyday clothes, no bag",
    "의료":       "casual comfortable clothes, no bag",
    "인사":       "neat smart-casual outfit, no bag",
    "일상":       "everyday casual wear, no bag",
    "주거":       "home casual wear, cozy sweater, no bag",
    "여가":       "relaxed leisure outfit matching the activity, no bag",
    "K-Culture":  "trendy Korean street fashion, stylish casual, no bag",
}
_DEFAULT_OUTFIT = "casual everyday outfit, no bag"


def _get_main_char_outfit(situation: dict) -> str:
    cat    = situation.get("category", "")
    sit_en = situation.get("situation_en", "").lower()
    sit_ko = situation.get("situation", "").lower()

    # ── 가방이 자연스러운 상황 ──────────────────────────────────
    # 이동/여행
    if any(k in sit_en for k in ("airport", "customs", "departure", "arrival", "boarding", "check-in")):
        return "travel outfit with a carry-on bag and passport in hand"
    if any(k in sit_en for k in ("ktx", "train station", "bus terminal", "bus station")):
        return "travel outfit with a rolling suitcase or backpack"
    if any(k in sit_en for k in ("taxi", "subway", "commut", "transfer")):
        return "casual outfit with a small crossbody bag"
    if any(k in sit_en for k in ("sightseeing", "tourist", "tour", "hiking", "mountain", "camping", "outdoor")):
        return "outdoor casual outfit with a light backpack"
    if any(k in sit_en for k in ("library", "study cafe", "study room")):
        return "casual outfit with a backpack"
    if any(k in sit_en for k in ("school", "class", "classroom", "university", "college", "lecture")):
        return "school casual outfit with a backpack"
    if any(k in sit_en for k in ("office", "workplace", "work", "meeting", "conference", "business")):
        return "business casual — collared shirt and neat trousers, carrying a slim work bag"
    if any(k in sit_en for k in ("shopping", "mart", "supermarket", "grocery", "market", "convenience store")):
        return "casual outfit, holding a shopping basket or bag"
    if any(k in sit_en for k in ("picnic", "park", "festival", "street food", "outdoor event")):
        return "casual outfit with a small crossbody bag"

    # ── 가방이 불필요한 상황 ────────────────────────────────────
    if any(k in sit_en for k in ("restaurant", "dining", "eating", "food", "meal", "cafe", "coffee", "bakery", "dessert")):
        return "casual everyday clothes, no bag"
    if any(k in sit_en for k in ("hospital", "clinic", "emergency", "pharmacy", "doctor", "medical")):
        return "casual comfortable clothes, no bag"
    if any(k in sit_en for k in ("hair salon", "beauty salon", "barbershop", "nail", "spa")):
        return "casual clothes, no bag"
    if any(k in sit_en for k in ("karaoke", "singing", "norebang")):
        return "fun casual outfit, no bag"
    if any(k in sit_en for k in ("sauna", "jimjilbang", "bath", "hot spring", "jjimjil")):
        return "light lounge wear, no bag"
    if any(k in sit_en for k in ("gym", "fitness", "workout", "exercise", "sport", "swimming", "pool")):
        return "sporty activewear, no bag"
    if any(k in sit_en for k in ("beach", "sea", "ocean", "resort")):
        return "summer casual with a sunhat, no bag"
    if any(k in sit_en for k in ("home", "house", "apartment", "moving", "neighbor", "landlord")):
        return "home casual wear, cozy sweater, no bag"
    if any(k in sit_en for k in ("hotel", "accommodation", "check in", "hostel", "guesthouse")):
        return "travel casual outfit, no bag (already checked in)"
    if any(k in sit_en for k in ("interview", "job", "recruit", "hiring")):
        return "neat business formal suit, no bag"
    if any(k in sit_en for k in ("party", "wedding", "ceremony", "celebration", "banquet")):
        return "smart casual party outfit, no bag"
    if any(k in sit_en for k in ("bbq", "barbecue", "grilling")):
        return "casual clothes with a light apron, no bag"
    if any(k in sit_en for k in ("post office", "bank", "government", "office visit", "service center")):
        return "casual neat outfit, no bag"

    return _CATEGORY_OUTFITS.get(cat, _DEFAULT_OUTFIT)


def _build_char_instruction(situation: dict, phrase_idx: int = 0,
                            is_first_panel: bool = False) -> str:
    outfit = _get_main_char_outfit(situation)
    sit_id = situation.get("id", 0)
    local_char, _ = _pick_characters(sit_id, situation, phrase_idx)

    # 첫 패널(intro/phrase_0)은 캐릭터 확립, 이후 패널은 "동일 캐릭터 유지" 강조
    if is_first_panel:
        consistency_note = (
            "ESTABLISH THESE TWO CHARACTERS — they will appear in ALL panels of this scene "
            "with the EXACT SAME species, fur color, and outfit throughout.\n"
        )
    else:
        consistency_note = (
            "⚠️ VISUAL CONSISTENCY REQUIRED: Use the EXACT SAME characters as the intro panel.\n"
            f"  LEFT: red panda — orange-red fur, white markings, {outfit}\n"
            f"  RIGHT: {local_char}\n"
            "Same species, same fur color, same outfit in EVERY panel. "
            "DIFFERENTIATE only via: expression, body pose, gesture, camera angle.\n"
        )

    return (
        "CHARACTER REFERENCE IMAGES ARE PROVIDED ABOVE.\n\n"
        "=== STYLE FIRST — MATCH THE REFERENCE IMAGES ===\n"
        "Draw in the EXACT SAME STYLE as the reference character images: "
        "soft pastel watercolor, Korean/Japanese children's picture book (kawaii storybook), "
        "thin delicate ink outlines, airy translucent watercolor washes, "
        "soft pastel gradient background — light and airy tones, "
        "chibi plush-toy proportions — large round head (40-45% of height), round compact body, short visible limbs. "
        "Tiny button eyes — fully dark, shiny bead-like, single white sparkle dot only, NO white sclera.\n\n"
        "=== FRAMING ===\n"
        "CLOSE MEDIUM SHOT: two characters fill the CENTER of the square frame. "
        "Heads near upper-center, feet near lower-center. "
        "Background at top and sides only — NOT dominating the lower half. "
        "Camera at character eye level. Do NOT push characters to the bottom.\n\n"
        "=== TWO CHARACTERS ===\n"
        f"LEFT — PROTAGONIST (RED PANDA): match the reference image exactly. "
        f"Orange-red fur, dark brown body, white facial markings, fluffy striped tail. "
        f"Outfit: {outfit}.\n"
        f"RIGHT — SUPPORTING CHARACTER: a {local_char}. "
        f"Must be clearly DIFFERENT color from the red panda (NOT orange/red/tan). "
        f"Same watercolor storybook style as the protagonist.\n"
        "The two characters must look CLEARLY DIFFERENT — different species, different colors, different sizes.\n"
        f"{consistency_note}\n"
    )


def _save_generated_image(response, output_path: Path) -> bool:
    """generate_content 응답에서 이미지를 꺼내 저장. 성공 시 True 반환."""
    parts = []
    try:
        parts = response.candidates[0].content.parts
    except Exception:
        try:
            parts = response.parts
        except Exception:
            return False
    for part in parts:
        try:
            if part.inline_data and part.inline_data.data:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)
                return True
        except Exception:
            continue
    return False


# ─── Gemini Flash Image 생성 ─────────────────────────────────
def _generate_image(prompt: str, output_path: Path, genai_client,
                    sit_id: int = 0, situation: dict | None = None,
                    phrase_idx: int = 0, is_first_panel: bool = False) -> bool:
    """Gemini Flash Image로 단일 이미지 생성 (캐릭터 레퍼런스 포함)"""
    if output_path.exists() and output_path.stat().st_size > 0:
        return True
    elif output_path.exists():
        output_path.unlink()

    char_instruction = _build_char_instruction(situation or {}, phrase_idx, is_first_panel)
    full_prompt = char_instruction + _apply_style(_lint_prompt(prompt), sit_id, situation, phrase_idx)

    # 캐릭터 레퍼런스 이미지 로드
    char_refs = _load_char_refs()

    # contents = [ref_img1, ref_img2, ..., text_prompt]
    contents = char_refs + [full_prompt]

    try:
        response = genai_client.models.generate_content(
            model=_IMAGE_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=[types.Modality.IMAGE],
                image_config=types.ImageConfig(aspect_ratio="1:1"),
            ),
        )
        if _save_generated_image(response, output_path):
            return True
        print(f"  [빈 응답] 이미지 없음: {output_path.name}")
        return False
    except Exception as e:
        print(f"  [생성 오류: {e}] {output_path.name}")
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print("\n[중단] API 일일 할당량 초과 — 내일 다시 시도하세요.")
            raise SystemExit(1)
        return False


# ─── 상황별 일러스트 생성 ────────────────────────────────────
def generate_situation(situation: dict, genai_client, anthropic_client,
                       progress: dict, intro_only: bool = False) -> tuple[int, int]:
    """단일 상황의 모든 패널 생성. (done, fail) 반환"""
    sit_id  = situation["id"]
    sit_ko  = situation.get("situation", "")
    sit_en  = situation.get("situation_en", "")
    phrases = situation.get("phrases", [])
    sit_dir = OUTPUT_DIR / f"sit_{sit_id}"
    sit_dir.mkdir(parents=True, exist_ok=True)

    done, fail = 0, 0

    # ── 상황 전체에서 쓸 캐릭터/의상/배경 한 번만 결정 ──────────
    local_char, learner_char = _pick_characters(sit_id, situation)
    main_outfit   = _get_main_char_outfit(situation)
    supp_outfit   = _get_supporting_char_outfit(situation)
    base_scene_bg = situation.get("scene_prompt", f"Modern Korean {sit_en.lower()} location")
    print(f"  [캐릭터] 주인공: red panda ({main_outfit})")
    print(f"  [캐릭터] 조연:   {local_char}")
    print(f"  [배경]   {base_scene_bg[:60]}...")

    # 1. 인트로 (설정 샷) — is_first_panel=True 로 캐릭터 확립
    intro_path = sit_dir / "intro.png"
    intro_key  = "intro"
    if not (intro_path.exists() and intro_path.stat().st_size > 0):
        print(f"  [인트로] {sit_ko} ({sit_en})")
        _mark_current(progress, sit_id, intro_key)
        scene = _build_intro_scene(situation, anthropic_client)
        print(f"    장면: {scene[:80]}...")
        if _generate_image(scene, intro_path, genai_client, sit_id, situation,
                           phrase_idx=0, is_first_panel=True):
            done += 1
            _mark_done(progress, sit_id, intro_key)
            print(f"    [OK] intro.png")
        else:
            fail += 1
            _mark_failed(progress, sit_id, intro_key, "generation failed")
            print(f"    [FAIL] intro.png")
        time.sleep(0.5)
    else:
        print(f"  [스킵] intro.png (이미 존재)")
        done += 1

    if intro_only:
        return done, fail

    # 2. 대화 쌍별 패널 — 동일 캐릭터/배경, 동작·표정·구도로만 차별화
    used_poses: list[str] = []  # 이 상황 내 이미 쓴 포즈/표정 요약
    for phrase_loop_idx, phrase in enumerate(phrases):
        ph_id   = phrase["id"]
        ph_key  = f"phrase_{ph_id}"
        ph_path = sit_dir / f"phrase_{ph_id}.png"

        if ph_path.exists() and ph_path.stat().st_size > 0:
            print(f"  [스킵] phrase_{ph_id}.png (이미 존재)")
            done += 1
            continue

        my_en = phrase.get("my_line", {}).get("en", "")
        print(f"  [phrase_{ph_id}] '{my_en[:50]}'")
        _mark_current(progress, sit_id, ph_key)
        scene = _build_phrase_scene(
            situation, phrase, anthropic_client,
            phrase_idx=phrase_loop_idx,
            prior_poses=used_poses if used_poses else None,
        )
        used_poses.append(scene[:80])  # 포즈 힌트로 앞 80자 기록
        print(f"    장면: {scene[:80]}...")
        # phrase_0 이후는 모두 is_first_panel=False → 일관성 강조 프롬프트 사용
        if _generate_image(scene, ph_path, genai_client, sit_id, situation,
                           phrase_idx=phrase_loop_idx, is_first_panel=False):
            done += 1
            _mark_done(progress, sit_id, ph_key)
            print(f"    [OK] phrase_{ph_id}.png")
        else:
            fail += 1
            _mark_failed(progress, sit_id, ph_key, "generation failed")
            print(f"    [FAIL] phrase_{ph_id}.png")
        time.sleep(0.5)

    return done, fail


# ─── 상태 출력 ───────────────────────────────────────────────
def print_status(db: list):
    progress = _load_progress()
    completed = progress.get("completed", {})
    failed    = progress.get("failed", {})

    total_sit    = len(db)
    total_panels = sum(1 + len(s.get("phrases", [])) for s in db)
    done_panels  = sum(len(v) for v in completed.values())
    fail_panels  = sum(len(v) for v in failed.values())

    print(f"\n=== 진행 상황 ===")
    print(f"상황 수:        {total_sit}")
    print(f"전체 패널:      {total_panels}")
    print(f"완료:           {done_panels}")
    print(f"실패:           {fail_panels}")
    print(f"미완료:         {total_panels - done_panels - fail_panels}")
    if progress.get("updated_at"):
        print(f"마지막 업데이트: {progress['updated_at']}")

    print(f"\n상황별 상세:")
    for sit in db:
        sid  = str(sit["id"])
        name = sit.get("situation", "")
        en   = sit.get("situation_en", "")
        n_phrases = len(sit.get("phrases", []))
        n_total   = 1 + n_phrases
        n_done    = len(completed.get(sid, []))
        n_fail    = len(failed.get(sid, {}) if isinstance(failed.get(sid), dict) else [])
        status = "완료" if n_done >= n_total else f"{n_done}/{n_total}"
        print(f"  sit_{sit['id']:03d} {name} ({en}): {status}"
              + (f" [실패:{n_fail}]" if n_fail else ""))


# ─── 메인 ────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="대화 상황별 웹툰 패널 일러스트 생성")
    parser.add_argument("--db", default=str(PHRASES_DB_PATH), help="phrases_db.json 경로")
    parser.add_argument("--start", type=int, default=None, help="시작 상황 ID")
    parser.add_argument("--end",   type=int, default=None, help="끝 상황 ID (포함)")
    parser.add_argument("--situation-id", type=int, default=None, help="단일 상황 ID")
    parser.add_argument("--intro-only", action="store_true", help="인트로 패널만 생성")
    parser.add_argument("--status", action="store_true", help="진행 상황 출력 후 종료")
    args = parser.parse_args()

    # API 키 확인
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        print("오류: GEMINI_API_KEY 환경변수가 없습니다.")
        print("  → https://aistudio.google.com 에서 API 키 발급 후 .env에 추가")
        return

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not anthropic_key:
        print("경고: ANTHROPIC_API_KEY 없음 — 장면 설명 fallback 모드로 실행")
        anthropic_client = None
    else:
        try:
            import anthropic
            anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
        except ImportError:
            print("경고: anthropic 패키지 없음 — pip install anthropic")
            anthropic_client = None

    # DB 로드
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"오류: DB 파일 없음: {db_path}")
        return
    with open(db_path, encoding="utf-8") as f:
        db = json.load(f)
    print(f"DB 로드: {len(db)}개 상황")

    # 상태 출력 모드
    if args.status:
        print_status(db)
        return

    # Imagen 클라이언트 초기화
    genai_client = genai.Client(api_key=gemini_key)

    # 처리 대상 필터링
    if args.situation_id is not None:
        targets = [s for s in db if s["id"] == args.situation_id]
        if not targets:
            print(f"오류: 상황 ID {args.situation_id}를 찾을 수 없습니다")
            return
    elif args.start is not None or args.end is not None:
        s = args.start if args.start is not None else 1
        e = args.end   if args.end   is not None else max(x["id"] for x in db)
        targets = [x for x in db if s <= x["id"] <= e]
    else:
        targets = db

    print(f"처리 대상: {len(targets)}개 상황")
    if args.intro_only:
        print("모드: 인트로 패널만")

    progress = _load_progress()
    total_done = 0
    total_fail = 0

    for i, situation in enumerate(targets):
        sit_id = situation["id"]
        sit_ko = situation.get("situation", "")
        n_phrases = len(situation.get("phrases", []))
        print(f"\n[{i+1}/{len(targets)}] sit_{sit_id}: {sit_ko} ({n_phrases}개 대화)")

        done, fail = generate_situation(
            situation, genai_client, anthropic_client,
            progress, intro_only=args.intro_only,
        )
        total_done += done
        total_fail += fail
        print(f"  → 완료: {done}, 실패: {fail}")

    print(f"\n=== 완료 ===")
    print(f"총 완료: {total_done}, 총 실패: {total_fail}")
    print(f"출력 경로: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
