#!/usr/bin/env python3
"""
파이프라인 전체 감사 harness (이미지 생성 없음)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

실행:
  python3 audit.py            # 전체
  python3 audit.py --db       # 1. DB 무결성
  python3 audit.py --sync     # 2. 이미지-DB 동기화
  python3 audit.py --video    # 3. 영상 파일 검증
  python3 audit.py --youtube  # 4. 유튜브 정책 검증
"""
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# ── 경로 ─────────────────────────────────────────────────────────
WORDS_DB     = Path("/app/data/LanguageTest/words_db.json")
PROMPTS_FILE = Path("/app/data/LanguageTest/illustration_prompts.json")
ILLUST_DIR   = Path("/app/assets/illustrations")
OUTPUT_DIR   = Path("/app/output")
VIDEOS_LOG   = Path("/app/logs/videos_log.json")
REPORT_FILE  = Path("/app/logs/audit_report.json")

VALID_SITUATIONS = {
    "home", "kitchen", "school", "office", "work", "restaurant", "cafe",
    "shopping", "market", "hospital", "bank", "post", "airport", "hotel",
    "travel", "park", "gym", "transport", "subway", "bus", "phone",
    "family", "friend", "weather", "library", "general",
}

# YouTube 정책 한도
YT_TITLE_MAX       = 100
YT_DESC_MAX        = 5000
YT_TAG_TOTAL_MAX   = 500
YT_THUMB_SIZE_MAX  = 2 * 1024 * 1024  # 2MB
YT_VIDEO_SIZE_MAX  = 128 * 1024 * 1024 * 1024  # 128GB (실질 무제한)
YT_DURATION_MIN    = 60    # 1분 (Shorts 제외)
YT_DURATION_MAX    = 43200 # 12시간


def hr(char="━", n=55):
    print(char * n)


def fmt(n, total):
    pct = n / total * 100 if total else 0
    return f"{n:5d} / {total} ({pct:.1f}%)"


# ══════════════════════════════════════════════════════════════════
# 1. DB 무결성 검증
# ══════════════════════════════════════════════════════════════════

def audit_db(db: list) -> dict:
    hr()
    print("  [1] DB 무결성 검증")
    hr()

    issues = []
    seen_ids = {}
    required_fields = {"id", "word", "romanization", "meaning", "part_of_speech", "level", "sentences"}
    sent_required   = {"ko", "en", "situation"}

    stats = {
        "total": len(db),
        "duplicate_ids": 0,
        "missing_fields": 0,
        "empty_sentences": 0,
        "sentences_lt10": 0,
        "bad_situation": 0,
        "missing_en": 0,
    }

    for w in db:
        wid = w.get("id")

        # 중복 ID
        if wid in seen_ids:
            issues.append(f"중복 ID {wid}: {w.get('word')} vs {seen_ids[wid]}")
            stats["duplicate_ids"] += 1
        else:
            seen_ids[wid] = w.get("word")

        # 필수 필드 누락
        missing = required_fields - set(w.keys())
        if missing:
            issues.append(f"ID {wid} ({w.get('word')}): 필드 누락 {missing}")
            stats["missing_fields"] += 1

        # 예문 검사
        sents = w.get("sentences", [])
        if not sents:
            issues.append(f"ID {wid} ({w.get('word')}): sentences 없음")
            stats["empty_sentences"] += 1
            continue

        if len(sents) < 10:
            issues.append(f"ID {wid} ({w.get('word')}): 예문 {len(sents)}개 (10개 미만)")
            stats["sentences_lt10"] += 1

        for i, s in enumerate(sents):
            sit = s.get("situation", "").lower().strip()
            # 키워드가 situation 문자열 안에 포함되면 OK (부분 매칭)
            if sit and not any(kw in sit for kw in VALID_SITUATIONS):
                issues.append(f"ID {wid} 예문[{i}]: 매핑 불가 situation '{s.get('situation')}'")
                stats["bad_situation"] += 1

            if not s.get("en", "").strip():
                issues.append(f"ID {wid} 예문[{i}]: en 번역 없음")
                stats["missing_en"] += 1

    # 출력
    total = stats["total"]
    print(f"  총 단어:          {total:5d}개")
    print(f"  중복 ID:          {fmt(stats['duplicate_ids'], total)}")
    print(f"  필드 누락:        {fmt(stats['missing_fields'], total)}")
    print(f"  예문 없음:        {fmt(stats['empty_sentences'], total)}")
    print(f"  예문 10개 미만:   {fmt(stats['sentences_lt10'], total)}")
    print(f"  잘못된 situation: {stats['bad_situation']:5d}개")
    print(f"  en 번역 없음:     {stats['missing_en']:5d}개")

    if issues:
        print(f"\n  ── 상위 10개 이슈 ──")
        for iss in issues[:10]:
            print(f"    • {iss}")
        if len(issues) > 10:
            print(f"    ... 외 {len(issues) - 10}개")
    else:
        print("\n  ✓ 이슈 없음")

    return {"stats": stats, "issues": issues}


