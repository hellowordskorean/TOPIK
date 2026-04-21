#!/usr/bin/env python3
"""
K-드라마 테마 인트로 일러스트 배치 생성
- Gemini 3.1 Flash Image (Nano Banana) 사용
- assets/kdrama_illustrations/sit_{id}/intro.png 에 저장
- kdrama_db.json의 scene_prompt, char_a, char_b 필드를 그대로 활용
- 기존 파일은 스킵 (resumable)

준비:
  .env 에 GEMINI_API_KEY=... 필수

실행:
  python generate_kdrama_illustrations.py              # 전체 100개
  python generate_kdrama_illustrations.py --start 1 --end 10
  python generate_kdrama_illustrations.py --theme-id 5
  python generate_kdrama_illustrations.py --status
"""
import argparse
import io
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except AttributeError:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from google import genai
from google.genai import types

_SCRIPT_DIR  = Path(__file__).parent
_APP_BASE    = os.environ.get("APP_BASE", str(_SCRIPT_DIR.parent))
OUTPUT_DIR   = _SCRIPT_DIR / "assets" / "kdrama_illustrations"
KDRAMA_DB    = Path(_APP_BASE) / "data" / "Conversation" / "kdrama_db.json"
PROGRESS_F   = _SCRIPT_DIR / "logs" / "kdrama_illust_progress.json"
IMAGE_MODEL  = "gemini-3.1-flash-image-preview"


# ─── 진행 상황 ──────────────────────────────────────────────
def _load_progress() -> dict:
    try:
        if PROGRESS_F.exists():
            with open(PROGRESS_F, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"completed": [], "failed": {}, "status": "idle", "updated_at": None}


