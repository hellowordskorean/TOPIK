"""
TOPIK Level 1 — 예문·프롬프트 10/10 완성도 달성 스크립트

핵심 문제: 예문 3000개 중 ~70%가 반말(-다)로 끝남 → TOPIK 1급 치명적 오류
전략:
  Phase A : 전체 재작성 (해요체 강제 + 문법 완벽 + 프롬프트 개선) — 5개 배치
  Phase B : 재검증 (5개 배치)
  Phase C : 10점 미달 재수정
  Phase D : B-C 최대 3라운드 반복

결과 파일:
  logs/improve_l1_A.json   — Phase A 재작성 결과 (재개 가능)
  logs/improve_l1_B.json   — Phase B 검증 결과
  logs/improve_l1_C.json   — Phase C 재수정 결과
  logs/improve_l1_Cn.json  — n라운드 추가 재수정
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
LOGS_DIR.mkdir(exist_ok=True)

LANG_FILES = {
    "EN": DATA_DIR / "EN/topik_1.json",
    "CN": DATA_DIR / "CN/topik_1.json",
    "JP": DATA_DIR / "JP/topik_1.json",
    "VN": DATA_DIR / "VN/topik_1.json",
    "SP": DATA_DIR / "SP/topik_1.json",
}

LOG_A = LOGS_DIR / "improve_l1_A.json"
LOG_B = LOGS_DIR / "improve_l1_B.json"

BATCH_SIZE = 5
MAX_ROUNDS = 3

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── 헬퍼 ────────────────────────────────────────────────────────

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

def extract_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"```\s*$", "", text)
    return json.loads(text.strip())

def has_banmal(sentence: str) -> bool:
    """반말(-다) 종결 감지"""
    return bool(re.search(r'[다][\.\!\?]?\s*$', sentence) and
                not re.search(r'(아요|어요|해요|예요|이에요|세요|ㄹ게요|겠어요|주세요|해주세요|드세요|읍시다|합시다|ㄹ까요|을까요|ㄴ가요|는가요)[\.\!\?]?\s*$', sentence))

def count_banmal(examples: list) -> int:
    return sum(1 for ex in examples if has_banmal(ex.get("ko", "")))

# ══════════════════════════════════════════════════════════════
# Phase A: 전체 재작성
# ══════════════════════════════════════════════════════════════

REWRITE_SYSTEM = """당신은 TOPIK 한국어 교재 최고 품질 편집 전문가입니다.

[절대 규칙 — 위반 시 10점 불가]
1. 모든 한국어 예문은 반드시 해요체로만 종결
   - 동사: -아요/어요/해요  (예: 가요, 먹어요, 공부해요)
   - 형용사: -아요/어요  (예: 좋아요, 비싸요, 작아요)
   - 이다: -이에요/예요  (예: 학생이에요, 가게예요)
   - 요청/청유: -세요/-ㅂ시다/-ㄹ까요  (예: 주세요, 갑시다, 할까요)
   - 미래: -ㄹ/을 거예요/-겠어요  (예: 갈 거예요, 먹겠어요)
   - 과거: -았어요/었어요/했어요  (예: 갔어요, 먹었어요)
2. 절대 금지: 문장을 -다로 끝내지 마세요
   (좋다→좋아요, 먹는다→먹어요, 비싸다→비싸요, 있다→있어요, 없다→없어요)
3. TOPIK 1급 초급 어휘/문법만 사용 (급수 초과 어휘 금지)
4. 자연스럽고 일상적인 상황의 실제 쓰이는 문장
5. 영어 번역: 정확하고 자연스러운 현대 영어
6. 일러스트 프롬프트: 핵심 개념을 명확히 시각화하는 완전한 영어 설명 문장

응답 형식 (JSON 배열 — 입력 단어 수와 동일한 수):
[
  {
    "id": 단어ID(정수),
    "word": "단어",
    "examples": [
      {"situation": "상황(영어)", "ko": "해요체 예문", "en": "자연스러운 영어 번역"},
      ...
    ],
    "word_prompt": "단어 핵심 개념 일러스트 프롬프트(영어)",
    "sentence_prompts": ["예문1 상황 프롬프트(영어)", ...]
  }
]

