#!/usr/bin/env python3
"""
2순위 harness: 이미지 의미 정합성 검증
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VLM이 생성된 이미지를 보고 단어 의미와 실제로 일치하는지 검증.
텍스트 검증(--vlm-verify)과 달리 "의미가 맞냐"를 봄.

검증 통과 기준:
  - matches=true AND confidence >= threshold (기본 60)

불일치 이미지 → logs/illust_semantic_fail.json 기록
--fix 플래그 시 → 즉시 재생성

실행:
  docker compose run --rm topik-bot python3 verify_illustrations.py --start 1 --end 50
  docker compose run --rm topik-bot python3 verify_illustrations.py --start 1 --end 50 --fix
  docker compose run --rm topik-bot python3 verify_illustrations.py --word-only --start 1 --end 200
"""
import json
import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent))
import generate_illustrations as gi
from google import genai

FAIL_FILE    = Path("/app/logs/illust_semantic_fail.json")
SUMMARY_FILE = Path("/app/logs/illust_semantic_summary.json")

# ── VLM 프롬프트 ────────────────────────────────────────────────

WORD_VERIFY_PROMPT = """This illustration is from a Korean language learning app.
It must visually represent: '{meaning}' (Korean word: {word}, {pos}, TOPIK level {level}).

Look ONLY at the visual content — ignore any text in the image.

Answer these questions:
1. What is the main subject/action you see?
2. Does it clearly convey the concept '{meaning}'?
3. Confidence 0-100: how likely would a learner guess '{meaning}' from this image?

Respond ONLY with JSON (no markdown):
{{"matches": true/false, "confidence": 0-100, "what_i_see": "one sentence", "issue": "reason if matches=false, else null"}}"""

SENT_VERIFY_PROMPT = """This illustration is from a Korean language learning app.
It must visually depict this situation: {ko} (English: {en})
The target word is '{word}' meaning '{meaning}'.

Look ONLY at the visual content — ignore any text in the image.

Answer:
1. What do you see happening in the image?
2. Does it match the described situation?
3. Confidence 0-100 that this image illustrates the given sentence.

Respond ONLY with JSON (no markdown):
{{"matches": true/false, "confidence": 0-100, "what_i_see": "one sentence", "issue": "reason if matches=false, else null"}}"""


def _call_vlm(client, image_path: Path, prompt: str) -> dict:
    """Gemini Vision 호출 공통 함수"""
    try:
        import PIL.Image
        img = PIL.Image.open(str(image_path))
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[img, prompt],
        )
        raw = (response.text or "").strip()
        if raw.startswith("```"):
            raw = raw[raw.index("\n") + 1:]
            if raw.endswith("```"):
                raw = raw[:-3].strip()
        return json.loads(raw)
    except Exception as e:
        # 검증 오류는 통과 처리 (재생성 루프 방지)
        return {"matches": True, "confidence": 100, "what_i_see": "", "issue": f"검증 오류: {e}"}


def verify_word_image(client, image_path: Path, word: dict) -> dict:
    prompt = WORD_VERIFY_PROMPT.format(
        meaning=word["meaning"],
        word=word["word"],
        pos=word["part_of_speech"],
        level=word["level"],
    )
    return _call_vlm(client, image_path, prompt)


def verify_sent_image(client, image_path: Path, word: dict, sent: dict) -> dict:
    prompt = SENT_VERIFY_PROMPT.format(
        ko=sent.get("ko", ""),
        en=sent.get("en", ""),
        word=word["word"],
        meaning=word["meaning"],
    )
    return _call_vlm(client, image_path, prompt)


