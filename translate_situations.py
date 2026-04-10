#!/usr/bin/env python3
"""
상황 설명(situation) 각 언어로 번역 → situation_jp / situation_cn 등 필드 추가
usage:
  python translate_situations.py --lang JP        # JP 전체 등급
  python translate_situations.py --lang CN --level 1
  python translate_situations.py --all            # 전체 언어 전체 등급
"""
import json, os, sys, time, argparse
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

import anthropic

client = anthropic.Anthropic()

DATA_ROOT = Path(__file__).parent.parent / "data" / "LanguageTest" / "TOPIK"

LANG_CONFIG = {
    "JP": {"folder": "JP", "key": "jp", "target_name": "Japanese"},
    "CN": {"folder": "CN", "key": "cn", "target_name": "Chinese (Simplified)"},
    "VN": {"folder": "VN", "key": "vn", "target_name": "Vietnamese"},
    "ES": {"folder": "SP", "key": "es", "target_name": "Spanish"},
}
LEVELS = [1, 2, 3, 4, 5, 6]


def batch_translate(situations: list[str], target_lang: str) -> dict[str, str]:
    """상황 목록을 target_lang으로 번역. {원문: 번역문} 반환"""
    if not situations:
        return {}
    # 30개씩 묶어서 번역 (토큰 절약)
    chunk_size = 30
    result = {}
    for i in range(0, len(situations), chunk_size):
        chunk = situations[i:i + chunk_size]
        numbered = "\n".join(f"{j+1}. {s}" for j, s in enumerate(chunk))
        prompt = (
            f"Translate these short Korean lesson situation labels into {target_lang}.\n"
            f"Keep them very short (3-7 words), natural, and suitable as a # hashtag label.\n"
            f"Return ONLY a JSON array of translated strings, same order, no extra text.\n\n"
            f"{numbered}"
        )
        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1200,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text.strip()
            # Extract JSON array
            start = raw.find('[')
            end   = raw.rfind(']') + 1
            if start >= 0 and end > start:
                translations = json.loads(raw[start:end])
                for orig, trans in zip(chunk, translations):
                    result[orig] = trans
            else:
                print(f"  [WARN] JSON 파싱 실패, 원문 유지")
                for orig in chunk:
                    result[orig] = orig
        except Exception as e:
            print(f"  [ERROR] 번역 실패: {e}")
            for orig in chunk:
                result[orig] = orig
        time.sleep(0.5)  # Rate limit 완화
    return result


def process_file(json_path: Path, lang_key: str, target_name: str) -> int:
    """단일 JSON 파일 처리. 추가된 sentence 수 반환"""
    with open(json_path, encoding="utf-8") as f:
        db = json.load(f)
    words = db.get("words", db) if isinstance(db, dict) else db

    # 번역이 필요한 고유 situation 수집
    field = f"situation_{lang_key}"
    unique_sit: set[str] = set()
    for w in words:
        for ex in w.get("examples", w.get("sentences", [])):
            sit = ex.get("situation", "")
            if sit and not ex.get(field):
                unique_sit.add(sit)

    if not unique_sit:
        print(f"  모두 번역됨, 건너뜀: {json_path.name}")
        return 0

    print(f"  {len(unique_sit)}개 situation 번역 중... ({json_path.name})")
    translation_map = batch_translate(sorted(unique_sit), target_name)

    # 각 예문에 번역 필드 추가
    count = 0
    for w in words:
        for ex in w.get("examples", w.get("sentences", [])):
            sit = ex.get("situation", "")
            if sit and not ex.get(field) and sit in translation_map:
                ex[field] = translation_map[sit]
                count += 1

    # 저장
    if isinstance(db, dict) and "words" in db:
        db["words"] = words
    else:
        db = words
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"  → {count}개 필드 추가 완료")
    return count


def run(lang: str = None, level: int = None):
    langs = [lang] if lang else list(LANG_CONFIG.keys())
    levels = [level] if level else LEVELS

    total = 0
    for lg in langs:
        cfg = LANG_CONFIG.get(lg)
        if not cfg:
            print(f"[SKIP] 알 수 없는 언어: {lg}")
            continue
        folder = DATA_ROOT / cfg["folder"]
        for lv in levels:
            fpath = folder / f"topik_{lv}.json"
            if not fpath.exists():
                continue
            print(f"\n[{lg} Lv.{lv}] {fpath}")
            total += process_file(fpath, cfg["key"], cfg["target_name"])

    print(f"\n완료! 총 {total}개 situation 번역 추가됨")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="situation 필드 다국어 번역")
    parser.add_argument("--lang", choices=list(LANG_CONFIG.keys()),
                        help="번역할 언어 (JP/CN/VN/ES)")
    parser.add_argument("--level", type=int, choices=LEVELS, help="등급 (1-6)")
    parser.add_argument("--all", action="store_true", help="모든 언어·등급 처리")
    args = parser.parse_args()

    if not args.lang and not args.all:
        parser.error("--lang 또는 --all 을 지정하세요")

    run(lang=args.lang, level=args.level)
