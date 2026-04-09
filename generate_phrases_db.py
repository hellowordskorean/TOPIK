#!/usr/bin/env python3
"""
generate_phrases_db.py
100개 상황별 한국어 기초회화 DB 생성 + 자동 검증/수정 루프

Usage:
  python generate_phrases_db.py                      # 전체 생성
  python generate_phrases_db.py --start 1 --end 10   # 1~10번 상황만
  python generate_phrases_db.py --verify             # 검증만 (생성 없이)
  python generate_phrases_db.py --verify --fix       # 검증 + 자동수정
  python generate_phrases_db.py --loop               # 100% 통과할 때까지 반복
"""

import json
import time
import argparse
import os
from pathlib import Path
import anthropic

# .env 파일에서 API 키 로드 (docker 외부 실행 시)
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

client = anthropic.Anthropic()

OUTPUT_FILE = Path(r"Z:\Hellowords\data\Conversation\phrases_db.json")

# ─────────────────────────────────────────────
# 100개 상황 정의
# ─────────────────────────────────────────────
SITUATIONS = [
    # ── 여행/교통 (1~20) ──────────────────────
    {"id":  1, "category": "여행", "situation": "공항 — 입국심사",       "situation_en": "Airport — Immigration"},
    {"id":  2, "category": "여행", "situation": "공항 — 수하물/출국",     "situation_en": "Airport — Baggage / Departure"},
    {"id":  3, "category": "여행", "situation": "공항 — 환승/연결편",     "situation_en": "Airport — Transit / Connecting Flight"},
    {"id":  4, "category": "여행", "situation": "환전/ATM",              "situation_en": "Currency Exchange / ATM"},
    {"id":  5, "category": "여행", "situation": "택시 타기",             "situation_en": "Taking a Taxi"},
    {"id":  6, "category": "여행", "situation": "지하철",                "situation_en": "Subway"},
    {"id":  7, "category": "여행", "situation": "버스",                  "situation_en": "Bus"},
    {"id":  8, "category": "여행", "situation": "KTX/기차",             "situation_en": "KTX / Train"},
    {"id":  9, "category": "여행", "situation": "렌터카",                "situation_en": "Car Rental"},
    {"id": 10, "category": "여행", "situation": "길 묻기",               "situation_en": "Asking for Directions"},
    {"id": 11, "category": "여행", "situation": "호텔 — 체크인",          "situation_en": "Hotel — Check-in"},
    {"id": 12, "category": "여행", "situation": "호텔 — 체크아웃",        "situation_en": "Hotel — Check-out"},
    {"id": 13, "category": "여행", "situation": "호텔 — 서비스 요청",     "situation_en": "Hotel — Service Request"},
    {"id": 14, "category": "여행", "situation": "숙소 예약 (전화/온라인)","situation_en": "Accommodation Booking"},
    {"id": 15, "category": "여행", "situation": "관광지 입장",            "situation_en": "Entering a Tourist Attraction"},
    {"id": 16, "category": "여행", "situation": "여행사/투어 신청",        "situation_en": "Travel Agency / Tour Booking"},
    {"id": 17, "category": "여행", "situation": "짐 보관/분실",           "situation_en": "Luggage Storage / Lost Item"},
    {"id": 18, "category": "여행", "situation": "관광 안내소",            "situation_en": "Tourist Information Center"},
    {"id": 19, "category": "여행", "situation": "기념품 쇼핑",            "situation_en": "Souvenir Shopping"},
    {"id": 20, "category": "여행", "situation": "면세점",                "situation_en": "Duty-free Shop"},

    # ── 식사/음식 (21~35) ─────────────────────
    {"id": 21, "category": "식사", "situation": "식당 — 예약",           "situation_en": "Restaurant — Reservation"},
    {"id": 22, "category": "식사", "situation": "식당 — 자리/주문",       "situation_en": "Restaurant — Seating / Ordering"},
    {"id": 23, "category": "식사", "situation": "식당 — 음식 추천 요청",  "situation_en": "Restaurant — Asking for Recommendations"},
    {"id": 24, "category": "식사", "situation": "식당 — 계산/영수증",     "situation_en": "Restaurant — Paying the Bill"},
    {"id": 25, "category": "식사", "situation": "식이 제한 (채식/알레르기)","situation_en": "Dietary Restrictions (Vegetarian / Allergy)"},
    {"id": 26, "category": "식사", "situation": "카페 주문",              "situation_en": "Cafe Order"},
    {"id": 27, "category": "식사", "situation": "편의점",                "situation_en": "Convenience Store"},
    {"id": 28, "category": "식사", "situation": "패스트푸드",             "situation_en": "Fast Food"},
    {"id": 29, "category": "식사", "situation": "배달 음식",              "situation_en": "Food Delivery"},
    {"id": 30, "category": "식사", "situation": "시장/길거리 음식",        "situation_en": "Market / Street Food"},
    {"id": 31, "category": "식사", "situation": "고깃집",                "situation_en": "Korean BBQ Restaurant"},
    {"id": 32, "category": "식사", "situation": "분식집 (떡볶이/순대)",    "situation_en": "Snack Bar (Tteokbokki / Sundae)"},
    {"id": 33, "category": "식사", "situation": "술집/맥주집",            "situation_en": "Bar / Beer Pub"},
    {"id": 34, "category": "식사", "situation": "노점/포장마차",           "situation_en": "Food Stall / Pojangmacha"},
    {"id": 35, "category": "식사", "situation": "뷔페",                  "situation_en": "Buffet"},

    # ── 쇼핑 (36~45) ─────────────────────────
    {"id": 36, "category": "쇼핑", "situation": "옷 가게 — 사이즈/피팅",  "situation_en": "Clothing Store — Size / Fitting"},
    {"id": 37, "category": "쇼핑", "situation": "옷 가게 — 교환/환불",    "situation_en": "Clothing Store — Exchange / Refund"},
    {"id": 38, "category": "쇼핑", "situation": "전자제품 매장",           "situation_en": "Electronics Store"},
    {"id": 39, "category": "쇼핑", "situation": "K-뷰티/화장품 매장",     "situation_en": "K-Beauty / Cosmetics Store"},
    {"id": 40, "category": "쇼핑", "situation": "마트/슈퍼마켓",          "situation_en": "Supermarket"},
    {"id": 41, "category": "쇼핑", "situation": "약국",                  "situation_en": "Pharmacy"},
    {"id": 42, "category": "쇼핑", "situation": "서점",                  "situation_en": "Bookstore"},
    {"id": 43, "category": "쇼핑", "situation": "할인/가격 문의",         "situation_en": "Discount / Price Inquiry"},
    {"id": 44, "category": "쇼핑", "situation": "포장/선물 요청",         "situation_en": "Gift Wrapping Request"},
    {"id": 45, "category": "쇼핑", "situation": "온라인 주문 픽업/반품",   "situation_en": "Online Order Pickup / Return"},

    # ── 의료/건강 (46~53) ─────────────────────
    {"id": 46, "category": "의료", "situation": "병원 — 예약/접수",       "situation_en": "Hospital — Appointment / Registration"},
    {"id": 47, "category": "의료", "situation": "병원 — 증상 설명",        "situation_en": "Hospital — Describing Symptoms"},
    {"id": 48, "category": "의료", "situation": "응급실",                 "situation_en": "Emergency Room"},
    {"id": 49, "category": "의료", "situation": "약국 — 약 구입/복용법",   "situation_en": "Pharmacy — Buying Medicine / Dosage"},
    {"id": 50, "category": "의료", "situation": "치과",                  "situation_en": "Dentist"},
    {"id": 51, "category": "의료", "situation": "피부과",                "situation_en": "Dermatologist"},
    {"id": 52, "category": "의료", "situation": "한의원",                "situation_en": "Korean Medicine Clinic"},
    {"id": 53, "category": "의료", "situation": "보험/진단서 요청",        "situation_en": "Insurance / Medical Certificate Request"},

    # ── 인사/기초 표현 (54~63) ───────────────
    {"id": 54, "category": "인사", "situation": "첫 만남/인사",           "situation_en": "First Meeting / Greetings"},
    {"id": 55, "category": "인사", "situation": "자기소개 — 이름/나라",    "situation_en": "Self-intro — Name / Country"},
    {"id": 56, "category": "인사", "situation": "자기소개 — 직업/학교",    "situation_en": "Self-intro — Job / School"},
    {"id": 57, "category": "인사", "situation": "가족 소개",              "situation_en": "Family Introduction"},
    {"id": 58, "category": "인사", "situation": "날씨 이야기",            "situation_en": "Talking about the Weather"},
    {"id": 59, "category": "인사", "situation": "시간/날짜 묻기",          "situation_en": "Asking the Time / Date"},
    {"id": 60, "category": "인사", "situation": "숫자/가격 이해",          "situation_en": "Understanding Numbers / Prices"},
    {"id": 61, "category": "인사", "situation": "감사/사과 표현",          "situation_en": "Expressing Thanks / Apology"},
    {"id": 62, "category": "인사", "situation": "못 알아들을 때",          "situation_en": "When You Don't Understand"},
    {"id": 63, "category": "인사", "situation": "작별 인사",              "situation_en": "Farewell / Goodbye"},

    # ── 일상생활 (64~75) ─────────────────────
    {"id": 64, "category": "일상", "situation": "전화 통화",              "situation_en": "Phone Call"},
    {"id": 65, "category": "일상", "situation": "카카오톡/문자",           "situation_en": "KakaoTalk / Text Message"},
    {"id": 66, "category": "일상", "situation": "은행/ATM/송금",          "situation_en": "Bank / ATM / Transfer"},
    {"id": 67, "category": "일상", "situation": "우체국/택배",             "situation_en": "Post Office / Parcel Delivery"},
    {"id": 68, "category": "일상", "situation": "미용실/이발소",           "situation_en": "Hair Salon / Barbershop"},
    {"id": 69, "category": "일상", "situation": "세탁소",                 "situation_en": "Laundry / Dry Cleaner"},
    {"id": 70, "category": "일상", "situation": "주유소",                 "situation_en": "Gas Station"},
    {"id": 71, "category": "일상", "situation": "와이파이/인터넷",          "situation_en": "WiFi / Internet"},
    {"id": 72, "category": "일상", "situation": "분실물 신고",             "situation_en": "Reporting a Lost Item"},
    {"id": 73, "category": "일상", "situation": "경찰서",                 "situation_en": "Police Station"},
    {"id": 74, "category": "일상", "situation": "사진 촬영 부탁",          "situation_en": "Asking Someone to Take a Photo"},
    {"id": 75, "category": "일상", "situation": "날씨/예보 대화",          "situation_en": "Weather Forecast Chat"},

    # ── 주거/생활 (76~82) ─────────────────────
    {"id": 76, "category": "주거", "situation": "부동산 — 집 구하기",      "situation_en": "Real Estate — Finding a Place"},
    {"id": 77, "category": "주거", "situation": "아파트 관리실",           "situation_en": "Apartment Management Office"},
    {"id": 78, "category": "주거", "situation": "전기/가스/수도 신고",      "situation_en": "Utilities — Reporting an Issue"},
    {"id": 79, "category": "주거", "situation": "이웃과 대화",             "situation_en": "Talking with a Neighbor"},
    {"id": 80, "category": "주거", "situation": "택배 받기/보내기",         "situation_en": "Receiving / Sending a Package"},
    {"id": 81, "category": "주거", "situation": "수리/AS 요청",            "situation_en": "Requesting Repair / After-service"},
    {"id": 82, "category": "주거", "situation": "이사",                   "situation_en": "Moving House"},

    # ── 사교/여가 (83~92) ─────────────────────
    {"id": 83, "category": "여가", "situation": "약속 잡기",              "situation_en": "Making Plans / Appointments"},
    {"id": 84, "category": "여가", "situation": "취미 이야기",            "situation_en": "Talking about Hobbies"},
    {"id": 85, "category": "여가", "situation": "스포츠/운동 (헬스장/수영장)","situation_en": "Sports / Gym / Swimming Pool"},
    {"id": 86, "category": "여가", "situation": "영화관",                 "situation_en": "Movie Theater"},
    {"id": 87, "category": "여가", "situation": "노래방",                 "situation_en": "Karaoke (Norebang)"},
    {"id": 88, "category": "여가", "situation": "찜질방/사우나",           "situation_en": "Jjimjilbang / Sauna"},
    {"id": 89, "category": "여가", "situation": "PC방",                  "situation_en": "PC Cafe (PC Bang)"},
    {"id": 90, "category": "여가", "situation": "술자리/건배 문화",         "situation_en": "Drinking Culture / Toast"},
    {"id": 91, "category": "여가", "situation": "선물 주고받기",           "situation_en": "Giving and Receiving Gifts"},
    {"id": 92, "category": "여가", "situation": "파티/모임",              "situation_en": "Party / Gathering"},

    # ── 직장/비즈니스 (93~96) ─────────────────
    {"id": 93, "category": "비즈니스", "situation": "비즈니스 인사/명함",  "situation_en": "Business Greeting / Business Card"},
    {"id": 94, "category": "비즈니스", "situation": "회의/발표",           "situation_en": "Meeting / Presentation"},
    {"id": 95, "category": "비즈니스", "situation": "출장/업무 식사",       "situation_en": "Business Trip / Business Meal"},
    {"id": 96, "category": "비즈니스", "situation": "면접",               "situation_en": "Job Interview"},

    # ── K-Culture 특화 (97~100) ──────────────
    {"id":  97, "category": "K-Culture", "situation": "K-팝 팬미팅/콘서트", "situation_en": "K-pop Fan Meeting / Concert"},
    {"id":  98, "category": "K-Culture", "situation": "K-드라마 속 표현",   "situation_en": "K-drama Expressions"},
    {"id":  99, "category": "K-Culture", "situation": "전통시장/한복 체험",  "situation_en": "Traditional Market / Hanbok Experience"},
    {"id": 100, "category": "K-Culture", "situation": "한국 예절/호칭",     "situation_en": "Korean Etiquette / Honorific Titles"},
]

