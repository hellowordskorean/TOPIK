"""
TOPIK Level 1 — 최종 품질 검증 (topik_1.json 직접 검증)

improve_l1_parallel.py가 완료된 후 실행하여 최종 결과를 확인합니다.
"""

import json
import os
import re
import sys
import time
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
LOG_FINAL = LOGS_DIR / "final_verify_l1.json"

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

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
    s = re.sub(r'[\.\!\?]?\s*$', '', sentence)
    if not s.endswith('다'):
        return False
    # ㅂ시다 청유형 / ㅂ니다 합쇼체: 앞 음절이 ㅂ받침이면 정중체 (예: 건넙시다, 엽니다)
    for suffix in ('시다', '니다'):
        if s.endswith(suffix) and len(s) >= 3:
            char_before = s[-(len(suffix)+1)]
            if ord(char_before) >= 0xAC00 and (ord(char_before) - 0xAC00) % 28 == 17:
                return False
    polite = re.search(
        r'(아요|어요|해요|예요|이에요|세요|ㄹ게요|겠어요|주세요|해주세요|드세요'
        r'|읍시다|합시다|ㄹ까요|을까요|ㄴ가요|는가요'
        r'|합니다|입니다|습니다|겠습니다|하십시오|드립니다|주십시오'
        r'|드릴까요|해드릴까요)[\.\!\?]?\s*$',
        sentence
    )
    return not polite

VERIFY_SYSTEM = """당신은 TOPIK 한국어 교재 품질 검수 전문가입니다.

[10점 기준]
1. 모든 한국어 예문이 해요체로 종결 (반말 절대 금지)
2. 문법 오류 없음
3. TOPIK 1급 초급 수준 어휘/문법만 사용
4. 예문이 자연스럽고 일상적인 상황 반영
5. 영어 번역이 한국어 원문과 정확히 일치하고 자연스러움
6. 일러스트 프롬프트가 단어/예문 핵심 의미를 명확히 시각화
7. 일러스트 프롬프트가 완전한 문장

응답: JSON 배열
[{"id":정수, "word":"단어", "overall_score":1~10, "issues":[...], "summary":"한줄요약"}]
반드시 valid JSON만 반환. 마크다운 없이."""

def verify_batch(batch: list, prompts_data: dict) -> list:
    lines = [f"아래 {len(batch)}개 단어를 검수해 주세요.\n"]
    for w in batch:
        wid = str(w["id"])
        pe = prompts_data.get(wid, {})
        lines.append(f"=== ID:{w['id']} [{w['word']}] ({w['pos']}) 뜻: {w['meaning']} ===")
        for i, ex in enumerate(w["examples"], 1):
            lines.append(f"  {i}. KO: {ex['ko']}")
            lines.append(f"     EN: {ex['en']}")
        lines.append(f"단어프롬프트: {pe.get('word_prompt','없음')}")
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
    return [{"id": w["id"], "word": w["word"], "overall_score": None, "issues": [], "summary": "검증 실패"} for w in batch]

def main():
    topik_data = load_json(DATA_DIR / "EN/topik_1.json")
    prompts_data = load_json(PROMPTS_F) or {}
    words = topik_data["words"]

    # 반말 통계
    banmal = sum(1 for w in words for ex in w["examples"] if has_banmal(ex.get("ko","")))
    print(f"\n[TOPIK Level 1 최종 검증]")
    print(f"단어: {len(words)}개, 반말 잔존: {banmal}건")
    print("=" * 60)

    existing = load_json(LOG_FINAL) or {}
    batches = [words[i:i+5] for i in range(0, len(words), 5)]
    n_batches = len(batches)

    print(f"\n[검증 중] {n_batches}개 배치...")
    for bi, batch in enumerate(batches, 1):
        todo = [w for w in batch if str(w["id"]) not in existing]
        if not todo:
            print(f"  배치 {bi:03d}/{n_batches} — 스킵", end="\r")
            continue

        ids = [w["id"] for w in todo]
        print(f"  배치 {bi:03d}/{n_batches} (id {ids[0]}~{ids[-1]}) ... ", end="", flush=True)

        results = verify_batch(todo, prompts_data)
        for r in results:
            existing[str(r["id"])] = r
        save_json(LOG_FINAL, existing)

        scores = [f"{r['word']}:{r.get('overall_score','?')}" for r in results]
        print(f"완료 [{', '.join(scores)}]")

    # 요약
    results = list(existing.values())
    scored = [r for r in results if r.get("overall_score") is not None]
    avg = sum(r["overall_score"] for r in scored) / len(scored) if scored else 0
    perfect = sum(1 for r in scored if r["overall_score"] == 10)
    under = sorted([r for r in scored if r["overall_score"] < 10], key=lambda x: x["overall_score"])

    dist = {}
    for r in scored:
        s = r["overall_score"]
        dist[s] = dist.get(s, 0) + 1

    print(f"\n{'='*60}")
    print(f"[최종 검증 결과]")
    print(f"  총 단어     : {len(results)}개")
    print(f"  평균 점수   : {avg:.2f} / 10")
    print(f"  10점 달성   : {perfect}개 ({perfect/len(results)*100:.1f}%)")
    print(f"  반말 잔존   : {banmal}건")
    print(f"  점수 분포:")
    for s in sorted(dist.keys()):
        bar = "#" * dist[s]
        print(f"    {s:2d}점: {bar} ({dist[s]}개)")

    if under:
        print(f"\n  10점 미달 단어 ({len(under)}개):")
        for r in under[:20]:
            print(f"    [{r['overall_score']}] {r['word']}: {r.get('summary','')[:60]}")

    print("=" * 60)

if __name__ == "__main__":
    main()
