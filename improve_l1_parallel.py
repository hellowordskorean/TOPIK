"""
TOPIK Level 1 — 병렬 처리 버전 (3 concurrent threads)

improve_l1_A.json 재활용 (기존 완료 항목 스킵)
Phase A: 병렬 재작성 (3개 스레드 × 3단어 배치)
Phase B: 검증
Phase C: 재수정
Phase D: B-C 반복 (최대 3라운드)
"""

import json
import os
import re
import sys
import time
import threading
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

BATCH_SIZE   = 3   # 단어/배치 (작게 유지해서 응답 안정화)
MAX_WORKERS  = 4   # 동시 스레드 수
MAX_ROUNDS   = 3

# 파일 접근 락
file_lock = threading.Lock()
print_lock = threading.Lock()

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
    """반말(-다) 종결 감지 — 합니다/입니다/ㅂ시다/ㅂ니다 형식은 제외"""
    s = re.sub(r'[\.\!\?]?\s*$', '', sentence)
    if not s.endswith('다'):
        return False
    # ㅂ시다 청유형 / ㅂ니다 합쇼체: 앞 음절이 ㅂ받침이면 정중체 (예: 건넙시다, 엽니다)
    for suffix in ('시다', '니다'):
        if s.endswith(suffix) and len(s) >= 3:
            char_before = s[-(len(suffix)+1)]
            if ord(char_before) >= 0xAC00 and (ord(char_before) - 0xAC00) % 28 == 17:
                return False
    # 해요체 / 합쇼체 / 청유형 예외
    polite = re.search(
        r'(아요|어요|해요|예요|이에요|세요|ㄹ게요|겠어요|주세요|해주세요|드세요'
        r'|읍시다|합시다|ㄹ까요|을까요|ㄴ가요|는가요'
        r'|합니다|입니다|습니다|겠습니다|하십시오|드립니다|주십시오'
        r'|드릴까요|해드릴까요|ㄹ게요)[\.\!\?]?\s*$',
        sentence
    )
    return not polite

def count_banmal(examples: list) -> int:
    return sum(1 for ex in examples if has_banmal(ex.get("ko", "")))

def safe_print(*args):
    with print_lock:
        print(*args)

# ══════════════════════════════════════════════════════════════
# Phase A: 병렬 재작성
# ══════════════════════════════════════════════════════════════

REWRITE_SYSTEM = """당신은 TOPIK 한국어 교재 최고 품질 편집 전문가입니다.

[절대 규칙 — 위반 시 10점 불가]
1. 모든 한국어 예문은 반드시 해요체로만 종결
   - 동사: -아요/어요/해요  (예: 가요, 먹어요, 공부해요)
   - 형용사: -아요/어요  (예: 좋아요, 비싸요, 작아요)
   - 이다: -이에요/예요  (예: 학생이에요, 가게예요)
   - 요청/청유: -세요/-ㅂ시다/-ㄹ까요  (예: 주세요, 갑시다, 할까요)
   - 미래: -ㄹ/을 거예요/-겠어요  (예: 갈 거예요)
   - 과거: -았어요/었어요/했어요  (예: 갔어요, 먹었어요)
2. 절대 금지: 문장을 -다로 끝내지 마세요
   (좋다→좋아요, 먹는다→먹어요, 비싸다→비싸요, 있다→있어요, 없다→없어요)
3. TOPIK 1급 초급 어휘/문법만 사용
4. 자연스럽고 일상적인 상황의 실제 문장
5. 영어 번역: 정확하고 자연스러운 현대 영어
6. 일러스트 프롬프트: 핵심 개념을 명확히 시각화하는 완전한 영어 설명 문장

응답 형식 (JSON 배열 — 입력 단어 수와 동일):
[
  {
    "id": 단어ID(정수),
    "word": "단어",
    "examples": [
      {"situation": "상황(영어)", "ko": "해요체 예문", "en": "자연스러운 영어 번역"},
      ...
    ],
    "word_prompt": "단어 핵심 개념 일러스트 프롬프트(영어 완전 문장)",
    "sentence_prompts": ["예문1 상황 프롬프트(영어)", ...]
  }
]

반드시 valid JSON 배열만 반환. 마크다운 없이."""

