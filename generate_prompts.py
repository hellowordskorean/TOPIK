#!/usr/bin/env python3
"""
illustration_prompts.json 자동 생성 + 검증 스크립트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- words_db.json 기반으로 word_prompt + 10 sentence prompts 생성
- Google Gemini API 사용
- Harness Engineering: 생성 → 검증 → 수정 반복 (100% 일치까지)

실행:
  python generate_prompts.py                        # 전체 (미완성만)
  python generate_prompts.py --start 601 --end 900  # 범위 지정
  python generate_prompts.py --verify-only           # 검증만
  python generate_prompts.py --force                 # 기존 덮어쓰기
"""

import json
import os
import sys
import time
import argparse
import traceback
from pathlib import Path
from google import genai
from google.genai import types

# ── .env 로드 ───────────────────────────────────────────────
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# ── 경로 ────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
WORDS_DB = BASE_DIR / "data" / "LanguageTest" / "words_db.json"
PROMPTS_FILE = BASE_DIR / "data" / "illustration_prompts.json"
PROGRESS_FILE = BASE_DIR / "data" / "prompt_gen_progress.json"

# ── Gemini API 설정 ─────────────────────────────────────────
GEN_MODEL = "gemini-2.5-flash"
VERIFY_MODEL = "gemini-2.5-flash"

# ── 프롬프트 생성 규칙 (시스템 프롬프트) ─────────────────────

GENERATE_SYSTEM = """You are a visual prompt designer for Korean language learning illustrations.
Your job: convert Korean words and example sentences into VISUAL SCENE DESCRIPTIONS that an AI image generator (Imagen) can render as hand-drawn watercolor illustrations.

━━━ ABSOLUTE RULES ━━━
1. Describe ONLY what can be SEEN: objects, actions, body language, facial expressions, settings, colors, positions
2. NEVER include: speech bubbles, dialogue, floating text, captions, watermarks
3. Replace any spoken/written communication with PHYSICAL ACTIONS and GESTURES
4. ABSOLUTELY NO TEXT in any form — replace ALL text with universal symbols and pictograms:
   - Shop signs → icon only (cup icon for cafe, scissors for barber, fork-and-knife for restaurant)
   - Price tags → numbers are OK, but no words
   - Books/papers → wavy lines or geometric patterns instead of words
   - Menus → colorful dot symbols or numbers instead of text
   - Clocks/calendars → numbers are OK
   - Screens → simple geometric icons only
   - Use ★ ♥ ● ▲ ♪ ☀ ✿ arrows and shapes to replace any writing
5. NO Korean, Chinese, Japanese, English, or ANY language text visible — no letters or words (numbers are allowed)
6. NO gibberish, made-up words, or letter-like shapes
6b. NEVER describe objects as having readable content — instead of "sign saying Open" write "sign with a sun icon"
7. Be SPECIFIC about: body positions, facial expressions, surroundings, relative positions of objects, colors, lighting
8. Each prompt must be SELF-EXPLANATORY — a viewer should understand the meaning without any text

━━━ WORD PROMPT RULES ━━━
- Capture the CORE VISUAL ESSENCE of the word's meaning
- For concrete nouns: describe the object with distinctive visual details (shape, color, texture, size)
- For abstract concepts: create a scene that EMBODIES the concept through visible actions/situations
- For verbs: show a person MID-ACTION performing the activity with clear body posture
- For adjectives: show objects/people clearly displaying that quality with visual contrast
- For adverbs: show a scene where the manner/frequency is visually obvious
- 1-3 sentences, 30-60 words
- Must be visually distinct from other similar concepts

━━━ SENTENCE PROMPT RULES ━━━
- Create a scene that visually tells the COMPLETE story of the sentence
- The TARGET WORD's concept must be the FOCAL POINT of the scene
- Show the SITUATION described with appropriate setting, characters, and props
- When multiple people appear in a scene, give each person DISTINCTLY DIFFERENT appearances: different hairstyles, hair colors, clothing styles, and body types — never draw identical-looking people
- Convey emotions through facial expressions and body language (smile, frown, wide eyes, slumped shoulders)
- Convey communication through gestures (pointing, nodding, showing, handing over, shaking head)
- 1-2 sentences, 25-50 words per sentence prompt
- Each of the 10 sentence prompts must be VISUALLY DISTINCT — different settings, compositions, characters, perspectives
- Avoid generic/vague descriptions — be as concrete and specific as possible

━━━ FORBIDDEN IN OUTPUT ━━━
NEVER include these phrases in prompts — they belong to the rendering pipeline, not the scene description:
- "rendered as..." / "in the style of..." / "hand-drawn" / "watercolor" / "illustration"
- "pastel color" / "ink outline" / "paper texture" / "cream background"
- Camera/rendering instructions
Your output is ONLY the visual scene content — the style is applied separately.

━━━ QUALITY CHECKLIST ━━━
Before outputting, verify each prompt:
✓ Could someone guess the word/sentence meaning from the image alone?
✓ Is the scene specific enough to illustrate THIS sentence vs. any other?
✓ Are there NO text elements (speech bubbles, captions)?
✓ Is there enough visual detail for an artist to render it?
✓ Does it contain ZERO style/rendering instructions?

━━━ OUTPUT FORMAT ━━━
Return ONLY a valid JSON object (no markdown fencing, no explanation):
{
  "word_prompt": "...",
  "sentences": ["prompt1", "prompt2", "prompt3", "prompt4", "prompt5", "prompt6", "prompt7", "prompt8", "prompt9", "prompt10"]
}"""

