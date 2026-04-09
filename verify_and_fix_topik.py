"""
TOPIK 전체 레벨 검증 + 자동 수정 스크립트

사용법:
  python verify_and_fix_topik.py 1        # Level 1만
  python verify_and_fix_topik.py 1 2 3    # 복수 레벨
  python verify_and_fix_topik.py          # 1~6 전체

Phase 1: 5개씩 배치 검증 → logs/verify_lN_full.json
Phase 2: error/warning 단어 자동 수정 → topik_N.json (전 언어) + illustration_prompts.json

재개 가능: 이미 처리된 id는 스킵
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

BASE = Path(__file__).parent
load_dotenv(BASE / ".env")

DATA_DIR  = BASE.parent / "data/LanguageTest/TOPIK"
PROMPTS_F = BASE.parent / "data/LanguageTest/illustration_prompts.json"
LOGS_DIR  = BASE / "logs"
LANGS     = ["EN", "CN", "JP", "VN", "SP"]
BATCH_SIZE = 5

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ── 공통 유틸 ────────────────────────────────────────────────

def load_json(path):
    p = Path(path)
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"```\s*$", "", text)
    text = text.strip()
    return json.loads(text)

def lang_path(level: int, lang: str) -> Path:
    return DATA_DIR / lang / f"topik_{level}.json"


# ══════════════════════════════════════════════════════════════
# PHASE 1 — 배치 검증
# ══════════════════════════════════════════════════════════════

VERIFY_SYSTEM = """당신은 TOPIK 한국어 교재 품질 검수 전문가입니다.
여러 단어를 한번에 검토하여 각각에 대한 검수 결과를 JSON 배열로 반환하세요.

검토 기준:
1. 한국어 문법
   - 형용사에 '-ㄴ다/는다' 동사 어미 사용 (치명적 오류)
   - 동사/형용사 기본형으로 문장 종결 (비문)
   - '-아/어 주신다'를 요청문에 사용 (서술형/요청형 혼용)
   - '-신다/하신다' 어미 서술문을 명령/요청문으로 오용
   - 해당 레벨에 부적합한 어휘·문형
   - 문체 비일관성 (해요체/합쇼체/반말 혼용)
2. 영어 번역 — 정확성, 자연스러움, 원문 문형(평서/의문/명령)과 일치
3. 일러스트 프롬프트
   - 예문 핵심 동작/상황 미표현
   - 프롬프트가 문장 중간에서 잘림(미완성)
   - 예문과 장면 불일치

응답 형식 (JSON 배열):
[
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
]

문제 없으면 issues는 []. 반드시 valid JSON 배열만 반환. 마크다운 코드블록 없이."""


def build_verify_prompt(batch: list, prompts_data: dict) -> str:
    lines = [f"아래 {len(batch)}개 단어를 검수해 주세요.\n"]
    for e in batch:
        wid = str(e["id"])
        pe  = prompts_data.get(wid) if prompts_data else None
        lines.append(f"=== ID:{e['id']} [{e['word']}] ({e['pos']}) '{e['meaning']}' ===")
        lines.append("예문:")
        for i, ex in enumerate(e["examples"], 1):
            lines.append(f"  {i}. KO: {ex['ko']}")
            lines.append(f"     EN: {ex.get('en', ex.get('meaning',''))}")
            lines.append(f"     상황: {ex['situation']}")
        if pe:
            lines.append("일러스트 프롬프트:")
            lines.append(f"  단어: {pe.get('word_prompt','(없음)')}")
            for i, sp in enumerate(pe.get("sentences", []), 1):
                lines.append(f"  {i}. {sp}")
        lines.append("")
    return "\n".join(lines)


def verify_batch(batch: list, prompts_data: dict) -> list:
    prompt = build_verify_prompt(batch, prompts_data)
    for attempt in range(3):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=8192,
                system=VERIFY_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text
            result = extract_json(raw)
            return result if isinstance(result, list) else [result]
        except Exception as e:
            print(f"  [retry {attempt+1}/3] {e}")
            time.sleep(2 ** attempt)
    return [{"id": e["id"], "word": e["word"], "overall_score": None,
             "issues": [], "summary": "검증 실패"} for e in batch]


def phase1_verify(level: int, words: list, prompts_data: dict) -> dict:
    verify_log = LOGS_DIR / f"verify_l{level}_full.json"
    existing   = load_json(verify_log) or {}
    batches    = [words[i:i+BATCH_SIZE] for i in range(0, len(words), BATCH_SIZE)]
    n = len(batches)

    print(f"\n[L{level} PHASE 1] 검증: {len(words)}개 단어, {n}배치")
    print("-" * 60)

    for bi, batch in enumerate(batches, 1):
        todo = [w for w in batch if str(w["id"]) not in existing]
        if not todo:
            print(f"  배치 {bi:03d}/{n} — 스킵")
            continue

        ids = [w["id"] for w in todo]
        print(f"  배치 {bi:03d}/{n} (id {ids[0]}~{ids[-1]}) ... ", end="", flush=True)

        results = verify_batch(todo, prompts_data)
        for r in results:
            existing[str(r["id"])] = r
        save_json(verify_log, existing)

        scores = ", ".join(f"{r['word']}:{r.get('overall_score','?')}" for r in results)
        issues = sum(len(r.get("issues", [])) for r in results)
        print(f"완료 [{scores}] 이슈:{issues}")

    print(f"\n[L{level} PHASE 1] 완료 → {verify_log}")
    return existing


# ══════════════════════════════════════════════════════════════
# PHASE 2 — 자동 수정
# ══════════════════════════════════════════════════════════════

FIX_SYSTEM = """당신은 TOPIK 한국어 교재 편집 전문가입니다.
제공된 단어 데이터와 검수 이슈를 바탕으로 수정된 데이터를 반환하세요.