def build_rewrite_prompt(batch: list, prompts_data: dict) -> str:
    lines = [f"아래 {len(batch)}개 단어의 예문과 프롬프트를 10점 만점 품질로 완전히 재작성하세요.\n"]
    for entry in batch:
        wid = str(entry["id"])
        pe = prompts_data.get(wid, {})
        lines.append(f"--- ID:{entry['id']} [{entry['word']}] ({entry['pos']}) 뜻: {entry['meaning']} ---")
        lines.append("기존 예문 (참고, 완전히 개선 가능):")
        for i, ex in enumerate(entry["examples"], 1):
            lines.append(f"  {i}. KO: {ex['ko']}")
            lines.append(f"     EN: {ex['en']}")
        lines.append(f"기존 단어프롬프트: {pe.get('word_prompt','없음')}")
        lines.append("")
    return "\n".join(lines)

def rewrite_batch_worker(batch: list, prompts_data: dict, client: anthropic.Anthropic) -> list:
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
            safe_print(f"  [retry {attempt+1}] {e}")
            time.sleep(2 ** attempt)
    return []

def worker_thread(todo_batches: list, prompts_data: dict, shared_log: dict,
                  worker_id: int, total_batches: int, done_counter: list):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    for batch in todo_batches:
        ids = [w["id"] for w in batch]

        # 이미 처리된 배치인지 재확인
        with file_lock:
            still_todo = [w for w in batch if str(w["id"]) not in shared_log]

        if not still_todo:
            with file_lock:
                done_counter[0] += 1
            safe_print(f"  [W{worker_id}] id {ids[0]}~{ids[-1]} 스킵")
            continue

        safe_print(f"  [W{worker_id}] id {still_todo[0]['id']}~{still_todo[-1]['id']} 재작성 중...")

        results = rewrite_batch_worker(still_todo, prompts_data, client)

        if not results:
            safe_print(f"  [W{worker_id}] 실패 — id {still_todo[0]['id']}~{still_todo[-1]['id']}")
            continue

        banmal_warns = []
        with file_lock:
            for r in results:
                wid = str(r["id"])
                bm = count_banmal(r.get("examples", []))
                if bm > 0:
                    banmal_warns.append(f"{r['word']}:{bm}")
                shared_log[wid] = r
            save_json(LOG_A, shared_log)
            done_counter[0] += 1

        warn_str = f" [반말:{', '.join(banmal_warns)}]" if banmal_warns else ""
        safe_print(f"  [W{worker_id}] 완료{warn_str} ({done_counter[0]}/{total_batches})")