VERIFY_SYSTEM = """You are a strict visual prompt verifier for language learning illustrations.
Your job: read image prompts and determine if they correctly and unambiguously convey their intended meanings.

━━━ VERIFICATION CRITERIA ━━━
For WORD prompts:
- Does the visual description clearly represent the word's meaning?
- Could this be confused with a different word? (If yes → FAIL)
- Is it too generic or vague? (If yes → FAIL)

For SENTENCE prompts:
- Does the scene capture the SPECIFIC meaning of THIS sentence?
- Is the target word's concept visible as the focal point?
- Could a viewer understand the sentence's meaning from the image? (If no → FAIL)
- Is the scene distinct enough from other sentences? (If too similar → FAIL)

━━━ STRICTNESS ━━━
- A prompt that could represent MULTIPLE different meanings → FAIL
- A prompt that only captures PART of the meaning → FAIL
- A prompt with text/dialogue elements → FAIL
- A prompt too vague for an artist to render → FAIL

━━━ OUTPUT FORMAT ━━━
Return ONLY valid JSON (no markdown fencing):
{
  "word_verification": {
    "interpreted_meaning": "what this prompt depicts",
    "pass": true/false,
    "issue": "explanation" (only if fail)
  },
  "sentence_verifications": [
    {
      "index": 0,
      "interpreted_meaning": "what this scene depicts",
      "pass": true/false,
      "issue": "explanation" (only if fail)
    }
  ]
}"""

FIX_SYSTEM = """You are a visual prompt fixer for language learning illustrations.
A previous prompt failed verification. Fix it to correctly and unambiguously convey the intended meaning.

RULES:
- ONLY visible elements: actions, objects, expressions, settings, colors, positions
- NO speech bubbles, dialogue, floating text, captions
- Signs/labels in ENGLISH ONLY (if essential)
- Be SPECIFIC about positions, expressions, surroundings
- The scene must be SELF-EXPLANATORY without any text
- Fix the SPECIFIC ISSUE identified in verification

Return ONLY the fixed prompt text, nothing else. No quotes, no explanation."""


# ── 유틸리티 ────────────────────────────────────────────────

def load_words_db() -> list:
    with open(WORDS_DB, encoding="utf-8") as f:
        return json.load(f)


