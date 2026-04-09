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
PHRASES_DB_PATH = Path("Z:/Hellowords/data/Conversation/phrases_db.json")
PROGRESS_FILE   = _SCRIPT_DIR / "logs" / "phrase_illust_progress.json"

# ─── 캐릭터 풀 ───────────────────────────────────────────────
# 상황 ID에 따라 다른 동물 조합 사용
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

# 주인공(학습자)은 래서 팬더로 고정 — 상황에 따라 옷만 변경
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

def _pick_characters(sit_id: int) -> tuple[str, str]:
    """상황 ID 기반으로 동물 캐릭터 쌍 선택 (결정론적)"""
    local   = _LOCAL_ANIMALS[sit_id % len(_LOCAL_ANIMALS)]
    outfit  = _LEARNER_OUTFITS[sit_id % len(_LEARNER_OUTFITS)]
    learner = f"red panda wearing {outfit}"
    return local, learner


# ─── 웹툰 스타일 상수 ─────────────────────────────────────────
_WEBTOON_STYLE_BASE = (
    # 아트 스타일
    "warm watercolor and pencil sketch illustration style, "
    "soft loose brushwork with visible watercolor paper texture, "
    "gentle pencil outlines (not thick black ink), "
    "watercolor wash backgrounds that are slightly soft and misty, "

    # 색상 팔레트
    "warm peach and cream sky, muted earth tones, "
    "soft golden hour lighting throughout the scene, "
    "pastel palette: warm peach, dusty rose, sage green, muted yellow, soft blue-gray, "
    "NO neon colors, NO dark or black-dominant areas, "

    # 캐릭터 비율 (엄격히 고정)
    "cute chibi anthropomorphic animal characters, "
    "STRICT PROPORTION RULES: "
    "head-to-body ratio 1:1.2 — head is nearly as tall as the body, very large round head, "
    "body is short and chubby, legs are extremely short and stubby (almost no visible legs), "
    "arms are short and rounded, "
    "total character height = 35 to 40 percent of the full frame height, "
    "both characters same height, positioned side by side in lower third of frame, "
    "full character visible from top of head to bottom of feet, "
    "characters have slightly more detail/contrast than the soft background, "
    "NO shoes NO boots NO sandals NO footwear — all characters have bare paws, "

    # 배경
    "Korean location background is soft and slightly faded behind the characters, "
    "depth: characters sharp in foreground, background gently blurred/misty, "
    "warm atmospheric haze giving a cozy golden hour feel, "

    # 구도 및 제약
    "square 1:1 composition, "
    "upper 35% of image is open sky or soft gradient — keep it uncluttered, "

    # 텍스트 완전 금지 — 심볼/아이콘으로 대체
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

def _webtoon_style(sit_id: int) -> str:
    local, learner = _pick_characters(sit_id)
    return (
        f"TWO animal characters in frame: "
        f"LEFT={local} (Korean local role), "
        f"RIGHT={learner} (learner role), "
        + _WEBTOON_STYLE_BASE
    )

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


def _apply_style(content: str, sit_id: int = 0) -> str:
    """장면 설명 + lint + 웹툰 스타일"""
    return f"{_lint_prompt(content)}. {_webtoon_style(sit_id)}"


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
    _save_progress(progress)


def _mark_failed(progress: dict, sit_id: int, key: str, reason: str):
    sit_key = str(sit_id)
    if sit_key not in progress["failed"]:
        progress["failed"][sit_key] = {}
    progress["failed"][sit_key][key] = reason
    _save_progress(progress)


# ─── Claude API 장면 설명 생성 ───────────────────────────────
def _build_intro_scene(situation: dict, anthropic_client) -> str:
    """상황 인트로 패널 장면 설명 생성 (설정 샷)"""
    sit_id  = situation.get("id", 0)
    sit_ko  = situation.get("situation", "")
    sit_en  = situation.get("situation_en", "")
    cat     = situation.get("category", "")
    local_char, learner_char = _pick_characters(sit_id)

    # DB에 미리 생성된 scene_prompt 우선 사용
    if situation.get("scene_prompt"):
        return situation["scene_prompt"]

    if anthropic_client is None:
        return (
            f"A soft minimalist Korean {sit_en.lower()} setting with warm cozy atmosphere. "
            f"A {local_char} stands on the left, "
            f"and a {learner_char} stands on the right, "
            f"both with cute chibi proportions and friendly expressions, ready to interact."
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
                    f"LEFT character: {local_char} (Korean local role)\n"
                    f"RIGHT character: {learner_char} (learner role)\n\n"
                    "RULES:\n"
                    "1. Describe the PHYSICAL SETTING — a soft minimalist Korean location matching the situation\n"
                    "2. Describe the two specific animal characters above standing in the scene, "
                    "body language suggesting the upcoming conversation\n"
                    "3. NO text, signs, labels, speech bubbles anywhere\n"
                    "4. Focus on cozy warm atmosphere\n\n"
                    "Output: 2 sentences ONLY. No preamble, no explanation."
                ),
            }],
        )
        return message.content[0].text.strip()
    except Exception as e:
        print(f"  [Claude 인트로 장면 실패: {e}] fallback 사용")
        return (
            f"A cozy soft Korean {sit_en.lower()} background with warm muted colors. "
            f"A cute {local_char} stands on the left, "
            f"and a cute {learner_char} stands on the right, "
            f"both with round chibi faces, button eyes, tiny noses, ready to begin their interaction."
        )