def phase_a_parallel(words: list, prompts_data: dict) -> dict:
    """Phase A: 병렬 재작성"""
    with file_lock:
        existing = load_json(LOG_A) or {}

    total = len(words)
    batches = [words[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    n_batches = len(batches)

    todo_batches = [b for b in batches if any(str(w["id"]) not in existing for w in b)]
    done_batches = n_batches - len(todo_batches)

    print(f"\n[PHASE A] 병렬 재작성: {total}개 단어")
    print(f"  이미 완료: {done_batches}배치, 남은: {len(todo_batches)}배치")
    print(f"  동시 스레드: {MAX_WORKERS}개")
    print("=" * 60)

    if not todo_batches:
        print("  모두 완료됨 — 스킵")
        return existing

    # 배치를 스레드별로 분배
    chunks = [[] for _ in range(MAX_WORKERS)]
    for i, batch in enumerate(todo_batches):
        chunks[i % MAX_WORKERS].append(batch)

    done_counter = [done_batches]
    threads = []

    for wi, chunk in enumerate(chunks):
        if not chunk:
            continue
        t = threading.Thread(
            target=worker_thread,
            args=(chunk, prompts_data, existing, wi+1, n_batches, done_counter)
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # 반말 잔존 항목 순차 재처리
    with file_lock:
        final = load_json(LOG_A) or {}

    banmal_ids = [wid for wid, r in final.items()
                  if int(wid) <= 300 and count_banmal(r.get("examples", [])) > 0]
    if banmal_ids:
        print(f"\n  [반말 재수정] {len(banmal_ids)}개 항목 재처리...")
        word_map = {str(w["id"]): w for w in words}
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        for wid in banmal_ids:
            w = word_map.get(wid)
            if not w:
                continue
            print(f"    [{w['word']}] 반말 재수정 ... ", end="", flush=True)
            results = rewrite_batch_worker([w], prompts_data, client)
            if results:
                r = results[0]
                bm = count_banmal(r.get("examples", []))
                with file_lock:
                    final[wid] = r
                    save_json(LOG_A, final)
                print(f"완료 (반말:{bm}개)")
            else:
                print("실패")

    with file_lock:
        final = load_json(LOG_A) or {}

    total_banmal = sum(
        count_banmal(final[k].get("examples", []))
        for k in final if int(k) <= 300
    )
    print(f"\n[PHASE A] 완료. 처리: {len(final)}개 단어, 반말 잔존: {total_banmal}건")
    return final

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

응답: JSON 배열
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

def verify_batch_api(batch_rewrites: list, client: anthropic.Anthropic) -> list:
    lines = [f"아래 {len(batch_rewrites)}개 단어를 검수해 주세요.\n"]
    for r in batch_rewrites:
        lines.append(f"=== ID:{r['id']} [{r['word']}] ===")
        for i, ex in enumerate(r.get("examples", []), 1):
            lines.append(f"  {i}. KO: {ex['ko']}")
            lines.append(f"     EN: {ex['en']}")
        lines.append(f"단어프롬프트: {r.get('word_prompt','없음')}")
        for i, sp in enumerate(r.get("sentence_prompts", []), 1):
            lines.append(f"  예문프롬프트{i}: {sp}")
        lines.append("")
    prompt = "\n".join(lines)

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
            return results if isinstance(results, list) else [results]
        except Exception as e:
            print(f"  [retry {attempt+1}] {e}")
            time.sleep(2 ** attempt)
    return [{"id": r["id"], "word": r.get("word","?"), "overall_score": None,
             "issues": [], "summary": "검증 실패"} for r in batch_rewrites]

def verify_worker(batches: list, verify_log: dict, worker_id: int,
                  done_counter: list, total: int):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    for batch in batches:
        with file_lock:
            todo = [r for r in batch if str(r["id"]) not in verify_log]
        if not todo:
            continue

        results = verify_batch_api(todo, client)

        with file_lock:
            for vr in results:
                verify_log[str(vr["id"])] = vr
            done_counter[0] += 1

        scores = [f"{vr['word']}:{vr.get('overall_score','?')}" for vr in results]
        safe_print(f"  [W{worker_id}] 검증 완료 [{', '.join(scores)}]")

def phase_b_verify_parallel(rewrite_data: dict, log_path: Path) -> dict:
    with file_lock:
        existing = load_json(log_path) or {}

    items = list(rewrite_data.values())
    batches = [items[i:i+5] for i in range(0, len(items), 5)]
    todo_batches = [b for b in batches if any(str(r["id"]) not in existing for r in b)]

    print(f"\n[VERIFY] {len(items)}개 검증, 남은: {len(todo_batches)}배치")
    print("-" * 60)

    if not todo_batches:
        print("  모두 완료됨")
        return existing

    chunks = [[] for _ in range(MAX_WORKERS)]
    for i, batch in enumerate(todo_batches):
        chunks[i % MAX_WORKERS].append(batch)

    done_counter = [0]
    threads = []
    for wi, chunk in enumerate(chunks):
        if not chunk:
            continue
        t = threading.Thread(
            target=verify_worker,
            args=(chunk, existing, wi+1, done_counter, len(todo_batches))
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    with file_lock:
        save_json(log_path, existing)

    return existing

# ══════════════════════════════════════════════════════════════
# Phase C: 재수정
# ══════════════════════════════════════════════════════════════

FIX_SYSTEM = """당신은 TOPIK 한국어 교재 편집 전문가입니다.

[절대 규칙]
1. 모든 한국어 예문은 반드시 해요체로만 종결 (-다로 끝나면 즉시 수정)
2. error/warning 이슈는 반드시 수정
3. TOPIK 1급 초급 수준 어휘/문법만 사용

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

def fix_single_api(rewrite_entry: dict, verify_result: dict, client: anthropic.Anthropic) -> dict | None:
    issues = verify_result.get("issues", [])
    banmal_found = [(i, ex["ko"]) for i, ex in enumerate(rewrite_entry.get("examples", []), 1)
                    if has_banmal(ex.get("ko",""))]

    lines = [
        f"단어: {rewrite_entry['word']} (현재 점수: {verify_result.get('overall_score','?')}/10)",
        "",
        "현재 예문:",
    ]
    for i, ex in enumerate(rewrite_entry.get("examples", []), 1):
        lines.append(f"  {i}. KO: {ex['ko']}")
        lines.append(f"     EN: {ex['en']}")
        lines.append(f"     상황: {ex.get('situation','')}")

    lines.append(f"\n단어프롬프트: {rewrite_entry.get('word_prompt','없음')}")
    for i, sp in enumerate(rewrite_entry.get("sentence_prompts", []), 1):
        lines.append(f"  예문프롬프트{i}: {sp}")

    if issues:
        lines.append("\n발견된 이슈:")
        for iss in issues:
            sev = iss.get("severity","?").upper()
            typ = iss.get("type","?").upper()
            desc = iss.get("description","")
            sug = iss.get("suggested","")
            lines.append(f"  [{sev}] {typ}: {desc}")
            if sug:
                lines.append(f"    => 개선안: {sug}")

    if banmal_found:
        lines.append("\n[자동 감지] 반말(-다) 종결 예문 — 반드시 해요체로 수정:")
        for idx, ko in banmal_found:
            lines.append(f"  {idx}번: {ko}")

    prompt = "\n".join(lines)

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

def fix_worker(targets: list, rewrite_data: dict, verify_data: dict,
               fix_log: dict, fix_log_path: Path, worker_id: int, done_counter: list, total: int):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    for wid in targets:
        vr = verify_data[wid]
        re_entry = rewrite_data.get(wid)
        if not re_entry:
            continue

        fixed = fix_single_api(re_entry, vr, client)

        with file_lock:
            done_counter[0] += 1
            if fixed:
                fix_log[wid] = fixed
                save_json(fix_log_path, fix_log)

        bm = count_banmal(fixed.get("examples", [])) if fixed else -1
        score = vr.get("overall_score", "?")
        safe_print(f"  [W{worker_id}] {vr['word']} (점수:{score}→?) 반말:{bm} [{done_counter[0]}/{total}]")

def phase_c_fix_parallel(rewrite_data: dict, verify_data: dict, fix_log_path: Path) -> dict:
    with file_lock:
        fix_log = load_json(fix_log_path) or {}

    targets = [wid for wid, vr in verify_data.items()
               if (vr.get("overall_score") or 0) < 10 and wid not in fix_log]
    total = len(targets)

    print(f"\n[FIX] {total}개 단어 재수정 (병렬)")
    print("-" * 60)

    if not targets:
        print("  재수정 대상 없음")
        return fix_log

    chunks = [[] for _ in range(MAX_WORKERS)]
    for i, wid in enumerate(targets):
        chunks[i % MAX_WORKERS].append(wid)

    done_counter = [0]
    threads = []
    for wi, chunk in enumerate(chunks):
        if not chunk:
            continue
        t = threading.Thread(
            target=fix_worker,
            args=(chunk, rewrite_data, verify_data, fix_log, fix_log_path, wi+1, done_counter, total)
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    with file_lock:
        return load_json(fix_log_path) or {}

# ══════════════════════════════════════════════════════════════
# 파일 적용
# ══════════════════════════════════════════════════════════════

def apply_to_files(final_data: dict, prompts_data: dict):
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
                n = len(new_examples)
                prompts_updated[wid]["sentences"] = new_sentence_prompts[:n]

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

def print_summary(verify_data: dict, label: str = "") -> bool:
    results = list(verify_data.values())
    scored = [r for r in results if r.get("overall_score") is not None]
    if not scored:
        print("  (검증 결과 없음)")
        return False

    avg = sum(r["overall_score"] for r in scored) / len(scored)
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
        print(f"    {s:2d}점: {'#'*dist[s]} ({dist[s]}개)")
    print("=" * 60)
    return perfect == len(results)

# ══════════════════════════════════════════════════════════════
# 메인
# ══════════════════════════════════════════════════════════════

def main():
    topik_data = load_json(LANG_FILES["EN"])
    prompts_data = load_json(PROMPTS_F) or {}
    words = topik_data["words"]

    print("=" * 60)
    print("TOPIK Level 1 — 병렬 처리 10/10 달성")
    print(f"단어 수: {len(words)}개 | 스레드: {MAX_WORKERS}개 | 배치: {BATCH_SIZE}개/배치")
    print("=" * 60)

    # ── Phase A: 병렬 재작성 ──────────────────────────────────
    rewrite_data = phase_a_parallel(words, prompts_data)

    # ── Phase B + C 반복 ─────────────────────────────────────
    current_rewrite = rewrite_data

    for round_n in range(1, MAX_ROUNDS + 1):
        log_b_path = LOGS_DIR / f"improve_l1_B{round_n}.json"
        log_c_path = LOGS_DIR / f"improve_l1_C{round_n}.json"

        print(f"\n{'='*60}")
        print(f"[ROUND {round_n}] 검증 + 재수정")
        print(f"{'='*60}")

        # Phase B: 검증 (로그 초기화해서 재검증)
        if log_b_path.exists():
            log_b_path.unlink()

        verify_data = phase_b_verify_parallel(current_rewrite, log_b_path)
        all_perfect = print_summary(verify_data, f"Round {round_n} 검증 결과")

        if all_perfect:
            print(f"\n전체 {len(words)}개 단어 10/10 달성!")
            break

        # Phase C: 병렬 재수정
        fix_log = phase_c_fix_parallel(current_rewrite, verify_data, log_c_path)

        if not fix_log:
            print("  재수정 대상 없음")
            break

        # current_rewrite 업데이트
        updated = deepcopy(current_rewrite)
        for wid, fixed in fix_log.items():
            updated[wid] = fixed
        current_rewrite = updated

    else:
        print(f"\n{MAX_ROUNDS}라운드 완료 — 최종 결과:")
        last_b = LOGS_DIR / f"improve_l1_B{MAX_ROUNDS}.json"
        if last_b.exists():
            print_summary(load_json(last_b), "최종 결과")

    # ── 파일 적용 ─────────────────────────────────────────────
    print("\n최종 결과를 JSON 파일에 반영합니다...")
    apply_to_files(current_rewrite, load_json(PROMPTS_F) or {})

    # ── 최종 반말 통계 ─────────────────────────────────────────
    banmal_total = sum(
        count_banmal(current_rewrite[k].get("examples", []))
        for k in current_rewrite if int(k) <= 300
    )
    print(f"\n[최종] 반말 잔존: {banmal_total}건")
    if banmal_total == 0:
        print("모든 예문이 해요체입니다!")
    else:
        print("일부 반말 잔존 — 수동 확인 필요")

if __name__ == "__main__":
    main()