# ══════════════════════════════════════════════════════════════════
# 2. 이미지-DB 동기화
# ══════════════════════════════════════════════════════════════════

def audit_sync(db: list) -> dict:
    hr()
    print("  [2] 이미지-DB 동기화 통계")
    hr()

    total_words   = len(db)
    word_ok       = 0
    word_missing  = []
    sent_total    = 0
    sent_ok       = 0
    sent_missing  = []

    for w in db:
        lv   = w.get("level", 1)
        word = w.get("word", "")
        wdir = ILLUST_DIR / f"lv{lv}" / word

        # word.png
        wpath = wdir / "word.png"
        if wpath.exists():
            word_ok += 1
        else:
            word_missing.append(w["id"])

        # 예문 이미지
        for idx in range(len(w.get("sentences", []))):
            sent_total += 1
            spath = wdir / f"{idx}.png"
            if spath.exists():
                sent_ok += 1
            else:
                sent_missing.append((w["id"], idx))

    print(f"  word.png 완성:    {fmt(word_ok, total_words)}")
    print(f"  예문 이미지 완성: {fmt(sent_ok, sent_total)}")

    # 레벨별 세분화
    print(f"\n  ── 레벨별 word.png ──")
    for lv in sorted({w["level"] for w in db}):
        lv_words = [w for w in db if w["level"] == lv]
        lv_ok = sum(
            1 for w in lv_words
            if (ILLUST_DIR / f"lv{lv}" / w["word"] / "word.png").exists()
        )
        print(f"    Level {lv}: {fmt(lv_ok, len(lv_words))}")

    # 미완성 상위 20개
    if word_missing:
        print(f"\n  word.png 없는 단어 (상위 20개): {word_missing[:20]}")

    return {
        "word_total": total_words, "word_ok": word_ok,
        "sent_total": sent_total, "sent_ok": sent_ok,
        "word_missing_count": len(word_missing),
        "sent_missing_count": len(sent_missing),
    }


# ══════════════════════════════════════════════════════════════════
# 3. 영상 파일 검증
# ══════════════════════════════════════════════════════════════════

def audit_video() -> dict:
    hr()
    print("  [3] 영상 파일 검증")
    hr()

    # videos_log 기반 검증
    if not VIDEOS_LOG.exists():
        print("  videos_log.json 없음 — 스킵")
        return {}

    with open(VIDEOS_LOG, encoding="utf-8") as f:
        logs = json.load(f)

    if not logs:
        print("  영상 로그 없음")
        return {}

    total    = len(logs)
    ok       = 0
    missing  = []
    zero_size = []
    size_warn = []
    SIZE_MIN = 500 * 1024  # 500KB 미만이면 의심

    for entry in logs:
        path = Path(entry.get("output_path", "").replace("/app/", "/app/"))
        if not path.exists():
            missing.append(entry.get("word", "?"))
            continue

        size = path.stat().st_size
        if size == 0:
            zero_size.append(entry.get("word", "?"))
        elif size < SIZE_MIN:
            size_warn.append((entry.get("word", "?"), size // 1024))
        else:
            ok += 1

    print(f"  로그 기록:   {total:5d}개")
    print(f"  파일 정상:   {fmt(ok, total)}")
    print(f"  파일 없음:   {fmt(len(missing), total)}")
    print(f"  크기 0:      {fmt(len(zero_size), total)}")
    print(f"  크기 의심:   {fmt(len(size_warn), total)}  (< 500KB)")

    if missing:
        print(f"\n  없는 파일 (상위 10): {missing[:10]}")
    if zero_size:
        print(f"  크기 0 파일: {zero_size[:10]}")
    if size_warn:
        print(f"  크기 의심 (단어, KB): {size_warn[:10]}")

    # ffprobe 가능하면 길이 검증
    try:
        import subprocess
        sample = next(
            (Path(e["output_path"]) for e in logs
             if Path(e["output_path"]).exists()), None
        )
        if sample:
            r = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(sample)],
                capture_output=True, text=True, timeout=5
            )
            if r.returncode == 0:
                dur = float(r.stdout.strip())
                print(f"\n  샘플 길이: {dur:.1f}초 ({sample.name})")
                if dur < YT_DURATION_MIN:
                    print(f"  ⚠ {YT_DURATION_MIN}초 미만 — Shorts 기준 확인 필요")
    except Exception:
        print("\n  (ffprobe 없음 — 길이 검증 스킵)")

    return {
        "total": total, "ok": ok,
        "missing": len(missing), "zero_size": len(zero_size),
        "size_warn": len(size_warn),
    }