반드시 valid JSON 배열만 반환. 마크다운 없이."""

def build_rewrite_prompt(batch: list, prompts_data: dict) -> str:
    lines = [f"아래 {len(batch)}개 단어의 예문과 프롬프트를 10점 만점 품질로 완전히 재작성하세요.\n"]
    lines.append("기존 데이터 참고용 (완전히 개선 가능):\n")
    for entry in batch:
        wid = str(entry["id"])
        pe = prompts_data.get(wid, {})
        lines.append(f"--- ID:{entry['id']} [{entry['word']}] ({entry['pos']}) 뜻: {entry['meaning']} ---")
        lines.append("기존 예문:")
        for i, ex in enumerate(entry["examples"], 1):
            lines.append(f"  {i}. KO: {ex['ko']}")
            lines.append(f"     EN: {ex['en']}")
            lines.append(f"     상황: {ex.get('situation','')}")
        lines.append(f"기존 단어프롬프트: {pe.get('word_prompt','없음')}")
        lines.append("기존 예문프롬프트:")
        for i, sp in enumerate(pe.get("sentences", [])[:len(entry["examples"])], 1):
            lines.append(f"  {i}. {sp}")
        lines.append("")
    return "\n".join(lines)

def rewrite_batch(batch: list, prompts_data: dict) -> list:
    prompt = build_rewrite_prompt(batch, prompts_data)
    for attempt in range(3):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=8192,
                system=REWRITE_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text
            results = extract_json(raw)
            if isinstance(results, list):
                return results
            return [results]
        except Exception as e:
            print(f"  [retry {attempt+1}] {e}")
            time.sleep(2 ** attempt)
    return []

def phase_a_rewrite(words: list, prompts_data: dict) -> dict:
    """Phase A: 전체 재작성. 이미 완료된 id 스킵."""
    existing = load_json(LOG_A) or {}
    total = len(words)
    batches = [words[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    n_batches = len(batches)

    print(f"\n[PHASE A] 전체 재작성: {total}개 단어, {n_batches}개 배치")
    print("=" * 60)

    for bi, batch in enumerate(batches, 1):
        todo = [w for w in batch if str(w["id"]) not in existing]
        if not todo:
            ids = [w["id"] for w in batch]
            print(f"  배치 {bi:03d}/{n_batches} (id {ids[0]}~{ids[-1]}) — 스킵")
            continue

        ids = [w["id"] for w in todo]
        print(f"  배치 {bi:03d}/{n_batches} (id {ids[0]}~{ids[-1]}) ... ", end="", flush=True)

        results = rewrite_batch(todo, prompts_data)

        banmal_warns = []
        for r in results:
            wid = str(r["id"])
            bm = count_banmal(r.get("examples", []))
            if bm > 0:
                banmal_warns.append(f"{r['word']}:{bm}")
            existing[wid] = r

        save_json(LOG_A, existing)
        warn_str = f" [반말잔존! {', '.join(banmal_warns)}]" if banmal_warns else ""
        print(f"완료{warn_str}")

    # 반말 잔존 항목 재시도
    banmal_ids = [wid for wid, r in existing.items() if count_banmal(r.get("examples", [])) > 0]
    if banmal_ids:
        print(f"\n  [반말 재수정] {len(banmal_ids)}개 항목 재처리...")
        word_map = {str(w["id"]): w for w in words}
        for wid in banmal_ids:
            w = word_map.get(wid)
            if not w:
                continue
            print(f"    [{w['word']}] 반말 재수정 ... ", end="", flush=True)
            results = rewrite_batch([w], prompts_data)
            if results:
                r = results[0]
                bm = count_banmal(r.get("examples", []))
                existing[wid] = r
                save_json(LOG_A, existing)
                print(f"완료 (반말 잔존: {bm}개)")
            else:
                print("실패")

    total_banmal = sum(count_banmal(r.get("examples", [])) for r in existing.values())
    print(f"\n[PHASE A] 완료. 반말 잔존: {total_banmal}건")
    return existing

# ══════════════════════════════════════════════════════════════
# Phase B: 검증
# ══════════════════════════════════════════════════════════════

VERIFY_SYSTEM = """당신은 TOPIK 한국어 교재 품질 검수 전문가입니다.