# ─────────────────────────────────────────────
# 생성 프롬프트
# ─────────────────────────────────────────────
GENERATE_SYSTEM = """You are a professional Korean language teacher creating a practical conversational Korean phrasebook.

For each situation, generate exactly 10 dialogue pairs that a foreigner in Korea would actually use.

STRICT RULES:
- Korean must be natural, spoken Korean (not textbook formal)
- Use 요-form (polite informal) as default — the most practical register
- my_line: what the foreign learner says
- response: a realistic reply a Korean person would give
- romanization: accurate Revised Romanization (not McCune-Reischauer)
- English: natural, idiomatic translation (not word-for-word)
- tip: one practical note — polite variant, cultural context, or common mistake to avoid (in English)
- Avoid duplicate phrases across the 10 items
- Phrases must be SHORT and usable — max 2 sentences per line
- No overly formal or literary Korean

Respond ONLY with valid JSON:
{
  "phrases": [
    {
      "id": 1,
      "my_line": {
        "ko": "Korean phrase (what I say)",
        "romanization": "romanization",
        "en": "English translation"
      },
      "response": {
        "ko": "Korean reply (what they say)",
        "romanization": "romanization",
        "en": "English translation"
      },
      "tip": "Practical tip in English"
    }
  ]
}"""


# ─────────────────────────────────────────────
# YouTube 메타데이터 프롬프트
# ─────────────────────────────────────────────
YOUTUBE_META_SYSTEM = """You are a YouTube SEO expert and Korean language content creator.
Generate click-worthy YouTube Shorts titles and descriptions for a Korean conversation lesson video.

Target audience: English speakers who want to learn Korean for travel or daily life.
Style: Hooky, urgent, benefit-driven. Like "10-minute Korean" or "Speak Korean TODAY" style.

Rules for title (pick the best ONE from 3 options):
- Under 60 characters
- Include a number (e.g. "10 phrases", "5분 완성")
- Mix Korean + English for international appeal
- Use power words: "완성", "필수", "바로 쓰는", "원어민처럼", "당황하지 마세요", "꼭 알아야 할"
- Optionally add 1 relevant emoji at the end

Rules for description:
- Line 1: Hook sentence (problem/fear the viewer has)
- Line 2: Promise (what they'll be able to do after watching)
- Line 3-12: List the 10 Korean phrases with English (취약 포인트 강조)
- Last 3 lines: CTA + hashtags

Hashtags must include: #한국어 #LearnKorean #KoreanPhrase + 3 situation-specific tags

Respond ONLY with valid JSON:
{
  "title": "Best title (under 60 chars)",
  "title_alternatives": ["Alt title 1", "Alt title 2"],
  "description": "Full YouTube description (use \\n for line breaks)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10"],
  "hashtags": "#한국어 #LearnKorean #KoreanPhrase #tag4 #tag5 #tag6"
}"""