def load_prompts() -> dict:
    if PROMPTS_FILE.exists():
        with open(PROMPTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_prompts(prompts: dict):
    """디스크의 최신 파일을 읽고 merge 후 저장 (동시 실행 안전)"""
    if PROMPTS_FILE.exists():
        with open(PROMPTS_FILE, encoding="utf-8") as f:
            on_disk = json.load(f)
        # merge: 완성도가 높은 쪽을 유지
        for key, val in prompts.items():
            disk_val = on_disk.get(key, {})
            mem_sents = len(val.get("sentences", []))
            disk_sents = len(disk_val.get("sentences", []))
            if mem_sents >= disk_sents:
                on_disk[key] = val
        prompts.update({k: v for k, v in on_disk.items() if k not in prompts})
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"generated": [], "verified": [], "failed": []}


def save_progress(prog: dict):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(prog, f, ensure_ascii=False, indent=2)


def parse_json_response(text: str) -> dict | None:
    """Gemini 응답에서 JSON 추출"""
    text = text.strip()
    # 마크다운 펜싱 제거
    if text.startswith("```"):
        # ```json 또는 ``` 이후 줄바꿈까지 제거
        first_nl = text.index("\n")
        text = text[first_nl + 1:]
        if text.endswith("```"):
            text = text[:-3].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # JSON 블록 추출 시도
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return None


# ── Gemini API 호출 ─────────────────────────────────────────

def create_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    return genai.Client(api_key=api_key)


def gemini_generate(client, model: str, system: str, user_msg: str,
                    max_tokens: int = 4000, temperature: float = 0.7) -> str | None:
    """Gemini API 호출 래퍼 (60초 타임아웃)"""
    import signal, threading

    result_container = [None]
    error_container = [None]

    def _call():
        try:
            resp = client.models.generate_content(
                model=model,
                contents=user_msg,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                    http_options={"timeout": 60000},
                ),
            )
            result_container[0] = resp.text.strip() if resp.text else None
        except Exception as e:
            error_container[0] = e

    thread = threading.Thread(target=_call, daemon=True)
    thread.start()
    thread.join(timeout=90)  # 90초 타임아웃

    if thread.is_alive():
        print(f"    ⚠ API 타임아웃 (90초 초과)")
        return None

    if error_container[0]:
        print(f"    ⚠ Gemini API 오류: {error_container[0]}")
        return None

    return result_container[0]


# ── 생성 ────────────────────────────────────────────────────

def generate_prompts_for_word(client, word: dict) -> dict | None:
    """한 단어에 대한 word_prompt + 10 sentence prompts 생성"""
    sentences_text = "\n".join(
        f"  {i+1}. [{s['situation']}] {s['ko']} = {s['en']}"
        for i, s in enumerate(word["sentences"][:10])
    )

    user_msg = f"""Korean word: {word['word']}
Meaning: {word['meaning']}
Part of speech: {word['part_of_speech']}
Level: TOPIK {word['level']}

Example sentences (Korean = English):
{sentences_text}

Generate the word_prompt and exactly 10 sentence prompts as JSON."""

    text = gemini_generate(client, GEN_MODEL, GENERATE_SYSTEM, user_msg,
                           max_tokens=4000, temperature=0.7)
    if not text:
        return None

    result = parse_json_response(text)
    if not result:
        print(f"    ⚠ JSON 파싱 실패")
        return None

    if "word_prompt" not in result or "sentences" not in result:
        print(f"    ⚠ 필수 필드 누락")
        return None

    if len(result["sentences"]) != 10:
        print(f"    ⚠ 문장 수 불일치: {len(result['sentences'])}/10")
        return None

    return result


# ── 검증 ────────────────────────────────────────────────────

