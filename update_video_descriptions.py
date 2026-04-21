#!/usr/bin/env python3
"""
이미 업로드된 YouTube 단어 본편 영상의 설명란을 10개 예문으로 업데이트.
uploads.json에서 fmt=youtube인 항목을 읽어 YouTube API로 description 갱신.

실행:
  python update_video_descriptions.py             # 전체
  python update_video_descriptions.py --lang EN   # 특정 언어만
  python update_video_descriptions.py --dry-run   # 실제 업데이트 없이 확인
"""
import io, json, os, sys, time, argparse
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except AttributeError:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

_SCRIPT_DIR = Path(__file__).parent
UPLOADS_LOG  = _SCRIPT_DIR / "logs" / "uploads.json"

def _find_data_root() -> Path:
    for candidate in [
        os.environ.get("DATA_ROOT", ""),
        "/app/data",
        str(_SCRIPT_DIR.parent / "data"),
    ]:
        if candidate:
            p = Path(candidate) / "LanguageTest" / "words_db.json"
            if p.exists():
                return Path(candidate)
    return Path("/app/data")

_DATA_ROOT = _find_data_root()
WORDS_DB   = _DATA_ROOT / "LanguageTest" / "words_db.json"


def _load_words_db() -> dict:
    db = json.loads(WORDS_DB.read_text(encoding="utf-8"))
    words = db if isinstance(db, list) else db.get("words", [])
    return {w["id"]: w for w in words}


def update_description(youtube, video_id: str, new_title: str, new_description: str,
                        new_tags: list, category_id: str = "27") -> bool:
    """YouTube video description 업데이트"""
    try:
        # 현재 snippet 조회
        resp = youtube.videos().list(part="snippet", id=video_id).execute()
        items = resp.get("items", [])
        if not items:
            print(f"  영상 없음: {video_id}")
            return False
        snippet = items[0]["snippet"]
        # title, description, tags, categoryId 업데이트
        snippet["title"]       = new_title
        snippet["description"] = new_description
        snippet["tags"]        = new_tags
        snippet["categoryId"]  = category_id
        youtube.videos().update(
            part="snippet",
            body={"id": video_id, "snippet": snippet}
        ).execute()
        return True
    except Exception as e:
        print(f"  업데이트 실패 ({video_id}): {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="업로드된 단어 본편 설명란 업데이트")
    parser.add_argument("--lang", default=None, help="특정 언어만 (EN, JP, CN, VN, ES)")
    parser.add_argument("--dry-run", action="store_true", help="실제 업데이트 없이 확인")
    parser.add_argument("--word-id", type=int, default=None, help="특정 단어 ID만")
    args = parser.parse_args()

    sys.path.insert(0, str(_SCRIPT_DIR))
    from upload_youtube import get_youtube_client, generate_metadata

    uploads = json.loads(UPLOADS_LOG.read_text(encoding="utf-8"))
    uploaded = uploads.get("uploaded", [])

    # YouTube 본편만 필터
    targets = [
        u for u in uploaded
        if u.get("fmt", "youtube") == "youtube"
        and u.get("video_id")
        and u.get("word_id")
        and (args.lang is None or u.get("lang") == args.lang)
        and (args.word_id is None or u.get("word_id") == args.word_id)
    ]
    # word_id 중복 제거 (같은 video_id 여러 번 업로드된 경우 최신 유지)
    seen = set()
    deduped = []
    for u in reversed(targets):
        key = (u.get("word_id"), u.get("lang"))
        if key not in seen:
            seen.add(key)
            deduped.append(u)
    targets = list(reversed(deduped))

    print(f"업데이트 대상: {len(targets)}개 영상 (dry-run={args.dry_run})")

    word_map = _load_words_db()
    ok, fail, skip = 0, 0, 0

    # 언어별 YouTube 클라이언트 캐시
    yt_clients = {}

    for i, u in enumerate(targets, 1):
        wid  = u["word_id"]
        lang = u.get("lang", "EN")
        vid  = u["video_id"]

        word = word_map.get(wid)
        if not word:
            print(f"[{i}/{len(targets)}] id={wid} {lang} — words_db에 없음, 스킵")
            skip += 1
            continue

        # 언어별 의미 (per-language DB에서 시도)
        lang_meaning = None
        try:
            lv = word.get("level", 1)
            lang_folder = "SP" if lang == "ES" else lang
            lv_path = _DATA_ROOT / "LanguageTest" / "TOPIK" / lang_folder / f"topik_{lv}.json"
            if lv_path.exists():
                lv_data = json.loads(lv_path.read_text(encoding="utf-8"))
                lv_words = lv_data.get("words", lv_data) if isinstance(lv_data, dict) else lv_data
                lv_w = next((w for w in lv_words if w["id"] == wid), None)
                if lv_w:
                    lang_meaning = lv_w.get("meaning")
        except Exception:
            pass

        meta = generate_metadata(word, wid, lang=lang, lang_meaning=lang_meaning, fmt="youtube")
        new_desc = meta["description"]
        new_title = meta["title"]
        new_tags  = meta.get("tags", [])

        # 예문 개수 확인
        sent_count = new_desc.count("\n     →")
        print(f"[{i}/{len(targets)}] id={wid} {word['word']} ({lang}) vid={vid[:8]} — 예문 {sent_count}개")

        if args.dry_run:
            ok += 1
            continue

        # 언어별 클라이언트
        if lang not in yt_clients:
            try:
                yt_clients[lang] = get_youtube_client(lang=lang)
            except Exception as e:
                print(f"  YouTube 인증 실패 ({lang}): {e}")
                fail += 1
                continue

        if update_description(yt_clients[lang], vid, new_title, new_desc, new_tags):
            ok += 1
            print(f"  ✓ 업데이트 완료")
        else:
            fail += 1
        time.sleep(0.5)

    print(f"\n=== 완료 === 성공 {ok} / 실패 {fail} / 스킵 {skip}")


if __name__ == "__main__":
    main()