# ─────────────────────────────────────────────
# 검증 프롬프트
# ─────────────────────────────────────────────
VALIDATE_SYSTEM = """You are a native Korean language expert reviewing a conversational Korean phrasebook for accuracy and practicality.

Evaluate each dialogue pair on these 4 criteria (each scored 1-5):
1. natural  — Does it sound like real spoken Korean? (not textbook stiff)
2. practical — Would people actually say this in the real situation?
3. clear    — Is the meaning unambiguous? Could it be misunderstood?
4. accurate — Is the romanization correct? Is the English translation accurate?

Flag any pair scoring below 4 on ANY criterion.

Respond ONLY with valid JSON:
{
  "results": [
    {
      "id": 1,
      "natural": 5,
      "practical": 5,
      "clear": 5,
      "accurate": 5,
      "pass": true,
      "issue": null
    },
    {
      "id": 2,
      "natural": 2,
      "practical": 3,
      "clear": 4,
      "accurate": 5,
      "pass": false,
      "issue": "너무 격식체. 실제로는 '주세요' 대신 '줘요' 사용"
    }
  ]
}"""


# ─────────────────────────────────────────────
# 씬 프롬프트 (이미지 생성용)
# ─────────────────────────────────────────────
SCENE_PROMPT_SYSTEM = """You are an art director creating image generation prompts for a Korean language learning app.

Illustration style: warm watercolor and pencil sketch, soft loose brushwork, visible watercolor paper texture,
warm peach/cream sky with golden hour lighting, muted earth tones, pastel palette,
cute chibi anthropomorphic animal characters with rounded chubby proportions,
Korean location background soft and slightly faded/misty behind characters,
upper 35% of image is open sky — uncluttered, NO text NO signs NO letters anywhere.

For each Korean conversation situation, write ONE scene prompt describing the BACKGROUND SETTING only.
This prompt is reused across all dialogue panels — describe location and atmosphere ONLY, NOT character actions.

Rules:
- Describe the exact Korean location with vivid sensory detail (warm lighting, specific objects, atmosphere, time of day)
- Mention TWO animal characters standing in the scene but do NOT describe their actions or expressions
- LEFT character = {local_char} (Korean local role), RIGHT character = {learner_char} (learner role)
- STRICT NO TEXT: zero letters, zero words, zero numbers in any language anywhere in the scene
- Replace ALL text-bearing elements with visual symbols/icons:
  pharmacy→red cross symbol, hair salon→scissors icon, restaurant→fork-and-spoon icon,
  cafe→coffee cup icon, menu board→illustrated food picture display,
  bus→colored stripe pattern on front, phone screen→simple geometric icon UI,
  storefront signs→pictogram icons only, price tags→coin stack icon
- EXCEPTION: "TAXI" yellow rooftop sign is allowed as an international symbol
- Keep under 80 words
- Output ONLY the prompt text, no preamble"""
FIX_SYSTEM = """You are a native Korean language expert fixing a flawed conversational Korean phrasebook entry.

Replace the flawed dialogue pair with a corrected version that fixes the identified issue.
Keep the same general intent and situation context.

Rules:
- Natural spoken Korean (요-form polite informal)
- Short, usable phrases (max 2 sentences)
- Accurate Revised Romanization
- Natural English translation

Respond ONLY with valid JSON:
{
  "my_line": {
    "ko": "...",
    "romanization": "...",
    "en": "..."
  },
  "response": {
    "ko": "...",
    "romanization": "...",
    "en": "..."
  },
  "tip": "..."
}"""