수정 규칙:
- error·warning 이슈는 반드시 수정
- suggestion은 판단하여 적용
- 수정하지 않는 필드는 원본 그대로 유지
- 한국어(ko) 문장은 해당 TOPIK 레벨에 맞는 자연스러운 문형으로 수정
- 형용사 오활용, 기본형 종결, 요청문 어미 오류를 반드시 수정
- 일러스트 프롬프트가 잘려있으면 완전한 영어 문장으로 완성

응답 형식 (JSON):
{
  "word": "단어",
  "examples": [
    {"situation": "상황", "ko": "수정된 한국어", "en": "수정된 영어"}
  ],
  "word_prompt": "수정된 단어 이미지 프롬프트 (변경 없으면 원본 그대로)",
  "sentence_prompts": ["예문1 프롬프트", "예문2 프롬프트", ...]
}

examples와 sentence_prompts 개수는 원본과 동일하게 유지하세요.
반드시 valid JSON만 반환. 마크다운 코드블록 없이."""


def build_fix_prompt(w: dict, pe: dict, issues: list) -> str:
    lines = [
        f"단어: {w['word']} ({w['pos']}) — {w['meaning']}",
        "", "현재 예문:"
    ]
    for i, ex in enumerate(w["examples"], 1):
        lines.append(f"  {i}. KO: {ex['ko']}")
        lines.append(f"     EN: {ex.get('en', ex.get('meaning',''))}")
        lines.append(f"     상황: {ex['situation']}")
    if pe:
        lines += ["", "현재 일러스트 프롬프트:",
                  f"  단어: {pe.get('word_prompt','(없음)')}"]
        for i, sp in enumerate(pe.get("sentences", []), 1):
            lines.append(f"  {i}. {sp}")
    lines += ["", "발견된 이슈:"]
    for iss in issues:
        sev = iss.get("severity","?").upper()
        typ = iss.get("type","?").upper()
        idx = iss.get("item_index","?")
        lines.append(f"  [{sev}] {typ} #{idx}: {iss.get('description','')}")
        if iss.get("suggested"):
            lines.append(f"    => {iss['suggested']}")
    return "\n".join(lines)


def fix_word(w: dict, pe: dict, issues: list) -> dict | None:
    prompt = build_fix_prompt(w, pe, issues)
    for attempt in range(3):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=FIX_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            return extract_json(resp.content[0].text)
        except Exception as e:
            print(f"  [retry {attempt+1}/3] {e}")
            time.sleep(2 ** attempt)
    return None


def apply_fixes(level: int, fix_log: dict, prompts_data: dict):
    """수정 결과를 실제 JSON 파일에 반영"""
    lang_data = {}
    for lang in LANGS:
        p = lang_path(level, lang)
        if p.exists():
            lang_data[lang] = load_json(p)

    prompts_updated = deepcopy(prompts_data) if prompts_data else {}
    count = 0

    for wid, fixed in fix_log.items():
        new_examples        = fixed.get("examples", [])
        new_word_prompt     = fixed.get("word_prompt")
        new_sentence_prompts = fixed.get("sentence_prompts", [])

        for lang, data in lang_data.items():
            for w in data.get("words", []):
                if str(w["id"]) == wid:
                    for i, ex in enumerate(new_examples):
                        if i < len(w["examples"]):
                            w["examples"][i]["ko"] = ex["ko"]
                            w["examples"][i]["situation"] = ex.get("situation", w["examples"][i]["situation"])
                            # 번역 필드는 해당 언어 키로 처리
                            if lang == "EN" and "en" in ex:
                                w["examples"][i]["en"] = ex["en"]
                    break

        if wid in prompts_updated:
            if new_word_prompt:
                prompts_updated[wid]["word_prompt"] = new_word_prompt
            if new_sentence_prompts:
                prompts_updated[wid]["sentences"] = new_sentence_prompts

        count += 1

    for lang, data in lang_data.items():
        save_json(lang_path(level, lang), data)
        print(f"  저장: topik_{level}.json ({lang})")

    if prompts_data is not None:
        save_json(PROMPTS_F, prompts_updated)
        print(f"  저장: illustration_prompts.json")

    print(f"  수정 반영: {count}개 단어")


def phase2_fix(level: int, verify_results: dict, words: list, prompts_data: dict):
    fix_log_path = LOGS_DIR / f"fix_l{level}_full.json"
    fix_log = load_json(fix_log_path) or {}

    targets = []
    for w in words:
        wid = str(w["id"])
        issues = verify_results.get(wid, {}).get("issues", [])
        actionable = [i for i in issues if i.get("severity") in ("error", "warning")]
        if actionable and wid not in fix_log:
            targets.append((w, actionable))

    total = len(targets)
    print(f"\n[L{level} PHASE 2] 수정: {total}개 단어")
    print("-" * 60)

    for idx, (w, issues) in enumerate(targets, 1):
        wid = str(w["id"])
        pe = prompts_data.get(wid) if prompts_data else None
        print(f"  [{idx:03d}/{total}] {w['word']} (이슈 {len(issues)}건) ... ", end="", flush=True)

        fixed = fix_word(w, pe, issues)
        if fixed is None:
            print("실패")
            continue

        fix_log[wid] = fixed
        save_json(fix_log_path, fix_log)
        print("완료")

    print(f"\n[L{level} PHASE 2] 수정 결과 반영 중...")
    apply_fixes(level, fix_log, prompts_data)


# ══════════════════════════════════════════════════════════════
# 통계 출력
# ══════════════════════════════════════════════════════════════

def print_summary(level: int, verify_results: dict):
    results = list(verify_results.values())
    total = len(results)
    scored = [r for r in results if r.get("overall_score") is not None]
    avg = sum(r["overall_score"] for r in scored) / len(scored) if scored else 0
    errors      = sum(1 for r in results for i in r.get("issues",[]) if i.get("severity")=="error")
    warnings    = sum(1 for r in results for i in r.get("issues",[]) if i.get("severity")=="warning")
    suggestions = sum(1 for r in results for i in r.get("issues",[]) if i.get("severity")=="suggestion")
    clean       = sum(1 for r in results if not r.get("issues"))
    dist = {}
    for r in scored:
        s = r["overall_score"]
        dist[s] = dist.get(s, 0) + 1

    print(f"\n{'='*60}")
    print(f"[LEVEL {level} 검증 요약] {total}개 단어")
    print(f"  평균 점수  : {avg:.1f} / 10")
    print(f"  이슈 없음  : {clean}개")
    print(f"  Error      : {errors}건")
    print(f"  Warning    : {warnings}건")
    print(f"  Suggestion : {suggestions}건")
    print(f"  점수 분포  : ", end="")
    for s in sorted(dist):
        print(f"{s}점×{dist[s]}", end="  ")
    print(f"\n{'='*60}")


# ══════════════════════════════════════════════════════════════
# 메인
# ══════════════════════════════════════════════════════════════

def process_level(level: int):
    print(f"\n{'#'*60}")
    print(f"#  TOPIK LEVEL {level} 처리 시작")
    print(f"{'#'*60}")

    en_path = lang_path(level, "EN")
    if not en_path.exists():
        print(f"  [SKIP] {en_path} 없음")
        return

    topik_data   = load_json(en_path)
    prompts_data = load_json(PROMPTS_F) if level == 1 else None  # 프롬프트는 레벨1 전용
    words        = topik_data["words"]

    print(f"  단어 수: {len(words)}")

    verify_results = phase1_verify(level, words, prompts_data)
    print_summary(level, verify_results)
    phase2_fix(level, verify_results, words, prompts_data)

    print(f"\n[LEVEL {level}] 완료!")


def main():
    levels = [int(a) for a in sys.argv[1:] if a.isdigit()] or list(range(1, 7))
    print(f"처리 레벨: {levels}")
    for lv in levels:
        process_level(lv)
    print(f"\n{'#'*60}")
    print(f"#  모든 처리 완료!")
    print(f"{'#'*60}")


if __name__ == "__main__":
    main()
