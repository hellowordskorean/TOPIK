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
import hashlib
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

# ── 카메라 구도 선택지 — 장면 디렉터가 대사에 맞는 구도를 "고르는" 메뉴.
# (2026-08-09) 예전에는 phrase_idx로 구도를 고정 배정해서 모든 상황의 N번 예문이
# 똑같은 앵글로 그려졌다. 이제는 디렉터가 대사 내용에 맞는 구도를 직접 고르고,
# 같은 상황에서 이미 쓴 구도는 피하도록만 제약한다. fallback 경로에서만 인덱스 대신
# 대사 해시로 하나 뽑아 쓴다.
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
    # ── 핵심 스타일 ─────────────────────────────────────────────
    # Imagen은 "NOT X" 부정어가 무효 → 긍정 묘사로만 작성

    #"soft pastel watercolor illustration, "
    #"Korean and Japanese children's picture book style, kawaii storybook, "
    #"thin delicate hand-drawn ink outlines — soft, slightly rounded, gentle even weight, "
    #"watercolor washes are airy and translucent — colors bleed softly at edges, "
    #"BACKGROUND ATMOSPHERE: warm peachy-cream gradient — soft peach at top fading to "
    #"warm cream-white at bottom, like gentle morning sunlight through frosted glass, "
    #"background is loose watercolor wash — simplified shapes, soft blurred edges, "
    #"PALETTE: warm cream, soft peach, dusty sage, muted terracotta, warm tan, soft sky blue — "
    #"warm low-saturation tones like faded watercolor pigments on paper, "
    #"paper grain subtly visible in wash areas, "
    #"overall mood: warm, cozy, heartwarming — like a beloved picture book, "

    "warm watercolor and pencil sketch illustration style, "
    "soft loose brushwork with visible watercolor paper texture, "
    "gentle pencil outlines (not thick black ink), "
    "watercolor wash backgrounds that are slightly soft and misty, "
    # 2026-07-21: "time of day matches the scene naturally"가 시장/식당 장면에서 저녁+등불
    # 조명(황금빛 고채도)을 유발 → 낮 기본값으로 고정. 밤은 대사가 명시할 때만.
    "soft bright daytime lighting by default — gentle diffused morning or afternoon light, "
    "use evening or night ONLY when the dialogue explicitly happens at night, "
    "never golden-hour glow, never lantern-lit amber cast, "
    "pastel palette: ivory white, soft sky-blue, dusty rose, sage green, "
    "light lavender, muted mint — balanced tones, not overly yellow or orange, "
    "NO neon colors, NO dark or black-dominant areas, "
    "IF animal characters appear: cute chibi anthropomorphic proportions, "
    "PROTAGONIST RULE — STRICTLY ENFORCED: the main character is ALWAYS a red panda — "
    "supporting/secondary characters can be any other cute animal but MUST be smaller "
    "or equal in size to the protagonist red panda, NEVER taller. "
    "PROTAGONIST CANONICAL PROPORTIONS — the attached reference character sheet is the ONLY "
    "source of truth: copy the red panda's head:body ratio, head size, and limb lengths "
    "EXACTLY as drawn in the reference sheet, identical in every illustration: "
    "1) total head height ≈ 1.0 unit, total body height ≈ 1.2 units (excluding legs), "
    "   head:body ratio is exactly 1 : 1.2 (head is larger and dominant), "
    "2) overall character height = 45% of the frame height (±5% tolerance only), "
    "3) head shape: perfectly round, very large, takes up roughly the top 45% of the silhouette, "
    "4) body shape: short, plump, oval-egg torso, no visible neck — head sits directly on shoulders, "
    "5) arms: short stubby pillars, length ≈ 0.4 of body height, rounded paw tips no fingers, "
    "6) legs: extremely short and stubby, length ≈ 0.3 of body height, barely separated stance, "
    "7) tail: bushy striped fox-like tail, length ≈ 1.0 of body height, ringed with 4–5 dark bands, "
    "8) ears: two small triangular ears on top of the head with white inner fluff, "
    "9) face: large dark eyes 35% of face width, small dot nose, tiny smile, white muzzle and eyebrow patches, "
    "10) fur color: warm rust-orange body, white face mask + ears + chest, dark brown limbs and ringed tail, "
    "11) outline: clean soft watercolor outline, no thick black bold strokes, "
    "ABSOLUTELY DO NOT change these proportions across illustrations — same character every time, like a brand mascot. "
    "ABSOLUTELY DO NOT add: thin tall human-like body, long humanoid legs, slender torso, "
    "muscular limbs, realistic adult proportions, large feet, fingers, knees, elbows, "
    "shoes, boots, sandals, sneakers, or any footwear (bare paws ONLY). "
    "characters naturally centered in the composition, fully visible head to feet, "
    "characters have slightly more detail/contrast than the soft background, "
    "background reflects MODERN everyday Korean life — "
    "STRICTLY AVOID: traditional tile-roof houses (기와집), wooden hanok structures, "
    "paper screen doors, traditional courtyards — these are tourist sites, not daily life. "
    "USE INSTEAD: concrete apartment buildings, modern cafes, convenience stores (24h), "
    "subway stations, school classrooms, offices, city parks, pedestrian streets, "
    "supermarkets, modern restaurants — whatever the scene naturally calls for. "
    "Background is soft and slightly faded. "
    "depth: foreground subjects sharp, background gently blurred/misty, "
    "square 1:1 composition, "
    "FIXED FRAMING — IDENTICAL in every illustration: medium shot, camera at character eye level, "
    "red panda total height ≈ 45% of the frame height (±5% tolerance only; "
    "in split-screen phone-call panels judge the height within the character's own half), "
    "main subject centered naturally — balanced, well-composed scene. "



    # ── 주인공 vs 조연 ────────────────────────────────────────────
    # 2026-07-22: 분할화면(phone-call)/솔로 패널과 충돌하지 않도록 기본 레이아웃임을 명시
    "DEFAULT CHARACTER LAYOUT — applies to face-to-face panels; if the FRAMING section above "
    "specifies a phone-call panel, a front-door handoff, or a solo panel, "
    "THAT layout OVERRIDES this: "
    "TWO DISTINCT CHARACTERS — they MUST look clearly different: "
    "PROTAGONIST (LEARNER): always a RED PANDA — orange-red fur with dark brown body, "
    "white facial markings, fluffy striped tail visible — "
    "positioned on the LEFT side of the frame. "
    "SUPPORTING CHARACTER: a completely DIFFERENT animal species "
    "with clearly different fur/body color (never orange, never red, never tan), "
    "positioned on the RIGHT side of the frame. "
    "DO NOT make both characters the same species or same color. "

    # ── 캐릭터 비율 / 눈 ─────────────────────────────────────────
    # 2026-07-21: 주인공 비율 1~11항이 위 핵심 스타일 블록과 통째로 중복돼 팔레트 지시를
    # 희석시키던 것 정리 — 비율 규칙은 위 블록 한 곳만 유지.
    "CHARACTERS: all characters are cute chibi cartoon animals. "
    "Supporting characters: other cute animals with clearly different colors. "
    "Total character height ≈ 45% of frame height (±5% tolerance only) — IDENTICAL in every illustration. "
    "Characters fully visible head to feet, centered in composition. "
    "EYES: small bead-like eyes — tiny dark circle with a single white highlight dot, "
    "sclera is warm cream-white, eye overall is small and simple. "

    # ── 표정 ──────────────────────────────────────────────────────
    "EXPRESSIVE FACES: each character shows a DISTINCT readable emotion — "
    "eyes and mouth clearly convey feeling (wide eyes for surprise, "
    "crescent eyes for joy, droopy eyes for worry, raised brow for confusion). "
    "Body language reinforces emotion — use VARIED poses from this list: "
    "handing item over with both paws, clutching item to chest, holding paper/card out, "
    "deep bow with head down, slight nod-bow with hand on chest, "
    "open both palms forward (explaining), sweeping arm to show direction, "
    "paw on own cheek (flustered), both paws to cheeks (surprised), "
    "one paw over mouth (shocked), paw on chin (thinking), scratching head, "
    "leaning forward attentively, patting the other character's shoulder, "
    "arms slightly raised at sides (cheerful), shrug with raised shoulders, "
    "waving hello/goodbye, reaching out one paw, crossing arms, "
    "tapping a counter/screen, writing or signing something, "
    "holding up a card/passport/phone, pointing direction with full open hand (NOT index finger). "
    "Index-finger-only raised pose: use SPARINGLY — at most once per scene. "
    "STRICTLY AVOID thumbs-up gesture. "

    # ── 구도 ─────────────────────────────────────────────────────
    "square 1:1 composition, "
    # 2026-07-22: 분할화면/솔로 패널에서는 FRAMING 섹션이 우선함을 명시
    "MEDIUM SHOT (default — the FRAMING section above OVERRIDES this for phone-call, "
    "front-door handoff, or solo panels): both characters centered in the frame, "
    "heads near upper-center, feet near lower-center, soft background space around them, "
    "camera at character eye level, "
    # 2026-07-21: 직원-손님 대화인데 둘 다 카운터 앞에 나란히 서 있던 문제 교정
    "ROLE-ACCURATE STAGING (face-to-face service scenes ONLY — never applies to phone-call "
    "panels where the speakers are in different places): "
    "when the supporting character is serving the protagonist "
    "(cashier, store clerk, restaurant staff, barista, pharmacist, receptionist, "
    "ticket agent, bank teller, nurse at reception): the supporting character stands "
    "BEHIND the counter/register/desk at their work station, and the protagonist stands "
    "IN FRONT of it as the customer — the counter surface runs between the two characters. "
    "NEVER place a staff member on the customer side casually chatting side-by-side. "
    "A doctor sits at the exam desk, a taxi driver sits in the driver's seat, "
    "a hair stylist stands behind the styling chair — each role occupies its real work position, "

    # ── 탈것 구조 정확도 (조건부) ─────────────────────────────────
    "LOCATION FOLLOWS THE DIALOGUE: "
    "transport-themed scenes do NOT default to a vehicle interior — many transport conversations "
    "happen at ticket counters, station halls, platforms, boarding gates, sidewalks, or bus stops. "
    "Use the scene description above to decide where the panel actually takes place; "
    "if it says counter/platform/sidewalk/station, render that environment, NOT a vehicle interior. "
    "VEHICLE INTERIOR ACCURACY — apply ONLY when the panel description explicitly places the scene "
    "inside a moving vehicle (seats, aisle, windows passing scenery, steering wheel, etc.): "
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
    "NO readable text anywhere in the image. "

    # ── 최종 색감/밀도 앵커 (2026-07-21 신설) ────────────────────
    # 프롬프트 맨 끝 = 모델 가중치가 가장 높은 위치. 단어 일러스트와 톤을 맞추기 위한
    # 세피아/고채도/과밀 배경 교정. 지우면 시장·식당 장면이 다시 황금빛으로 물듦.
    "FINAL COLOR AND DENSITY RULES — HIGHEST PRIORITY, THESE OVERRIDE EVERYTHING ABOVE: "
    "overall HIGH-KEY, LIGHT and AIRY pastel image on soft ivory-white watercolor paper, "
    "background heavily faded, desaturated and misty — a pale washed-out suggestion "
    "of the location, not a fully painted set, "
    "at least one third of the frame stays as soft empty breathing space, "
    "maximum 2-3 muted accent colors in the entire scene, "
    "props kept minimal — only the items this dialogue actually needs, "
    "NO sepia or golden-amber overall cast, NO lanterns, NO rainbow-colored awnings, "
    "NO bunting or festival decorations, NO string lights, "
    "NO densely packed shelves or walls of colorful goods, "
    "the same light gentle pastel tone as a children's picture book page"
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

    # 2026-07-21: DB scene_prompt를 그대로 반환하던 로직 제거 — 구버전 프롬프트에 박힌
    # 고채도 지시("cheerful red-and-yellow color scheme" 등)와 뒤바뀐 캐릭터 좌우/종이
    # 그대로 재현되던 원인. Claude가 있으면 항상 새 규칙으로 재작성하고 DB는 장소 힌트로만 사용.
    db_scene = situation.get("scene_prompt", "")
    if db_scene and anthropic_client is None:
        return db_scene

    if anthropic_client is None:
        return (
            f"A modern Korean setting suggesting the broader {sit_en.lower()} context. "
            f"A cute {learner_char} and a {local_char} "
            f"with chibi proportions and friendly expressions, ready to interact."
        )

    try:
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=280,
            messages=[{
                "role": "user",
                "content": (
                    "You are an illustration director for a Korean language learning app.\n"
                    "Write a 2-sentence establishing shot description for a cute animal character panel.\n\n"
                    f"Situation: {sit_ko} ({sit_en})\n"
                    f"Category: {cat}\n"
                    + (
                        "⚠️ REMOTE-BY-DEFAULT SITUATION: this situation's theme is inherently "
                        "remote (phone/text/online/delivery), so output 'STAGING: phone-call' "
                        "and set the LEFT half at the protagonist's home.\n"
                        if _is_remote_theme(situation) else ""
                    )
                    + (f"Location hint from database (use ONLY for the location idea — "
                       f"IGNORE any color scheme, character species, or left/right placement "
                       f"written in it, they are outdated): {db_scene}\n" if db_scene else "")
                    + f"PROTAGONIST (red panda, LARGER, LEFT side): {learner_char}\n"
                    f"SUPPORTING character (different animal, SMALLER, RIGHT side): {local_char}\n\n"
                    "RULES:\n"
                    "1. Describe a MODERN everyday Korean setting that captures the BROADER theme of "
                    "   this situation (cafe, subway, office, park, etc.). The intro shot is the WORLD "
                    "   the conversation happens in — not necessarily one fixed spot.\n"
                    "   For TRANSPORT themes (KTX/train, bus, taxi, subway): the intro should suggest the "
                    "   transport context as a whole — e.g., a station hall, platform, or bus stop is "
                    "   often a better choice than the cramped vehicle interior, because later panels "
                    "   need the freedom to show ticket counters, platforms, or boarding areas too.\n"
                    "   Do NOT use traditional tile-roof hanok or wooden houses.\n"
                    "1-1. POINT OF VIEW — set the world where the PROTAGONIST actually is during "
                    "these conversations. For REMOTE situations where the speakers talk from "
                    "different places (food delivery, phone orders or reservations, calling a taxi, "
                    "customer service / repair / AS calls, reporting utility problems, calling the "
                    "management office, KakaoTalk/text chats), the world is the protagonist's HOME — "
                    "a cozy living room with a phone — NOT the business's interior. "
                    "If the situation title itself mentions phone/전화, text/문자, or online, "
                    "default to phone-call. In phone-call intros BOTH characters must each hold "
                    "their own phone/headset/receiver. "
                    "In that case output 'STAGING: phone-call' as the first line and describe "
                    "LEFT half = protagonist at home with phone, RIGHT half = the supporting "
                    "character answering at their own workplace. Otherwise output "
                    "'STAGING: face-to-face'.\n"
                    "2. Characters are SMALL cute chibi figures in the lower-center of the frame — "
                    "   surrounded by ample soft empty background space.\n"
                    "3. BACKGROUND is minimal abstract color wash only — "
                    "   suggest location with 1-2 simple shapes, NO detailed props or furniture.\n"
                    "4. NO text, signs, labels, speech bubbles anywhere.\n"
                    "5. Focus on gentle, LIGHT pastel atmosphere with wide open space — "
                    "   soft daylight, at most 2-3 muted accent colors. "
                    "   NEVER mention: lanterns, rainbow/multicolored awnings, bunting, "
                    "   string lights, festival decorations, or shelves packed with goods.\n"
                    "6. VEHICLE ACCURACY (only if you actually choose a vehicle interior): "
                    "driver on LEFT with steering wheel facing FORWARD, "
                    "passenger on RIGHT facing FORWARD, "
                    "steering wheel always visible, characters never sideways or backward.\n\n"
                    "Output: the STAGING line first, then 2 sentences ONLY. No preamble."
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
                        prior_poses: list | None = None,
                        prior_views: list | None = None) -> str:
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

    # 구도는 인덱스로 고정하지 않는다 — 디렉터가 대사에 맞는 구도를 고른다.
    # fallback(Claude 미사용/실패) 경로에서만 대사 해시로 하나 뽑아 쓴다.
    _vh_seed = int(hashlib.md5((my_ko or my_en or str(phrase_idx)).encode("utf-8")).hexdigest()[:8], 16)
    view_hint = _PANEL_VARIATION_HINTS[_vh_seed % len(_PANEL_VARIATION_HINTS)]

    # DB에 미리 생성된 scene_prompt가 있으면 배경으로 사용 + 동작 설명 추가
    base_scene = situation.get("scene_prompt", "")

    if anthropic_client is None:
        action = (
            f"The {learner_char} gestures expressively while saying '{my_en}', "
            f"and the {local_char} responds warmly."
        )
        location = base_scene if base_scene else f"A modern Korean setting fitting this dialogue ({sit_en.lower()})"
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
            f"Broader theme/world (intro background — use ONLY as location info; "
            f"IGNORE any color scheme, character species, or left/right placement "
            f"written in it, they are outdated): {base_scene}\n" if base_scene
            else f"Broader theme: soft minimalist Korean {sit_en.lower()}\n"
        )
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=320,
            messages=[{
                "role": "user",
                "content": (
                    "You are an illustration director for a Korean language learning app.\n"
                    "Write 1-2 sentences describing the scene for this dialogue panel.\n\n"
                    f"{setting_hint}"
                    f"Situation theme: {sit_ko} ({sit_en})\n"
                    + (
                        "⚠️ REMOTE-BY-DEFAULT SITUATION: this situation's theme is inherently "
                        "remote (phone/text/online/delivery). Output 'STAGING: phone-call' for "
                        "this panel UNLESS this specific line can ONLY happen in person "
                        "(e.g., physically arriving at the place, or receiving the item at the "
                        "door → then use door-handoff). Any location hint below describing a "
                        "business interior applies to the OTHER side of the call, not to the "
                        "protagonist.\n"
                        if _is_remote_theme(situation) else ""
                    )
                    + "PANEL CAMERA/AREA — YOU CHOOSE. There is no assigned angle for this "
                    "panel: pick the framing that best shows what THIS line is actually doing "
                    "(pointing at something far away needs a wider shot; handing over an item "
                    "or reading a menu needs a closer one; asking staff behind a counter needs "
                    "the counter in frame). Menu of options — pick one or describe your own:\n"
                    + "\n".join(f"  • {v}" for v in _PANEL_VARIATION_HINTS) + "\n"
                    + (
                        "ALREADY-USED FRAMINGS in this situation — pick a DIFFERENT one unless "
                        "the dialogue really demands the same:\n"
                        + "\n".join(f"  - {v}" for v in (prior_views or [])[-6:]) + "\n"
                        if prior_views else ""
                    )
                    + f"LEFT character — PROTAGONIST (red panda, LARGER): {learner_char} — says: '{my_en}'\n"
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
                    + "BEFORE WRITING — UNDERSTAND THE SCENE (think silently, do not output this):\n"
                    "  (a) WHO is the supporting character in THIS situation — staff serving the "
                    "protagonist (cashier, clerk, barista, pharmacist, doctor, driver, ticket agent, "
                    "receptionist) or a peer (friend, neighbor, colleague)?\n"
                    "  (b) WHERE does each character physically belong at this exact moment — "
                    "which side of the counter, seated or standing, holding what?\n"
                    "  (c) WHAT is each speaker feeling, judged from what their line actually MEANS — "
                    "not a generic smile?\n"
                    "  (d) ARE the two speakers even in the SAME PLACE? Phone/app orders, delivery "
                    "inquiries ('where is my order?'), and phone reservations mean they are in "
                    "DIFFERENT places and must NOT be drawn together.\n\n"
                    "RULES:\n"
                    "0. STAGING — output this FIRST on its own line, exactly one of:\n"
                    "   'STAGING: phone-call' — the speakers are NOT in the same place. This covers "
                    "ANY remote conversation: ordering food or calling a taxi by phone/app, delivery "
                    "inquiries, reservations by phone (hotel, restaurant, hospital, salon), calling "
                    "customer service / repair / AS centers, reporting utility problems, calling the "
                    "apartment management office or landlord, KakaoTalk/text message chats, and "
                    "making plans by phone or text with a friend. The panel will be drawn as a "
                    "SPLIT-SCREEN, so describe BOTH sides in your scene sentences: what the "
                    "protagonist does and feels at their own location, AND what the supporting "
                    "character does at their own location while answering. ALWAYS state the device "
                    "for BOTH sides — e.g., 'phone gripped in one paw pressed to ear' / 'headset "
                    "on' / 'holding the receiver' — both speakers MUST visibly hold their own "
                    "device. ONE-PAW GESTURES ONLY while holding a phone: the phone paw stays at "
                    "the ear, so pick gestures using just the OTHER free paw (open palm, paw on "
                    "chest, paw on cheek) — never both-paws-clasped, both-paws-to-cheeks, or "
                    "arms-thrown-up during a call (headset wearers may use both paws). For "
                    "TEXT/app chats, both characters look down at their phone screens typing — "
                    "no phone held to the ear.\n"
                    "   THEME OVERRIDE: if the situation theme itself mentions phone/전화, text/문자, "
                    "or online booking, DEFAULT to phone-call for every line unless that specific "
                    "line clearly happens in person.\n"
                    "   'STAGING: door-handoff' — a delivery worker or visitor is at the "
                    "protagonist's front door (receiving food, 'leave it at the door' moment, "
                    "courier handing over a package).\n"
                    "   'STAGING: face-to-face' — both speakers really are in the same room.\n"
                    "   'STAGING: solo' — the protagonist acts alone (tapping an app, reading a "
                    "menu flyer at home, no one else present).\n"
                    "1. CONSISTENCY: The SAME two characters appear throughout this entire scene — "
                    "same species, same fur/body color, same outfit as the intro panel. "
                    "DO NOT change species, color, or clothing between panels.\n"
                    "2. LOCATION — DIALOGUE-DRIVEN: Pick the location that PHYSICALLY matches THIS panel's "
                    "spoken dialogue, even if it differs from the intro background. "
                    "The intro background is just the broader theme/world (e.g., \"train travel\"), "
                    "NOT a forced setting for every panel. Use these mappings:\n"
                    "   • Buying/cancelling tickets, asking schedule before boarding → ticket counter / kiosk / station hall\n"
                    "   • Asking which platform / where to board / how long until departure → platform / boarding gate\n"
                    "   • Finding seat, asking about stops while moving, requesting window seat → INSIDE the moving vehicle\n"
                    "   • Asking taxi to go somewhere / fare → could be sidewalk hailing OR inside taxi (pick what fits)\n"
                    "   • Bus fare / boarding → at the entrance door area near the fare reader\n"
                    "   • Ordering food IN PERSON → at counter or seated at a table (pick what the line implies)\n"
                    "   • Ordering/asking by PHONE or app (delivery, reservation, order status) → "
                    "phone-call split-screen: protagonist's home living room ↔ the business's counter/kitchen\n"
                    "   • Calling customer service / AS / utilities / management office → "
                    "phone-call split-screen: protagonist's home ↔ the service desk or office\n"
                    "   • KakaoTalk/text chat, making plans by text → phone-call split-screen: "
                    "each side at their own place, looking at their phone screen and typing\n"
                    "   • Receiving a delivery, 'leave it at the door', paying a rider → "
                    "door-handoff at the protagonist's apartment front door\n"
                    "   • Asking for the bill / takeout → at table or at the counter\n"
                    "   Keep the same overall art style and color palette as the intro, but the SUB-LOCATION "
                    "must serve the dialogue. Do NOT cram every panel into the same single spot.\n"
                    "2-1. ROLE-ACCURATE STAGING: if the supporting character is STAFF, they are "
                    "AT THEIR WORK STATION — behind the counter/register/desk, at the exam desk, "
                    "in the driver's seat, behind the styling chair. The protagonist faces them "
                    "from the customer side, the counter running between them. "
                    "NEVER describe staff and customer standing side-by-side on the customer side "
                    "casually chatting — that breaks the scene's realism.\n"
                    "2-2. COLOR RESTRAINT: describe the location simply and airy — at most ONE "
                    "colored prop. NEVER mention: lanterns, rainbow/multicolored awnings, bunting, "
                    "string lights, festival decorations, or shelves densely packed with goods. "
                    "Prefer soft daylight unless the dialogue explicitly happens at night.\n"
                    "3. DIFFERENTIATION via ACTION+EXPRESSION: "
                    "Each panel must show a DIFFERENT body pose, gesture, and facial expression. "
                    "Describe SPECIFIC concrete visuals: eye shape, mouth, paw position, "
                    "lean direction, blush, sweat drop, item being held/handed, etc.\n"
                    "3-1. EXPRESSIONS MUST MATCH THE DIALOGUE MEANING: derive each character's "
                    "emotion from what THEIR OWN line says — apologizing → embarrassed slight bow; "
                    "asking a favor → hopeful lean forward; complaining → troubled frown; "
                    "receiving something → delighted; being thanked → modest warm nod. "
                    "The two characters usually feel DIFFERENT things — give each their own "
                    "distinct expression, never the same generic smile on both.\n"
                    "4. First sentence: the camera angle YOU chose + the dialogue-appropriate "
                    "sub-location for this panel. State the angle explicitly (e.g. 'wide three-quarter "
                    "shot', 'close medium shot over the counter') so it reads as a deliberate choice "
                    "for this line, not a default.\n"
                    "5. Second sentence: specific actions and expressions matching the dialogue.\n"
                    "6. AVOID: repeating poses from previous panels, generic 'warm smile', "
                    "thumbs-up gesture, raised-index-finger pose (OVERUSED — use at most once per entire scene).\n"
                    "   USE VARIED POSES — pick from this list (each panel must use a different one):\n"
                    "   • handing item over with both paws / holding out card, passport, paper\n"
                    "   • deep bow with head down / slight nod-bow with paw on chest\n"
                    "   • open both palms forward (explaining) / one open palm facing up\n"
                    "   • sweeping arm gesture to show direction (open hand, not index finger)\n"
                    "   • paw on own cheek (flustered/embarrassed) / both paws to cheeks (surprised)\n"
                    "   • one paw over mouth (shocked/sorry) / stepping back slightly\n"
                    "   • paw on chin, tilted head (thinking) / scratching back of head\n"
                    "   • leaning forward attentively / leaning back and looking up\n"
                    "   • patting the other character's shoulder / reaching toward them\n"
                    "   • arms lightly raised at sides (happy/relieved) / small shrug\n"
                    "   • waving hello or goodbye / waving one paw dismissively\n"
                    "   • crossing arms (waiting/firm) / hands clasped in front\n"
                    "   • tapping a counter, screen, or sign / writing or signing something\n"
                    "   • holding up a card/phone/ticket (both paws) / clutching item to chest\n"
                    "   • pointing at self with both paws (\"me?\") / spreading both paws wide\n"
                    "7. Protagonist is LEFT and LARGER; supporting is RIGHT and SMALLER.\n"
                    "8. VEHICLE ACCURACY (only when the dialogue actually takes place inside a moving vehicle): "
                    "driver ALWAYS sits on the LEFT behind the steering wheel facing FORWARD; "
                    "passenger sits on RIGHT or behind, also facing FORWARD; "
                    "steering wheel MUST be visible in front of driver; "
                    "characters NEVER sit sideways or backward; "
                    "bus fare card reader is near the entrance on driver's right. "
                    "If the dialogue is at a counter/platform/sidewalk, do NOT force a vehicle interior.\n"
                    "9. DEMONSTRATIVES (이/그/저 · 여기/거기/저기 · 이거/그거/저거): if the line "
                    "refers to something with a demonstrative, place it at the MATCHING distance — "
                    "이/여기/이거 (this/here, near speaker) = right beside the LEFT protagonist; "
                    "그/거기/그거 (that/there, near listener) = beside the RIGHT supporting character; "
                    "저/저기/저쪽 (that over there, far from both) = a distant spot, the speaker "
                    "sweeping an open hand toward the far location. NEVER put a 그/저 referent in the "
                    "speaker's own hands (that reads as 이/this).\n"
                    "10. PHONE SCREENS: when a character looks at their OWN phone, the screen faces "
                    "that character's own eyes (tilted toward themselves), NOT turned outward. Only "
                    "when they deliberately show it to the other character may it face outward.\n"
                    "Output: the STAGING line first, then 1-2 scene sentences. No preamble."
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
        location = base_scene if base_scene else f"A modern Korean setting fitting this dialogue ({sit_en.lower()})"
        return (
            f"{location}, {view_hint}. "
            + action
        )


_IMAGE_MODEL   = "gemini-3.1-flash-image-preview"
_CHARS_DIR     = _SCRIPT_DIR / "assets" / "characters" / "topik"


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
    # 2) 주인공 표정시트 (표정 레퍼런스)
    face_sheet = _CHARS_DIR / "main_character_facialexpression.png"
    if face_sheet.exists():
        try:
            refs.append(PILImage.open(str(face_sheet)).convert("RGB"))
        except Exception:
            pass
    # 3) extra 캐릭터 시트 (있는 것 모두 포함)
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


# ─── 스테이징 타입 (2026-07-22) ──────────────────────────────
# 장면 디렉터가 패널마다 "STAGING: <type>" 태그를 첫 줄에 출력 → 구도 분기.
# phone-call: 두 화자가 다른 장소(전화 주문/예약/배달 문의) → 분할화면.
# door-handoff: 배달원이 현관에 도착한 순간. solo: 주인공 단독. face-to-face: 대면(기본).
_STAGING_TYPES = ("face-to-face", "phone-call", "door-handoff", "solo")
# phone-split은 phone-call의 별칭으로만 허용(디렉터가 가끔 출력해도 안전하게 처리)
_STAGING_RE = re.compile(
    r'^\s*STAGING:\s*(face-to-face|phone-call|phone-split|door-handoff|solo)\s*\.?\s*\n?',
    re.IGNORECASE,
)


# 상황명 자체가 원격 대화(전화/문자/온라인/배달)를 뜻하면 phone-call을 기본값으로 강제.
# 프롬프트 권고만으론 DB 장소 힌트(리셉션 등)에 밀려 대면으로 오판되는 사례(sit_14)가 있어
# 코드에서 결정적으로 주입 (2026-07-22).
_REMOTE_THEME_RE = re.compile(
    r'전화|통화|문자|카카오|온라인|배달|phone|text message|kakao|online|delivery',
    re.IGNORECASE,
)


def _is_remote_theme(situation: dict) -> bool:
    text = f"{situation.get('situation', '')} {situation.get('situation_en', '')}"
    return bool(_REMOTE_THEME_RE.search(text))


def _split_staging(scene: str) -> tuple[str, str]:
    """장면 텍스트에서 STAGING 태그를 분리. (staging, 본문) 반환. 태그 없으면 face-to-face."""
    m = _STAGING_RE.match(scene or "")
    if m:
        staging = m.group(1).lower()
        if staging == "phone-split":
            staging = "phone-call"
        return staging, scene[m.end():].strip()
    return "face-to-face", (scene or "").strip()


def _build_char_instruction(situation: dict, phrase_idx: int = 0,
                            is_first_panel: bool = False,
                            staging: str = "face-to-face",
                            has_scene_ref: bool = False) -> str:
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
            f"  PROTAGONIST: red panda — orange-red fur, white markings, {outfit}\n"
            + (f"  SUPPORTING: {local_char}\n" if staging != "solo" else "")
            + "Same species, same fur color, same outfit in EVERY panel. "
            "DIFFERENTIATE only via: expression, body pose, gesture, camera angle.\n"
        )

    # ── 스테이징별 구도/배치 블록 (2026-07-22) ──────────────────
    if staging == "phone-call":
        # 2026-07-22 확정: 원거리 대화(전화 등)는 인트로·패널 모두 분할샷 — 두 화자를
        # 각자의 공간에 그림(사용자 확정. 주인공 단독안은 폐기).
        layout_block = (
            "=== FRAMING — SPLIT-SCREEN PHONE CALL ===\n"
            "The two speakers are in DIFFERENT PLACES talking on the phone — they are NOT together.\n"
            "Vertical SPLIT-SCREEN composition: a soft hand-drawn wavy watercolor divider line runs "
            "from top to bottom down the middle of the square frame, creating two half-panels.\n"
            f"LEFT HALF — the red panda protagonist at their OWN location as the scene describes "
            f"(e.g., home living room), phone to ear — or looking down at the phone screen and "
            f"typing if the scene describes a text/app chat. Outfit: {outfit}.\n"
            f"RIGHT HALF — the {local_char} at their own separate location as the scene describes "
            f"(restaurant counter, kitchen, office, service desk, or their own home), answering "
            f"on a phone or headset — or typing on their own phone for a text chat.\n"
            "Each half has its OWN background. The two characters NEVER share a room, never touch, "
            "and no counter or table connects the two halves. "
            "MANDATORY — BOTH CHARACTERS HOLD THEIR OWN DEVICE: the protagonist holds a phone AND "
            "the supporting character holds their own phone (or wears a headset, or holds a "
            "landline receiver). A character talking in a phone call WITHOUT any device in "
            "paw/on head is WRONG — never draw that. For text chats, both hold phones and look "
            "down at their screens.\n"
            "PHONE IS ALWAYS GRIPPED BY ONE PAW pressed to the ear — a phone floating at the ear "
            "with no paw holding it is WRONG. Therefore during a call each character has only ONE "
            "free paw: all gestures must be ONE-PAW gestures (open palm, pointing direction, paw "
            "on chest, paw on cheek, scratching head). NEVER draw two-paw poses — both paws "
            "clasped together, both paws on cheeks, both arms thrown up — while on a call. "
            "(Exception: a character wearing a HEADSET has both paws free.)\n"
            "Each character ≈ 70% of the frame height inside their own half, medium shot, eye level, "
            "fully visible head to feet.\n"
            f"SUPPORTING CHARACTER: a {local_char} — clearly DIFFERENT color from the red panda "
            "(NOT orange/red/tan), same watercolor storybook style.\n"
        )
    elif staging == "door-handoff":
        layout_block = (
            "=== FRAMING — FRONT DOOR HANDOFF ===\n"
            "The scene happens at the protagonist's apartment FRONT DOOR.\n"
            f"LEFT — the red panda protagonist stands INSIDE the home at the open front door. "
            f"Outfit: {outfit}.\n"
            f"RIGHT — the {local_char} stands OUTSIDE in the hallway as a DELIVERY WORKER: "
            "wearing a delivery cap or helmet, holding a paper food bag or insulated delivery box "
            "with both paws.\n"
            "The open door frame clearly separates inside and outside. "
            "Camera at eye level, medium shot, both characters fully visible.\n"
            f"SUPPORTING CHARACTER: a {local_char} — clearly DIFFERENT color from the red panda "
            "(NOT orange/red/tan), same watercolor storybook style.\n"
        )
    elif staging == "solo":
        layout_block = (
            "=== FRAMING — SOLO PANEL ===\n"
            "ONLY ONE character appears in this panel: the red panda protagonist ALONE at the "
            f"location the scene describes, interacting with their phone or the item at hand. "
            f"Outfit: {outfit}.\n"
            "NO second character anywhere in the image. "
            "Protagonist centered, medium shot, eye level, fully visible head to feet.\n"
        )
    else:  # face-to-face (기본)
        layout_block = (
            "=== FRAMING ===\n"
            "CLOSE MEDIUM SHOT: two characters fill the CENTER of the square frame. "
            "Heads near upper-center, feet near lower-center. "
            "Background at top and sides only — NOT dominating the lower half. "
            "Camera at character eye level. Do NOT push characters to the bottom.\n"
            "ROLE-ACCURATE STAGING: if the supporting character is staff serving the protagonist "
            "(cashier, clerk, barista, pharmacist, receptionist, ticket agent), place them BEHIND "
            "their counter/register/desk with the protagonist in FRONT as the customer — "
            "the counter runs between the two. Never show staff standing on the customer side.\n\n"
            "=== TWO CHARACTERS ===\n"
            f"LEFT — PROTAGONIST (RED PANDA): match the reference image exactly. "
            f"Orange-red fur, dark brown body, white facial markings, fluffy striped tail. "
            f"Outfit: {outfit}.\n"
            f"RIGHT — SUPPORTING CHARACTER: a {local_char}. "
            f"Must be clearly DIFFERENT color from the red panda (NOT orange/red/tan). "
            f"Same watercolor storybook style as the protagonist.\n"
            "The two characters must look CLEARLY DIFFERENT — different species, different colors, "
            "different sizes.\n"
        )

    return (
        "CHARACTER REFERENCE IMAGES ARE PROVIDED ABOVE.\n"
        "  - 1st reference = main character (red panda) base design — the ONLY source of truth "
        "for body proportions: copy the head:body ratio, head size, limb lengths, fur color, "
        "markings, and drawing style EXACTLY as drawn in this sheet. The character's proportions "
        "must be pixel-identical to this reference in EVERY panel — never slimmer, never taller, "
        "never more realistic.\n"
        "  - 2nd reference = main character FACIAL EXPRESSION SHEET — 20 expressions of the "
        "same red panda (Neutral, Happy, Laughing, Excited, Curious, Surprised, Shocked, "
        "Thinking, Confused, Sleepy, Sad, Crying, Angry, Annoyed, Embarrassed, Shy, "
        "Scared, Determined, Playful Wink, Proud). Pick the ONE expression from this sheet "
        "that best fits the scene emotion and reproduce it faithfully on the red panda.\n"
        "  - Any remaining references = supporting character sheets"
        + (
            ", EXCEPT THE LAST reference image which is the INTRO PANEL of this exact scene — "
            "copy the supporting character's species, face shape, body proportions, colors and "
            "outfit EXACTLY from that intro panel, and keep the same watercolor rendering style "
            "so every panel of this scene looks drawn by the same artist"
            if has_scene_ref else ""
        )
        + ".\n\n"
        "=== STYLE ===\n"
        # ⚠ 2026-07-21: 기존 "STYLE FIRST — MATCH THE REFERENCE IMAGES(그림 전체)" 지시가
        #    웜톤 시트(주황/갈색/크림) 색감을 화면 전체에 물들여 세피아/고채도의 원인이었음.
        #    레퍼런스 매칭은 캐릭터 외형 한정으로 완화 — 전체 스타일 매칭으로 되돌리지 말 것.
        "Use the reference images for CHARACTER APPEARANCE ONLY — body proportions, fur colors, "
        "markings, and outline style of the characters themselves. "
        "Do NOT tint the whole image with the reference sheet's warm orange-brown tones. "
        "Overall rendering: soft pastel watercolor, Korean/Japanese children's picture book "
        "(kawaii storybook), thin delicate ink outlines — soft, slightly rounded, gentle even weight, "
        "airy translucent watercolor washes, "
        # ⚠ 단어 시스템과 톤 통일: "warm peachy-cream gradient"는 세피아/황금빛 과다(채도 상승)
        #    원인이라 제거. 단어 _WEBTOON_STYLE_CORE와 동일한 중립 파스텔로 맞춤(2026-06-20).
        "pastel palette: ivory white, soft sky-blue, dusty rose, sage green, light lavender, "
        "muted mint — balanced tones, not overly yellow or orange, NO neon colors. "
        "CHARACTERS: cute chibi cartoon animals. "
        "PROTAGONIST RULE — STRICTLY ENFORCED: main character is ALWAYS a red panda; "
        "supporting characters MUST be smaller or equal in size, NEVER taller. "
        "PROTAGONIST CANONICAL PROPORTIONS — identical in every illustration: "
        "head:body ratio EXACTLY 1:1.2 (head dominant); head perfectly round, top 45% of silhouette; "
        "body short plump oval-egg, no visible neck; arms 0.4× body height, stubby paw tips no fingers; "
        "legs 0.3× body height, very short stubby; tail 1.0× body height, bushy with 4–5 dark rings; "
        "ears small triangles with white inner fluff; eyes 35% of face width with small dot nose; "
        "fur: rust-orange body + white face/ears/chest + dark brown limbs and ringed tail; "
        "clean watercolor outline (no thick black strokes). "
        "DO NOT use thin human-like body, long legs, muscular sleek frame, fingers, shoes/boots/sandals. "
        "Total character height ≈ 45% of frame height (±5% tolerance only) — IDENTICAL in every panel. "
        "Characters fully visible head to feet. NO footwear — bare paws only. "
        "EYES: small bead-like eyes — tiny dark circle with a single white highlight dot, "
        "sclera is warm cream-white, eye overall is small and simple.\n\n"
        + layout_block
        + consistency_note + "\n"
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


# ─── 팔레트 검증 (단어 시스템 palette_ok 이식, 2026-07-21) ─────
_PALETTE_FIX_SUFFIX = (
    " STYLE FIX — the previous attempt was too saturated/dark: render this scene as a "
    "HIGH-KEY light airy pastel watercolor — heavily faded desaturated misty background, "
    "soft ivory-white paper showing through, maximum 2-3 muted accent colors, "
    "soft diffused daylight, no sepia or golden-amber cast, no lanterns, "
    "no festival decorations, no densely packed colorful props."
)


def _verify_palette(image_path: Path, genai_client) -> tuple[bool, str]:
    """생성 이미지가 저채도 파스텔 톤인지 VLM으로 검증.
    검증 자체가 실패하면 통과 처리(파이프라인을 막지 않음)."""
    try:
        from PIL import Image as PILImage
        img = PILImage.open(str(image_path)).convert("RGB")
        resp = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                img,
                "Evaluate this illustration's color palette. Answer in strict JSON only: "
                '{"palette_ok": true or false, "reason": "one short sentence"}. '
                "palette_ok is true ONLY if ALL of these hold: "
                "overall tone is light high-key pastel; "
                "background is faded/desaturated with soft pale washes; "
                "no strong sepia or golden-amber cast over the whole image; "
                "no large heavily-saturated color areas dominating the frame; "
                "no densely packed colorful props (lanterns, bunting, packed shelves). "
                "Judge strictly.",
            ],
        )
        m = re.search(r"\{.*\}", resp.text or "", re.DOTALL)
        if not m:
            return True, "no-json"
        data = json.loads(m.group(0))
        return bool(data.get("palette_ok", True)), str(data.get("reason", ""))[:150]
    except Exception as e:
        return True, f"verify-error: {e}"


# ─── Gemini Flash Image 생성 ─────────────────────────────────
def _generate_image(prompt: str, output_path: Path, genai_client,
                    sit_id: int = 0, situation: dict | None = None,
                    phrase_idx: int = 0, is_first_panel: bool = False) -> bool:
    """Gemini Flash Image로 단일 이미지 생성 (캐릭터 레퍼런스 포함)"""
    if output_path.exists() and output_path.stat().st_size > 0:
        return True
    elif output_path.exists():
        output_path.unlink()

    # STAGING 태그 분리 (2026-07-22): 전화 통화=분할화면, 현관 인수, 단독 패널 등 구도 분기
    staging, scene_body = _split_staging(prompt)

    # 캐릭터 레퍼런스 이미지 로드
    char_refs = _load_char_refs()

    # 이 상황의 인트로 패널을 추가 레퍼런스로 첨부 (2026-07-22):
    # 패널마다 독립 생성이라 조연 디자인/화풍이 널뛰던 문제 → 인트로에서 확립된 look을 고정
    scene_ref = None
    if not is_first_panel:
        intro_path = output_path.parent / "intro.png"
        if intro_path.exists() and intro_path.stat().st_size > 0:
            try:
                from PIL import Image as PILImage
                scene_ref = PILImage.open(str(intro_path)).convert("RGB")
            except Exception:
                scene_ref = None

    char_instruction = _build_char_instruction(
        situation or {}, phrase_idx, is_first_panel,
        staging=staging, has_scene_ref=scene_ref is not None,
    )
    full_prompt = char_instruction + _apply_style(_lint_prompt(scene_body), sit_id, situation, phrase_idx)
    all_refs = char_refs + ([scene_ref] if scene_ref is not None else [])

    def _call(prompt_text: str, path: Path) -> bool:
        response = genai_client.models.generate_content(
            model=_IMAGE_MODEL,
            contents=all_refs + [prompt_text],
            config=types.GenerateContentConfig(
                response_modalities=[types.Modality.IMAGE],
                image_config=types.ImageConfig(aspect_ratio="1:1"),
            ),
        )
        return _save_generated_image(response, path)

    try:
        if not _call(full_prompt, output_path):
            print(f"  [빈 응답] 이미지 없음: {output_path.name}")
            return False
        # 팔레트 검증(단어 시스템의 palette_ok 이식, 2026-07-21) — NG면 1회만 재생성.
        # 재시도는 임시 파일에 생성 후 교체: 재시도 실패 시 원본 유지(원본삭제 위험 방지).
        ok, reason = _verify_palette(output_path, genai_client)
        if not ok:
            print(f"  [팔레트 NG → 재생성 1회] {output_path.name}: {reason}")
            retry_path = output_path.with_name(output_path.stem + "_retry.png")
            if _call(full_prompt + _PALETTE_FIX_SUFFIX, retry_path):
                retry_path.replace(output_path)
            else:
                retry_path.unlink(missing_ok=True)
        return True
    except Exception as e:
        print(f"  [생성 오류: {e}] {output_path.name}")
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print("\n[중단] API 일일 할당량 초과 — 내일 다시 시도하세요.")
            raise SystemExit(1)
        return False


# ─── 상황별 일러스트 생성 ────────────────────────────────────
def generate_situation(situation: dict, genai_client, anthropic_client,
                       progress: dict, intro_only: bool = False,
                       only_key: str | None = None) -> tuple[int, int]:
    """단일 상황의 패널 생성. (done, fail) 반환.
    only_key 가 지정되면 그 패널 1개만 생성 (예: "intro" 또는 "phrase_3").
    """
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

    do_intro = (only_key is None) or (only_key == "intro")

    # 1. 인트로 (설정 샷) — is_first_panel=True 로 캐릭터 확립
    intro_path = sit_dir / "intro.png"
    intro_key  = "intro"
    if do_intro:
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
        elif only_key == "intro":
            print(f"  [스킵] intro.png (이미 존재)")
            done += 1
        else:
            print(f"  [스킵] intro.png (이미 존재)")
            done += 1

    if intro_only or only_key == "intro":
        return done, fail

    # 2. 대화 쌍별 패널 — 동일 캐릭터/배경, 동작·표정·구도로만 차별화
    used_poses: list[str] = []  # 이 상황 내 이미 쓴 포즈/표정 요약
    used_views: list[str] = []  # 이 상황 내 이미 쓴 카메라 구도(첫 문장) 요약
    for phrase_loop_idx, phrase in enumerate(phrases):
        ph_id   = phrase["id"]
        ph_key  = f"phrase_{ph_id}"
        ph_path = sit_dir / f"phrase_{ph_id}.png"

        # only_key 가 지정되면 그 패널만 생성, 나머지는 (포즈 추적만 하고) 스킵
        if only_key is not None and only_key != ph_key:
            if ph_path.exists() and ph_path.stat().st_size > 0:
                used_poses.append("(prior generated panel)")
            continue

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
            prior_views=used_views if used_views else None,
        )
        # 포즈 힌트 기록 — STAGING 태그 제거 후, 첫 문장(카메라/장소)을 건너뛰고
        # 둘째 문장부터(동작·표정) 기록. (구버전 scene[:80]은 장소 텍스트만 쌓여
        # 포즈 중복 방지가 전혀 안 됐음. 2026-07-21 수정, 2026-07-22 태그 제거 추가)
        _sc_body = _split_staging(scene)[1]
        _sc_parts = _sc_body.split(". ", 1)
        used_poses.append((_sc_parts[1] if len(_sc_parts) > 1 else _sc_body)[:150])
        # 구도 기록 — 첫 문장(카메라 앵글+서브장소)을 다음 패널에 "이미 쓴 구도"로 전달
        used_views.append(_sc_parts[0][:120])
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
    parser.add_argument("--phrase-key", type=str, default=None,
                        help='단일 패널만 생성 (예: "intro" 또는 "phrase_3"). --situation-id 와 함께 사용')
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
    if args.phrase_key:
        print(f"모드: 단일 패널만 ({args.phrase_key})")

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
            only_key=args.phrase_key,
        )
        total_done += done
        total_fail += fail
        print(f"  → 완료: {done}, 실패: {fail}")

    print(f"\n=== 완료 ===")
    print(f"총 완료: {total_done}, 총 실패: {total_fail}")
    print(f"출력 경로: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