def _save_progress(d: dict):
    try:
        PROGRESS_F.parent.mkdir(parents=True, exist_ok=True)
        d["updated_at"] = datetime.now().isoformat()
        with open(PROGRESS_F, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  [progress save failed: {e}]")


# ─── 프롬프트 ───────────────────────────────────────────────
# K-드라마 전용 스타일: 동물 NO, 인간 캐릭터, 여주 고정 + 테마별 남주 일관성
_KDRAMA_STYLE_BASE = (
    "warm soft K-drama webtoon illustration style, "
    "clean digital painting with subtle watercolor texture, "
    "gentle natural lighting, cinematic Korean drama atmosphere, "
    "pastel palette: ivory white, soft sky-blue, dusty rose, sage green, "
    "light lavender, warm peach — balanced tones, NO neon, NO oversaturated colors, "
    "NO dark or black-dominant areas, "

    # ── 캐릭터 종류: 인간만 (동물 절대 금지) ─────────────────
    "TWO REAL HUMAN CHARACTERS — ABSOLUTELY NO ANIMALS, no anthropomorphic animals, "
    "no chibi animals, no cartoon animals, no red panda, no dog, no cat, no bear, "
    "no fox, no rabbit, no any animal-like features (no animal ears, tails, snouts, fur), "
    "characters are KOREAN HUMANS with normal human anatomy, "
    "natural adult human proportions (head:body ≈ 1:7), realistic facial features, "
    "soft K-drama illustration faces (slightly stylized but clearly human), "

    # ── 모던 한국 배경 ──────────────────────────────────────
    "background reflects MODERN everyday Korean life — "
    "STRICTLY AVOID traditional hanok, tile-roof houses, paper screen doors. "
    "USE modern apartments, cafes, convenience stores, subway stations, "
    "school classrooms, offices, city parks, pedestrian streets, supermarkets, "
    "modern restaurants, rooftop terraces — fitting the scene naturally. "
    "Background is soft and slightly faded, "
    "depth: foreground subjects sharp, background gently blurred/misty, "
    "square 1:1 composition, "
    "vary shot size — close-up for emotion, medium for action, wide for atmosphere, "

    # ── 텍스트 금지 ────────────────────────────────────────
    "STRICT NO TEXT RULE: absolutely zero letters, zero words, zero numbers in any language, "
    "replace ALL signage and labels with visual symbols and icons only: "
    "pharmacy→red cross symbol, cafe→coffee cup icon, restaurant→fork-and-spoon icon, "
    "convenience store→colorful shelf display, hospital→red cross emblem"
)
# 하위 호환용 별칭 (기존 코드 호출 보존)
_STYLE_BASE = _KDRAMA_STYLE_BASE

# ── 여자 주인공 (모든 테마 공통, 절대 변하지 않음) ──────────
_FEMALE_PROTAGONIST = (
    "FEMALE PROTAGONIST (FIXED across ALL themes and ALL panels — NEVER change her): "
    "a young Korean woman in her early 20s (around age 22), "
    "shoulder-length straight black hair parted in the middle "
    "(hair ends just touching her shoulders — never shorter, never longer, never tied up), "
    "warm fair skin tone, gentle almond-shaped eyes with soft natural makeup, "
    "subtle pink lip tint, slim build around 165cm tall, "
    "small silver stud earrings, NO necklace, NO glasses, NO hat, "
    "wearing the SAME outfit in EVERY panel: a soft cream-colored knit cardigan "
    "over a pale blue blouse and a high-waisted denim midi skirt, "
    "white canvas sneakers — "
    "her face shape, hair length and style, body proportions, and outfit "
    "MUST stay COMPLETELY IDENTICAL in every single panel — same person every time"
)

# ── 남자 캐릭터 템플릿 (테마 ID 기반으로 고정 매칭) ────────
# 한 테마(id) 내에서는 항상 같은 남주, 다른 테마는 다른 남주
_MALE_TEMPLATES = [
    # 0: 따뜻한 대학생
    "MALE CHARACTER for this theme — Korean man in his early 20s, slim build "
    "around 175cm, soft slightly messy black hair swept naturally to the side, "
    "warm friendly dark eyes, gentle small smile, no facial hair, no glasses, "
    "wearing a cream cable-knit sweater over a white t-shirt, light blue jeans, "
    "white sneakers — same face, hair, outfit in EVERY panel",
    # 1: 깔끔한 직장인
    "MALE CHARACTER for this theme — Korean man in his mid-20s, slim athletic "
    "build around 180cm, neatly cut short black hair, sharp dark eyes, calm "
    "reserved expression, no facial hair, no glasses, "
    "wearing a fitted navy blazer over a light grey shirt, dark slim trousers, "
    "thin silver wristwatch — same face, hair, outfit in EVERY panel",
    # 2: 쿨한 캐주얼
    "MALE CHARACTER for this theme — Korean man in his early 20s, lean build "
    "around 178cm, slightly longer black hair parted naturally, sharp jawline, "
    "cool composed expression, no facial hair, no glasses, "
    "wearing a black leather jacket over a white turtleneck, dark jeans, "
    "black ankle boots — same face, hair, outfit in EVERY panel",
    # 3: 편안한 홈웨어 (실내 장면 적합)
    "MALE CHARACTER for this theme — Korean man in his mid-20s, average build "
    "around 176cm, soft tousled dark brown hair, warm gentle eyes, soft smile, "
    "no facial hair, no glasses, "
    "wearing an oversized beige cardigan over a white tee, grey jogger pants, "
    "house slippers — same face, hair, outfit in EVERY panel",
    # 4: 활동적 야외
    "MALE CHARACTER for this theme — Korean man in his early 20s, fit athletic "
    "build around 182cm, tousled short black hair, bright energetic eyes, easy "
    "smile, no facial hair, no glasses, "
    "wearing a hunter green hoodie over a white tee, dark joggers, "
    "white sneakers — same face, hair, outfit in EVERY panel",
    # 5: 로맨틱 신사
    "MALE CHARACTER for this theme — Korean man in his mid-20s, tall slim 183cm, "
    "neatly styled dark hair swept slightly back, deep warm eyes, soft attentive "
    "expression, no facial hair, no glasses, "
    "wearing a charcoal wool coat over a light cream sweater and dark trousers, "
    "brown leather shoes — same face, hair, outfit in EVERY panel",
    # 6: 예술적 힙스터 (안경)
    "MALE CHARACTER for this theme — Korean man in his early 20s, lean 177cm, "
    "slightly longer dark wavy hair, thoughtful eyes behind round black-framed "
    "glasses, calm reflective face, no facial hair, "
    "wearing a mustard yellow corduroy jacket over a white tee, brown trousers, "
    "white canvas shoes — same face, hair, outfit in EVERY panel",
    # 7: 고등학생 교복
    "MALE CHARACTER for this theme — Korean male high school student around 18, "
    "slim 175cm, neat short black hair, bright clear eyes, slight blush on "
    "cheeks, no facial hair, no glasses, "
    "wearing a black school blazer with crest, white shirt with red striped tie, "
    "grey trousers, white sneakers — same face, hair, outfit in EVERY panel",
]


def _male_for_theme(theme: dict) -> str:
    """테마 ID 기반 남주 템플릿 고정 선택 — 같은 테마는 항상 같은 남주."""
    tid = int(theme.get("id", 0))
    return _MALE_TEMPLATES[tid % len(_MALE_TEMPLATES)]


_MOOD_MAP = {
    "연애/고백/이별": "time of day: soft golden dusk or evening — romantic warm glow",
    "감탄/반응":      "time of day: bright daytime — expressive close-up, wide eyes",
    "드라마 클리셰":  "time of day: dramatic evening light — slightly cinematic",
    "싸움/갈등/화해": "time of day: overcast afternoon — tense but not dark, cool muted tones",
    "감정 표현":      "time of day: gentle afternoon light — soft emotional atmosphere",
    "일상 구어체":    "time of day: natural daytime — warm everyday life atmosphere",
    "직장/학교":      "time of day: bright morning or afternoon — clean indoor setting",
    "가족/관계":      "time of day: warm cozy evening — family home atmosphere",
    "속어/유행어":    "time of day: lively afternoon — modern cafe or street scene, playful mood",
}


def _build_prompt(theme: dict) -> str:
    """K-드라마 테마 인트로 프롬프트 — 인간 캐릭터, 여주 고정 + 테마별 남주."""
    cat       = theme.get("category", "")
    situation = theme.get("situation", "")
    male_char = _male_for_theme(theme)

    mood = _MOOD_MAP.get(cat, "time of day matches the scene naturally")

    header = (
        f"K-drama style scene with TWO HUMAN CHARACTERS (NOT animals): "
        f"the female protagonist and a male character.\n\n"
        f"{_FEMALE_PROTAGONIST}\n\n"
        f"{male_char}\n\n"
        f"OVERALL SCENE: \"{situation}\" (category: {cat}).\n"
        f"This is the INTRO panel — establish both characters' look clearly. "
        f"Use a balanced two-shot composition that shows both faces and outfits. "
        f"NO speech bubbles, NO text in the image.\n\n"
    )
    style = f"{_KDRAMA_STYLE_BASE} {mood}. "
    return f"{header}{style}"


# ─── 패널 카메라/구도 변주 힌트 (10개 phrase 각각 다르게) ──────
_PANEL_VIEWS = [
    "medium two-shot, slight angle, both characters visible from waist up",
    "close-up on protagonist's expressive face with supporting char visible behind",
    "over-the-shoulder shot from supporting char's POV looking at protagonist",
    "wide shot showing the full setting with both characters small in frame",
    "low angle shot looking up at the characters",
    "high angle shot looking down at the characters",
    "side profile two-shot, characters facing each other",
    "close-up on supporting char's reaction with protagonist partially visible",
    "medium shot from a corner of the room, characters in mid-action",
    "intimate close-up of both characters' upper bodies, emphasizing emotion",
]


def _build_phrase_prompt(theme: dict, phrase: dict, phrase_idx: int) -> str:
    """K-드라마 phrase 패널 프롬프트 — 인간, 같은 두 사람 일관성 유지."""
    cat       = theme.get("category", "")
    situation = theme.get("situation", "")
    male_char = _male_for_theme(theme)

    my_line = phrase.get("my_line", {}) or {}
    response = phrase.get("response", {}) or {}
    my_ko = my_line.get("ko", "")
    my_en = my_line.get("en", "")
    resp_ko = response.get("ko", "")
    resp_en = response.get("en", "")
    tip = phrase.get("tip", "")

    mood = _MOOD_MAP.get(cat, "time of day matches the scene naturally")
    view = _PANEL_VIEWS[phrase_idx % len(_PANEL_VIEWS)]

    header = (
        f"K-drama dialogue panel with TWO HUMAN CHARACTERS (NOT animals).\n\n"
        f"{_FEMALE_PROTAGONIST}\n\n"
        f"{male_char}\n\n"
        f"CONSISTENCY RULE: Both characters must have the EXACT SAME face, hair, "
        f"outfit, height, and build as the intro panel and all other panels of "
        f"this scene — do NOT change their appearance between panels. "
        f"The female protagonist's hair length, makeup, and clothes are fixed across ALL themes.\n\n"
        f"OVERALL SCENE: \"{situation}\" (category: {cat}).\n\n"
        f"THIS PANEL'S DIALOGUE:\n"
        f"  Female protagonist says (in Korean): \"{my_ko}\"\n"
        f"  English: \"{my_en}\"\n"
        f"  Male character responds (in Korean): \"{resp_ko}\"\n"
        f"  English: \"{resp_en}\"\n"
        + (f"  Context tip: {tip}\n" if tip else "")
        + f"\nCAMERA / FRAMING for this panel: {view}.\n"
        f"VARIATION RULE: Each panel shows DIFFERENT body poses, gestures, and facial "
        f"expressions matching THIS specific dialogue. "
        f"Vary arm positions, lean direction, eye contact, mouth shape, eyebrow angle. "
        f"Show the EMOTION behind the words. "
        f"DO NOT vary characters' faces, hair, or clothes — only their poses/expressions.\n"
        f"NO speech bubbles, NO text in the image.\n\n"
    )
    style = f"{_KDRAMA_STYLE_BASE} {mood}. "
    return f"{header}{style}"


def _save_image(response, out_path: Path) -> bool:
    parts = []
    try:
        parts = response.candidates[0].content.parts
    except Exception:
        try:
            parts = response.parts
        except Exception:
            return False
    for p in parts:
        try:
            if p.inline_data and p.inline_data.data:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "wb") as f:
                    f.write(p.inline_data.data)
                return True
        except Exception:
            continue
    return False


