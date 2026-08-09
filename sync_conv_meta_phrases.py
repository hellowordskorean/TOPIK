#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""회화 YouTube 메타(youtube.description / youtube.localizations[*].description)의
1️⃣~🔟 예문 목록을 phrases_db 의 현재 문장으로 동기화한다.

예문을 수정하면 영상 설명문에 박혀 있는 10문장 목록이 옛 문장 그대로 남는다
(generate_phrase_metadata 가 localizations 를 그대로 쓰기 때문). 이 스크립트가
번호 줄만 현재 DB 문장으로 갈아끼운다. 나머지 훅·해시태그 문구는 건드리지 않는다.

사용:
  python sync_conv_meta_phrases.py --sits 31,32,33 --dry-run
  python sync_conv_meta_phrases.py --sits 31 --go
  python sync_conv_meta_phrases.py --all --go
"""
import argparse
import io
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_APP_BASE = os.environ.get("APP_BASE", str(Path(__file__).parent.parent))
DB_PATH = Path(_APP_BASE) / "data" / "Conversation" / "phrases_db.json"

MARKERS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
LANG_KEYS = ["en", "jp", "cn", "vn", "es"]
# 한국어 마스터 description 은 영어 번역을 병기한다
MASTER_LANG_KEY = "en"


def _rewrite_block(desc: str, phrases: list, lang_key: str) -> tuple:
    """description 안의 1️⃣~🔟 줄을 현재 문장으로 교체. (새 description, 바뀐 줄 수)"""
    if not desc:
        return desc, 0
    lines = desc.split("\n")
    changed = 0
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        for idx, mk in enumerate(MARKERS):
            if not stripped.startswith(mk):
                continue
            if idx >= len(phrases):
                break
            ph = phrases[idx]
            ko = ph.get("my_line", {}).get("ko", "")
            tr = ph.get("my_line", {}).get(lang_key) or ph.get("my_line", {}).get("en", "")
            if not ko or not tr:
                break
            # 기존 줄의 구분자(→ / —)와 꼬리 주석(⭐ ...)은 살린다
            body = stripped[len(mk):].lstrip()
            sep = " → "
            m = re.search(r"\s(→|—|-)\s", body)
            if m:
                sep = f" {m.group(1)} "
                tail_src = body[m.end():]
            else:
                tail_src = ""
            star = ""
            ms = re.search(r"\s(⭐.*)$", tail_src)
            if ms:
                star = " " + ms.group(1)
            new_line = f"{mk} {ko}{sep}{tr}{star}"
            if new_line != stripped:
                indent = line[: len(line) - len(stripped)]
                lines[i] = indent + new_line
                changed += 1
            break
    return "\n".join(lines), changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sits", help="상황 ID 목록 (예: 31,32,33)")
    ap.add_argument("--all", action="store_true", help="전체 상황")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--go", action="store_true")
    args = ap.parse_args()

    if not args.all and not args.sits:
        ap.error("--sits 또는 --all 이 필요합니다")

    db = json.load(open(DB_PATH, encoding="utf-8"))
    targets = ({int(x) for x in args.sits.split(",") if x.strip()}
               if args.sits else {s["id"] for s in db})

    total_lines = 0
    touched_sits = []
    for sit in db:
        if sit["id"] not in targets:
            continue
        phrases = sit.get("phrases", [])[:10]
        yt = sit.get("youtube") or {}
        if not yt:
            continue
        n_sit = 0

        new_desc, n = _rewrite_block(yt.get("description", ""), phrases, MASTER_LANG_KEY)
        if n:
            yt["description"] = new_desc
            n_sit += n

        for lk, loc in (yt.get("localizations") or {}).items():
            if lk not in LANG_KEYS or not isinstance(loc, dict):
                continue
            new_loc, n = _rewrite_block(loc.get("description", ""), phrases, lk)
            if n:
                loc["description"] = new_loc
                n_sit += n

        if n_sit:
            touched_sits.append((sit["id"], sit.get("situation", ""), n_sit))
            total_lines += n_sit

    print(f"수정 대상 상황 {len(touched_sits)}개 / 갱신된 예문 줄 {total_lines}개")
    for sid, name, n in touched_sits:
        print(f"  id{sid:>3} {name} — {n}줄")

    if args.dry_run:
        print("\nDRY-RUN — 저장하지 않음. 실행하려면 --go")
        return

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = DB_PATH.with_suffix(f".json.bak_meta_{stamp}")
    shutil.copy2(DB_PATH, bak)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"\n💾 저장 완료 (백업: {bak.name})")


if __name__ == "__main__":
    main()