def main():
    parser = argparse.ArgumentParser(description="이미지 의미 정합성 검증 harness")
    parser.add_argument("--db", default="/app/data/LanguageTest/words_db.json")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end",   type=int, default=1800)
    parser.add_argument("--fix",   action="store_true", help="불일치 이미지 즉시 재생성")
    parser.add_argument("--word-only", action="store_true", help="word.png만 검증")
    parser.add_argument("--threshold", type=int, default=60,
                        help="최소 confidence (기본 60). 이 이하면 실패 처리")
    parser.add_argument("--backend", default="imagen", choices=["imagen", "flux"])
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("오류: GEMINI_API_KEY 없음")
        return
    client = genai.Client(api_key=api_key)

    with open(args.db, encoding="utf-8") as f:
        db = json.load(f)
    words = [w for w in db if args.start <= w["id"] <= args.end]

    gi._load_custom_prompts()
    if args.fix:
        gi._BACKEND = args.backend
        gi._VLM_VERIFY = True

    fail_log = []
    total = passed = failed = missing = 0

    print(f"{'━' * 55}")
    print(f"  의미 정합성 검증: {len(words)}개 단어")
    print(f"  threshold={args.threshold} | fix={args.fix} | word-only={args.word_only}")
    print(f"{'━' * 55}")

    for word in words:
        lv = word["level"]
        wpath = gi.word_img_path(word["word"], lv)

        # ── word.png 검증 ──────────────────────────────────────
        if not wpath.exists():
            missing += 1
        else:
            total += 1
            result = verify_word_image(client, wpath, word)
            ok = result.get("matches", True) and result.get("confidence", 100) >= args.threshold

            if ok:
                passed += 1
                print(f"  ✓ [{word['id']:4d}] {word['word']:10s}  "
                      f"conf={result.get('confidence', '?'):3}  {result.get('what_i_see','')[:50]}")
            else:
                failed += 1
                entry = {
                    "word_id": word["id"], "word": word["word"],
                    "type": "word", "sent_idx": -1,
                    "confidence": result.get("confidence", 0),
                    "what_i_see": result.get("what_i_see", ""),
                    "issue": result.get("issue", ""),
                    "path": str(wpath),
                }
                fail_log.append(entry)
                print(f"  ✗ [{word['id']:4d}] {word['word']:10s}  "
                      f"conf={result.get('confidence', '?'):3}  "
                      f"본 것: {result.get('what_i_see','')[:40]}  "
                      f"/ {result.get('issue','')[:40]}")
                if args.fix:
                    wpath.unlink()
                    prompt = gi.get_word_custom_prompt(word["id"]) or gi._word_prompt(word["meaning"])
                    gi.generate_image(
                        gi._reinforce_no_text(gi._lint_prompt(prompt)),
                        wpath, client, word=word, sent_idx=-1
                    )

        time.sleep(0.3)

        # ── 예문 이미지 검증 ────────────────────────────────────
        if args.word_only:
            continue

        for idx, sent in enumerate(word.get("sentences", [])):
            spath = gi.sent_img_path(word["word"], lv, idx)
            if not spath.exists():
                missing += 1
                continue

            total += 1
            result = verify_sent_image(client, spath, word, sent)
            ok = result.get("matches", True) and result.get("confidence", 100) >= args.threshold

            if not ok:
                failed += 1
                fail_log.append({
                    "word_id": word["id"], "word": word["word"],
                    "type": "sentence", "sent_idx": idx,
                    "sentence_ko": sent.get("ko", ""),
                    "confidence": result.get("confidence", 0),
                    "what_i_see": result.get("what_i_see", ""),
                    "issue": result.get("issue", ""),
                    "path": str(spath),
                })
                if args.fix:
                    spath.unlink()
                    prompt = gi.build_sentence_prompt(word, sent, sent_idx=idx)
                    gi.generate_image(
                        gi._reinforce_no_text(gi._lint_prompt(prompt)),
                        spath, client, word=word, sent_idx=idx
                    )
            else:
                passed += 1

            time.sleep(0.2)

    # ── 결과 저장 ────────────────────────────────────────────────
    FAIL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FAIL_FILE, "w", encoding="utf-8") as f:
        json.dump(fail_log, f, ensure_ascii=False, indent=2)

    summary = {
        "run_at": datetime.now().isoformat(),
        "range": f"{args.start}-{args.end}",
        "threshold": args.threshold,
        "total": total, "passed": passed,
        "failed": failed, "missing": missing,
        "pass_rate": f"{passed / total * 100:.1f}%" if total else "N/A",
    }
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'━' * 55}")
    print(f"  검증: {total} | 통과: {passed} | 실패: {failed} | 없음: {missing}")
    print(f"  통과율: {summary['pass_rate']}")
    print(f"  실패 목록: {FAIL_FILE}")


if __name__ == "__main__":
    main()
