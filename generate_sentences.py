#!/usr/bin/env python3
"""
STEP 1: 단어 1800개 예문 일괄 생성
- PDF에서 추출한 단어 목록을 입력으로 받아
- Claude API로 각 단어당 예문 10개 생성
- words_db.json으로 저장
"""

import json
import time
import anthropic
import argparse
from pathlib import Path

client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 환경변수 필요

SYSTEM_PROMPT = """You are a Korean language teacher creating TOPIK study materials.
For each Korean word provided, generate exactly 10 example sentences.
Respond ONLY with valid JSON, no extra text.
Format:
{
  "sentences": [
    {"ko": "Korean sentence", "en": "English translation", "situation": "context keyword"},
    ...
  ]
}

Linguistic rules:
- Sentences should be natural, everyday Korean
- Vary the sentence structure across 10 examples
- English translations should be natural and accurate
- Difficulty appropriate for the TOPIK level given
- Include particles/grammar naturally

Visual friendliness rules (important — sentences are illustrated):
- Each sentence must describe ONE clear action with a concrete, identifiable subject
- Include at least one concrete noun that can be depicted visually
- Prefer action sentences (someone doing something) over abstract state sentences
- Avoid sentences that primarily describe spoken communication ("I said...", "She told...")
- Avoid heavily abstract sentences with no visual anchor ("Life is precious")
- Favor physical actions, visible emotions, and spatial relationships

situation field: choose ONE keyword from this list that best fits the sentence context:
home, kitchen, school, office, work, restaurant, cafe, shopping, market,
hospital, bank, post, airport, hotel, travel, park, gym, transport,
subway, bus, phone, family, friend, weather, library, general
"""

# ── 시각화 친화성 검증/수정 프롬프트 ───────────────────────────
VISUAL_SCORE_SYSTEM = """You are evaluating Korean example sentences for visual depictability.
Score each sentence 1-5 based on how easily an AI can draw it as a single illustration.

5 = Perfect: one clear action, concrete noun, specific setting (e.g., "She placed apples in a basket")
4 = Good: clear scene with minor abstraction
3 = Acceptable: depictable with some interpretation
2 = Poor: abstract, no visual anchor, or primarily dialogue/thought
1 = Fail: cannot be illustrated (pure abstraction, complex internal state)

Respond ONLY with valid JSON:
{"scores": [{"index": 0, "score": 5, "issue": null}, {"index": 1, "score": 2, "issue": "no concrete action"}, ...]}"""

VISUAL_FIX_SYSTEM = """Replace this Korean example sentence with a more visually concrete version.
Keep the same target word, similar TOPIK difficulty level, and natural Korean.

Requirements:
- One clear action: concrete subject + visible verb + specific object or setting
- The target word must appear naturally in the sentence
- Avoid dialogue-only sentences and pure abstract states
- Include a physical action or visible emotion

Return ONLY valid JSON:
{"ko": "Korean sentence", "en": "English translation", "situation": "keyword"}"""


def _claude_call(system: str, user: str, max_tokens: int = 800) -> str | None:
    """Claude API 단순 호출 래퍼"""
    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"    API 오류: {e}")
        return None


def score_visual_friendliness(word: dict, sentences: list) -> list:
    """예문 10개의 시각화 친화성 점수 반환"""
    sents_text = "\n".join(
        f"  {i}. [{s.get('situation','general')}] {s['ko']} ({s['en']})"
        for i, s in enumerate(sentences)
    )
    user_msg = f"""Word: {word['word']} ({word['meaning']}, {word['part_of_speech']}, TOPIK {word['level']})

Sentences to evaluate:
{sents_text}

Score each sentence 1-5 for visual depictability."""

    text = _claude_call(VISUAL_SCORE_SYSTEM, user_msg, max_tokens=600)
    if not text:
        return []
    try:
        # JSON 파싱
        if text.startswith("```"):
            text = text[text.index("\n") + 1:]
            if text.endswith("```"):
                text = text[:-3].strip()
        return json.loads(text).get("scores", [])
    except Exception:
        return []


def fix_visual_sentence(word: dict, sentence: dict, issue: str) -> dict | None:
    """시각화 점수 낮은 예문을 더 구체적인 버전으로 교체"""
    user_msg = f"""Word: {word['word']} ({word['meaning']}, {word['part_of_speech']}, TOPIK {word['level']})
Original sentence: {sentence['ko']} ({sentence['en']})
Issue: {issue or 'not visually concrete'}

Generate a better replacement sentence."""

    text = _claude_call(VISUAL_FIX_SYSTEM, user_msg, max_tokens=200)
    if not text:
        return None
    try:
        if text.startswith("```"):
            text = text[text.index("\n") + 1:]
            if text.endswith("```"):
                text = text[:-3].strip()
        result = json.loads(text)
        if "situation" not in result:
            result["situation"] = sentence.get("situation", "general")
        return result
    except Exception:
        return None