def _generate_one(client, theme: dict, out_path: Path, retries: int = 2) -> tuple[bool, str]:
    if out_path.exists() and out_path.stat().st_size > 0:
        return True, "skipped (exists)"
    prompt = _build_prompt(theme)
    return _call_image_model(client, prompt, out_path, retries)


def _generate_phrase(client, theme: dict, phrase: dict, phrase_idx: int,
                      out_path: Path, retries: int = 2) -> tuple[bool, str]:
    if out_path.exists() and out_path.stat().st_size > 0:
        return True, "skipped (exists)"
    prompt = _build_phrase_prompt(theme, phrase, phrase_idx)
    return _call_image_model(client, prompt, out_path, retries)


def _call_image_model(client, prompt: str, out_path: Path, retries: int = 2) -> tuple[bool, str]:
    last_err = ""
    for attempt in range(retries + 1):
        try:
            resp = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_modalities=[types.Modality.IMAGE],
                    image_config=types.ImageConfig(aspect_ratio="1:1"),
                ),
            )
            if _save_image(resp, out_path):
                return True, "ok"
            last_err = "empty response"
        except Exception as e:
            last_err = str(e)[:200]
        if attempt < retries:
            time.sleep(2)
    return False, last_err


def print_status(db: list):
    prog = _load_progress()
    done = set(prog.get("completed", []))
    total = len(db)
    existing = 0
    for t in db:
        p = OUTPUT_DIR / f"sit_{t['id']}" / "intro.png"
        if p.exists() and p.stat().st_size > 0:
            existing += 1
    print(f"전체: {total} / 파일 존재: {existing} / 진행 기록: {len(done)}")
    print(f"출력: {OUTPUT_DIR}")


