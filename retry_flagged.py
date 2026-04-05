#!/usr/bin/env python3
"""
1순위 harness: flagged 이미지 자동 재처리
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
logs/illust_flagged.json 의 실패 이미지를 lint 강화 + VLM 재검증으로 재처리.
통과 시 flagged 목록에서 자동 제거.

실행:
  docker compose run --rm topik-bot python3 retry_flagged.py
  docker compose run --rm topik-bot python3 retry_flagged.py --dry-run
  docker compose run --rm topik-bot python3 retry_flagged.py --backend flux
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

FLAGGED_FILE = Path("/app/logs/illust_flagged.json")
RESULT_FILE  = Path("/app/logs/retry_results.json")


def load_flagged() -> list:
    if not FLAGGED_FILE.exists():
        return []
    with open(FLAGGED_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_flagged(data: list):
    with open(FLAGGED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_reinforced_prompt(word: dict, sent_idx: int) -> str:
    """기존 프롬프트에 lint + no-text 강화 적용"""
    if sent_idx == -1:
        base = gi.get_word_custom_prompt(word["id"]) or gi._word_prompt(word["meaning"])
    else:
        sents = word.get("sentences", [])
        sent = sents[sent_idx] if sent_idx < len(sents) else {}
        base = gi.get_sentence_custom_prompt(word["id"], sent_idx) or gi._sentence_prompt(word, sent)
    return gi._reinforce_no_text(gi._lint_prompt(base))


def main():
    parser = argparse.ArgumentParser(description="flagged 이미지 자동 재처리 harness")
    parser.add_argument("--db", default="/app/data/LanguageTest/words_db.json")
    parser.add_argument("--dry-run", action="store_true", help="목록만 출력, 생성 안 함")
    parser.add_argument("--backend", default="imagen", choices=["imagen", "flux"])
    parser.add_argument("--reason-filter", default=None,
                        help="특정 사유 키워드 포함 항목만 처리 (예: 'text detected')")
    args = parser.parse_args()

    gi._BACKEND = args.backend
    gi._VLM_VERIFY = True  # 재처리는 항상 VLM 검증

    flagged = load_flagged()
    if not flagged:
        print("flagged 이미지 없음.")
        return

    # 사유 필터
    if args.reason_filter:
        flagged = [f for f in flagged if args.reason_filter in f.get("reason", "")]
        print(f"필터 '{args.reason_filter}' 적용: {len(flagged)}개")

    with open(args.db, encoding="utf-8") as f:
        db = json.load(f)
    word_map = {w["id"]: w for w in db}
    gi._load_custom_prompts()

    client = None
    if args.backend == "imagen":
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            print("오류: GEMINI_API_KEY 없음")
            return
        from google import genai
        client = genai.Client(api_key=api_key)

    print(f"{'━' * 55}")
    print(f"  재처리 대상: {len(flagged)}개")
    print(f"  백엔드: {args.backend.upper()} | VLM 검증: ON")
    print(f"{'━' * 55}")

    if args.dry_run:
        for item in flagged:
            label = "단어" if item.get("sent_idx", -1) == -1 else f"예문[{item.get('sent_idx')}]"
            print(f"  [{item['word_id']:4d}] {item['word']:10s} {label:8s}  {item.get('reason','')[:60]}")
        return

    success, still_fail, skipped = 0, 0, 0
    remaining = []

    for item in flagged:
        word = word_map.get(item["word_id"])
        if not word:
            remaining.append(item)
            skipped += 1
            continue

        sent_idx = item.get("sent_idx", -1)
        lv = word["level"]
        target = (gi.word_img_path(word["word"], lv) if sent_idx == -1
                  else gi.sent_img_path(word["word"], lv, sent_idx))
        label = "단어" if sent_idx == -1 else f"예문[{sent_idx}]"

        print(f"\n[{word['id']}] {word['word']} / {label}")
        print(f"  사유: {item.get('reason', '')[:80]}")

        if target.exists():
            target.unlink()

        prompt = build_reinforced_prompt(word, sent_idx)
        ok = gi.generate_image(prompt, target, client, word=word, sent_idx=sent_idx)

        if ok:
            success += 1
            print(f"  ✓ 재생성 성공")
        else:
            still_fail += 1
            remaining.append(item)
            print(f"  ✗ 재생성 실패 — flagged 유지")

        time.sleep(0.5)

    # flagged 목록 업데이트 (성공한 것 제거)
    all_flagged = load_flagged()
    success_ids = {
        (item["word_id"], item.get("sent_idx", -1))
        for item in flagged
        if (item["word_id"], item.get("sent_idx", -1)) not in
           {(r["word_id"], r.get("sent_idx", -1)) for r in remaining}
    }
    updated_flagged = [
        f for f in all_flagged
        if (f["word_id"], f.get("sent_idx", -1)) not in success_ids
    ]
    save_flagged(updated_flagged)

    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "run_at": datetime.now().isoformat(),
            "total": len(flagged),
            "success": success,
            "still_fail": still_fail,
            "skipped": skipped,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n{'━' * 55}")
    print(f"  성공: {success} | 실패: {still_fail} | 스킵: {skipped}")
    print(f"  남은 flagged: {len(updated_flagged)}개")
    print(f"  결과: {RESULT_FILE}")


if __name__ == "__main__":
    main()