[10점 기준 — 모두 충족해야 10점]
1. 모든 한국어 예문이 해요체(-아요/어요/해요/이에요/예요)로 종결 (반말 절대 금지)
2. 문법 오류 없음 (조사, 어미, 활용 완벽)
3. TOPIK 1급 초급 수준 어휘/문법만 사용
4. 예문이 자연스럽고 일상적인 상황을 정확히 반영
5. 영어 번역이 한국어 원문과 정확히 일치하고 자연스러움
6. 일러스트 프롬프트가 단어/예문 핵심 의미를 명확히 시각화
7. 일러스트 프롬프트가 완전한 문장 (잘리거나 미완성 금지)

[감점 기준]
- 반말 1개 = -3점
- 문법 error = -2점
- 문법 warning = -1점
- 번역 부정확 = -1점
- 프롬프트 불완전 = -1점

응답: 단어 수만큼의 JSON 배열
[
  {
    "id": 단어ID(정수),
    "word": "단어",
    "overall_score": 1~10(정수),
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

반드시 valid JSON 배열만 반환. 마크다운 없이."""

def build_verify_prompt(batch_rewrites: list) -> str:
    lines = [f"아래 {len(batch_rewrites)}개 단어를 검수해 주세요.\n"]
    for r in batch_rewrites:
        lines.append(f"=== ID:{r['id']} [{r['word']}] ===")
        lines.append("예문:")
        for i, ex in enumerate(r.get("examples", []), 1):
            lines.append(f"  {i}. KO: {ex['ko']}")
            lines.append(f"     EN: {ex['en']}")
            lines.append(f"     상황: {ex.get('situation','')}")
        lines.append(f"단어프롬프트: {r.get('word_prompt','없음')}")
        for i, sp in enumerate(r.get("sentence_prompts", []), 1):
            lines.append(f"  예문프롬프트{i}: {sp}")
        lines.append("")
    return "\n".join(lines)

def verify_batch(batch_rewrites: list) -> list:
    prompt = build_verify_prompt(batch_rewrites)
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
            return [results]
        except Exception as e:
            print(f"  [retry {attempt+1}] {e}")
            time.sleep(2 ** attempt)
    return [{"id": r["id"], "word": r.get("word","?"), "overall_score": None,
             "issues": [], "summary": "검증 실패"} for r in batch_rewrites]

def phase_b_verify(rewrite_data: dict, log_path: Path) -> dict:
    """Phase B: 재작성 결과 검증"""
    existing = load_json(log_path) or {}
    items = list(rewrite_data.values())
    batches = [items[i:i+BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]
    n_batches = len(batches)

    print(f"\n[VERIFY] {len(items)}개 검증, {n_batches}개 배치")
    print("-" * 60)

    for bi, batch in enumerate(batches, 1):
        todo = [r for r in batch if str(r["id"]) not in existing]
        if not todo:
            print(f"  배치 {bi:03d}/{n_batches} — 스킵")
            continue

        ids = [r["id"] for r in todo]
        print(f"  배치 {bi:03d}/{n_batches} (id {ids[0]}~{ids[-1]}) ... ", end="", flush=True)

        results = verify_batch(todo)
        for vr in results:
            existing[str(vr["id"])] = vr
        save_json(log_path, existing)

        scores = [f"{vr['word']}:{vr.get('overall_score','?')}" for vr in results]
        print(f"완료 [{', '.join(scores)}]")

    return existing

# ══════════════════════════════════════════════════════════════
# Phase C: 재수정
# ══════════════════════════════════════════════════════════════

FIX_SYSTEM = """당신은 TOPIK 한국어 교재 편집 전문가입니다.
검수 이슈를 바탕으로 예문과 프롬프트를 완벽하게 수정하세요.

[절대 규칙]
1. 모든 한국어 예문은 반드시 해요체로만 종결 (-다로 끝나면 즉시 수정)
2. error/warning 이슈는 반드시 수정
3. 수정하지 않는 필드는 원본 그대로 유지
4. TOPIK 1급 초급 수준 어휘/문법만 사용

응답 형식 (JSON):
{
  "id": 단어ID(정수),
  "word": "단어",
  "examples": [
    {"situation": "상황(영어)", "ko": "해요체 예문", "en": "자연스러운 영어 번역"},
    ...
  ],
  "word_prompt": "단어 일러스트 프롬프트(영어)",
  "sentence_prompts": ["예문1 프롬프트(영어)", ...]
}

examples와 sentence_prompts는 원본과 같은 수로 반환.
반드시 valid JSON만 반환. 마크다운 없이."""

def build_fix_prompt(rewrite_entry: dict, verify_result: dict) -> str:
    issues = verify_result.get("issues", [])
    lines = [
        f"단어: {rewrite_entry['word']}",
        f"현재 점수: {verify_result.get('overall_score', '?')}/10",
        "",
        "현재 예문 데이터:",
    ]
    for i, ex in enumerate(rewrite_entry.get("examples", []), 1):
        lines.append(f"  {i}. KO: {ex['ko']}")
        lines.append(f"     EN: {ex['en']}")
        lines.append(f"     상황: {ex.get('situation','')}")
    lines.append(f"\n현재 단어프롬프트: {rewrite_entry.get('word_prompt','없음')}")
    for i, sp in enumerate(rewrite_entry.get("sentence_prompts", []), 1):
        lines.append(f"  예문프롬프트{i}: {sp}")
    lines.append("\n발견된 이슈:")
    for iss in issues:
        sev = iss.get("severity","?").upper()
        typ = iss.get("type","?").upper()
        idx = iss.get("item_index","?")
        desc = iss.get("description","")
        sug = iss.get("suggested","")
        lines.append(f"  [{sev}] {typ} #{idx}: {desc}")
        if sug:
            lines.append(f"    => 개선안: {sug}")

    # 반말 자동 감지 추가
    banmal_found = [(i, ex["ko"]) for i, ex in enumerate(rewrite_entry.get("examples", []), 1)
                    if has_banmal(ex.get("ko",""))]
    if banmal_found:
        lines.append("\n[자동 감지] 반말(-다) 종결 예문 (반드시 해요체로 수정):")
        for idx, ko in banmal_found:
            lines.append(f"  {idx}번: {ko}")

    return "\n".join(lines)

def fix_single(rewrite_entry: dict, verify_result: dict) -> dict | None:
    prompt = build_fix_prompt(rewrite_entry, verify_result)
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

def phase_c_fix(rewrite_data: dict, verify_data: dict, fix_log_path: Path) -> dict:
    """Phase C: 10점 미달 단어 재수정"""
    fix_log = load_json(fix_log_path) or {}

    targets = []
    for wid, vr in verify_data.items():
        score = vr.get("overall_score")
        if score is None or score < 10:
            if wid not in fix_log:
                targets.append(wid)

    total = len(targets)
    print(f"\n[FIX] {total}개 단어 재수정")
    print("-" * 60)

    for idx, wid in enumerate(targets, 1):
        vr = verify_data[wid]
        re_entry = rewrite_data.get(wid)
        if not re_entry:
            continue

        score = vr.get("overall_score", "?")
        n_issues = len(vr.get("issues", []))
        bm = count_banmal(re_entry.get("examples", []))

        print(f"  [{idx:03d}/{total}] {vr['word']} (점수:{score} 이슈:{n_issues} 반말:{bm}) ... ",
              end="", flush=True)

        fixed = fix_single(re_entry, vr)
        if fixed is None:
            print("실패")
            continue

        fix_log[wid] = fixed
        save_json(fix_log_path, fix_log)

        bm_after = count_banmal(fixed.get("examples", []))
        print(f"완료 (반말:{bm_after}개)")

    return fix_log

# ══════════════════════════════════════════════════════════════
# 파일 적용
# ══════════════════════════════════════════════════════════════

def apply_to_files(final_data: dict, prompts_data: dict):
    """최종 데이터를 실제 JSON 파일에 반영"""
    print("\n[APPLY] JSON 파일 반영 중...")

    lang_data = {}
    for lang, path in LANG_FILES.items():
        if path.exists():
            lang_data[lang] = load_json(path)

    prompts_updated = deepcopy(prompts_data)
    count = 0

    for wid, fixed in final_data.items():
        new_examples = fixed.get("examples", [])
        new_word_prompt = fixed.get("word_prompt")
        new_sentence_prompts = fixed.get("sentence_prompts", [])

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
                prompts_updated[wid]["sentences"] = new_sentence_prompts[:len(new_examples)]

        count += 1

    for lang, data in lang_data.items():
        save_json(LANG_FILES[lang], data)
        print(f"  저장: {LANG_FILES[lang].name} ({lang})")

    save_json(PROMPTS_F, prompts_updated)
    print(f"  저장: illustration_prompts.json")
    print(f"  → {count}개 단어 반영 완료")

# ══════════════════════════════════════════════════════════════
# 요약 출력
# ══════════════════════════════════════════════════════════════

def print_summary(verify_data: dict, label: str = ""):
    results = list(verify_data.values())
    scored = [r for r in results if r.get("overall_score") is not None]
    avg = sum(r["overall_score"] for r in scored) / len(scored) if scored else 0
    perfect = sum(1 for r in scored if r["overall_score"] == 10)
    under = [r for r in scored if r["overall_score"] < 10]
    errors   = sum(1 for r in results for i in r.get("issues",[]) if i.get("severity")=="error")
    warnings = sum(1 for r in results for i in r.get("issues",[]) if i.get("severity")=="warning")

    print(f"\n{'='*60}")
    if label:
        print(f"[{label}]")
    print(f"  총 단어     : {len(results)}개")
    print(f"  평균 점수   : {avg:.2f} / 10")
    print(f"  10점 달성   : {perfect}개 ({perfect/len(results)*100:.1f}%)")
    print(f"  10점 미달   : {len(under)}개")
    print(f"  Error 건수  : {errors}")
    print(f"  Warning 건수: {warnings}")

    dist = {}
    for r in scored:
        s = r["overall_score"]
        dist[s] = dist.get(s, 0) + 1
    print(f"  점수 분포:")
    for s in sorted(dist.keys()):
        bar = "#" * dist[s]
        print(f"    {s:2d}점: {bar} ({dist[s]}개)")
    print("=" * 60)
    return perfect == len(results)

# ══════════════════════════════════════════════════════════════
# 메인
# ══════════════════════════════════════════════════════════════

def main():
    topik_data = load_json(LANG_FILES["EN"])
    prompts_data = load_json(PROMPTS_F) or {}
    words = topik_data["words"]  # 300개

    print("=" * 60)
    print("TOPIK Level 1 — 10/10 완성도 달성 프로세스")
    print(f"단어 수: {len(words)}개, 예문 수: {len(words) * len(words[0]['examples'])}개")
    print("=" * 60)

    # ── Phase A: 전체 재작성 ──────────────────────────────────
    rewrite_data = phase_a_rewrite(words, prompts_data)

    # ── Phase B + C 반복 ─────────────────────────────────────
    current_rewrite = rewrite_data  # 초기 재작성 결과

    for round_n in range(1, MAX_ROUNDS + 1):
        log_b_path = LOGS_DIR / f"improve_l1_B{round_n}.json"
        log_c_path = LOGS_DIR / f"improve_l1_C{round_n}.json"

        print(f"\n{'='*60}")
        print(f"[ROUND {round_n}] 검증 + 재수정")
        print(f"{'='*60}")

        # Phase B: 검증
        verify_data = phase_b_verify(current_rewrite, log_b_path)
        all_perfect = print_summary(verify_data, f"Round {round_n} 검증 결과")

        if all_perfect:
            print(f"\n🎉 전체 {len(words)}개 단어 10/10 달성!")
            break

        # Phase C: 재수정
        fix_log = phase_c_fix(current_rewrite, verify_data, log_c_path)

        if not fix_log:
            print("  재수정 대상 없음 (이미 처리됨)")
            break

        # 재수정된 항목을 current_rewrite에 반영
        updated = deepcopy(current_rewrite)
        for wid, fixed in fix_log.items():
            updated[wid] = fixed
        current_rewrite = updated

        # 이미 verify된 항목 초기화 (재검증 위해)
        log_b_path.unlink(missing_ok=True)

    else:
        print(f"\n[완료] {MAX_ROUNDS}라운드 후 최종 결과:")
        # 마지막 라운드 결과 출력
        last_b = LOGS_DIR / f"improve_l1_B{MAX_ROUNDS}.json"
        if last_b.exists():
            print_summary(load_json(last_b), "최종 결과")

    # ── 파일 적용 ─────────────────────────────────────────────
    print("\n최종 결과를 JSON 파일에 반영합니다...")
    apply_to_files(current_rewrite, load_json(PROMPTS_F) or {})

    # ── 최종 반말 통계 ─────────────────────────────────────────
    banmal_total = sum(count_banmal(r.get("examples", [])) for r in current_rewrite.values())
    print(f"\n[최종] 반말 잔존: {banmal_total}건")
    if banmal_total == 0:
        print("✅ 모든 예문이 해요체입니다!")
    else:
        print("⚠️  일부 반말 잔존 — 수동 확인 필요")

if __name__ == "__main__":
    main()