# ─────────────────────────────────────────────
# Claude API 래퍼
# ─────────────────────────────────────────────
def _claude(system: str, user: str, max_tokens: int = 2000) -> str | None:
    delays = [5, 30, 60]  # 529 overload 대비 점진적 대기
    for attempt in range(3):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return resp.content[0].text.strip()
        except Exception as e:
            err = str(e)
            wait = delays[attempt]
            if "529" in err or "overloaded" in err.lower():
                print(f"    서버 과부하 (시도 {attempt+1}/3) — {wait}초 대기 후 재시도...")
            else:
                print(f"    API 오류 (시도 {attempt+1}/3): {e}")
            time.sleep(wait)
    return None


def _parse_json(text: str) -> dict | None:
    if not text:
        return None
    try:
        if text.startswith("```"):
            text = text[text.index("\n") + 1:]
            text = text[:text.rfind("```")].strip()
        return json.loads(text)
    except Exception:
        return None


# ─────────────────────────────────────────────
# 생성
# ─────────────────────────────────────────────
def generate_situation(sit: dict) -> list | None:
    user_msg = f"""Situation #{sit['id']}: {sit['situation']} ({sit['situation_en']})
Category: {sit['category']}

Generate 10 practical dialogue pairs for this situation."""

    text = _claude(GENERATE_SYSTEM, user_msg, max_tokens=3000)
    data = _parse_json(text)
    if not data:
        return None
    phrases = data.get("phrases", [])
    # id 정규화
    for i, p in enumerate(phrases):
        p["id"] = i + 1
    return phrases[:10]