def verify_prompts(client, word: dict, prompts_entry: dict) -> dict:
    """생성된 프롬프트를 역독해하여 원래 의미와 일치하는지 검증"""
    sentences_for_verify = "\n".join(
        f"  Sentence {i}: {prompts_entry['sentences'][i]}"
        for i in range(len(prompts_entry.get("sentences", [])))
    )

    user_msg = f"""Verify these illustration prompts for the Korean word "{word['word']}" (meaning: {word['meaning']}, {word['part_of_speech']}).

=== WORD PROMPT ===
{prompts_entry['word_prompt']}

=== SENTENCE PROMPTS ===
{sentences_for_verify}

=== ORIGINAL SENTENCES (ground truth) ===
""" + "\n".join(
        f"  {i}. {s['en']}"
        for i, s in enumerate(word["sentences"][:10])
    ) + "\n\nVerify each prompt matches its intended meaning. Return JSON."

    text = gemini_generate(client, VERIFY_MODEL, VERIFY_SYSTEM, user_msg,
                           max_tokens=3000, temperature=0.2)
    if not text:
        return {"word_verification": {"pass": True}, "sentence_verifications": []}

    result = parse_json_response(text)
    if not result:
        return {"word_verification": {"pass": True}, "sentence_verifications": []}

    return result


# ── 수정 ────────────────────────────────────────────────────

def fix_prompt(client, word: dict, original_prompt: str,
               intended_meaning: str, issue: str, is_word: bool = True) -> str | None:
    """검증 실패한 프롬프트 수정"""
    prompt_type = "word illustration" if is_word else "sentence illustration"
    user_msg = f"""Fix this {prompt_type} prompt:

Korean word: {word['word']} ({word['meaning']})
Intended meaning to convey: {intended_meaning}
Current (failed) prompt: {original_prompt}
Verification issue: {issue}

Generate a corrected prompt that UNAMBIGUOUSLY conveys the intended meaning visually."""

    text = gemini_generate(client, GEN_MODEL, FIX_SYSTEM, user_msg,
                           max_tokens=300, temperature=0.5)
    if not text:
        return None

    # 따옴표 제거
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    if text.startswith("'") and text.endswith("'"):
        text = text[1:-1]
    return text.strip()


# ── 메인 파이프라인 ──────────────────────────────────────────

def needs_generation(prompts: dict, gid: int, word: dict, force: bool = False) -> bool:
    """이 단어에 대해 프롬프트 생성이 필요한지 판단"""
    key = str(gid)
    if key not in prompts:
        return True
    entry = prompts[key]
    if force:
        return True
    # sentence prompts가 10개 미만이면 생성 필요
    if len(entry.get("sentences", [])) < 10:
        return True
    return False


