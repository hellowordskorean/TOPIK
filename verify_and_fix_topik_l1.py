"""
TOPIK Level 1 - 전체 300개 단어 검증 + 자동 수정 스크립트

Phase 1: 5개씩 배치 검증 → logs/verify_l1_full.json
Phase 2: 문제 단어 수정 → topik_1.json (EN) + illustration_prompts.json
         (한국어 ko 필드 수정은 모든 언어 버전에 반영)

재개 가능: 이미 처리된 항목은 스킵
"""

import json
import os
import re
import sys
import time
from copy import deepcopy
from pathlib import Path
from dotenv import load_dotenv
import anthropic

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── 경로 ────────────────────────────────────────────────────
BASE = Path(__file__).parent
load_dotenv(BASE / ".env")

DATA_DIR   = BASE.parent / "data/LanguageTest/TOPIK"
TOPIK_EN   = DATA_DIR / "EN/topik_1.json"
PROMPTS_F  = BASE.parent / "data/LanguageTest/illustration_prompts.json"
LOGS_DIR   = BASE / "logs"

VERIFY_LOG = LOGS_DIR / "verify_l1_full.json"
FIX_LOG    = LOGS_DIR / "fix_l1_full.json"

LANG_FILES = {
    "EN": DATA_DIR / "EN/topik_1.json",
    "CN": DATA_DIR / "CN/topik_1.json",
    "JP": DATA_DIR / "JP/topik_1.json",
    "VN": DATA_DIR / "VN/topik_1.json",
    "SP": DATA_DIR / "SP/topik_1.json",
}

BATCH_SIZE = 5  # 검증 배치 크기

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── JSON 로드/저장 헬퍼 ───────────────────────────────────────
def load_json(path):
    if not Path(path).exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_json(text: str):
    """마크다운 코드블록 제거 후 JSON 파싱"""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"```\s*$", "", text)
    text = text.strip()
    return json.loads(text)

# ══════════════════════════════════════════════════════════════
# PHASE 1: 배치 검증
# ══════════════════════════════════════════════════════════════

VERIFY_SYSTEM = """당신은 TOPIK 한국어 교재 품질 검수 전문가입니다.
여러 단어를 한번에 검토하여 각각에 대한 검수 결과를 반환하세요.

검토 기준:
1. **한국어 문법** — 조사/어미/시제/활용 오류. 특히:
   - 형용사에 '-ㄴ다/는다' 동사 어미 사용 (치명적 오류)
   - 동사 기본형으로 문장 종결 (비문)
   - '-아/어 주신다'를 요청문에 사용 (서술형/요청형 혼용)
   - TOPIK 1 수준 부적합 어휘·문형
2. **영어 번역** — 정확성, 자연스러움, 원문 문형과의 일치
3. **일러스트 프롬프트** — 단어/예문 핵심 의미 시각화 적절성, 잘림(미완성), 예문과 불일치

응답 형식: 단어 수만큼의 JSON 배열. 각 항목:
{
  "id": 단어id(정수),
  "word": "단어",
  "overall_score": 1~10,
  "issues": [
    {
      "type": "grammar|translation|prompt",
      "item_index": 예문번호(1~N) 또는 "word_prompt",
      "severity": "error|warning|suggestion",
      "description": "문제 설명",
      "original": "원문",
      "suggested": "개선안"
    }
  ],
  "summary": "한줄 요약"
}

문제 없으면 issues는 []. 반드시 valid JSON 배열만 반환. 마크다운 코드블록 없이."""

def build_batch_verify_prompt(batch: list, prompts_data: dict) -> str:
    lines = [f"아래 {len(batch)}개 단어를 검수해 주세요.\n"]
    for entry in batch:
        wid = str(entry["id"])
        pe = prompts_data.get(wid)
        lines.append(f"=== ID:{entry['id']} [{entry['word']}] ({entry['pos']}) '{entry['meaning']}' ===")
        lines.append("예문:")
        for i, ex in enumerate(entry["examples"], 1):
            lines.append(f"  {i}. KO: {ex['ko']}")
            lines.append(f"     EN: {ex['en']}")
            lines.append(f"     상황: {ex['situation']}")
        if pe:
            lines.append("일러스트 프롬프트:")
            lines.append(f"  단어: {pe.get('word_prompt','(없음)')}")
            for i, sp in enumerate(pe.get("sentences", []), 1):
                lines.append(f"  {i}. {sp}")
        lines.append("")
    return "\n".join(lines)

def verify_batch(batch: list, prompts_data: dict) -> list:
    prompt = build_batch_verify_prompt(batch, prompts_data)
    for attempt in range(3):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=8192,
                system=VERIFY_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text
            results = extract_json(raw)
            if isinstance(results, list):
                return results
            # 단일 객체로 반환된 경우
            return [results]
        except Exception as e:
            print(f"  [retry {attempt+1}] {e}")
            time.sleep(2 ** attempt)
    # 실패 시 빈 결과 반환
    return [{"id": e["id"], "word": e["word"], "overall_score": None,
             "issues": [], "summary": f"검증 실패"} for e in batch]

