"""
현재까지의 최선 결과를 즉시 파일에 적용
improve_l1_A.json (재작성) + improve_l1_C1.json (수정) 병합
"""

import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
load_dotenv(BASE / ".env")

DATA_DIR  = BASE.parent / "data/LanguageTest/TOPIK"
PROMPTS_F = BASE.parent / "data/LanguageTest/illustration_prompts.json"
LOGS_DIR  = BASE / "logs"

LANG_FILES = {
    "EN": DATA_DIR / "EN/topik_1.json",
    "CN": DATA_DIR / "CN/topik_1.json",
    "JP": DATA_DIR / "JP/topik_1.json",
    "VN": DATA_DIR / "VN/topik_1.json",
    "SP": DATA_DIR / "SP/topik_1.json",
}

def load_json(path):
    p = Path(path)
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    # 데이터 로드
    log_a = load_json(LOGS_DIR / "improve_l1_A.json") or {}
    log_c1 = load_json(LOGS_DIR / "improve_l1_C1.json") or {}
    log_b1 = load_json(LOGS_DIR / "improve_l1_B1.json") or {}
    prompts_data = load_json(PROMPTS_F) or {}

    print(f"LOG_A: {len(log_a)}개")
    print(f"LOG_C1 (수정): {len(log_c1)}개")
    print(f"LOG_B1 (검증): {len(log_b1)}개")

    # C1으로 A 업데이트 (C1이 있으면 C1 우선)
    merged = deepcopy(log_a)
    for wid, fixed in log_c1.items():
        merged[wid] = fixed
    print(f"병합 결과: {len(merged)}개")

    # LOG_A에 없는 ID 확인
    missing = [i for i in range(1, 301) if str(i) not in merged]
    if missing:
        print(f"누락 ID: {len(missing)}개 - {missing[:10]}...")
        print("누락 ID는 원본 데이터를 유지합니다.")
    else:
        print("모든 300개 단어 데이터 확인됨")

    # 반말 통계
    import re
    def has_banmal(s):
        if not re.search(r'다[\.\!\?]?\s*$', s): return False
        return not re.search(
            r'(아요|어요|해요|예요|이에요|세요|겠어요|주세요|합니다|입니다|습니다|겠습니다)[\.\!\?]?\s*$', s)

    banmal_before_apply = sum(1 for d in merged.values() for ex in d.get('examples', []) if has_banmal(ex.get('ko','')))
    print(f"적용 예정 데이터 반말: {banmal_before_apply}건")

    # 파일 적용
    print("\n[APPLY] 파일 반영 중...")

    lang_data = {}
    for lang, path in LANG_FILES.items():
        if path.exists():
            lang_data[lang] = load_json(path)

    prompts_updated = deepcopy(prompts_data)
    applied = 0
    skipped = 0

    for wid, fixed in merged.items():
        if int(wid) > 300:
            continue

        new_examples = fixed.get("examples", [])
        new_word_prompt = fixed.get("word_prompt")
        new_sentence_prompts = fixed.get("sentence_prompts", [])

        if not new_examples:
            skipped += 1
            continue

        for lang, data in lang_data.items():
            for w in data.get("words", []):
                if str(w["id"]) == wid:
                    for i, ex in enumerate(new_examples):
                        if i < len(w["examples"]):
                            w["examples"][i]["ko"] = ex["ko"]
                            w["examples"][i]["situation"] = ex.get("situation", w["examples"][i].get("situation",""))
                            if lang == "EN" and "en" in ex:
                                w["examples"][i]["en"] = ex["en"]
                    break

        if wid in prompts_updated:
            if new_word_prompt:
                prompts_updated[wid]["word_prompt"] = new_word_prompt
            if new_sentence_prompts:
                n = len(new_examples)
                prompts_updated[wid]["sentences"] = new_sentence_prompts[:n]

        applied += 1

    # 저장
    for lang, data in lang_data.items():
        save_json(LANG_FILES[lang], data)
        print(f"  저장: {LANG_FILES[lang].name} ({lang})")

    save_json(PROMPTS_F, prompts_updated)
    print(f"  저장: illustration_prompts.json")
    print(f"\n[완료] {applied}개 단어 반영 (스킵: {skipped}개)")

    # 최종 반말 통계
    final_en = load_json(LANG_FILES["EN"])
    banmal_after = sum(1 for w in final_en["words"] for ex in w["examples"]
                       if has_banmal(ex.get("ko","")))
    total = sum(len(w["examples"]) for w in final_en["words"])
    print(f"\n[최종] topik_1.json 반말: {banmal_after}/{total}건")

    # 점수 요약
    if log_b1:
        scored = [r for r in log_b1.values() if r.get('overall_score') is not None]
        avg = sum(r['overall_score'] for r in scored) / len(scored) if scored else 0
        perfect = sum(1 for r in scored if r['overall_score'] == 10)
        print(f"[B1 검증 기준] 평균 점수: {avg:.2f}/10, 10점: {perfect}/300개")

if __name__ == "__main__":
    main()