def _build_phrase_scene(situation: dict, phrase: dict, anthropic_client) -> str:
    """대화 쌍별 패널 장면 설명 생성"""
    sit_id      = situation.get("id", 0)
    sit_ko      = situation.get("situation", "")
    sit_en      = situation.get("situation_en", "")
    my_ko       = phrase["my_line"]["ko"]
    my_en       = phrase["my_line"]["en"]
    resp_ko     = phrase["response"]["ko"]
    resp_en     = phrase["response"]["en"]
    tip         = phrase.get("tip", "")
    local_char, learner_char = _pick_characters(sit_id)

    # DB에 미리 생성된 scene_prompt가 있으면 배경으로 사용 + 동작 설명 추가
    base_scene = situation.get("scene_prompt", "")

    if anthropic_client is None:
        action = (
            f"The {learner_char} on the right gestures expressively while saying '{my_en}', "
            f"and the {local_char} on the left responds warmly."
        )
        return f"{base_scene} {action}".strip() if base_scene else (
            f"Inside a cozy Korean {sit_en.lower()}, a cute {learner_char} on the right "
            f"is speaking with an expressive gesture matching '{my_en}'. "
            f"A {local_char} on the left responds warmly, "
            f"both cute animal characters visible from head to waist with chibi proportions."
        )

    try:
        setting_hint = (
            f"Background setting (already established): {base_scene}\n" if base_scene
            else f"Setting: soft minimalist Korean {sit_en.lower()}\n"
        )
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=150,
            messages=[{
                "role": "user",
                "content": (
                    "You are an illustration director for a Korean language learning app.\n"
                    "Write ONE sentence describing the characters' actions/emotions for this dialogue panel.\n\n"
                    f"{setting_hint}"
                    f"RIGHT character: {learner_char} (learner, says: '{my_en}')\n"
                    f"LEFT character: {local_char} (Korean local, responds: '{resp_en}')\n"
                    + (f"Tip: {tip}\n" if tip else "") +
                    "\nDescribe ONLY the characters' cute gesture/expression — not the setting.\n"
                    "Output: 1 sentence ONLY. No preamble."
                ),
            }],
        )
        action = message.content[0].text.strip()
        return f"{base_scene} {action}".strip() if base_scene else action
    except Exception as e:
        print(f"  [Claude 대화 장면 실패: {e}] fallback 사용")
        action = (
            f"The {learner_char} on the right makes an expressive cute gesture, "
            f"and the {local_char} on the left responds with a warm friendly smile."
        )
        return f"{base_scene} {action}".strip() if base_scene else (
            f"Inside a soft cozy Korean {sit_en.lower()}, two cute animal characters interact. "
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
    "여행":       "travel outfit: light jacket, crossbody bag",
    "식사":       "casual everyday clothes, slightly hungry expression",
    "쇼핑":       "casual outfit with a tote shopping bag over shoulder",
    "의료":       "casual clothes, small bandage or looking slightly unwell",
    "인사":       "neat smart-casual outfit, warm friendly smile",
    "일상":       "everyday casual wear, relaxed posture",
    "주거":       "home casual wear, cozy sweater",
    "여가":       "relaxed leisure outfit matching the activity",
    "비즈니스":   "business casual — collared shirt, neat trousers",
    "K-Culture":  "trendy Korean street fashion, stylish casual",
}
_DEFAULT_OUTFIT = "casual everyday outfit appropriate to the situation"


