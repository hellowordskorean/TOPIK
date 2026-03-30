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
    {"ko": "Korean sentence", "en": "English translation"},
    ...
  ]
}

Rules:
- Sentences should be natural, everyday Korean
- Vary the sentence structure across 10 examples
- English translations should be natural and accurate
- Difficulty appropriate for the TOPIK level given
- Include particles/grammar naturally
"""

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
            return data["sentences"][:10]
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TOPIK 단어 예문 생성")
    parser.add_argument("--input", default="data/LanguageTest/words_input.json", help="입력 단어 JSON 파일")
    parser.add_argument("--output", default="data/LanguageTest/words_db.json", help="출력 DB JSON 파일")
    parser.add_argument("--start", type=int, default=1, help="시작 ID")
    parser.add_argument("--end", type=int, default=9999, help="종료 ID")
    args = parser.parse_args()
    
    process_words(args.input, args.output, args.start, args.end)