def verify_and_fix_word(word: dict, threshold: int = 3) -> tuple[list, int]:
    """단어의 예문을 검증하고 threshold 미만 예문을 수정. (fixed_sentences, fix_count) 반환"""
    sentences = word.get("sentences", [])
    if not sentences:
        return sentences, 0

    scores = score_visual_friendliness(word, sentences)
    if not scores:
        return sentences, 0

    fixed = list(sentences)
    fix_count = 0

    for item in scores:
        idx = item.get("index", -1)
        score = item.get("score", 5)
        issue = item.get("issue") or ""
        if 0 <= idx < len(fixed) and score < threshold:
            replacement = fix_visual_sentence(word, fixed[idx], issue)
            if replacement:
                fixed[idx] = replacement
                fix_count += 1
                print(f"    [{idx}] score={score} → 교체: {replacement['ko'][:40]}")
            else:
                print(f"    [{idx}] score={score} 교체 실패 (유지)")

    return fixed, fix_count


def generate_sentences(word: dict) -> list:
    """단어 하나에 대한 예문 10개 생성"""
    prompt = f"""Generate 10 example sentences for this Korean word:
Word: {word['word']}
Meaning: {word['meaning']}
Part of speech: {word['part_of_speech']}
TOPIK Level: {word['level']}
Romanization: {word['romanization']}
"""
    
    for attempt in range(3):
        try:
            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=1500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text.strip()
            # JSON 파싱
            data = json.loads(text)
            sentences = data["sentences"][:10]
            # situation 필드 누락 시 기본값 보완
            for s in sentences:
                if "situation" not in s:
                    s["situation"] = "general"
            return sentences
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    
    return []

def process_words(input_file: str, output_file: str, start_id: int = 1, end_id: int = 9999):
    """단어 파일 처리"""
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    # 기존 진행상황 로드
    if output_path.exists():
        with open(output_path) as f:
            db = json.load(f)
        done_ids = {w["id"] for w in db}
        print(f"기존 완료: {len(done_ids)}개")
    else:
        db = []
        done_ids = set()
    
    # 입력 단어 로드
    with open(input_path) as f:
        words = json.load(f)
    
    # 범위 필터
    words = [w for w in words if start_id <= w["id"] <= end_id and w["id"] not in done_ids]
    print(f"처리할 단어: {len(words)}개")
    
    for i, word in enumerate(words):
        print(f"[{i+1}/{len(words)}] {word['word']} ({word['meaning']}) 처리 중...")
        
        sentences = generate_sentences(word)
        if sentences:
            word["sentences"] = sentences
            db.append(word)
            print(f"  ✓ 예문 {len(sentences)}개 생성 완료")
        else:
            print(f"  ✗ 실패 - 스킵")
        
        # 10개마다 저장 (중간 저장)
        if (i + 1) % 10 == 0:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
            print(f"  → 중간 저장 완료 ({len(db)}개)")
        
        # API 레이트 리밋 방지
        time.sleep(0.5)
    
    # 최종 저장
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"\n완료! 총 {len(db)}개 저장: {output_path}")


def verify_process(db_file: str, start_id: int, end_id: int,
                   threshold: int = 3, batch_save: int = 20):
    """3순위 harness: 기존 words_db.json 예문 시각화 친화성 검증 + 수정"""
    db_path = Path(db_file)
    with open(db_path, encoding="utf-8") as f:
        db = json.load(f)

    words = [w for w in db if start_id <= w["id"] <= end_id and w.get("sentences")]
    print(f"검증 대상: {len(words)}개 단어 (threshold={threshold})\n{'━'*50}")

    total_fixed = 0
    modified_ids = set()

    for i, word in enumerate(words):
        print(f"[{i+1}/{len(words)}] {word['word']} ({word['meaning']})")
        fixed_sents, fix_count = verify_and_fix_word(word, threshold=threshold)

        if fix_count > 0:
            word["sentences"] = fixed_sents
            modified_ids.add(word["id"])
            total_fixed += fix_count
            print(f"  → {fix_count}개 교체")
        else:
            print(f"  → 전부 통과")

        # 주기적 저장
        if (i + 1) % batch_save == 0:
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
            print(f"\n  ── 중간 저장 ({i+1}/{len(words)}) ──\n")

        time.sleep(0.3)

    # 최종 저장
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"\n{'━'*50}")
    print(f"  완료! 교체된 예문: {total_fixed}개 ({len(modified_ids)}개 단어)")
    print(f"  저장: {db_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TOPIK 단어 예문 생성 + 시각화 검증")
    parser.add_argument("--input",  default="../data/LanguageTest/words_input.json")
    parser.add_argument("--output", default="../data/LanguageTest/words_db.json")
    parser.add_argument("--start",  type=int, default=1)
    parser.add_argument("--end",    type=int, default=9999)
    # 3순위 harness: 기존 예문 시각화 친화성 검증
    parser.add_argument("--verify", action="store_true",
                        help="신규 생성 없이 기존 words_db 예문 시각화 검증 + 수정")
    parser.add_argument("--threshold", type=int, default=3,
                        help="시각화 점수 기준 (1-5, 기본 3). 미만이면 교체")
    parser.add_argument("--batch-save", type=int, default=20,
                        help="N개마다 중간 저장 (기본 20)")
    args = parser.parse_args()

    if args.verify:
        verify_process(args.output, args.start, args.end, args.threshold, args.batch_save)
    else:
        process_words(args.input, args.output, args.start, args.end)
