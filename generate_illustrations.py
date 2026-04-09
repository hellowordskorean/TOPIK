#!/usr/bin/env python3
"""
단어별 귀여운 일러스트 배치 생성 (최초 1회)
- Google Gemini (gemini-3.1-flash-image-preview) 사용
- assets/illustrations/{한국어단어}.png 에 저장 (기존 파일 스킵)
- 한국어 단어가 같으면 EN/CN/JP/VN 어느 DB든 동일 이미지 재사용

준비:
  1. https://aistudio.google.com 에서 API 키 발급
  2. .env 에 GEMINI_API_KEY=... 추가

실행:
  docker compose run --rm topik-bot python3 generate_illustrations.py
  docker compose run --rm topik-bot python3 generate_illustrations.py --start 1 --end 10
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

# 이미지 생성 백엔드: "imagen" | "flux"
_BACKEND = "imagen"
# 생성 후 Gemini Vision으로 텍스트 검증 여부 (--vlm-verify 플래그로 활성화)
_VLM_VERIFY = False

OUTPUT_DIR    = Path("/app/assets/illustrations")
PROMPTS_FILE  = Path("/app/data/LanguageTest/illustration_prompts.json")
SCENE_CACHE   = Path("/app/logs/scene_cache.json")  # /app/data는 dashboard에서 ro 마운트
FLAGGED_FILE  = Path("/app/logs/illust_flagged.json")
USAGE_FILE    = Path("/app/logs/illust_usage.json")


# ── 일일 사용량 추적 ────────────────────────────────────────
def _load_usage() -> dict:
    try:
        if USAGE_FILE.exists():
            with open(USAGE_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_usage(data: dict):
    try:
        USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _track_usage(success: bool, exhausted: bool = False):
    """API 호출 1회 기록"""
    data = _load_usage()
    today = datetime.now().strftime("%Y-%m-%d")
    if data.get("date") != today:
        data = {"date": today, "calls": 0, "success": 0, "fail": 0, "exhausted": False, "exhausted_at": None}
    data["calls"] += 1
    if success:
        data["success"] += 1
    else:
        data["fail"] += 1
    if exhausted:
        data["exhausted"] = True
        data["exhausted_at"] = datetime.now().strftime("%H:%M:%S")
    _save_usage(data)

# ── 웹툰 동물 캐릭터 스타일 ─────────────────────────────────────
_LOCAL_ANIMALS = [
    "tabby cat wearing a striped vest",
    "beagle dog wearing a cozy scarf",
    "gray cat wearing a polka-dot blouse",
    "golden retriever dog wearing a button-up shirt",
    "dalmatian dog wearing a yellow bandana",
    "calico cat wearing glasses and a blazer",
    "poodle wearing a beret and stylish sweater",
    "corgi wearing an apron",
    "gray cat wearing a plaid shirt",
    "shiba inu wearing a traditional outfit",
]

_LEARNER_OUTFITS = [
    "casual sweater and jeans",
    "hoodie and backpack",
    "colorful cardigan",
    "striped shirt and cap",
    "cozy knit sweater",
    "light jacket with tote bag",
    "denim jacket",
    "floral blouse and skirt",
    "sporty tracksuit",
    "trench coat",
]

def _pick_characters(word_id: int) -> tuple[str, str]:
    """단어 ID 기반으로 동물 캐릭터 쌍 선택 (결정론적)"""
    local  = _LOCAL_ANIMALS[word_id % len(_LOCAL_ANIMALS)]
    outfit = _LEARNER_OUTFITS[word_id % len(_LEARNER_OUTFITS)]
    return local, f"red panda wearing {outfit}"


def _inject_characters(content: str, word_id: int) -> str:
    """'person/people' 등 인물 표현을 동물 캐릭터 설명으로 교체.
    주인공(단수 행위자) = red panda (learner), 조연(역할 표현) = 다른 동물 (local)."""
    local, learner = _pick_characters(word_id)
    # 복수 인물 → 주인공(red panda) + 조연
    content = re.sub(r'\btwo people\b',      f'{learner} and {local}',  content, flags=re.IGNORECASE)
    content = re.sub(r'\btwo persons\b',     f'{learner} and {local}',  content, flags=re.IGNORECASE)
    content = re.sub(r'\btwo figures\b',     f'{learner} and {local}',  content, flags=re.IGNORECASE)
    content = re.sub(r'\btwo characters\b',  f'{learner} and {local}',  content, flags=re.IGNORECASE)
    content = re.sub(r'\bpeople\b',          f'{learner} and {local}',  content, flags=re.IGNORECASE)
    # 단수 인물 → 모두 주인공(red panda)으로
    content = re.sub(r'\ba young woman\b',   f'a {learner}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\ba young man\b',     f'a {learner}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe young woman\b', f'the {learner}',          content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe young man\b',   f'the {learner}',          content, flags=re.IGNORECASE)
    content = re.sub(r'\ba woman\b',         f'a {learner}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\ba man\b',           f'a {learner}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe woman\b',       f'the {learner}',          content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe man\b',         f'the {learner}',          content, flags=re.IGNORECASE)
    content = re.sub(r'\ba person\b',        f'a {learner}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe person\b',      f'the {learner}',          content, flags=re.IGNORECASE)
    content = re.sub(r'\ba figure\b',        f'a {learner}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe figure\b',      f'the {learner}',          content, flags=re.IGNORECASE)
    content = re.sub(r'\bsomeone\b',         f'{learner}',              content, flags=re.IGNORECASE)
    # 역할 표현: 학습자 계열 → 주인공(red panda), 상대역 → 조연
    content = re.sub(r'\ba student\b',       f'a {learner}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe student\b',     f'the {learner}',          content, flags=re.IGNORECASE)
    content = re.sub(r'\ba learner\b',       f'a {learner}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe learner\b',     f'the {learner}',          content, flags=re.IGNORECASE)
    content = re.sub(r'\ba customer\b',      f'a {learner}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe customer\b',    f'the {learner}',          content, flags=re.IGNORECASE)
    content = re.sub(r'\ba teacher\b',       f'a {local}',              content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe teacher\b',     f'the {local}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\ba vendor\b',        f'a {local}',              content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe vendor\b',      f'the {local}',            content, flags=re.IGNORECASE)
    content = re.sub(r'\ba scientist\b',     f'a {local}',              content, flags=re.IGNORECASE)
    content = re.sub(r'\bthe scientist\b',   f'the {local}',            content, flags=re.IGNORECASE)
    return content

_WEBTOON_STYLE_BASE = (
    "warm watercolor and pencil sketch illustration style, "
    "soft loose brushwork with visible watercolor paper texture, "
    "gentle pencil outlines (not thick black ink), "
    "watercolor wash backgrounds that are slightly soft and misty, "
    "time of day matches the scene naturally — morning, afternoon, evening, or night, "
    "pastel palette: ivory white, soft sky-blue, dusty rose, sage green, "
    "light lavender, muted mint — balanced tones, not overly yellow or orange, "
    "NO neon colors, NO dark or black-dominant areas, "
    "IF animal characters appear: cute chibi anthropomorphic proportions, "
    "PROTAGONIST RULE: the main character is ALWAYS a red panda — "
    "supporting/secondary characters can be any other cute animal, "
    "head-to-body ratio 1:1.2 — very large round head, body short and chubby, "
    "legs extremely short and stubby (almost no visible legs), arms short and rounded, "
    "total character height = 35 to 40 percent of the full frame height, "
    "characters naturally centered in the composition, fully visible head to feet, "
    "characters have slightly more detail/contrast than the soft background, "
    "NO shoes NO boots NO sandals NO footwear — all characters have bare paws, "
    "background reflects MODERN everyday Korean life — "
    "STRICTLY AVOID: traditional tile-roof houses (기와집), wooden hanok structures, "
    "paper screen doors, traditional courtyards — these are tourist sites, not daily life. "
    "USE INSTEAD: concrete apartment buildings, modern cafes, convenience stores (24h), "
    "subway stations, school classrooms, offices, city parks, pedestrian streets, "
    "supermarkets, modern restaurants — whatever the scene naturally calls for. "
    "Background is soft and slightly faded. "
    "depth: foreground subjects sharp, background gently blurred/misty, "
    "warm atmospheric haze giving a cozy golden hour feel, "
    "square 1:1 composition, "
    "vary the shot size to suit the scene — close-up for detail/emotion, "
    "medium shot for action/interaction, wide shot for location/atmosphere, "
    "choose whichever framing makes the concept most instantly clear, "
    "main subject centered naturally — balanced, well-composed scene, "
    "STRICT NO TEXT RULE: absolutely zero letters, zero words, zero numbers in any language, "
    "replace ALL signage and labels with visual symbols and icons only: "
    "pharmacy→red cross symbol, hair salon→scissors icon, restaurant→fork-and-spoon icon, "
    "cafe→coffee cup icon, hospital→red cross emblem, convenience store→colorful shelf display, "
    "bus destination→colored stripe pattern, menu board→illustrated food picture display, "
    "price tags→coin stack icon, receipts→dotted line pattern paper, "
    "phone screens→simple geometric icon UI, "
    "EXCEPTION: 'TAXI' yellow rooftop sign is allowed as a recognizable international symbol, "
    "all other storefronts must use pictogram icons only — NO readable text anywhere"
)

def _webtoon_style(word_id: int, has_characters: bool = True) -> str:
    return _WEBTOON_STYLE_BASE

# ── AI 장면 생성 시스템 ───────────────────────────────────────
# 품사별 시각화 가이드
_POS_GUIDE = {
    "명사": (
        "Show the object/place/person in its most recognizable natural context. "
        "The noun itself must be the unmistakable focal point."
    ),
    "동사": (
        "Capture the PEAK ACTION MOMENT — body mid-motion, objects involved, "
        "clear cause-and-effect visible. Not before, not after — the exact moment."
    ),
    "형용사": (
        "Show the quality through a CONCRETE EXAMPLE using contrast: "
        "place two objects or two characters side by side to make the quality unmistakable. "
        "E.g. for 'heavy': one person lifting a feather vs straining to lift a boulder."
    ),
    "부사": (
        "DO NOT show a generic scene. Instead use a VISUAL METAPHOR or COMPARISON: "
        "frequency adverbs → calendar/clock comparison; "
        "degree adverbs → a scale/spectrum with 3 intensity levels; "
        "manner adverbs → exaggerated body posture/speed lines showing HOW."
    ),
    "관형사": (
        "Show a concrete scene where the determiner's meaning is the unmistakable focus. "
        "Use labeled groups, quantities, or pointing to make the concept clear."
    ),
    "대명사": (
        "Show a character POINTING at or gesturing toward the referent — "
        "self-pointing for 나/저, outward pointing for 너, "
        "circling group gesture for 우리/저희."
    ),
    "감탄사": (
        "Show a character's FULL-BODY EMOTIONAL REACTION that embodies this exclamation — "
        "extreme facial expression, dramatic hand gesture, body posture. "
        "The emotion must be instantly readable."
    ),
    "접속사": (
        "Show TWO distinct scenes connected visually — "
        "use arrows, bridges, or sequential panels to show the logical connection."
    ),
}

# ── 단어별 시각화 앵커 (알려진 어려운 단어에 정확한 장면 지정) ───
_WORD_VISUAL_ANCHORS: dict[str, str] = {
    # ── 1-2급 빈도 부사 ──────────────────────────────────────
    "가끔":   "A monthly calendar pinned to a wall: most days are blank, but only 2-3 days have a small circle drawn on them — showing 'sometimes'.",
    "가장":   "Three children standing in a row by height — shortest, medium, tallest — with a gold star crown floating above the tallest one.",
    "갑자기": "A person mid-stride on a path, body frozen in sudden shock — coffee cup flying from hand, liquid mid-air, eyes wide.",
    "같이":   "Two friends walking side by side on a sunny path, arms linked, matching steps.",
    "거의":   "A tall glass of water filled to 95%, a tiny sliver of empty space at the very top.",
    "계속":   "A person jogging on a track, with a circular arrow looping back to the starting point — showing continuous repetition.",
    "꼭":     "A person gripping a pencil with extreme concentration, circling an important item on a list — fingers tight, brow furrowed.",
    "너무":   "A small cup completely overflowing — water cascading over the edges in all directions, creating a puddle below.",
    "늘":     "A daily calendar with every single day checked off in sequence — not one day missed.",
    "다시":   "A person rewinding a spool of film or rewinding a tape — arrow clearly pointing backward to start.",
    "더":     "Two stacks of coins side by side — left stack is 3 coins high, right stack is 6 coins high — clearly more.",
    "매우":   "A thermometer with the mercury at the absolute maximum, red line at the very top, small steam wisps rising.",
    "모두":   "A basket with 10 identical apples — every single one taken out and laid in a neat row, empty basket tipped over.",
    "바로":   "A person snapping fingers, and in the very next instant (shown side by side) the result appears instantly — no delay.",
    "빨리":   "A running figure with exaggerated speed lines streaming behind, feet barely touching ground.",
    "아직":   "An hourglass with sand still falling — halfway done, clearly not finished yet.",
    "이미":   "An empty plate with only crumbs remaining, a satisfied person leaning back — the meal already done.",
    "자주":   "A monthly calendar with nearly every other day circled — showing frequent occurrence.",
    "잘":     "A person presenting their completed project — a neat stack of papers, everything aligned perfectly, small sparkle.",
    "정말":   "A person with hands on cheeks, eyes wide, mouth open — genuine disbelief and astonishment.",
    "제일":   "A podium with three places — gold/silver/bronze — a figure standing proudly on the tallest gold platform.",
    "조금":   "A tiny pinch of salt between two fingers, hovering over a bowl — minuscule amount.",
    "천천히": "A turtle walking alongside a footpath, with slow relaxed steps and gentle expression.",
    "함께":   "Four hands from different directions joining together in the center — forming a unified grip.",
    "혼자":   "A single small figure sitting at a large empty table with many chairs — all other seats vacant.",
    "각":     "A row of 5 gift boxes, each with a different colored ribbon — one box per person, individual and distinct.",
    "간단히": "A complex tangled rope on the left, and the same rope neatly tied in one simple knot on the right.",
    "다":     "An open bag tipped over with ALL its contents spread out — every item visible, nothing left inside.",
    "또":     "A person eating a sandwich, then shown again eating another sandwich — two sequential panels with an 'again' arrow.",
    "특히":   "A row of identical apples, but one in the center glowing with a spotlight — highlighted and special.",

    # ── 1-2급 감탄사 ─────────────────────────────────────────
    "네":     "A person nodding vigorously with a wide smile and a big thumbs-up — enthusiastic agreement.",
    "아이고": "A person with both hands pressed to cheeks, eyes wide, mouth in an 'O' — classic flustered reaction.",
    "와":     "A person with arms thrown wide open, head tilted back — pure amazement and delight.",
    "아":     "A person with mouth open wide in sudden realization — the 'aha' moment, one finger raised.",

    # ── 1-2급 대명사 ─────────────────────────────────────────
    "나":     "A person pointing both thumbs at their own chest with a confident smile.",
    "저":     "A person pointing one thumb at their own chest with a humble, gentle bow.",
    "너":     "A person pointing one index finger directly forward — at the viewer — with a friendly expression.",
    "우리":   "A small group of three friends standing together, arms around each other's shoulders.",
    "저희":   "A small group bowing slightly together in a polite, humble group gesture.",
    "그것":   "A person pointing at a nearby object (a box) with one finger, eyes directed at it.",

    # ── 4급 심리/감정 추상명사 ───────────────────────────────
    "자존감":  "A person standing tall in front of a full-length mirror — their reflection glows with a warm aura, shoulders back, chin up, confident smile.",
    "불안감":  "A person sitting hunched on a chair, hands tightly wringing in lap, shoulders tense — a swirling gray cloud floating above their head.",
    "압박감":  "A small figure visibly straining, arms braced upward — a massive invisible weight pressing down from above, flattening the ground under their feet.",
    "열등감":  "Two figures standing side by side — one tall and glowing, one shorter with shoulders dropped, eyes cast downward at own feet.",
    "집중력":  "A person bent over a desk in a tight spotlight — everything outside the circle of light is dim, their eyes locked on the single task.",
    "성취감":  "A person standing at the peak of a mountain with arms raised triumphantly — sunrise behind them, climbing path visible below.",
    "당혹감":  "A person with bright red flushed cheeks, perspiration drops, eyes darting sideways — visible embarrassment.",
    "감정이입":"Two people: one is crying with tears, the second person leans in with a hand on their shoulder — second person's eyes also glistening with tears.",
    "감정":    "A single face split into four quadrants — each quarter showing a different clear emotion: joy, sadness, anger, surprise.",
    "정서":    "A warm family scene at a dinner table — soft light, gentle smiles, hands close together — the calm feeling of emotional belonging.",
    "감성":    "A person standing in rain, eyes closed, face tilted up — a single tear mixed with raindrops, surrounded by falling autumn leaves.",

    # ── 5급 외교/국제관계 ────────────────────────────────────
    "외교":    "Two formally dressed representatives from different nations shaking hands across a table — two small flags on either side of the table.",
    "협상":    "Two parties seated at opposite ends of a long table, both leaning slightly toward the center — papers spread between them, a gap still visible in the middle.",
    "조약":    "An official scroll document laid flat with an ornate wax seal — two fountain pens hovering over the signature lines, about to sign.",
    "협약":    "Two hands from different sides reaching toward the center and clasping in a firm handshake — a small document beneath the joined hands.",
    "동맹":    "Five arms reaching in from different corners of the frame, all joining at the center in a unified group handshake.",
    "제재":    "A cargo ship approaching a port — a large red barrier gate lowered across the entrance, blocking passage.",
    "외교관":  "A formally dressed figure carrying a briefcase, walking toward an official building entrance — small national flags flanking the doorway.",
    "영사관":  "An official building exterior with a national flag on a pole and a small emblem above the door — a visitor approaching the entrance.",
    "유엔":    "A circular table with many small flags from different countries arranged around it — globe motif in the center.",
    "국제법":  "A large open book with a globe resting on top — scales of justice balanced beside it on a formal desk.",
    "중재하다":"A person standing calmly between two groups who face away from each other — the mediator has both hands gently extended toward each group.",
    "인식하다":"A person turning their head with wide eyes and a sudden expression of clarity — a lightbulb moment shown as a small bright dot near their eye.",
    "주장하다":"A person standing at a podium with one hand raised firmly making a point — confident posture, clear gesture of assertion.",
    "검증하다":"A scientist figure holding up a test tube, peering through a magnifying glass at its contents — checklist partially completed nearby.",
    "구축하다":"Hands placing the final brick on top of a carefully built wall — structure rising from foundation, clearly assembled piece by piece.",
    "타당하다":"A balance scale in perfect equilibrium — both sides level, no tipping — representing soundness and validity.",
    "합리적이다":"A person at a crossroads choosing the straight clear path over the winding tangled one — calm and logical expression.",
    "체계적이다":"A neat organizational chart on paper — boxes connected by clear lines, everything in logical order from top to bottom.",

    # ── 6급 철학/논리학 ──────────────────────────────────────
    "경험론":  "Two hands reaching out and directly touching, smelling, and tasting real objects — an apple, a flame, a piece of fabric — raw sensory contact with reality.",
    "공리계":  "A row of dominoes standing in sequence — the first one has just fallen, triggering a chain reaction, all others falling in logical order.",
    "정합성":  "A jigsaw puzzle nearly complete — the final piece hovering over the one remaining gap, a perfect fit about to be made.",
    "주체성":  "A person standing at a fork in a road — confidently choosing one path despite two pointing arrows pulling in different directions.",
    "개연성":  "A single die mid-roll — multiple ghosted faces visible showing possible outcomes, one face slightly larger/brighter indicating higher likelihood.",
    "변증법적":"Two opposing arrows colliding in the center — and from the collision point, a new single upward arrow emerging, representing synthesis.",
    "선험적":  "A person sitting with eyes closed in pure thought — lightbulb appearing in their mind, with no real-world objects present, just abstract shapes.",
    "존재론적":"A mirror showing a reflection — but the reflection is slightly different from reality, raising the question of what is real existence.",
    "타당성":  "A scale of justice with both sides perfectly balanced — solid geometric shapes on each side, stable and level.",
    "논거":    "A simple logical flow diagram: one statement box connected by an arrow to a conclusion box — clear cause-and-effect structure.",
    "도출":    "A funnel with multiple items entering the wide top — one clear, refined result emerging from the narrow bottom spout.",
    "귀결하다":"A maze shown with all paths leading inevitably to one single exit — no other way out, logical inevitability.",
    "고찰하다":"A person sitting quietly at a desk, chin resting on hand, gazing thoughtfully at a single object placed before them.",
    "성찰하다":"A person looking into a still pond — their reflection gazes back — visual metaphor of looking inward at oneself.",
    "논증하다":"A chalkboard (blank) with arrows showing logical steps from premise to conclusion — geometric proof style layout.",
    "규정하다":"A clear boundary line drawn on the ground — objects on each side sorted into distinct categories.",
    "포괄하다":"A large circle drawn with many smaller shapes (triangle, square, star) all contained within it — all encompassed.",
    "서술하다":"A person gesturing expressively while a simple storyboard of sequential images unfolds beside them.",
}


def _classify_word_visual_type(word: dict) -> tuple[str, str]:
    """단어 유형 분류 → (유형코드, 시각화 전략 힌트) 반환.
    어려운 단어에 맞춤 전략을 제공해 AI 프롬프트 품질을 높임."""
    pos     = word.get("pos", "명사")
    meaning = word.get("meaning", "").lower()
    level   = word.get("level", 1)
    korean  = word.get("word", "")

    # 0. 앵커 사전에 정확한 장면이 있으면 최우선
    if korean in _WORD_VISUAL_ANCHORS:
        return "anchored", _WORD_VISUAL_ANCHORS[korean]

    # 1. 부사 세분화
    if pos in ("부사", "접속사"):
        freq = ["sometimes", "occasionally", "rarely", "often", "always", "never",
                "usually", "frequently", "regularly", "seldom", "constantly"]
        deg  = ["very", "too", "extremely", "most", "more", "less", "so", "quite",
                "rather", "fairly", "pretty", "really", "truly", "highly"]
        mann = ["suddenly", "quickly", "slowly", "carefully", "together",
                "again", "already", "still", "immediately", "directly",
                "simply", "easily", "quietly", "loudly", "strongly"]
        if any(x in meaning for x in freq):
            return "adverb_freq", (
                "Use a CALENDAR or CLOCK visual: show the action happening on "
                "only a few days vs many days to make frequency instantly visible."
            )
        if any(x in meaning for x in deg):
            return "adverb_deg", (
                "Show a 3-STEP SCALE: three objects of increasing intensity "
                "(small/medium/overflowing, dim/bright/blazing). "
                "Highlight the relevant degree level clearly."
            )
        if any(x in meaning for x in mann):
            return "adverb_manner", (
                "Exaggerate the MANNER of action through extreme body posture, "
                "motion lines, or a direct visual comparison — "
                "the HOW must be unmistakable."
            )
        return "adverb_general", (
            "Use a visual metaphor or before/after comparison to show "
            "what this adverb means in practice."
        )

    # 2. 관형사/대명사/감탄사
    if pos == "관형사":
        return "determiner", (
            "Show a clear GROUPING or SELECTION scene: items in a row, "
            "one highlighted, or groups separated — the determiner's meaning "
            "visible through spatial arrangement."
        )
    if pos == "대명사":
        return "pronoun", (
            "Show a character POINTING or GESTURING at the referent — "
            "self-pointing for 나/저, outward for 너, group gesture for 우리."
        )
    if pos == "감탄사":
        return "exclamation", (
            "Show a character's FULL-BODY REACTION: extreme facial expression, "
            "arm position, body language — the emotion must be instantly readable."
        )

    # 3. 4급+ 심리/감정 추상명사
    psych_neg = ["anxiety", "stress", "inferiority", "pressure", "depression",
                 "embarrass", "unease", "worry", "fear", "frustration", "burden"]
    psych_pos = ["self-esteem", "confidence", "achievement", "satisfaction",
                 "motivation", "pride", "joy", "happiness", "gratitude"]
    psych_neu = ["emotion", "feeling", "sensibility", "empathy", "sentiment",
                 "affective", "mood", "temperament", "attachment"]
    if any(x in meaning for x in psych_neg):
        return "emotion_neg", (
            "Show the PHYSICAL MANIFESTATION of this negative state: "
            "specific body posture (hunched/tense/collapsed), facial cues, "
            "and an environmental metaphor (weight, shadow, barrier) that "
            "makes the emotion UNMISTAKABLY different from other negative states."
        )
    if any(x in meaning for x in psych_pos):
        return "emotion_pos", (
            "Show the FULL-BODY EXPRESSION of this positive state: "
            "open posture, upward motion, warm light, achievement cue. "
            "Must be visually distinct from other positive emotions."
        )
    if any(x in meaning for x in psych_neu):
        return "emotion_neu", (
            "Show this emotional concept through a SPLIT or CONTRASTING scene "
            "that makes the specific nuance clear."
        )

    # 4. 5급 외교/국제관계
    diplomacy_kw = ["diplomacy", "treaty", "alliance", "negotiation", "sanction",
                    "sovereign", "coalition", "consulate", "diplomat", "mediat",
                    "international", "ratif", "multilateral", "bilateral"]
    if level >= 5 and any(x in meaning for x in diplomacy_kw):
        return "diplomacy", (
            "Show a SPECIFIC DIPLOMATIC MOMENT with unique visual elements "
            "that distinguish this word from other diplomatic terms. "
            "Do NOT use a generic handshake — be precise to this word's meaning."
        )

    # 5. 6급 철학/논리학
    philosophy_kw = ["empiricism", "axiomatic", "coherence", "subjectivity",
                     "dialectic", "ontolog", "probability", "validity", "a priori",
                     "proposition", "syllogism", "deduction", "induction",
                     "phenomenolog", "epistemolog", "methodology", "postcolonial"]
    if level >= 6 and any(x in meaning for x in philosophy_kw):
        return "philosophy", (
            "Create a TANGIBLE PHYSICAL METAPHOR using everyday objects. "
            "Do NOT use books, professors, or classrooms. "
            "Map the abstract concept to a concrete visual: "
            "chain reaction for logical systems, "
            "hands touching objects for empirical knowledge, "
            "puzzle pieces for coherence, "
            "fork-in-road for agency."
        )

    return "standard", ""

# situation 키워드 → 물리적 배경 (fallback용)
_SETTINGS = {
    "transport": "city street near a transit stop",
    "subway": "underground platform with warm overhead lights",
    "bus": "inside a bus looking out a window",
    "school": "bright classroom with wooden desks",
    "home": "cozy living room with sofa and warm lamps",
    "kitchen": "home kitchen with pots and cooking utensils",
    "shopping": "room with neat product shelves",
    "market": "outdoor market with colorful fresh produce",
    "restaurant": "dining table with steaming bowls and chopsticks",
    "cafe": "warm wooden counter with coffee and ceramic mugs",
    "hospital": "clean bright medical room",
    "office": "tidy modern room with desks",
    "work": "bright office with desk and computer",
    "travel": "scenic outdoor destination",
    "park": "sunny green park with trees",
    "gym": "sports area with exercise equipment",
    "bank": "clean formal room with counter",
    "airport": "bright hall with travelers and luggage",
    "hotel": "tidy room with bed and nightstand",
    "library": "quiet reading room with tall shelves",
}

def _fallback_setting(situation: str) -> str:
    if not situation:
        return "everyday Korean setting"
    low = situation.lower()
    for key, desc in _SETTINGS.items():
        if key in low:
            return desc
    return "everyday Korean setting"


def _ai_word_scene(word: dict, client) -> str:
    """Gemini Flash로 단어에 최적화된 구체적 시각 장면 생성.
    캐시 우선 사용. client=None이면 fallback 사용.
    앵커 사전에 있는 단어는 API 호출 없이 즉시 반환."""
    cache_key = f"word_{word['id']}"
    if cache_key in _scene_cache:
        return _scene_cache[cache_key]

    # 앵커 사전 우선 확인 (API 호출 없이 반환)
    visual_type, strategy = _classify_word_visual_type(word)
    if visual_type == "anchored":
        _scene_cache[cache_key] = strategy
        _save_scene_cache()
        return strategy

    if client is None:
        return _word_prompt_fallback(word["meaning"])

    korean   = word["word"]
    meaning  = word["meaning"]
    pos      = word.get("pos", "명사")
    synonyms = ", ".join((word.get("synonyms") or [])[:3])
    pos_guide = _POS_GUIDE.get(pos, _POS_GUIDE["명사"])

    # 전략 힌트를 프롬프트에 포함 (분류 유형에 따라 특화 안내)
    strategy_block = f"VISUALIZATION STRATEGY: {strategy}\n" if strategy else ""

    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[(
                "You are an illustration director for a Korean vocabulary learning app.\n"
                "Design ONE concrete visual scene for a square flashcard illustration.\n\n"
                f"Korean word: {korean}\n"
                f"Part of speech: {pos}\n"
                f"English meaning: {meaning}\n"
                f"Korean synonyms: {synonyms}\n\n"
                f"{strategy_block}"
                "SETTING RULE: Use MODERN everyday Korean environments. "
                "FORBIDDEN backgrounds: traditional tile-roof houses, wooden hanok, paper screen doors, "
                "traditional courtyards — these are rare tourist sites, NOT where Koreans live daily. "
                "USE: apartment interiors, modern cafes, convenience stores (24h), subway platforms, "
                "school classrooms, offices, city parks, shopping streets, supermarkets, "
                "modern restaurants, apartment building exteriors.\n\n"
                "RULES:\n"
                f"1. {pos_guide}\n"
                "2. A student must INSTANTLY understand what this word means just from the image\n"
                "3. Be HYPER-SPECIFIC — exact objects, exact action, exact positions\n"
                "4. Characters are OPTIONAL. Include only when a living being naturally belongs.\n"
                "   Count: zero (objects/nature/abstract), one (solo action), two+ (social scenes).\n"
                "   PROTAGONIST RULE: if any character appears, the MAIN character is always\n"
                "   'a chibi red panda wearing [outfit]'. Supporting characters can be other animals.\n"
                "5. Composition: choose the most expressive shot — close-up, medium, or wide.\n"
                "   Main subject centered. Not pushed to the bottom.\n"
                "6. NO text, signs, labels, or writing anywhere\n\n"
                "Output: 2-3 sentences ONLY. Start with the main subject and action. "
                "No preamble, no explanation."
            )]
        )
        scene = resp.text.strip()
        _scene_cache[cache_key] = scene
        _save_scene_cache()
        return scene
    except Exception as e:
        print(f"  [AI 장면 생성 실패: {e}] fallback 사용")
        return _word_prompt_fallback(meaning)


def _ai_sentence_scene(word: dict, sent: dict, sent_idx: int, client) -> str:
    """Gemini Flash로 예문에 최적화된 구체적 시각 장면 생성."""
    cache_key = f"sent_{word['id']}_{sent_idx}"
    if cache_key in _scene_cache:
        return _scene_cache[cache_key]

    if client is None:
        return _sentence_scene_fallback(word, sent)

    korean    = word["word"]
    meaning   = word["meaning"]
    situation = sent.get("situation", "")
    ko        = sent.get("ko", "")
    en        = sent.get("en", "")

    # 단어 분류로 문장 장면에도 전략 힌트 활용
    visual_type, strategy = _classify_word_visual_type(word)
    # 앵커 단어는 단어 뜻 장면을 기반으로 문장 상황 추가
    if visual_type == "anchored":
        anchor_hint = (
            f"The core word concept is: {strategy} "
            f"Now adapt this to the specific sentence context below."
        )
    elif strategy:
        anchor_hint = f"WORD VISUALIZATION HINT: {strategy}"
    else:
        anchor_hint = ""

    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[(
                "You are an illustration director for a Korean vocabulary learning app.\n"
                "Design ONE concrete visual scene showing this example sentence in use.\n\n"
                f"Korean word: {korean} (meaning: {meaning})\n"
                f"Situation: {situation}\n"
                f"Korean sentence: {ko}\n"
                f"English sentence: {en}\n"
                + (f"\n{anchor_hint}\n" if anchor_hint else "") +
                "\nSETTING RULE: Use MODERN everyday Korean environments. "
                "FORBIDDEN: traditional tile-roof houses, wooden hanok, paper screen doors. "
                "USE: apartments, modern cafes, convenience stores, subway, schools, "
                "offices, parks, city streets, supermarkets.\n"
                "\nRULES:\n"
                f"1. Show the SPECIFIC MOMENT described in the sentence — not before, not after\n"
                f"2. Make '{korean}' ({meaning.split(',')[0].strip()}) VISUALLY OBVIOUS as the focal concept\n"
                "3. Be HYPER-SPECIFIC — exact objects, exact action, exact location details\n"
                "4. Characters are OPTIONAL. Include only as many as the scene genuinely needs:\n"
                "   zero (objects/location/weather/metaphor), one (solo action), two+ (interaction).\n"
                "   PROTAGONIST RULE: if any character appears, the MAIN one is always\n"
                "   'a chibi red panda wearing [outfit]'. Supporting roles can be other cute animals.\n"
                "5. Composition: choose the most expressive shot — close-up, medium, or wide.\n"
                "   Main subject centered. Not pushed to the bottom.\n"
                "6. No text or signs anywhere.\n\n"
                "Output: 2-3 sentences ONLY. Start with the main subject and action. No preamble."
            )]
        )
        scene = resp.text.strip()
        _scene_cache[cache_key] = scene
        _save_scene_cache()
        return scene
    except Exception as e:
        print(f"  [AI 장면 생성 실패: {e}] fallback 사용")
        return _sentence_scene_fallback(word, sent)


def _ai_improve_scene(original_scene: str, issues: list[str],
                      word: dict, sent: dict | None, client) -> str:
    """VLM 피드백 기반으로 Gemini가 장면 설명 개선."""
    if client is None:
        return original_scene

    korean  = word["word"]
    meaning = word["meaning"]
    issue_text = "; ".join(issues)
    ctx = f"Korean sentence: {sent.get('ko','')} / {sent.get('en','')}" if sent else ""

    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[(
                f"You wrote this illustration prompt:\n{original_scene}\n\n"
                f"A quality checker found these problems: {issue_text}\n\n"
                f"This image is for the Korean word '{korean}' (meaning: {meaning}). {ctx}\n\n"
                "Rewrite the prompt to FIX ALL the listed problems while keeping educational clarity.\n"
                "Keep the same core concept but fix anatomy, scale, perspective, style issues.\n"
                "Output ONLY the improved prompt. 2-3 sentences. No preamble."
            )]
        )
        return resp.text.strip()
    except Exception as e:
        print(f"  [AI 프롬프트 개선 실패: {e}]")
        return original_scene


def _pre_improve_scene_for_regen(word: dict, sent_idx: int,
                                 issues_str: str, client) -> str | None:
    """재생성 전 감사 실패 이유를 반영해 장면 프롬프트를 AI로 사전 개선.
    개선된 장면을 캐시에 저장 후 반환. 이슈 없으면 None 반환."""
    if not issues_str or issues_str.strip() in ("", "—"):
        return None
    issues_list = [i.strip() for i in issues_str.split("|") if i.strip()]
    if not issues_list:
        return None

    ck = f"word_{word['id']}" if sent_idx < 0 else f"sent_{word['id']}_{sent_idx}"

    # 기존 캐시 장면을 기반으로 개선 (없으면 새로 생성)
    existing_scene = _scene_cache.get(ck)
    if not existing_scene:
        if sent_idx < 0:
            existing_scene = _ai_word_scene(word, client)
        else:
            sents = word.get("sentences", [])
            sent = sents[sent_idx] if sent_idx < len(sents) else {}
            existing_scene = _ai_sentence_scene(word, sent, sent_idx, client)

    sent_obj = None
    if sent_idx >= 0:
        sents = word.get("sentences", [])
        sent_obj = sents[sent_idx] if sent_idx < len(sents) else None

    print(f"  [사전 개선] 알려진 문제 반영: {', '.join(i.split(':')[0] for i in issues_list)}")
    improved = _ai_improve_scene(existing_scene, issues_list, word, sent_obj, client)
    _scene_cache[ck] = improved
    _save_scene_cache()
    return improved


# ── Fallback 프롬프트 (client 없을 때) ───────────────────────
def _word_prompt_fallback(meaning: str) -> str:
    keyword = meaning.split(",")[0].strip()
    return (
        f"A clear picture-book illustration showing the concept '{keyword}'. "
        f"One specific concrete moment with objects and setting that immediately "
        f"communicates '{keyword}' without any text."
    )

def _sentence_scene_fallback(word: dict, sent: dict) -> str:
    main = word["meaning"].split(",")[0].strip()
    situation = sent.get("situation", "")
    setting = _fallback_setting(situation)
    return (
        f"A specific scene showing '{main}' in action — "
        f"concrete objects and clear body language tell the story, {setting}, no dialogue"
    )


# ── 텍스트 유발 토큰 치환 ─────────────────────────────────────
_BANNED_SUBSTITUTIONS = [
    (r'\bshop sign\b',          'colorful awning with a simple icon symbol'),
    (r'\bstore sign\b',         'colorful awning with a simple icon symbol'),
    (r'\bsign\b',               'blank placard with a simple pictogram'),
    (r'\bbanner\b',             'hanging colored cloth decoration'),
    (r'\bposter\b',             'framed illustration on the wall'),
    (r'\blabel\b',              'small tag with a simple icon'),
    (r'\bprice tag\b',          'small coin-stack icon'),
    (r'\bmenu board\b',         'illustrated food-picture display board'),
    (r'\bmenu\b',               'illustrated food-picture board'),
    (r'\bchalkboard\b',         'blank chalkboard with chalk drawing of food'),
    (r'\bsmartphone\b',         'small handheld device with a glowing screen showing simple icons'),
    (r'\bcell phone\b',         'small handheld device with glowing icon screen'),
    (r'\blaptop\b',             'open portable computer with abstract icon screen'),
    (r'\bscreen\b',             'glowing surface showing simple geometric icons'),
    (r'\bdisplay\b',            'glowing panel with simple pictogram icons'),
    (r'\bmonitor\b',            'glowing rectangular screen with simple icons'),
    (r'\bnewspaper\b',          'folded paper printed with wavy decorative lines'),
    (r'\bmagazine\b',           'colorful booklet with illustrated cover'),
    (r'\bbook\b',               'illustrated storybook with picture cover'),
    (r'\bdocument\b',           'paper sheet with wavy-line pattern'),
    (r'\breceipt\b',            'small paper strip with dotted line pattern'),
    (r'\bticket\b',             'small colored card with stripe pattern'),
    (r'\bpassport\b',           'small dark booklet with embossed emblem'),
    (r'\bform\b',               'paper sheet with checkbox symbols'),
    (r'\bshop\b',               'room with product shelves'),
    (r'\bstore\b',              'room with displayed items'),
    (r'\bcaf[eé]\b',            'warm counter with coffee cup icons'),
    (r'\bentrance\b',           'open decorative doorway'),
    (r'\breception\b',          'front counter with bell icon'),
    (r'\bbus destination\b',    'bus with colored stripe pattern on front'),
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


_CHAR_MARKERS = (
    'chibi', 'panda', 'animal', 'wearing ',
    'cat ', 'dog ', 'fox ', 'bear ', 'corgi', 'beagle',
    'poodle', 'retriever', 'dalmatian', 'shiba',
    'character', 'figure ',
)

def _apply_style(content: str, word_id: int = 0) -> str:
    """커스텀 프롬프트 + lint + (선택) 캐릭터 교체 + 웹툰 스타일.
    장면 설명에 캐릭터가 언급될 때만 캐릭터 스타일 적용."""
    linted   = _lint_prompt(content)
    injected = _inject_characters(linted, word_id)
    has_chars = any(m in injected.lower() for m in _CHAR_MARKERS)
    return f"{injected}. {_webtoon_style(word_id, has_characters=has_chars)}"


# ── 장면 캐시 ────────────────────────────────────────────────
_scene_cache: dict = {}

def _load_scene_cache():
    global _scene_cache
    if SCENE_CACHE.exists():
        with open(SCENE_CACHE, encoding="utf-8") as f:
            _scene_cache = json.load(f)
        print(f"  장면 캐시 로드: {len(_scene_cache)}개")

def _save_scene_cache():
    try:
        SCENE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with open(SCENE_CACHE, "w", encoding="utf-8") as f:
            json.dump(_scene_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  [캐시 저장 실패: {e}]")




def _flag_image(word: dict, sent_idx: int, prompt: str, reason: str):
    try:
        flagged = []
        if FLAGGED_FILE.exists():
            with open(FLAGGED_FILE, encoding="utf-8") as f:
                flagged = json.load(f)
        flagged.append({
            "word_id": word["id"], "word": word["word"],
            "sent_idx": sent_idx, "reason": reason,
            "prompt": prompt[:200],
            "flagged_at": datetime.now().isoformat(),
        })
        FLAGGED_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(FLAGGED_FILE, "w", encoding="utf-8") as f:
            json.dump(flagged, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ── 커스텀 프롬프트 로드 ──────────────────────────────────────
_custom_prompts: dict = {}

def _load_custom_prompts():
    global _custom_prompts
    if PROMPTS_FILE.exists():
        with open(PROMPTS_FILE, encoding="utf-8") as f:
            _custom_prompts = json.load(f)
        print(f"  커스텀 프롬프트 로드: {len(_custom_prompts)}개 단어")
    else:
        print(f"  커스텀 프롬프트 없음 ({PROMPTS_FILE})")


def get_word_custom_prompt(word_id: int) -> str | None:
    """단어 ID로 커스텀 word_prompt 반환 (없으면 None)"""
    entry = _custom_prompts.get(str(word_id))
    if entry and entry.get("word_prompt"):
        return _apply_style(entry["word_prompt"], word_id)
    return None


def get_sentence_custom_prompt(word_id: int, sent_idx: int) -> str | None:
    """단어 ID + 예문 인덱스로 커스텀 sentence prompt 반환 (없으면 None)"""
    entry = _custom_prompts.get(str(word_id))
    if entry:
        sentences = entry.get("sentences", [])
        if sent_idx < len(sentences) and sentences[sent_idx]:
            return _apply_style(sentences[sent_idx], word_id)
    return None


def word_dir(word: dict) -> Path:
    """단어별 폴더: illustrations/lv{level}/{id}_{word}/"""
    return OUTPUT_DIR / f"lv{word['level']}" / f"{word['id']}_{word['word']}"


def word_img_path(word: dict) -> Path:
    """단어 일러스트: illustrations/lv{level}/{id}_{word}/word.png"""
    return word_dir(word) / "word.png"


def sent_img_path(word: dict, idx: int) -> Path:
    """예문 일러스트: illustrations/lv{level}/{id}_{word}/{idx}.png"""
    return word_dir(word) / f"{idx}.png"


def _log_error(msg: str):
    """에러를 파일에 기록"""
    try:
        log_path = Path("/app/logs/illust_errors.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    except Exception:
        pass


def _generate_once_flux(prompt: str, output_path: Path) -> bool:
    """Flux Schnell (Replicate API)로 이미지 생성"""
    try:
        import replicate
        import urllib.request
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={
                "prompt": prompt,
                "num_outputs": 1,
                "aspect_ratio": "1:1",
                "output_format": "png",
                "output_quality": 90,
                "go_fast": True,
                "megapixels": "1",
            },
        )
        if output:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(str(output[0]), str(output_path))
            _track_usage(success=True)
            return True
        _log_error(f"Flux 빈 응답: {output_path.name} | prompt: {prompt[:100]}")
        _track_usage(success=False)
        return False
    except Exception as e:
        _log_error(f"Flux 생성 오류: {e} | {output_path.name} | prompt: {prompt[:100]}")
        print(f"  Flux 생성 오류: {e}")
        _track_usage(success=False)
        return False


_IMAGE_MODEL = "gemini-3.1-flash-image-preview"
_CHARS_DIR   = Path("/app/assets/characters")

# 캐릭터 레퍼런스 이미지 캐시 (프로세스당 1회 로드)
_char_refs_cache: list | None = None

def _load_char_refs() -> list:
    """캐릭터 레퍼런스 이미지 로드 (PIL Image 리스트, 없으면 빈 리스트)"""
    global _char_refs_cache
    if _char_refs_cache is not None:
        return _char_refs_cache
    from PIL import Image as PILImage
    refs = []
    main = _CHARS_DIR / "main_character.png"
    if main.exists():
        try:
            refs.append(PILImage.open(str(main)).convert("RGB"))
        except Exception:
            pass
    for extra in sorted(_CHARS_DIR.glob("extra_characters*.png")):
        try:
            refs.append(PILImage.open(str(extra)).convert("RGB"))
        except Exception:
            pass
    if refs:
        print(f"  [캐릭터 레퍼런스] {len(refs)}장 로드")
    else:
        print(f"  [경고] 캐릭터 레퍼런스 없음 ({_CHARS_DIR}) — 텍스트 프롬프트만 사용")
    _char_refs_cache = refs
    return refs


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


def _generate_once(prompt: str, output_path: Path, client) -> bool:
    """단일 이미지 생성 — 백엔드에 따라 Gemini Image / Flux 분기"""
    if _BACKEND == "flux":
        return _generate_once_flux(prompt, output_path)
    # ── Gemini Flash Image ──────────────────────────────────
    try:
        char_refs = _load_char_refs()
        contents  = char_refs + [prompt]   # 캐릭터 레퍼런스 이미지 + 텍스트 프롬프트
        response = client.models.generate_content(
            model=_IMAGE_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=[types.Modality.IMAGE],
                image_config=types.ImageConfig(aspect_ratio="1:1"),
            ),
        )
        if _save_generated_image(response, output_path):
            _track_usage(success=True)
            return True
        _log_error(f"빈 응답 (이미지 없음): {output_path.name} | prompt: {prompt[:100]}")
        _track_usage(success=False)
        return False
    except Exception as e:
        _log_error(f"생성 오류: {e} | {output_path.name} | prompt: {prompt[:100]}")
        print(f"  생성 오류: {e}")
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            _track_usage(success=False, exhausted=True)
            print("\n[중단] API 일일 할당량 초과 — 내일 다시 시도하세요.")
            raise SystemExit(1)
        _track_usage(success=False)
        return False

def _parse_vlm_json(raw: str) -> dict:
    """VLM 응답에서 JSON 추출"""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw[raw.index("\n") + 1:]
        if raw.endswith("```"):
            raw = raw[:-3].strip()
    return json.loads(raw)


def _verify_image_vlm(image_path: Path, client) -> tuple[bool, str]:
    """Gemini Vision으로 이미지 내 텍스트 감지. 텍스트 없으면 (True, '') 반환"""
    if client is None:
        return True, ""
    try:
        import PIL.Image
        img = PIL.Image.open(str(image_path))
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                img,
                (
                    "Does this image contain ANY visible text, letters, numbers, "
                    "characters (in any language), speech bubbles, or captions? "
                    "Answer ONLY with JSON (no markdown): "
                    "{\"has_text\": true/false, \"details\": \"brief description or none\"}"
                ),
            ],
        )
        result = _parse_vlm_json(response.text or "")
        has_text = result.get("has_text", False)
        return not has_text, result.get("details", "")
    except Exception as e:
        return True, f"검증 오류 (통과 처리): {e}"


def _verify_image_style(image_path: Path, client) -> tuple[bool, str]:
    """Gemini Vision으로 스타일·비율·투시·해부학적 이상·물리적 오류 종합 검증.
    Returns (passed, issues_str)."""
    if client is None:
        return True, ""
    try:
        import PIL.Image
        img = PIL.Image.open(str(image_path))
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                img,
                (
                    "You are a strict quality checker for children's book illustrations. "
                    "Carefully examine every part of this image and answer ONLY with JSON (no markdown):\n"
                    "{\n"
                    "  \"has_person\": true/false,\n"

                    # 비율
                    "  \"proportion_ok\": true if no person present OR standing person height is 40-70% of frame height,\n"
                    "  \"scale_ok\": true if objects are correctly sized relative to humans "
                    "(chair seat at knee height, table at hip height, door taller than person — "
                    "no person dwarfed by a coffee cup, no person larger than a building interior wall),\n"

                    # 투시
                    "  \"perspective_ok\": true if camera is roughly eye-level, "
                    "no extreme distortion, objects recede naturally,\n"

                    # 스타일/팔레트
                    "  \"style_ok\": true if flat/semi-flat illustration (NOT photorealistic, NOT oil painting),\n"
                    "  \"palette_ok\": true if overall tone is warm/light/pastel (NOT dark or black-dominant),\n"

                    # 해부학적 이상
                    "  \"anatomy_ok\": true if all human figures have correct anatomy — "
                    "exactly 2 arms, 2 legs, 1 head, normal hand/finger count, "
                    "no extra limbs, no missing limbs, no floating body parts, "
                    "no fused or merged figures, normal facial features (2 eyes, 1 nose, 1 mouth),\n"

                    # 물리적/논리적 이상
                    "  \"physics_ok\": true if all objects follow physical logic — "
                    "no upside-down objects that should be right-side-up (cups, plates, furniture), "
                    "no objects passing through other solid objects, "
                    "no doors or windows opening impossibly (e.g. two doors colliding into each other), "
                    "no floating objects without context, "
                    "objects rest on surfaces correctly,\n"

                    # 구체적 문제 목록
                    "  \"issues\": \"concise comma-separated list of specific problems found "
                    "(e.g. '3 arms on person', 'cup is upside-down', 'person is 10% of frame', "
                    "'two doors opening into each other'), or empty string if none\"\n"
                    "}"
                ),
            ],
        )
        result = _parse_vlm_json(response.text or "")
        failed = []
        if not result.get("proportion_ok", True):
            failed.append("proportion")
        if not result.get("scale_ok", True):
            failed.append("scale")
        if not result.get("perspective_ok", True):
            failed.append("perspective")
        if not result.get("style_ok", True):
            failed.append("style")
        if not result.get("palette_ok", True):
            failed.append("palette")
        if not result.get("anatomy_ok", True):
            failed.append("anatomy")
        if not result.get("physics_ok", True):
            failed.append("physics")
        issues = result.get("issues", "")
        if failed:
            return False, f"[{','.join(failed)}] {issues}"
        return True, ""
    except Exception as e:
        return True, f"스타일 검증 오류 (통과 처리): {e}"


def _verify_image_educational(image_path: Path, word: dict, client) -> tuple[bool, str]:
    """이미지가 단어 의미를 교육적으로 명확하게 전달하는지 검증.
    학생이 텍스트 없이 이미지만 보고 단어 뜻을 추측할 수 있어야 함."""
    if client is None:
        return True, ""
    try:
        import PIL.Image
        img = PIL.Image.open(str(image_path))
        korean  = word["word"]
        meaning = word["meaning"].split(",")[0].strip()
        pos     = word.get("pos", "명사")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                img,
                (
                    f"This illustration is for a Korean vocabulary flashcard.\n"
                    f"Korean word: '{korean}' | English meaning: '{meaning}' | Part of speech: {pos}\n\n"
                    f"Evaluate strictly. Answer ONLY with JSON (no markdown):\n"
                    "{\n"
                    f"  \"recognizable\": true if a student could guess this image represents "
                    f"'{meaning}' without seeing any text (must be clear and unambiguous),\n"
                    f"  \"concept_visible\": true if the core concept of '{meaning}' is the "
                    f"clear visual focus (not hidden in background or secondary),\n"
                    f"  \"specific\": true if the scene is specific and concrete "
                    f"(NOT vague, NOT overly abstract, NOT a generic person doing nothing clear),\n"
                    f"  \"clarity_score\": integer 1-5 "
                    f"(5=instantly obvious, 3=guessable, 1=impossible to guess),\n"
                    f"  \"issues\": \"specific description of what is unclear or wrong, or empty string\"\n"
                    "}"
                ),
            ],
        )
        result = _parse_vlm_json(response.text or "")
        score = result.get("clarity_score", 3)
        ok = (
            result.get("recognizable", True)
            and result.get("concept_visible", True)
            and result.get("specific", True)
            and score >= 3
        )
        issues = result.get("issues", "")
        if not ok:
            return False, f"[educational,score={score}] {issues}"
        return True, f"score={score}"
    except Exception as e:
        return True, f"교육 검증 오류 (통과): {e}"


def _verify_image_full(image_path: Path, client,
                       word: dict = None) -> tuple[bool, list[str]]:
    """텍스트 + 스타일/비율/해부/물리 + 교육적 품질 통합 검증.
    Returns (passed, [issue_strings])"""
    issues = []
    text_ok, text_detail = _verify_image_vlm(image_path, client)
    if not text_ok:
        issues.append(f"text:{text_detail}")
    style_ok, style_detail = _verify_image_style(image_path, client)
    if not style_ok:
        issues.append(f"style:{style_detail}")
    if word:
        edu_ok, edu_detail = _verify_image_educational(image_path, word, client)
        if not edu_ok:
            issues.append(f"educational:{edu_detail}")
    return len(issues) == 0, issues


def _reinforce_no_text(prompt: str) -> str:
    """재생성 시 텍스트 금지 지시 강화"""
    return (
        prompt
        + " CRITICAL OVERRIDE: absolutely zero visible text, zero letters, zero digits, "
        "zero characters in any language, all surfaces completely blank or abstract shapes only"
    )


def _reinforce_scale(prompt: str) -> str:
    """재생성 시 비율/투시 강화"""
    return (
        prompt
        + " SCALE FIX: human figure must be exactly 50-65% of frame height — "
        "not a giant filling the whole frame, not a tiny dwarf. "
        "Eye-level perspective. Objects (chairs, tables, doors) correctly sized next to person."
    )


def _reinforce_style(prompt: str) -> str:
    """재생성 시 스타일 강화"""
    return (
        prompt
        + " STYLE FIX: warm watercolor and pencil sketch style ONLY — "
        "soft loose brushwork, visible watercolor paper texture, "
        "gentle pencil outlines (NOT thick black ink), "
        "pastel palette with peach/cream/sage tones, NO flat vector, NO cel-shading."
    )


def _reinforce_anatomy(prompt: str) -> str:
    """재생성 시 해부학적 정확성 강화"""
    return (
        prompt
        + " ANATOMY FIX: every human figure must have EXACTLY 2 arms, 2 legs, 1 head, "
        "2 eyes, 1 nose, 1 mouth, normal 5-fingered hands — "
        "absolutely no extra limbs, no missing limbs, no fused bodies, "
        "no floating detached body parts. Simple clean anatomy."
    )


def _reinforce_physics(prompt: str) -> str:
    """재생성 시 물리적 논리성 강화"""
    return (
        prompt
        + " PHYSICS FIX: all objects must obey normal physical logic — "
        "cups and plates right-side-up, furniture on the floor, "
        "doors open in one direction only, objects rest on surfaces, "
        "no items floating in mid-air without reason, "
        "no objects passing through walls or each other."
    )


def generate_image(prompt: str, output_path: Path, client,
                   word: dict = None, sent_idx: int = -1,
                   sent: dict = None) -> bool:
    """이미지 생성 + VLM 하네스 루프 (--vlm-verify 활성화 시)
    검증: 텍스트 / 스타일·비율·해부·물리 / 교육적 명확성
    실패 시: 문제 유형별 프롬프트 강화 → AI 개선 → 재생성 반복"""
    if output_path.exists() and output_path.stat().st_size > 0:
        return True
    elif output_path.exists():
        output_path.unlink()  # 빈 파일 제거 후 재생성

    max_attempts = 5 if _VLM_VERIFY else 1
    word_id = word["id"] if word else 0
    # 커스텀 프롬프트는 이미 _apply_style 처리됨 → 중복 방지
    is_full_prompt = "TWO animal characters in frame:" in prompt
    current_scene = prompt
    current_prompt = prompt if is_full_prompt else _apply_style(_lint_prompt(prompt), word_id)

    for attempt in range(max_attempts):
        ok = _generate_once(current_prompt, output_path, client)
        if not ok:
            if word:
                _flag_image(word, sent_idx, current_prompt, "generation failed")
            return False

        if not _VLM_VERIFY:
            return True

        # ── 통합 VLM 검증 ──────────────────────────────────
        passed, issues = _verify_image_full(output_path, client, word=word)
        if passed:
            print(f"  [VLM ✓] 모든 검사 통과")
            return True

        issue_str = " | ".join(issues)
        remaining = max_attempts - attempt - 1
        print(f"  [VLM ✗] {issue_str} — 재시도 {remaining}회 남음")
        _flag_image(word, sent_idx, current_prompt, issue_str)
        if output_path.exists():
            output_path.unlink()

        if remaining == 0:
            break

        # ── 프롬프트 개선 전략 ──────────────────────────────
        # 1단계: 룰 기반 강화 (빠름)
        if attempt < 2:
            reinforced = _lint_prompt(current_scene)
            if any("text" in i for i in issues):
                reinforced = _reinforce_no_text(reinforced)
            if any("scale" in i or "proportion" in i for i in issues):
                reinforced = _reinforce_scale(reinforced)
            if any("style" in i or "palette" in i for i in issues):
                reinforced = _reinforce_style(reinforced)
            if any("anatomy" in i for i in issues):
                reinforced = _reinforce_anatomy(reinforced)
            if any("physics" in i for i in issues):
                reinforced = _reinforce_physics(reinforced)
            current_scene = reinforced
        else:
            # 2단계: AI 기반 장면 재설계 (깊은 개선)
            print(f"  [AI] 장면 재설계 중...")
            improved = _ai_improve_scene(current_scene, issues, word, sent, client)
            current_scene = improved
            # 장면 캐시 갱신
            if word:
                ck = f"word_{word['id']}" if sent_idx < 0 else f"sent_{word['id']}_{sent_idx}"
                _scene_cache[ck] = improved
                _save_scene_cache()

        # 커스텀 프롬프트는 이미 스타일 포함 → 중복 방지
        if is_full_prompt:
            current_prompt = _lint_prompt(current_scene)
        else:
            current_prompt = _apply_style(_lint_prompt(current_scene), word_id)

    if word:
        _flag_image(word, sent_idx, current_prompt, "harness failed after all retries")
    return False


def generate_one(word: dict, client) -> bool:
    """단어 일러스트 생성 → illustrations/lv{level}/{id}_{word}/word.png
    우선순위: 커스텀 프롬프트 → AI 장면 생성 → fallback"""
    korean_word = word["word"]
    custom_full = get_word_custom_prompt(word["id"])
    if custom_full:
        print(f"  [커스텀] {korean_word}")
        return generate_image(custom_full, word_img_path(word), client,
                              word=word, sent_idx=-1)
    # AI 장면 생성 (캐시 활용)
    scene = _ai_word_scene(word, client)
    return generate_image(scene, word_img_path(word), client,
                          word=word, sent_idx=-1)


def build_sentence_prompt(word: dict, sent: dict, sent_idx: int = -1) -> str:
    """예문 프롬프트 생성 — 우선순위: 커스텀 → AI 생성 (캐시 활용)
    주의: client 없이는 fallback 사용. generate_sentences에서 직접 AI 호출 권장."""
    if sent_idx >= 0:
        custom = get_sentence_custom_prompt(word["id"], sent_idx)
        if custom:
            return custom
    return _sentence_scene_fallback(word, sent)


def generate_sentences(word: dict, client) -> tuple[int, int]:
    """예문 일러스트 생성 → illustrations/lv{level}/{id}_{word}/{idx}.png
    AI 장면 생성 → 이미지 생성 → VLM 하네스 검증 루프"""
    done, fail = 0, 0
    for idx, sent in enumerate(word.get("sentences", [])):
        output_path = sent_img_path(word, idx)
        en = sent.get("en", "")
        # 우선순위: 커스텀 → AI 장면 생성
        custom = get_sentence_custom_prompt(word["id"], idx)
        if custom:
            scene = custom
            src = "커스텀"
        else:
            scene = _ai_sentence_scene(word, sent, idx, client)
            src = "AI"
        print(f"  [{idx+1}/10] [{src}] '{en[:45]}' → 장면 생성 완료")
        if generate_image(scene, output_path, client,
                          word=word, sent_idx=idx, sent=sent):
            done += 1
            print(f"    [OK] {output_path.name}")
        else:
            fail += 1
            print(f"    [FAIL] (스킵)")
        time.sleep(0.3)
    return done, fail


PROG_FILE = Path("/app/logs/illust_progress.json")


def _write_prog(pct: int, step: str = "", done_word: int = 0, done_sent: int = 0):
    try:
        PROG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROG_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "status": "running", "pct": pct, "step": step,
                "done_word": done_word, "done_sent": done_sent,
                "updated_at": datetime.now().isoformat(),
            }, f, ensure_ascii=False)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="TOPIK 일러스트 생성 (단어 + 예문)")
    parser.add_argument("--db", default="/app/data/LanguageTest/words_db.json")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end",   type=int, default=1800)
    parser.add_argument("--words-only",     action="store_true", help="단어 일러스트만")
    parser.add_argument("--sentences-only", action="store_true", help="예문 일러스트만")
    parser.add_argument("--sentences-for-id", type=int, default=None,
                        help="특정 단어 ID의 예문 일러스트만 생성")
    parser.add_argument("--regen", type=int, default=None,
                        help="특정 단어 ID의 이미지 재생성 (기존 삭제 후)")
    parser.add_argument("--regen-idx", type=int, default=None,
                        help="--regen과 함께: 재생성할 예문 인덱스 (0-9). 미지정시 word.png 재생성")
    parser.add_argument("--regen-issues", type=str, default=None,
                        help="재생성 시 반영할 감사 실패 이유 ('text:설명 | style:설명' 형식)")
    parser.add_argument("--backend", default="imagen", choices=["imagen", "flux"],
                        help="이미지 생성 백엔드: imagen (기본) | flux (Flux Schnell/Replicate)")
    parser.add_argument("--vlm-verify", action="store_true",
                        help="생성 후 Gemini Vision으로 텍스트+비율+스타일 검증 + 자동 재생성 (권장)")
    parser.add_argument("--style-audit", nargs="+", type=int, default=None, metavar="ID",
                        help="기존 이미지 스타일 감사: --style-audit 1 5 10 (word_id 목록). "
                             "생성 없이 이미지 품질만 검사하고 결과를 출력")
    parser.add_argument("--style-audit-all", action="store_true",
                        help="--start~--end 범위의 모든 생성된 이미지 감사")
    parser.add_argument("--scan-prompts", action="store_true",
                        help="API 호출 없이 모든 단어 시각화 전략 분류 및 통계 출력 (dry-run)")
    parser.add_argument("--regen-audit-failed", action="store_true",
                        help="style_audit.json의 실패 이미지를 --vlm-verify로 재생성")
    args = parser.parse_args()

    global _BACKEND, _VLM_VERIFY
    _BACKEND = args.backend
    _VLM_VERIFY = args.vlm_verify
    print(f"백엔드: {_BACKEND.upper()}")
    if _VLM_VERIFY:
        print("VLM 통합 검증: 활성화 (텍스트 + 비율 + 스타일)")

    if _BACKEND == "flux":
        replicate_key = os.environ.get("REPLICATE_API_TOKEN", "")
        if not replicate_key:
            print("오류: REPLICATE_API_TOKEN 환경변수가 없습니다.")
            print("  → https://replicate.com/account/api-tokens 에서 발급 후 .env에 추가")
            return
        os.environ["REPLICATE_API_TOKEN"] = replicate_key
        client = None
    else:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            print("오류: GEMINI_API_KEY 환경변수가 없습니다.")
            return
        client = genai.Client(api_key=api_key)
    _load_custom_prompts()
    _load_scene_cache()

    with open(args.db, encoding="utf-8") as f:
        db = json.load(f)

    # ── 프롬프트 전략 스캔 모드 (dry-run) ──────────────────────
    if args.scan_prompts:
        with open(args.db, encoding="utf-8") as f:
            db = json.load(f)
        from collections import Counter
        type_counts: dict[int, Counter] = {}
        for w in db:
            lv = w["level"]
            vtype, _ = _classify_word_visual_type(w)
            if lv not in type_counts:
                type_counts[lv] = Counter()
            type_counts[lv][vtype] += 1
        print("\n=== 단어 시각화 전략 분류 통계 ===\n")
        all_types: Counter = Counter()
        for lv in sorted(type_counts):
            c = type_counts[lv]
            total_lv = sum(c.values())
            anchored = c.get("anchored", 0)
            print(f"  {lv}급 ({total_lv}개 단어):")
            for t, n in sorted(c.items(), key=lambda x: -x[1]):
                bar = "█" * (n * 20 // total_lv)
                pct = n * 100 // total_lv
                label = "✓ 앵커(API절약)" if t == "anchored" else t
                print(f"    {label:30s} {n:3d}개 ({pct:2d}%) {bar}")
            ai_calls = total_lv - anchored
            print(f"    → AI 호출 필요: {ai_calls}개, 앵커 절약: {anchored}개\n")
            all_types.update(c)
        print(f"  전체 합계 ({sum(all_types.values())}개 단어):")
        total_all = sum(all_types.values())
        for t, n in sorted(all_types.items(), key=lambda x: -x[1]):
            print(f"    {t:30s} {n:3d}개 ({n*100//total_all:2d}%)")
        print(f"\n  앵커 커버리지: {all_types.get('anchored',0)}/{total_all} "
              f"({all_types.get('anchored',0)*100//total_all}%) API 절약\n")
        return

    # ── 스타일 감사 모드 ─────────────────────────────────────────
    if args.style_audit or args.style_audit_all:
        if args.style_audit_all:
            target_words = [w for w in db if args.start <= w["id"] <= args.end]
        else:
            target_words = [w for w in db if w["id"] in args.style_audit]
        total_images = sum(1 + len(w.get("sentences", [])) for w in target_words)
        print(f"\n=== 스타일 감사 시작: {len(target_words)}개 단어, {total_images}개 이미지 (단어+예문) ===\n")
        audit_results = []
        pass_count = fail_count = skip_count = 0
        for w in target_words:
            lv = w["level"]
            # ── 단어 이미지 감사 ──────────────────────────────
            wp = word_img_path(w)
            label = f"[{w['id']}] {w['word']} (lv{lv}) word"
            if not wp.exists():
                print(f"  {label} — [SKIP] 이미지 없음")
                skip_count += 1
            else:
                passed, issues_list = _verify_image_full(wp, client, word=w)
                status = "OK" if passed else "FAIL"
                issue_str = " | ".join(issues_list) if issues_list else "—"
                print(f"  {label} [{status}] {issue_str}")
                audit_results.append({
                    "word_id": w["id"], "word": w["word"], "level": lv,
                    "sent_idx": -1,
                    "passed": passed, "issues": issue_str,
                    "issue_types": [i.split(":")[0] for i in issues_list],
                })
                if passed:
                    pass_count += 1
                else:
                    fail_count += 1
                time.sleep(0.3)
            # ── 예문 이미지 감사 ──────────────────────────────
            for idx, sent in enumerate(w.get("sentences", [])):
                sp = sent_img_path(w, idx)
                slabel = f"[{w['id']}] {w['word']} (lv{lv}) sent[{idx}]"
                if not sp.exists():
                    print(f"  {slabel} — [SKIP] 이미지 없음")
                    skip_count += 1
                    continue
                passed, issues_list = _verify_image_full(sp, client, word=w)
                status = "OK" if passed else "FAIL"
                issue_str = " | ".join(issues_list) if issues_list else "—"
                print(f"  {slabel} [{status}] {issue_str}")
                audit_results.append({
                    "word_id": w["id"], "word": w["word"], "level": lv,
                    "sent_idx": idx,
                    "passed": passed, "issues": issue_str,
                    "issue_types": [i.split(":")[0] for i in issues_list],
                })
                if passed:
                    pass_count += 1
                else:
                    fail_count += 1
                time.sleep(0.3)
        print(f"\n=== 감사 완료: 통과 {pass_count} / 실패 {fail_count} / 스킵 {skip_count} ===")
        # 결과를 JSON으로 저장
        audit_path = Path("/app/logs/style_audit.json")
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump({
                "audited_at": datetime.now().isoformat(),
                "pass": pass_count, "fail": fail_count, "skip": skip_count,
                "results": audit_results,
            }, f, ensure_ascii=False, indent=2)
        print(f"결과 저장: {audit_path}")
        return

    # ── 감사 실패 이미지 재생성 ──────────────────────────────────
    if args.regen_audit_failed:
        audit_path = Path("/app/logs/style_audit.json")
        if not audit_path.exists():
            print("오류: style_audit.json 없음 — 먼저 --style-audit-all 실행 필요")
            return
        with open(audit_path, encoding="utf-8") as f:
            audit_data = json.load(f)
        failed_entries = [r for r in audit_data.get("results", []) if not r["passed"]]
        if not failed_entries:
            print("재생성 대상 없음 (모두 통과)")
            return
        with open(args.db, encoding="utf-8") as f:
            db = json.load(f)
        id_to_word = {w["id"]: w for w in db}
        _VLM_VERIFY = True  # 재생성 시 검증 강제 활성화
        word_fails = [e for e in failed_entries if e.get("sent_idx", -1) == -1]
        sent_fails = [e for e in failed_entries if e.get("sent_idx", -1) >= 0]
        print(f"\n=== 감사 실패 재생성: 단어 {len(word_fails)}개, 예문 {len(sent_fails)}개 ===\n")
        success = fail = 0
        # ── 단어 이미지 재생성 ────────────────────────────────
        for entry in word_fails:
            wid = entry["word_id"]
            word = id_to_word.get(wid)
            if not word:
                print(f"  [SKIP] ID {wid} DB에 없음")
                continue
            lv = word["level"]
            target = word_img_path(word)
            issues_str = entry.get("issues", "")
            print(f"  [{wid}] {word['word']} (lv{lv}) word — {issues_str[:70]}")
            if target.exists():
                target.unlink()
            # 감사 실패 이유를 반영해 장면 프롬프트 사전 개선 → 캐시에 저장
            improved = _pre_improve_scene_for_regen(word, -1, issues_str, client)
            if not improved:
                # 이슈 정보 없으면 캐시 초기화 후 새로 생성
                ck = f"word_{word['id']}"
                if ck in _scene_cache:
                    del _scene_cache[ck]
                    _save_scene_cache()
            ok = generate_one(word, client)
            if ok:
                success += 1
                print(f"    [OK]")
            else:
                fail += 1
                print(f"    [FAIL]")
            time.sleep(0.5)
        # ── 예문 이미지 재생성 ────────────────────────────────
        for entry in sent_fails:
            wid = entry["word_id"]
            idx = entry["sent_idx"]
            word = id_to_word.get(wid)
            if not word:
                print(f"  [SKIP] ID {wid} DB에 없음")
                continue
            lv = word["level"]
            sents = word.get("sentences", [])
            if idx >= len(sents):
                print(f"  [SKIP] ID {wid} 예문[{idx}] 없음")
                continue
            sent = sents[idx]
            target = sent_img_path(word, idx)
            issues_str = entry.get("issues", "")
            print(f"  [{wid}] {word['word']} (lv{lv}) sent[{idx}] — {issues_str[:70]}")
            if target.exists():
                target.unlink()
            # 감사 실패 이유를 반영해 장면 프롬프트 사전 개선
            improved = _pre_improve_scene_for_regen(word, idx, issues_str, client)
            if improved:
                scene = improved
            else:
                ck = f"sent_{word['id']}_{idx}"
                if ck in _scene_cache:
                    del _scene_cache[ck]
                    _save_scene_cache()
                scene = _ai_sentence_scene(word, sent, idx, client)
            ok = generate_image(scene, target, client, word=word, sent_idx=idx, sent=sent)
            if ok:
                success += 1
                print(f"    [OK]")
            else:
                fail += 1
                print(f"    [FAIL]")
            time.sleep(0.5)
        _save_scene_cache()
        print(f"\n=== 재생성 완료: 성공 {success} / 실패 {fail} ===")
        return

    # ── 개별 재생성 모드 ────────────────────────────────────────
    if args.regen is not None:
        word = next((w for w in db if w["id"] == args.regen), None)
        if not word:
            print(f"단어 ID {args.regen}를 찾을 수 없습니다.")
            return
        lv = word["level"]
        issues_str = args.regen_issues or ""
        if args.regen_idx is not None:
            # 예문 1장 재생성
            idx = args.regen_idx
            target = sent_img_path(word, idx)
            if target.exists():
                target.unlink()
                print(f"기존 삭제: {target}")
            sent = word.get("sentences", [])[idx] if idx < len(word.get("sentences", [])) else {}
            # 예문 재생성: 캐시를 항상 먼저 삭제 → 예문 기반 완전 새 장면 생성
            cache_key = f"sent_{word['id']}_{idx}"
            if cache_key in _scene_cache:
                del _scene_cache[cache_key]
                _save_scene_cache()
                print(f"  [캐시 삭제] {cache_key}")
            # 사용자 노트 또는 예문 텍스트로 추가 개선 지시
            if not issues_str and sent:
                ko = sent.get("ko", "")
                en = sent.get("en", "")
                if en or ko:
                    issues_str = (
                        f"educational:이미지가 이 예문을 명확히 표현해야 함 — "
                        f"{en} / {ko}. "
                        "예문의 구체적인 행동·상황·장소를 중심으로 장면을 재설계할 것"
                    )
            # 캐시 삭제 후 _ai_sentence_scene이 새 장면 생성 → 추가 노트 있으면 개선 적용
            scene = _ai_sentence_scene(word, sent, idx, client)
            if issues_str:
                try:
                    improved = _ai_improve_scene(scene, [s.strip() for s in issues_str.split("|") if s.strip()],
                                                 word, sent, client)
                    if improved:
                        scene = improved
                        _scene_cache[cache_key] = improved
                        _save_scene_cache()
                except Exception as e_imp:
                    print(f"  [장면 개선 오류, 기본 장면 사용: {e_imp}]")
            print(f"재생성: {word['word']} 예문[{idx}]")
            ok = generate_image(scene, target, client, word=word, sent_idx=idx, sent=sent)
            _save_scene_cache()
            print("성공" if ok else "실패")
        else:
            # 단어 이미지 재생성
            target = word_img_path(word)
            if target.exists():
                target.unlink()
                print(f"기존 삭제: {target}")
            # 감사 실패 이유 반영 사전 개선 (없으면 캐시 초기화 후 새로 생성)
            try:
                improved = _pre_improve_scene_for_regen(word, -1, issues_str, client)
            except Exception as e_pre:
                print(f"  [사전 개선 오류, 기본 생성으로 대체: {e_pre}]")
                improved = None
            if not improved:
                cache_key = f"word_{word['id']}"
                if cache_key in _scene_cache:
                    del _scene_cache[cache_key]
                    _save_scene_cache()
            print(f"재생성: {word['word']} 단어 이미지")
            ok = generate_one(word, client)
            print("성공" if ok else "실패")
        return

    # ── 특정 단어 예문 모드 ───────────────────────────────────
    if args.sentences_for_id is not None:
        word = next((w for w in db if w["id"] == args.sentences_for_id), None)
        if not word:
            print(f"단어 ID {args.sentences_for_id}를 찾을 수 없습니다.")
            return
        print(f"예문 일러스트 생성: {word['word']} ({word['meaning']})")
        print(f"예상 비용: ${len(word.get('sentences',[])) * 0.02:.2f}\n")
        done, fail = generate_sentences(word, client)
        _save_scene_cache()
        print(f"\n완료! 생성 {done}개 | 실패 {fail}개")
        print(f"총 비용: ${done * 0.02:.2f}")
        return

    # ── 배치 모드 (단어 + 예문) ──────────────────────────────
    words = [w for w in db if args.start <= w["id"] <= args.end]

    # 생성 필요한 수 계산
    need_word = [] if args.sentences_only else [
        w for w in words if not word_img_path(w).exists()
    ]
    need_sent = [] if args.words_only else [
        (w, idx, sent)
        for w in words
        for idx, sent in enumerate(w.get("sentences", []))
        if not sent_img_path(w, idx).exists()
    ]
    total = len(need_word) + len(need_sent)

    unit_cost = 0.003 if _BACKEND == "flux" else 0.02
    print(f"단어 일러스트 생성 필요: {len(need_word)}개")
    print(f"예문 일러스트 생성 필요: {len(need_sent)}개")
    print(f"총 예상 비용: ${total * unit_cost:.2f} ({_BACKEND.upper()})\n")

    done_word = 0
    done_sent = 0
    fail = 0
    completed = 0
    last_word_id = args.start

    try:
        for i, word in enumerate(words):
            last_word_id = word["id"]
            step_base = f"[{i+1}/{len(words)}] {word['word']}"

            # ── 단어 일러스트 ──────────────────────────────────
            if not args.sentences_only:
                wpath = word_img_path(word)
                if not wpath.exists():
                    src = "커스텀" if get_word_custom_prompt(word["id"]) else "기본"
                    keyword = word["meaning"].split(",")[0].strip().split()[0]
                    print(f"{step_base} [단어/{src}] '{keyword}' 생성 중...")
                    if generate_one(word, client):
                        done_word += 1
                        print(f"  [OK] {wpath.name}")
                    else:
                        fail += 1
                        print(f"  [FAIL] (스킵)")
                    completed += 1
                    time.sleep(0.3)
                    pct = int(completed / total * 100) if total else 100
                    _write_prog(pct, f"단어: {word['word']}", done_word, done_sent)

            # ── 예문 일러스트 ──────────────────────────────────
            if not args.words_only:
                sents = word.get("sentences", [])
                for idx, sent in enumerate(sents):
                    spath = sent_img_path(word, idx)
                    if spath.exists():
                        continue
                    custom = get_sentence_custom_prompt(word["id"], idx)
                    if custom:
                        scene = custom
                        src = "커스텀"
                    else:
                        scene = _ai_sentence_scene(word, sent, idx, client)
                        src = "AI"
                    en = sent.get("en", "")
                    print(f"  [예문 {idx+1}/{len(sents)}] [{src}] {en[:40]}")
                    if generate_image(scene, spath, client, word=word, sent_idx=idx, sent=sent):
                        done_sent += 1
                        print(f"    [OK] {spath.name}")
                    else:
                        fail += 1
                        print(f"    [FAIL] (스킵)")
                    completed += 1
                    time.sleep(0.3)
                    pct = int(completed / total * 100) if total else 100
                    _write_prog(pct, f"예문: {word['word']} [{idx+1}/{len(sents)}]", done_word, done_sent)

            if (done_word + done_sent) > 0 and (done_word + done_sent) % 20 == 0:
                _save_scene_cache()
                print(f"\n--- 누계: 단어 {done_word}개, 예문 {done_sent}개 / ${(done_word+done_sent)*unit_cost:.2f} ---\n")

    except KeyboardInterrupt:
        print(f"\n\n[취소됨] Ctrl+C 감지 — 진행 상황 저장 중...")
        _save_scene_cache()
        try:
            PROG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(PROG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "status": "cancelled", "pct": int(completed / total * 100) if total else 0,
                    "done_word": done_word, "done_sent": done_sent,
                    "last_word_id": last_word_id,
                    "cancelled_at": datetime.now().isoformat(),
                }, f, ensure_ascii=False)
        except Exception:
            pass
        print(f"  단어 일러스트: {done_word}개 생성")
        print(f"  예문 일러스트: {done_sent}개 생성")
        print(f"  마지막 단어 ID: {last_word_id}")
        print(f"  이어서 실행: --start {last_word_id} --end {args.end}")
        return

    _save_scene_cache()

    # 완료 기록
    try:
        PROG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROG_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "status": "done", "pct": 100,
                "done_word": done_word, "done_sent": done_sent,
                "completed_at": datetime.now().isoformat(),
            }, f, ensure_ascii=False)
    except Exception:
        pass

    print(f"\n=== 완료 ===")
    print(f"  단어 일러스트: {done_word}개 생성")
    print(f"  예문 일러스트: {done_sent}개 생성")
    print(f"  실패: {fail}개")
    print(f"  총 비용: ${(done_word+done_sent)*unit_cost:.2f}")


if __name__ == "__main__":
    main()
