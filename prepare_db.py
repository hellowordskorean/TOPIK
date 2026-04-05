#!/usr/bin/env python3
"""
데이터 변환: data/TOPIK/{LANG}/*.json → data/words_db_{lang}.json
- make_video.py / upload_youtube.py 가 기대하는 형식으로 변환
- romanization 자동 생성 (Revised Romanization 간략 버전)

실행:
  python3 prepare_db.py              # EN (기본)
  python3 prepare_db.py --lang JP    # 일본어
  python3 prepare_db.py --lang ES    # 스페인어
  python3 prepare_db.py --lang all   # EN + JP + ES 모두
"""

import json
import sys
import io
import argparse
from pathlib import Path

# Windows cp949 인코딩 문제 방지
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except AttributeError:
        pass

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


# ─── 언어 설정 ──────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
TOPIK_BASE = BASE_DIR.parent / 'data' / 'LanguageTest' / 'TOPIK'

# 언어 코드 → (소스 폴더, 예문 키, 출력 파일명)
_LANG_CONFIG = {
    'EN': ('EN', 'en', 'words_db.json'),
    'JP': ('JP', 'jp', 'words_db_jp.json'),
    'ES': ('SP', 'es', 'words_db_es.json'),
    'CN': ('CN', 'cn', 'words_db_cn.json'),
    'VN': ('VN', 'vn', 'words_db_vn.json'),
}


def build_db(lang: str):
    """지정 언어의 words_db 생성"""
    if lang not in _LANG_CONFIG:
        print(f'  ✗ 지원하지 않는 언어: {lang}  (지원: {list(_LANG_CONFIG)})')
        return

    src_folder, sent_key, out_file = _LANG_CONFIG[lang]
    data_dir = TOPIK_BASE / src_folder
    output_path = BASE_DIR.parent / 'data' / 'LanguageTest' / out_file

    if not data_dir.exists():
        print(f'  ✗ 데이터 폴더 없음: {data_dir}')
        return

    all_words = []
    global_id = 1

    for level in range(1, 7):
        filepath = data_dir / f'topik_{level}.json'
        if not filepath.exists():
            print(f'  ⚠ 파일 없음: {filepath}')
            continue

        with open(filepath, encoding='utf-8') as f:
            data = json.load(f)

        for word in data['words']:
            sentences = []
            for ex in word.get('examples', [])[:10]:
                tl = ex.get(sent_key) or ex.get('en', '')
                sentences.append({
                    'situation': ex.get('situation', ''),
                    'ko': ex['ko'],
                    sent_key: tl,
                })
            converted = {
                'id': global_id,
                'word': word['word'],
                'romanization': romanize(word['word']),
                'meaning': word['meaning'],
                'part_of_speech': word['pos'],
                'level': level,
                'language': lang,
                'sentences': sentences,
            }
            all_words.append(converted)
            global_id += 1

        print(f'  [{lang}] Level {level}: {len(data["words"])}개 변환 완료')

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_words, f, ensure_ascii=False, indent=2)

    print(f'  [OK] {out_file} 생성: 총 {len(all_words)}개 단어')
    print(f'    저장: {output_path}')

    sample = all_words[0]
    print(f'  [샘플] {sample["word"]} / {sample["romanization"]} / {sample["meaning"]}')
    print(f'    sentences[0]: {sample["sentences"][0]["ko"]}')


def main():
    parser = argparse.ArgumentParser(description='TOPIK 단어 DB 변환')
    parser.add_argument('--lang', default='EN',
                        help='대상 언어: EN | JP | ES | CN | VN | all')
    args = parser.parse_args()

    langs = list(_LANG_CONFIG.keys()) if args.lang.lower() == 'all' else [args.lang.upper()]
    for lang in langs:
        print(f'\n=== {lang} 변환 중 ===')
        build_db(lang)
    print('\n완료!')


if __name__ == '__main__':
    main()