def generate_youtube_meta(sit: dict, phrases: list) -> dict | None:
    """상황 + 10개 표현을 기반으로 YouTube 제목/설명 생성"""
    phrase_list = "\n".join(
        f'  {p["id"]}. {p["my_line"]["ko"]} — {p["my_line"]["en"]}'
        for p in phrases
    )
    user_msg = f"""Situation #{sit['id']}: {sit['situation']} ({sit['situation_en']})
Category: {sit['category']}

10 phrases covered in this video:
{phrase_list}

Generate a YouTube Shorts title and description for this Korean conversation lesson."""

    text = _claude(YOUTUBE_META_SYSTEM, user_msg, max_tokens=1200)
    return _parse_json(text)


# ─────────────────────────────────────────────
# 검증
# ─────────────────────────────────────────────
def validate_situation(sit: dict, phrases: list) -> list:
    """검증 결과 반환. pass=False인 항목만 반환."""
    items_text = "\n".join(
        f'  {p["id"]}. 내가: "{p["my_line"]["ko"]}" / 상대: "{p["response"]["ko"]}"'
        for p in phrases
    )
    user_msg = f"""Situation: {sit['situation']} ({sit['situation_en']})

Dialogue pairs to evaluate:
{items_text}

Score each pair on: natural, practical, clear, accurate (1-5). Flag any below 4."""

    text = _claude(VALIDATE_SYSTEM, user_msg, max_tokens=2000)
    data = _parse_json(text)
    if not data:
        return []
    return [r for r in data.get("results", []) if not r.get("pass", True)]


