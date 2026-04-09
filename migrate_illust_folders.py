#!/usr/bin/env python3
"""
일러스트 폴더 이름 마이그레이션: {word} → {id}_{word}
예: lv1/가게/ → lv1/1_가게/

실행:
  python migrate_illust_folders.py          # 미리보기 (실제 이동 없음)
  python migrate_illust_folders.py --apply  # 실제 이동
"""
import json
import os
import sys
from pathlib import Path

ILLUST_DIR = Path("Z:/Hellowords/youtube/assets/illustrations")
DB_PATH    = Path("Z:/Hellowords/data/LanguageTest/words_db.json")

def main():
    apply = "--apply" in sys.argv

    with open(DB_PATH, encoding="utf-8") as f:
        db = json.load(f)
    words = db if isinstance(db, list) else db.get("words", [])

    # word 텍스트 → id 매핑 (level도 고려)
    word_map = {}  # (word_text, level) → id
    for w in words:
        word_map[(w["word"], w["level"])] = w["id"]

    rename_count = 0
    skip_count = 0
    error_count = 0

    for lv in range(1, 7):
        lv_dir = ILLUST_DIR / f"lv{lv}"
        if not lv_dir.exists():
            continue
        for folder in sorted(lv_dir.iterdir()):
            if not folder.is_dir():
                continue
            name = folder.name
            # 이미 {숫자}_ 형식이면 스킵
            if name.split("_")[0].isdigit():
                print(f"  [SKIP] 이미 변환됨: lv{lv}/{name}")
                skip_count += 1
                continue
            # 구 폴더명에서 word_id 찾기
            word_id = word_map.get((name, lv))
            if word_id is None:
                print(f"  [WARN] DB에 없음: lv{lv}/{name}")
                skip_count += 1
                continue
            new_name = f"{word_id}_{name}"
            new_path = lv_dir / new_name
            if new_path.exists():
                print(f"  [SKIP] 이미 존재: lv{lv}/{new_name}")
                skip_count += 1
                continue
            print(f"  {'[이동]' if apply else '[예정]'} lv{lv}/{name} → lv{lv}/{new_name}")
            if apply:
                try:
                    folder.rename(new_path)
                    rename_count += 1
                except Exception as e:
                    print(f"    오류: {e}")
                    error_count += 1
            else:
                rename_count += 1

    print(f"\n{'실제 이동' if apply else '예정'}: {rename_count}개 | 스킵: {skip_count}개 | 오류: {error_count}개")
    if not apply:
        print("\n실제 이동하려면: python migrate_illust_folders.py --apply")

if __name__ == "__main__":
    main()
