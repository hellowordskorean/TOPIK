#!/usr/bin/env python3
"""
웹용 JSON 자동 동기화 스크립트
원본: D:/MakingApps/Apps/Hellowords/Ko/{Lang}/topik_N.json
생성:
  - HW/level_data/topik_{lang}_lvN.json        (단일 레벨, word-keyed)
  - HW/level_data/topik_{lang}_lv1_2.json      (레벨 1+2 병합)
  - HW/level_data/topik_{lang}_lv3_4.json      (레벨 3+4 병합)
  - HW/level_data/topik_{lang}_lv5_6.json      (레벨 5+6 병합)

실행:
  python sync_web_data.py                    # EN (기본)
  python sync_web_data.py --lang jp          # 일본어
  python sync_web_data.py --lang es          # 스페인어
  python sync_web_data.py --lang all         # EN + JP + ES 전체
  python sync_web_data.py --dry-run          # 실제 저장 없이 변환 결과 확인
"""

import json
import argparse
from pathlib import Path

WEB_ROOT   = Path("D:/MakingApps/Apps/Hellowords")
TARGET_DIR = WEB_ROOT / "HW" / "level_data"
LEVELS     = [1, 2, 3, 4, 5, 6]
COMBINED   = [(1, 2), (3, 4), (5, 6)]

# 언어 코드 → (Ko/ 하위 폴더, 원본 예문 키, HW 파일명 prefix)
_LANG_CONFIG = {
    "en": ("En", "en",  "topik_en"),
    "jp": ("Jp", "jp",  "topik_jp"),
    "es": ("Sp", "es",  "topik_sp"),
    "cn": ("Cn", "cn",  "topik_cn"),
    "vn": ("Vn", "vn",  "topik_vn"),
}


def load_source(lang: str, level: int) -> dict | None:
    folder, _, _ = _LANG_CONFIG[lang]
    path = WEB_ROOT / "Ko" / folder / f"topik_{level}.json"
    if not path.exists():
        print(f"  [건너뜀] 파일 없음: {path}")
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def to_hw_single(source: dict, lang: str) -> dict:
    """배열 형식 → word-keyed dict (단일 레벨)"""
    _, sent_key, _ = _LANG_CONFIG[lang]
    level_str = str(source["level"])
    result = {}
    for w in source["words"]:
        examples_tl = [
            {
                "situation": ex.get("situation", ""),
                "ko": ex["ko"],
                "tl": ex.get(sent_key) or ex.get("tl", ""),
            }
            for ex in w.get("examples", [])
        ]
        first_ex = examples_tl[0] if examples_tl else {}
        result[w["word"]] = {
            "word":        w["word"],
            "phonetic":    "",
            "pos":         w.get("pos", ""),
            "meaning":     w.get("meaning", ""),
            "synonyms":    w.get("synonyms", []),
            "level":       level_str,
            "lang":        lang,
            "situation":   first_ex.get("situation", ""),
            "example_ko":  first_ex.get("ko", ""),
            "example_tl":  first_ex.get("tl", ""),
            "examples":    examples_tl,
        }
    return result


def to_hw_combined(lang: str, sources: list[tuple[int, dict]]) -> dict:
    """여러 레벨 병합 → word-keyed dict"""
    _, sent_key, _ = _LANG_CONFIG[lang]
    result = {}
    for level, source in sources:
        for w in source["words"]:
            examples_tl = [
                {
                    "situation": ex.get("situation", ""),
                    "ko": ex["ko"],
                    "tl": ex.get(sent_key) or ex.get("tl", ""),
                }
                for ex in w.get("examples", [])
            ]
            result[w["word"]] = {
                "word":         w["word"],
                "pos":          w.get("pos", ""),
                "meaning":      w.get("meaning", ""),
                "synonyms":     w.get("synonyms", []),
                "source_level": level,
                "examples":     examples_tl,
            }
    return result


def save_json(path: Path, data: dict, dry_run: bool):
    if dry_run:
        print(f"  [dry-run] 저장 예정: {path.name} ({len(data)}개 단어)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [OK] {path.name} ({len(data)}개 단어)")


def sync_lang(lang: str, dry_run: bool):
    _, _, prefix = _LANG_CONFIG[lang]
    print(f"\n=== {lang.upper()} 동기화 ===")

    loaded: dict[int, dict] = {}
    for lv in LEVELS:
        source = load_source(lang, lv)
        if source is None:
            continue
        loaded[lv] = source
        hw = to_hw_single(source, lang)
        save_json(TARGET_DIR / f"{prefix}_lv{lv}.json", hw, dry_run)

    for lv_a, lv_b in COMBINED:
        sources = [(lv, loaded[lv]) for lv in (lv_a, lv_b) if lv in loaded]
        if not sources:
            print(f"  [건너뜀] lv{lv_a}+{lv_b}: 원본 없음")
            continue
        hw = to_hw_combined(lang, sources)
        save_json(TARGET_DIR / f"{prefix}_lv{lv_a}_{lv_b}.json", hw, dry_run)


def main():
    parser = argparse.ArgumentParser(description="웹용 JSON 동기화")
    parser.add_argument("--lang", default="en",
                        help="언어: en | jp | es | cn | vn | all")
    parser.add_argument("--dry-run", action="store_true",
                        help="실제 저장 없이 변환 결과 확인")
    args = parser.parse_args()

    dry_run = args.dry_run
    if dry_run:
        print("=== DRY RUN 모드 (파일 저장 안 함) ===")

    langs = list(_LANG_CONFIG.keys()) if args.lang.lower() == "all" else [args.lang.lower()]
    for lang in langs:
        if lang not in _LANG_CONFIG:
            print(f"지원하지 않는 언어: {lang}  (지원: {list(_LANG_CONFIG)})")
            continue
        sync_lang(lang, dry_run)

    print("\n완료!")
    if not dry_run:
        print("다음 단계: D:/MakingApps/Apps/Hellowords/ 에서 git add + commit + push 하세요.")


if __name__ == "__main__":
    main()
