#!/usr/bin/env python3
"""
데이터 변환: data/TOPIK/EN/*.json → data/words_db.json
- make_video.py / upload_youtube.py 가 기대하는 형식으로 변환
- romanization 자동 생성 (Revised Romanization 간략 버전)

실행: python3 prepare_db.py
"""

import json
from pathlib import Path

# ─── 한국어 로마자 변환 (Revised Romanization) ─────────────────

CHOSEONG = [
    'g', 'kk', 'n', 'd', 'tt', 'r', 'm', 'b', 'pp',
    's', 'ss', '', 'j', 'jj', 'ch', 'k', 't', 'p', 'h'
]
JUNGSEONG = [
    'a', 'ae', 'ya', 'yae', 'eo', 'e', 'yeo', 'ye', 'o',
    'wa', 'wae', 'oe', 'yo', 'u', 'wo', 'we', 'wi', 'yu', 'eu', 'ui', 'i'
]
JONGSEONG = [
    '', 'k', 'k', 'k', 'n', 'n', 'n', 't', 'l', 'k', 'm',
    'l', 'l', 'l', 'p', 'l', 'm', 'p', 'p', 't', 't',
    'ng', 't', 't', 'k', 't', 'p', 't'
]

def romanize(text: str) -> str:
    """한국어 단어 → 로마자 변환 (표시용)"""
    result = []
    for char in text:
        code = ord(char)
        if 0xAC00 <= code <= 0xD7A3:
            syllable = code - 0xAC00
            jong = syllable % 28
            syllable //= 28
            jung = syllable % 21
            cho = syllable // 21
            result.append(CHOSEONG[cho] + JUNGSEONG[jung] + JONGSEONG[jong])
        elif char == ' ':
            result.append('-')
        else:
            result.append(char.lower())
    return ''.join(result)


# ─── 변환 ──────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data' / 'LanguageTest' / 'TOPIK' / 'EN'
OUTPUT_PATH = BASE_DIR / 'data' / 'LanguageTest' / 'words_db.json'


def main():
    all_words = []
    global_id = 1

    for level in range(1, 7):
        filepath = DATA_DIR / f'topik_{level}.json'
        if not filepath.exists():
            print(f'  ⚠ 파일 없음: {filepath}')
            continue

        with open(filepath, encoding='utf-8') as f:
            data = json.load(f)

        for word in data['words']:
            converted = {
                'id': global_id,
                'word': word['word'],
                'romanization': romanize(word['word']),
                'meaning': word['meaning'],
                'part_of_speech': word['pos'],
                'level': level,
                'sentences': [
                    {'situation': ex.get('situation', ''), 'ko': ex['ko'], 'en': ex['en']}
                    for ex in word.get('examples', [])[:10]
                ]
            }
            all_words.append(converted)
            global_id += 1

        print(f'  Level {level}: {len(data["words"])}개 변환 완료')

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_words, f, ensure_ascii=False, indent=2)

    print(f'\n✓ words_db.json 생성: 총 {len(all_words)}개 단어')
    print(f'  저장 경로: {OUTPUT_PATH}')

    # 샘플 확인
    sample = all_words[0]
    print(f'\n[샘플] {sample["word"]} / {sample["romanization"]} / {sample["meaning"]}')
    print(f'  sentences[0]: {sample["sentences"][0]["ko"]}')


if __name__ == '__main__':
    main()