# ─────────────────────────────────────────────
# 수정
# ─────────────────────────────────────────────
def fix_phrase(sit: dict, phrase: dict, issue: str) -> dict | None:
    user_msg = f"""Situation: {sit['situation']} ({sit['situation_en']})

Flawed dialogue pair:
  My line:  {phrase['my_line']['ko']} → {phrase['my_line']['en']}
  Response: {phrase['response']['ko']} → {phrase['response']['en']}
  Tip: {phrase.get('tip', '')}

Issue: {issue}

Please provide a corrected version."""

    text = _claude(FIX_SYSTEM, user_msg, max_tokens=400)
    return _parse_json(text)


# ─────────────────────────────────────────────
# 씬 프롬프트 생성
# ─────────────────────────────────────────────
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

def _pick_characters(sit_id: int) -> tuple:
    local  = _LOCAL_ANIMALS[sit_id % len(_LOCAL_ANIMALS)]
    outfit = _LEARNER_OUTFITS[sit_id % len(_LEARNER_OUTFITS)]
    return local, f"red panda wearing {outfit}"


def generate_scene_prompt(sit: dict) -> str | None:
    """상황별 이미지 배경 씬 프롬프트 생성"""
    local_char, learner_char = _pick_characters(sit["id"])
    system = SCENE_PROMPT_SYSTEM.format(
        local_char=local_char,
        learner_char=learner_char,
    )
    user_msg = (
        f"Situation #{sit['id']}: {sit['situation']} ({sit['situation_en']})\n"
        f"Category: {sit['category']}\n"
        f"LEFT character: {local_char}\n"
        f"RIGHT character: {learner_char}\n\n"
        f"Write the scene prompt for this situation."
    )
    return _claude(system, user_msg, max_tokens=200)


def run_add_scene_prompts(start: int, end: int, overwrite: bool = False):
    """phrases_db.json의 각 상황에 scene_prompt 필드 추가"""
    db = load_db()
    targets = [s for s in SITUATIONS if start <= s["id"] <= end and s["id"] in db]
    need = [s for s in targets if overwrite or not db[s["id"]].get("scene_prompt")]
    print(f"씬 프롬프트 생성 대상: {len(need)}개 상황 (overwrite={overwrite})\n{'━'*50}")

    for i, sit in enumerate(need):
        print(f"[{i+1}/{len(need)}] #{sit['id']} {sit['situation']}...")
        prompt = generate_scene_prompt(sit)
        if prompt:
            db[sit["id"]]["scene_prompt"] = prompt.strip()
            print(f"  ✓ {prompt[:80]}...")
        else:
            print(f"  ✗ 실패 — 스킵")
        if (i + 1) % 10 == 0:
            save_db(db)
            print(f"  → 중간 저장 ({i+1}/{len(need)})")
        time.sleep(0.5)

    save_db(db)
    print(f"\n완료! scene_prompt 추가: {sum(1 for s in need if db[s['id']].get('scene_prompt'))}개")


# ─────────────────────────────────────────────
# DB 로드/저장
# ─────────────────────────────────────────────
def load_db() -> dict:
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            items = json.load(f)
        return {item["id"]: item for item in items}
    return {}


