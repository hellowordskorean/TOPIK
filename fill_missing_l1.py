"""
LOG_A (improve_l1_A.json)에서 누락된 ID들만 재작성하여 채우기
기존 b4bjdfrdq가 메모리에만 있고 LOG_A에 없는 항목들
"""

import json
import os
import re
import sys
import time
import threading
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
LOG_A = LOGS_DIR / "improve_l1_A.json"

BATCH_SIZE = 3
MAX_WORKERS = 3

file_lock = threading.Lock()
print_lock = threading.Lock()

def load_json(path):
    p = Path(path)
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"```\s*$", "", text)
    return json.loads(text.strip())

def safe_print(*args):
    with print_lock:
        print(*args)

REWRITE_SYSTEM = """당신은 TOPIK 한국어 교재 최고 품질 편집 전문가입니다.

[절대 규칙]
1. 모든 한국어 예문은 반드시 해요체로만 종결
   - 동사: -아요/어요/해요  예: 가요, 먹어요
   - 형용사: -아요/어요  예: 좋아요, 비싸요
   - 이다: -이에요/예요
   - 요청: -세요  예: 주세요
   - 과거: -았어요/었어요  예: 갔어요
   - 미래: -ㄹ/을 거예요
2. 절대 금지: 문장을 -다로 끝내지 마세요
3. TOPIK 1급 초급 어휘/문법만 사용
4. 자연스럽고 일상적인 상황의 실제 문장
5. 영어 번역: 정확하고 자연스러운 현대 영어
6. 일러스트 프롬프트: 핵심 개념을 명확히 시각화하는 완전한 영어 설명 문장

응답 형식 (JSON 배열):
[{"id":정수,"word":"단어","examples":[{"situation":"상황(영어)","ko":"해요체 예문","en":"영어 번역"}...],"word_prompt":"단어 일러스트 프롬프트(영어)","sentence_prompts":["예문1 프롬프트(영어)",...]}]

반드시 valid JSON만 반환. 마크다운 없이."""

def rewrite_batch(batch: list, prompts_data: dict, client: anthropic.Anthropic) -> list:
    lines = [f"아래 {len(batch)}개 단어의 예문과 프롬프트를 10점 만점 품질로 재작성하세요.\n"]
    for entry in batch:
        wid = str(entry["id"])
        pe = prompts_data.get(wid, {})
        lines.append(f"--- ID:{entry['id']} [{entry['word']}] ({entry['pos']}) 뜻: {entry['meaning']} ---")
        for i, ex in enumerate(entry["examples"], 1):
            lines.append(f"  {i}. KO: {ex['ko']}")
            lines.append(f"     EN: {ex['en']}")
        lines.append(f"기존 프롬프트: {pe.get('word_prompt','없음')}")
        lines.append("")
    prompt = "\n".join(lines)

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
            return results if isinstance(results, list) else [results]
        except Exception as e:
            safe_print(f"  [retry {attempt+1}] {e}")
            time.sleep(2 ** attempt)
    return []

def worker(todo_batches: list, prompts_data: dict, shared_log: dict, worker_id: int, counter: list, total: int):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    for batch in todo_batches:
        with file_lock:
            still_todo = [w for w in batch if str(w["id"]) not in shared_log]
        if not still_todo:
            with file_lock:
                counter[0] += 1
            continue

        safe_print(f"  [W{worker_id}] id {still_todo[0]['id']}~{still_todo[-1]['id']} 재작성 중...")
        results = rewrite_batch(still_todo, prompts_data, client)
        if not results:
            safe_print(f"  [W{worker_id}] 실패")
            continue

        with file_lock:
            for r in results:
                shared_log[str(r["id"])] = r
            save_json(LOG_A, shared_log)
            counter[0] += 1
        safe_print(f"  [W{worker_id}] 완료 ({counter[0]}/{total})")

def main():
    topik_data = load_json(DATA_DIR / "EN/topik_1.json")
    prompts_data = load_json(PROMPTS_F) or {}
    words = topik_data["words"]

    with file_lock:
        existing = load_json(LOG_A) or {}

    missing_words = [w for w in words if str(w["id"]) not in existing]
    print(f"LOG_A: {len(existing)}개 보유, 누락: {len(missing_words)}개")

    if not missing_words:
        print("모든 단어 처리 완료!")
        return

    batches = [missing_words[i:i+BATCH_SIZE] for i in range(0, len(missing_words), BATCH_SIZE)]
    n_batches = len(batches)
    print(f"처리할 배치: {n_batches}개 ({MAX_WORKERS}개 스레드)")
    print("=" * 60)

    chunks = [[] for _ in range(MAX_WORKERS)]
    for i, batch in enumerate(batches):
        chunks[i % MAX_WORKERS].append(batch)

    counter = [0]
    threads = []
    for wi, chunk in enumerate(chunks):
        if not chunk:
            continue
        t = threading.Thread(target=worker, args=(chunk, prompts_data, existing, wi+1, counter, n_batches))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    with file_lock:
        final = load_json(LOG_A) or {}

    still_missing = [i for i in range(1, 301) if str(i) not in final]
    print(f"\n완료! LOG_A: {len(final)}개, 여전히 누락: {len(still_missing)}개")
    if still_missing:
        print(f"누락 ID: {still_missing[:20]}")

if __name__ == "__main__":
    main()