# ══════════════════════════════════════════════════════════════════
# 4. 유튜브 정책 검증
# ══════════════════════════════════════════════════════════════════

def audit_youtube(db: list) -> dict:
    hr()
    print("  [4] 유튜브 업로드 정책 검증")
    hr()

    if not VIDEOS_LOG.exists():
        print("  videos_log.json 없음 — 스킵")
        return {}

    with open(VIDEOS_LOG, encoding="utf-8") as f:
        logs = json.load(f)

    # 업로드 로그 (이미 업로드된 것)
    uploads_log = Path("/app/logs/uploads.json")
    uploaded_ids = set()
    if uploads_log.exists():
        for enc in ("utf-8", "utf-8-sig", "cp949", "latin-1"):
            try:
                with open(uploads_log, encoding=enc) as f:
                    uploads = json.load(f)
                uploaded_ids = {u.get("word_id") for u in uploads} if isinstance(uploads, list) else set()
                break
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue

    # DB에서 단어-의미 맵
    word_map = {w["id"]: w for w in db}

    title_fail  = []
    thumb_fail  = []
    total = len(logs)

    for entry in logs:
        wid  = entry.get("word_id")
        word = entry.get("word", "")
        mean = entry.get("meaning", "")
        lv   = entry.get("level", 1)
        lang = entry.get("language", "EN")
        exam = entry.get("exam", "TOPIK")

        # 유튜브 제목 시뮬레이션 (upload_youtube.py 패턴 추정)
        title = f"[{exam} Lv.{lv}] {word} - {mean} | Korean Vocabulary"
        if len(title) > YT_TITLE_MAX:
            title_fail.append({
                "word": word, "title_len": len(title), "title": title[:60] + "..."
            })

        # 썸네일 크기 검사
        thumb_dir = Path("/app/output/TOPIK") / lang / f"lv{lv}" / "thumbnails"
        thumb_path = thumb_dir / f"topik_{wid:04d}_{word}.jpg"
        if not thumb_path.exists():
            thumb_path = thumb_dir / f"topik_{wid:04d}_{word}.png"
        if thumb_path.exists():
            size = thumb_path.stat().st_size
            if size > YT_THUMB_SIZE_MAX:
                thumb_fail.append({"word": word, "size_mb": size / 1024 / 1024})

    print(f"  검사 영상:      {total:5d}개")
    print(f"  이미 업로드:    {len(uploaded_ids):5d}개")
    print(f"  제목 100자 초과: {fmt(len(title_fail), total)}")
    print(f"  썸네일 2MB 초과: {fmt(len(thumb_fail), total)}")

    if title_fail:
        print(f"\n  제목 초과 (상위 5):")
        for t in title_fail[:5]:
            print(f"    [{t['title_len']}자] {t['title']}")
    if thumb_fail:
        print(f"\n  썸네일 초과 (상위 5):")
        for t in thumb_fail[:5]:
            print(f"    {t['word']}: {t['size_mb']:.2f}MB")

    if not title_fail and not thumb_fail:
        print("\n  ✓ 정책 위반 없음")

    return {
        "total": total, "uploaded": len(uploaded_ids),
        "title_fail": len(title_fail), "thumb_fail": len(thumb_fail),
    }


# ══════════════════════════════════════════════════════════════════
# main
# ══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="파이프라인 전체 감사")
    parser.add_argument("--db",      action="store_true", help="1. DB 무결성")
    parser.add_argument("--sync",    action="store_true", help="2. 이미지-DB 동기화")
    parser.add_argument("--video",   action="store_true", help="3. 영상 파일 검증")
    parser.add_argument("--youtube", action="store_true", help="4. 유튜브 정책 검증")
    args = parser.parse_args()

    # 플래그 없으면 전체 실행
    run_all = not any([args.db, args.sync, args.video, args.youtube])

    print()
    hr("═")
    print(f"  파이프라인 감사  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    hr("═")

    with open(WORDS_DB, encoding="utf-8") as f:
        db = json.load(f)

    report = {"run_at": datetime.now().isoformat()}

    if run_all or args.db:
        report["db"] = audit_db(db)

    if run_all or args.sync:
        report["sync"] = audit_sync(db)

    if run_all or args.video:
        report["video"] = audit_video()

    if run_all or args.youtube:
        report["youtube"] = audit_youtube(db)

    hr("═")
    print(f"  감사 완료. 리포트: {REPORT_FILE}")
    hr("═")
    print()

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