def process_word(client, word: dict, prompts: dict,
                 force: bool = False, max_fix_rounds: int = 3) -> bool:
    """한 단어의 프롬프트 생성 → 검증 → 수정 전체 파이프라인"""
    gid = word["id"]
    key = str(gid)

    if not needs_generation(prompts, gid, word, force):
        return True  # 이미 완성

    print(f"\n  [{gid}/1800] {word['word']} ({word['meaning']})")

    # 기존 word_prompt 보존 여부 결정
    existing = prompts.get(key, {})
    keep_word_prompt = (
        word["level"] <= 2
        and "word_prompt" in existing
        and not force
    )

    # ── 1단계: 생성 ──
    generated = None
    for attempt in range(3):
        generated = generate_prompts_for_word(client, word)
        if generated:
            break
        print(f"    재시도 {attempt + 2}/3...")
        time.sleep(2)

    if not generated:
        print(f"    ✗ 생성 실패")
        return False

    # 기존 word_prompt 보존 (Level 1-2)
    if keep_word_prompt:
        generated["word_prompt"] = existing["word_prompt"]

    # ── 2단계: 검증 (Harness Engineering) ──
    for fix_round in range(max_fix_rounds):
        verification = verify_prompts(client, word, generated)

        # word_prompt 검증
        wv = verification.get("word_verification", {})
        word_pass = wv.get("pass", True)

        # sentence 검증
        sv_list = verification.get("sentence_verifications", [])
        all_pass = word_pass
        failed_sentences = []

        for sv in sv_list:
            if not sv.get("pass", True):
                all_pass = False
                failed_sentences.append(sv)

        if all_pass:
            if fix_round > 0:
                print(f"    ✓ Round {fix_round + 1}: 전체 검증 통과")
            else:
                print(f"    ✓ 검증 통과")
            break

        # 수정 필요
        fail_count = (0 if word_pass else 1) + len(failed_sentences)
        print(f"    ⟳ Round {fix_round + 1}: {fail_count}개 실패, 수정 중...")

        # word_prompt 수정
        if not word_pass and not keep_word_prompt:
            fixed = fix_prompt(
                client, word,
                generated["word_prompt"],
                word["meaning"],
                wv.get("issue", "unclear"),
                is_word=True
            )
            if fixed:
                generated["word_prompt"] = fixed

        # sentence 수정
        for sv in failed_sentences:
            idx = sv.get("index", -1)
            if 0 <= idx < 10:
                sentence = word["sentences"][idx]
                fixed = fix_prompt(
                    client, word,
                    generated["sentences"][idx],
                    sentence["en"],
                    sv.get("issue", "unclear"),
                    is_word=False
                )
                if fixed:
                    generated["sentences"][idx] = fixed

        time.sleep(1)
    else:
        print(f"    ⚠ {max_fix_rounds}라운드 후에도 일부 미통과 (저장)")

    # 저장
    prompts[key] = generated
    return True


def verify_only_mode(client, words: list, prompts: dict, start: int, end: int):
    """검증 전용 모드: 기존 프롬프트를 검증만"""
    target = [w for w in words if start <= w["id"] <= end]
    total_pass = 0
    total_fail = 0
    failures = []

    for word in target:
        key = str(word["id"])
        entry = prompts.get(key, {})
        if "sentences" not in entry or len(entry.get("sentences", [])) < 10:
            continue

        print(f"\n  검증: [{word['id']}] {word['word']} ({word['meaning']})")
        verification = verify_prompts(client, word, entry)

        wv = verification.get("word_verification", {})
        sv_list = verification.get("sentence_verifications", [])

        passed = wv.get("pass", True)
        fail_items = []
        if not passed:
            fail_items.append(("word", wv.get("issue", "")))

        for sv in sv_list:
            if not sv.get("pass", True):
                passed = False
                fail_items.append((f"sent_{sv.get('index', '?')}", sv.get("issue", "")))

        if passed:
            total_pass += 1
            print(f"    ✓ PASS")
        else:
            total_fail += 1
            failures.append({"id": word["id"], "word": word["word"], "failures": fail_items})
            print(f"    ✗ FAIL: {len(fail_items)}개")
            for item_type, issue in fail_items:
                print(f"      - {item_type}: {issue}")

        time.sleep(0.5)

    print(f"\n{'━' * 60}")
    print(f"  검증 결과: PASS {total_pass} | FAIL {total_fail}")
    if failures:
        print(f"  실패 목록:")
        for f in failures:
            print(f"    ID {f['id']} ({f['word']}): {[x[0] for x in f['failures']]}")
    print("━" * 60)