def save_db(db: dict):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    items = sorted(db.values(), key=lambda x: x["id"])
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────
# 메인: 생성
# ─────────────────────────────────────────────
def run_generate(start: int, end: int):
    db = load_db()
    targets = [s for s in SITUATIONS if start <= s["id"] <= end and s["id"] not in db]
    print(f"생성 대상: {len(targets)}개 상황\n{'━'*50}")

    for i, sit in enumerate(targets):
        print(f"[{i+1}/{len(targets)}] #{sit['id']} {sit['situation']} 생성 중...")
        phrases = generate_situation(sit)
        if phrases:
            print(f"  ✓ 표현 {len(phrases)}개 생성 — YouTube 메타 생성 중...")
            youtube = generate_youtube_meta(sit, phrases)
            if youtube:
                print(f"  ✓ 제목: {youtube.get('title', '(없음)')}")
            else:
                print(f"  ⚠ YouTube 메타 생성 실패 (표현은 저장)")
            db[sit["id"]] = {
                "id": sit["id"],
                "category": sit["category"],
                "situation": sit["situation"],
                "situation_en": sit["situation_en"],
                "phrases": phrases,
                "youtube": youtube or {},
            }
        else:
            print(f"  ✗ 실패 — 스킵")

        if (i + 1) % 5 == 0:
            save_db(db)
            print(f"  → 중간 저장 ({len(db)}개)")

        time.sleep(1)

    save_db(db)
    print(f"\n완료! 총 {len(db)}개 저장: {OUTPUT_FILE}")


# ─────────────────────────────────────────────
# 메인: 검증 (+ 선택적 수정)
# ─────────────────────────────────────────────
def run_verify(start: int, end: int, auto_fix: bool = False) -> int:
    """검증 실행. 실패 항목 수 반환."""
    db = load_db()
    targets = [s for s in SITUATIONS if start <= s["id"] <= end and s["id"] in db]
    print(f"검증 대상: {len(targets)}개 상황 (auto_fix={auto_fix})\n{'━'*50}")

    total_fail = 0
    total_fixed = 0

    for i, sit in enumerate(targets):
        item = db[sit["id"]]
        phrases = item["phrases"]
        print(f"[{i+1}/{len(targets)}] #{sit['id']} {sit['situation']} 검증 중...")

        failures = validate_situation(sit, phrases)

        if not failures:
            print(f"  ✓ 전부 통과")
        else:
            total_fail += len(failures)
            for fail in failures:
                pid = fail["id"] - 1  # 0-indexed
                scores = f"natural={fail['natural']} practical={fail['practical']} clear={fail['clear']} accurate={fail['accurate']}"
                issue = fail.get("issue", "")
                print(f"  ✗ #{fail['id']} [{scores}] → {issue}")

                if auto_fix and 0 <= pid < len(phrases):
                    fixed = fix_phrase(sit, phrases[pid], issue)
                    if fixed:
                        phrases[pid].update(fixed)
                        total_fixed += 1
                        print(f"    → 수정: {fixed['my_line']['ko']}")
                    else:
                        print(f"    → 수정 실패")

            if auto_fix:
                item["phrases"] = phrases
                db[sit["id"]] = item

        if (i + 1) % 10 == 0:
            if auto_fix:
                save_db(db)
            print(f"  ── 진행 {i+1}/{len(targets)} ──")

        time.sleep(0.5)

    if auto_fix:
        save_db(db)

    print(f"\n{'━'*50}")
    print(f"  검증 완료 — 실패: {total_fail}개 / 수정: {total_fixed}개")
    return total_fail


# ─────────────────────────────────────────────
# 메인: 루프 (100% 통과할 때까지 반복)
# ─────────────────────────────────────────────
def run_loop(start: int, end: int, max_rounds: int = 5):
    print(f"{'━'*50}")
    print(f"  하네스 루프 시작 — 100% 통과할 때까지 반복 (최대 {max_rounds}회)")
    print(f"{'━'*50}\n")

    for round_num in range(1, max_rounds + 1):
        print(f"\n{'═'*50}")
        print(f"  라운드 {round_num}/{max_rounds}")
        print(f"{'═'*50}\n")

        fail_count = run_verify(start, end, auto_fix=True)

        if fail_count == 0:
            print(f"\n{'★'*50}")
            print(f"  ✅ 100% 통과! ({round_num}라운드 만에 완료)")
            print(f"{'★'*50}")
            return

        print(f"\n  → {fail_count}개 항목 수정 후 재검증...")

    print(f"\n  ⚠️  {max_rounds}회 시도 후에도 일부 미통과 — 수동 확인 필요")


