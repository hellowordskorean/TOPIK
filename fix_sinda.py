#!/usr/bin/env python3
"""
모든 TOPIK 소스 JSON에서 Korean 문장의 '신다.' → '세요.' 일괄 수정
실행:
  python fix_sinda.py          # dry-run (변경 사항 미리 보기)
  python fix_sinda.py --apply  # 실제 파일 수정
"""

import json
import sys
import io
import argparse
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except AttributeError:
        pass

BASE_DIR = Path(__file__).parent.parent

# 처리 대상 디렉토리
TOPIK_DIRS = [
    BASE_DIR / "data" / "LanguageTest" / "TOPIK" / "EN",
    BASE_DIR / "data" / "LanguageTest" / "TOPIK" / "JP",
    BASE_DIR / "data" / "LanguageTest" / "TOPIK" / "SP",
    BASE_DIR / "data" / "LanguageTest" / "TOPIK" / "CN",
    BASE_DIR / "data" / "LanguageTest" / "TOPIK" / "VN",
]

KO_WEB_DIRS = [
    Path("D:/MakingApps/Apps/Hellowords/Ko/En"),
    Path("D:/MakingApps/Apps/Hellowords/Ko/Jp"),
    Path("D:/MakingApps/Apps/Hellowords/Ko/Sp"),
    Path("D:/MakingApps/Apps/Hellowords/Ko/Cn"),
    Path("D:/MakingApps/Apps/Hellowords/Ko/Vn"),
]


def fix_ko_text(text: str) -> tuple[str, int]:
    """'신다.' → '세요.' 변환. 변경 횟수 반환"""
    original = text
    text = text.replace("신다.", "세요.")
    count = original.count("신다.")
    return text, count


def process_topik_file(filepath: Path, apply: bool) -> int:
    """TOPIK JSON 파일 처리. 변경 횟수 반환"""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    total_changes = 0
    for word in data.get("words", []):
        for ex in word.get("examples", []):
            ko = ex.get("ko", "")
            if ko:
                fixed, count = fix_ko_text(ko)
                if count:
                    total_changes += count
                    if apply:
                        ex["ko"] = fixed
                    else:
                        print(f"  [{filepath.parent.name}] {ko!r}")
                        print(f"    → {fixed!r}")

    if apply and total_changes:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return total_changes


def process_web_file(filepath: Path, apply: bool) -> int:
    """Ko/ 웹 소스 JSON 파일 처리. 변경 횟수 반환"""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    total_changes = 0

    def fix_in_obj(obj):
        nonlocal total_changes
        if isinstance(obj, list):
            for item in obj:
                fix_in_obj(item)
        elif isinstance(obj, dict):
            if "ko" in obj and isinstance(obj["ko"], str):
                ko = obj["ko"]
                fixed, count = fix_ko_text(ko)
                if count:
                    total_changes += count
                    if apply:
                        obj["ko"] = fixed
                    else:
                        print(f"  [{filepath.parent.name}/{filepath.name}] {ko!r}")
                        print(f"    → {fixed!r}")
            for v in obj.values():
                if isinstance(v, (list, dict)):
                    fix_in_obj(v)

    fix_in_obj(data)

    if apply and total_changes:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return total_changes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="실제 파일 수정 (없으면 dry-run)")
    args = parser.parse_args()

    mode = "수정 적용" if args.apply else "DRY-RUN (미리 보기)"
    print(f"\n=== 신다 → 세요 일괄 수정 [{mode}] ===\n")

    total = 0

    # TOPIK 소스 파일
    print("[TOPIK 소스 파일]")
    for d in TOPIK_DIRS:
        if not d.exists():
            print(f"  폴더 없음: {d}")
            continue
        for fp in sorted(d.glob("topik_[1-6].json")):
            count = process_topik_file(fp, args.apply)
            if count:
                print(f"  {fp.parent.name}/{fp.name}: {count}개 수정")
                total += count

    # Ko/ 웹 소스 파일
    print("\n[Ko/ 웹 소스 파일]")
    for d in KO_WEB_DIRS:
        if not d.exists():
            print(f"  폴더 없음: {d}")
            continue
        for fp in sorted(d.glob("*.json")):
            if ".bak" in fp.name:
                continue
            count = process_web_file(fp, args.apply)
            if count:
                print(f"  {fp.parent.name}/{fp.name}: {count}개 수정")
                total += count

    print(f"\n총 {total}개 수정{'됨' if args.apply else ' 예정'}")
    if not args.apply:
        print("\n실제 수정하려면: python fix_sinda.py --apply")


if __name__ == "__main__":
    main()