def phase1_verify(words: list, prompts_data: dict) -> dict:
    """Phase 1: 전체 검증. 이미 완료된 id는 스킵."""
    existing = load_json(VERIFY_LOG) or {}
    total = len(words)
    batches = [words[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    n_batches = len(batches)

    print(f"\n[PHASE 1] 검증 시작: {total}개 단어, {n_batches}개 배치")
    print("-" * 60)

    for bi, batch in enumerate(batches, 1):
        # 이미 처리된 배치 스킵
        todo = [w for w in batch if str(w["id"]) not in existing]
        if not todo:
            done_ids = [w["id"] for w in batch]
            print(f"  배치 {bi:03d}/{n_batches} (id {done_ids[0]}~{done_ids[-1]}) — 스킵(기처리)")
            continue

        ids = [w["id"] for w in todo]
        print(f"  배치 {bi:03d}/{n_batches} (id {ids[0]}~{ids[-1]}) ... ", end="", flush=True)

        results = verify_batch(todo, prompts_data)

        for r in results:
            existing[str(r["id"])] = r

        save_json(VERIFY_LOG, existing)

        score_str = ", ".join(
            f"{r['word']}:{r.get('overall_score','?')}" for r in results
        )
        total_issues = sum(len(r.get("issues", [])) for r in results)
        print(f"완료 | 점수 [{score_str}] | 이슈 {total_issues}건")

    print(f"\n[PHASE 1] 완료. 결과: {VERIFY_LOG}")
    return existing

# ══════════════════════════════════════════════════════════════
# PHASE 2: 자동 수정
# ══════════════════════════════════════════════════════════════

FIX_SYSTEM = """당신은 TOPIK 한국어 교재 편집 전문가입니다.
제공된 단어 데이터와 검수 이슈를 바탕으로 수정된 데이터를 반환하세요.

수정 규칙:
- error·warning 이슈는 반드시 수정하세요
- suggestion은 판단하여 적용하세요
- 수정하지 않는 필드는 원본 그대로 유지하세요
- 한국어(ko) 문장은 TOPIK 1 초급 수준에 맞게 수정하세요
- 일러스트 프롬프트가 잘려있으면 완전한 영어 문장으로 완성하세요

응답 형식 (JSON):
{
  "word": "단어",
  "examples": [
    {
      "situation": "상황",
      "ko": "수정된 한국어 예문",
      "en": "수정된 영어 번역"
    }
  ],
  "word_prompt": "수정된 단어 이미지 프롬프트",
  "sentence_prompts": ["예문1 프롬프트", "예문2 프롬프트", ...]
}

examples는 원본과 같은 순서, 같은 수로 반환하세요.
sentence_prompts도 원본 examples 수와 동일하게 반환하세요.
반드시 valid JSON만 반환. 마크다운 코드블록 없이."""

def build_fix_prompt(word_entry: dict, prompt_entry: dict, issues: list) -> str:
    lines = [
        f"단어: {word_entry['word']} ({word_entry['pos']}) — {word_entry['meaning']}",
        "",
        "현재 예문 데이터:",
    ]
    for i, ex in enumerate(word_entry["examples"], 1):
        lines.append(f"  {i}. KO: {ex['ko']}")
        lines.append(f"     EN: {ex['en']}")
        lines.append(f"     상황: {ex['situation']}")

    if prompt_entry:
        lines += ["", "현재 일러스트 프롬프트:",
                  f"  단어: {prompt_entry.get('word_prompt','(없음)')}"]
        for i, sp in enumerate(prompt_entry.get("sentences", []), 1):
            lines.append(f"  {i}. {sp}")

    lines += ["", "발견된 이슈:"]
    for iss in issues:
        sev = iss.get("severity", "?").upper()
        typ = iss.get("type", "?").upper()
        idx = iss.get("item_index", "?")
        desc = iss.get("description", "")
        sug = iss.get("suggested", "")
        lines.append(f"  [{sev}] {typ} #{idx}: {desc}")
        if sug:
            lines.append(f"    => 개선안: {sug}")

    return "\n".join(lines)

def fix_word(word_entry: dict, prompt_entry: dict, issues: list) -> dict | None:
    if not issues:
        return None
    prompt = build_fix_prompt(word_entry, prompt_entry, issues)
    for attempt in range(3):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=FIX_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text
            return extract_json(raw)
        except Exception as e:
            print(f"  [retry {attempt+1}] {e}")
            time.sleep(2 ** attempt)
    return None

def phase2_fix(verify_results: dict, words: list, prompts_data: dict):
    """Phase 2: 이슈 있는 단어 수정 후 JSON 파일 업데이트"""
    fix_log = load_json(FIX_LOG) or {}

    # 수정 대상: error 또는 warning 이슈가 있는 단어
    targets = []
    for w in words:
        wid = str(w["id"])
        vr = verify_results.get(wid, {})
        issues = vr.get("issues", [])
        actionable = [i for i in issues if i.get("severity") in ("error", "warning")]
        if actionable and wid not in fix_log:
            targets.append((w, actionable))

    total = len(targets)
    print(f"\n[PHASE 2] 수정 시작: {total}개 단어 (error/warning 보유)")
    print("-" * 60)

    for idx, (w, issues) in enumerate(targets, 1):
        wid = str(w["id"])
        print(f"  [{idx:03d}/{total}] {w['word']} (이슈 {len(issues)}건) ... ", end="", flush=True)

        pe = prompts_data.get(wid)
        fixed = fix_word(w, pe, issues)

        if fixed is None:
            print("수정 실패")
            continue

        fix_log[wid] = fixed
        save_json(FIX_LOG, fix_log)
        print("완료")

    print(f"\n[PHASE 2] 수정 결과 저장: {FIX_LOG}")

    # ── 파일 업데이트 ───────────────────────────────────────
    print("\n[PHASE 2] JSON 파일 반영 중...")
    apply_fixes(fix_log, prompts_data)

def apply_fixes(fix_log: dict, prompts_data: dict):
    """수정된 데이터를 실제 JSON 파일에 반영"""

    # EN 파일 + 한국어(ko) 수정은 모든 언어 파일에 반영
    lang_data = {}
    for lang, path in LANG_FILES.items():
        if path.exists():
            lang_data[lang] = load_json(path)

    prompts_updated = deepcopy(prompts_data)
    fixed_count = 0

    for wid, fixed in fix_log.items():
        word_name = fixed.get("word", "?")
        new_examples = fixed.get("examples", [])
        new_word_prompt = fixed.get("word_prompt")
        new_sentence_prompts = fixed.get("sentence_prompts", [])

        # 각 언어 파일의 word 찾아서 업데이트
        for lang, data in lang_data.items():
            for w in data.get("words", []):
                if str(w["id"]) == wid:
                    # ko 필드는 모든 언어에 반영, en 필드는 EN만
                    for i, ex in enumerate(new_examples):
                        if i < len(w["examples"]):
                            w["examples"][i]["ko"] = ex["ko"]
                            w["examples"][i]["situation"] = ex["situation"]
                            if lang == "EN" and "en" in ex:
                                w["examples"][i]["en"] = ex["en"]
                    break

        # 일러스트 프롬프트 업데이트
        if wid in prompts_updated:
            if new_word_prompt:
                prompts_updated[wid]["word_prompt"] = new_word_prompt
            if new_sentence_prompts:
                prompts_updated[wid]["sentences"] = new_sentence_prompts

        fixed_count += 1

    # 저장
    for lang, data in lang_data.items():
        path = LANG_FILES[lang]
        save_json(path, data)
        print(f"  저장: {path.name} ({lang})")

    save_json(PROMPTS_F, prompts_updated)
    print(f"  저장: illustration_prompts.json")
    print(f"\n[DONE] {fixed_count}개 단어 수정 반영 완료")

# ══════════════════════════════════════════════════════════════
# 메인
# ══════════════════════════════════════════════════════════════

def print_summary(verify_results: dict):
    results = list(verify_results.values())
    total = len(results)
    scored = [r for r in results if r.get("overall_score") is not None]
    avg = sum(r["overall_score"] for r in scored) / len(scored) if scored else 0
    errors   = sum(1 for r in results for i in r.get("issues",[]) if i.get("severity")=="error")
    warnings = sum(1 for r in results for i in r.get("issues",[]) if i.get("severity")=="warning")
    suggestions = sum(1 for r in results for i in r.get("issues",[]) if i.get("severity")=="suggestion")
    clean = sum(1 for r in results if not r.get("issues"))

    print(f"\n{'='*60}")
    print(f"[VERIFY SUMMARY] {total}개 단어")
    print(f"  평균 점수  : {avg:.1f} / 10")
    print(f"  이슈 없음  : {clean}개")
    print(f"  Error      : {errors}건")
    print(f"  Warning    : {warnings}건")
    print(f"  Suggestion : {suggestions}건")

    # 점수 분포
    dist = {}
    for r in scored:
        s = r["overall_score"]
        dist[s] = dist.get(s, 0) + 1
    print(f"\n  점수 분포:")
    for s in sorted(dist.keys()):
        bar = "#" * dist[s]
        print(f"    {s:2d}점: {bar} ({dist[s]})")
    print("="*60)

def main():
    topik_data = load_json(TOPIK_EN)
    prompts_data = load_json(PROMPTS_F)
    words = topik_data["words"]  # 300개

    # Phase 1: 전체 검증
    verify_results = phase1_verify(words, prompts_data)
    print_summary(verify_results)

    # Phase 2: 자동 수정
    phase2_fix(verify_results, words, prompts_data)

if __name__ == "__main__":
    main()
