#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""회화 영상 교체: 기존 YouTube 업로드 삭제 후 재렌더된 로컬 파일로 재업로드.

replace_word_uploads.py 의 회화판. 예약 발행(publishAt)이 걸린 화수는 그 시각을
그대로 유지하고, 이미 공개된 영상만 즉시 공개로 다시 올린다.

- 메타데이터: upload_youtube.generate_phrase_metadata (일반 업로드와 동일 경로)
- 썸네일: 본편만 첨부 (쇼츠는 세로 프레임 그대로 두는 기존 정책 유지)
- 재생목록: 본편 'phrase' / 쇼츠 'phrase_shorts'
- 로그: logs/conv_log.json, logs/uploads_phrase_{lang}.json, (있으면) logs/uploads.json

사용:
  python replace_conv_uploads.py --theme 31 --dry-run
  python replace_conv_uploads.py --theme 31 --go
  python replace_conv_uploads.py --theme 31 --langs EN,JP --fmts youtube --go
"""
import argparse
import io
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

_APP_BASE = os.environ.get("APP_BASE", str(BASE.parent))
DB_PATH = Path(_APP_BASE) / "data" / "Conversation" / "phrases_db.json"
CONV_LOG_F = BASE / "logs" / "conv_log.json"
UPLOADS_F = BASE / "logs" / "uploads.json"
DAILY_AUTO_F = BASE / "logs" / "daily_auto.json"

ALL_LANGS = ["EN", "JP", "CN", "VN", "ES"]
ALL_FMTS = ["youtube", "reels"]
# 업로드 시점에 publishAt 이 과거면 YouTube 가 거부 → 이 여유분 안쪽이면 즉시 공개
PUBLISH_MARGIN = timedelta(minutes=5)


def load(p, d):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return d


def save(p, data):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def video_path(theme_id, lang, fmt):
    base = BASE / "output" / "conversation" / lang
    if fmt == "reels":
        return base / "reels" / f"conv_{theme_id}_{lang}_reels.mp4"
    return base / f"conv_{theme_id}_{lang}.mp4"


def thumb_path(theme_id, lang):
    return BASE / "output" / "conversation" / lang / "thumbnail" / f"conv_{theme_id}_{lang}_thumb.png"


def conv_rows(theme_id, langs, fmts):
    rows = []
    for r in load(CONV_LOG_F, []):
        if str(r.get("theme_id")) != str(theme_id):
            continue
        if r.get("lang") not in langs or r.get("fmt", "youtube") not in fmts:
            continue
        rows.append(r)
    rows.sort(key=lambda r: (ALL_LANGS.index(r["lang"]) if r["lang"] in ALL_LANGS else 9,
                             0 if r.get("fmt", "youtube") == "youtube" else 1))
    return rows


def parse_dt(raw):
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def publish_arg(privacy, publish_at):
    """기존 공개 상태를 보고 새 업로드의 발행 인자 결정. None = 즉시 공개."""
    now = datetime.now(timezone.utc)
    if privacy == "private" and publish_at and publish_at > now + PUBLISH_MARGIN:
        return publish_at, f"예약 유지({publish_at.isoformat()})"
    if privacy == "private" and publish_at:
        return None, "공개(즉시 — 예약시각 지남)"
    if privacy in ("public", None):
        return None, "공개(즉시)"
    return None, f"공개(즉시 — 기존 {privacy})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", required=True, type=int, help="교체할 회화 상황 ID")
    ap.add_argument("--langs", default=",".join(ALL_LANGS))
    ap.add_argument("--fmts", default=",".join(ALL_FMTS))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--go", action="store_true")
    args = ap.parse_args()

    DRY = args.dry_run
    theme_id = args.theme
    langs = [x.strip().upper() for x in args.langs.split(",") if x.strip()]
    fmts = [x.strip().lower() for x in args.fmts.split(",") if x.strip()]

    db = json.load(open(DB_PATH, encoding="utf-8"))
    situation = next((s for s in db if s["id"] == theme_id), None)
    if not situation:
        print(f"✗ 상황 {theme_id} 없음"); sys.exit(1)

    from upload_youtube import (get_youtube_client, generate_phrase_metadata, upload_video,
                                get_or_create_typed_playlist, add_to_playlist)

    print(f"now UTC = {datetime.now(timezone.utc).isoformat()}  |  mode = {'DRY-RUN' if DRY else 'LIVE'}")
    print(f"상황 {theme_id} — {situation.get('situation','')}\n")

    rows = conv_rows(theme_id, langs, fmts)
    if not rows:
        print("✗ conv_log 에 해당 항목이 없습니다"); sys.exit(1)

    # ── 계획 작성 (기존 영상 상태 조회) ──
    plan = []
    clients = {}
    for r in rows:
        lang, fmt = r["lang"], r.get("fmt", "youtube")
        old_id = r.get("video_id")
        vp = video_path(theme_id, lang, fmt)
        privacy, pub_at = None, None
        if old_id:
            try:
                yt = clients.get(lang) or clients.setdefault(lang, get_youtube_client(lang=lang))
                resp = yt.videos().list(part="status", id=old_id).execute()
                items = resp.get("items", [])
                if items:
                    st = items[0]["status"]
                    privacy = st.get("privacyStatus")
                    pub_at = parse_dt(st.get("publishAt"))
                else:
                    privacy = "(없음)"
            except Exception as e:
                privacy = f"(조회실패: {type(e).__name__})"
        pub, action = publish_arg(privacy, pub_at)
        plan.append(dict(lang=lang, fmt=fmt, old_id=old_id, vpath=vp, exists=vp.exists(),
                         mtime=(datetime.fromtimestamp(vp.stat().st_mtime).strftime("%m-%d %H:%M")
                                if vp.exists() else "-"),
                         privacy=privacy, pub=pub, action=action, row=r))

    print(f"{'언어':4} {'유형':8} {'기존ID':14} {'영상':6} {'렌더시각':12} {'기존상태':10} {'발행처리'}")
    for p in plan:
        print(f"{p['lang']:4} {p['fmt']:8} {str(p['old_id']):14} {str(p['exists']):6} "
              f"{p['mtime']:12} {str(p['privacy']):10} {p['action']}")
    missing = [p for p in plan if not p["exists"]]
    print(f"\n총 {len(plan)}건 | 로컬 영상 없음 {len(missing)}건")

    if DRY:
        print("\nDRY-RUN 완료 — 실제 변경 없음. 실행하려면 --go")
        return

    # ── 실행 ──
    for p in plan:
        lang, fmt = p["lang"], p["fmt"]
        print(f"\n----- {theme_id} {lang}/{fmt} -----")
        if not p["exists"]:
            print(f"  ✗ 로컬 영상 없음, 스킵: {p['vpath']}")
            continue
        yt = clients.get(lang) or clients.setdefault(lang, get_youtube_client(lang=lang))

        # 1) 기존 삭제
        if p["old_id"]:
            try:
                yt.videos().delete(id=p["old_id"]).execute()
                print(f"  🗑 삭제 완료: {p['old_id']}")
            except Exception as de:
                print(f"  ⚠ 삭제 실패(계속): {p['old_id']} — {de}")

        # 2) 메타데이터 + 썸네일
        md = generate_phrase_metadata(situation, theme_id, lang=lang, fmt=fmt, chapters=None)
        th = thumb_path(theme_id, lang)
        thumb = str(th) if (fmt != "reels" and th.exists()) else None

        # 3) 업로드 (발행 인자 재계산 — 실행 중 예약시각이 지날 수 있음)
        pub, action = publish_arg(p["privacy"], p["pub"])
        new_id = upload_video(yt, str(p["vpath"]), md, publish_at=pub, thumbnail_path=thumb)
        if not new_id:
            print("  ✗ 업로드 실패")
            continue
        print(f"  ✅ 업로드: {new_id} ({action}) thumb={'O' if thumb else 'X'}")

        # 4) 재생목록
        try:
            ptype = "phrase_shorts" if fmt == "reels" else "phrase"
            pl = get_or_create_typed_playlist(yt, lang, ptype)
            add_to_playlist(yt, pl, new_id)
            print("  ＋재생목록 추가")
        except Exception as pe:
            print(f"  ⚠ 재생목록 실패(무시): {pe}")

        # 5) 로그 갱신
        clog = load(CONV_LOG_F, [])
        for e in clog:
            if (str(e.get("theme_id")) == str(theme_id) and e.get("lang") == lang
                    and e.get("fmt", "youtube") == fmt):
                e["video_id"] = new_id
                e["uploaded"] = True
                e["replaced_at"] = datetime.now().isoformat()
        save(CONV_LOG_F, clog)

        pf = BASE / "logs" / f"uploads_phrase_{lang.lower()}.json"
        plog = load(pf, {"uploaded": []})
        hit = next((r for r in plog.get("uploaded", [])
                    if r.get("sit_id") == theme_id and r.get("fmt", "youtube") == fmt), None)
        entry = {
            "num": theme_id, "sit_id": theme_id, "fmt": fmt,
            "situation": situation.get("situation", ""), "video_id": new_id, "lang": lang,
            "publish_at": pub.isoformat() if pub else None,
            "uploaded_at": datetime.now().isoformat(),
        }
        if hit:
            hit.update(entry)
        else:
            plog.setdefault("uploaded", []).append(entry)
        save(pf, plog)

        # daily_auto 의 화수 상태에도 새 video_id 반영 (삭제된 ID 참조 방지)
        st = load(DAILY_AUTO_F, {})
        ps = st.get("phrase_langs", {}).get(lang)
        if ps and ps.get("conv_ep_override") == theme_id:
            ps["yt_video_id" if fmt == "youtube" else "reels_video_id"] = new_id
            save(DAILY_AUTO_F, st)

        ul = load(UPLOADS_F, {"uploaded": []})
        hit2 = next((r for r in ul.get("uploaded", [])
                     if r.get("type") == "conversation" and str(r.get("theme_id")) == str(theme_id)
                     and r.get("lang") == lang and r.get("fmt", "youtube") == fmt), None)
        if hit2:
            hit2["video_id"] = new_id
            hit2["youtube_url"] = f"https://youtube.com/watch?v={new_id}"
            hit2["uploaded_at"] = datetime.now().isoformat()
            save(UPLOADS_F, ul)

        time.sleep(1)

    print("\n=== 완료 ===")


if __name__ == "__main__":
    main()