def _get_main_char_outfit(situation: dict) -> str:
    cat = situation.get("category", "")
    sit_en = situation.get("situation_en", "").lower()
    # 세부 상황별 오버라이드
    overrides = {
        "hospital": "patient-casual clothes, slightly worried expression",
        "emergency": "casual clothes, clearly in distress",
        "gym":       "sporty tracksuit",
        "beach":     "summer casual, sunhat",
        "ktx":       "travel outfit with luggage",
        "airport":   "travel outfit with carry-on bag and passport in hand",
        "interview": "neat business formal suit",
        "karaoke":   "fun casual outfit, holding a mic",
        "bbq":       "casual clothes, bib or apron",
        "sauna":     "light towel wrap or casual lounge wear",
    }
    for keyword, outfit in overrides.items():
        if keyword in sit_en:
            return outfit
    return _CATEGORY_OUTFITS.get(cat, _DEFAULT_OUTFIT)


def _build_char_instruction(situation: dict) -> str:
    outfit = _get_main_char_outfit(situation)
    return (
        "CHARACTER REFERENCE IMAGES ARE PROVIDED ABOVE.\n"
        f"RIGHT character (protagonist/learner): the RED PANDA from the first reference image. "
        f"Draw it with IDENTICAL design — same orange-red fur, dark brown body, striped ringed tail, "
        f"white facial markings, round dark eyes. "
        f"Outfit for this situation: {outfit}. "
        f"Proportions: very large round head (head ≈ body height), short chubby body, "
        f"extremely short stubby legs, short rounded arms. Bare paws, no footwear.\n"
        "LEFT character (Korean local): design a NEW cute chibi animal character "
        "in the SAME warm watercolor style as the reference sheets — "
        "choose any animal species that fits the role naturally. "
        "SAME proportions: giant round head, tiny stubby legs, chubby body. "
        "Bare paws, no footwear.\n\n"
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
                    sit_id: int = 0, situation: dict | None = None) -> bool:
    """Gemini Flash Image로 단일 이미지 생성 (캐릭터 레퍼런스 포함)"""
    if output_path.exists() and output_path.stat().st_size > 0:
        return True
    elif output_path.exists():
        output_path.unlink()

    char_instruction = _build_char_instruction(situation or {})
    full_prompt = char_instruction + _apply_style(_lint_prompt(prompt), sit_id)

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

    # 1. 인트로 (설정 샷)
    intro_path = sit_dir / "intro.png"
    intro_key  = "intro"
    if not (intro_path.exists() and intro_path.stat().st_size > 0):
        print(f"  [인트로] {sit_ko} ({sit_en})")
        scene = _build_intro_scene(situation, anthropic_client)
        print(f"    장면: {scene[:80]}...")
        if _generate_image(scene, intro_path, genai_client, sit_id, situation):
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

    # 2. 대화 쌍별 패널
    for phrase in phrases:
        ph_id   = phrase["id"]
        ph_key  = f"phrase_{ph_id}"
        ph_path = sit_dir / f"phrase_{ph_id}.png"

        if ph_path.exists() and ph_path.stat().st_size > 0:
            print(f"  [스킵] phrase_{ph_id}.png (이미 존재)")
            done += 1
            continue

        my_en = phrase["my_line"]["en"]
        print(f"  [phrase_{ph_id}] '{my_en[:50]}'")
        scene = _build_phrase_scene(situation, phrase, anthropic_client)
        print(f"    장면: {scene[:80]}...")
        if _generate_image(scene, ph_path, genai_client, sit_id, situation):
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