# ─────────────────────────────────────────────
# 진행상황 요약
# ─────────────────────────────────────────────
def print_summary():
    db = load_db()
    total = len(SITUATIONS)
    done = len(db)
    print(f"\n{'━'*50}")
    print(f"  진행상황: {done}/{total}개 완료")
    print(f"{'━'*50}")
    by_cat = {}
    for s in SITUATIONS:
        cat = s["category"]
        by_cat.setdefault(cat, {"total": 0, "done": 0})
        by_cat[cat]["total"] += 1
        if s["id"] in db:
            by_cat[cat]["done"] += 1
    for cat, counts in by_cat.items():
        bar = "█" * counts["done"] + "░" * (counts["total"] - counts["done"])
        print(f"  {cat:12s} {bar} {counts['done']}/{counts['total']}")
    print()


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="100개 상황별 한국어 기초회화 DB 생성/검증")
    parser.add_argument("--start",  type=int, default=1,    help="시작 상황 ID (기본 1)")
    parser.add_argument("--end",    type=int, default=100,  help="끝 상황 ID (기본 100)")
    parser.add_argument("--verify", action="store_true",    help="검증만 실행")
    parser.add_argument("--fix",    action="store_true",    help="검증 + 자동수정 (--verify와 함께)")
    parser.add_argument("--loop",   action="store_true",    help="100% 통과할 때까지 반복 검증/수정")
    parser.add_argument("--rounds", type=int, default=5,    help="루프 최대 반복 횟수 (기본 5)")
    parser.add_argument("--status",      action="store_true", help="진행상황 요약만 표시")
    parser.add_argument("--youtube-meta", action="store_true", dest="youtube_meta",
                        help="YouTube 제목/설명만 재생성 (표현 DB가 이미 있을 때)")
    parser.add_argument("--with-youtube", action="store_true", dest="with_youtube",
                        help="--verify --fix 와 함께 쓰면 YouTube 메타도 같이 생성")
    parser.add_argument("--add-scene-prompts", action="store_true", dest="add_scene_prompts",
                        help="각 상황에 이미지 생성용 scene_prompt 필드 추가")
    parser.add_argument("--overwrite-scenes", action="store_true", dest="overwrite_scenes",
                        help="--add-scene-prompts 시 기존 scene_prompt도 덮어쓰기")
    args = parser.parse_args()

    if args.add_scene_prompts:
        run_add_scene_prompts(args.start, args.end, overwrite=args.overwrite_scenes)
    elif args.status:
        print_summary()
    elif args.youtube_meta:
        # YouTube 메타만 재생성 (표현 DB가 이미 있을 때)
        db = load_db()
        targets = [s for s in SITUATIONS if args.start <= s["id"] <= args.end and s["id"] in db]
        print(f"YouTube 메타 재생성: {len(targets)}개 상황\n{'━'*50}")
        for i, sit in enumerate(targets):
            item = db[sit["id"]]
            print(f"[{i+1}/{len(targets)}] #{sit['id']} {sit['situation']}...")
            youtube = generate_youtube_meta(sit, item["phrases"])
            if youtube:
                item["youtube"] = youtube
                db[sit["id"]] = item
                print(f"  ✓ {youtube.get('title', '')}")
            else:
                print(f"  ✗ 실패")
            if (i + 1) % 5 == 0:
                save_db(db)
            time.sleep(0.5)
        save_db(db)
        print(f"\n완료!")
    elif args.loop:
        run_generate(args.start, args.end)   # 미생성 먼저 생성
        run_loop(args.start, args.end, max_rounds=args.rounds)
    elif args.verify:
        run_verify(args.start, args.end, auto_fix=args.fix)
        if args.with_youtube:
            db = load_db()
            targets = [s for s in SITUATIONS if args.start <= s["id"] <= args.end and s["id"] in db]
            print(f"\nYouTube 메타 생성: {len(targets)}개\n{'━'*50}")
            for i, sit in enumerate(targets):
                item = db[sit["id"]]
                if item.get("youtube"):
                    print(f"  [{i+1}] #{sit['id']} 이미 있음 — 스킵")
                    continue
                print(f"  [{i+1}] #{sit['id']} {sit['situation']}...")
                youtube = generate_youtube_meta(sit, item["phrases"])
                if youtube:
                    item["youtube"] = youtube
                    db[sit["id"]] = item
                    print(f"  ✓ {youtube.get('title', '')}")
                if (i + 1) % 5 == 0:
                    save_db(db)
                time.sleep(0.5)
            save_db(db)
            print("완료!")
    else:
        run_generate(args.start, args.end)
        print("\n생성 완료. 검증을 시작합니다...\n")
        run_loop(args.start, args.end, max_rounds=args.rounds)