def main():
    parser = argparse.ArgumentParser(description="프롬프트 자동 생성 + 검증")
    parser.add_argument("--start", type=int, default=1, help="시작 ID (default: 1)")
    parser.add_argument("--end", type=int, default=1800, help="종료 ID (default: 1800)")
    parser.add_argument("--force", action="store_true", help="기존 프롬프트 덮어쓰기")
    parser.add_argument("--verify-only", action="store_true", help="검증만 실행")
    parser.add_argument("--max-fix-rounds", type=int, default=3, help="최대 수정 라운드 (default: 3)")
    parser.add_argument("--batch-save", type=int, default=10, help="N개마다 저장 (default: 10)")
    parser.add_argument("--preserve-complete", action="store_true", default=True,
                        help="완성된 세트(ID 1-5) 보존 (default: True)")
    args = parser.parse_args()

    print("━" * 60)
    print("  프롬프트 자동 생성 + 검증 시스템 (Gemini)")
    print("━" * 60)

    # 데이터 로드
    words = load_words_db()
    prompts = load_prompts()

    print(f"  총 단어: {len(words)}개")
    print(f"  기존 프롬프트: {len(prompts)}개")
    complete_count = sum(
        1 for v in prompts.values()
        if "word_prompt" in v and len(v.get("sentences", [])) == 10
    )
    print(f"  완성 프롬프트: {complete_count}개")
    print(f"  처리 범위: ID {args.start} ~ {args.end}")

    # Gemini 클라이언트
    client = create_client()
    print(f"  생성 모델: {GEN_MODEL}")
    print(f"  검증 모델: {VERIFY_MODEL}")

    # 검증 전용 모드
    if args.verify_only:
        print("━" * 60)
        verify_only_mode(client, words, prompts, args.start, args.end)
        return

    # 처리 대상 필터링
    target_words = [w for w in words if args.start <= w["id"] <= args.end]

    # ID 1-5 보존
    if args.preserve_complete and not args.force:
        target_words = [w for w in target_words if w["id"] > 5]
        print(f"  ID 1-5 보존 (완성된 세트)")

    # 미완성 필터
    if not args.force:
        before = len(target_words)
        target_words = [
            w for w in target_words
            if needs_generation(prompts, w["id"], w)
        ]
        print(f"  생성 필요: {len(target_words)}개 (건너뜀: {before - len(target_words)})")

    if not target_words:
        print("\n  모든 프롬프트가 이미 완성되었습니다.")
        return

    print(f"  최대 수정 라운드: {args.max_fix_rounds}")
    print("━" * 60)

    # 처리
    success = 0
    fail = 0
    progress = load_progress()
    start_time = time.time()

    for i, word in enumerate(target_words):
        try:
            ok = process_word(client, word, prompts, args.force, args.max_fix_rounds)
            if ok:
                success += 1
                if word["id"] not in progress["generated"]:
                    progress["generated"].append(word["id"])
            else:
                fail += 1
                if word["id"] not in progress["failed"]:
                    progress["failed"].append(word["id"])

            # 주기적 저장
            if (i + 1) % args.batch_save == 0:
                save_prompts(prompts)
                save_progress(progress)
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed * 60 if elapsed > 0 else 0
                remaining = (len(target_words) - i - 1) / max(rate / 60, 0.001)
                print(f"\n  ── 진행: {i+1}/{len(target_words)} | "
                      f"성공: {success} | 실패: {fail} | "
                      f"속도: {rate:.1f}/min | 남은: {remaining/60:.1f}min ──")

            # Rate limiting
            time.sleep(0.5)

        except KeyboardInterrupt:
            print(f"\n\n  ⚠ 중단됨. 현재까지 저장...")
            save_prompts(prompts)
            save_progress(progress)
            sys.exit(0)
        except Exception as e:
            print(f"    ✗ 예외: {e}")
            traceback.print_exc()
            fail += 1

    # 최종 저장
    save_prompts(prompts)
    save_progress(progress)

    elapsed = time.time() - start_time
    print("\n" + "━" * 60)
    print(f"  완료!")
    print(f"  성공: {success} | 실패: {fail}")
    print(f"  소요 시간: {elapsed/60:.1f}분")
    print(f"  저장: {PROMPTS_FILE}")

    complete = sum(
        1 for v in prompts.values()
        if "word_prompt" in v and len(v.get("sentences", [])) == 10
    )
    print(f"  전체 완성도: {complete}/1800 ({complete/1800*100:.1f}%)")
    print("━" * 60)


if __name__ == "__main__":
    main()