# ─── 메인 ──────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="K-드라마 테마 인트로 일러스트 생성")
    parser.add_argument("--db", default=str(KDRAMA_DB), help="kdrama_db.json 경로")
    parser.add_argument("--start", type=int, default=None)
    parser.add_argument("--end",   type=int, default=None)
    parser.add_argument("--theme-id", type=int, default=None)
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--overwrite", action="store_true", help="기존 파일도 재생성")
    parser.add_argument("--intro-only", action="store_true", help="인트로만 생성 (phrase 스킵)")
    parser.add_argument("--phrases-only", action="store_true", help="phrase만 생성 (intro 스킵)")
    args = parser.parse_args()

    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        print("오류: GEMINI_API_KEY 환경변수가 없습니다 (.env 확인)")
        sys.exit(1)

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"오류: DB 없음 {db_path}")
        sys.exit(1)
    with open(db_path, encoding="utf-8") as f:
        db = json.load(f)
    if isinstance(db, dict):
        db = db.get("themes", [])
    print(f"DB 로드: {len(db)}개 테마")

    if args.status:
        print_status(db)
        return

    # 대상 필터
    if args.theme_id is not None:
        targets = [t for t in db if t["id"] == args.theme_id]
    elif args.start is not None or args.end is not None:
        s = args.start if args.start is not None else 1
        e = args.end   if args.end   is not None else max(x["id"] for x in db)
        targets = [x for x in db if s <= x["id"] <= e]
    else:
        targets = db

    print(f"대상: {len(targets)}개")

    client = genai.Client(api_key=key)
    prog = _load_progress()
    prog["status"] = "running"
    _save_progress(prog)

    done_cnt, fail_cnt, skip_cnt = 0, 0, 0
    try:
        for i, theme in enumerate(targets, 1):
            tid = theme["id"]
            sit = theme.get("situation", "")
            theme_dir = OUTPUT_DIR / f"sit_{tid}"
            prog["current"] = {"theme_id": tid, "situation": sit}
            _save_progress(prog)

            # ─── 인트로 ─────────────────────────────────────────
            if not args.phrases_only:
                intro_out = theme_dir / "intro.png"
                if intro_out.exists() and intro_out.stat().st_size > 0 and not args.overwrite:
                    print(f"[{i}/{len(targets)}] #{tid} {sit} intro — 스킵 (이미 있음)")
                    skip_cnt += 1
                else:
                    if intro_out.exists() and args.overwrite:
                        intro_out.unlink()
                    print(f"[{i}/{len(targets)}] #{tid} {sit} intro — 생성 중...")
                    ok, info = _generate_one(client, theme, intro_out)
                    if ok:
                        done_cnt += 1
                        print(f"  ✓ {intro_out.name}")
                    else:
                        fail_cnt += 1
                        prog["failed"][f"{tid}/intro"] = info
                        print(f"  ✗ intro 실패: {info}")

            # ─── phrase 10개 ──────────────────────────────────────
            if not args.intro_only:
                phrases = theme.get("phrases", []) or []
                for p_idx, phrase in enumerate(phrases[:10]):
                    phrase_out = theme_dir / f"phrase_{p_idx + 1}.png"
                    if phrase_out.exists() and phrase_out.stat().st_size > 0 and not args.overwrite:
                        skip_cnt += 1
                        continue
                    if phrase_out.exists() and args.overwrite:
                        phrase_out.unlink()
                    my_en = (phrase.get("my_line", {}) or {}).get("en", "")[:35]
                    print(f"  [{p_idx+1}/10] {my_en!r} — 생성 중...")
                    ok, info = _generate_phrase(client, theme, phrase, p_idx, phrase_out)
                    if ok:
                        done_cnt += 1
                        print(f"    ✓ {phrase_out.name}")
                    else:
                        fail_cnt += 1
                        prog["failed"][f"{tid}/phrase_{p_idx+1}"] = info
                        print(f"    ✗ 실패: {info}")
                    time.sleep(1)

            # 테마 완료 표시 (intro 또는 phrase 일부라도 성공했으면)
            if not args.phrases_only and not args.intro_only:
                if str(tid) not in prog["completed"]:
                    prog["completed"].append(str(tid))
            _save_progress(prog)
    finally:
        prog["status"] = "idle"
        prog["current"] = None
        _save_progress(prog)

    print(f"\n=== 완료 ===  생성 {done_cnt} / 실패 {fail_cnt} / 스킵 {skip_cnt}")
    print(f"출력 폴더: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
