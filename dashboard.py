#!/usr/bin/env python3
"""Hellowords 대시보드  —  http://NAS-IP:8765"""
import glob, json, os, subprocess, sys, threading, time
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from flask import Flask, jsonify, render_template_string, request, send_from_directory

app = Flask(__name__)

BASE          = "/app"
DATA_ROOT     = f"{BASE}/data"
OUTPUT_DIR    = f"{BASE}/output"
UPLOADS_LOG   = f"{BASE}/logs/uploads.json"
PROGRESS_F    = f"{BASE}/logs/progress.json"
VIDEOS_LOG    = f"{BASE}/logs/videos_log.json"
MUSIC_DIR     = f"{BASE}/assets/music"
ILLUST_DIR    = f"{BASE}/assets/illustrations"
ILLUST_PROG_F = f"{BASE}/logs/illust_progress.json"
RENDER_CONFIG   = f"{BASE}/logs/render_config.json"
QUEUE_FILE      = f"{BASE}/logs/render_queue.json"
SCHEDULE_CONFIG = f"{BASE}/logs/schedule_config.json"
UPLOAD_SCHED_F  = f"{BASE}/logs/upload_schedule_config.json"
BATCH_QUEUE_F   = f"{BASE}/logs/batch_queue.json"
ILLUST_USAGE_F  = f"{BASE}/logs/illust_usage.json"
DAILY_AUTO_F    = f"{BASE}/logs/daily_auto.json"
PHRASES_DB_PATH   = f"{BASE}/data/Conversation/phrases_db.json"
KDRAMA_DB_PATH    = f"{BASE}/data/Conversation/kdrama_db.json"
CONV_DB_PATH    = PHRASES_DB_PATH   # 하위 호환 별칭
CONV_LOG_F      = f"{BASE}/logs/conv_log.json"
KDRAMA_LOG_F    = f"{BASE}/logs/kdrama_log.json"
KDRAMA_ILLUST_DIR   = f"{BASE}/assets/kdrama_illustrations"
KDRAMA_ILLUST_PROG  = f"{BASE}/logs/kdrama_illust_progress.json"
PHRASE_DB_F     = PHRASES_DB_PATH   # 하위 호환 별칭
PHRASE_ILLUST_DIR = f"{BASE}/assets/phrase_illustrations"
PHRASE_ILLUST_PROG= f"{BASE}/logs/phrase_illust_progress.json"
PHRASE_VIDEO_LOG  = f"{BASE}/logs/phrase_videos_log.json"
GLOBAL_QUEUE_F    = f"{BASE}/logs/global_queue.json"
DESKTOP_PHRASE_Q  = f"{BASE}/logs/desktop_phrase_queue.json"
OPEN_FOLDER_REQ_F = f"{BASE}/logs/open_folder_request.json"

DAILY_LANGS = ["EN", "CN", "JP", "VN", "ES"]
_LANG_FLAG  = {"EN":"🇺🇸","CN":"🇹🇼","JP":"🇯🇵","VN":"🇻🇳","ES":"🇲🇽"}
_LANG_NAME  = {"EN":"English","CN":"中文","JP":"日本語","VN":"Tiếng Việt","ES":"Español"}

try:
    from zoneinfo import ZoneInfo as _ZI
    _LANG_TZ = {"EN":_ZI("America/New_York"),"CN":_ZI("Asia/Taipei"),
                "JP":_ZI("Asia/Tokyo"),"VN":_ZI("Asia/Ho_Chi_Minh"),
                "ES":_ZI("America/Mexico_City")}
    _HAS_TZ = True
except Exception:
    _HAS_TZ = False
    _LANG_UTC_OFFSET_H = {"EN":-5,"CN":8,"JP":9,"VN":7,"ES":-6}

def _next_publish_at(lang: str) -> datetime:
    if _HAS_TZ:
        tz = _LANG_TZ.get(lang, _LANG_TZ["EN"])
        now_l = datetime.now(tz)
        t = now_l.replace(hour=7, minute=30, second=0, microsecond=0)
        if t <= now_l: t += timedelta(days=1)
        return t.astimezone(timezone.utc)
    off = _LANG_UTC_OFFSET_H.get(lang, -5)
    now_u = datetime.now(timezone.utc)
    now_l = now_u + timedelta(hours=off)
    t = now_l.replace(hour=7, minute=30, second=0, microsecond=0)
    if t <= now_l: t += timedelta(days=1)
    return (t - timedelta(hours=off)).replace(tzinfo=timezone.utc)

DEFAULT_SCHEDULE = {"slots": [
    {"exam":"TOPIK","lang":"EN","level":1,"fmt":"both"},
    {"exam":"TOPIK","lang":"EN","level":2,"fmt":"both"},
    {"exam":"TOPIK","lang":"EN","level":3,"fmt":"both"},
    {"exam":"TOPIK","lang":"JP","level":1,"fmt":"both"},
    {"exam":"TOPIK","lang":"JP","level":2,"fmt":"both"},
    {"exam":"TOPIK","lang":"JP","level":3,"fmt":"both"},
    {"exam":"TOPIK","lang":"ES","level":1,"fmt":"both"},
    {"exam":"TOPIK","lang":"ES","level":2,"fmt":"both"},
    {"exam":"TOPIK","lang":"ES","level":3,"fmt":"both"},
]}

# ─── 전체 콘텐츠 구조 정의 ───────────────────────────────────
STRUCTURE = {
    "시험용": {
        "icon": "📚", "color": "#6366f1",
        "exams": {
            "TOPIK":  {"flag":"🇰🇷","color":"#818cf8","levels":[1,2,3,4,5,6],
                       "langs":["EN","CN","JP","VN","ES"]},
            "TOEIC":  {"flag":"📝","color":"#60a5fa","levels":["LC","RC"],
                       "langs":["KO","CN","JP","VN"]},
            "JLPT":   {"flag":"🌸","color":"#f472b6","levels":["N5","N4","N3","N2","N1"],
                       "langs":["KO","EN","CN","VN"]},
            "IELTS":  {"flag":"🎓","color":"#a78bfa","levels":["4-5","5-6","6-7","7-8","8-9"],
                       "langs":["KO","CN","JP","VN"]},
            "HSK":    {"flag":"🐉","color":"#f87171","levels":[1,2,3,4,5,6],
                       "langs":["KO","EN","JP","VN"]},
        }
    },
    "여행용": {
        "icon": "✈️", "color": "#10b981",
        "langs": ["EN","CN","JP","VN","ES","KO","FR","DE"],
    }
}

LANG_META = {
    "EN":{"flag":"🇺🇸","name":"영어"},   "CN":{"flag":"🇨🇳","name":"중국어"},
    "JP":{"flag":"🇯🇵","name":"일본어"},  "VN":{"flag":"🇻🇳","name":"베트남어"},
    "ES":{"flag":"🇪🇸","name":"스페인어"},"KO":{"flag":"🇰🇷","name":"한국어"},
    "FR":{"flag":"🇫🇷","name":"프랑스어"},"DE":{"flag":"🇩🇪","name":"독일어"},
}

# ─── 유틸 ────────────────────────────────────────────────────
def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except: return default

def illust_exists(path: str) -> bool:
    """일러스트 파일이 실제로 존재하고 내용이 있는지 확인 (빈 파일 제외)"""
    try:
        return os.path.exists(path) and os.path.getsize(path) > 0
    except Exception:
        return False

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _normalize_words(data):
    """per-level 형식(object) → 통합 배열 형식으로 정규화"""
    if isinstance(data, dict) and "words" in data:
        file_level = data.get("level")
        words = data["words"]
        for w in words:
            if "level" not in w and file_level is not None:
                w["level"] = file_level
            if "sentences" not in w and "examples" in w:
                w["sentences"] = w["examples"]
            if "part_of_speech" not in w and "pos" in w:
                w["part_of_speech"] = w["pos"]
        return words
    if isinstance(data, list):
        return data
    return []

def get_db(category="시험용", exam="TOPIK", lang="EN"):
    """DB 로드 — 실제 파일 구조에서 읽어 통합 배열로 반환"""
    LT = f"{DATA_ROOT}/LanguageTest"
    # TOPIK: 언어별 per-level 파일 합치기
    if category == "시험용" and exam == "TOPIK":
        all_words = []
        for lv in range(1, 7):
            path = f"{LT}/TOPIK/{lang}/topik_{lv}.json"
            data = load_json(path, None)
            if data is not None:
                all_words.extend(_normalize_words(data))
        if all_words:
            return all_words
    # 다른 시험: 디렉토리 내 모든 json 합치기
    elif category == "시험용" and exam:
        exam_dir = f"{LT}/{exam}"
        if os.path.isdir(exam_dir):
            all_words = []
            for fname in sorted(os.listdir(exam_dir)):
                if fname.endswith(".json") and not fname.endswith(".bak"):
                    fpath = os.path.join(exam_dir, fname)
                    data = load_json(fpath, None)
                    if data is not None:
                        all_words.extend(_normalize_words(data))
            if all_words:
                return all_words
    # fallback
    return load_json(f"{LT}/words_db.json", [])

def render_db_path_for(exam, lang, level):
    """렌더링 시 make_video.py에 전달할 DB 파일 경로"""
    LT = f"{DATA_ROOT}/LanguageTest"
    fallback = f"{LT}/words_db.json"
    if exam == "TOPIK":
        # 1순위: per-language per-level DB (lang_localized situation+translation)
        lang_lc = lang.lower()
        per_lv = f"{LT}/words_db_{lang_lc}_{level}.json"
        if os.path.exists(per_lv):
            return per_lv
        # 2순위: per-language full DB
        per_lang = f"{LT}/words_db_{lang_lc}.json"
        if os.path.exists(per_lang):
            return per_lang
        # 3순위 (legacy): 옛 TOPIK/ 폴더 — 보통 stale, 사용 안 함
        folder = "SP" if lang == "ES" else lang
        legacy = f"{LT}/TOPIK/{folder}/topik_{level}.json"
        if os.path.exists(legacy):
            return legacy
        return fallback
    # 다른 시험: 파일명에서 level 매칭
    exam_dir = f"{LT}/{exam}"
    if os.path.isdir(exam_dir):
        level_str = str(level).lower().replace("-", "_")
        for fname in sorted(os.listdir(exam_dir)):
            if fname.endswith(".json") and not fname.endswith(".bak"):
                if level_str in fname.lower():
                    return f"{exam_dir}/{fname}"
    return fallback

# ─── 통계 ────────────────────────────────────────────────────
def get_videos_log():  return load_json(VIDEOS_LOG, [])
def get_uploads():
    d = load_json(UPLOADS_LOG, {"uploaded":[],"last_day":0})
    return d.get("uploaded",[]), d.get("last_day",0)
def get_progress():
    d = load_json(PROGRESS_F, {"status":"idle","step":"대기 중","pct":0})
    try:
        age = (datetime.now()-datetime.fromisoformat(d.get("updated_at","2000-01-01"))).total_seconds()
        if age > 300: d["status"] = "idle"
    except: pass
    return d

def get_render_config():
    cfg = load_json(RENDER_CONFIG, {"desktop_enabled": True})
    cfg["queue"] = load_json(QUEUE_FILE, {})
    return cfg

def set_render_config(desktop_enabled):
    save_json(RENDER_CONFIG, {"desktop_enabled": desktop_enabled})

def get_words_db():
    """전역 words_db.json 로드 — 일러스트 폴더명과 동일한 전역 ID(1~1800) 사용"""
    return load_json(f"{DATA_ROOT}/LanguageTest/words_db.json", [])

def get_topik_examples(level: int, word_id: int) -> list:
    """words_db.json에서 예문(sentences) 반환 — topik_N.json은 id가 달라 불일치 발생하므로 사용 안 함."""
    db = get_words_db()
    w = next((x for x in db if x["id"] == word_id), None)
    if not w:
        return []
    sents = w.get("sentences") or w.get("examples") or []
    return [{"ko": s.get("ko", ""), "en": s.get("en", "")} for s in sents]

def get_illustration_stats():
    db = get_words_db()
    stats = {"total": len(db), "word_done": 0, "sent_done": 0, "sent_total": 0, "by_level": {}}
    for w in db:
        lv = str(w.get("level", 1))
        num_sents = len(w.get("sentences", []))
        stats["by_level"].setdefault(lv, {"total": 0, "word_done": 0, "sent_total": 0, "sent_done": 0})
        stats["by_level"][lv]["total"] += 1
        stats["by_level"][lv]["sent_total"] += num_sents
        stats["sent_total"] += num_sents
        if illust_exists(f"{ILLUST_DIR}/lv{lv}/{w['id']}_{w['word']}/word.png"):
            stats["word_done"] += 1
            stats["by_level"][lv]["word_done"] += 1
        for i in range(num_sents):
            if illust_exists(f"{ILLUST_DIR}/lv{lv}/{w['id']}_{w['word']}/{i}.png"):
                stats["sent_done"] += 1
                stats["by_level"][lv]["sent_done"] += 1
    stats["progress"] = load_json(ILLUST_PROG_F, {"status": "idle", "pct": 0})
    # 일일 사용량
    from datetime import date as _date
    usage = load_json(ILLUST_USAGE_F, {})
    today = _date.today().isoformat()
    if usage.get("date") == today:
        stats["usage"] = usage
    else:
        stats["usage"] = {"date": today, "calls": 0, "success": 0, "fail": 0, "exhausted": False}
    return stats

def get_node_stats(category, exam=None, lang=None):
    """특정 노드(카테고리/시험/언어)의 통계"""
    videos = get_videos_log()
    uploaded, last_day = get_uploads()

    # 필터링
    def match(v):
        if category == "시험용":
            if exam and v.get("exam","TOPIK") != exam: return False
            if lang and v.get("language","EN") != lang: return False
        elif category == "여행용":
            if v.get("category","시험용") != "여행용": return False
            if lang and v.get("language","EN") != lang: return False
        return True

    gen = [v for v in videos if match(v)]
    upl = [u for u in uploaded if match({"exam":u.get("exam","TOPIK"),"language":u.get("lang") or u.get("language","EN")})]

    db = get_db(category, exam or "TOPIK", lang or "EN")
    by_level = defaultdict(lambda:{"total":0,"generated":0,"uploaded":0,"min_id":None,"max_id":None})
    gen_ids = {v["word_id"] for v in gen}
    upl_ids = {u["word_id"] for u in upl}
    for w in db:
        lv = str(w.get("level","?"))
        by_level[lv]["total"] += 1
        wid = w["id"]
        if by_level[lv]["min_id"] is None or wid < by_level[lv]["min_id"]:
            by_level[lv]["min_id"] = wid
        if by_level[lv]["max_id"] is None or wid > by_level[lv]["max_id"]:
            by_level[lv]["max_id"] = wid
        if wid in gen_ids: by_level[lv]["generated"] += 1
        if wid in upl_ids: by_level[lv]["uploaded"] += 1

    return {
        "total":     len(db),
        "generated": len(gen_ids),
        "uploaded":  len(upl_ids),
        "last_day":  last_day,
        "by_level":  dict(by_level),
    }

def get_next_word_id():
    db = get_db()
    done = {v["word_id"] for v in get_videos_log()}
    for w in sorted(db, key=lambda x: x["id"]):
        if w["id"] not in done: return w["id"]
    return None

def get_next_words_for_custom(exam, lang, level, count=30, start_id=None, end_id=None):
    """커스텀 렌더: 지정 시험/언어/등급의 미렌더 단어 반환 (ID범위 지원)"""
    db = get_words_db()  # 전역 ID 기반
    videos = get_videos_log()
    rendered = {v["word_id"] for v in videos
                if v.get("exam", "TOPIK") == exam and v.get("language", "EN") == lang}
    words = []
    for w in sorted(db, key=lambda x: x["id"]):
        if w.get("level") == level and w["id"] not in rendered:
            if start_id and w["id"] < start_id:
                continue
            if end_id and w["id"] > end_id:
                continue
            words.append(w)
            if len(words) >= count:
                break
    return words

def parse_ids_str(ids_str):
    """'1,3~10,15' 형식 파싱 → 정렬된 ID 리스트"""
    import re
    ids = set()
    for part in str(ids_str).split(','):
        part = part.strip()
        if not part:
            continue
        m = re.match(r'^(\d+)\s*[~\-]\s*(\d+)$', part)
        if m:
            for i in range(int(m.group(1)), int(m.group(2)) + 1):
                ids.add(i)
        elif part.isdigit():
            ids.add(int(part))
    return sorted(ids)

def get_words_by_ids(exam, lang, level, ids):
    """지정 ID 목록의 단어 반환 — 전역 words_db.json 기준"""
    db = get_words_db()
    id_set = set(ids)
    return [w for w in sorted(db, key=lambda x: x["id"])
            if w["id"] in id_set and (level is None or w.get("level") == level)]

def get_level_id_range(exam, lang, level):
    """해당 등급의 ID 범위 반환 (min_id, max_id, total)"""
    db = get_words_db()
    ids = [w["id"] for w in db if w.get("level") == level]
    if not ids:
        return None, None, 0
    return min(ids), max(ids), len(ids)

def get_music_files():
    if not os.path.isdir(MUSIC_DIR): return []
    return sorted(f for f in os.listdir(MUSIC_DIR) if f.endswith((".mp3",".wav",".m4a")))

def get_youtube_stats(video_ids):
    key = os.environ.get("YOUTUBE_API_KEY","")
    cid = os.environ.get("YOUTUBE_CHANNEL_ID","")
    if not key: return None
    try:
        from googleapiclient.discovery import build
        yt = build("youtube","v3",developerKey=key)
        result = {"channel":None,"video_stats":{}}
        if cid:
            ch = yt.channels().list(part="statistics,snippet",id=cid).execute()
            if ch.get("items"):
                s=ch["items"][0]["statistics"]
                result["channel"]={"name":ch["items"][0]["snippet"]["title"],
                    "subscribers":int(s.get("subscriberCount",0)),
                    "views":int(s.get("viewCount",0)),
                    "video_count":int(s.get("videoCount",0))}
        ids=[v for v in video_ids if v][-50:]
        if ids:
            vids=yt.videos().list(part="statistics",id=",".join(ids)).execute()
            for v in vids.get("items",[]):
                s=v["statistics"]
                result["video_stats"][v["id"]]={"views":int(s.get("viewCount",0)),"likes":int(s.get("likeCount",0))}
        return result
    except Exception as e: return {"error":str(e)}

_LANG_FLAGS_YT = {"EN":"🇺🇸","JP":"🇯🇵","CN":"🇨🇳","VN":"🇻🇳","ES":"🇲🇽"}

def _get_playlist_item_count(yt, playlist_id: str) -> int:
    """플레이리스트의 영상 수 조회"""
    try:
        resp = yt.playlists().list(part="contentDetails", id=playlist_id).execute()
        items = resp.get("items", [])
        if items:
            return int(items[0]["contentDetails"].get("itemCount", 0))
    except Exception:
        pass
    return 0

def _get_local_upload_counts(lang: str) -> dict:
    """로컬 uploads.json에서 본편/쇼츠/회화/K드라마 수 집계 (API 불필요)"""
    bonpyeon = reels = phrase = kdrama = 0
    try:
        ul = load_json(f"{BASE}/logs/uploads.json", {}).get("uploaded", [])
        for u in ul:
            if u.get("lang") != lang:
                continue
            if u.get("type") == "kdrama":
                kdrama += 1
            elif u.get("type") == "conversation" or u.get("theme_id"):
                phrase += 1
            elif u.get("fmt") == "reels":
                reels += 1
            else:
                bonpyeon += 1
        # conv_log에서 업로드 완료된 회화도 합산
        for e in load_json(CONV_LOG_F, []):
            if e.get("lang") == lang and e.get("uploaded") and e.get("fmt", "youtube") == "youtube":
                phrase += 1
        # kdrama_log에서 업로드 완료된 K드라마도 합산
        for e in load_json(KDRAMA_LOG_F, []):
            if e.get("lang") == lang and e.get("uploaded") and e.get("fmt", "youtube") == "youtube":
                kdrama += 1
    except Exception:
        pass
    return {"bonpyeon": bonpyeon, "reels": reels, "phrase": phrase, "kdrama": kdrama}


def _get_playlist_type_counts(yt, lang_playlists: dict) -> dict:
    """본편/릴스/회화 플레이리스트 영상 수 집계"""
    bonpyeon = 0
    reels    = 0
    phrase   = 0
    for key, pid in lang_playlists.items():
        if not pid:
            continue
        if key in ("shorts",):
            reels += _get_playlist_item_count(yt, pid)
        elif key in ("phrase", "phrase_shorts"):
            phrase += _get_playlist_item_count(yt, pid)
        elif key.startswith("lv"):
            bonpyeon += _get_playlist_item_count(yt, pid)
    return {"bonpyeon": bonpyeon, "reels": reels, "phrase": phrase}


def _scan_and_save_playlists(yt, lang: str, uy) -> dict:
    """채널의 모든 플레이리스트를 스캔해 제목으로 매핑, youtube_playlists.json에 저장."""
    _PT   = getattr(uy, "PLAYLIST_TITLES",              {})
    _PTS  = getattr(uy, "PLAYLIST_TITLES_SHORTS",        {})
    _PTP  = getattr(uy, "PLAYLIST_TITLES_PHRASE",        {})
    _PTPS = getattr(uy, "PLAYLIST_TITLES_PHRASE_SHORTS", {})
    title_map = {}
    for lv in range(1, 7):
        tmpl = _PT.get(lang) or _PT.get("EN", "")
        if tmpl:
            title_map[tmpl.format(level=lv)] = f"lv{lv}"
    if _PTS:  title_map[_PTS.get(lang) or _PTS.get("EN", "")] = "shorts"
    if _PTP:  title_map[_PTP.get(lang) or _PTP.get("EN", "")] = "phrase"
    if _PTPS: title_map[_PTPS.get(lang) or _PTPS.get("EN", "")] = "phrase_shorts"
    title_map.pop("", None)

    found = {}
    next_page = None
    while True:
        kwargs = dict(part="snippet", mine=True, maxResults=50)
        if next_page:
            kwargs["pageToken"] = next_page
        resp = yt.playlists().list(**kwargs).execute()
        for item in resp.get("items", []):
            t = item["snippet"]["title"]
            if t in title_map:
                found[title_map[t]] = item["id"]
        next_page = resp.get("nextPageToken")
        if not next_page:
            break

    if found:
        playlists_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "secrets", "youtube_playlists.json")
        try:
            all_pl = {}
            if os.path.exists(playlists_file):
                with open(playlists_file, encoding="utf-8") as f:
                    all_pl = json.load(f)
            all_pl.setdefault(lang, {}).update(found)
            with open(playlists_file, "w", encoding="utf-8") as f:
                json.dump(all_pl, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    return found

def get_all_channel_stats():
    """언어별 OAuth 토큰으로 각 채널 통계 조회"""
    try:
        import importlib.util, pickle
        spec = importlib.util.spec_from_file_location("upload_youtube",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload_youtube.py"))
        uy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(uy)
    except Exception as e:
        return {"channels": [], "error": str(e)}

    # 로컬 플레이리스트 캐시 로드
    playlists_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "secrets", "youtube_playlists.json")
    all_playlists = {}
    if os.path.exists(playlists_file):
        try:
            with open(playlists_file, encoding="utf-8") as f:
                all_playlists = json.load(f)
        except Exception:
            pass

    def _get_yt_client_readonly(lang):
        """토큰 저장 없이 YouTube 클라이언트 반환 (read-only FS 환경 대응)"""
        import pickle as _pickle
        from google.oauth2.credentials import Credentials as _Creds
        from google.auth.transport.requests import Request as _Req
        from googleapiclient.discovery import build as _build
        token_path = uy._token_path_for_lang(lang)
        with open(token_path, "rb") as f:
            creds = _pickle.load(f)
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(_Req())
            except Exception:
                pass
        return _build("youtube", "v3", credentials=creds)

    results = []
    for lang in ["EN", "JP", "CN", "VN", "ES"]:
        token_path = uy._token_path_for_lang(lang)
        if not os.path.exists(token_path):
            continue
        try:
            yt = _get_yt_client_readonly(lang)
            ch = yt.channels().list(
                part="statistics,snippet,contentDetails", mine=True
            ).execute()
            if ch.get("items"):
                s    = ch["items"][0]["statistics"]
                snip = ch["items"][0]["snippet"]
                lang_playlists = all_playlists.get(lang, {})
                if not lang_playlists:
                    lang_playlists = _scan_and_save_playlists(yt, lang, uy)
                    all_playlists[lang] = lang_playlists
                # 플레이리스트 API 카운트 시도, 모두 0이면 로컬 로그로 fallback
                type_counts = _get_playlist_type_counts(yt, lang_playlists) if lang_playlists else {}
                if not any(type_counts.values()):
                    type_counts = _get_local_upload_counts(lang)

                # 채널 업로드 플레이리스트에서 실제 video_id 수집
                uploads_pl = (ch["items"][0]
                              .get("contentDetails", {})
                              .get("relatedPlaylists", {})
                              .get("uploads", ""))
                video_ids = []
                if uploads_pl:
                    next_token = None
                    while True:
                        kwargs = dict(part="contentDetails", playlistId=uploads_pl, maxResults=50)
                        if next_token:
                            kwargs["pageToken"] = next_token
                        pl_res = yt.playlistItems().list(**kwargs).execute()
                        for item in pl_res.get("items", []):
                            vid = item["contentDetails"].get("videoId")
                            if vid:
                                video_ids.append(vid)
                        next_token = pl_res.get("nextPageToken")
                        if not next_token:
                            break

                # 조회수는 채널 통계 사용 (Shorts 포함 정확)
                # 좋아요/댓글은 개별 영상 합산
                total_views    = int(s.get("viewCount", 0))
                total_likes, total_comments = 0, 0
                for i in range(0, len(video_ids), 50):
                    batch = video_ids[i:i+50]
                    vres = yt.videos().list(part="statistics", id=",".join(batch)).execute()
                    for vitem in vres.get("items", []):
                        vs = vitem.get("statistics", {})
                        total_likes    += int(vs.get("likeCount", 0))
                        total_comments += int(vs.get("commentCount", 0))

                results.append({
                    "lang":        lang,
                    "flag":        _LANG_FLAGS_YT.get(lang, ""),
                    "name":        snip.get("title", lang),
                    "channel_id":  ch["items"][0]["id"],
                    "subscribers": int(s.get("subscriberCount", 0)),
                    "views":       total_views,
                    "likes":       total_likes,
                    "comments":    total_comments,
                    "video_count": int(s.get("videoCount", 0)),
                    "bonpyeon":    type_counts.get("bonpyeon", 0),
                    "reels":       type_counts.get("reels", 0),
                    "phrase":      type_counts.get("phrase", 0),
                })
        except Exception as e:
            results.append({"lang": lang, "flag": _LANG_FLAGS_YT.get(lang,""),
                            "name": lang, "error": str(e)[:120]})
    return {"channels": results}

# ─── 스케줄 / 배치 ───────────────────────────────────────────
def get_schedule():
    return load_json(SCHEDULE_CONFIG, DEFAULT_SCHEDULE)

def get_next_word_for_slot(exam, lang, level):
    db = get_db("시험용", exam, lang)
    videos = get_videos_log()
    # 같은 exam/lang/level 에서 렌더된 word_id만 필터
    rendered = {v["word_id"] for v in videos
                if v.get("exam", "TOPIK") == exam
                and v.get("language", "EN") == lang
                and v.get("level") == level}
    for w in sorted(db, key=lambda x: x["id"]):
        if w.get("level") == level and w["id"] not in rendered:
            return w
    return None

def get_batch_today():
    slots  = get_schedule().get("slots", [])
    videos = get_videos_log()
    uploaded, _ = get_uploads()
    # (exam, lang, level, word_id) 로 중복 방지 — ID가 등급별로 독립적이므로
    seen_keys: set = set()
    batch = []
    for i, slot in enumerate(slots):
        exam  = slot.get("exam", "TOPIK")
        lang  = slot.get("lang", "EN")
        level = slot.get("level", 1)
        # 슬롯의 exam/lang에 맞는 ID만 필터
        slot_vid_ids = {v["word_id"] for v in videos
                        if v.get("exam", "TOPIK") == exam and v.get("language", "EN") == lang}
        slot_upl_ids = {u["word_id"] for u in uploaded
                        if u.get("exam", "TOPIK") == exam and (u.get("lang") or u.get("language", "EN")) == lang}
        word  = get_next_word_for_slot(exam, lang, level)
        # 같은 슬롯 조합에서 이미 선택된 단어면 다음으로
        if word and (exam, lang, level, word["id"]) in seen_keys:
            db    = get_db("시험용", exam, lang)
            for w in sorted(db, key=lambda x: x["id"]):
                if w.get("level") == level and w["id"] not in slot_vid_ids and (exam, lang, level, w["id"]) not in seen_keys:
                    word = w; break
            else:
                word = None
        if word:
            seen_keys.add((exam, lang, level, word["id"]))
        status = ("uploaded" if word and word["id"] in slot_upl_ids
                  else "generated" if word and word["id"] in slot_vid_ids
                  else "pending"   if word
                  else "no_word")
        # 일러스트 존재 여부
        has_illust = False
        if word:
            lv = str(word.get("level", 1))
            has_illust = illust_exists(f"{ILLUST_DIR}/lv{lv}/{word['id']}_{word['word']}/word.png")
        batch.append({"slot": i, "exam": exam, "lang": lang, "level": level,
                      "word": word, "status": status, "has_illust": has_illust,
                      "fmt": slot.get("fmt", "both")})
    return batch

def get_batch_for_date(date_str):
    videos   = get_videos_log()
    uploaded, _ = get_uploads()
    upl_map  = {u["word_id"]: u for u in uploaded}
    result   = []
    for v in videos:
        if (v.get("generated_at") or "").startswith(date_str):
            u = upl_map.get(v["word_id"])
            result.append({"word_id": v["word_id"], "word": v["word"],
                "level": v["level"], "exam": v.get("exam","TOPIK"),
                "lang": v.get("language","EN"),
                "generated_at": v.get("generated_at"),
                "uploaded_at": u.get("uploaded_at") if u else None,
                "video_id": u.get("video_id") if u else None})
    return sorted(result, key=lambda x: x.get("generated_at",""))

# ─── 렌더링 ──────────────────────────────────────────────────
def write_queue_job(word_id, db_path=None, exam="TOPIK", lang="EN", fmt="youtube",
                    thumb_style="portrait", thumb_only=False):
    if not db_path:
        db_path = "/app/data/LanguageTest/words_db.json"
    job_id = f"{word_id}_{lang}_{fmt}_{int(time.time()*1000)}"
    save_json(QUEUE_FILE,{"job_id":job_id,"word_id":word_id,"db_path":db_path,
        "exam":exam,"lang":lang,"fmt":fmt,"thumb_style":thumb_style,
        "thumb_only":thumb_only,
        "status":"pending","claimed_by":None,"claimed_at":None,
        "created_at":datetime.now().isoformat(),"completed_at":None})
    return job_id

_render_thread = None
_illust_thread = None
_illust_proc   = None   # 일러스트 생성 서브프로세스 (취소용)
_nas_proc      = None   # NAS 렌더링 서브프로세스 (취소용)
_batch_thread  = None

# ─── 글로벌 작업 큐 ──────────────────────────────────────────
_gq_worker_thread   = None
_gq_active_job_id   = None
_gq_cancel_requested = False
_gq_active_proc     = None   # 현재 작업의 서브프로세스

def load_global_queue():
    q = load_json(GLOBAL_QUEUE_F, {"jobs": []})
    if "jobs" not in q:
        q["jobs"] = []
    return q

def save_global_queue(q):
    save_json(GLOBAL_QUEUE_F, q)

def _gq_update_job(job_id, status, pct=None, step=None, error=None):
    q = load_global_queue()
    for j in q["jobs"]:
        if j["id"] == job_id:
            j["status"] = status
            if pct is not None:  j["pct"] = pct
            if step is not None: j["step"] = step
            if error is not None: j["error"] = str(error)[:400]
            if status == "running" and not j.get("started_at"):
                j["started_at"] = datetime.now().isoformat()
            if status in ("done", "failed", "cancelled"):
                j["completed_at"] = datetime.now().isoformat()
            break
    save_global_queue(q)

def _gq_is_cancelled(job_id):
    global _gq_cancel_requested
    if _gq_cancel_requested:
        return True
    q = load_global_queue()
    for j in q["jobs"]:
        if j["id"] == job_id:
            return j["status"] == "cancelled"
    return False

def _dispatch_to_desktop_phrase(job_id, jtype, params, timeout_sec=7200):
    """desktop_phrase_queue.json에 작업을 기록하고 완료까지 폴링 (NAS worker 스레드에서 호출)"""
    save_json(DESKTOP_PHRASE_Q, {
        "job_id": job_id, "type": jtype, "params": params,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "claimed_at": None, "completed_at": None, "error": None,
    })
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if _gq_is_cancelled(job_id):
            dq = load_json(DESKTOP_PHRASE_Q, {})
            dq["status"] = "cancelled"
            save_json(DESKTOP_PHRASE_Q, dq)
            _gq_update_job(job_id, "cancelled")
            return
        dq = load_json(DESKTOP_PHRASE_Q, {})
        st = dq.get("status")
        if st == "done":
            _gq_update_job(job_id, "done", pct=100)
            return
        if st in ("failed", "error"):
            _gq_update_job(job_id, "failed", error=dq.get("error", "데스크탑 처리 실패"))
            return
        time.sleep(5)
    # 타임아웃
    dq = load_json(DESKTOP_PHRASE_Q, {})
    dq["status"] = "failed"
    dq["error"] = "2시간 초과 (timeout)"
    save_json(DESKTOP_PHRASE_Q, dq)
    _gq_update_job(job_id, "failed", error="데스크탑 작업 2시간 초과")

def enqueue_job(jtype, description, target="auto", params=None):
    """글로벌 큐에 작업 추가 → job_id 반환"""
    job_id = f"gq_{int(time.time()*1000)}_{jtype}"
    q = load_global_queue()
    q["jobs"].append({
        "id": job_id, "type": jtype, "description": description,
        "target": target, "status": "queued", "pct": 0, "step": "",
        "created_at": datetime.now().isoformat(),
        "started_at": None, "completed_at": None, "error": None,
        "params": params or {}
    })
    # 최근 100개만 유지
    q["jobs"] = q["jobs"][-100:]
    save_global_queue(q)
    _ensure_gq_worker()
    return job_id

def _run_gq_job(job):
    global _gq_cancel_requested, _nas_proc, _illust_proc, _gq_active_proc
    jtype  = job["type"]
    params = job.get("params", {})
    job_id = job["id"]
    target = job.get("target", "auto")

    try:
        if jtype == "video_batch":
            job_items   = [tuple(j) for j in params.get("job_items", [])]
            queue_items = params.get("queue_items", [])
            words_map   = {int(k): v for k, v in params.get("words_map", {}).items()}
            auto_upload = params.get("auto_upload", False)
            exam        = params.get("exam", "TOPIK")
            lang        = params.get("lang", "EN")
            thumb_style = params.get("thumb_style", "portrait")
            thumb_only  = params.get("thumb_only", False)
            save_json(BATCH_QUEUE_F, {
                "status": "running", "total": len(queue_items), "current": 0,
                "items": queue_items, "target": target,
                "started_at": datetime.now().isoformat()
            })
            run_batch_render(
                word_ids=[], target=target, exam=exam, lang=lang,
                job_items=job_items, auto_upload=auto_upload, words_map=words_map,
                thumb_style=thumb_style, thumb_only=thumb_only
            )
            bq = load_json(BATCH_QUEUE_F, {})
            if bq.get("status") == "cancelled" or _gq_cancel_requested:
                _gq_update_job(job_id, "cancelled")
            elif bq.get("status") == "done":
                _gq_update_job(job_id, "done", pct=100)
            else:
                _gq_update_job(job_id, "failed", error="배치 렌더링 실패")

        elif jtype == "illust":
            start = params.get("start", 1)
            end   = params.get("end", 10)
            mode  = params.get("mode", "both")
            cfg = get_render_config()
            if target == "desktop" and cfg.get("desktop_enabled"):
                _dispatch_to_desktop_phrase(job_id, jtype, params)
                return
            # NAS 실행
            run_illustration_generation(start, end, mode)
            prog = load_json(ILLUST_PROG_F, {})
            fs = prog.get("status", "failed")
            if fs == "done":
                _gq_update_job(job_id, "done", pct=100)
            elif fs == "cancelled" or _gq_cancel_requested:
                _gq_update_job(job_id, "cancelled")
            else:
                _gq_update_job(job_id, "failed", error=prog.get("error", ""))

        elif jtype == "phrase_illust_regen":
            cfg = get_render_config()
            if target == "desktop" and cfg.get("desktop_enabled"):
                _dispatch_to_desktop_phrase(job_id, jtype, params)
                return
            # NAS 실행
            sit_id = params.get("sit_id")
            key    = params.get("key")
            file_path = os.path.join(PHRASE_ILLUST_DIR, f"sit_{sit_id}", f"{key}.png")
            if os.path.exists(file_path):
                try: os.remove(file_path)
                except: pass
            cmd = [sys.executable, "/app/generate_phrase_illustrations.py",
                   "--db", PHRASE_DB_F, "--situation-id", str(sit_id)]
            if key == "intro":
                cmd += ["--intro-only"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _gq_active_proc = proc
            deadline = time.time() + 7200
            while proc.poll() is None:
                if time.time() > deadline:
                    proc.kill(); proc.wait()
                    _gq_active_proc = None
                    _gq_update_job(job_id, "failed", error="2시간 초과 (NAS timeout)")
                    return
                if _gq_is_cancelled(job_id):
                    proc.terminate()
                    try: proc.wait(timeout=5)
                    except: proc.kill()
                    _gq_active_proc = None
                    _gq_update_job(job_id, "cancelled")
                    return
                time.sleep(2)
            _gq_active_proc = None
            if proc.returncode == 0:
                _gq_update_job(job_id, "done", pct=100)
            else:
                err = (proc.stderr.read() or b"").decode("utf-8", errors="replace")[-400:]
                _gq_update_job(job_id, "failed", error=err)

        elif jtype in ("conv_video", "kdrama_video", "phrase_video", "phrase_illust", "kdrama_illust"):
            cfg = get_render_config()
            if target == "desktop" and cfg.get("desktop_enabled"):
                _dispatch_to_desktop_phrase(job_id, jtype, params)
                # conv/kdrama 영상 완료 시 로그 업데이트
                if jtype in ("conv_video", "kdrama_video"):
                    q_check = load_global_queue()
                    j_check = next((j for j in q_check["jobs"] if j["id"] == job_id), None)
                    if j_check and j_check["status"] == "done":
                        tid  = str(params.get("theme_id"))
                        lang = params.get("lang", "EN")
                        fmt  = params.get("fmt", "youtube")
                        if jtype == "kdrama_video":
                            vp   = _kdrama_video_path(tid, lang, fmt)
                            klog = load_kdrama_log()
                            klog = [x for x in klog if not (str(x.get("theme_id")) == tid and x.get("lang") == lang and x.get("fmt", "youtube") == fmt)]
                            klog.append({"theme_id": tid, "lang": lang, "fmt": fmt, "video_path": vp,
                                         "rendered_at": datetime.now().isoformat(), "uploaded": False})
                            save_kdrama_log(klog)
                        else:
                            vp   = _conv_video_path(tid, lang, fmt)
                            clog = load_conv_log()
                            clog = [x for x in clog if not (str(x.get("theme_id")) == tid and x.get("lang") == lang and x.get("fmt", "youtube") == fmt)]
                            clog.append({"theme_id": tid, "lang": lang, "fmt": fmt, "video_path": vp,
                                         "rendered_at": datetime.now().isoformat(), "uploaded": False})
                            save_conv_log(clog)
                return
            # NAS 실행
            if jtype == "conv_video":
                cmd = [sys.executable, "/app/make_conversation.py",
                       "--db", CONV_DB_PATH,
                       "--theme", str(params.get("theme_id")),
                       "--lang", params.get("lang", "EN"),
                       "--output", OUTPUT_DIR]
                if params.get("fmt") == "reels":
                    cmd += ["--format", "reels"]
            elif jtype == "kdrama_video":
                cmd = [sys.executable, "/app/make_conversation.py",
                       "--db", KDRAMA_DB_PATH,
                       "--theme", str(params.get("theme_id")),
                       "--lang", params.get("lang", "EN"),
                       "--output", OUTPUT_DIR,
                       "--subdir", "kdrama",
                       "--illust-dir", "kdrama_illustrations",
                       "--filename-prefix", "kdrama"]
                if params.get("fmt") == "reels":
                    cmd += ["--format", "reels"]
            elif jtype == "phrase_video":
                sit_id = params.get("sit_id")
                lang   = params.get("lang", "EN")
                cmd = [sys.executable, "/app/make_conversation.py",
                       "--db", PHRASE_DB_F,
                       "--theme", str(sit_id),
                       "--lang", lang,
                       "--output", OUTPUT_DIR,
                       "--subdir", "phrases",
                       "--illust-dir", "phrase_illustrations",
                       "--filename-prefix", "phrases"]
                if params.get("fmt") == "reels":
                    cmd += ["--format", "reels"]
            elif jtype == "kdrama_illust":
                cmd = [sys.executable, "/app/generate_kdrama_illustrations.py",
                       "--db", KDRAMA_DB_PATH]
                theme_id = params.get("theme_id")
                start  = params.get("start")
                end    = params.get("end")
                if theme_id is not None:
                    cmd += ["--theme-id", str(theme_id)]
                elif start is not None and end is not None:
                    cmd += ["--start", str(start), "--end", str(end)]
                if params.get("overwrite"):
                    cmd += ["--overwrite"]
                if params.get("intro_only"):
                    cmd += ["--intro-only"]
                if params.get("phrases_only"):
                    cmd += ["--phrases-only"]
            else:  # phrase_illust
                cmd = [sys.executable, "/app/generate_phrase_illustrations.py",
                       "--db", PHRASE_DB_F]
                sit_id = params.get("sit_id")
                start  = params.get("start")
                end    = params.get("end")
                if sit_id is not None:
                    cmd += ["--situation-id", str(sit_id)]
                elif start is not None and end is not None:
                    cmd += ["--start", str(start), "--end", str(end)]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            _gq_active_proc = proc
            deadline = time.time() + 7200
            while proc.poll() is None:
                if time.time() > deadline:
                    proc.kill(); proc.wait()
                    _gq_active_proc = None
                    _gq_update_job(job_id, "failed", error="2시간 초과 (NAS timeout)")
                    return
                if _gq_is_cancelled(job_id):
                    proc.terminate()
                    try: proc.wait(timeout=5)
                    except: proc.kill()
                    _gq_active_proc = None
                    _gq_update_job(job_id, "cancelled")
                    return
                time.sleep(5)
            _gq_active_proc = None
            out = (proc.stdout.read() or b"").decode("utf-8", errors="replace")
            if proc.returncode == 0:
                _gq_update_job(job_id, "done", pct=100)
                # conv/kdrama 완료 시 로그 업데이트
                if jtype in ("conv_video", "kdrama_video"):
                    tid  = str(params.get("theme_id"))
                    lang = params.get("lang", "EN")
                    fmt  = params.get("fmt", "youtube")
                    if jtype == "kdrama_video":
                        vp   = _kdrama_video_path(tid, lang, fmt)
                        klog = load_kdrama_log()
                        klog = [x for x in klog if not (str(x.get("theme_id")) == tid and x.get("lang") == lang and x.get("fmt", "youtube") == fmt)]
                        klog.append({"theme_id": tid, "lang": lang, "fmt": fmt, "video_path": vp,
                                     "rendered_at": datetime.now().isoformat(), "uploaded": False})
                        save_kdrama_log(klog)
                    else:
                        vp   = _conv_video_path(tid, lang, fmt)
                        clog = load_conv_log()
                        clog = [x for x in clog if not (str(x.get("theme_id")) == tid and x.get("lang") == lang and x.get("fmt", "youtube") == fmt)]
                        clog.append({"theme_id": tid, "lang": lang, "fmt": fmt, "video_path": vp,
                                     "rendered_at": datetime.now().isoformat(), "uploaded": False})
                        save_conv_log(clog)
            else:
                _gq_update_job(job_id, "failed", error=out[-600:])
    except Exception as e:
        _gq_active_proc = None
        _gq_update_job(job_id, "failed", error=str(e))

def _queue_worker_loop():
    global _gq_active_job_id, _gq_cancel_requested
    # 시작 시 stuck된 running 잡 복구 (서버 재시작 또는 크래시 후)
    try:
        q = load_global_queue()
        for j in q["jobs"]:
            if j["status"] == "running":
                _gq_update_job(j["id"], "failed", error="서버 재시작으로 중단됨")
    except Exception as e:
        print(f"[gq_worker] startup recovery error: {e}")
    while True:
        try:
            q = load_global_queue()
            nxt = next((j for j in q["jobs"] if j["status"] == "queued"), None)
            if not nxt:
                time.sleep(3)
                continue
            job_id = nxt["id"]
            _gq_active_job_id = job_id
            _gq_cancel_requested = False
            _gq_update_job(job_id, "running")
            # 최신 job 데이터 다시 읽기
            q2 = load_global_queue()
            job_fresh = next((j for j in q2["jobs"] if j["id"] == job_id), nxt)
            _run_gq_job(job_fresh)
            # 완료 후 상태가 running이면 done으로 처리
            q3 = load_global_queue()
            j3 = next((j for j in q3["jobs"] if j["id"] == job_id), None)
            if j3 and j3["status"] == "running":
                _gq_update_job(job_id, "done", pct=100)
            _gq_active_job_id = None
        except Exception as e:
            print(f"[gq_worker] {e}")
            _gq_active_job_id = None
            time.sleep(5)

def _ensure_gq_worker():
    global _gq_worker_thread
    if _gq_worker_thread is None or not _gq_worker_thread.is_alive():
        _gq_worker_thread = threading.Thread(target=_queue_worker_loop, daemon=True)
        _gq_worker_thread.start()

def _desktop_is_busy() -> bool:
    """데스크탑이 현재 렌더링 작업을 처리 중인지 확인"""
    # 단어 영상 큐
    q = load_json(QUEUE_FILE, {})
    if q.get("status") == "claimed":
        return True
    # 회화/일러스트 큐
    dq = load_json(DESKTOP_PHRASE_Q, {})
    if dq.get("status") in ("pending", "claimed"):
        return True
    # progress.json 기준: 2분 내 업데이트된 running 상태
    try:
        p = load_json(PROGRESS_F, {})
        if p.get("status") == "running":
            age = (datetime.now() - datetime.fromisoformat(
                p.get("updated_at","2000-01-01"))).total_seconds()
            if age < 120:
                return True
    except Exception:
        pass
    return False

def _is_batch_cancelled():
    if _gq_cancel_requested:
        return True
    bq = load_json(BATCH_QUEUE_F, {})
    return bq.get("status") == "cancelled"

def run_batch_render(word_ids, target="auto", db_path=None, auto_upload=False,
                     exam="TOPIK", lang="EN", words_map=None, job_items=None,
                     thumb_style="portrait", thumb_only=False):
    """target: "desktop", "nas", "auto"(글로벌 토글 따름)
    auto_upload: True면 렌더링 후 YouTube 자동 업로드
    job_items: [(word_id, lang, db_path, word_text), ...] — 다중 언어 지원 시 사용"""
    global _batch_thread
    # job_items가 있으면 per-item lang/db_path 사용, 없으면 기존 방식
    if job_items is not None:
        # 5-tuple (word_id, lang, db_path, word_text, fmt) 또는 구형 4-tuple 지원
        jobs = [j if len(j) == 5 else (*j, "youtube") for j in job_items]
    else:
        jobs = [(wid, lang, db_path, None, "youtube") for wid in word_ids]

    for i, (word_id, job_lang, job_db_path, _word_text, job_fmt) in enumerate(jobs):
        # 취소 확인
        if _is_batch_cancelled():
            bq = load_json(BATCH_QUEUE_F, {})
            for item in bq.get("items", []):
                if item.get("status") in ("pending", "rendering"):
                    item["status"] = "skipped"
            bq["status"] = "cancelled"
            bq["completed_at"] = datetime.now().isoformat()
            save_json(BATCH_QUEUE_F, bq)
            return

        render_ok = False
        try:
            bq = load_json(BATCH_QUEUE_F, {})
            bq["current"] = i
            # (word_id, lang, fmt) 셋으로 매칭
            for item in bq.get("items", []):
                if (item["word_id"] == word_id and item.get("lang", lang) == job_lang
                        and item.get("fmt", "youtube") == job_fmt):
                    item["status"] = "rendering"
                    break
            save_json(BATCH_QUEUE_F, bq)

            cfg = get_render_config()
            use_desktop = (target == "desktop") if target != "auto" else cfg.get("desktop_enabled")

            if use_desktop:
                # 데스크탑이 바쁘면 먼저 완료될 때까지 대기 (최대 45분)
                busy_deadline = time.time() + 45 * 60
                while time.time() < busy_deadline:
                    if _is_batch_cancelled(): break
                    if not _desktop_is_busy(): break
                    time.sleep(15)
                if _is_batch_cancelled(): continue

                # 여전히 바쁘면 NAS로 전환
                if _desktop_is_busy():
                    print(f"  [batch] 데스크탑 busy → NAS 폴백 ({job_lang}/{job_fmt})")
                    render_ok = run_render_nas(word_id, job_db_path, exam=exam, lang=job_lang, fmt=job_fmt, thumb_style=thumb_style, thumb_only=thumb_only)
                else:
                    # job_id로 내 작업 완료 여부 추적
                    job_id = write_queue_job(word_id, job_db_path, exam=exam, lang=job_lang, fmt=job_fmt, thumb_style=thumb_style, thumb_only=thumb_only)
                    deadline = time.time() + 40 * 60
                    finished = False
                    while time.time() < deadline:
                        if _is_batch_cancelled(): break
                        time.sleep(15)
                        rq = load_json(QUEUE_FILE, {})
                        if (rq.get("job_id") == job_id and
                                rq.get("status") in ("done", "failed")):
                            finished = True; break
                    if _is_batch_cancelled(): continue
                    if not finished:
                        print(f"  [batch] 데스크탑 타임아웃 → NAS 폴백 ({job_lang}/{job_fmt})")
                        render_ok = run_render_nas(word_id, job_db_path, exam=exam, lang=job_lang, fmt=job_fmt, thumb_style=thumb_style, thumb_only=thumb_only)
                    else:
                        rq = load_json(QUEUE_FILE, {})
                        render_ok = rq.get("status") == "done"
            else:
                render_ok = run_render_nas(word_id, job_db_path, exam=exam, lang=job_lang, fmt=job_fmt, thumb_style=thumb_style, thumb_only=thumb_only)

            # 렌더링 후 자동 업로드
            if render_ok and auto_upload and words_map and word_id in words_map:
                bq2 = load_json(BATCH_QUEUE_F, {})
                for item in bq2.get("items", []):
                    if (item["word_id"] == word_id and item.get("lang", lang) == job_lang
                            and item.get("fmt", "youtube") == job_fmt):
                        item["status"] = "uploading"
                save_json(BATCH_QUEUE_F, bq2)

                word = words_map[word_id]
                lv = word.get("level", 1)
                sub_dir = "reels" if job_fmt == "reels" else "video"
                suf = "_reels" if job_fmt == "reels" else ""
                video_path = f"/app/output/{exam}/{job_lang}/lv{lv}/{sub_dir}/{exam.lower()}_{word_id:04d}_{word['word']}_{job_lang}{suf}.mp4"
                if os.path.exists(video_path):
                    vid = run_upload(word, video_path, exam=exam, lang=job_lang)
                    if vid:
                        for item in bq2.get("items", []):
                            if (item["word_id"] == word_id and item.get("lang", lang) == job_lang
                                    and item.get("fmt", "youtube") == job_fmt):
                                item["video_id"] = vid
        except Exception as e:
            render_ok = False

        bq = load_json(BATCH_QUEUE_F, {})
        for item in bq.get("items", []):
            if (item["word_id"] == word_id and item.get("lang", lang) == job_lang
                    and item.get("fmt", "youtube") == job_fmt):
                item["status"] = "done" if render_ok else "failed"
                break
        bq["current"] = i + 1
        save_json(BATCH_QUEUE_F, bq)

    bq = load_json(BATCH_QUEUE_F, {})
    bq["status"] = "done"
    bq["completed_at"] = datetime.now().isoformat()
    save_json(BATCH_QUEUE_F, bq)

def run_render_nas(word_id, db_path=None, exam="TOPIK", lang="EN", fmt="youtube",
                   thumb_style="portrait", thumb_only=False) -> bool:
    """NAS에서 단어 영상 렌더링. True=성공, False=실패/취소"""
    global _nas_proc
    if not db_path:
        db_path = "/app/data/LanguageTest/words_db.json"
    try:
        cmd = [sys.executable,"/app/make_video.py",
            "--db",db_path,"--id",str(word_id),
            "--output","/app/output/","--exam",exam,"--lang",lang]
        if fmt == "reels":
            cmd += ["--format","reels"]
        if thumb_only:
            cmd += ["--thumb-only"]
        _nas_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cancelled = False
        while _nas_proc.poll() is None:
            if _is_batch_cancelled():
                _nas_proc.terminate()
                try: _nas_proc.wait(timeout=10)
                except Exception: _nas_proc.kill()
                cancelled = True
                break
            time.sleep(15)
        returncode = _nas_proc.returncode
        stderr_out = (_nas_proc.stderr.read() or b"").decode("utf-8", errors="replace") if not cancelled else ""
        _nas_proc = None
        if cancelled:
            return False
        if returncode != 0:
            print(f"  [NAS render FAIL] {lang}/{fmt} id={word_id}\n{stderr_out[-800:]}")
            return False
        return True
    except Exception as e:
        _nas_proc = None
        print(f"  [NAS render ERROR] {e}")
        return False

def run_upload(word, video_path, exam="TOPIK", lang="EN", publish_at=None, fmt="youtube"):
    """렌더링 완료된 영상을 YouTube에 업로드"""
    try:
        sys.path.insert(0, os.path.dirname(__file__) or "/app")
        from upload_youtube import get_youtube_client, generate_metadata, upload_video, load_upload_log, save_upload_log

        log_path = f"{BASE}/logs/uploads.json"
        upload_log = load_upload_log(log_path)
        day_number = word["id"]  # 단어 ID를 그대로 에피소드 번호로 사용

        # 언어별 의미 조회 (per-language DB에서 — 없으면 word['meaning'] 그대로)
        lang_meaning = None
        try:
            db_path = render_db_path_for(exam, lang, word.get("level", 1))
            with open(db_path, encoding="utf-8") as _f:
                _raw = json.load(_f)
            _words = _raw.get("words", _raw) if isinstance(_raw, dict) else _raw
            _pw = next((w for w in _words if w["id"] == word["id"]), None)
            if _pw:
                lang_meaning = _pw.get("meaning")
        except Exception:
            pass

        try:
            metadata = generate_metadata(word, day_number, lang=lang, lang_meaning=lang_meaning, fmt=fmt)
        except TypeError:
            metadata = generate_metadata(word, day_number, lang=lang, lang_meaning=lang_meaning)
        youtube = get_youtube_client(lang=lang)

        # 썸네일 경로 추정
        thumb_path = video_path.rsplit(".", 1)[0] + "_thumb.png"
        if not os.path.exists(thumb_path):
            # thumbnail/ 폴더에 있을 수 있음
            vdir = os.path.dirname(video_path)
            tdir = os.path.join(os.path.dirname(vdir), "thumbnail") if os.path.basename(vdir) == "video" else vdir
            tname = os.path.splitext(os.path.basename(video_path))[0] + "_thumb.png"
            alt = os.path.join(tdir, tname)
            if os.path.exists(alt):
                thumb_path = alt
            else:
                thumb_path = None

        video_id = upload_video(youtube, video_path, metadata,
                                publish_at=publish_at,
                                thumbnail_path=thumb_path if thumb_path and os.path.exists(thumb_path) else None)
        if not video_id:
            raise RuntimeError("upload_video가 video_id를 반환하지 않음")

        # 재생목록에 추가
        try:
            from upload_youtube import get_or_create_playlist, get_or_create_typed_playlist, add_to_playlist
            if fmt == "reels":
                pl_id = get_or_create_typed_playlist(youtube, lang, "shorts")
            else:
                pl_id = get_or_create_playlist(
                    youtube, lang,
                    word.get("topik_level", word.get("level", 1))
                )
            add_to_playlist(youtube, pl_id, video_id)
            print(f"  [playlist] {lang}/{fmt} 재생목록 추가 완료")
        except Exception as pe:
            print(f"  [playlist] 추가 실패 (무시): {pe}")

        if not publish_at:
            upload_log["last_day"] = day_number
            upload_log["last_word_id"] = word["id"]
        upload_log.setdefault("uploaded", []).append({
            "day": day_number,
            "word_id": word["id"],
            "word": word["word"],
            "meaning": word.get("meaning", ""),
            "lang": lang,
            "fmt": fmt,
            "video_id": video_id,
            "youtube_url": f"https://youtube.com/watch?v={video_id}",
            "scheduled_at": publish_at.isoformat() if publish_at else None,
            "uploaded_at": datetime.now().isoformat(),
        })
        save_upload_log(upload_log, log_path)
        return video_id
    except Exception as e:
        import traceback
        print(f"  업로드 실패: {e}\n{traceback.format_exc()}")
        raise  # 호출자에게 예외 전파

# ─── 회화 영상 렌더링·업로드 ──────────────────────────────────
_CONV_CAT_STYLE = {
    "여행":           ("#4F8EF7", "✈️"),
    "식사":           ("#F77C4F", "🍜"),
    "쇼핑":           ("#F7C44F", "🛍️"),
    "인사":           ("#4FF7A0", "👋"),
    "일상":           ("#A04FF7", "💬"),
    "비즈니스":       ("#4FD4F7", "💼"),
    "K-Culture":      ("#F74FA0", "🎭"),
    "의료":           ("#F74F4F", "🏥"),
    "주거":           ("#7EF74F", "🏠"),
    "여가":           ("#F7A04F", "🎮"),
    # K-드라마 카테고리
    "연애/고백/이별":  ("#FF6B9D", "💕"),
    "감탄/반응":       ("#FFB347", "😲"),
    "드라마 클리셰":   ("#C77DFF", "🎬"),
    "싸움/갈등/화해":  ("#FF6B6B", "⚡"),
    "감정 표현":       ("#74B9FF", "💙"),
    "일상 구어체":     ("#55EFC4", "💬"),
    "직장/학교":       ("#636E72", "🏢"),
    "가족/관계":       ("#FDCB6E", "👨‍👩‍👧"),
    "속어/유행어":     ("#00CEC9", "🔥"),
}

def load_kdrama_db():
    raw = load_json(KDRAMA_DB_PATH, [])
    if isinstance(raw, list):
        def _enrich(item):
            cat = item.get("category", "")
            color, emoji = _CONV_CAT_STYLE.get(cat, ("#FF6B9D", "🎭"))
            return {
                **item,
                "title": {
                    "ko": item.get("situation",""), "KR": item.get("situation",""),
                    "en": item.get("situation_en",""), "EN": item.get("situation_en",""),
                    "jp": item.get("situation_jp",""), "JP": item.get("situation_jp",""),
                    "cn": item.get("situation_cn",""), "CN": item.get("situation_cn",""),
                    "vn": item.get("situation_vn",""), "VN": item.get("situation_vn",""),
                    "es": item.get("situation_es",""), "ES": item.get("situation_es",""),
                },
                "color": item.get("color", color),
                "emoji": item.get("emoji", emoji),
            }
        return {"themes": [_enrich(item) for item in raw]}
    return raw

def load_conv_db():
    raw = load_json(CONV_DB_PATH, [])
    # phrases_db.json은 리스트 형식 — themes 형식으로 변환
    if isinstance(raw, list):
        def _enrich(item):
            cat = item.get("category", "")
            color, emoji = _CONV_CAT_STYLE.get(cat, ("#4F8EF7", "💬"))
            return {
                **item,
                "title": {"KR": item.get("situation",""), "EN": item.get("situation_en","")},
                "color": item.get("color", color),
                "emoji": item.get("emoji", emoji),
            }
        return {"themes": [_enrich(item) for item in raw]}
    return raw

def load_conv_log():
    return load_json(CONV_LOG_F, [])

def save_conv_log(log):
    save_json(CONV_LOG_F, log)

def load_kdrama_log():
    return load_json(KDRAMA_LOG_F, [])

def save_kdrama_log(log):
    save_json(KDRAMA_LOG_F, log)

def _kdrama_video_path(tid, lang, fmt):
    base = f"{OUTPUT_DIR}/kdrama/{lang}"
    if fmt == "reels":
        return f"{base}/reels/kdrama_{tid}_{lang}_reels.mp4"
    return f"{base}/kdrama_{tid}_{lang}.mp4"

def _conv_video_path(tid, lang, fmt):
    """회화 영상 실제 경로 반환 (포맷별 서브폴더)"""
    base = f"{OUTPUT_DIR}/conversation/{lang}"
    if fmt == "reels":
        return f"{base}/reels/conv_{tid}_{lang}_reels.mp4"
    return f"{base}/conv_{tid}_{lang}.mp4"

def _phrase_video_path(tid, lang, fmt="youtube"):
    """일반 회화(phrases) 영상 경로"""
    base = f"{OUTPUT_DIR}/phrases/{lang}"
    if fmt == "reels":
        return f"{base}/reels/phrases_{tid}_{lang}_reels.mp4"
    return f"{base}/phrases_{tid}_{lang}.mp4"

def _conv_thumb_path(tid, lang):
    """회화 썸네일 경로 반환"""
    return f"{OUTPUT_DIR}/conversation/{lang}/thumbnail/conv_{tid}_{lang}_thumb.png"

def _kdrama_thumb_path(tid, lang):
    """K-드라마 썸네일 경로 반환"""
    return f"{OUTPUT_DIR}/kdrama/{lang}/thumbnail/kdrama_{tid}_{lang}_thumb.png"

def _conv_path_exists(path: str) -> bool:
    """Docker /app 경로와 로컬 경로를 모두 확인"""
    if os.path.exists(path):
        return True
    # /app/... → BASE/... 로컬 변환 시도
    local = path.replace("/app/", BASE.rstrip("/") + "/", 1) if path.startswith("/app/") else path
    return os.path.exists(local)

_conv_render_thread = None
_conv_render_progress = {"status": "idle", "theme_id": None, "lang": None, "pct": 0, "msg": ""}

def run_conv_render_bg(theme_id: str, lang: str):
    global _conv_render_thread, _conv_render_progress
    if _conv_render_thread and _conv_render_thread.is_alive():
        return False, "이미 렌더링 중입니다"
    def _run():
        global _conv_render_progress
        _conv_render_progress = {"status": "running", "theme_id": theme_id, "lang": lang, "pct": 10, "msg": "렌더링 시작..."}
        try:
            cmd = [sys.executable, "/app/make_conversation.py",
                   "--db", CONV_DB_PATH,
                   "--theme", theme_id,
                   "--lang", lang,
                   "--output", OUTPUT_DIR]
            _conv_render_progress["pct"] = 20
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0:
                video_path = _conv_video_path(theme_id, lang, "youtube")
                log = load_conv_log()
                log = [x for x in log if not (x.get("theme_id") == theme_id and x.get("lang") == lang)]
                log.append({"theme_id": theme_id, "lang": lang, "video_path": video_path,
                             "rendered_at": datetime.now().isoformat(), "uploaded": False})
                save_conv_log(log)
                _conv_render_progress = {"status": "done", "theme_id": theme_id, "lang": lang, "pct": 100, "msg": "완료"}
            else:
                _conv_render_progress = {"status": "failed", "theme_id": theme_id, "lang": lang,
                                         "pct": 0, "msg": r.stderr[-400:]}
        except Exception as e:
            _conv_render_progress = {"status": "failed", "theme_id": theme_id, "lang": lang, "pct": 0, "msg": str(e)}
    _conv_render_thread = threading.Thread(target=_run, daemon=True)
    _conv_render_thread.start()
    return True, "렌더링 시작"

# ─── 회화 일러스트·영상 생성 ──────────────────────────────────
def load_phrase_db():
    return load_json(PHRASE_DB_F, [])

def load_phrase_video_log():
    return load_json(PHRASE_VIDEO_LOG, [])

_phrase_illust_thread = None
_phrase_illust_progress = {"status": "idle", "sit_id": None, "pct": 0, "msg": ""}

def run_phrase_illust_bg(sit_id: int | None, start: int | None, end: int | None):
    global _phrase_illust_thread, _phrase_illust_progress
    if _phrase_illust_thread and _phrase_illust_thread.is_alive():
        return False, "이미 생성 중입니다"
    def _run():
        global _phrase_illust_progress
        _phrase_illust_progress = {"status": "running", "sit_id": sit_id, "pct": 10, "msg": "일러스트 생성 시작..."}
        try:
            cmd = [sys.executable, "/app/generate_phrase_illustrations.py",
                   "--db", PHRASE_DB_F]
            if sit_id is not None:
                cmd += ["--situation-id", str(sit_id)]
            elif start is not None and end is not None:
                cmd += ["--start", str(start), "--end", str(end)]
            _phrase_illust_progress["pct"] = 20
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0:
                _phrase_illust_progress = {"status": "done", "sit_id": sit_id, "pct": 100, "msg": "완료"}
            else:
                _phrase_illust_progress = {"status": "failed", "sit_id": sit_id,
                                           "pct": 0, "msg": r.stderr[-400:]}
        except Exception as e:
            _phrase_illust_progress = {"status": "failed", "sit_id": sit_id, "pct": 0, "msg": str(e)}
    _phrase_illust_thread = threading.Thread(target=_run, daemon=True)
    _phrase_illust_thread.start()
    return True, "일러스트 생성 시작"

_phrase_video_thread = None
_phrase_video_progress = {"status": "idle", "sit_id": None, "pct": 0, "msg": ""}

def run_phrase_video_bg(sit_id: int | None, start: int | None, end: int | None, lang: str = "EN"):
    global _phrase_video_thread, _phrase_video_progress
    if _phrase_video_thread and _phrase_video_thread.is_alive():
        return False, "이미 영상 생성 중입니다"
    def _run():
        global _phrase_video_progress
        _phrase_video_progress = {"status": "running", "sit_id": sit_id, "pct": 10, "msg": "영상 생성 시작..."}
        try:
            ids = [sit_id] if sit_id is not None else list(range(start, end + 1))
            for i, sid in enumerate(ids):
                cmd = [sys.executable, "/app/make_conversation.py",
                       "--db", PHRASE_DB_F,
                       "--theme", str(sid),
                       "--lang", lang,
                       "--output", OUTPUT_DIR,
                       "--subdir", "phrases",
                       "--illust-dir", "phrase_illustrations",
                       "--filename-prefix", "phrases"]
                _phrase_video_progress["pct"] = 20 + int(i / len(ids) * 70)
                r = subprocess.run(cmd, capture_output=True, text=True)
                if r.returncode != 0:
                    _phrase_video_progress = {"status": "failed", "sit_id": sid,
                                              "pct": 0, "msg": r.stderr[-400:]}
                    return
            _phrase_video_progress = {"status": "done", "sit_id": sit_id, "pct": 100, "msg": "완료"}
        except Exception as e:
            _phrase_video_progress = {"status": "failed", "sit_id": sit_id, "pct": 0, "msg": str(e)}
    _phrase_video_thread = threading.Thread(target=_run, daemon=True)
    _phrase_video_thread.start()
    return True, "영상 생성 시작"

def run_conv_upload(theme_id: str, lang: str, fmt: str = "youtube"):
    """회화 영상 YouTube 업로드"""
    try:
        video_path = _conv_video_path(theme_id, lang, fmt)
        if not _conv_path_exists(video_path):
            return None, "영상 파일이 없습니다 — 먼저 렌더링하세요"

        db = load_conv_db()
        theme = next((t for t in db["themes"] if str(t["id"]) == str(theme_id)), None)
        if not theme:
            return None, f"테마 '{theme_id}'를 찾을 수 없습니다"

        sys.path.insert(0, os.path.dirname(__file__) or "/app")
        from upload_youtube import get_youtube_client, upload_video, load_upload_log, save_upload_log

        lang_key = lang.lower()
        ko_title = theme["title"].get("ko", theme_id)
        local_title = theme["title"].get(lang_key, ko_title)
        search_title = theme.get("search_title", {}).get(lang_key, local_title)
        emoji = theme.get("emoji", "💬")
        theme_num = int(theme_id) if str(theme_id).isdigit() else 0

        _CONV_HOOKS = {
            "EN": f"🔥 Master Real Korean Conversations — Phrases Natives ACTUALLY Use! {emoji}",
            "JP": f"🔥 ネイティブが実際に使う韓国語フレーズを一気にマスター！{emoji}",
            "CN": f"🔥 韩国人每天都在用的实用韩语短句！一次学会！{emoji}",
            "VN": f"🔥 Học những câu tiếng Hàn người bản xứ dùng HÀNG NGÀY! {emoji}",
            "ES": f"🔥 ¡Aprende frases coreanas REALES que los nativos usan a diario! {emoji}",
        }
        _CONV_LABELS = {
            "EN": {"title":"📖 Today's Phrases","sub":"Korean Conversation","learn":"Learn these 10 phrases by heart — you'll sound like a local!","like":"👍 Like + Subscribe for daily Korean lessons!","hash":"#LearnKorean #KoreanConversation #KoreanPhrases #Korean #한국어 #KoreanStudy #KDrama #KPop #SpeakKorean #KoreanForBeginners"},
            "JP": {"title":"📖 今日のフレーズ","sub":"韓国語会話シリーズ","learn":"この10フレーズを覚えれば、ネイティブみたいに話せる！","like":"👍 いいね＆チャンネル登録で毎日韓国語レッスン！","hash":"#韓国語 #韓国語会話 #韓国語フレーズ #韓国語勉強 #한국어 #K-POP #韓流 #韓国ドラマ #韓国語初心者 #韓国語学習"},
            "CN": {"title":"📖 今日短句","sub":"韩语日常会话","learn":"把这10句记下来，你就跟韩国人一样会说！","like":"👍 点赞＋订阅，每天学韩语！","hash":"#韩语 #韩语对话 #韩语短句 #学韩语 #한국어 #韩流 #韩剧 #K-POP #韩语入门 #韩语学习"},
            "VN": {"title":"📖 Câu hội thoại hôm nay","sub":"Hội thoại tiếng Hàn","learn":"Học thuộc 10 câu này — bạn sẽ nói tiếng Hàn như người bản xứ!","like":"👍 Like & Đăng ký để học tiếng Hàn mỗi ngày!","hash":"#tiếngHàn #hộithoạitiếngHàn #họctiếngHàn #한국어 #phimHàn #KPop #tiếngHàngiaotiếp #tiếngHàncơbản #EPSTOPIK #tiếngHànonline"},
            "ES": {"title":"📖 Frases de Hoy","sub":"Conversación en Coreano","learn":"¡Memoriza estas 10 frases y hablarás como un nativo!","like":"👍 Dale like y suscríbete para lecciones diarias!","hash":"#aprendercoreano #coreano #frasesEnCoreano #한국어 #KPop #KDrama #Hangul #coreanoParaPrincipiantes #coreanoBásico #doramas"},
        }

        hook = _CONV_HOOKS.get(lang, _CONV_HOOKS["EN"])
        L = _CONV_LABELS.get(lang, _CONV_LABELS["EN"])

        # ── phrase 10개를 설명에 포함 ────────────────────────
        phrases = theme.get("phrases", [])
        sent_lines = []
        for i, p in enumerate(phrases, 1):
            ml = p.get("my_line", {}) or {}
            ko = ml.get("ko", "")
            tr = ml.get(lang_key) or ml.get("en", "")
            if ko and tr:
                sent_lines.append(f"  {i}. {ko}\n     → {tr}")
        phrases_text = "\n".join(sent_lines) if sent_lines else ""

        # ── 풍부한 description ──────────────────────────────
        num_str = f" #{theme_num:03d}" if theme_num > 0 else ""
        shorts_suffix = " #Shorts" if fmt == "reels" else ""
        divider = "─" * 36
        if fmt == "reels":
            description = (
                f"{hook}\n\n"
                f"{L['sub']}{num_str} — {local_title}\n\n"
                f"{L['like']}\n\n"
                f"{L['hash']}"
            )
        else:
            description = (
                f"{hook}\n\n"
                f"{divider}\n"
                f"{L['title']} — {local_title}\n"
                f"{divider}\n"
                f"{phrases_text}\n\n"
                f"{L['learn']}\n\n"
                f"{L['like']}\n\n"
                f"📚 {L['sub']}{num_str}\n\n"
                f"{L['hash']}"
            )

        # ── 태그 대폭 확장 (언어별 50+ 풀) ──────────────────
        _CONV_TAGS = {
            "EN": [
                "learn Korean", "Korean conversation", "Korean phrases", "speak Korean",
                "Korean for beginners", "Korean listening", "daily Korean", "Korean speaking",
                "K-drama Korean", "K-pop Korean", "BTS Korean", "BLACKPINK Korean",
                "Stray Kids Korean", "NewJeans Korean", "aespa Korean", "TWICE Korean",
                "Korean lessons", "how to speak Korean", "real Korean", "natural Korean",
                "Korean expressions", "useful Korean", "Korean culture", "한국어",
                "한국어 공부", "한국어 회화", "Hangul", "learn Hangul", "read Hangul",
                "Korean tutorial", "Korean podcast", "Korean listening practice",
                "everyday Korean", "Korean survival phrases", "Korean travel phrases",
                "easy Korean", "Korean practice", "Korean for travel", "Korean greetings",
                "Korean slang", "Korean romance", "Korean love phrases", "Korean confession",
                "Korean apology", "Korean thank you", "Korean small talk",
                "Korean work expressions", "Korean business Korean", "Korean texting",
                "Korean for kdrama fans", "Korean for kpop fans", "Korean for army",
                "Korean formal", "Korean informal", "Korean honorifics", "Korean pronunciation",
                "learn Korean fast", "learn Korean free", "study Korean", "Korean 101",
            ],
            "JP": [
                "韓国語", "韓国語会話", "韓国語フレーズ", "韓国語勉強", "韓国語初心者",
                "韓国語日常会話", "毎日韓国語", "ハングル", "ハングル読み方", "韓国語学習",
                "韓国語リスニング", "韓国語聞き流し", "韓国語発音", "韓国語独学",
                "韓流", "韓国ドラマ韓国語", "韓ドラで学ぶ韓国語", "K-POP韓国語",
                "BTS韓国語", "BLACKPINK韓国語", "Stray Kids 韓国語", "NewJeans 韓国語",
                "TWICE 韓国語", "aespa 韓国語", "推しの韓国語", "オタ活韓国語",
                "한국어", "한국어 회화", "한국어 공부", "韓国旅行 会話", "旅行韓国語",
                "韓国語 挨拶", "韓国語 日常", "韓国語 ネイティブ", "韓国語 スラング",
                "韓国語 かわいい", "韓国語 恋愛", "韓国語 告白", "韓国語 愛してる",
                "韓国語 ありがとう", "韓国語 ごめんなさい", "韓国語 喧嘩", "韓国語 仲直り",
                "韓国語 家族", "韓国語 ビジネス", "韓国語 友達", "韓国語 SNS",
                "韓国語 新造語", "韓国語 流行語", "1日1フレーズ", "韓国語 教室",
                "ゼロから韓国語", "韓国語 タメ口", "韓国語 敬語",
            ],
            "CN": [
                "韩语", "韩语对话", "韩语短语", "学韩语", "韩语入门",
                "韩语日常会话", "每日韩语", "韩语发音", "韩语学习", "韩语听力",
                "零基础学韩语", "韩语自学", "韩剧学韩语", "韩综学韩语", "韩流",
                "K-POP韩语", "BTS韩语", "BLACKPINK韩语", "防弹少年团", "Stray Kids 韩语",
                "NewJeans 韩语", "TWICE 韩语", "aespa 韩语", "韩语口语", "韩语旅游",
                "实用韩语", "韩语打卡", "学韩文", "韩国人常用", "韩语短句", "背韩语",
                "한국어", "한국어 공부", "한국어 회화", "韩语教学", "韩语课程",
                "韩语 恋爱", "韩语 表白", "韩语 告白", "韩语 情话", "韩语 我爱你",
                "韩语 谢谢", "韩语 对不起", "韩语 吵架", "韩语 和好", "韩语 家庭",
                "韩语 职场", "韩语 朋友", "韩语 网络用语", "韩语 流行语", "韩语 新造词",
                "韩语 敬语", "韩语 半语", "韩国文化", "韩语 每日一句",
            ],
            "VN": [
                "tiếng Hàn", "hội thoại tiếng Hàn", "học tiếng Hàn", "tiếng Hàn giao tiếp",
                "tiếng Hàn cơ bản", "tiếng Hàn cho người mới", "phát âm tiếng Hàn",
                "tiếng Hàn mỗi ngày", "EPS tiếng Hàn", "EPSTOPIK", "tự học tiếng Hàn",
                "tiếng Hàn online", "tiếng Hàn miễn phí", "tiếng Hàn thực tế",
                "K-pop tiếng Hàn", "Kdrama tiếng Hàn", "BTS tiếng Hàn",
                "BLACKPINK tiếng Hàn", "Stray Kids tiếng Hàn", "NewJeans tiếng Hàn",
                "TWICE tiếng Hàn", "phim Hàn Quốc", "xem phim Hàn",
                "한국어", "한국어 공부", "한국어 회화", "đi Hàn Quốc", "visa Hàn Quốc",
                "du học Hàn Quốc", "Hangul", "học Hangul", "tiếng Hàn du lịch",
                "tiếng Hàn sơ cấp", "câu tiếng Hàn thông dụng", "tiếng Hàn dễ học",
                "tiếng Hàn tỏ tình", "tiếng Hàn yêu thương", "tiếng Hàn anh yêu em",
                "tiếng Hàn cảm ơn", "tiếng Hàn xin lỗi", "tiếng Hàn cãi nhau",
                "tiếng Hàn làm hòa", "tiếng Hàn gia đình", "tiếng Hàn công sở",
                "tiếng Hàn bạn bè", "tiếng Hàn mạng xã hội", "tiếng Hàn tuổi teen",
                "tiếng Hàn trang trọng", "tiếng Hàn thân mật", "văn hóa Hàn Quốc",
                "tiếng Hàn mỗi ngày 1 câu",
            ],
            "ES": [
                "aprender coreano", "coreano conversación", "frases en coreano",
                "coreano para principiantes", "coreano básico", "coreano del día",
                "coreano fácil", "clases de coreano", "curso de coreano",
                "pronunciación coreana", "gramática coreana", "Kpop español",
                "Kdrama español", "BTS español", "BLACKPINK español",
                "Stray Kids español", "NewJeans español", "TWICE español", "aespa español",
                "coreano kpop", "coreano kdrama", "army español", "blink español",
                "한국어", "한국어 공부", "한국어 회화", "hangul", "alfabeto coreano",
                "leer hangul", "viaje a Corea", "coreano para viajar", "Corea del Sur",
                "aprender coreano desde cero", "coreano México", "coreano latino",
                "frases útiles coreano", "doramas coreanos", "coreano romance",
                "coreano te amo", "coreano confesión", "coreano gracias",
                "coreano perdón", "coreano discusión", "coreano reconciliación",
                "coreano familia", "coreano trabajo", "coreano amigos",
                "coreano redes sociales", "coreano slang", "coreano jerga",
                "coreano formal", "coreano informal", "cultura coreana", "idioma coreano",
                "escuchar coreano", "coreano diario",
            ],
        }
        # 카테고리별 전략 태그 (상황 맞춤 — 앞쪽에 배치해 우선 선택되게)
        _CAT_BOOST = {
            "연애/고백/이별": {
                "EN": ["Korean love phrases", "Korean confession phrases", "Korean romance", "Korean dating phrases", "Korean pickup lines", "K-drama love lines", "how to say I love you in Korean"],
                "JP": ["韓国語 恋愛", "韓国語 告白", "韓国語 愛してる", "韓国語 彼氏彼女", "韓ドラ 名セリフ 告白", "韓国語 プロポーズ"],
                "CN": ["韩语 表白", "韩语 告白", "韩语 我爱你", "韩语 情话", "韩剧 经典台词 表白", "韩语 恋爱用语"],
                "VN": ["tiếng Hàn tỏ tình", "tiếng Hàn anh yêu em", "tiếng Hàn hẹn hò", "câu nói tỏ tình tiếng Hàn", "phim Hàn cảnh tỏ tình"],
                "ES": ["coreano te amo", "coreano confesión", "coreano citas", "frases románticas coreano", "cómo decir te amo en coreano"],
            },
            "감탄/반응": {
                "EN": ["Korean reactions", "Korean exclamations", "K-drama reactions", "how Koreans react", "Korean surprise phrases"],
                "JP": ["韓国語 リアクション", "韓国語 感嘆", "韓国語 びっくり", "韓国語 相槌"],
                "CN": ["韩语 感叹", "韩语 反应", "韩语 惊讶", "韩语 日常反应"],
                "VN": ["tiếng Hàn phản ứng", "tiếng Hàn cảm thán", "tiếng Hàn bất ngờ"],
                "ES": ["reacciones en coreano", "exclamaciones coreano", "coreano sorpresa"],
            },
            "드라마 클리셰": {
                "EN": ["K-drama cliche lines", "K-drama iconic phrases", "K-drama classic lines", "K-drama famous quotes"],
                "JP": ["韓国ドラマ 名セリフ", "韓ドラ あるある", "韓国ドラマ 名言"],
                "CN": ["韩剧 经典台词", "韩剧 名台词", "韩剧 名言", "韩剧 套路"],
                "VN": ["câu thoại phim Hàn kinh điển", "câu nói hay phim Hàn", "thoại phim Hàn đi vào lòng"],
                "ES": ["frases icónicas kdrama", "frases clásicas de doramas", "citas famosas kdrama"],
            },
            "싸움/갈등/화해": {
                "EN": ["Korean argument phrases", "Korean reconciliation", "Korean apology phrases", "Korean fight phrases"],
                "JP": ["韓国語 喧嘩", "韓国語 仲直り", "韓国語 謝罪", "韓国語 言い争い"],
                "CN": ["韩语 吵架", "韩语 和好", "韩语 道歉", "韩语 争吵"],
                "VN": ["tiếng Hàn cãi nhau", "tiếng Hàn làm hòa", "tiếng Hàn xin lỗi", "tiếng Hàn giận dỗi"],
                "ES": ["coreano discusión", "coreano reconciliación", "coreano disculpa", "coreano pelea"],
            },
            "감정 표현": {
                "EN": ["Korean emotions", "express emotions in Korean", "Korean feeling words", "Korean mood phrases"],
                "JP": ["韓国語 感情", "韓国語 気持ち", "韓国語 感情表現"],
                "CN": ["韩语 情感", "韩语 心情", "韩语 情绪表达"],
                "VN": ["tiếng Hàn cảm xúc", "tiếng Hàn biểu lộ cảm xúc", "tiếng Hàn tâm trạng"],
                "ES": ["coreano emociones", "expresar emociones en coreano", "coreano sentimientos"],
            },
            "일상 구어체": {
                "EN": ["Korean casual phrases", "Korean everyday phrases", "Korean small talk", "Korean colloquial"],
                "JP": ["韓国語 日常", "韓国語 タメ口", "韓国語 日常会話", "韓国語 リアル"],
                "CN": ["韩语 日常口语", "韩语 日常用语", "韩国人 日常", "韩语 生活用语"],
                "VN": ["tiếng Hàn đời thường", "tiếng Hàn thông dụng", "tiếng Hàn hàng ngày"],
                "ES": ["coreano cotidiano", "coreano diario", "frases cotidianas coreano", "coreano coloquial"],
            },
            "직장/학교": {
                "EN": ["Korean workplace phrases", "Korean school phrases", "Korean business Korean", "Korean for work"],
                "JP": ["韓国語 職場", "韓国語 学校", "韓国語 ビジネス", "韓国語 会社"],
                "CN": ["韩语 职场", "韩语 学校", "韩语 商务", "韩语 公司"],
                "VN": ["tiếng Hàn công sở", "tiếng Hàn trường học", "tiếng Hàn thương mại", "tiếng Hàn văn phòng"],
                "ES": ["coreano trabajo", "coreano escuela", "coreano de negocios", "coreano oficina"],
            },
            "가족/관계": {
                "EN": ["Korean family phrases", "Korean relationship words", "Korean family terms", "Korean for parents"],
                "JP": ["韓国語 家族", "韓国語 両親", "韓国語 兄弟姉妹", "韓国語 親戚"],
                "CN": ["韩语 家庭", "韩语 家人", "韩语 亲戚", "韩语 父母"],
                "VN": ["tiếng Hàn gia đình", "tiếng Hàn cha mẹ", "tiếng Hàn anh chị em", "tiếng Hàn họ hàng"],
                "ES": ["coreano familia", "coreano padres", "coreano hermanos", "coreano parientes"],
            },
            "속어/유행어": {
                "EN": ["Korean slang", "Korean trendy phrases", "Korean Gen Z slang", "Korean internet slang", "Korean new words"],
                "JP": ["韓国語 スラング", "韓国語 流行語", "韓国語 新造語", "韓国語 若者言葉"],
                "CN": ["韩语 俚语", "韩语 流行语", "韩语 新造词", "韩语 网络流行语"],
                "VN": ["tiếng Hàn tiếng lóng", "tiếng Hàn trend", "tiếng Hàn teen", "tiếng Hàn mạng"],
                "ES": ["coreano slang", "coreano jerga", "coreano de moda", "coreano Gen Z"],
            },
        }
        tags = _CONV_TAGS.get(lang, _CONV_TAGS["EN"])
        # 카테고리 boost: 상황 맞춤 키워드를 맨 앞에 배치
        category = theme.get("category", "")
        boost = _CAT_BOOST.get(category, {}).get(lang, [])
        # 테마 특화 태그
        theme_tags = [t for t in [search_title, local_title, ko_title, category] if t]
        # 우선순위: 카테고리 booster → 테마 특화 → 범용 풀
        all_tags = boost + theme_tags + tags
        if fmt == "reels":
            all_tags += ["Shorts", "Korean Shorts", "shorts", "Korean shorts video"]
        # 중복 제거(순서 유지) + 500자 이내로 자르기
        seen = set()
        selected, total = [], 0
        for t in all_tags:
            if not t: continue
            key = t.lower()
            if key in seen: continue
            seen.add(key)
            if total + len(t) + 1 <= 490:
                selected.append(t); total += len(t) + 1
            if len(selected) >= 35:
                break

        metadata = {
            "title": f"{emoji} {search_title}{num_str}{shorts_suffix}"[:100],
            "description": description[:4900],
            "tags": selected,            # YouTube API는 list[str] 기대
            "category_id": "27",
            "categoryId": "27",          # 하위 호환
            "default_language": "ko",
            "privacyStatus": "public",
        }

        # 회화 썸네일 경로 (새 구조: {lang}/thumbnail/)
        thumb_candidate = _conv_thumb_path(theme_id, lang)
        conv_thumb = thumb_candidate if _conv_path_exists(thumb_candidate) else None

        # 없으면 즉시 생성
        if conv_thumb is None:
            try:
                sys.path.insert(0, os.path.dirname(__file__) or "/app")
                from make_thumbnail import make_conv_thumbnail as _mct
                os.makedirs(os.path.dirname(thumb_candidate), exist_ok=True)
                _mct(theme, lang, thumb_candidate)
                conv_thumb = thumb_candidate
                print(f"  [thumb] 회화 썸네일 생성: {conv_thumb}")
            except Exception as te:
                print(f"  [thumb] 회화 썸네일 생성 실패 (무시): {te}")

        youtube = get_youtube_client(lang=lang)
        video_id = upload_video(youtube, video_path, metadata, publish_at=None, thumbnail_path=conv_thumb)

        # 재생목록에 추가
        try:
            from upload_youtube import get_or_create_typed_playlist, add_to_playlist
            ptype = "phrase_shorts" if fmt == "reels" else "phrase"
            pl_id = get_or_create_typed_playlist(youtube, lang, ptype)
            add_to_playlist(youtube, pl_id, video_id)
            print(f"  [playlist] 회화 {lang}/{fmt} 재생목록 추가 완료")
        except Exception as pe:
            print(f"  [playlist] 회화 추가 실패 (무시): {pe}")

        log_path = f"{BASE}/logs/uploads.json"
        upload_log = load_upload_log(log_path)
        upload_log.setdefault("uploaded", []).append({
            "type": "conversation",
            "theme_id": theme_id,
            "lang": lang,
            "fmt": fmt,
            "video_id": video_id,
            "youtube_url": f"https://youtube.com/watch?v={video_id}",
            "uploaded_at": datetime.now().isoformat(),
        })
        save_upload_log(upload_log, log_path)

        # conv_log 업데이트 (theme_id 타입 불일치 방지: str로 통일 비교)
        clog = load_conv_log()
        for e in clog:
            if str(e.get("theme_id")) == str(theme_id) and e.get("lang") == lang and e.get("fmt", "youtube") == fmt:
                e["uploaded"] = True
                e["video_id"] = video_id
        save_conv_log(clog)

        return video_id, None
    except Exception as e:
        import traceback; traceback.print_exc()
        return None, str(e)

def run_kdrama_upload(theme_id: str, lang: str, fmt: str = "youtube"):
    """K-드라마 영상 YouTube 업로드 (배치 업로드 공용)"""
    try:
        video_path = _kdrama_video_path(theme_id, lang, fmt)
        if not _conv_path_exists(video_path):
            return None, "영상 파일이 없습니다 — 먼저 렌더링하세요"

        db = load_kdrama_db()
        themes = db.get("themes", [])
        theme = next((t for t in themes if str(t["id"]) == str(theme_id)), None)
        if not theme:
            return None, f"테마 '{theme_id}'를 찾을 수 없습니다"

        sys.path.insert(0, os.path.dirname(__file__) or "/app")
        from upload_youtube import get_youtube_client, upload_video, load_upload_log, save_upload_log

        lang_key = lang.lower()
        ko_title = theme.get("title", {}).get("ko", str(theme_id))
        local_title = theme.get("title", {}).get(lang_key, ko_title)
        search_title = theme.get("search_title", {}).get(lang_key, local_title)
        emoji = theme.get("emoji", "🎬")
        category = theme.get("category", "")
        theme_num = int(theme_id) if str(theme_id).isdigit() else 0

        _HOOKS = {
            "EN": f"🎬 K-DRAMA Phrases Decoded! The EXACT lines you hear in every K-drama {emoji}",
            "JP": f"🎬 Kドラマ頻出フレーズ解説！韓国ドラマで絶対聞くセリフを習得 {emoji}",
            "CN": f"🎬 韩剧必学台词！你追的每部韩剧都会听到这些句子 {emoji}",
            "VN": f"🎬 Câu thoại K-Drama đỉnh cao! Nghe được trong MỌI phim Hàn Quốc {emoji}",
            "ES": f"🎬 ¡Frases ICÓNICAS de K-Dramas! Las escucharás en TODOS los doramas {emoji}",
        }
        _LABELS = {
            "EN": {"title":"📖 K-Drama Phrases","sub":"Learn Korean with K-Drama","learn":"Memorize these 10 phrases — you'll understand K-dramas WITHOUT subtitles!","like":"👍 Like + Subscribe for more K-drama Korean!","hash":"#Kdrama #LearnKorean #KoreanPhrases #KoreanConversation #한국어 #KoreanDrama #KPop #BTS #KoreanLanguage #SpeakKorean #KdramaKorean #KoreanStudy"},
            "JP": {"title":"📖 Kドラマで学ぶ韓国語","sub":"韓国ドラマで学ぶ韓国語","learn":"この10フレーズを覚えれば字幕なしで韓国ドラマが分かる！","like":"👍 いいね＆登録でKドラマ韓国語レッスン！","hash":"#韓国ドラマ #韓国語 #Kドラマ #韓流 #韓国語勉強 #韓国語フレーズ #韓国語会話 #한국어 #KPOP #推しの韓国語 #BTS韓国語"},
            "CN": {"title":"📖 韩剧学韩语","sub":"看韩剧学韩语","learn":"背下这10句，不用字幕也能看懂韩剧！","like":"👍 点赞订阅，每天学韩剧韩语！","hash":"#韩剧 #韩语 #学韩语 #韩剧台词 #韩流 #韩语入门 #韩语对话 #한국어 #K-POP #BTS #防弹少年团 #韩综"},
            "VN": {"title":"📖 Tiếng Hàn qua K-Drama","sub":"Học tiếng Hàn qua phim Hàn","learn":"Học thuộc 10 câu này — bạn xem phim Hàn KHÔNG CẦN phụ đề!","like":"👍 Like & Đăng ký để học tiếng Hàn qua K-drama!","hash":"#KDrama #phimHàn #tiếngHàn #hộithoạitiếngHàn #학tiếngHàn #한국어 #KPop #BTS #BLACKPINK #tiếngHàngiaotiếp #phimHànQuốc"},
            "ES": {"title":"📖 Coreano con K-Dramas","sub":"Aprende coreano con doramas","learn":"¡Memoriza estas 10 frases y entenderás K-dramas SIN subtítulos!","like":"👍 Dale like y suscríbete para más coreano K-drama!","hash":"#Kdrama #aprendercoreano #doramas #coreano #frasesEnCoreano #한국어 #KPop #BTS #BLACKPINK #doramascoreanos #coreanoKpop"},
        }

        hook = _HOOKS.get(lang, _HOOKS["EN"])
        L = _LABELS.get(lang, _LABELS["EN"])

        # ── phrase 10개를 설명에 포함 ────────────────────────
        phrases = theme.get("phrases", [])
        sent_lines = []
        for i, p in enumerate(phrases, 1):
            ml = p.get("my_line", {}) or {}
            ko = ml.get("ko", "")
            tr = ml.get(lang_key) or ml.get("en", "")
            if ko and tr:
                sent_lines.append(f"  {i}. {ko}\n     → {tr}")
        phrases_text = "\n".join(sent_lines) if sent_lines else ""

        num_str = f" #{theme_num:03d}" if theme_num > 0 else ""
        shorts_suffix = " #Shorts" if fmt == "reels" else ""
        divider = "─" * 36
        if fmt == "reels":
            description = (
                f"{hook}\n\n"
                f"{L['sub']}{num_str} — {local_title}\n"
                f"{('🏷 ' + category) if category else ''}\n\n"
                f"{L['like']}\n\n"
                f"{L['hash']}"
            )
        else:
            description = (
                f"{hook}\n\n"
                f"{divider}\n"
                f"{L['title']} — {local_title}\n"
                f"{('🏷 ' + category) if category else ''}\n"
                f"{divider}\n"
                f"{phrases_text}\n\n"
                f"{L['learn']}\n\n"
                f"{L['like']}\n\n"
                f"📚 {L['sub']}{num_str}\n\n"
                f"{L['hash']}"
            )

        # ── K-드라마 특화 태그 ─────────────────────────────
        _TAGS = {
            "EN": [
                "K-drama", "Kdrama", "Korean drama", "learn Korean with K-drama",
                "K-drama phrases", "Korean drama phrases", "Korean drama lines",
                "learn Korean", "Korean conversation", "Korean phrases", "speak Korean",
                "Korean for beginners", "K-drama Korean", "K-pop Korean", "BTS Korean",
                "BLACKPINK Korean", "Korean lessons", "real Korean", "natural Korean",
                "Korean expressions", "useful Korean", "Korean culture", "Netflix Korean",
                "squid game Korean", "한국어", "한국어 공부", "한국어 회화", "K드라마",
                "Korean romance phrases", "Korean confession phrases", "Korean love phrases",
            ],
            "JP": [
                "韓国ドラマ", "Kドラマ", "韓流ドラマ", "韓国ドラマ 名台詞", "韓ドラ",
                "韓ドラ 韓国語", "韓国語 ドラマ", "韓国語会話", "韓国語フレーズ",
                "韓国語勉強", "韓国語初心者", "韓国語リスニング", "韓国語学習",
                "推しの韓国語", "オタ活韓国語", "BTS韓国語", "BLACKPINK韓国語",
                "K-POP韓国語", "韓流", "毎日韓国語", "ハングル", "한국어",
                "한국어 회화", "韓国ドラマで学ぶ", "ネトフリ 韓国", "韓国語 愛してる",
                "韓国語 告白", "韓国語 かっこいい", "韓国語 名言", "韓流スター",
            ],
            "CN": [
                "韩剧", "韩国电视剧", "韩剧台词", "看韩剧学韩语", "韩剧推荐",
                "韩剧名台词", "韩剧经典台词", "韩剧学韩语", "学韩语", "韩语对话",
                "韩语短语", "韩语入门", "韩流", "K-POP韩语", "BTS韩语",
                "BLACKPINK韩语", "防弹少年团", "韩语日常会话", "韩语听力",
                "Netflix韩剧", "鱿鱼游戏", "한국어", "한국어 회화", "韩综",
                "韩语表白", "韩语告白", "韩语情话", "韩语名言", "韩国明星",
            ],
            "VN": [
                "phim Hàn", "Kdrama", "phim Hàn Quốc", "xem phim Hàn học tiếng Hàn",
                "thoại phim Hàn", "câu thoại phim Hàn", "học tiếng Hàn qua phim",
                "tiếng Hàn", "hội thoại tiếng Hàn", "tiếng Hàn giao tiếp",
                "học tiếng Hàn", "tiếng Hàn cơ bản", "tiếng Hàn cho người mới",
                "EPS tiếng Hàn", "K-pop tiếng Hàn", "BTS tiếng Hàn",
                "BLACKPINK tiếng Hàn", "Kpop", "Hàn Quốc", "한국어",
                "phim Hàn trên Netflix", "tiếng Hàn tỏ tình", "tiếng Hàn lãng mạn",
                "tiếng Hàn yêu đương", "câu nói hay phim Hàn", "Squid Game",
                "phim Hàn hay", "phim Hàn hot", "tiếng Hàn trong phim",
            ],
            "ES": [
                "Kdrama", "K-drama", "doramas coreanos", "doramas", "aprender coreano con doramas",
                "frases de K-drama", "frases de doramas", "aprender coreano",
                "coreano conversación", "frases en coreano", "coreano básico",
                "coreano para principiantes", "Kpop español", "Kdrama español",
                "BTS español", "BLACKPINK español", "coreano kpop", "coreano kdrama",
                "한국어", "Corea del Sur", "dramas coreanos", "Netflix doramas",
                "squid game coreano", "frases románticas coreano", "coreano amor",
                "coreano confesión", "coreano romántico", "coreano sentimental",
                "doramas románticos", "frases icónicas kdrama",
            ],
        }
        tags = _TAGS.get(lang, _TAGS["EN"])
        theme_tags = [t for t in [search_title, local_title, ko_title, category] if t]
        all_tags = tags + theme_tags
        if fmt == "reels":
            all_tags += ["Shorts", "K-drama Shorts", "shorts"]
        selected, total = [], 0
        for t in all_tags:
            if not t: continue
            if total + len(t) + 1 <= 490:
                selected.append(t); total += len(t) + 1
            if len(selected) >= 30:
                break

        metadata = {
            "title": f"{emoji} {search_title}{num_str}{shorts_suffix}"[:100],
            "description": description[:4900],
            "tags": selected,
            "category_id": "24",   # Entertainment (K-drama)
            "categoryId": "24",
            "default_language": "ko",
            "privacyStatus": "public",
        }

        # 썸네일 (K-드라마 전용 폴더)
        kdrama_thumb = _kdrama_thumb_path(theme_id, lang)
        if not _conv_path_exists(kdrama_thumb):
            try:
                from make_thumbnail import make_conv_thumbnail as _mct
                os.makedirs(os.path.dirname(kdrama_thumb), exist_ok=True)
                _mct(theme, lang, kdrama_thumb)
                print(f"  [thumb] K-드라마 썸네일 생성: {kdrama_thumb}")
            except Exception as te:
                print(f"  [thumb] K-드라마 썸네일 생성 실패 (무시): {te}")
        thumb = kdrama_thumb if _conv_path_exists(kdrama_thumb) else None

        youtube = get_youtube_client(lang=lang)
        vid = upload_video(youtube, video_path, metadata, publish_at=None, thumbnail_path=thumb)
        if not vid:
            return None, "upload_video가 video_id를 반환하지 않음"

        # 재생목록
        try:
            from upload_youtube import get_or_create_typed_playlist, add_to_playlist
            ptype = "phrase_shorts" if fmt == "reels" else "phrase"
            pl_id = get_or_create_typed_playlist(youtube, lang, ptype)
            add_to_playlist(youtube, pl_id, vid)
        except Exception as pe:
            print(f"  [playlist] K드라마 추가 실패 (무시): {pe}")

        klog = load_kdrama_log()
        for e in klog:
            if str(e.get("theme_id")) == str(theme_id) and e.get("lang") == lang and e.get("fmt", "youtube") == fmt:
                e["uploaded"] = True
                e["video_id"] = vid
                break
        else:
            klog.append({"theme_id": str(theme_id), "lang": lang, "fmt": fmt,
                         "video_path": video_path, "uploaded": True, "video_id": vid})
        save_kdrama_log(klog)

        up = load_json(UPLOADS_LOG, {"uploaded": [], "last_day": 0})
        up.setdefault("uploaded", []).append({
            "type": "kdrama",
            "theme_id": str(theme_id),
            "lang": lang,
            "fmt": fmt,
            "video_id": vid,
            "youtube_url": f"https://youtube.com/watch?v={vid}",
            "uploaded_at": datetime.now().isoformat(),
        })
        save_json(UPLOADS_LOG, up)

        return vid, None
    except Exception as e:
        import traceback; traceback.print_exc()
        return None, str(e)


def _run_upload_batch(count: int, lang: str = "", fmt: str = "", tab: str = "word") -> dict:
    """스케줄에 따라 대기 중인 영상을 count개 업로드"""
    done = 0
    errors = []
    try:
        if tab == "word":
            videos = load_json(VIDEOS_LOG, [])
            uploads = load_json(UPLOADS_LOG, {"uploaded": []})
            uploaded_keys = set()
            for u in uploads.get("uploaded", []):
                uploaded_keys.add((u["word_id"], u.get("lang", "EN"), u.get("fmt", "youtube")))
            pending = []
            for v in videos:
                _path = v.get("output_path", "")
                _fmt = v.get("fmt") or ("reels" if "/reels/" in _path or "_reels" in _path else "youtube")
                _lang = v.get("language", "EN")
                if lang and _lang != lang:
                    continue
                if fmt and _fmt != fmt:
                    continue
                key = (v["word_id"], _lang, _fmt)
                if key not in uploaded_keys and os.path.exists(_path):
                    pending.append((v, _lang, _fmt, _path))
            for v, _lang, _fmt, _path in pending[:count]:
                try:
                    db = get_words_db()
                    word = next((w for w in db if w["id"] == v["word_id"]), None)
                    if not word:
                        errors.append(f"단어 없음: id={v['word_id']}")
                        continue
                    vid = run_upload(word, _path, exam=v.get("exam", "TOPIK"), lang=_lang, fmt=_fmt)
                    if vid:
                        done += 1
                    else:
                        errors.append(f"업로드 실패: {v['word_id']} ({_lang}/{_fmt})")
                except Exception as e:
                    errors.append(str(e)[:200])
        elif tab == "kdrama":
            # K-드라마 탭
            klog = load_json(KDRAMA_LOG_F, [])
            pending = []
            for c in klog:
                if c.get("uploaded"):
                    continue
                _lang = c.get("lang", "EN")
                _fmt  = c.get("fmt", "youtube")
                _path = c.get("video_path", "")
                if lang and _lang != lang:
                    continue
                if fmt and _fmt != fmt:
                    continue
                if os.path.exists(_path):
                    pending.append(c)
            for c in pending[:count]:
                try:
                    vid, err = run_kdrama_upload(str(c.get("theme_id")), c.get("lang", "EN"), c.get("fmt", "youtube"))
                    if vid:
                        done += 1
                    else:
                        errors.append(f"K드라마 업로드 실패: {c.get('theme_id')} ({c.get('lang')}) — {err}")
                except Exception as e:
                    errors.append(str(e)[:200])
        else:
            # conv 탭
            conv_log = load_json(CONV_LOG_F, [])
            pending = []
            for c in conv_log:
                if c.get("uploaded"):
                    continue
                _lang = c.get("lang", "EN")
                _fmt  = c.get("fmt", "youtube")
                _path = c.get("video_path", "")
                if lang and _lang != lang:
                    continue
                if fmt and _fmt != fmt:
                    continue
                if os.path.exists(_path):
                    pending.append(c)
            for c in pending[:count]:
                try:
                    vid, err = run_conv_upload(str(c.get("theme_id")), c.get("lang", "EN"), c.get("fmt", "youtube"))
                    if vid:
                        done += 1
                    else:
                        errors.append(f"회화 업로드 실패: {c.get('theme_id')} ({c.get('lang')}) — {err}")
                except Exception as e:
                    errors.append(str(e)[:200])
    except Exception as e:
        errors.append(f"배치 전체 오류: {str(e)[:300]}")
    return {"done": done, "errors": errors}

# ─── 일별 자동 렌더링·업로드 시스템 ─────────────────────────
_daily_rendering = False
_daily_render_lock = threading.Lock()

def _next_sit_id(current_id: int) -> int:
    """다음 회화 상황 ID 반환 (순환)"""
    try:
        with open(PHRASES_DB_PATH, encoding="utf-8") as f:
            db = json.load(f)
        ids = sorted(s["id"] for s in db)
        if not ids: return 1
        if current_id not in ids: return ids[0]
        return ids[(ids.index(current_id) + 1) % len(ids)]
    except Exception:
        return 1

def _phrase_video_exists(sit_id: int, lang: str = "EN") -> bool:
    """회화 영상 파일 존재 여부 확인"""
    for fmt in ("youtube", "reels"):
        p = _phrase_video_path(sit_id, lang, fmt)
        if _conv_path_exists(p):
            return True
    return False

_phrase_rendering = False
_phrase_render_lock = threading.Lock()

def _phrase_render_job(sit_id: int, lang: str = "EN"):
    """회화 영상 렌더링 (NAS 직접)"""
    global _phrase_rendering
    try:
        cmd = [sys.executable, "/app/make_conversation.py",
               "--db", PHRASES_DB_PATH,
               "--theme", str(sit_id),
               "--lang", lang,
               "--output", OUTPUT_DIR,
               "--subdir", "phrases",
               "--illust-dir", "phrase_illustrations",
               "--filename-prefix", "phrases"]
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"  [phrase_render] 오류: {e}")
    _phrase_rendering = False

def _phrase_upload_job(sit_id: int, lang: str = "EN"):
    """회화 영상 업로드 — 언어별 렌더 영상을 각 언어 채널에 업로드"""
    try:
        from upload_youtube import (
            get_youtube_client, generate_phrase_metadata,
            upload_video, load_upload_log, save_upload_log,
            get_or_create_typed_playlist, add_to_playlist
        )
        with open(PHRASES_DB_PATH, encoding="utf-8") as f:
            db = json.load(f)
        situation = next((s for s in db if s["id"] == sit_id), None)
        if not situation: return

        s = load_json(DAILY_AUTO_F, {})
        for lg in DAILY_LANGS:
            if s.get("phrase_langs", {}).get(lg, {}).get("uploaded"):
                continue
            # 언어별 영상 파일 경로 — 반드시 루프 안에서 계산해야 각 채널에
            # 해당 언어의 영상이 올라간다. (이 계산을 루프 밖에서 한 번만 하면
            # 모든 채널에 첫 언어(EN) 영상이 올라가는 버그가 생긴다.)
            vpath = _phrase_video_path(sit_id, lg)
            if not _conv_path_exists(vpath):
                print(f"  [phrase_upload] 영상 없음 (스킵): sit_{sit_id} lang={lg} — {vpath}")
                continue
            try:
                log_path = f"{BASE}/logs/uploads_phrase_{lg.lower()}.json"
                ulog = load_upload_log(log_path)
                num = ulog.get("last_day", 0) + 1
                metadata = generate_phrase_metadata(situation, num, lang=lg)
                youtube = get_youtube_client(lang=lg)
                pub = _next_publish_at(lg)
                vid = upload_video(youtube, vpath, metadata, publish_at=pub)
                try:
                    pl = get_or_create_typed_playlist(youtube, lg, "phrase")
                    add_to_playlist(youtube, pl, vid)
                except Exception as pe:
                    print(f"  [phrase_upload] 재생목록 실패 ({lg}): {pe}")
                ulog["last_day"] = num
                ulog.setdefault("uploaded", []).append({
                    "num": num, "sit_id": sit_id,
                    "situation": situation.get("situation", ""),
                    "video_id": vid, "lang": lg,
                    "uploaded_at": datetime.now().isoformat(),
                })
                save_upload_log(ulog, log_path)
                # 상태 저장
                s = load_json(DAILY_AUTO_F, {})
                s.setdefault("phrase_langs", {}).setdefault(lg, {})["uploaded"] = True
                s["phrase_langs"][lg]["video_id"] = vid
                save_json(DAILY_AUTO_F, s)
                print(f"  [phrase_upload] {lg} 완료: {vid}")
                time.sleep(2)
            except Exception as e:
                print(f"  [phrase_upload] {lg} 오류: {e}")
    except Exception as e:
        print(f"  [phrase_upload] 전체 오류: {e}")

def _next_lv1_word_id(current_id: int) -> int:
    db = get_words_db()
    lv1 = sorted([w["id"] for w in db if w.get("level") == 1])
    if not lv1: return 1
    if current_id not in lv1: return lv1[0]
    return lv1[(lv1.index(current_id) + 1) % len(lv1)]

def _illust_exists_for(word_id: int) -> bool:
    db = get_words_db()
    w = next((x for x in db if x["id"] == word_id), None)
    if not w: return True
    lv_dir = f"{BASE}/assets/illustrations/lv{w['level']}"
    if not os.path.isdir(lv_dir): return False
    for entry in os.listdir(lv_dir):
        parts = entry.split("_", 1)
        if len(parts) == 2 and parts[0].isdigit() and parts[1] == w["word"]:
            if os.path.exists(os.path.join(lv_dir, entry, "word.png")):
                return True
    return False

def _daily_init_langs() -> dict:
    return {lg: {
        "youtube_rendered": False, "reels_rendered": False,
        "youtube_uploaded": False, "reels_uploaded": False,
        "youtube_video_id": None,  "reels_video_id":  None,
        "publish_at": _next_publish_at(lg).strftime("%Y-%m-%dT%H:%M:%SZ"),
    } for lg in DAILY_LANGS}

def _daily_render_job(word_id: int, lang: str, fmt: str):
    global _daily_rendering
    db_path = render_db_path_for("TOPIK", lang, 1)
    ok = False
    try:
        cfg2 = get_render_config()
        if cfg2.get("desktop_enabled"):
            write_queue_job(word_id, db_path, exam="TOPIK", lang=lang, fmt=fmt)
            deadline = time.time() + 40 * 60
            finished = False
            while time.time() < deadline:
                time.sleep(15)
                rq = load_json(QUEUE_FILE, {})
                if rq.get("status") in ("done", "failed"):
                    finished = True; break
            if finished and load_json(QUEUE_FILE, {}).get("status") == "done":
                ok = True
            else:
                ok = run_render_nas(word_id, db_path, exam="TOPIK", lang=lang, fmt=fmt)
        else:
            ok = run_render_nas(word_id, db_path, exam="TOPIK", lang=lang, fmt=fmt)
    except Exception as e:
        print(f"  [daily] 렌더 오류 ({lang}/{fmt}): {e}")
    s = load_json(DAILY_AUTO_F, {})
    key = "youtube_rendered" if fmt == "youtube" else "reels_rendered"
    if lang in s.get("langs", {}):
        s["langs"][lang][key] = ok
        save_json(DAILY_AUTO_F, s)
    _daily_rendering = False

def _daily_upload_job(word: dict, lang: str, fmt: str):
    lv = word.get("level", 1)
    sub = "reels" if fmt == "reels" else "video"
    suf = "_reels" if fmt == "reels" else ""
    vpath = f"/app/output/TOPIK/{lang}/lv{lv}/{sub}/topik_{word['id']:04d}_{word['word']}_{lang}{suf}.mp4"
    if not os.path.exists(vpath):
        print(f"  [daily] 영상 없음: {vpath}")
        return
    pub = None
    s = load_json(DAILY_AUTO_F, {})
    raw_pub = s.get("langs", {}).get(lang, {}).get("publish_at")
    if raw_pub:
        try: pub = datetime.fromisoformat(raw_pub.replace("Z", "+00:00"))
        except: pass
    vid = run_upload(word, vpath, exam="TOPIK", lang=lang, publish_at=pub, fmt=fmt)
    s = load_json(DAILY_AUTO_F, {})
    ku = "youtube_uploaded" if fmt == "youtube" else "reels_uploaded"
    kv = "youtube_video_id"  if fmt == "youtube" else "reels_video_id"
    if lang in s.get("langs", {}):
        s["langs"][lang][ku] = bool(vid)
        if vid: s["langs"][lang][kv] = vid
        save_json(DAILY_AUTO_F, s)

def _is_schedule_day(today: str, start_date: str, interval: int) -> bool:
    """기준일로부터 interval일 주기에 해당하는 날인지 확인"""
    try:
        d0 = datetime.strptime(start_date, "%Y-%m-%d")
        dt = datetime.strptime(today, "%Y-%m-%d")
        return dt >= d0 and (dt - d0).days % interval == 0
    except Exception:
        return True

def _next_lv1_word_ids(current_id: int, count: int) -> list:
    """오늘 처리할 단어 ID 목록 (count개)"""
    ids, last = [], current_id
    for _ in range(count):
        last = _next_lv1_word_id(last)
        ids.append(last)
    return ids

def _daily_auto_tick():
    global _daily_rendering, _phrase_rendering
    try:
        s = load_json(DAILY_AUTO_F, {})
        today = datetime.now().strftime("%Y-%m-%d")

        # ── 설정값 읽기 ───────────────────────────────────────
        word_freq      = s.get("word_freq",          "daily")
        word_render    = s.get("word_render",         "auto")
        word_illust    = s.get("word_illust",         "auto")
        word_prebuf    = int(s.get("word_prebuffer_h", 2))
        phrase_freq    = s.get("phrase_freq",         "every2days")
        phrase_render  = s.get("phrase_render",       "auto")
        phrase_illust  = s.get("phrase_illust",       "auto")
        phrase_prebuf  = int(s.get("phrase_prebuffer_h", 2))
        auto_start     = s.get("auto_start_date",     "")

        # ── 기준일 체크: 시작일 이전이면 자동 실행 안 함 ─────
        if auto_start:
            try:
                if datetime.strptime(today, "%Y-%m-%d") < datetime.strptime(auto_start, "%Y-%m-%d"):
                    return
            except Exception:
                pass

        # ── 단어 주기/개수 계산 ──────────────────────────────
        _wint = {"daily":1,"every2days":2,"every3days":3,"2perday":1,"3perday":1}
        _wcnt = {"daily":1,"every2days":1,"every3days":1,"2perday":2,"3perday":3}
        word_interval  = _wint.get(word_freq, 1)
        word_count     = _wcnt.get(word_freq, 1)
        word_day       = _is_schedule_day(today, auto_start or today, word_interval)

        # ── 날짜 전환 처리 ────────────────────────────────────
        if s.get("today") != today:
            # 단어 오늘의 ID 목록
            last_id = s.get("current_word_id", 0)
            # 현재 화수가 아직 업로드되지 않았으면 advance하지 않음
            _prev_langs = s.get("langs", {})
            _any_uploaded = any(
                _prev_langs.get(lg, {}).get("youtube_uploaded") or
                _prev_langs.get(lg, {}).get("reels_uploaded")
                for lg in DAILY_LANGS
            )
            if word_day and _any_uploaded:
                word_ids = _next_lv1_word_ids(last_id, word_count)
            else:
                # 아직 업로드 안 됐거나 오늘이 배치일 아니면 현재 ID 유지
                word_ids = s.get("current_word_ids", [last_id] if last_id else [])
            next_id  = word_ids[0] if word_ids else last_id

            # 회화 주기 확인
            _freq_map = {"daily":1,"every2days":2,"every3days":3}
            phrase_interval = _freq_map.get(phrase_freq, 2)
            last_phrase_date = s.get("phrase_last_date", "")
            phrase_due = False
            if last_phrase_date:
                try:
                    delta = (datetime.strptime(today,"%Y-%m-%d") -
                             datetime.strptime(last_phrase_date,"%Y-%m-%d")).days
                    phrase_due = (delta >= phrase_interval and
                                  _is_schedule_day(today, auto_start or today, phrase_interval))
                except Exception:
                    phrase_due = True
            else:
                phrase_due = True

            if phrase_due:
                next_sit = _next_sit_id(s.get("current_sit_id", 0))
            else:
                next_sit = s.get("current_sit_id", 1)

            s = {"auto_upload":        s.get("auto_upload", False),
                 "current_word_id":    next_id,
                 "current_word_ids":   word_ids,
                 "today":              today,
                 "word_day":           word_day,
                 "illust_done":        False,
                 "langs":              _daily_init_langs(),
                 # 설정값 유지
                 "word_freq":          word_freq,
                 "word_render":        word_render,
                 "word_illust":        word_illust,
                 "word_prebuffer_h":   word_prebuf,
                 "phrase_freq":        phrase_freq,
                 "phrase_render":      phrase_render,
                 "phrase_illust":      phrase_illust,
                 "phrase_prebuffer_h": phrase_prebuf,
                 "auto_start_date":    auto_start,
                 # 회화 관련 유지
                 "current_sit_id":     next_sit,
                 "phrase_last_date":   s.get("phrase_last_date", ""),
                 "phrase_due":         phrase_due,
                 "phrase_rendered":    False,
                 "phrase_langs":       {lg: {"uploaded": False,
                                            **({k: v for k, v in s.get("phrase_langs", {}).get(lg, {}).items()
                                                if k == "conv_ep_override"})}
                                        for lg in DAILY_LANGS}
                                       if phrase_due else s.get("phrase_langs", {}),
                 }
            save_json(DAILY_AUTO_F, s)

        if not s.get("auto_upload"): return

        # ── 단어: 오늘이 배치 실행일인지 확인 ────────────────
        if not s.get("word_day", True): goto_phrase = True
        else:
            goto_phrase = False
            word_ids = s.get("current_word_ids") or [s.get("current_word_id")]
            word_ids = [wid for wid in word_ids if wid]
            if not word_ids: goto_phrase = True

        if not goto_phrase:
            # ── 단어 사전 제작 시간 체크 ──────────────────────
            now_utc = datetime.now(timezone.utc)
            earliest_pub = None
            for lg in DAILY_LANGS:
                raw = s.get("langs", {}).get(lg, {}).get("publish_at", "")
                if raw:
                    try:
                        p = datetime.fromisoformat(raw.replace("Z","+00:00"))
                        if earliest_pub is None or p < earliest_pub:
                            earliest_pub = p
                    except Exception: pass
            if earliest_pub and now_utc < earliest_pub - timedelta(hours=word_prebuf):
                goto_phrase = True  # 아직 사전 제작 시간 아님 → 회화 처리로 넘어감

        if not goto_phrase:
            # ── 단어 일러스트 확인 ────────────────────────────
            word_id = word_ids[0]
            illust_mode = word_illust
            if not s.get("illust_done"):
                if _illust_exists_for(word_id):
                    s["illust_done"] = True; save_json(DAILY_AUTO_F, s)
                elif illust_mode in ("auto", "auto_if_missing"):
                    if _illust_proc is None:
                        threading.Thread(target=run_illustration_generation,
                            args=(word_id, word_id), kwargs={"mode":"both"}, daemon=True).start()
                    return
                # manual: 일러스트 없어도 진행 가능

            if _daily_rendering: return
            db = get_words_db()

            # ── 각 단어 ID에 대해 렌더링 ─────────────────────
            for wid in word_ids:
                word = next((w for w in db if w["id"] == wid), None)
                if not word: continue
                lv = word.get("level", 1)
                sub = "video"
                vpath = f"/app/output/TOPIK/EN/lv{lv}/{sub}/topik_{wid:04d}_{word['word']}_EN.mp4"
                for lg in DAILY_LANGS:
                    lang_key = f"word_{wid}_{lg}"
                    ls = s["langs"].get(lg, {})
                    for fmt in ("youtube", "reels"):
                        rkey = f"{fmt}_rendered"
                        # auto_if_missing: 이미 파일이 있으면 렌더링 스킵
                        if word_render == "auto_if_missing":
                            sub2 = "reels" if fmt == "reels" else "video"
                            suf2 = "_reels" if fmt == "reels" else ""
                            ep = f"/app/output/TOPIK/{lg}/lv{lv}/{sub2}/topik_{wid:04d}_{word['word']}_{lg}{suf2}.mp4"
                            if os.path.exists(ep):
                                if not ls.get(rkey):
                                    s["langs"][lg][rkey] = True
                                    save_json(DAILY_AUTO_F, s)
                                continue
                        if not ls.get(rkey) and word_render != "manual":
                            with _daily_render_lock:
                                if _daily_rendering: return
                                _daily_rendering = True
                            threading.Thread(target=_daily_render_job,
                                args=(wid, lg, fmt), daemon=True).start()
                            return

            # ── 단어 업로드 ───────────────────────────────────
            for wid in word_ids:
                word = next((w for w in db if w["id"] == wid), None)
                if not word: continue
                for lg in DAILY_LANGS:
                    ls = s["langs"].get(lg, {})
                    for fmt in ("youtube", "reels"):
                        if ls.get(f"{fmt}_rendered") and not ls.get(f"{fmt}_uploaded"):
                            threading.Thread(target=_daily_upload_job,
                                args=(word, lg, fmt), daemon=True).start()
                            time.sleep(1)

        # ── 회화 주기 처리 ───────────────────────────────────
        if s.get("phrase_due") and s.get("auto_upload"):
            sit_id = s.get("current_sit_id")
            if sit_id:
                p_render = s.get("phrase_render", "auto")
                # 회화 사전 제작 시간 체크
                now_utc = datetime.now(timezone.utc)
                phrase_prebuf_val = int(s.get("phrase_prebuffer_h", 2))
                earliest_ppub = None
                for lg in DAILY_LANGS:
                    raw = s.get("langs", {}).get(lg, {}).get("publish_at","")
                    if raw:
                        try:
                            p = datetime.fromisoformat(raw.replace("Z","+00:00"))
                            if earliest_ppub is None or p < earliest_ppub:
                                earliest_ppub = p
                        except Exception: pass
                if earliest_ppub and now_utc < earliest_ppub - timedelta(hours=phrase_prebuf_val):
                    return  # 회화 사전 제작 시간 아직 안 됨

                # 렌더링 확인
                if not s.get("phrase_rendered"):
                    video_exists = _phrase_video_exists(sit_id)
                    if video_exists or p_render == "auto_if_missing" and video_exists:
                        s["phrase_rendered"] = True
                        save_json(DAILY_AUTO_F, s)
                    elif video_exists:
                        s["phrase_rendered"] = True
                        save_json(DAILY_AUTO_F, s)
                    elif p_render in ("auto", "auto_if_missing") and not _phrase_rendering:
                        with _phrase_render_lock:
                            if not _phrase_rendering:
                                _phrase_rendering = True
                        threading.Thread(target=_phrase_render_job,
                            args=(sit_id,), daemon=True).start()
                    # manual이면 렌더링 기다리지 않음
                # 업로드 (렌더링 완료 후, 아직 안 한 언어 있으면)
                elif not all(s.get("phrase_langs", {}).get(lg, {}).get("uploaded")
                             for lg in DAILY_LANGS):
                    threading.Thread(target=_phrase_upload_job,
                        args=(sit_id,), daemon=True).start()
                # 모두 완료
                elif all(s.get("phrase_langs", {}).get(lg, {}).get("uploaded")
                         for lg in DAILY_LANGS):
                    s["phrase_due"] = False
                    s["phrase_last_date"] = s.get("today", "")
                    save_json(DAILY_AUTO_F, s)

        # ── 업로드 스케줄 체크 (4개 독립 타입) ───────────────────
        usched = load_json(UPLOAD_SCHED_F, {})
        for stype, (tab, fmt) in _SCHED_TYPE_MAP.items():
            cfg = usched.get(stype, {})
            if not cfg.get("enabled"):
                continue
            interval = int(cfg.get("interval_days", 1))
            last_run = cfg.get("last_run") or "2000-01-01"
            if _is_schedule_day(today, last_run, interval) and today != last_run:
                _run_upload_batch(int(cfg.get("count", 2)), cfg.get("lang", ""), fmt, tab)
                usched.setdefault(stype, {})["last_run"] = today
        save_json(UPLOAD_SCHED_F, usched)

    except Exception as e:
        print(f"  [daily_tick] {e}")

def _daily_scheduler_loop():
    while True:
        time.sleep(300)
        _daily_auto_tick()

threading.Thread(target=_daily_scheduler_loop, daemon=True).start()
_ensure_gq_worker()   # 글로벌 작업 큐 워커 시작

def run_illustration_generation(start, end, mode="both"):
    global _illust_proc
    try:
        save_json(ILLUST_PROG_F, {"status":"running","start":start,"end":end,"mode":mode,
            "pct":0,"done_word":0,"done_sent":0,"started_at":datetime.now().isoformat()})
        cmd = [sys.executable, "/app/generate_illustrations.py",
               "--db", "/app/data/LanguageTest/words_db.json",
               "--start", str(start), "--end", str(end)]
        if mode == "words":
            cmd.append("--words-only")
        elif mode == "sentences":
            cmd.append("--sentences-only")
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)
        _illust_proc = proc
        _, stderr_bytes = proc.communicate()
        _illust_proc = None
        rc = proc.returncode
        stderr_txt = (stderr_bytes or b"").decode("utf-8", errors="replace")[-600:].strip()
        final = load_json(ILLUST_PROG_F, {})
        if final.get("status") == "running":
            update = {**final,
                "status": "cancelled" if rc == -15 else ("done" if rc == 0 else "failed"),
                "pct": final.get("pct", 0),
                "completed_at": datetime.now().isoformat()}
            if rc != 0 and stderr_txt:
                update["error"] = stderr_txt
            save_json(ILLUST_PROG_F, update)
    except Exception as e:
        _illust_proc = None
        save_json(ILLUST_PROG_F, {"status":"failed","error":str(e)})

# ─── API ─────────────────────────────────────────────────────
@app.route("/api/overview")
def api_overview():
    videos = get_videos_log()
    uploaded, last_day = get_uploads()
    db = get_db()
    video_ids = [u.get("video_id") for u in uploaded if u.get("video_id")]
    yt = get_youtube_stats(video_ids)
    timeline = {}
    for u in uploaded:
        try:
            dt = datetime.fromisoformat(u["uploaded_at"])
            if (datetime.now()-dt).days <= 30:
                day = dt.strftime("%m/%d")
                timeline[day] = timeline.get(day,0)+1
        except: pass
    return jsonify({
        "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "progress": get_progress(),
        "render_config": get_render_config(),
        "overview": {"total":len(db),"generated":sum(1 for v in videos if os.path.exists(v.get("output_path",""))),"uploaded":len(uploaded),"last_day":last_day},
        "illustration": get_illustration_stats(),
        "music_files": get_music_files(),
        "timeline": timeline,
        "youtube": yt,
        "structure": STRUCTURE,
    })

@app.route("/api/videos/all")
def api_videos_all():
    """영상 목록 탭 전용 — 모든 언어/시험 통합"""
    videos = get_videos_log()
    uploaded, _ = get_uploads()
    upl_map = {(u.get("word_id"), u.get("lang") or u.get("language","EN"), u.get("exam","TOPIK"), u.get("fmt","youtube")): u for u in uploaded}
    result = []
    for v in sorted(videos, key=lambda x: (x.get("exam",""), x.get("language",""), x.get("word_id",0))):
        # fmt 필드: 신규 로그는 직접, 구형 로그는 output_path로 추론
        _path = v.get("output_path", "")
        _fmt = v.get("fmt") or ("reels" if "/reels/" in _path or "_reels" in _path else "youtube")
        key = (v["word_id"], v.get("language","EN"), v.get("exam","TOPIK"), _fmt)
        ul = upl_map.get(key)
        result.append({
            "word_id":      v["word_id"],
            "word":         v.get("word",""),
            "level":        v.get("level",1),
            "meaning":      v.get("meaning",""),
            "exam":         v.get("exam","TOPIK"),
            "language":     v.get("language","EN"),
            "fmt":          _fmt,
            "music_file":   v.get("music_file"),
            "file_size":    v.get("file_size",0),
            "generated_at": v.get("generated_at"),
            "video_id":     ul.get("video_id") if ul else None,
            "uploaded_at":  ul.get("uploaded_at") if ul else None,
            "day":          ul.get("day") if ul else None,
            "file_exists":  os.path.exists(_path),
            "views": 0, "likes": 0,
        })
    return jsonify({"video_list": result})

@app.route("/api/node")
def api_node():
    cat   = request.args.get("category","시험용")
    exam  = request.args.get("exam")
    lang  = request.args.get("lang")
    level = request.args.get("level")  # 단계 필터 (선택)
    stats = get_node_stats(cat, exam, lang)
    videos = get_videos_log()
    uploaded, _ = get_uploads()
    upl_map = {u["word_id"]:u for u in uploaded
               if (not exam or u.get("exam","TOPIK") == exam) and (not lang or (u.get("lang") or u.get("language","EN")) == lang)}
    vid_map = {v["word_id"]:v for v in videos
               if (not exam or v.get("exam","TOPIK") == exam) and (not lang or v.get("language","EN") == lang)}
    db = get_db(cat, exam or "TOPIK", lang or "EN")
    # 단계 필터 적용
    if level:
        level_int = int(level)
        db = [w for w in db if w.get("level", 0) == level_int]
        db_ids = {w["id"] for w in db}
        vid_map = {wid: v for wid, v in vid_map.items() if wid in db_ids}
        upl_map = {wid: u for wid, u in upl_map.items() if wid in db_ids}
        stats["total"]     = len(db)
        stats["generated"] = len(vid_map)
        stats["uploaded"]  = len(upl_map)
        lv_s = str(level_int)
        stats["by_level"]  = {lv_s: stats.get("by_level", {}).get(lv_s, {
            "total": len(db), "generated": len(vid_map), "uploaded": len(upl_map),
            "min_id": min((w["id"] for w in db), default=None),
            "max_id": max((w["id"] for w in db), default=None),
        })}
    video_ids = [u.get("video_id") for u in uploaded if u.get("video_id")]
    yt_stats = (get_youtube_stats(video_ids) or {}).get("video_stats",{})
    video_list = []
    for w in sorted(db, key=lambda x:x["id"]):
        vl = vid_map.get(w["id"])
        ul = upl_map.get(w["id"])
        if not vl and not ul: continue
        vid_id = ul.get("video_id") if ul else None
        yv = yt_stats.get(vid_id,{}) if vid_id else {}
        video_list.append({"word_id":w["id"],"word":w["word"],"level":w["level"],
            "meaning":w["meaning"],"music_file":vl.get("music_file") if vl else None,
            "file_size":vl.get("file_size",0) if vl else 0,
            "generated_at":vl.get("generated_at") if vl else None,
            "video_id":vid_id,"uploaded_at":ul.get("uploaded_at") if ul else None,
            "day":ul.get("day") if ul else None,
            "views":yv.get("views",0),"likes":yv.get("likes",0)})
    return jsonify({**stats,"video_list":video_list[-200:],"db_path":db_path_for(cat,exam,lang),"level":level})

@app.route("/api/queue")
def api_global_queue():
    """글로벌 작업 큐 조회"""
    q = load_global_queue()
    jobs = q.get("jobs", [])
    # 실행 중인 작업에 실시간 진행률 주입
    for job in jobs:
        if job["status"] == "running":
            if job["type"] == "video_batch":
                bq = load_json(BATCH_QUEUE_F, {})
                total = bq.get("total", 1) or 1
                current = bq.get("current", 0)
                # progress.json 에서 현재 항목 내부 진행률 반영
                p = load_json(PROGRESS_F, {})
                sub_pct = p.get("pct", 0) if p.get("status") == "running" else 0
                job["pct"] = min(int((current + sub_pct / 100) / total * 100), 99)
                sub_step = p.get("step", "") if sub_pct > 0 else ""
                job["step"] = f"{current}/{total}" + (f" — {sub_step}" if sub_step else "")
                job["batch_items"] = bq.get("items", [])
            elif job["type"] == "illust":
                if job.get("target") == "desktop":
                    dq = load_json(DESKTOP_PHRASE_Q, {})
                    dq_st = dq.get("status", "") if dq.get("job_id") == job["id"] else "pending"
                    if dq_st == "pending":
                        job["pct"] = 10; job["step"] = "GPU 전송 대기 중..."
                    elif dq_st == "claimed":
                        # illust_progress.json 에서 실제 진행률 읽기
                        ip = load_json(ILLUST_PROG_F, {})
                        if ip.get("status") == "running":
                            job["pct"] = ip.get("pct", 30)
                            job["step"] = ip.get("step", "GPU 처리 중...")
                            job["current_word_id"]  = ip.get("current_word_id")
                            job["current_type"]     = ip.get("current_type", "")
                            job["current_sent_idx"] = ip.get("current_sent_idx")
                        else:
                            job["pct"] = 30; job["step"] = "GPU 처리 중..."
                    elif dq_st == "done":
                        job["pct"] = 99; job["step"] = "완료 대기 중..."
                    else:
                        job["pct"] = 20; job["step"] = dq_st
                else:
                    ip = load_json(ILLUST_PROG_F, {})
                    job["pct"] = ip.get("pct", 0)
                    job["step"] = ip.get("current_word", "")
                    job["current_word_id"]  = ip.get("current_word_id")
                    job["current_type"]     = ip.get("current_type", "")
                    job["current_sent_idx"] = ip.get("current_sent_idx")
            elif job["type"] == "phrase_illust":
                if job.get("target") == "desktop":
                    # desktop 디스패치 중: desktop_phrase_queue 상태로 pct 표시
                    dq = load_json(DESKTOP_PHRASE_Q, {})
                    dq_job_id = dq.get("job_id", "")
                    dq_st = dq.get("status", "") if dq_job_id == job["id"] else "pending"
                    if dq_st == "pending":
                        job["pct"] = 10; job["step"] = "GPU 전송 대기 중..."
                    elif dq_st == "claimed":
                        job["pct"] = 30; job["step"] = "GPU 처리 중..."
                    elif dq_st == "done":
                        job["pct"] = 99; job["step"] = "완료 대기 중..."
                    else:
                        job["pct"] = 20; job["step"] = dq_st
                else:
                    params = job.get("params", {})
                    sit_id = params.get("sit_id")
                    start = params.get("start") or (sit_id if sit_id else 1)
                    end = params.get("end") or (sit_id if sit_id else start)
                    try:
                        start, end = int(start), int(end)
                        total_items = (end - start + 1) * 11
                        # 실제 파일 존재 여부로 카운트 (progress 기억 무시)
                        done_count = 0
                        for sid in range(start, end + 1):
                            sit_dir = os.path.join(PHRASE_ILLUST_DIR, f"sit_{sid}")
                            if os.path.isdir(sit_dir):
                                if os.path.isfile(os.path.join(sit_dir, "intro.png")):
                                    done_count += 1
                                done_count += len([f for f in os.listdir(sit_dir) if f.startswith("phrase_") and f.endswith(".png")])
                        job["pct"] = min(int(done_count / total_items * 100), 99) if total_items > 0 else 0
                        job["step"] = f"{done_count}/{total_items}"
                    except Exception:
                        pass
            elif job["type"] in ("conv_video", "kdrama_video", "phrase_video"):
                # progress.json 에서 실시간 진행률 주입
                p = load_json(PROGRESS_F, {})
                if p.get("status") == "running":
                    job["pct"] = p.get("pct", 0)
                    step = p.get("step", "")
                    frame = p.get("frame")
                    total_frames = p.get("total_frames")
                    if frame is not None and total_frames:
                        step = f"{step} [{frame}/{total_frames}f]"
                    job["step"] = step
                    job["frame"] = frame
                    job["total_frames"] = total_frames
    cfg = get_render_config()
    return jsonify({
        "jobs": jobs,
        "active_job_id": _gq_active_job_id,
        "render_config": cfg,
        "desktop_busy": _desktop_is_busy(),
    })

@app.route("/api/queue/cancel/<job_id>", methods=["POST"])
def api_cancel_job(job_id):
    """개별 작업 취소"""
    global _gq_cancel_requested, _nas_proc, _illust_proc, _gq_active_proc
    q = load_global_queue()
    job = next((j for j in q["jobs"] if j["id"] == job_id), None)
    if not job:
        return jsonify({"error": "작업을 찾을 수 없습니다"}), 404
    if job["status"] == "queued":
        job["status"] = "cancelled"
        job["completed_at"] = datetime.now().isoformat()
        save_global_queue(q)
        return jsonify({"status": "cancelled"})
    if job["status"] == "running":
        _gq_cancel_requested = True
        job["status"] = "cancelled"
        job["completed_at"] = datetime.now().isoformat()
        save_global_queue(q)
        # NAS 프로세스 종료 (NAS 실행 잡인 경우)
        if _gq_active_job_id == job_id:
            for proc in [_nas_proc, _illust_proc, _gq_active_proc]:
                if proc and proc.poll() is None:
                    try:
                        proc.terminate()
                        proc.wait(timeout=5)
                    except Exception:
                        try: proc.kill()
                        except Exception: pass
        # 데스크탑 렌더링 취소 신호: render_queue.json 상태를 cancelled로 변경
        rq = load_json(QUEUE_FILE, {})
        if rq.get("status") in ("pending", "claimed"):
            rq["status"] = "cancelled"
            rq["error"] = "cancelled"
            rq["completed_at"] = datetime.now().isoformat()
            save_json(QUEUE_FILE, rq)
        # batch_queue.json도 취소 처리
        bq = load_json(BATCH_QUEUE_F, {})
        if bq.get("status") == "running":
            bq["status"] = "cancelled"
            bq["completed_at"] = datetime.now().isoformat()
            save_json(BATCH_QUEUE_F, bq)
        # progress.json 즉시 idle로 리셋 (녹색 불 유지 방지)
        save_json(PROGRESS_F, {"status": "idle", "step": "", "pct": 0,
                               "updated_at": datetime.now().isoformat()})
        return jsonify({"status": "cancelled"})
    return jsonify({"status": "nothing_to_cancel"})

@app.route("/api/open-folder", methods=["POST"])
def api_open_folder():
    """완료된 작업의 출력 폴더를 데스크탑에서 열기"""
    data = request.get_json(silent=True) or {}
    job_id = data.get("job_id", "")
    q = load_global_queue()
    job = next((j for j in q["jobs"] if j["id"] == job_id), None)
    if not job:
        return jsonify({"error": "작업을 찾을 수 없습니다"}), 404
    jtype  = job["type"]
    params = job.get("params", {})
    if jtype == "conv_video":
        lang   = params.get("lang", "EN")
        folder = f"/app/output/conversation/{lang}"
    elif jtype == "kdrama_video":
        lang   = params.get("lang", "EN")
        folder = f"/app/output/kdrama/{lang}"
    elif jtype in ("video_batch",):
        folder = "/app/output"
    elif jtype == "illust":
        folder = "/app/assets/illustrations"
    elif jtype in ("phrase_illust", "phrase_illust_regen"):
        sit_id = params.get("sit_id")
        folder = f"/app/assets/phrase_illustrations/sit_{sit_id}" if sit_id else "/app/assets/phrase_illustrations"
    else:
        folder = "/app/output"
    save_json(OPEN_FOLDER_REQ_F, {"path": folder, "requested_at": datetime.now().isoformat()})
    return jsonify({"status": "ok", "path": folder})

@app.route("/api/queue/delete/<job_id>", methods=["POST"])
def api_delete_job(job_id):
    """완료/실패/취소된 작업 큐에서 삭제"""
    q = load_global_queue()
    job = next((j for j in q["jobs"] if j["id"] == job_id), None)
    if not job:
        return jsonify({"error": "작업을 찾을 수 없습니다"}), 404
    if job["status"] in ("queued", "running"):
        return jsonify({"error": "진행 중인 작업은 삭제할 수 없습니다"}), 400
    q["jobs"] = [j for j in q["jobs"] if j["id"] != job_id]
    save_global_queue(q)
    return jsonify({"status": "deleted"})

@app.route("/api/queue/restart/<job_id>", methods=["POST"])
def api_restart_job(job_id):
    """실패/취소된 작업을 동일한 파라미터로 재시작"""
    q = load_global_queue()
    job = next((j for j in q["jobs"] if j["id"] == job_id), None)
    if not job:
        return jsonify({"error": "작업을 찾을 수 없습니다"}), 404
    if job["status"] not in ("failed", "cancelled"):
        return jsonify({"error": "실패하거나 취소된 작업만 재시작할 수 있습니다"}), 400
    new_job_id = enqueue_job(
        job["type"], job["description"],
        target=job.get("target", "auto"),
        params=job.get("params", {})
    )
    return jsonify({"status": "queued", "job_id": new_job_id})

@app.route("/api/queue/target/<job_id>", methods=["POST"])
def api_set_job_target(job_id):
    """큐에 대기 중인 작업의 렌더링 대상 변경"""
    data = request.get_json(silent=True) or {}
    new_target = data.get("target", "auto")
    q = load_global_queue()
    for j in q["jobs"]:
        if j["id"] == job_id and j["status"] == "queued":
            j["target"] = new_target
            save_global_queue(q)
            return jsonify({"status": "ok", "target": new_target})
    return jsonify({"error": "대기 중인 작업 없음"}), 404

@app.route("/api/youtube/channels")
def api_youtube_channels():
    return jsonify(get_all_channel_stats())

@app.route("/api/youtube/sync-playlists", methods=["POST"])
def api_youtube_sync_playlists():
    """각 채널의 플레이리스트를 스캔해 youtube_playlists.json 갱신."""
    try:
        import importlib.util, pickle as _pickle
        spec = importlib.util.spec_from_file_location("upload_youtube",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload_youtube.py"))
        uy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(uy)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    def _get_yt_ro(lang):
        from google.oauth2.credentials import Credentials as _Creds
        from google.auth.transport.requests import Request as _Req
        from googleapiclient.discovery import build as _build
        token_path = uy._token_path_for_lang(lang)
        with open(token_path, "rb") as f:
            creds = _pickle.load(f)
        if creds and creds.expired and creds.refresh_token:
            try: creds.refresh(_Req())
            except Exception: pass
        return _build("youtube", "v3", credentials=creds)

    results = {}
    for lang in ["EN", "JP", "CN", "VN", "ES"]:
        token_path = uy._token_path_for_lang(lang)
        if not os.path.exists(token_path):
            continue
        try:
            yt = _get_yt_ro(lang)
            found = _scan_and_save_playlists(yt, lang, uy)
            results[lang] = found
        except Exception as e:
            results[lang] = {"error": str(e)}
    return jsonify({"synced": results})

@app.route("/api/youtube/debug/<lang>")
def api_youtube_debug(lang):
    """채널 원시 통계 디버그 (viewCount, video stats 비교)"""
    try:
        import importlib.util, pickle as _pickle
        spec = importlib.util.spec_from_file_location("upload_youtube",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload_youtube.py"))
        uy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(uy)
        from google.auth.transport.requests import Request as _Req
        from googleapiclient.discovery import build as _build
        token_path = uy._token_path_for_lang(lang.upper())
        with open(token_path, "rb") as f:
            creds = _pickle.load(f)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(_Req())
        yt = _build("youtube", "v3", credentials=creds)
        ch = yt.channels().list(part="statistics,snippet,contentDetails", mine=True).execute()
        ch_stats = ch["items"][0]["statistics"] if ch.get("items") else {}
        uploads_pl = (ch["items"][0].get("contentDetails",{}).get("relatedPlaylists",{}).get("uploads","") if ch.get("items") else "")
        video_ids = []
        if uploads_pl:
            pl_res = yt.playlistItems().list(part="contentDetails", playlistId=uploads_pl, maxResults=5).execute()
            video_ids = [it["contentDetails"]["videoId"] for it in pl_res.get("items",[]) if it.get("contentDetails",{}).get("videoId")]
        video_stats = []
        if video_ids:
            vres = yt.videos().list(part="statistics,snippet", id=",".join(video_ids)).execute()
            for v in vres.get("items",[]):
                video_stats.append({"id": v["id"], "title": v["snippet"]["title"][:50], "stats": v.get("statistics",{})})
        return jsonify({"channel_stats": ch_stats, "first_videos": video_stats})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/youtube/upload-status")
def api_yt_upload_status():
    """렌더링된 영상의 업로드 상태 + YouTube 통계 조회"""
    def _norm(p):
        p = str(p).replace("\\", "/")
        if "/output/" in p:
            return OUTPUT_DIR + "/" + p.split("/output/", 1)[1]
        return p

    # 업로드 완료 set + video_id 맵 구성
    uploads = load_json(UPLOADS_LOG, {"uploaded": []})
    vid_map = {}       # (word_id, lang, fmt) -> video_id
    uploaded_pairs = set()
    conv_uploaded_set = set()  # (str(theme_id), lang, fmt)
    conv_vid_from_uploads = {}  # (str(theme_id), lang, fmt) -> video_id
    kdrama_uploaded_set = set()
    kdrama_vid_from_uploads = {}
    for u in uploads.get("uploaded", []):
        if u.get("type") == "kdrama":
            ck = (str(u.get("theme_id", "")), u.get("lang", "EN"), u.get("fmt", "youtube"))
            kdrama_uploaded_set.add(ck)
            if u.get("video_id"):
                kdrama_vid_from_uploads[ck] = u["video_id"]
        elif u.get("type") == "conversation":
            ck = (str(u.get("theme_id", "")), u.get("lang", "EN"), u.get("fmt", "youtube"))
            conv_uploaded_set.add(ck)
            if u.get("video_id"):
                conv_vid_from_uploads[ck] = u["video_id"]
        else:
            if "word_id" not in u:
                continue
            k = (u["word_id"], u.get("lang", "EN"), u.get("fmt", "youtube"))
            uploaded_pairs.add(k)
            if u.get("video_id"):
                vid_map[k] = u["video_id"]

    upload_all = load_json(f"{BASE}/logs/upload_all_done.json", {"uploaded_keys": []})
    for key in upload_all.get("uploaded_keys", []):
        parts = key.split("_")
        if len(parts) >= 3:
            try:
                wid = int(parts[0])
                fmt_k = parts[-1]
                lang_k = parts[-2]
                uploaded_pairs.add((wid, lang_k, fmt_k))
            except (ValueError, IndexError):
                pass

    # conv_log video_id 수집
    conv_log = load_json(CONV_LOG_F, [])
    conv_vid_map = {}  # (theme_id, lang, fmt) -> video_id
    for c in conv_log:
        if c.get("video_id"):
            conv_vid_map[(str(c.get("theme_id")), c.get("lang","EN"), c.get("fmt","youtube"))] = c["video_id"]
    # uploads.json 기반 video_id도 병합
    conv_vid_map.update(conv_vid_from_uploads)

    # kdrama_log video_id 수집
    kdrama_log = load_json(KDRAMA_LOG_F, [])
    kdrama_vid_map = {}
    for c in kdrama_log:
        if c.get("video_id"):
            kdrama_vid_map[(str(c.get("theme_id")), c.get("lang","EN"), c.get("fmt","youtube"))] = c["video_id"]
    kdrama_vid_map.update(kdrama_vid_from_uploads)

    # YouTube 통계 배치 조회
    yt_stats = {}  # video_id -> {views, likes, comments}
    _stats_failed = False
    all_vids = list({v for v in list(vid_map.values()) + list(conv_vid_map.values()) + list(kdrama_vid_map.values()) if v})

    def _fetch_stats_with_key(vids, api_key):
        from googleapiclient.discovery import build as _build
        svc = _build("youtube", "v3", developerKey=api_key)
        for i in range(0, len(vids), 50):
            batch = vids[i:i+50]
            resp = svc.videos().list(part="statistics", id=",".join(batch)).execute()
            for item in resp.get("items", []):
                s = item["statistics"]
                yt_stats[item["id"]] = {
                    "views":    int(s.get("viewCount", 0)),
                    "likes":    int(s.get("likeCount", 0)),
                    "comments": int(s.get("commentCount", 0)),
                }

    def _fetch_stats_with_oauth(vids):
        import importlib.util as _ilu, pickle as _pk
        spec = _ilu.spec_from_file_location("upload_youtube",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload_youtube.py"))
        uy = _ilu.module_from_spec(spec); spec.loader.exec_module(uy)
        from google.auth.transport.requests import Request as _Req
        from googleapiclient.discovery import build as _build
        used_langs = set()
        for (wid, lang, fmt), vid in vid_map.items():
            if vid in vids: used_langs.add(lang)
        for (tid, lang, fmt), vid in conv_vid_map.items():
            if vid in vids: used_langs.add(lang)
        if not used_langs: used_langs = {"EN"}
        fetched = set()
        for lang in used_langs:
            token_path = uy._token_path_for_lang(lang)
            if not os.path.exists(token_path): continue
            try:
                with open(token_path, "rb") as f: creds = _pk.load(f)
                if creds and creds.expired and creds.refresh_token:
                    try: creds.refresh(_Req())
                    except Exception: pass
                svc = _build("youtube", "v3", credentials=creds)
                remaining = [v for v in vids if v not in fetched]
                for i in range(0, len(remaining), 50):
                    batch = remaining[i:i+50]
                    resp = svc.videos().list(part="statistics", id=",".join(batch)).execute()
                    for item in resp.get("items", []):
                        s = item["statistics"]
                        yt_stats[item["id"]] = {
                            "views":    int(s.get("viewCount", 0)),
                            "likes":    int(s.get("likeCount", 0)),
                            "comments": int(s.get("commentCount", 0)),
                        }
                        fetched.add(item["id"])
            except Exception as e:
                print(f"  [upload-status] OAuth stats 오류 ({lang}): {e}")
            if fetched >= set(vids): break

    if all_vids:
        yt_api_key = os.environ.get("YOUTUBE_API_KEY", "")
        try:
            if yt_api_key:
                _fetch_stats_with_key(all_vids, yt_api_key)
            else:
                _fetch_stats_with_oauth(all_vids)
        except Exception as e:
            print(f"  [upload-status] YouTube stats 오류: {e}")
            _stats_failed = True

    def _stats(video_id):
        if not video_id:
            return {}
        if video_id in yt_stats:
            return yt_stats[video_id]
        # stats 조회 실패(quota 등) + video_id 존재 → error 표시
        if _stats_failed:
            return {"error": True}
        return {}

    # 단어 영상
    word_videos = []
    for v in load_json(VIDEOS_LOG, []):
        wid = v["word_id"]
        lang = v.get("language", "EN")
        fmt = v.get("fmt", "youtube")
        vid_key = (wid, lang, fmt)
        video_id = vid_map.get(vid_key)
        st = _stats(video_id)
        word_videos.append({
            "word_id": wid,
            "word": v.get("word", ""),
            "meaning": v.get("meaning", ""),
            "lang": lang,
            "level": v.get("level", 1),
            "exam": v.get("exam", "TOPIK"),
            "fmt": fmt,
            "file_exists": os.path.exists(_norm(v.get("output_path", ""))),
            "uploaded": (vid_key in uploaded_pairs) or bool(video_id),
            "generated_at": v.get("generated_at", ""),
            "video_id": video_id,
            "views":    st.get("views"),
            "likes":    st.get("likes"),
            "comments": st.get("comments"),
            "stats_error": st.get("error", False),
        })

    # 회화 영상
    conv_videos = []
    for c in conv_log:
        _ck = (str(c.get("theme_id")), c.get("lang","EN"), c.get("fmt","youtube"))
        video_id = c.get("video_id") or conv_vid_map.get(_ck)
        # uploads.json에 있으면 업로드됨으로 확정
        _uploaded = c.get("uploaded", False) or (_ck in conv_uploaded_set)
        st = _stats(video_id)
        conv_videos.append({
            "theme_id": c.get("theme_id"),
            "lang": c.get("lang", "EN"),
            "fmt": c.get("fmt", "youtube"),
            "uploaded": _uploaded,
            "file_exists": os.path.exists(_norm(c.get("video_path", ""))),
            "rendered_at": c.get("rendered_at", ""),
            "video_id": video_id,
            "views":    st.get("views"),
            "likes":    st.get("likes"),
            "comments": st.get("comments"),
            "stats_error": st.get("error", False),
        })

    # K-드라마 영상
    kdrama_videos = []
    for c in kdrama_log:
        _ck = (str(c.get("theme_id")), c.get("lang","EN"), c.get("fmt","youtube"))
        video_id = c.get("video_id") or kdrama_vid_map.get(_ck)
        _uploaded = c.get("uploaded", False) or (_ck in kdrama_uploaded_set)
        st = _stats(video_id)
        kdrama_videos.append({
            "theme_id": c.get("theme_id"),
            "lang": c.get("lang", "EN"),
            "fmt": c.get("fmt", "youtube"),
            "uploaded": _uploaded,
            "file_exists": os.path.exists(_norm(c.get("video_path", ""))),
            "rendered_at": c.get("rendered_at", ""),
            "video_id": video_id,
            "views":    st.get("views"),
            "likes":    st.get("likes"),
            "comments": st.get("comments"),
            "stats_error": st.get("error", False),
        })

    return jsonify({"word_videos": word_videos, "conv_videos": conv_videos,
                    "kdrama_videos": kdrama_videos,
                    "stats_error": _stats_failed})

_SCHED_DEFAULTS = {
    "word-yt":      {"enabled": False, "interval_days": 1, "count": 2, "lang": ""},
    "word-reels":   {"enabled": False, "interval_days": 1, "count": 2, "lang": ""},
    "conv-yt":      {"enabled": False, "interval_days": 1, "count": 1, "lang": ""},
    "conv-reels":   {"enabled": False, "interval_days": 1, "count": 1, "lang": ""},
    "kdrama-yt":    {"enabled": False, "interval_days": 1, "count": 1, "lang": ""},
    "kdrama-reels": {"enabled": False, "interval_days": 1, "count": 1, "lang": ""},
}
_SCHED_TYPE_MAP = {
    "word-yt":      ("word",   "youtube"),
    "word-reels":   ("word",   "reels"),
    "conv-yt":      ("conv",   "youtube"),
    "conv-reels":   ("conv",   "reels"),
    "kdrama-yt":    ("kdrama", "youtube"),
    "kdrama-reels": ("kdrama", "reels"),
}

@app.route("/api/youtube/upload-schedule", methods=["GET"])
def api_get_upload_schedule():
    raw = load_json(UPLOAD_SCHED_F, {})
    result = {}
    for t, default in _SCHED_DEFAULTS.items():
        result[t] = {**default, **raw.get(t, {})}
    return jsonify(result)

@app.route("/api/youtube/upload-schedule", methods=["POST"])
def api_save_upload_schedule():
    data = request.get_json(silent=True) or {}
    stype = data.get("type")
    raw = load_json(UPLOAD_SCHED_F, {})
    if stype and stype in _SCHED_DEFAULTS:
        raw.setdefault(stype, {}).update({
            k: v for k, v in data.items()
            if k in ("enabled", "interval_days", "count", "lang")
        })
    else:
        # 레거시: 전체 저장
        raw.update(data)
    save_json(UPLOAD_SCHED_F, raw)
    return jsonify({"ok": True})

@app.route("/api/youtube/upload-run", methods=["POST"])
def api_upload_run():
    data = request.get_json(silent=True) or {}
    stype = data.get("type", "word-yt")
    tab, fmt = _SCHED_TYPE_MAP.get(stype, ("word", "youtube"))
    count = int(data.get("count", 2))
    lang  = data.get("lang", "")
    result = _run_upload_batch(count, lang, fmt, tab)
    raw = load_json(UPLOAD_SCHED_F, {})
    raw.setdefault(stype, {})["last_run"] = datetime.now().strftime("%Y-%m-%d")
    save_json(UPLOAD_SCHED_F, raw)
    return jsonify(result)


# ─── YouTube 업로드 로그 복구 (Reconcile) ─────────────────────
_WORD_TITLE_MARKERS = {
    "EN": "Korean Word of the Day",
    "JP": "今日の一語",
    "CN": "每日韩语单词",
    "VN": "Tiếng Hàn mỗi ngày",
    "ES": "Coreano del día",
}
_TITLE_NUM_RE = __import__("re").compile(r"#(\d{2,4})")

def _parse_iso8601_duration_to_sec(s: str) -> int:
    """PT1M5S → 65, PT30S → 30"""
    import re as _re
    m = _re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    if not m: return 0
    h = int(m.group(1) or 0); mn = int(m.group(2) or 0); sc = int(m.group(3) or 0)
    return h*3600 + mn*60 + sc


def _fetch_channel_uploads(lang: str) -> list:
    """해당 언어 채널의 모든 업로드 영상 메타데이터 리턴 (duration 포함)."""
    sys.path.insert(0, os.path.dirname(__file__) or "/app")
    from upload_youtube import get_youtube_client
    yt = get_youtube_client(lang=lang)
    resp = yt.channels().list(part="contentDetails", mine=True).execute()
    items = resp.get("items", [])
    if not items:
        return []
    uploads_pid = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # 1) 업로드 재생목록의 videoId/title 수집
    videos, page_token = [], None
    while True:
        r = yt.playlistItems().list(
            part="snippet", playlistId=uploads_pid,
            maxResults=50, pageToken=page_token,
        ).execute()
        for it in r.get("items", []):
            sn = it["snippet"]
            videos.append({
                "video_id": sn["resourceId"]["videoId"],
                "title": sn.get("title", ""),
                "published_at": sn.get("publishedAt", ""),
                "duration_sec": 0,
            })
        page_token = r.get("nextPageToken")
        if not page_token: break

    # 2) videos.list batch — duration 조회 (쇼츠 여부 정확히 판정)
    id_to_idx = {v["video_id"]: i for i, v in enumerate(videos)}
    ids = list(id_to_idx.keys())
    for i in range(0, len(ids), 50):
        batch = ids[i:i+50]
        try:
            r = yt.videos().list(part="contentDetails",
                                 id=",".join(batch)).execute()
            for it in r.get("items", []):
                vid = it["id"]
                dur = _parse_iso8601_duration_to_sec(
                    it.get("contentDetails", {}).get("duration", ""))
                idx = id_to_idx.get(vid)
                if idx is not None:
                    videos[idx]["duration_sec"] = dur
        except Exception:
            pass
    return videos


def _build_theme_title_map(db, lang_key):
    """테마 제목 → theme_id 역매핑. 쇼츠/번호 제거된 정규화 제목과도 매칭되도록."""
    m = {}
    for t in db.get("themes", []):
        tid = str(t["id"])
        for v in [
            (t.get("search_title", {}) or {}).get(lang_key),
            (t.get("title", {}) or {}).get(lang_key),
            (t.get("title", {}) or {}).get("ko"),
        ]:
            if v:
                m[v.strip()] = tid
    return m


def reconcile_youtube_uploads(lang: str = None) -> dict:
    """YouTube 채널의 실제 업로드 상태를 스캔해 uploads.json / conv_log / kdrama_log 복구.
    fmt 판별: 영상 duration 60초 이하 → reels, 초과 → youtube.
    단어 매칭: 언어별 marker(있으면) OR (#NNN + 단어명/뜻이 제목에 포함) 이중 체크.
    """
    import re as _re
    langs = [lang] if lang else ["EN", "JP", "CN", "VN", "ES"]
    summary = {"per_lang": {}, "added_word": 0, "added_conv": 0,
               "added_kdrama": 0, "unknown_total": 0,
               "unknown_samples": {}, "errors": []}

    up = load_json(UPLOADS_LOG, {"uploaded": [], "last_day": 0})
    known_word, known_conv, known_kd = set(), set(), set()
    for u in up.get("uploaded", []):
        if u.get("type") == "conversation":
            known_conv.add((str(u.get("theme_id")), u.get("lang", ""), u.get("fmt", "youtube")))
        elif u.get("type") == "kdrama":
            known_kd.add((str(u.get("theme_id")), u.get("lang", ""), u.get("fmt", "youtube")))
        elif "word_id" in u:
            try:
                known_word.add((int(u["word_id"]), u.get("lang", ""), u.get("fmt", "youtube")))
            except (ValueError, TypeError):
                pass

    conv_log = load_json(CONV_LOG_F, [])
    conv_log_idx = {(str(c.get("theme_id")), c.get("lang", ""), c.get("fmt", "youtube")): c
                    for c in conv_log}
    kdrama_log = load_json(KDRAMA_LOG_F, [])
    kdrama_log_idx = {(str(c.get("theme_id")), c.get("lang", ""), c.get("fmt", "youtube")): c
                      for c in kdrama_log}

    try:
        conv_db = load_conv_db()
    except Exception:
        conv_db = {"themes": []}
    try:
        kdrama_db = load_kdrama_db()
    except Exception:
        kdrama_db = {"themes": []}

    # 단어 DB: word_id → (ko, meaning[lang]) 역맵 — words_db.json 전역 id 기준
    def _build_word_map(L):
        m = {}
        lang_key = L.lower()
        lt = f"{DATA_ROOT}/LanguageTest"
        # 언어별 words_db_{lang}.json 우선, 없으면 통합 words_db.json
        lang_db_path = f"{lt}/words_db_{lang_key}.json"
        base_db_path = f"{lt}/words_db.json"
        db_path = lang_db_path if os.path.exists(lang_db_path) else base_db_path
        raw = load_json(db_path, [])
        words = raw if isinstance(raw, list) else raw.get("words", [])
        for w in words:
            wid = w.get("id")
            if wid is None: continue
            m[int(wid)] = {
                "word": w.get("word", ""),
                "meaning": w.get("meaning", ""),
            }
        return m

    new_uploads = []
    for L in langs:
        lang_key = L.lower()
        conv_title_map = _build_theme_title_map(conv_db, lang_key)
        kd_title_map = _build_theme_title_map(kdrama_db, lang_key)
        word_map = _build_word_map(L)
        marker = _WORD_TITLE_MARKERS.get(L, "")

        try:
            videos = _fetch_channel_uploads(L)
        except Exception as e:
            summary["errors"].append(f"{L}: {str(e)[:200]}")
            summary["per_lang"][L] = {"error": str(e)[:120]}
            continue

        lang_sum = {"scanned": len(videos), "word": 0, "conv": 0,
                    "kdrama": 0, "already": 0, "unknown": 0}
        unknown_list = []

        for v in videos:
            title = v["title"]
            vid = v["video_id"]
            published = v["published_at"]
            dur = v.get("duration_sec", 0)
            # fmt 판별 — duration 우선, 폴백으로 #Shorts 텍스트
            if dur and dur <= 60:
                fmt = "reels"
            elif dur and dur > 60:
                fmt = "youtube"
            else:
                fmt = "reels" if ("#Shorts" in title or "#shorts" in title) else "youtube"

            # 1) 단어 매칭
            nm = _TITLE_NUM_RE.search(title)
            word_id = int(nm.group(1)) if nm else None
            is_word = False
            if word_id is not None:
                if marker and marker in title:
                    is_word = True
                else:
                    # marker 없어도 단어/뜻이 제목에 포함되면 단어로 확정
                    w = word_map.get(word_id)
                    if w and (w["word"] and w["word"] in title or
                              w["meaning"] and w["meaning"].lower() in title.lower()):
                        is_word = True

            if is_word:
                key = (word_id, L, fmt)
                if key in known_word:
                    lang_sum["already"] += 1
                    continue
                w = word_map.get(word_id, {})
                new_uploads.append({
                    "day": word_id, "word_id": word_id,
                    "word": w.get("word", ""),
                    "meaning": w.get("meaning", ""),
                    "lang": L, "fmt": fmt,
                    "video_id": vid,
                    "uploaded_at": published,
                    "reconciled": True,
                })
                known_word.add(key)
                lang_sum["word"] += 1
                summary["added_word"] += 1
                continue

            # 2) 회화/K-드라마 매칭 — 정규화된 제목
            base = title.replace(" #Shorts", "").replace("#Shorts", "").strip()
            num_m = _TITLE_NUM_RE.search(base)
            if num_m:
                base_no_num = base[:num_m.start()].strip().rstrip("|｜").strip()
            else:
                base_no_num = base
            base_clean = _re.sub(r'^[^\w가-힣A-Za-z]+', '', base_no_num).strip()

            theme_id, source = None, None
            for tm, src in [(conv_title_map, "conv"), (kd_title_map, "kdrama")]:
                for t_title, tid in tm.items():
                    tt = t_title.strip()
                    if tt and (tt == base_clean or tt == base_no_num or tt in base):
                        theme_id, source = tid, src
                        break
                if theme_id:
                    break

            if theme_id:
                key = (theme_id, L, fmt)
                if source == "conv":
                    if key in known_conv:
                        lang_sum["already"] += 1
                        continue
                    new_uploads.append({
                        "type": "conversation",
                        "theme_id": theme_id, "lang": L, "fmt": fmt,
                        "video_id": vid,
                        "uploaded_at": published,
                        "reconciled": True,
                    })
                    vp = _conv_video_path(theme_id, L, fmt)
                    entry = conv_log_idx.get(key)
                    if entry:
                        entry["uploaded"] = True
                        entry["video_id"] = vid
                    else:
                        new_entry = {
                            "theme_id": theme_id, "lang": L, "fmt": fmt,
                            "video_path": vp, "uploaded": True, "video_id": vid,
                            "rendered_at": published, "reconciled": True,
                        }
                        conv_log.append(new_entry)
                        conv_log_idx[key] = new_entry
                    known_conv.add(key)
                    lang_sum["conv"] += 1
                    summary["added_conv"] += 1
                else:
                    if key in known_kd:
                        lang_sum["already"] += 1
                        continue
                    new_uploads.append({
                        "type": "kdrama",
                        "theme_id": theme_id, "lang": L, "fmt": fmt,
                        "video_id": vid,
                        "uploaded_at": published,
                        "reconciled": True,
                    })
                    vp = _kdrama_video_path(theme_id, L, fmt)
                    entry = kdrama_log_idx.get(key)
                    if entry:
                        entry["uploaded"] = True
                        entry["video_id"] = vid
                    else:
                        new_entry = {
                            "theme_id": theme_id, "lang": L, "fmt": fmt,
                            "video_path": vp, "uploaded": True, "video_id": vid,
                            "rendered_at": published, "reconciled": True,
                        }
                        kdrama_log.append(new_entry)
                        kdrama_log_idx[key] = new_entry
                    known_kd.add(key)
                    lang_sum["kdrama"] += 1
                    summary["added_kdrama"] += 1
                continue

            lang_sum["unknown"] += 1
            summary["unknown_total"] += 1
            if len(unknown_list) < 8:
                unknown_list.append({"title": title[:120], "dur": dur, "fmt": fmt})

        lang_sum["unknown_samples"] = unknown_list
        summary["per_lang"][L] = lang_sum
        if unknown_list:
            summary["unknown_samples"][L] = unknown_list

    up["uploaded"].extend(new_uploads)
    save_json(UPLOADS_LOG, up)
    save_json(CONV_LOG_F, conv_log)
    save_json(KDRAMA_LOG_F, kdrama_log)
    return summary


@app.route("/api/youtube/reconcile", methods=["POST"])
def api_reconcile_uploads():
    data = request.get_json(silent=True) or {}
    lang = data.get("lang")
    try:
        summary = reconcile_youtube_uploads(lang)
        return jsonify({"ok": True, **summary})
    except Exception as e:
        import traceback
        return jsonify({"ok": False, "error": str(e),
                        "trace": traceback.format_exc()[-800:]}), 500


# ─── Instagram API ────────────────────────────────────────────
IG_TOKEN_F = f"{BASE}/logs/instagram_token.json"

@app.route("/api/instagram/token", methods=["POST"])
def api_ig_save_token():
    data = request.get_json(silent=True) or {}
    token = data.get("token", "").strip()
    if not token:
        return jsonify({"error": "token 필요"}), 400
    save_json(IG_TOKEN_F, {"access_token": token})
    return jsonify({"status": "saved"})

@app.route("/api/instagram/status")
def api_ig_status():
    import urllib.request, urllib.error
    cfg = load_json(IG_TOKEN_F, {})
    token = cfg.get("access_token", "")
    if not token:
        return jsonify({"connected": False})
    try:
        url = f"https://graph.instagram.com/me?fields=id,name,username,followers_count&access_token={token}"
        with urllib.request.urlopen(url, timeout=5) as resp:
            d = json.loads(resp.read())
        return jsonify({"connected": True, "name": d.get("name",""), "username": d.get("username",""), "followers": d.get("followers_count",0)})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})

@app.route("/api/instagram/upload", methods=["POST"])
def api_ig_upload():
    """Instagram 릴스 업로드 (Meta Graph API)"""
    cfg = load_json(IG_TOKEN_F, {})
    token = cfg.get("access_token", "")
    if not token:
        return jsonify({"error": "Instagram 토큰 없음 — 설정에서 먼저 연결하세요"}), 400
    data = request.get_json(silent=True) or {}
    word_id = data.get("word_id")
    lang = data.get("lang", "EN")
    if not word_id:
        return jsonify({"error": "word_id 필요"}), 400
    # 영상 파일 경로 찾기
    videos = get_videos_log()
    vid = next((v for v in videos if str(v.get("word_id")) == str(word_id) and v.get("language", "EN") == lang), None)
    if not vid:
        return jsonify({"error": "해당 영상을 찾을 수 없습니다"}), 404
    video_path = vid.get("file_path", "")
    if not video_path or not os.path.exists(video_path):
        return jsonify({"error": "영상 파일이 없습니다 — 먼저 렌더링하세요"}), 404
    return jsonify({"error": "Instagram 업로드는 공개 URL이 필요합니다. Meta Graph API 설정 후 이용 가능합니다."}), 501

@app.route("/api/render-config/toggle", methods=["POST"])
def api_toggle_render():
    data = request.get_json(silent=True) or {}
    enabled = data.get("desktop_enabled", True)
    set_render_config(enabled)
    return jsonify({"desktop_enabled": enabled})

@app.route("/api/render", methods=["POST"])
def api_render():
    """단일 단어 렌더링 → 글로벌 큐에 video_batch 잡으로 등록"""
    data    = request.get_json(silent=True) or {}
    word_id = data.get("word_id") or get_next_word_id()
    target  = data.get("target", "auto")
    exam    = data.get("exam", "TOPIK")
    lang    = data.get("lang", "EN")
    fmt     = data.get("fmt", "youtube")
    if fmt not in ("youtube", "reels"): fmt = "youtube"
    if not word_id:
        return jsonify({"error": "렌더링할 단어가 없습니다"}), 400
    db = get_db("시험용", exam, lang)
    word = next((w for w in db if w["id"] == word_id), None)
    word_level = word.get("level", 1) if word else 1
    db_path    = render_db_path_for(exam, lang, word_level)
    word_text  = word["word"] if word else str(word_id)
    fmt_label  = " [릴스]" if fmt == "reels" else ""
    desc = f"{exam} {word_text}{fmt_label} ({lang})"
    job_id = enqueue_job("video_batch", desc, target=target, params={
        "job_items":   [(word_id, lang, db_path, word_text, fmt)],
        "queue_items": [{"word_id": word_id, "word": word_text + fmt_label, "exam": exam,
                         "level": word_level, "lang": lang, "fmt": fmt, "status": "pending"}],
        "words_map":   {str(word_id): word} if word else {},
        "auto_upload": False,
        "exam": exam, "lang": lang,
    })
    return jsonify({"status": "queued", "job_id": job_id, "word_id": word_id})

@app.route("/api/schedule", methods=["GET"])
def api_get_schedule():
    return jsonify(get_schedule())

@app.route("/api/schedule", methods=["POST"])
def api_save_schedule():
    data = request.get_json(silent=True) or {}
    slots = data.get("slots", [])
    save_json(SCHEDULE_CONFIG, {"slots": slots})
    return jsonify({"status": "ok", "slots": slots})

# ─── 일별 자동 API ───────────────────────────────────────────
_DAILY_CONFIG_KEYS = {
    "auto_upload":        bool,
    "word_freq":          str,  # daily | every2days | every3days | 2perday | 3perday
    "word_render":        str,  # auto | auto_if_missing | manual
    "word_illust":        str,  # auto | auto_if_missing | manual
    "word_prebuffer_h":   int,  # hours before upload to pre-render word video
    "phrase_freq":        str,  # daily | every2days | every3days
    "phrase_render":      str,  # auto | auto_if_missing | manual
    "phrase_illust":      str,  # auto | auto_if_missing | manual
    "phrase_prebuffer_h": int,  # hours before upload to pre-render phrase video
    "auto_start_date":    str,  # YYYY-MM-DD — schedule begins from this date
    "ep_word_yt_start":    int,  # 기준일의 단어 본편 시작 화수
    "ep_word_reels_start": int,  # 기준일의 단어 쇼츠 시작 화수
    "ep_conv_yt_start":    int,  # 기준일의 회화 본편 시작 화수
    "ep_conv_reels_start": int,  # 기준일의 회화 쇼츠 시작 화수
}

@app.route("/api/daily/config", methods=["GET","POST"])
def api_daily_config():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        s = load_json(DAILY_AUTO_F, {})
        for key, cast in _DAILY_CONFIG_KEYS.items():
            if key in data:
                try: s[key] = cast(data[key])
                except Exception: pass
        save_json(DAILY_AUTO_F, s)
        if data.get("auto_upload"):
            threading.Thread(target=_daily_auto_tick, daemon=True).start()
        return jsonify({"ok": True})
    return jsonify(load_json(DAILY_AUTO_F, {}))

@app.route("/api/daily/countdown")
def api_daily_countdown():
    """언어별 다음 업로드 시각(UTC) + 파일 준비 상태 (단어/회화 분리)"""
    KST = timezone(timedelta(hours=9))
    s   = load_json(DAILY_AUTO_F, {})
    global_word_id = s.get("current_word_id")
    try:
        db = get_words_db()
    except Exception:
        db = []

    result = {}
    for lang in DAILY_LANGS:
        next_ut = _next_publish_at(lang)
        kst_fixed = next_ut.astimezone(KST).strftime("%H:%M")

        # 현지 날짜 계산
        if _HAS_TZ:
            local_dt = next_ut.astimezone(_LANG_TZ.get(lang, _LANG_TZ["EN"]))
        else:
            off = _LANG_UTC_OFFSET_H.get(lang, -5)
            local_dt = next_ut + timedelta(hours=off)
        local_date = f"{local_dt.month}월 {local_dt.day}일"

        lang_state   = s.get("langs", {}).get(lang, {})
        phrase_state = s.get("phrase_langs", {}).get(lang, {})

        yt_ok  = lang_state.get("youtube_rendered", False)
        rl_ok  = lang_state.get("reels_rendered",  False)
        yt_upl = lang_state.get("youtube_uploaded", False)
        rl_upl = lang_state.get("reels_uploaded",  False)
        conv_upl = phrase_state.get("uploaded", False)

        # 언어별 ep_override → global current_word_id 순으로 파일 경로 결정
        lang_word_id = lang_state.get("ep_override") or global_word_id
        word = None
        if lang_word_id and db:
            word = next((w for w in db if w["id"] == lang_word_id), None)

        file_yt = file_rl = file_il = False
        if word:
            lv  = word.get("level", 1)
            wid = word["id"]
            wrd = word["word"]
            file_yt = os.path.exists(f"{OUTPUT_DIR}/TOPIK/{lang}/lv{lv}/video/topik_{wid:04d}_{wrd}_{lang}.mp4")
            file_rl = os.path.exists(f"{OUTPUT_DIR}/TOPIK/{lang}/lv{lv}/reels/topik_{wid:04d}_{wrd}_{lang}_reels.mp4")
            il_path = f"{ILLUST_DIR}/lv{lv}/{wid}_{wrd}/word.png"
            file_il = illust_exists(il_path)

        word_ep_num = lang_state.get("ep_override") or global_word_id or 0
        conv_ep_num = phrase_state.get("conv_ep_override") or 0

        result[lang] = {
            "next_upload_utc": next_ut.isoformat(),
            "kst_time":        kst_fixed,
            "local_date":      local_date,
            # 단어
            "word_ep_num":     word_ep_num,
            "video_ready":     yt_ok or file_yt,
            "reels_ready":     rl_ok or file_rl,
            "illust_ready":    file_il,
            "video_uploaded":  yt_upl,
            "reels_uploaded":  rl_upl,
            # 회화
            "conv_ep_num":     conv_ep_num,
            "conv_uploaded":   conv_upl,
        }
    return jsonify(result)


@app.route("/api/daily/set-episode", methods=["POST"])
def api_daily_set_episode():
    """언어별 업로드 화수 override 설정 (단어/회화 구분)"""
    data  = request.get_json(silent=True) or {}
    lang  = data.get("lang")
    ep    = data.get("episode_num")
    ctype = data.get("ctype", "word")   # "word" | "conv" | "kdrama"
    if not lang or ep is None:
        return jsonify({"error": "lang, episode_num 필요"}), 400
    try:
        ep = int(ep)
    except (ValueError, TypeError):
        return jsonify({"error": "episode_num은 정수여야 합니다"}), 400
    s = load_json(DAILY_AUTO_F, {})
    if ctype == "conv":
        s.setdefault("phrase_langs", {}).setdefault(lang, {})["conv_ep_override"] = ep
    elif ctype == "kdrama":
        s.setdefault("kdrama_langs", {}).setdefault(lang, {})["kdrama_ep_override"] = ep
    else:
        s.setdefault("langs", {}).setdefault(lang, {})["ep_override"] = ep
    save_json(DAILY_AUTO_F, s)
    return jsonify({"ok": True, "lang": lang, "ctype": ctype, "episode_num": ep})


@app.route("/api/daily/upload-now", methods=["POST"])
def api_daily_upload_now():
    """지금 바로 업로드 (예약 없이 즉시 공개). 다음 주기 자동 세팅."""
    data = request.get_json(silent=True) or {}
    lang = data.get("lang", "EN")
    fmt  = data.get("fmt", "youtube")   # youtube | reels

    s = load_json(DAILY_AUTO_F, {})
    # 언어별 override → global current_word_id 순으로 확인
    word_id = s.get("langs", {}).get(lang, {}).get("ep_override") or s.get("current_word_id")
    if not word_id:
        return jsonify({"error": "업로드할 화수가 설정되지 않았습니다"}), 400

    db   = get_words_db()
    word = next((w for w in db if w["id"] == word_id), None)
    if not word:
        return jsonify({"error": f"단어 없음: id={word_id}"}), 404

    lv  = word.get("level", 1)
    wid = word["id"]
    wrd = word["word"]
    sub = "reels" if fmt == "reels" else "video"
    suf = "_reels" if fmt == "reels" else ""
    vpath = f"{OUTPUT_DIR}/TOPIK/{lang}/lv{lv}/{sub}/topik_{wid:04d}_{wrd}_{lang}{suf}.mp4"

    if not os.path.exists(vpath):
        return jsonify({"error": f"영상 파일 없음: {vpath}"}), 404

    # publish_at=None → 즉시 공개
    try:
        vid = run_upload(word, vpath, exam="TOPIK", lang=lang, publish_at=None, fmt=fmt)
    except Exception as _e:
        import traceback
        return jsonify({"error": f"업로드 예외: {_e}", "trace": traceback.format_exc()[-800:]}), 500
    if not vid:
        # run_upload 내부 로그에서 원인 확인 (print로 출력됨)
        return jsonify({"error": "업로드 실패 — 서버 로그 확인 필요"}), 500

    # daily_auto 상태 업데이트
    s = load_json(DAILY_AUTO_F, {})
    ku = "youtube_uploaded" if fmt == "youtube" else "reels_uploaded"
    kv = "youtube_video_id"  if fmt == "youtube" else "reels_video_id"
    s.setdefault("langs", {}).setdefault(lang, {})[ku] = True
    s["langs"][lang][kv] = vid
    # 다음 주기 publish_at 갱신 (내일 현지 07:30)
    next_pub = _next_publish_at(lang)
    s["langs"][lang]["publish_at"] = next_pub.isoformat()
    save_json(DAILY_AUTO_F, s)

    return jsonify({"ok": True, "video_id": vid,
                    "next_publish_at": next_pub.isoformat()})

@app.route("/api/daily/status")
def api_daily_status():
    s = load_json(DAILY_AUTO_F, {})
    word_id = s.get("current_word_id")
    word = None
    if word_id:
        db = get_words_db()
        word = next((w for w in db if w["id"] == word_id), None)
    # 현지 업로드 시간 표시용 변환
    for lg in DAILY_LANGS:
        ls = s.get("langs", {}).get(lg, {})
        raw = ls.get("publish_at","")
        if raw:
            try:
                dt = datetime.fromisoformat(raw.replace("Z","+00:00"))
                if _HAS_TZ:
                    loc = dt.astimezone(_LANG_TZ[lg])
                    ls["publish_local"] = loc.strftime("%m/%d %H:%M (%Z)")
                else:
                    ls["publish_local"] = dt.strftime("%m/%d %H:%M UTC")
            except: pass
    lv1_total = len([w for w in get_words_db() if w.get("level")==1])
    illust_generating = _illust_proc is not None and _illust_proc.poll() is None
    return jsonify({"state": s, "word": word, "rendering": _daily_rendering,
                    "lv1_total": lv1_total, "illust_generating": illust_generating})

@app.route("/api/daily/trigger", methods=["POST"])
def api_daily_trigger():
    threading.Thread(target=_daily_auto_tick, daemon=True).start()
    return jsonify({"ok": True})

@app.route("/api/daily/set-word", methods=["POST"])
def api_daily_set_word():
    data = request.get_json(silent=True) or {}
    try: word_id = int(data["word_id"])
    except: return jsonify({"error":"word_id 필요"}), 400
    s = load_json(DAILY_AUTO_F, {})
    s.update({"current_word_id": word_id, "today": datetime.now().strftime("%Y-%m-%d"),
               "illust_done": False, "langs": _daily_init_langs()})
    save_json(DAILY_AUTO_F, s)
    return jsonify({"ok": True})

@app.route("/api/batch/today")
def api_batch_today():
    batch = get_batch_today()
    bq    = load_json(BATCH_QUEUE_F, {})
    return jsonify({"batch": batch, "queue": bq})

@app.route("/api/batch/history")
def api_batch_history():
    date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    items = []
    videos = get_videos_log()
    for v in videos:
        ts = (v.get("generated_at") or "")[:10]
        if ts == date:
            items.append({
                "word": v.get("word", ""),
                "lang": v.get("language", ""),
                "format": "youtube",
                "status": "done",
                "rendered_at": v.get("generated_at", ""),
                "exam": v.get("exam", "TOPIK"),
                "level": v.get("level", ""),
            })
    uploaded, _ = get_uploads()
    for u in uploaded:
        ts = (u.get("uploaded_at") or u.get("date") or "")[:10]
        if ts == date:
            items.append({
                "word": u.get("word", u.get("title", "")),
                "lang": u.get("lang") or u.get("language", ""),
                "format": u.get("format", "youtube"),
                "status": "uploaded",
                "rendered_at": u.get("uploaded_at", ""),
            })
    items.sort(key=lambda x: x.get("rendered_at", ""), reverse=True)
    return jsonify({"items": items})

@app.route("/api/batch/clear", methods=["POST"])
def api_batch_clear():
    """배치 진행 기록 초기화"""
    save_json(BATCH_QUEUE_F, {})
    return jsonify({"status": "cleared"})

@app.route("/api/batch/date")
def api_batch_date():
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    return jsonify(get_batch_for_date(date_str))

@app.route("/api/render/batch", methods=["POST"])
def api_render_batch():
    data        = request.get_json(silent=True) or {}
    items_req   = data.get("items", [])       # [{word_id, exam, lang, level, formats}] — per-item
    word_ids_req= data.get("word_ids", [])    # 레거시: 동일 포맷 적용
    target      = data.get("target", "auto")
    auto_upload = data.get("auto_upload", False)
    default_fmts= data.get("formats", ["youtube", "reels"])

    batch = get_batch_today()
    db = get_db()

    job_items   = []
    queue_items = []
    word_ids_set= set()

    if items_req:
        # per-item 포맷 지정 모드
        for item in items_req:
            wid   = item.get("word_id")
            fmts  = item.get("formats", default_fmts)
            lang  = item.get("lang", "EN")
            exam  = item.get("exam", "TOPIK")
            level = item.get("level", 1)
            if not wid: continue
            word_obj = next((w for w in db if w["id"] == wid), None)
            word_text = word_obj["word"] if word_obj else ""
            db_path = render_db_path_for(exam, lang, level)
            for fmt in fmts:
                job_items.append((wid, lang, db_path, word_text, fmt))
                fmt_label = "" if fmt == "youtube" else " [쇼츠]"
                queue_items.append({"word_id": wid, "word": word_text + fmt_label,
                                    "lang": lang, "fmt": fmt, "status": "pending"})
            word_ids_set.add(wid)
    else:
        # word_ids 또는 전체 pending 배치
        if word_ids_req:
            sel_ids = set(word_ids_req)
        else:
            sel_ids = {b["word"]["id"] for b in batch if b.get("word") and b.get("status") == "pending"}
        if not sel_ids:
            return jsonify({"error": "렌더링할 단어가 없습니다"}), 400
        # batch_meta: word_id → (lang, exam, level, fmts)
        batch_meta = {b["word"]["id"]: (b.get("lang","EN"), b.get("exam","TOPIK"),
                                        b.get("level",1), b.get("fmt","both"))
                      for b in batch if b.get("word")}
        words_map_tmp = {w["id"]: w for w in db if w["id"] in sel_ids}
        for wid in sel_ids:
            lang, exam, level, slot_fmt = batch_meta.get(wid, ("EN","TOPIK",1,"both"))
            fmts = default_fmts if data.get("formats") else (
                ["youtube"] if slot_fmt == "youtube" else
                ["reels"]   if slot_fmt == "reels"   else
                ["youtube", "reels"]
            )
            db_path   = render_db_path_for(exam, lang, level)
            word_text = words_map_tmp.get(wid, {}).get("word", "")
            for fmt in fmts:
                job_items.append((wid, lang, db_path, word_text, fmt))
                fmt_label = "" if fmt == "youtube" else " [쇼츠]"
                queue_items.append({"word_id": wid, "word": word_text + fmt_label,
                                    "lang": lang, "fmt": fmt, "status": "pending"})
            word_ids_set.add(wid)

    if not job_items:
        return jsonify({"error": "렌더링할 항목이 없습니다"}), 400

    words_map  = {w["id"]: w for w in db if w["id"] in word_ids_set}
    langs_str  = "+".join(sorted(set(it[1] for it in job_items)))
    word_count = len(word_ids_set)
    desc = f"배치 {word_count}단어 ({langs_str})"
    thumb_style = data.get("thumb_style", "portrait")
    job_id = enqueue_job("video_batch", desc, target=target, params={
        "job_items":   [list(j) for j in job_items],
        "queue_items": queue_items,
        "words_map":   {str(k): v for k, v in words_map.items()},
        "auto_upload": auto_upload,
        "exam": "TOPIK", "lang": langs_str,
        "thumb_style": thumb_style,
    })
    return jsonify({"status": "queued", "job_id": job_id, "count": len(job_items),
                    "target": target, "auto_upload": auto_upload})

@app.route("/api/render/upload", methods=["POST"])
def api_render_upload():
    """렌더링 완료된 영상 수동 업로드"""
    data = request.get_json(silent=True) or {}
    word_id = data.get("word_id")
    lang    = data.get("lang", "EN")
    exam    = data.get("exam", "TOPIK")
    fmt     = data.get("fmt", "youtube")
    if fmt not in ("youtube", "reels"): fmt = "youtube"
    if not word_id:
        return jsonify({"error": "word_id 필요"}), 400
    db = get_words_db()
    word = next((w for w in db if w["id"] == word_id), None)
    if not word:
        return jsonify({"error": f"단어 {word_id} 없음"}), 404
    lv = word.get("level", 1)
    # videos_log에서 정확한 경로 우선 조회
    def _norm(p):
        p = str(p).replace("\\", "/")
        if "/output/" in p:
            return OUTPUT_DIR + "/" + p.split("/output/", 1)[1]
        return p
    vpath = None
    for v in load_json(VIDEOS_LOG, []):
        if v["word_id"] == word_id and v.get("language") == lang and v.get("fmt", "youtube") == fmt:
            vpath = _norm(v.get("output_path", "")); break
    if not vpath:
        # 폴백: 경로 패턴으로 추정
        if fmt == "reels":
            vpath = f"{OUTPUT_DIR}/{exam}/{lang}/lv{lv}/reels/{exam.lower()}_{word_id:04d}_{word['word']}_{lang}_reels.mp4"
        else:
            vpath = f"{OUTPUT_DIR}/{exam}/{lang}/lv{lv}/video/{exam.lower()}_{word_id:04d}_{word['word']}_{lang}.mp4"
    if not os.path.exists(vpath):
        return jsonify({"error": f"영상 파일 없음: {vpath}"}), 404
    try:
        vid = run_upload(word, vpath, exam=exam, lang=lang, fmt=fmt)
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()[-800:]}), 500
    if vid:
        bq = load_json(BATCH_QUEUE_F, {})
        for it in bq.get("items", []):
            if it.get("word_id") == word_id and it.get("lang", "EN") == lang:
                it["status"] = "uploaded"
                it["video_id"] = vid
        save_json(BATCH_QUEUE_F, bq)
    return jsonify({"ok": True, "video_path": vpath, "video_id": vid})

@app.route("/api/update-descriptions", methods=["POST"])
def api_update_descriptions():
    """이미 업로드된 YouTube 본편 영상의 설명란을 10개 예문으로 일괄 업데이트"""
    data = request.get_json(silent=True) or {}
    lang = data.get("lang", None)  # None=전체

    def _run():
        import subprocess
        cmd = [sys.executable, "/app/update_video_descriptions.py"]
        if lang:
            cmd += ["--lang", lang]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, _ = proc.communicate()
        print("[update-desc]", (out or b"").decode("utf-8", errors="replace")[-1000:])

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"ok": True, "lang": lang})


@app.route("/api/daily/upload-lang", methods=["POST"])
def api_daily_upload_lang():
    """오늘의 배치 — 언어별 수동 업로드"""
    data  = request.get_json(silent=True) or {}
    lang  = data.get("lang", "EN")
    fmts  = data.get("fmts", ["youtube", "reels"])  # 업로드할 포맷 목록
    s     = load_json(DAILY_AUTO_F, {})
    wid   = s.get("current_word_id")
    if not wid:
        return jsonify({"error": "current_word_id 없음"}), 400
    db   = get_words_db()
    word = next((w for w in db if w["id"] == wid), None)
    if not word:
        return jsonify({"error": f"단어 {wid} 없음"}), 404
    def _run():
        for fmt in fmts:
            _daily_upload_job(word, lang, fmt)
    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"ok": True, "word_id": wid, "lang": lang, "fmts": fmts})

@app.route("/api/video/delete", methods=["POST"])
def api_video_delete():
    """단어 영상 삭제 — 파일 + videos_log 항목 제거"""
    data    = request.get_json(silent=True) or {}
    word_id = data.get("word_id")
    lang    = data.get("lang", "EN")
    exam    = data.get("exam", "TOPIK")
    fmt     = data.get("fmt")  # None이면 모든 포맷 삭제 (기존 호환)
    if not word_id:
        return jsonify({"error": "word_id 필요"}), 400
    # videos_log 에서 파일 경로 찾기
    vlog  = get_videos_log()
    def _matches_fmt(v):
        if fmt is None: return True
        _path = v.get("output_path", "")
        _vfmt = v.get("fmt") or ("reels" if "/reels/" in _path or "_reels" in _path else "youtube")
        return _vfmt == fmt
    entry = next((v for v in vlog
                  if v.get("word_id") == word_id
                  and v.get("language", "EN") == lang
                  and v.get("exam", "TOPIK") == exam
                  and _matches_fmt(v)), None)
    deleted_file = False
    if entry:
        fpath = entry.get("output_path", "")
        if fpath and os.path.exists(fpath):
            try: os.remove(fpath); deleted_file = True
            except Exception: pass
        vlog = [v for v in vlog
                if not (v.get("word_id") == word_id
                        and v.get("language", "EN") == lang
                        and v.get("exam", "TOPIK") == exam
                        and _matches_fmt(v))]
        save_json(VIDEOS_LOG, vlog)
    return jsonify({"ok": True, "deleted_file": deleted_file})

@app.route("/api/conv/delete", methods=["POST"])
def api_conv_delete():
    """회화 영상 삭제 — 파일 + conv_log 항목 제거"""
    data     = request.get_json(silent=True) or {}
    theme_id = str(data.get("theme_id", ""))
    lang     = data.get("lang", "EN")
    if not theme_id:
        return jsonify({"error": "theme_id 필요"}), 400
    deleted_file = False
    for fmt in ("youtube", "reels"):
        vp = _conv_video_path(theme_id, lang, fmt)
        local_vp = vp.replace("/app/", BASE.rstrip("/") + "/", 1) if vp.startswith("/app/") else vp
        for p in (vp, local_vp):
            if os.path.exists(p):
                try: os.remove(p); deleted_file = True
                except Exception: pass
    # 썸네일도 삭제
    tp = _conv_thumb_path(theme_id, lang)
    local_tp = tp.replace("/app/", BASE.rstrip("/") + "/", 1) if tp.startswith("/app/") else tp
    for p in (tp, local_tp):
        if os.path.exists(p):
            try: os.remove(p)
            except Exception: pass
    clog = load_conv_log()
    clog = [x for x in clog
            if not (str(x.get("theme_id")) == theme_id and x.get("lang") == lang)]
    save_conv_log(clog)
    return jsonify({"ok": True, "deleted_file": deleted_file})

@app.route("/api/render/cancel", methods=["POST"])
def api_render_cancel():
    """배치/단일 렌더링 취소 — NAS 프로세스 강제 종료 포함"""
    global _nas_proc, _illust_proc
    cancelled_any = False
    # 1) 배치 큐 취소 신호
    bq = load_json(BATCH_QUEUE_F, {})
    if bq.get("status") in ("running", "pending"):
        bq["status"] = "cancelled"
        bq["completed_at"] = datetime.now().isoformat()
        save_json(BATCH_QUEUE_F, bq)
        cancelled_any = True
    # 2) 단일 렌더 큐 취소
    q = load_json(QUEUE_FILE, {})
    if q.get("status") in ("pending", "claimed"):
        q["status"] = "failed"
        q["error"] = "cancelled"
        q["completed_at"] = datetime.now().isoformat()
        save_json(QUEUE_FILE, q)
        cancelled_any = True
    # 3) NAS 렌더링 프로세스 직접 종료
    if _nas_proc and _nas_proc.poll() is None:
        try:
            _nas_proc.terminate()
            _nas_proc.wait(timeout=5)
        except Exception:
            try: _nas_proc.kill()
            except Exception: pass
        cancelled_any = True
    # 4) 일러스트 생성 프로세스 직접 종료
    if _illust_proc and _illust_proc.poll() is None:
        try:
            _illust_proc.terminate()
            _illust_proc.wait(timeout=5)
        except Exception:
            try: _illust_proc.kill()
            except Exception: pass
        ill_prog = load_json(ILLUST_PROG_F, {})
        ill_prog["status"] = "cancelled"
        save_json(ILLUST_PROG_F, ill_prog)
        cancelled_any = True
    if cancelled_any:
        return jsonify({"status": "cancelled"})
    return jsonify({"status": "nothing_to_cancel"})

@app.route("/api/upload/manual", methods=["POST"])
def api_upload_manual():
    """생성된 영상을 수동으로 YouTube 업로드"""
    data = request.get_json(silent=True) or {}
    word_id = data.get("word_id")
    exam    = data.get("exam", "TOPIK")
    lang    = data.get("lang", "EN")
    if not word_id:
        return jsonify({"error": "word_id가 필요합니다"}), 400
    # 단어 정보 가져오기
    db = get_db("시험용", exam, lang)
    word = None
    for w in db:
        if w["id"] == word_id:
            word = w; break
    if not word:
        return jsonify({"error": f"단어 ID {word_id}를 찾을 수 없습니다"}), 404
    # 영상 파일 찾기
    lv = word.get("level", 1)
    video_path = None
    candidates = [
        f"{OUTPUT_DIR}/{exam}/{lang}/lv{lv}/video/{exam.lower()}_{word_id:04d}_{word['word']}_{lang}.mp4",
        f"{OUTPUT_DIR}/{exam}/{lang}/lv{lv}/video/{exam.lower()}_{word_id:04d}_{word['word']}.mp4",  # 구형 이름 폴백
        f"{OUTPUT_DIR}/topik_{word_id:04d}_{word['word']}.mp4",
    ]
    for p in candidates:
        if os.path.exists(p):
            video_path = p; break
    if not video_path:
        return jsonify({"error": f"영상 파일을 찾을 수 없습니다: {word['word']}"}), 404
    # 업로드 실행
    try:
        vid = run_upload(word, video_path, exam=exam, lang=lang)
        if vid:
            return jsonify({"status": "uploaded", "video_id": vid,
                            "url": f"https://youtube.com/watch?v={vid}"})
        return jsonify({"error": "업로드 실패"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/render/preview")
def api_render_preview():
    """커스텀 렌더링 미리보기 — ID 범위 지원"""
    exam     = request.args.get("exam", "TOPIK")
    lang     = request.args.get("lang", "EN")
    level    = int(request.args.get("level", 1))
    ids_str  = request.args.get("ids", "")
    if ids_str:
        ids   = parse_ids_str(ids_str)
        words = get_words_by_ids(exam, lang, level, ids)
    else:
        words = get_next_words_for_custom(exam, lang, level, 30, None, None)
    # 일러스트 존재 여부 추가
    for w in words:
        lv = str(w.get("level", 1))
        w["has_illust"] = illust_exists(f"{ILLUST_DIR}/lv{lv}/{w['id']}_{w['word']}/word.png")
    # 남은 수 계산
    all_words_db = get_words_db()
    videos = get_videos_log()
    rendered = {v["word_id"] for v in videos
                if v.get("exam", "TOPIK") == exam and v.get("language", "EN") == lang}
    remaining = sum(1 for w in all_words_db if w.get("level") == level and w["id"] not in rendered)
    # 등급 ID 범위
    min_id, max_id, total = get_level_id_range(exam, lang, level)
    return jsonify({"words": words, "count": len(words), "remaining": remaining,
                    "level_min_id": min_id, "level_max_id": max_id, "level_total": total})

@app.route("/api/render/custom", methods=["POST"])
def api_render_custom():
    """커스텀 렌더링 — 시험(다중)/언어(다중)/등급/ID범위/위치 지정"""
    data     = request.get_json(silent=True) or {}
    # targets: [{exam, level}, ...] 다중 지원. 구형 단일 호환
    raw_targets = data.get("targets")
    if raw_targets:
        targets = [{"exam": t.get("exam","TOPIK"), "level": int(t.get("level",1)),
                    "ids_str": t.get("ids_str",""), "fmts": t.get("fmts")} for t in raw_targets]
    else:
        targets = [{"exam": data.get("exam","TOPIK"), "level": int(data.get("level",1)),
                    "ids_str": ""}]
    # langs: 다중 선택 지원
    langs    = data.get("langs") or [data.get("lang", "EN")]
    formats  = data.get("formats") or ["youtube"]
    target   = data.get("target", "auto")
    base_lang = langs[0]
    # 모든 시험×등급 조합에서 단어 수집
    job_items = []
    queue_items = []
    all_words = []
    for t in targets:
        exam_t    = t["exam"]
        level_t   = t["level"]
        ids_str_t = t.get("ids_str", "")
        target_fmts = t.get("fmts") or formats  # per-row formats, fallback to global
        if ids_str_t:
            ids_list = parse_ids_str(ids_str_t)
            words_t  = get_words_by_ids(exam_t, base_lang, level_t, ids_list)
        else:
            words_t = get_next_words_for_custom(exam_t, base_lang, level_t, 30, None, None)
        all_words.extend(words_t)
        for lg in langs:
            db_path = render_db_path_for(exam_t, lg, level_t)
            for w in words_t:
                for fmt in target_fmts:
                    job_items.append((w["id"], lg, db_path, w["word"], fmt))
                    fmt_label = "" if fmt == "youtube" else " [릴스]"
                    queue_items.append({"word_id": w["id"], "word": w["word"] + fmt_label,
                                         "exam": exam_t, "level": level_t,
                                         "lang": lg, "fmt": fmt, "status": "pending"})
    if not job_items:
        return jsonify({"error": "렌더링할 단어가 없습니다"}), 400
    first_exam  = targets[0]["exam"]
    first_level = targets[0]["level"]
    first_fmts  = targets[0].get("fmts") or formats
    fmt_label   = "본편+쇼츠" if set(first_fmts) >= {"youtube","reels"} else ("본편" if "youtube" in first_fmts else "쇼츠")
    langs_str = "+".join(langs)
    words_label = "+".join(w["word"] for w in all_words[:3])
    if len(all_words) > 3: words_label += f" 외 {len(all_words)-3}개"
    desc = f"{first_exam}-{first_level}급-{words_label}-{fmt_label} ({langs_str})"
    all_words_map = {str(w["id"]): w for w in all_words}
    thumb_only = bool(data.get("thumb_only", False))
    job_id = enqueue_job("video_batch", desc, target=target, params={
        "job_items":   [list(j) for j in job_items],
        "queue_items": queue_items,
        "words_map":   all_words_map,
        "auto_upload": False,
        "exam": first_exam, "lang": base_lang,
        "thumb_only":  thumb_only,
    })
    return jsonify({"status":"queued","job_id":job_id,"count":len(job_items),"target":target,
                    "words":[{"id":w["id"],"word":w["word"]} for w in all_words],
                    "langs": langs})

@app.route("/api/illustrations/word/<int:word_id>")
def api_illust_word(word_id):
    """단어별 일러스트 상태 조회 (썸네일 경로 + 존재 여부)"""
    level = request.args.get("level", type=int)
    db = get_words_db()  # 전역 ID 기반 words_db.json 사용
    word = next((w for w in db if w["id"] == word_id and (level is None or w.get("level") == level)), None)
    if not word:
        return jsonify({"error": "단어 없음"}), 404
    lv = word.get("level", 1)
    korean = word["word"]
    folder = f"{word_id}_{korean}"
    base = f"{ILLUST_DIR}/lv{lv}/{folder}"
    sents = get_topik_examples(lv, word_id)
    items = []
    # word.png
    wp = f"{base}/word.png"
    items.append({"idx": -1, "type": "word", "exists": illust_exists(wp),
                  "url": f"/illust/{lv}/{folder}/word.png"})
    # 예문 0~9
    for i, s in enumerate(sents):
        sp = f"{base}/{i}.png"
        items.append({"idx": i, "type": "sentence", "exists": illust_exists(sp),
                      "url": f"/illust/{lv}/{folder}/{i}.png",
                      "ko": s.get("ko", ""), "en": s.get("en", "")})
    return jsonify({"word_id": word_id, "word": korean,
                    "meaning": word.get("meaning", ""), "level": lv, "items": items})

@app.route("/illust/<int:lv>/<word>/<filename>")
def serve_illust(lv, word, filename):
    """일러스트 이미지 서빙"""
    dirpath = f"{ILLUST_DIR}/lv{lv}/{word}"
    return send_from_directory(dirpath, filename)

_regen_threads = {}   # key: (word_id, idx) → Thread
_regen_status  = {}   # key: (word_id, idx) → {status, log, error}

def _run_regen(word_id, idx, notes=""):
    """단일 이미지 재생성 (백그라운드 스레드) — VLM 통합 검증 포함"""
    key = (word_id, idx)
    _regen_status[key] = {"status": "running", "started_at": datetime.now().isoformat()}
    cmd = [sys.executable, "/app/generate_illustrations.py",
           "--db", "/app/data/LanguageTest/words_db.json",
           "--regen", str(word_id),
           "--vlm-verify"]
    if idx is not None and idx >= 0:
        cmd += ["--regen-idx", str(idx)]
    if notes:
        cmd += ["--regen-issues", notes]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        out_tail = (result.stdout or "")[-800:]
        err_tail = (result.stderr or "")[-800:]
        if result.returncode != 0:
            _regen_status[key] = {"status": "failed", "log": out_tail, "error": err_tail}
            app.logger.error(f"[regen] word={word_id} idx={idx} 실패\nSTDERR:\n{err_tail}\nSTDOUT:\n{out_tail}")
        else:
            _regen_status[key] = {"status": "done", "log": out_tail}
            app.logger.info(f"[regen] word={word_id} idx={idx} 완료\n{out_tail}")
    except subprocess.TimeoutExpired:
        _regen_status[key] = {"status": "timeout", "error": "subprocess 10분 초과"}
        app.logger.error(f"[regen] word={word_id} idx={idx} 타임아웃 (10분 초과)")
    except Exception as e:
        _regen_status[key] = {"status": "error", "error": str(e)}
        app.logger.error(f"[regen] word={word_id} idx={idx} 예외: {e}")

@app.route("/api/illustrations/regen", methods=["POST"])
def api_illust_regen():
    """개별 이미지 재생성: {"word_id": 301, "idx": 3, "notes": "..."}"""
    global _regen_threads
    data = request.get_json(silent=True) or {}
    word_id = int(data.get("word_id", 0))
    idx = data.get("idx")  # None=word, 0~9=sentence
    notes = data.get("notes", "")
    if not word_id:
        return jsonify({"error": "word_id 필요"}), 400
    regen_idx = int(idx) if idx is not None and int(idx) >= 0 else None
    key = (word_id, regen_idx)
    # 동일 이미지가 이미 재생성 중이면 거부
    if key in _regen_threads and _regen_threads[key].is_alive():
        return jsonify({"error": "해당 이미지 재생성 진행 중"}), 409
    t = threading.Thread(target=_run_regen, args=(word_id, regen_idx, notes), daemon=True)
    _regen_threads[key] = t
    t.start()
    label = f"예문[{regen_idx}]" if regen_idx is not None else "단어"
    return jsonify({"status": "started", "word_id": word_id, "target": label})

@app.route("/api/illustrations/regen/log")
def api_illust_regen_log():
    """재생성 상태/에러 로그 조회"""
    word_id = int(request.args.get("word_id", 0))
    idx_raw = request.args.get("idx", "none")
    regen_idx = int(idx_raw) if idx_raw not in ("none", "-1", "", "null") else None
    key = (word_id, regen_idx)
    info = dict(_regen_status.get(key, {"status": "unknown"}))
    info["running"] = key in _regen_threads and _regen_threads[key].is_alive()
    return jsonify(info)

@app.route("/api/illustrations/cancel", methods=["POST"])
def api_cancel_illustrations():
    global _illust_proc
    prog = load_json(ILLUST_PROG_F, {})
    # 프로세스가 살아있으면 종료
    if _illust_proc is not None:
        try:
            _illust_proc.terminate()
        except Exception:
            pass
        _illust_proc = None
    elif prog.get("status") != "running":
        return jsonify({"error": "생성 중인 작업 없음"}), 409
    # progress 파일을 cancelled로 업데이트 (프로세스 유무 무관)
    save_json(ILLUST_PROG_F, {**prog, "status": "cancelled",
                              "cancelled_at": datetime.now().isoformat()})
    return jsonify({"status": "cancelled"})

@app.route("/api/illustrations/reset", methods=["POST"])
def api_reset_illust_progress():
    """stuck된 running 상태를 강제 리셋"""
    global _illust_proc, _illust_thread
    if _illust_proc is not None:
        try: _illust_proc.terminate()
        except Exception: pass
        _illust_proc = None
    save_json(ILLUST_PROG_F, {"status": "idle", "pct": 0,
                               "reset_at": datetime.now().isoformat()})
    return jsonify({"status": "reset"})

@app.route("/api/illustrations/generate", methods=["POST"])
def api_generate_illustrations():
    data = request.get_json(silent=True) or {}
    start  = int(data.get("start", 1))
    end    = int(data.get("end", 10))
    mode   = data.get("mode", "both")  # "both", "words", "sentences"
    target = data.get("target", "nas")  # "nas" or "desktop"
    mode_label = {"both":"단어+예문","words":"단어만","sentences":"예문만"}.get(mode, mode)
    target_label = "GPU" if target == "desktop" else "NAS"
    desc = f"일러스트 {start}~{end} ({mode_label}) [{target_label}]"
    job_id = enqueue_job("illust", desc, target=target, params={"start": start, "end": end, "mode": mode})
    return jsonify({"status": "queued", "job_id": job_id, "start": start, "end": end, "mode": mode, "target": target})

AUDIT_FILE = f"{BASE}/logs/style_audit.json"
_audit_thread = None

def _run_style_audit(word_ids):
    """스타일 감사 백그라운드 실행"""
    cmd = [sys.executable, "/app/generate_illustrations.py",
           "--db", "/app/data/LanguageTest/words_db.json",
           "--style-audit"] + [str(i) for i in word_ids]
    subprocess.run(cmd)

@app.route("/api/illustrations/audit", methods=["POST"])
def api_style_audit():
    global _audit_thread
    if _audit_thread and _audit_thread.is_alive():
        return jsonify({"error": "감사 진행 중"}), 409
    data = request.get_json(silent=True) or {}
    word_ids = data.get("word_ids", [])
    if not word_ids:
        return jsonify({"error": "word_ids 필요"}), 400
    _audit_thread = threading.Thread(target=_run_style_audit, args=(word_ids,), daemon=True)
    _audit_thread.start()
    return jsonify({"status": "started", "count": len(word_ids)})

@app.route("/api/illustrations/audit/results")
def api_audit_results():
    data = load_json(AUDIT_FILE, None)
    if data is None:
        return jsonify({"error": "감사 결과 없음"}), 404
    running = bool(_audit_thread and _audit_thread.is_alive())
    return jsonify({**data, "running": running})

_audit_regen_thread = None
_audit_regen_progress = {"status": "idle"}

def _run_audit_regen_all():
    global _audit_regen_progress
    _audit_regen_progress = {"status": "running"}
    subprocess.run([sys.executable, "/app/generate_illustrations.py",
                    "--db", "/app/data/LanguageTest/words_db.json",
                    "--regen-audit-failed"])
    _audit_regen_progress = {"status": "done"}

def _run_audit_regen_selected(entries):
    global _audit_regen_progress
    total = len(entries)
    _audit_regen_progress = {"status": "running", "total": total, "done": 0, "errors": 0}
    for entry in entries:
        word_id = int(entry["word_id"])
        sent_idx = int(entry.get("sent_idx", -1))
        issues = entry.get("issues", "")
        cmd = [sys.executable, "/app/generate_illustrations.py",
               "--db", "/app/data/LanguageTest/words_db.json",
               "--regen", str(word_id), "--vlm-verify"]
        if sent_idx >= 0:
            cmd += ["--regen-idx", str(sent_idx)]
        if issues and issues != "—":
            cmd += ["--regen-issues", issues]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0:
            _audit_regen_progress["done"] = _audit_regen_progress.get("done", 0) + 1
        else:
            _audit_regen_progress["errors"] = _audit_regen_progress.get("errors", 0) + 1
    _audit_regen_progress = {**_audit_regen_progress, "status": "done"}

@app.route("/api/illustrations/audit/regen", methods=["POST"])
def api_audit_regen():
    global _audit_regen_thread
    if _audit_regen_thread and _audit_regen_thread.is_alive():
        return jsonify({"error": "재생성 진행 중"}), 409
    data = request.get_json(silent=True) or {}
    all_failed = data.get("all_failed", False)
    entries = data.get("entries", [])
    if all_failed:
        _audit_regen_thread = threading.Thread(target=_run_audit_regen_all, daemon=True)
    elif entries:
        _audit_regen_thread = threading.Thread(target=_run_audit_regen_selected, args=(entries,), daemon=True)
    else:
        return jsonify({"error": "entries 또는 all_failed 필요"}), 400
    _audit_regen_thread.start()
    return jsonify({"status": "started"})

@app.route("/api/illustrations/audit/regen/status")
def api_audit_regen_status():
    running = bool(_audit_regen_thread and _audit_regen_thread.is_alive())
    return jsonify({**_audit_regen_progress, "running": running})

# ─── 회화 API ─────────────────────────────────────────────────
@app.route("/api/conv/themes")
def api_conv_themes():
    db = load_conv_db()
    clog = load_conv_log()
    log_map = {}
    for e in clog:
        key = (str(e["theme_id"]), e["lang"], e.get("fmt", "youtube"))
        log_map[key] = e
    themes = []
    for t in db.get("themes", []):
        langs = {}
        for lang in ["EN", "JP", "CN", "VN", "ES"]:
            yt_e = log_map.get((str(t["id"]), lang, "youtube"))
            rl_e = log_map.get((str(t["id"]), lang, "reels"))
            # 로그 경로 우선, 없으면 표준 경로로 fallback 확인
            yt_path = (yt_e.get("video_path") if yt_e else None) or _conv_video_path(str(t["id"]), lang, "youtube")
            rl_path = (rl_e.get("video_path") if rl_e else None) or _conv_video_path(str(t["id"]), lang, "reels")
            langs[lang] = {
                "rendered":       bool(yt_e and _conv_path_exists(yt_path)),
                "uploaded":       bool(yt_e and yt_e.get("uploaded")),
                "video_id":       yt_e.get("video_id") if yt_e else None,
                "reels_rendered": bool(rl_e and _conv_path_exists(rl_path)),
                "reels_uploaded": bool(rl_e and rl_e.get("uploaded")),
            }
        themes.append({
            "id": t["id"], "emoji": t.get("emoji", "💬"),
            "title": t.get("title", {}),
            "phrase_count": len(t.get("phrases", [])),
            "color": t.get("color", "#818cf8"),
            "langs": langs,
        })
    return jsonify({"themes": themes})

@app.route("/api/conv/render", methods=["POST"])
def api_conv_render():
    data = request.get_json(silent=True) or {}
    theme_id = data.get("theme_id")
    lang = data.get("lang", "EN")
    if not theme_id:
        return jsonify({"error": "theme_id 필요"}), 400
    target = data.get("target", "nas")
    fmt = data.get("fmt", "youtube")
    fmt_label = " [쇼츠]" if fmt == "reels" else ""
    desc = f"회화영상 {theme_id} [{lang}]{fmt_label}"
    job_id = enqueue_job("conv_video", desc, target=target,
                         params={"theme_id": theme_id, "lang": lang, "fmt": fmt})
    return jsonify({"status": "queued", "job_id": job_id, "theme_id": theme_id, "lang": lang})

@app.route("/api/conv/render/status")
def api_conv_render_status():
    running = bool(_conv_render_thread and _conv_render_thread.is_alive())
    return jsonify({**_conv_render_progress, "running": running})

@app.route("/api/conv/upload", methods=["POST"])
def api_conv_upload():
    data = request.get_json(silent=True) or {}
    theme_id = data.get("theme_id")
    lang = data.get("lang", "EN")
    fmt = data.get("fmt", "youtube")
    if not theme_id:
        return jsonify({"error": "theme_id 필요"}), 400
    video_id, err = run_conv_upload(theme_id, lang, fmt=fmt)
    if err:
        return jsonify({"error": err}), 500
    return jsonify({"status": "ok", "video_id": video_id,
                    "youtube_url": f"https://youtube.com/watch?v={video_id}"})

# ─── 회화 일러스트·영상 API ───────────────────────────────────
# ─── K-드라마 API ────────────────────────────────────────────
@app.route("/api/kdrama/themes")
def api_kdrama_themes():
    db = load_kdrama_db()
    klog = load_kdrama_log()
    log_map = {}
    for e in klog:
        key = (str(e["theme_id"]), e["lang"], e.get("fmt", "youtube"))
        log_map[key] = e
    themes = []
    for t in db.get("themes", []):
        langs = {}
        for lang in ["EN", "JP", "CN", "VN", "ES"]:
            yt_e = log_map.get((str(t["id"]), lang, "youtube"))
            rl_e = log_map.get((str(t["id"]), lang, "reels"))
            yt_path = (yt_e.get("video_path") if yt_e else None) or _kdrama_video_path(str(t["id"]), lang, "youtube")
            rl_path = (rl_e.get("video_path") if rl_e else None) or _kdrama_video_path(str(t["id"]), lang, "reels")
            langs[lang] = {
                "rendered":       bool(yt_e and _conv_path_exists(yt_path)),
                "uploaded":       bool(yt_e and yt_e.get("uploaded")),
                "video_id":       yt_e.get("video_id") if yt_e else None,
                "reels_rendered": bool(rl_e and _conv_path_exists(rl_path)),
                "reels_uploaded": bool(rl_e and rl_e.get("uploaded")),
            }
        themes.append({
            "id": t["id"], "emoji": t.get("emoji", "🎬"),
            "title": t.get("title", {}),
            "category": t.get("category", ""),
            "phrase_count": len(t.get("phrases", [])),
            "color": t.get("color", "#FF6B9D"),
            "langs": langs,
        })
    return jsonify({"themes": themes})


@app.route("/api/kdrama/render", methods=["POST"])
def api_kdrama_render():
    data = request.get_json(silent=True) or {}
    theme_id = data.get("theme_id")
    lang = data.get("lang", "EN")
    if not theme_id:
        return jsonify({"error": "theme_id 필요"}), 400
    fmt = data.get("fmt", "youtube")
    fmt_label = " [쇼츠]" if fmt == "reels" else ""
    desc = f"K드라마 {theme_id} [{lang}]{fmt_label}"
    job_id = enqueue_job("kdrama_video", desc, target=data.get("target", "nas"),
                         params={"theme_id": theme_id, "lang": lang, "fmt": fmt})
    return jsonify({"status": "queued", "job_id": job_id, "theme_id": theme_id, "lang": lang})


@app.route("/api/kdrama/upload", methods=["POST"])
def api_kdrama_upload():
    data = request.get_json(silent=True) or {}
    theme_id = str(data.get("theme_id", ""))
    lang = data.get("lang", "EN")
    fmt = data.get("fmt", "youtube")
    if not theme_id:
        return jsonify({"error": "theme_id 필요"}), 400
    vid, err = run_kdrama_upload(theme_id, lang, fmt)
    if not vid:
        return jsonify({"error": err or "업로드 실패"}), 500
    return jsonify({"status": "ok", "video_id": vid,
                    "youtube_url": f"https://youtube.com/watch?v={vid}"})


# ─── K-드라마 일러스트 API ───────────────────────────────────
@app.route("/api/kdrama/illust/start", methods=["POST"])
def api_kdrama_illust_start():
    """K-드라마 인트로 일러스트 생성 작업 큐에 추가."""
    data = request.get_json(silent=True) or {}
    theme_id = data.get("theme_id")
    start    = data.get("start")
    end      = data.get("end")
    overwrite    = bool(data.get("overwrite"))
    intro_only   = bool(data.get("intro_only"))
    phrases_only = bool(data.get("phrases_only"))

    params = {"overwrite": overwrite,
              "intro_only": intro_only,
              "phrases_only": phrases_only}
    mode_label = "Phrase만" if phrases_only else ("인트로만" if intro_only else "인트로+Phrase")
    if theme_id is not None:
        params["theme_id"] = int(theme_id)
        desc = f"K드라마 일러스트 #{theme_id} ({mode_label})"
    elif start is not None and end is not None:
        params["start"] = int(start)
        params["end"]   = int(end)
        desc = f"K드라마 일러스트 {start}~{end} ({mode_label})"
    else:
        desc = f"K드라마 일러스트 전체 100개 ({mode_label})"

    job_id = enqueue_job("kdrama_illust", desc,
                         target=data.get("target", "nas"), params=params)
    return jsonify({"status": "queued", "job_id": job_id})


@app.route("/api/kdrama/illust/status")
def api_kdrama_illust_status():
    """K-드라마 일러스트 생성 진행 상황 + 테마별 완성 여부."""
    prog = load_json(KDRAMA_ILLUST_PROG, {})
    try:
        with open(KDRAMA_DB_PATH, encoding="utf-8") as f:
            db_raw = json.load(f)
    except Exception:
        db_raw = []
    themes = db_raw if isinstance(db_raw, list) else db_raw.get("themes", [])
    items = []
    intro_done_total = 0
    phrase_done_total = 0
    for t in themes:
        tid = t["id"]
        theme_dir = os.path.join(KDRAMA_ILLUST_DIR, f"sit_{tid}")
        intro_p = os.path.join(theme_dir, "intro.png")
        intro_done = os.path.exists(intro_p) and os.path.getsize(intro_p) > 0
        phrases_done = 0
        for i in range(1, 11):
            pp = os.path.join(theme_dir, f"phrase_{i}.png")
            if os.path.exists(pp) and os.path.getsize(pp) > 0:
                phrases_done += 1
        if intro_done: intro_done_total += 1
        phrase_done_total += phrases_done
        items.append({
            "id": tid,
            "situation": t.get("situation", ""),
            "category": t.get("category", ""),
            "done": intro_done,                 # intro 기준 (기존 호환)
            "intro_done": intro_done,
            "phrases_done": phrases_done,        # 0-10
            "all_done": intro_done and phrases_done == 10,
            "path": intro_p if intro_done else None,
        })
    return jsonify({
        "total": len(items),
        "done": intro_done_total,                # intro 완료 수 (기존 호환)
        "intro_done": intro_done_total,
        "phrases_done": phrase_done_total,       # 전체 phrase 이미지 합계
        "phrases_total": len(items) * 10,
        "all_done": sum(1 for x in items if x["all_done"]),
        "items": items,
        "progress": prog,
    })


@app.route("/api/kdrama/illust/image/<int:tid>")
def api_kdrama_illust_image(tid):
    """썸네일 미리보기용 — 해당 테마의 intro.png 반환."""
    p = os.path.join(KDRAMA_ILLUST_DIR, f"sit_{tid}", "intro.png")
    if not os.path.exists(p):
        return jsonify({"error": "not found"}), 404
    return send_from_directory(os.path.dirname(p), os.path.basename(p))


@app.route("/api/kdrama/illust/panel/<int:tid>/<key>")
def api_kdrama_illust_panel(tid, key):
    """패널 단일 이미지 반환 — key: intro | phrase_1..phrase_10"""
    if key != "intro" and not (key.startswith("phrase_") and key[7:].isdigit()):
        return jsonify({"error": "invalid key"}), 400
    p = os.path.join(KDRAMA_ILLUST_DIR, f"sit_{tid}", f"{key}.png")
    if not os.path.exists(p):
        return jsonify({"error": "not found"}), 404
    return send_from_directory(os.path.dirname(p), os.path.basename(p))


@app.route("/api/kdrama/illust/delete", methods=["POST"])
def api_kdrama_illust_delete():
    """단일 패널 이미지 삭제 — body: {theme_id, key}"""
    data = request.get_json(silent=True) or {}
    tid = data.get("theme_id")
    key = data.get("key", "")
    if not tid:
        return jsonify({"error": "theme_id 필요"}), 400
    if key != "intro" and not (key.startswith("phrase_") and key[7:].isdigit()):
        return jsonify({"error": "invalid key"}), 400
    p = os.path.join(KDRAMA_ILLUST_DIR, f"sit_{int(tid)}", f"{key}.png")
    deleted = False
    if os.path.exists(p):
        try:
            os.remove(p)
            deleted = True
        except Exception as e:
            return jsonify({"error": f"삭제 실패: {e}"}), 500
    # .txt 캐시도 함께 삭제
    txt_p = p + ".txt"
    if os.path.exists(txt_p):
        try: os.remove(txt_p)
        except Exception: pass
    return jsonify({"ok": True, "deleted": deleted, "path": p})


@app.route("/api/kdrama/illust/browse/<int:tid>")
def api_kdrama_illust_browse(tid):
    """테마의 11개 패널(intro + phrase 1~10)을 대화 텍스트와 함께 반환"""
    try:
        with open(KDRAMA_DB_PATH, encoding="utf-8") as f:
            db_raw = json.load(f)
    except Exception:
        return jsonify({"error": "DB load failed"}), 500
    themes = db_raw if isinstance(db_raw, list) else db_raw.get("themes", [])
    theme = next((t for t in themes if t["id"] == tid), None)
    if not theme:
        return jsonify({"error": f"theme {tid} not found"}), 404
    theme_dir = os.path.join(KDRAMA_ILLUST_DIR, f"sit_{tid}")
    items = []
    # intro
    intro_p = os.path.join(theme_dir, "intro.png")
    items.append({
        "key": "intro",
        "label": "Intro",
        "exists": os.path.exists(intro_p) and os.path.getsize(intro_p) > 0,
        "url": f"/api/kdrama/illust/panel/{tid}/intro",
        "ko": theme.get("situation", ""),
        "en": theme.get("situation_en", ""),
    })
    # phrases
    phrases = theme.get("phrases", []) or []
    for i, phrase in enumerate(phrases[:10]):
        key = f"phrase_{i+1}"
        pp = os.path.join(theme_dir, f"{key}.png")
        my = phrase.get("my_line", {}) or {}
        resp = phrase.get("response", {}) or {}
        items.append({
            "key": key,
            "label": f"P{i+1}",
            "exists": os.path.exists(pp) and os.path.getsize(pp) > 0,
            "url": f"/api/kdrama/illust/panel/{tid}/{key}",
            "ko": my.get("ko", ""),
            "en": my.get("en", ""),
            "resp_ko": resp.get("ko", ""),
            "resp_en": resp.get("en", ""),
        })
    return jsonify({
        "id": tid,
        "situation": theme.get("situation", ""),
        "situation_en": theme.get("situation_en", ""),
        "category": theme.get("category", ""),
        "items": items,
    })


@app.route("/api/phrase/situations")
def api_phrase_situations():
    db = load_phrase_db()
    if isinstance(db, list):
        situations = db
    else:
        situations = db.get("situations", [])

    video_log = load_phrase_video_log()
    video_map = {e["situation_id"]: e for e in video_log}

    # 일러스트 진행 파일에서 완성 목록 읽기
    illust_prog = load_json(PHRASE_ILLUST_PROG, {})
    completed = illust_prog.get("completed", {})

    result = []
    for s in situations:
        sid = s["id"]
        sit_key = f"sit_{sid}"
        illust_dir = os.path.join(PHRASE_ILLUST_DIR, sit_key)
        phrase_count = len(s.get("phrases", []))
        # 일러스트 수: intro + phrase_N
        expected_keys = ["intro"] + [f"phrase_{p['id']}" for p in s.get("phrases", [])]
        illust_done = [k for k in expected_keys if os.path.exists(os.path.join(illust_dir, f"{k}.png"))]
        video_entry = video_map.get(sid)
        result.append({
            "id": sid,
            "category": s.get("category", ""),
            "situation": s.get("situation", ""),
            "situation_en": s.get("situation_en", ""),
            "phrase_count": phrase_count,
            "illust_total": len(expected_keys),
            "illust_done": len(illust_done),
            "video_exists": bool(video_entry and os.path.exists(video_entry.get("output_path", ""))),
            "video_generated_at": video_entry.get("generated_at") if video_entry else None,
        })
    return jsonify({"situations": result})

@app.route("/api/phrase/illust/generate", methods=["POST"])
def api_phrase_illust_generate():
    data = request.get_json(silent=True) or {}
    sit_id = data.get("sit_id")
    start  = data.get("start")
    end    = data.get("end")
    target = data.get("target", "nas")
    if sit_id is not None:
        desc = f"회화 일러스트 상황#{sit_id}"
    else:
        desc = f"회화 일러스트 {start}~{end}"
    job_id = enqueue_job("phrase_illust", desc, target=target,
                         params={"sit_id": sit_id, "start": start, "end": end})
    return jsonify({"status": "queued", "job_id": job_id})

@app.route("/api/phrase/illust/progress")
def api_phrase_illust_progress():
    running = bool(_phrase_illust_thread and _phrase_illust_thread.is_alive())
    prog = load_json(PHRASE_ILLUST_PROG, {})
    return jsonify({**_phrase_illust_progress, "running": running,
                    "file_progress": prog})

@app.route("/api/phrase/illust/panel-status/<int:sit_id>")
def api_phrase_panel_status(sit_id):
    """패널 뷰어 실시간 상태 — completed / failed / current 반환 (파일 존재 확인)"""
    prog = load_json(PHRASE_ILLUST_PROG, {})
    sit_key = str(sit_id)
    sit_dir = os.path.join(PHRASE_ILLUST_DIR, f"sit_{sit_id}")
    # progress 기록이 아닌 실제 파일 존재 여부로 completed 판단
    raw_completed = prog.get("completed", {}).get(sit_key, [])
    completed = []
    for key in raw_completed:
        if key == "intro":
            if os.path.isfile(os.path.join(sit_dir, "intro.png")):
                completed.append(key)
        elif key.startswith("phrase_"):
            ph_id = key.split("_", 1)[1]
            if os.path.isfile(os.path.join(sit_dir, f"phrase_{ph_id}.png")):
                completed.append(key)
    return jsonify({
        "sit_id":    sit_id,
        "completed": completed,
        "failed":    prog.get("failed",    {}).get(sit_key, {}),
        "current":   prog.get("current"),   # {"sit_id": N, "key": "phrase_1"} or null
    })

@app.route("/api/illustrations/live-status")
def api_illust_live_status():
    """단어 일러스트 실시간 현재 생성 중인 항목 반환"""
    prog = load_json(ILLUST_PROG_F, {})
    return jsonify({
        "status":           prog.get("status", "idle"),
        "pct":              prog.get("pct", 0),
        "current_word_id":  prog.get("current_word_id"),
        "current_type":     prog.get("current_type", ""),
        "current_sent_idx": prog.get("current_sent_idx"),
    })

@app.route("/api/phrase/illust/cancel", methods=["POST"])
def api_phrase_illust_cancel():
    global _phrase_illust_progress
    _phrase_illust_progress = {**_phrase_illust_progress, "status": "cancelled", "msg": "취소됨"}
    return jsonify({"status": "cancelled"})

@app.route("/api/phrase/video/generate", methods=["POST"])
def api_phrase_video_generate():
    data = request.get_json(silent=True) or {}
    sit_id = data.get("sit_id")
    start  = data.get("start")
    end    = data.get("end")
    lang   = data.get("lang", "EN")
    target = data.get("target", "nas")
    fmt    = data.get("fmt", "youtube")
    if sit_id is not None:
        desc = f"회화영상 상황#{sit_id} [{lang}]"
    else:
        desc = f"회화영상 {start}~{end} [{lang}]"
    job_id = enqueue_job("phrase_video", desc, target=target,
                         params={"sit_id": sit_id, "start": start, "end": end, "lang": lang, "fmt": fmt})
    return jsonify({"status": "queued", "job_id": job_id})

@app.route("/api/phrase/video/progress")
def api_phrase_video_progress():
    running = bool(_phrase_video_thread and _phrase_video_thread.is_alive())
    return jsonify({**_phrase_video_progress, "running": running})

@app.route("/api/phrase/video/cancel", methods=["POST"])
def api_phrase_video_cancel():
    global _phrase_video_progress
    _phrase_video_progress = {**_phrase_video_progress, "status": "cancelled", "msg": "취소됨"}
    return jsonify({"status": "cancelled"})

@app.route("/phrase-illust/<sit_key>/<filename>")
def serve_phrase_illust(sit_key, filename):
    directory = os.path.join(PHRASE_ILLUST_DIR, sit_key)
    return send_from_directory(directory, filename)

@app.route("/api/phrase/illust/browse/<int:sit_id>")
def api_phrase_illust_browse(sit_id):
    """회화 상황별 일러스트 상태 조회 (썸네일 + 존재 여부)"""
    db = load_phrase_db()
    situations = db if isinstance(db, list) else db.get("situations", [])
    sit = next((s for s in situations if s["id"] == sit_id), None)
    if not sit:
        return jsonify({"error": "상황 없음"}), 404
    sit_key   = f"sit_{sit_id}"
    illust_dir = os.path.join(PHRASE_ILLUST_DIR, sit_key)
    items = []
    intro_path = os.path.join(illust_dir, "intro.png")
    items.append({
        "key": "intro", "label": "인트로",
        "ko": sit.get("situation", ""),
        "exists": os.path.exists(intro_path),
        "url": f"/phrase-illust/{sit_key}/intro.png"
    })
    for p in sit.get("phrases", []):
        ph_id  = p["id"]
        ph_key = f"phrase_{ph_id}"
        ph_path = os.path.join(illust_dir, f"{ph_key}.png")
        items.append({
            "key": ph_key, "label": f"대화 {ph_id}",
            "ko":      p.get("my_line", {}).get("ko", ""),
            "en":      p.get("my_line", {}).get("en", ""),
            "resp_ko": p.get("response",  {}).get("ko", ""),
            "resp_en": p.get("response",  {}).get("en", ""),
            "tip":     p.get("tip", ""),
            "exists": os.path.exists(ph_path),
            "url": f"/phrase-illust/{sit_key}/{ph_key}.png"
        })
    return jsonify({
        "sit_id": sit_id,
        "situation": sit.get("situation", ""),
        "situation_en": sit.get("situation_en", ""),
        "category": sit.get("category", ""),
        "items": items
    })

_phrase_regen_threads: dict = {}
_phrase_regen_status:  dict = {}

def _run_phrase_regen(sit_id: int, key: str):
    """회화 패널 단일 재생성 (백그라운드 스레드)"""
    rkey = (sit_id, key)
    _phrase_regen_status[rkey] = {"status": "running", "started_at": datetime.now().isoformat()}
    sit_dir   = os.path.join(PHRASE_ILLUST_DIR, f"sit_{sit_id}")
    file_path = os.path.join(sit_dir, f"{key}.png")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass
    cmd = [sys.executable, "/app/generate_phrase_illustrations.py",
           "--db", PHRASE_DB_F, "--situation-id", str(sit_id)]
    if key == "intro":
        cmd += ["--intro-only"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        out_tail = (result.stdout or "")[-800:]
        err_tail = (result.stderr or "")[-800:]
        if result.returncode != 0:
            _phrase_regen_status[rkey] = {"status": "failed", "log": out_tail, "error": err_tail}
            app.logger.error(f"[phrase_regen] sit={sit_id} key={key} 실패\n{err_tail}")
        else:
            _phrase_regen_status[rkey] = {"status": "done", "log": out_tail}
    except subprocess.TimeoutExpired:
        _phrase_regen_status[rkey] = {"status": "timeout", "error": "subprocess 5분 초과"}
    except Exception as e:
        _phrase_regen_status[rkey] = {"status": "error", "error": str(e)}

@app.route("/api/phrase/illust/regen", methods=["POST"])
def api_phrase_illust_regen():
    """회화 패널 단일 재생성 → 글로벌 큐에 순차 추가"""
    data   = request.get_json(silent=True) or {}
    sit_id = int(data.get("sit_id", 0))
    key    = data.get("key", "")
    if not sit_id or not key:
        return jsonify({"error": "sit_id, key 필요"}), 400
    target = data.get("target") or (get_render_config().get("desktop_enabled") and "desktop" or "nas")
    desc   = f"일러스트 재생성: sit_{sit_id}/{key}"
    job_id = enqueue_job("phrase_illust_regen", desc, target=target,
                         params={"sit_id": sit_id, "key": key})
    return jsonify({"status": "queued", "job_id": job_id, "sit_id": sit_id, "key": key})

@app.route("/api/phrase/illust/regen/log")
def api_phrase_illust_regen_log():
    """회화 패널 재생성 상태/로그 조회"""
    sit_id = int(request.args.get("sit_id", 0))
    key    = request.args.get("key", "")
    rkey   = (sit_id, key)
    info   = dict(_phrase_regen_status.get(rkey, {"status": "unknown"}))
    info["running"] = rkey in _phrase_regen_threads and _phrase_regen_threads[rkey].is_alive()
    return jsonify(info)

@app.route("/api/phrase/illust/delete", methods=["POST"])
def api_phrase_illust_delete():
    """회화 일러스트 단일 이미지 삭제: {"sit_id": 1, "key": "phrase_3"}"""
    data   = request.get_json(silent=True) or {}
    sit_id = int(data.get("sit_id", 0))
    key    = data.get("key", "")
    if not sit_id or not key:
        return jsonify({"error": "sit_id, key 필요"}), 400
    sit_key  = f"sit_{sit_id}"
    img_path = os.path.join(PHRASE_ILLUST_DIR, sit_key, f"{key}.png")
    if not os.path.exists(img_path):
        return jsonify({"error": "파일 없음"}), 404
    try:
        os.remove(img_path)
        return jsonify({"status": "deleted", "sit_id": sit_id, "key": key})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/illustrations/delete", methods=["POST"])
def api_illust_delete():
    """단어 일러스트 이미지 삭제: {"word_id": 301, "level": 1, "idx": 3}  (idx=-1 → word.png)"""
    data    = request.get_json(silent=True) or {}
    word_id = int(data.get("word_id", 0))
    level   = int(data.get("level", 1))
    idx     = data.get("idx")
    if not word_id or idx is None:
        return jsonify({"error": "word_id, idx 필요"}), 400
    db = get_words_db()
    word = next((w for w in db if w["id"] == word_id and w.get("level") == level), None)
    if not word:
        return jsonify({"error": "단어 없음"}), 404
    folder   = f"{word_id}_{word['word']}"
    filename = "word.png" if int(idx) < 0 else f"{int(idx)}.png"
    img_path = os.path.join(ILLUST_DIR, f"lv{level}", folder, filename)
    if not os.path.exists(img_path):
        return jsonify({"error": "파일 없음"}), 404
    try:
        os.remove(img_path)
        return jsonify({"status": "deleted", "word_id": word_id, "idx": idx})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/queue/cleanup", methods=["POST"])
def api_queue_cleanup():
    """완료/실패/취소된 작업을 글로벌 큐에서 제거"""
    q = load_global_queue()
    before = len(q["jobs"])
    keep = {"queued", "running"}
    q["jobs"] = [j for j in q["jobs"] if j["status"] in keep]
    after = len(q["jobs"])
    save_global_queue(q)
    return jsonify({"removed": before - after, "remaining": after})

# ─── HTML ─────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hellowords Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
:root{--bg:#0d1117;--bg2:#161b22;--bg3:#1c2128;--border:#21262d;--border2:#30363d;--text:#e6edf3;--muted:#8b949e;--muted2:#484f58;--accent:#818cf8;--green:#3fb950;--red:#f87171;--amber:#f59e0b;--blue:#58a6ff;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,-apple-system,sans-serif;display:flex;flex-direction:column;height:100vh;overflow:hidden;}
::-webkit-scrollbar{width:5px;}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px;}
::-webkit-scrollbar-track{background:transparent;}
/* HEADER */
#header{background:var(--bg2);border-bottom:1px solid var(--border);padding:0 20px;height:48px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;z-index:100;}
#header .logo{font-weight:700;font-size:.92rem;letter-spacing:-.02em;}
#header .clock{font-size:.75rem;color:var(--muted);font-variant-numeric:tabular-nums;}
#header .status-pill{display:flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;font-size:.7rem;font-weight:600;background:var(--bg3);border:1px solid var(--border);}
/* LAYOUT */
#body{display:flex;flex:1;overflow:hidden;}
#sidebar{width:200px;background:var(--bg);border-right:1px solid var(--border);overflow-y:auto;flex-shrink:0;padding:6px 0;display:flex;flex-direction:column;}
#main{flex:1;overflow-y:auto;padding:20px 24px;}
/* SIDEBAR */
.s-group{display:flex;align-items:center;justify-content:space-between;padding:10px 14px 4px;font-size:.62rem;font-weight:700;color:var(--muted);letter-spacing:.06em;margin-top:4px;user-select:none;}
.s-group.tog{cursor:pointer;}
.s-group.tog:hover{color:var(--text);}
.s-arr{font-size:.55rem;transition:transform .2s;flex-shrink:0;margin-left:auto;}
.s-sep{height:1px;background:var(--border);margin:8px 14px;}
.s-item{display:flex;align-items:center;gap:7px;padding:7px 14px;cursor:pointer;font-size:.8rem;color:var(--muted);border-left:2px solid transparent;transition:all .12s;user-select:none;}
.s-item:hover{background:var(--bg2);color:var(--text);}
.s-item.active{background:var(--bg2);color:var(--text);border-left-color:var(--c,var(--accent));}
.s-item.l2{padding-left:26px;font-size:.78rem;}
.s-item.l3{padding-left:40px;font-size:.75rem;}
.s-item .arrow{margin-left:auto;font-size:.55rem;color:var(--muted2);transition:.2s;}
.s-ch{display:none;}.s-ch.open{display:block;}
.s-item.dim{opacity:.45;cursor:default;}
.s-item.dim:hover{background:transparent;color:var(--muted);}
/* CARDS */
.card{background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:16px;}
.card-sm{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:12px;}
.kpi{text-align:center;}
.kpi .num{font-size:1.6rem;font-weight:700;line-height:1.1;}
.kpi .label{font-size:.68rem;color:var(--muted);margin-top:4px;}
/* PROGRESS */
.pbar-bg{background:var(--border);border-radius:4px;overflow:hidden;}
.pbar{border-radius:4px;transition:width .4s ease;}
/* TABLE */
table{width:100%;border-collapse:collapse;}
th{color:var(--muted);font-size:.66rem;text-transform:uppercase;padding:7px 10px;border-bottom:1px solid var(--border);text-align:left;font-weight:500;letter-spacing:.03em;}
td{padding:7px 10px;border-bottom:1px solid var(--border);font-size:.8rem;}
tr:hover td{background:var(--bg3);}
/* BADGES */
.badge{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:20px;font-size:.66rem;font-weight:600;}
.badge-g{background:#0d2b0d;color:var(--green);border:1px solid var(--green);}
.badge-p{background:#1c1c2e;color:var(--accent);border:1px solid var(--accent);}
.badge-a{background:#2d1f00;color:var(--amber);border:1px solid var(--amber);}
.badge-m{background:var(--bg3);color:var(--muted);border:1px solid var(--border2);}
/* BUTTONS */
.btn{padding:6px 14px;border-radius:7px;font-size:.76rem;font-weight:600;cursor:pointer;border:1px solid;transition:.12s;display:inline-flex;align-items:center;gap:5px;}
.btn:hover{filter:brightness(1.15);}
.btn-g{background:#0d2b0d;color:var(--green);border-color:var(--green);}
.btn-r{background:#2b0d0d;color:var(--red);border-color:var(--red);}
.btn-a{background:#2d1f00;color:var(--amber);border-color:var(--amber);}
.btn-p{background:#1a1a3a;color:var(--accent);border-color:var(--accent);}
.btn-b{background:#0d1b2b;color:var(--blue);border-color:var(--blue);}
.btn-m{background:transparent;color:var(--muted);border-color:var(--border2);}
/* GRIDS */
.g2{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;}
.g6{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;}
/* TABS */
.tabs{display:flex;gap:0;border-bottom:1px solid var(--border);margin-bottom:16px;}
.tab{padding:8px 16px;font-size:.78rem;font-weight:600;color:var(--muted);cursor:pointer;border-bottom:2px solid transparent;transition:.12s;background:none;border-top:none;border-left:none;border-right:none;}
.tab:hover{color:var(--text);}
.tab.on{color:var(--text);border-bottom-color:var(--green);}
/* BREADCRUMB */
.bc{font-size:.76rem;color:var(--muted);margin-bottom:16px;display:flex;align-items:center;gap:5px;}
.bc span{cursor:pointer;}.bc span:hover{color:var(--text);}.bc .cur{color:var(--text);font-weight:600;}
/* SECTION */
.sec{font-size:.74rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;}
/* MISC */
.pulse{animation:pulse 1.8s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
@keyframes regenProg{0%{width:0%}60%{width:75%}85%{width:88%}95%{width:93%}100%{width:96%}}
/* ── BATCH REDESIGN ─── */
.batch-section{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:14px 16px;margin-bottom:10px;}
.batch-section-header{display:flex;align-items:center;gap:8px;margin-bottom:12px;}
.batch-section-title{font-size:.88rem;font-weight:700;}
.batch-section-sub{font-size:.75rem;font-weight:600;color:var(--muted);}
.batch-section-badge{margin-left:auto;font-size:.65rem;color:var(--muted2);}
.batch-word-info{font-size:1.2rem;font-weight:700;color:var(--blue);}
.batch-divider{border:none;border-top:1px solid var(--border);margin:10px 0;}
.batch-setting-row{display:flex;align-items:center;gap:10px;margin-bottom:8px;}
.batch-setting-label{font-size:.65rem;color:var(--muted2);font-weight:600;text-transform:uppercase;letter-spacing:.05em;min-width:62px;flex-shrink:0;}
.pill-group{display:flex;gap:4px;flex-wrap:wrap;}
.pill{padding:3px 10px;border-radius:20px;font-size:.68rem;font-weight:600;cursor:pointer;border:1px solid var(--border2);background:transparent;color:var(--muted);transition:.12s;}
.pill:hover{border-color:var(--muted);color:var(--text);}
.pill.on{background:var(--bg3);border-color:var(--blue);color:var(--blue);}
.pill.on-green{background:#0d2b0d;border-color:var(--green);color:var(--green);}
.batch-lang-table{width:100%;font-size:.7rem;border-collapse:collapse;margin-bottom:10px;}
.batch-lang-table th{text-align:left;padding:4px 6px;font-size:.62rem;color:var(--muted2);border-bottom:1px solid var(--border);font-weight:500;text-transform:none;letter-spacing:0;}
.batch-lang-table td{padding:4px 6px;border-bottom:1px solid var(--border);}
.batch-action-row{display:flex;gap:7px;margin-top:12px;}
.batch-footer{background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:14px 16px;margin-bottom:8px;}
.batch-auto-row{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;background:var(--bg2);border:1px solid var(--border);border-radius:9px;margin-top:10px;}
.batch-auto-title{font-size:.84rem;font-weight:700;}
.batch-auto-sub{font-size:.64rem;color:var(--muted);margin-top:2px;}
.batch-prebuf-row{display:flex;align-items:center;gap:6px;}
@keyframes regenSpin{to{transform:rotate(360deg)}}
@keyframes spin{to{transform:rotate(360deg)}}
.regen-overlay{position:absolute;inset:0;background:rgba(0,0,0,.78);border-radius:6px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;z-index:10;}
.regen-overlay .regen-spinner{width:28px;height:28px;border:3px solid rgba(255,255,255,.15);border-top-color:#6366f1;border-radius:50%;animation:regenSpin .8s linear infinite;}
.regen-overlay .regen-bar-wrap{width:75%;height:5px;background:rgba(255,255,255,.12);border-radius:3px;overflow:hidden;}
.regen-overlay .regen-bar{height:100%;background:linear-gradient(90deg,#6366f1,#818cf8);border-radius:3px;animation:regenProg 270s ease-out forwards;}
.chip{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:16px;font-size:.7rem;background:var(--border);border:1px solid var(--border2);}
.num-input{background:var(--border);border:1px solid var(--border2);border-radius:5px;color:var(--text);padding:4px 8px;font-size:.78rem;width:68px;}
.view{display:none;}.view:first-child{display:block;}
.slot{display:flex;align-items:center;gap:8px;padding:10px 12px;background:var(--bg3);border-radius:8px;margin-bottom:5px;border:1px solid var(--border);}
.slot.hl{border-color:rgba(63,185,80,.25);}
select.inp{background:var(--border);color:var(--text);border:1px solid var(--border2);border-radius:6px;padding:5px 8px;font-size:.76rem;}
input.inp{background:var(--border);color:var(--text);border:1px solid var(--border2);border-radius:6px;padding:5px 8px;font-size:.76rem;}
</style>
</head>
<body>
<!-- ══ HEADER ═══════════════════════════════════════════ -->
<div id="header">
  <div style="display:flex;align-items:center;gap:10px;">
    <span style="font-size:1.15rem;">🌍</span>
    <span class="logo">Hellowords</span>
  </div>
  <div style="display:flex;align-items:center;gap:10px;">
    <div id="render-status" class="status-pill" style="display:none;">
      <span class="pulse" style="color:var(--green);">●</span>
      <span id="rs-text">렌더링 중...</span>
    </div>
    <span id="queue-badge" style="font-size:.68rem;color:var(--muted);"></span>
    <div style="text-align:right;">
      <div id="clock" class="clock"></div>
      <div id="last-upd" style="font-size:.58rem;color:var(--muted2);"></div>
    </div>
  </div>
</div>
<!-- 진행 바 -->
<div id="progress-row" style="display:none;background:var(--bg2);border-bottom:1px solid var(--border);padding:6px 20px;align-items:center;gap:12px;flex-shrink:0;">
  <span id="pr-word" style="font-weight:700;color:var(--accent);font-size:.85rem;min-width:100px;"></span>
  <span id="pr-step" style="font-size:.72rem;color:var(--muted);flex:0 0 180px;"></span>
  <div class="pbar-bg" style="flex:1;height:5px;"><div id="pr-bar" class="pbar" style="width:0%;height:5px;background:linear-gradient(90deg,#6366f1,#a855f7);"></div></div>
  <span id="pr-pct" style="font-size:.72rem;color:var(--muted);min-width:30px;text-align:right;"></span>
</div>

<!-- ══ BODY ═══════════════════════════════════════════ -->
<div id="body">
<!-- ── SIDEBAR ── -->
<div id="sidebar">
  <div class="s-item active" data-view="overview" onclick="nav(this,'overview')" style="--c:#818cf8;">
    <span>📊</span><span>대시보드</span>
  </div>

  <!-- 시험별 단어 (JS 동적 생성) -->
  <div id="sb-exam-list"></div>
  <div class="s-sep"></div>

  <!-- 단어 -->
  <div class="s-group tog" onclick="toggleSGroup('word')">
    <span>📚 단어</span><span class="s-arr" id="s-arr-word">▾</span>
  </div>
  <div class="s-ch open" id="s-ch-word">
    <div class="s-item l2" data-view="videos" onclick="nav(this,'videos')" style="--c:#818cf8;">
      <span>🎬</span><span>영상</span>
    </div>
    <div class="s-item l2" data-view="word-illust" onclick="navRenderTab(this,'illust')" style="--c:#a78bfa;">
      <span>🎨</span><span>일러스트</span>
    </div>
  </div>

  <!-- 회화 -->
  <div class="s-group tog" onclick="toggleSGroup('conv')">
    <span>💬 회화</span><span class="s-arr" id="s-arr-conv">▾</span>
  </div>
  <div class="s-ch open" id="s-ch-conv">
    <div class="s-item l2" data-view="conv-video" onclick="navConvTab(this,'basic')" style="--c:#ec4899;">
      <span>🎬</span><span>영상</span>
    </div>
    <div class="s-item l2" data-view="conv-illust" onclick="navConvTab(this,'illust')" style="--c:#f472b6;">
      <span>🖼</span><span>일러스트</span>
    </div>
  </div>

  <!-- K-드라마 -->
  <div class="s-group tog" onclick="toggleSGroup('kdrama')">
    <span>🎬 K-드라마</span><span class="s-arr" id="s-arr-kdrama">▾</span>
  </div>
  <div class="s-ch open" id="s-ch-kdrama">
    <div class="s-item l2" data-view="kdrama-video" onclick="navKdramaTab(this,'video')" style="--c:#C77DFF;">
      <span>🎬</span><span>영상</span>
    </div>
    <div class="s-item l2" data-view="kdrama-illust" onclick="navKdramaTab(this,'illust')" style="--c:#9d4edd;">
      <span>🎨</span><span>일러스트</span>
    </div>
  </div>

  <!-- 영상 작업 -->
  <div class="s-group tog" onclick="toggleSGroup('work')">
    <span>🎬 영상 작업</span><span id="sb-render-badge" style="font-size:.6rem;margin-left:6px;"></span><span class="s-arr" id="s-arr-work">▾</span>
  </div>
  <div class="s-ch open" id="s-ch-work">
    <div class="s-item l2" data-view="work" onclick="nav(this,'work')" style="--c:#3b82f6;">
      <span>📋</span><span>작업 센터</span>
    </div>
    <div class="s-item l2" data-view="render-history" onclick="navRenderTab(this,'history')" style="--c:#6366f1;">
      <span>📅</span><span>날짜별 이력</span>
    </div>
  </div>

  <!-- YouTube -->
  <div class="s-group tog" onclick="toggleSGroup('yt')">
    <span>▶ YouTube</span><span class="s-arr" id="s-arr-yt">▾</span>
  </div>
  <div class="s-ch open" id="s-ch-yt">
    <div class="s-item l2" data-view="youtube" onclick="nav(this,'youtube')" style="--c:#f87171;">
      <span>📊</span><span>채널 통계</span>
    </div>
    <div class="s-item l2" data-view="yt-upload" onclick="nav(this,'yt-upload')" style="--c:#f87171;">
      <span>📤</span><span>업로드 현황</span>
    </div>
  </div>

  <!-- Instagram -->
  <div class="s-group tog" onclick="toggleSGroup('ig')">
    <span>📸 Instagram</span><span class="s-arr" id="s-arr-ig">▾</span>
  </div>
  <div class="s-ch open" id="s-ch-ig">
    <div class="s-item l2" data-view="instagram" onclick="nav(this,'instagram')" style="--c:#e1306c;">
      <span>🎬</span><span>릴스</span>
    </div>
  </div>
</div>

<!-- ── MAIN ── -->
<div id="main">

<!-- ══ 대시보드 (개요) ═══════════════════════════════════ -->
<div id="view-overview" class="view" style="display:block;">
  <div class="g4" style="margin-bottom:14px;">
    <div class="card-sm kpi"><div id="ov-total" class="num" style="color:var(--muted);">–</div><div class="label">전체 단어</div></div>
    <div class="card-sm kpi">
      <div id="ov-gen" class="num" style="color:var(--accent);">–</div><div class="label">영상 생성</div>
      <div class="pbar-bg" style="height:3px;margin-top:6px;"><div id="ov-gen-bar" class="pbar" style="height:3px;background:var(--accent);width:0%;"></div></div>
    </div>
    <div class="card-sm kpi">
      <div id="ov-upl" class="num" style="color:var(--green);">–</div><div class="label">업로드 완료</div>
      <div class="pbar-bg" style="height:3px;margin-top:6px;"><div id="ov-upl-bar" class="pbar" style="height:3px;background:var(--green);width:0%;"></div></div>
    </div>
    <div class="card-sm kpi"><div id="ov-remain" class="num" style="color:var(--amber);">–</div><div class="label">남은 영상</div></div>
  </div>
  <div class="g2" style="margin-bottom:14px;">
    <!-- 파이프라인 -->
    <div class="card">
      <div class="sec">파이프라인 현황</div>
      <div style="display:flex;justify-content:space-between;font-size:.72rem;color:var(--muted);margin-bottom:3px;"><span>🎬 렌더링</span><span id="ov-pipe-render">0 / 0</span></div>
      <div class="pbar-bg" style="height:4px;margin-bottom:10px;"><div id="ov-pipe-render-bar" class="pbar" style="height:4px;background:var(--accent);width:0%;"></div></div>
      <div style="display:flex;justify-content:space-between;font-size:.72rem;color:var(--muted);margin-bottom:3px;"><span>⬆ 업로드</span><span id="ov-pipe-upload">0 / 0</span></div>
      <div class="pbar-bg" style="height:4px;margin-bottom:10px;"><div id="ov-pipe-upload-bar" class="pbar" style="height:4px;background:var(--green);width:0%;"></div></div>
      <div style="display:flex;justify-content:space-between;font-size:.72rem;color:var(--muted);margin-bottom:3px;"><span>🖼 일러스트 (단어)</span><span id="ov-illust-word-txt">–</span></div>
      <div class="pbar-bg" style="height:4px;margin-bottom:10px;"><div id="ov-illust-word-bar" class="pbar" style="height:4px;background:var(--amber);width:0%;"></div></div>
      <div style="display:flex;justify-content:space-between;font-size:.72rem;color:var(--muted);margin-bottom:3px;"><span>📝 일러스트 (예문)</span><span id="ov-illust-sent-txt">–</span></div>
      <div class="pbar-bg" style="height:4px;"><div id="ov-illust-sent-bar" class="pbar" style="height:4px;background:#a855f7;width:0%;"></div></div>
      <!-- 일일 사용량 -->
      <div id="ov-illust-usage" style="margin-top:12px;background:var(--bg3);border-radius:7px;padding:8px 10px;border:1px solid var(--border2);">
        <div style="display:flex;align-items:center;justify-content:space-between;">
          <span style="font-size:.72rem;color:var(--muted);">오늘 Gemini API</span>
          <span id="ov-illust-usage-txt" style="font-size:.72rem;font-weight:700;">–</span>
        </div>
        <div id="ov-illust-usage-detail" style="font-size:.65rem;color:var(--muted);margin-top:2px;"></div>
        <div id="ov-illust-exhausted" style="display:none;margin-top:6px;padding:5px 8px;border-radius:5px;background:#dc262622;border:1px solid #dc262644;font-size:.7rem;color:#f87171;font-weight:600;text-align:center;"></div>
      </div>
      <!-- 일러스트 생성 진행 (숨김) -->
      <div id="ov-illust-gen-progress" style="display:none;margin-top:12px;background:var(--bg3);border-radius:7px;padding:8px 10px;border:1px solid var(--border2);">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span id="ov-illust-gen-label" style="font-size:.7rem;font-weight:600;color:var(--amber);">생성 중...</span><span id="ov-illust-gen-pct" style="font-size:.7rem;font-weight:700;color:var(--amber);">0%</span></div>
        <div class="pbar-bg" style="height:6px;"><div id="ov-illust-gen-bar" class="pbar" style="height:6px;width:0%;background:var(--amber);"></div></div>
        <div id="ov-illust-gen-step" style="font-size:.62rem;color:var(--muted);margin-top:3px;"></div>
      </div>
    </div>
    <!-- 타임라인 -->
    <div class="card">
      <div class="sec">업로드 타임라인 (30일)</div>
      <canvas id="chart-timeline" height="140"></canvas>
    </div>
  </div>
  <div class="g2">
    <!-- 콘텐츠 카테고리 -->
    <div class="card">
      <div class="sec">콘텐츠</div>
      <div style="display:flex;flex-direction:column;gap:8px;">
        <div onclick="toggleExam(document.querySelector('[data-view=exam\\:TOPIK]'),'exam:TOPIK')" style="cursor:pointer;background:var(--bg3);border-radius:7px;padding:10px 12px;border-left:3px solid var(--accent);display:flex;align-items:center;justify-content:space-between;">
          <div style="display:flex;align-items:center;gap:7px;"><span>🇰🇷</span><span style="font-weight:600;font-size:.85rem;">TOPIK</span></div>
          <span style="font-size:.7rem;color:var(--muted);">EN · CN · JP · VN · ES</span>
        </div>
        <div style="background:var(--bg3);border-radius:7px;padding:10px 12px;border-left:3px solid var(--border2);opacity:.4;">
          <div style="display:flex;align-items:center;gap:7px;"><span>✈️</span><span style="font-weight:600;font-size:.85rem;">여행용</span><span class="badge badge-m" style="margin-left:8px;">준비 중</span></div>
        </div>
      </div>
    </div>
    <!-- 배경 음악 -->
    <div class="card">
      <div class="sec">배경 음악</div>
      <div id="ov-music" style="display:flex;flex-wrap:wrap;gap:5px;"></div>
    </div>
  </div>
  <!-- 히든 엘리먼트 (일러스트 등급별 — 개요에서는 숨김, 일러스트 뷰에서 사용) -->
  <div id="ov-illust-summary" style="display:none;"></div>
  <div id="ov-illust-levels" style="display:none;"></div>
  <div id="ov-illust-badge" style="display:none;"></div>
  <div id="ov-illust-word-pct" style="display:none;"></div>
  <div id="ov-illust-sent-pct" style="display:none;"></div>
  <div id="ov-illust-log" style="display:none;"></div>
  <input id="illust-start" type="hidden" value="1"><input id="illust-end" type="hidden" value="10">
  <select id="illust-mode" style="display:none;"><option value="both">both</option></select>
  <span id="illust-cost" style="display:none;"></span>
</div>

<!-- ══ TOPIK 언어 카드 ══════════════════════════════════ -->
<div id="view-exam:TOPIK" class="view">
  <div class="bc">
    <span onclick="nav(document.querySelector('[data-view=overview]'),'overview')">대시보드</span><span style="color:var(--muted2);">›</span><span class="cur">TOPIK</span>
  </div>
  <div class="sec" style="color:var(--accent);">학습 언어별 현황</div>
  <div id="topik-lang-cards" class="g3"></div>
</div>

<!-- ══ 언어 상세 뷰 (EN 기본 + 나머지 JS 동적) ════════ -->
<div id="view-lang:TOPIK:EN" class="view"></div>

<!-- ══ 영상 작업 센터 (새 통합 페이지) ════════════════════ -->
<div id="view-work" class="view">
  <div class="bc"><span class="cur">🎬 영상 작업 센터</span></div>
  <!-- 탭 버튼 -->
  <div style="display:flex;gap:4px;margin-bottom:14px;border-bottom:1px solid var(--border);padding-bottom:10px;">
    <button id="wt-tab-today" class="btn btn-g on" onclick="workTab('today')" style="font-size:.74rem;">📋 오늘 작업</button>
    <button id="wt-tab-custom" class="btn btn-m" onclick="workTab('custom')" style="font-size:.74rem;">⚙️ 커스텀</button>
    <button id="wt-tab-queue" class="btn btn-m" onclick="workTab('queue')" style="font-size:.74rem;">⏳ 큐</button>
  </div>

  <!-- ═══ [오늘 작업] 탭 ════════════════════════════════ -->
  <div id="wt-panel-today">

    <!-- ── 언어별 업로드 타임 & 카운트다운 ─────────────── -->
    <div class="card" style="padding:12px 14px;margin-bottom:14px;">
      <div style="font-size:.74rem;font-weight:700;margin-bottom:10px;display:flex;align-items:center;gap:6px;">
        <span>⏰</span><span>언어별 업로드 타임</span>
        <span id="cd-upload-date" style="font-size:.62rem;color:var(--amber);font-weight:600;margin-left:4px;"></span>
        <span style="font-size:.62rem;color:var(--muted);font-weight:400;">현지 07:30 기준</span>
        <button onclick="loadCountdown()" style="margin-left:auto;background:transparent;border:1px solid var(--border2);color:var(--muted);border-radius:5px;padding:2px 8px;font-size:.62rem;cursor:pointer;">새로고침</button>
      </div>
      <div id="countdown-grid" style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;">
        <!-- JS로 채워짐 -->
        <div style="grid-column:1/-1;text-align:center;font-size:.7rem;color:var(--muted2);padding:10px;">로딩 중…</div>
      </div>
    </div>

    <!-- 4개 콘텐츠 상태 카드 (2×2 그리드) -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px;">

      <!-- 단어 본편 카드 -->
      <div class="card" style="padding:12px 14px;">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
          <span style="font-size:.9rem;">📹</span>
          <span style="font-weight:700;font-size:.82rem;">단어 본편</span>
        </div>
        <div id="wc-word-yt-langs" style="display:flex;flex-direction:column;gap:3px;margin-bottom:10px;font-size:.7rem;"></div>
        <div style="display:flex;gap:5px;">
          <button onclick="renderBatchAll()" class="btn btn-g" style="flex:1;justify-content:center;font-size:.68rem;padding:4px 6px;">▶ 렌더링</button>
          <button onclick="dailyUploadAll()" class="btn btn-m" style="flex:1;justify-content:center;font-size:.68rem;padding:4px 6px;">⬆ 업로드</button>
        </div>
      </div>

      <!-- 단어 쇼츠 카드 -->
      <div class="card" style="padding:12px 14px;">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
          <span style="font-size:.9rem;">📱</span>
          <span style="font-weight:700;font-size:.82rem;">단어 쇼츠</span>
        </div>
        <div id="wc-word-reels-langs" style="display:flex;flex-direction:column;gap:3px;margin-bottom:10px;font-size:.7rem;"></div>
        <div style="display:flex;gap:5px;">
          <button onclick="renderBatchAll()" class="btn btn-g" style="flex:1;justify-content:center;font-size:.68rem;padding:4px 6px;">▶ 렌더링</button>
          <button onclick="dailyUploadAll()" class="btn btn-m" style="flex:1;justify-content:center;font-size:.68rem;padding:4px 6px;">⬆ 업로드</button>
        </div>
      </div>

      <!-- 회화 본편 카드 -->
      <div class="card" style="padding:12px 14px;">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
          <span style="font-size:.9rem;">💬</span>
          <span style="font-weight:700;font-size:.82rem;">회화 본편</span>
        </div>
        <div id="wc-conv-yt-langs" style="display:flex;flex-direction:column;gap:3px;margin-bottom:10px;font-size:.7rem;"></div>
        <div style="display:flex;gap:5px;">
          <button onclick="renderConvOnly()" class="btn btn-g" style="flex:1;justify-content:center;font-size:.68rem;padding:4px 6px;">▶ 렌더링</button>
          <button onclick="uploadPhraseToday()" class="btn btn-m" style="flex:1;justify-content:center;font-size:.68rem;padding:4px 6px;">⬆ 업로드</button>
        </div>
      </div>

      <!-- 회화 쇼츠 카드 -->
      <div class="card" style="padding:12px 14px;">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
          <span style="font-size:.9rem;">📱</span>
          <span style="font-weight:700;font-size:.82rem;">회화 쇼츠</span>
        </div>
        <div id="wc-conv-reels-langs" style="display:flex;flex-direction:column;gap:3px;margin-bottom:10px;font-size:.7rem;"></div>
        <div style="display:flex;gap:5px;">
          <button onclick="renderConvOnly()" class="btn btn-g" style="flex:1;justify-content:center;font-size:.68rem;padding:4px 6px;">▶ 렌더링</button>
          <button onclick="uploadPhraseToday()" class="btn btn-m" style="flex:1;justify-content:center;font-size:.68rem;padding:4px 6px;">⬆ 업로드</button>
        </div>
      </div>

    </div>

    <!-- 통합 실행 버튼 -->
    <div style="display:flex;gap:7px;margin-bottom:14px;">
      <button onclick="renderBatchBoth()" class="btn btn-g" style="flex:1;justify-content:center;font-size:.75rem;">▶ 단어+회화+K드라마 렌더링 (YT+릴스)</button>
      <button onclick="dailyTrigger()" class="btn btn-m" style="font-size:.75rem;padding:0 14px;">▶ 오늘</button>
    </div>

    <!-- 자동화 설정 통합 섹션 -->
    <div class="card" style="padding:14px 16px;">
      <div style="font-size:.78rem;font-weight:700;margin-bottom:12px;display:flex;align-items:center;gap:6px;">
        <span>⚙️</span><span>자동화 설정</span>
      </div>

      <!-- 자동 배치 스케줄 -->
      <div style="background:var(--bg2);border:1px solid var(--border);border-radius:9px;padding:12px 14px;margin-bottom:10px;">
        <div style="font-size:.72rem;font-weight:700;margin-bottom:8px;display:flex;align-items:center;gap:6px;">
          <span>📅</span><span>자동 배치 스케줄</span>
          <span id="wc-schedule-status" style="margin-left:auto;font-size:.65rem;color:var(--muted2);"></span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px;">
          <span style="font-size:.68rem;color:var(--muted);">기준일:</span>
          <input type="date" id="wc-start-date" class="inp"
            style="font-size:.72rem;padding:3px 8px;width:130px;"
            onchange="saveBatchConfig({auto_start_date:this.value});_updateScheduleStatus()">
          <span style="font-size:.65rem;color:var(--muted2);">이 날짜부터 자동으로 렌더링·업로드 시작</span>
        </div>

        <!-- 기준 화수 설정 -->
        <div style="background:var(--bg3);border:1px solid var(--border);border-radius:7px;padding:10px 12px;margin-bottom:10px;">
          <div style="font-size:.68rem;font-weight:700;margin-bottom:8px;color:var(--text);">📌 기준일의 시작 화수</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:7px;">
            <!-- 단어 본편 -->
            <div style="display:flex;align-items:center;gap:6px;">
              <span style="font-size:.65rem;color:var(--muted);white-space:nowrap;">📹 단어 본편</span>
              <input type="number" id="wc-ep-word-yt" min="1" value="1" class="inp"
                style="width:58px;font-size:.72rem;padding:2px 6px;"
                onchange="saveEpStart()">
              <span style="font-size:.62rem;color:var(--muted);">화</span>
              <span id="wc-ep-word-yt-today" style="font-size:.65rem;color:var(--blue);font-weight:700;margin-left:2px;"></span>
            </div>
            <!-- 단어 쇼츠 -->
            <div style="display:flex;align-items:center;gap:6px;">
              <span style="font-size:.65rem;color:var(--muted);white-space:nowrap;">📱 단어 쇼츠</span>
              <input type="number" id="wc-ep-word-reels" min="1" value="1" class="inp"
                style="width:58px;font-size:.72rem;padding:2px 6px;"
                onchange="saveEpStart()">
              <span style="font-size:.62rem;color:var(--muted);">화</span>
              <span id="wc-ep-word-reels-today" style="font-size:.65rem;color:var(--blue);font-weight:700;margin-left:2px;"></span>
            </div>
            <!-- 회화 본편 -->
            <div style="display:flex;align-items:center;gap:6px;">
              <span style="font-size:.65rem;color:var(--muted);white-space:nowrap;">💬 회화 본편</span>
              <input type="number" id="wc-ep-conv-yt" min="1" value="1" class="inp"
                style="width:58px;font-size:.72rem;padding:2px 6px;"
                onchange="saveEpStart()">
              <span style="font-size:.62rem;color:var(--muted);">화</span>
              <span id="wc-ep-conv-yt-today" style="font-size:.65rem;color:var(--green);font-weight:700;margin-left:2px;"></span>
            </div>
            <!-- 회화 쇼츠 -->
            <div style="display:flex;align-items:center;gap:6px;">
              <span style="font-size:.65rem;color:var(--muted);white-space:nowrap;">📱 회화 쇼츠</span>
              <input type="number" id="wc-ep-conv-reels" min="1" value="1" class="inp"
                style="width:58px;font-size:.72rem;padding:2px 6px;"
                onchange="saveEpStart()">
              <span style="font-size:.62rem;color:var(--muted);">화</span>
              <span id="wc-ep-conv-reels-today" style="font-size:.65rem;color:var(--green);font-weight:700;margin-left:2px;"></span>
            </div>
          </div>
        </div>

        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px;">
          <span style="font-size:.68rem;color:var(--muted);">단어 주기:</span>
          <div class="pill-group" id="wc-word-freq-group">
            <button class="pill" data-v="daily"      onclick="setBatchPill('wc-word-freq-group',this,'word_freq')">매일</button>
            <button class="pill" data-v="every2days" onclick="setBatchPill('wc-word-freq-group',this,'word_freq')">이틀에 1개</button>
            <button class="pill" data-v="every3days" onclick="setBatchPill('wc-word-freq-group',this,'word_freq')">삼일에 1개</button>
            <button class="pill" data-v="2perday"    onclick="setBatchPill('wc-word-freq-group',this,'word_freq')">하루 2개</button>
            <button class="pill" data-v="3perday"    onclick="setBatchPill('wc-word-freq-group',this,'word_freq')">하루 3개</button>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
          <span style="font-size:.68rem;color:var(--muted);">회화 주기:</span>
          <div class="pill-group" id="wc-phrase-freq-group">
            <button class="pill" data-v="daily"      onclick="setBatchPill('wc-phrase-freq-group',this,'phrase_freq')">매일</button>
            <button class="pill" data-v="every2days" onclick="setBatchPill('wc-phrase-freq-group',this,'phrase_freq')">이틀에 1개</button>
            <button class="pill" data-v="every3days" onclick="setBatchPill('wc-phrase-freq-group',this,'phrase_freq')">삼일에 1개</button>
          </div>
        </div>
        <div style="margin-top:8px;font-size:.64rem;color:var(--muted);line-height:1.5;" id="wc-schedule-desc">
          기준일을 설정하면 단어·회화 각각의 빈도 설정에 따라 자동 스케줄이 계산됩니다.
        </div>
      </div>

      <!-- 자동 실행 ON/OFF 토글 -->
      <div class="batch-auto-row" style="margin-bottom:10px;">
        <div>
          <div class="batch-auto-title">자동 실행 ON/OFF</div>
          <div class="batch-auto-sub" id="wc-auto-desc">설정 로딩 중…</div>
        </div>
        <label style="position:relative;display:inline-block;width:52px;height:28px;cursor:pointer;flex-shrink:0;">
          <input type="checkbox" id="wc-auto-toggle" onchange="setDailyAuto(this.checked)" style="opacity:0;width:0;height:0;">
          <span id="wc-toggle-slider" style="position:absolute;inset:0;background:#444;border-radius:28px;transition:.3s;">
            <span id="wc-toggle-knob" style="position:absolute;left:3px;top:3px;width:22px;height:22px;background:#fff;border-radius:50%;transition:.3s;"></span>
          </span>
        </label>
      </div>

      <!-- 업로드 스케줄 (4개 독립 설정) -->
      <div style="border-top:1px solid var(--border);padding-top:10px;margin-top:4px;">
        <div style="font-size:.72rem;font-weight:700;margin-bottom:10px;">⏱ 업로드 스케줄</div>
        <div style="display:flex;flex-direction:column;gap:8px;" id="sched-rows-wrap">
          <!-- 공통 헬퍼: sched-{type}-* -->
          <!-- 단어 본편 -->
          <div class="sched-row" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:7px 10px;background:var(--bg3);border-radius:7px;border:1px solid var(--border);">
            <span style="font-size:.7rem;min-width:72px;">📹 단어 본편</span>
            <div id="sched-word-yt-tog" onclick="schedToggle('word-yt')" style="width:38px;height:20px;border-radius:10px;background:#333;position:relative;cursor:pointer;transition:background .2s;flex-shrink:0;">
              <div id="sched-word-yt-knob" style="width:16px;height:16px;border-radius:50%;background:#fff;position:absolute;top:2px;left:2px;transition:left .2s;"></div>
            </div>
            <span id="sched-word-yt-lbl" style="font-size:.65rem;color:var(--muted);width:22px;">OFF</span>
            <select id="sched-word-yt-interval" class="inp" style="width:78px;font-size:.7rem;"><option value="1">매일</option><option value="2">격일</option><option value="3">3일마다</option></select>
            <span style="font-size:.65rem;color:var(--muted);">회당</span>
            <input id="sched-word-yt-count" type="number" min="1" max="20" value="2" class="inp" style="width:50px;font-size:.7rem;">
            <span style="font-size:.65rem;color:var(--muted);">개</span>
            <select id="sched-word-yt-lang" class="inp" style="width:80px;font-size:.7rem;"><option value="">전체</option><option value="EN">🇺🇸 EN</option><option value="JP">🇯🇵 JP</option><option value="CN">🇨🇳 CN</option><option value="VN">🇻🇳 VN</option><option value="ES">🇪🇸 ES</option></select>
            <button onclick="saveSchedType('word-yt')" class="btn btn-m" style="font-size:.66rem;padding:3px 8px;">저장</button>
            <button id="sched-word-yt-run" onclick="runSchedType('word-yt',this)" class="btn btn-g" style="font-size:.66rem;padding:3px 8px;">▶ 실행</button>
            <span id="sched-word-yt-last" style="font-size:.6rem;color:var(--muted2);margin-left:auto;"></span>
          </div>
          <!-- 단어 쇼츠 -->
          <div class="sched-row" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:7px 10px;background:var(--bg3);border-radius:7px;border:1px solid var(--border);">
            <span style="font-size:.7rem;min-width:72px;">📱 단어 쇼츠</span>
            <div id="sched-word-reels-tog" onclick="schedToggle('word-reels')" style="width:38px;height:20px;border-radius:10px;background:#333;position:relative;cursor:pointer;transition:background .2s;flex-shrink:0;">
              <div id="sched-word-reels-knob" style="width:16px;height:16px;border-radius:50%;background:#fff;position:absolute;top:2px;left:2px;transition:left .2s;"></div>
            </div>
            <span id="sched-word-reels-lbl" style="font-size:.65rem;color:var(--muted);width:22px;">OFF</span>
            <select id="sched-word-reels-interval" class="inp" style="width:78px;font-size:.7rem;"><option value="1">매일</option><option value="2">격일</option><option value="3">3일마다</option></select>
            <span style="font-size:.65rem;color:var(--muted);">회당</span>
            <input id="sched-word-reels-count" type="number" min="1" max="20" value="2" class="inp" style="width:50px;font-size:.7rem;">
            <span style="font-size:.65rem;color:var(--muted);">개</span>
            <select id="sched-word-reels-lang" class="inp" style="width:80px;font-size:.7rem;"><option value="">전체</option><option value="EN">🇺🇸 EN</option><option value="JP">🇯🇵 JP</option><option value="CN">🇨🇳 CN</option><option value="VN">🇻🇳 VN</option><option value="ES">🇪🇸 ES</option></select>
            <button onclick="saveSchedType('word-reels')" class="btn btn-m" style="font-size:.66rem;padding:3px 8px;">저장</button>
            <button id="sched-word-reels-run" onclick="runSchedType('word-reels',this)" class="btn btn-g" style="font-size:.66rem;padding:3px 8px;">▶ 실행</button>
            <span id="sched-word-reels-last" style="font-size:.6rem;color:var(--muted2);margin-left:auto;"></span>
          </div>
          <!-- 회화 본편 -->
          <div class="sched-row" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:7px 10px;background:var(--bg3);border-radius:7px;border:1px solid var(--border);">
            <span style="font-size:.7rem;min-width:72px;">💬 회화 본편</span>
            <div id="sched-conv-yt-tog" onclick="schedToggle('conv-yt')" style="width:38px;height:20px;border-radius:10px;background:#333;position:relative;cursor:pointer;transition:background .2s;flex-shrink:0;">
              <div id="sched-conv-yt-knob" style="width:16px;height:16px;border-radius:50%;background:#fff;position:absolute;top:2px;left:2px;transition:left .2s;"></div>
            </div>
            <span id="sched-conv-yt-lbl" style="font-size:.65rem;color:var(--muted);width:22px;">OFF</span>
            <select id="sched-conv-yt-interval" class="inp" style="width:78px;font-size:.7rem;"><option value="1">매일</option><option value="2">격일</option><option value="3">3일마다</option></select>
            <span style="font-size:.65rem;color:var(--muted);">회당</span>
            <input id="sched-conv-yt-count" type="number" min="1" max="20" value="1" class="inp" style="width:50px;font-size:.7rem;">
            <span style="font-size:.65rem;color:var(--muted);">개</span>
            <select id="sched-conv-yt-lang" class="inp" style="width:80px;font-size:.7rem;"><option value="">전체</option><option value="EN">🇺🇸 EN</option><option value="JP">🇯🇵 JP</option><option value="CN">🇨🇳 CN</option><option value="VN">🇻🇳 VN</option><option value="ES">🇪🇸 ES</option></select>
            <button onclick="saveSchedType('conv-yt')" class="btn btn-m" style="font-size:.66rem;padding:3px 8px;">저장</button>
            <button id="sched-conv-yt-run" onclick="runSchedType('conv-yt',this)" class="btn btn-g" style="font-size:.66rem;padding:3px 8px;">▶ 실행</button>
            <span id="sched-conv-yt-last" style="font-size:.6rem;color:var(--muted2);margin-left:auto;"></span>
          </div>
          <!-- 회화 쇼츠 -->
          <div class="sched-row" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:7px 10px;background:var(--bg3);border-radius:7px;border:1px solid var(--border);">
            <span style="font-size:.7rem;min-width:72px;">📱 회화 쇼츠</span>
            <div id="sched-conv-reels-tog" onclick="schedToggle('conv-reels')" style="width:38px;height:20px;border-radius:10px;background:#333;position:relative;cursor:pointer;transition:background .2s;flex-shrink:0;">
              <div id="sched-conv-reels-knob" style="width:16px;height:16px;border-radius:50%;background:#fff;position:absolute;top:2px;left:2px;transition:left .2s;"></div>
            </div>
            <span id="sched-conv-reels-lbl" style="font-size:.65rem;color:var(--muted);width:22px;">OFF</span>
            <select id="sched-conv-reels-interval" class="inp" style="width:78px;font-size:.7rem;"><option value="1">매일</option><option value="2">격일</option><option value="3">3일마다</option></select>
            <span style="font-size:.65rem;color:var(--muted);">회당</span>
            <input id="sched-conv-reels-count" type="number" min="1" max="20" value="1" class="inp" style="width:50px;font-size:.7rem;">
            <span style="font-size:.65rem;color:var(--muted);">개</span>
            <select id="sched-conv-reels-lang" class="inp" style="width:80px;font-size:.7rem;"><option value="">전체</option><option value="EN">🇺🇸 EN</option><option value="JP">🇯🇵 JP</option><option value="CN">🇨🇳 CN</option><option value="VN">🇻🇳 VN</option><option value="ES">🇪🇸 ES</option></select>
            <button onclick="saveSchedType('conv-reels')" class="btn btn-m" style="font-size:.66rem;padding:3px 8px;">저장</button>
            <button id="sched-conv-reels-run" onclick="runSchedType('conv-reels',this)" class="btn btn-g" style="font-size:.66rem;padding:3px 8px;">▶ 실행</button>
            <span id="sched-conv-reels-last" style="font-size:.6rem;color:var(--muted2);margin-left:auto;"></span>
          </div>
          <!-- K-드라마 본편 -->
          <div class="sched-row" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:7px 10px;background:var(--bg3);border-radius:7px;border:1px solid var(--border);">
            <span style="font-size:.7rem;min-width:72px;color:#C77DFF;">🎬 K드라마 본편</span>
            <div id="sched-kdrama-yt-tog" onclick="schedToggle('kdrama-yt')" style="width:38px;height:20px;border-radius:10px;background:#333;position:relative;cursor:pointer;transition:background .2s;flex-shrink:0;">
              <div id="sched-kdrama-yt-knob" style="width:16px;height:16px;border-radius:50%;background:#fff;position:absolute;top:2px;left:2px;transition:left .2s;"></div>
            </div>
            <span id="sched-kdrama-yt-lbl" style="font-size:.65rem;color:var(--muted);width:22px;">OFF</span>
            <select id="sched-kdrama-yt-interval" class="inp" style="width:78px;font-size:.7rem;"><option value="1">매일</option><option value="2">격일</option><option value="3">3일마다</option></select>
            <span style="font-size:.65rem;color:var(--muted);">회당</span>
            <input id="sched-kdrama-yt-count" type="number" min="1" max="20" value="1" class="inp" style="width:50px;font-size:.7rem;">
            <span style="font-size:.65rem;color:var(--muted);">개</span>
            <select id="sched-kdrama-yt-lang" class="inp" style="width:80px;font-size:.7rem;"><option value="">전체</option><option value="EN">🇺🇸 EN</option><option value="JP">🇯🇵 JP</option><option value="CN">🇨🇳 CN</option><option value="VN">🇻🇳 VN</option><option value="ES">🇪🇸 ES</option></select>
            <button onclick="saveSchedType('kdrama-yt')" class="btn btn-m" style="font-size:.66rem;padding:3px 8px;">저장</button>
            <button id="sched-kdrama-yt-run" onclick="runSchedType('kdrama-yt',this)" class="btn btn-g" style="font-size:.66rem;padding:3px 8px;">▶ 실행</button>
            <span id="sched-kdrama-yt-last" style="font-size:.6rem;color:var(--muted2);margin-left:auto;"></span>
          </div>
          <!-- K-드라마 쇼츠 -->
          <div class="sched-row" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:7px 10px;background:var(--bg3);border-radius:7px;border:1px solid var(--border);">
            <span style="font-size:.7rem;min-width:72px;color:#C77DFF;">📱 K드라마 쇼츠</span>
            <div id="sched-kdrama-reels-tog" onclick="schedToggle('kdrama-reels')" style="width:38px;height:20px;border-radius:10px;background:#333;position:relative;cursor:pointer;transition:background .2s;flex-shrink:0;">
              <div id="sched-kdrama-reels-knob" style="width:16px;height:16px;border-radius:50%;background:#fff;position:absolute;top:2px;left:2px;transition:left .2s;"></div>
            </div>
            <span id="sched-kdrama-reels-lbl" style="font-size:.65rem;color:var(--muted);width:22px;">OFF</span>
            <select id="sched-kdrama-reels-interval" class="inp" style="width:78px;font-size:.7rem;"><option value="1">매일</option><option value="2">격일</option><option value="3">3일마다</option></select>
            <span style="font-size:.65rem;color:var(--muted);">회당</span>
            <input id="sched-kdrama-reels-count" type="number" min="1" max="20" value="1" class="inp" style="width:50px;font-size:.7rem;">
            <span style="font-size:.65rem;color:var(--muted);">개</span>
            <select id="sched-kdrama-reels-lang" class="inp" style="width:80px;font-size:.7rem;"><option value="">전체</option><option value="EN">🇺🇸 EN</option><option value="JP">🇯🇵 JP</option><option value="CN">🇨🇳 CN</option><option value="VN">🇻🇳 VN</option><option value="ES">🇪🇸 ES</option></select>
            <button onclick="saveSchedType('kdrama-reels')" class="btn btn-m" style="font-size:.66rem;padding:3px 8px;">저장</button>
            <button id="sched-kdrama-reels-run" onclick="runSchedType('kdrama-reels',this)" class="btn btn-g" style="font-size:.66rem;padding:3px 8px;">▶ 실행</button>
            <span id="sched-kdrama-reels-last" style="font-size:.6rem;color:var(--muted2);margin-left:auto;"></span>
          </div>
        </div>
      </div>

      <div style="margin-top:8px;font-size:.62rem;color:var(--muted2);text-align:center;">자동 OFF 상태에서도 수동으로 실행 가능</div>
    </div>

  </div>

  <!-- ═══ [커스텀] 탭 ════════════════════════════════════ -->
  <div id="wt-panel-custom" style="display:none;">
    <div class="sec">렌더링 대상</div>
    <div style="margin-bottom:10px;">
      <div id="wc-rc-targets">
        <div class="rc-target-row" style="display:flex;gap:6px;align-items:flex-end;margin-bottom:6px;">
          <div style="flex:2.5;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">시험</div>
            <select class="rc-exam inp" onchange="onExamChange(this.closest('.rc-target-row'))" style="width:100%;"><option value="TOPIK">🇰🇷 TOPIK</option><option value="TOEIC">📝 TOEIC</option><option value="JLPT">🌸 JLPT</option><option value="IELTS">🎓 IELTS</option><option value="HSK">🐉 HSK</option><option value="회화">💬 회화</option></select></div>
          <div class="rc-level-wrap" style="flex:1.5;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">등급</div>
            <select class="rc-level inp" onchange="updateCustomPreview()" style="width:100%;"><option value="1">1급</option><option value="2">2급</option><option value="3">3급</option><option value="4">4급</option><option value="5">5급</option><option value="6">6급</option></select></div>
          <div class="rc-conv-wrap" style="flex:1.5;display:none;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">화수</div>
            <input class="rc-conv-range inp" placeholder="예: 3~10, 15" oninput="updateCustomPreview()" style="width:100%;"></div>
          <div class="rc-ids-wrap" style="flex:2;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">ID <span style="font-weight:400;opacity:.7;">(숫자·범위)</span></div>
            <input class="rc-ids inp" placeholder="예: 1, 3~10, 15" oninput="updateCustomPreview()" style="width:100%;"></div>
          <div style="flex:0 0 auto;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">포맷</div>
            <div style="display:flex;gap:2px;">
              <button class="rc-row-fmt active" data-fmt="youtube" onclick="toggleRowFmt(this)" style="padding:4px 7px;font-size:.62rem;border-radius:5px;border:1px solid var(--green);background:var(--green)22;color:var(--green);cursor:pointer;white-space:nowrap;">▶본편</button>
              <button class="rc-row-fmt active" data-fmt="reels" onclick="toggleRowFmt(this)" style="padding:4px 7px;font-size:.62rem;border-radius:5px;border:1px solid var(--amber);background:var(--amber)22;color:var(--amber);cursor:pointer;white-space:nowrap;">⚡쇼츠</button>
            </div></div>
          <div style="width:28px;flex-shrink:0;"></div>
        </div>
      </div>
      <button onclick="addTargetRow()" class="btn btn-m" style="font-size:.68rem;padding:5px 12px;margin-top:4px;">＋ 추가</button>
    </div>
    <div style="margin-bottom:12px;">
      <div style="font-size:.62rem;color:var(--muted2);margin-bottom:6px;">단어 언어 <span style="color:var(--muted2);font-weight:400;">(복수 선택 가능)</span></div>
      <div id="wc-rc-lang-btns" style="display:flex;gap:6px;flex-wrap:wrap;">
        <button class="rc-lang-btn active" data-lang="EN" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--blue);background:var(--blue)22;color:var(--blue);cursor:pointer;">🇺🇸 EN</button>
        <button class="rc-lang-btn" data-lang="JP" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;">🇯🇵 JP</button>
        <button class="rc-lang-btn" data-lang="CN" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;">🇨🇳 CN</button>
        <button class="rc-lang-btn" data-lang="VN" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;">🇻🇳 VN</button>
        <button class="rc-lang-btn" data-lang="ES" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;">🇪🇸 ES</button>
        <button class="rc-lang-btn" data-lang="KO" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;">🇰🇷 KO</button>
      </div>
    </div>
    <div style="display:flex;gap:6px;margin-bottom:6px;">
      <button id="wc-rc-target-desktop" onclick="setCustomTarget('desktop')" class="btn btn-p" style="flex:1;justify-content:center;font-size:.72rem;">💻 GPU</button>
      <button id="wc-rc-target-nas" onclick="setCustomTarget('nas')" class="btn btn-m" style="flex:1;justify-content:center;font-size:.72rem;">🖥 NAS CPU</button>
    </div>
    <div id="wc-rc-time-est" style="font-size:.64rem;color:var(--muted2);margin-bottom:12px;"></div>
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
      <span class="sec" style="margin:0;">미리보기</span>
      <span id="wc-rc-remaining" style="font-size:.62rem;color:var(--muted2);"></span>
    </div>
    <div id="wc-rc-preview" style="margin-bottom:12px;max-height:300px;overflow-y:auto;"></div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
      <label style="font-size:.72rem;color:var(--muted);display:flex;align-items:center;gap:4px;cursor:pointer;">
        <input type="checkbox" id="wc-rc-thumb-only"> 썸네일만 재생성
      </label>
    </div>
    <div style="display:flex;gap:8px;">
      <button id="wc-rc-start" onclick="startCustomRender()" class="btn btn-g" style="flex:1;justify-content:center;">▶ 렌더링 시작</button>
      <button id="wc-rc-cancel" onclick="cancelRender()" class="btn btn-d" style="display:none;padding:0 16px;">✕ 취소</button>
    </div>
  </div>

  <!-- ═══ [큐] 탭 ══════════════════════════════════════ -->
  <div id="wt-panel-queue" style="display:none;">
    <!-- 작업 큐 -->
    <div class="card" style="margin-bottom:14px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="font-size:.8rem;font-weight:700;">작업 큐</span>
          <span id="wc-gq-count-badge" style="font-size:.65rem;color:var(--muted2);background:var(--bg3);padding:1px 8px;border-radius:10px;"></span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span id="wc-ql-desktop-status" style="font-size:.65rem;color:var(--muted2);"></span>
          <button id="wc-ql-btn-desktop" onclick="setGlobalTarget('desktop')" class="btn btn-p" style="font-size:.68rem;padding:3px 10px;">💻 GPU</button>
          <button id="wc-ql-btn-nas" onclick="setGlobalTarget('nas')" class="btn btn-m" style="font-size:.68rem;padding:3px 10px;">🖥 NAS</button>
          <button onclick="cleanupQueue()" class="btn btn-m" style="font-size:.68rem;padding:3px 10px;" title="완료/실패 작업 정리">🗑 정리</button>
        </div>
      </div>
      <div id="wc-global-queue-list">
        <div style="font-size:.72rem;color:var(--muted2);text-align:center;padding:10px 0;">대기 중인 작업이 없습니다</div>
      </div>
    </div>
    <!-- 렌더링 진행 -->
    <div id="wc-live-summary" style="display:none;margin-bottom:12px;padding:12px;background:var(--bg3);border-radius:8px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <span id="wc-live-status-label" style="font-size:.8rem;font-weight:700;color:var(--green);">대기 중</span>
        <div style="display:flex;align-items:center;gap:8px;">
          <span id="wc-live-timing" style="font-size:.62rem;color:var(--muted2);"></span>
          <button id="wc-live-cancel-btn" onclick="cancelBatchRender()" style="display:none;font-size:.68rem;padding:3px 10px;border-radius:5px;border:none;background:#ef4444;color:#fff;cursor:pointer;font-weight:600;">⏹ 취소</button>
          <button onclick="clearBatchQueue()" style="font-size:.6rem;padding:2px 8px;border-radius:5px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;" title="진행 기록 지우기">✕ 지우기</button>
        </div>
      </div>
      <div style="background:rgba(255,255,255,.08);border-radius:4px;height:8px;overflow:hidden;margin-bottom:6px;">
        <div id="wc-live-pbar" style="height:100%;background:linear-gradient(90deg,#6366f1,#3fb950);border-radius:4px;width:0%;transition:width .4s;"></div>
      </div>
      <div style="display:flex;gap:16px;font-size:.66rem;color:var(--muted2);">
        <span>✅ 완료: <b id="wc-live-done" style="color:var(--green);">0</b></span>
        <span>⏳ 대기: <b id="wc-live-pending" style="color:var(--amber);">0</b></span>
        <span>⟳ 진행: <b id="wc-live-running" style="color:#58a6ff;">0</b></span>
        <span>✕ 실패: <b id="wc-live-failed" style="color:var(--red);">0</b></span>
        <span>↷ 건너뜀: <b id="wc-live-skipped" style="color:var(--muted);">0</b></span>
        <span style="margin-left:auto;">합계: <b id="wc-live-total">0</b></span>
      </div>
    </div>
    <div id="wc-live-list" style="max-height:420px;overflow-y:auto;display:flex;flex-direction:column;gap:3px;"></div>
  </div>

  <!-- ═══ [날짜별 이력] 패널 (사이드바에서 직접 접근) ══════════ -->
  <div id="wt-panel-history" style="display:none;">
    <input type="date" id="wc-date-pick" onchange="loadWcHistoryDate()" class="inp" style="width:100%;margin-bottom:12px;">
    <div id="wc-history-list"></div>
  </div>

</div>

<!-- ══ 렌더링 (통합 페이지 - 호환성 유지, 숨김) ═══════════ -->
<div id="view-render" class="view" style="display:none!important;">
  <!-- 탭 내용: 배치 (일별 자동 시스템) -->
  <div id="rp-batch">

    <!-- ═══ 단어 섹션 ═════════════════════════════════════════ -->
    <div class="batch-section">
      <!-- 헤더 -->
      <div class="batch-section-header">
        <span style="font-size:1rem;">🎬</span>
        <span class="batch-section-title">단어</span>
        <span id="daily-lv1-progress" class="batch-section-badge"></span>
      </div>
      <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:12px;">
        <span id="daily-word-ko" class="batch-word-info">—</span>
        <span id="daily-word-meaning" style="font-size:.8rem;color:var(--muted);"></span>
        <span id="daily-illust-badge" style="margin-left:auto;font-size:.65rem;"></span>
      </div>

      <hr class="batch-divider">

      <!-- 설정 -->
      <div class="batch-setting-row">
        <span class="batch-setting-label">업로드 빈도</span>
        <div class="pill-group" id="word-freq-group">
          <button class="pill" data-v="daily"      onclick="setBatchPill('word-freq-group',this,'word_freq')">매일</button>
          <button class="pill" data-v="every2days" onclick="setBatchPill('word-freq-group',this,'word_freq')">이틀에 1개</button>
          <button class="pill" data-v="every3days" onclick="setBatchPill('word-freq-group',this,'word_freq')">삼일에 1개</button>
          <button class="pill" data-v="2perday"    onclick="setBatchPill('word-freq-group',this,'word_freq')">하루 2개</button>
          <button class="pill" data-v="3perday"    onclick="setBatchPill('word-freq-group',this,'word_freq')">하루 3개</button>
        </div>
      </div>
      <div class="batch-setting-row">
        <span class="batch-setting-label">렌더링</span>
        <div class="pill-group" id="word-render-group">
          <button class="pill" data-v="auto"   onclick="setBatchPill('word-render-group',this,'word_render')">자동</button>
          <button class="pill" data-v="auto_if_missing" onclick="setBatchPill('word-render-group',this,'word_render')">없으면 자동</button>
          <button class="pill" data-v="manual"          onclick="setBatchPill('word-render-group',this,'word_render')">수동</button>
        </div>
      </div>
      <div class="batch-setting-row">
        <span class="batch-setting-label">일러스트</span>
        <div class="pill-group" id="word-illust-group">
          <button class="pill" data-v="auto"            onclick="setBatchPill('word-illust-group',this,'word_illust')">자동</button>
          <button class="pill" data-v="auto_if_missing" onclick="setBatchPill('word-illust-group',this,'word_illust')">없으면 자동</button>
          <button class="pill" data-v="manual"          onclick="setBatchPill('word-illust-group',this,'word_illust')">수동</button>
        </div>
      </div>
      <div class="batch-setting-row">
        <span class="batch-setting-label">사전 제작</span>
        <div class="batch-prebuf-row">
          <span style="font-size:.7rem;color:var(--muted);">업로드</span>
          <input id="word-prebuf-h" type="number" value="2" min="1" max="24" class="inp"
            style="width:46px;font-size:.72rem;padding:2px 5px;text-align:center;"
            onchange="saveBatchConfig({word_prebuffer_h:parseInt(this.value)||2})">
          <span style="font-size:.7rem;color:var(--muted);">시간 전 영상 미리 제작</span>
        </div>
      </div>

      <hr class="batch-divider">

      <!-- 언어별 상태 -->
      <table class="batch-lang-table" id="daily-lang-table">
        <thead><tr>
          <th>언어</th><th style="text-align:center;">본편</th>
          <th style="text-align:center;">쇼츠</th>
          <th style="text-align:center;">업로드됨</th><th>예약 시간</th><th>액션</th>
        </tr></thead>
        <tbody id="daily-lang-tbody"></tbody>
      </table>
      <div id="daily-render-status" style="display:none;padding:6px 10px;background:var(--bg);border-radius:7px;margin-bottom:8px;font-size:.7rem;color:var(--amber);font-weight:600;"></div>

      <!-- ID 변경 -->
      <div style="display:flex;gap:6px;align-items:center;margin-bottom:10px;">
        <span style="font-size:.63rem;color:var(--muted2);">ID:</span>
        <input id="daily-word-id-input" class="inp" type="number" min="1" max="300" style="width:64px;font-size:.72rem;padding:2px 6px;" placeholder="ID">
        <button onclick="dailySetWord()" class="btn btn-m" style="font-size:.68rem;padding:3px 8px;">변경</button>
      </div>

      <!-- 썸네일 스타일 선택 -->
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
        <span style="font-size:.63rem;color:var(--muted2);">썸네일:</span>
        <button id="thumb-style-portrait" onclick="setThumbStyle('portrait')" class="btn btn-g" style="font-size:.66rem;padding:2px 9px;">☰ 세로형</button>
        <button id="thumb-style-landscape" onclick="setThumbStyle('landscape')" class="btn btn-m" style="font-size:.66rem;padding:2px 9px;">⊟ 가로형</button>
      </div>
      <!-- 단어 실행 버튼 -->
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
        <label style="display:flex;align-items:center;gap:5px;font-size:.74rem;cursor:pointer;">
          <input type="checkbox" id="rp-auto-upload" style="width:14px;height:14px;">
          렌더링 후 자동 업로드
        </label>
      </div>
      <div class="batch-action-row">
        <button id="rp-render-all" onclick="renderBatchAll()" class="btn btn-g" style="flex:1;justify-content:center;font-size:.74rem;">▶ 단어 렌더링</button>
        <button id="rp-upload-all-btn" onclick="dailyUploadAll()" class="btn btn-m" style="flex:1;justify-content:center;font-size:.74rem;">⬆ 전체 업로드</button>
        <button id="rp-cancel-btn" onclick="cancelRender()" class="btn btn-d" style="display:none;font-size:.74rem;padding:0 12px;">✕ 취소</button>
      </div>
    </div>

    <!-- ═══ 회화 섹션 ═════════════════════════════════════════ -->
    <div class="batch-section">
      <!-- 헤더 -->
      <div class="batch-section-header">
        <span style="font-size:1rem;">💬</span>
        <span class="batch-section-title">회화</span>
        <span id="daily-phrase-next-badge" class="batch-section-badge"></span>
      </div>
      <div id="daily-conv-display" style="font-size:.88rem;font-weight:700;margin-bottom:12px;">—</div>

      <hr class="batch-divider">

      <!-- 설정 -->
      <div class="batch-setting-row">
        <span class="batch-setting-label">업로드 빈도</span>
        <div class="pill-group" id="phrase-freq-group">
          <button class="pill" data-v="daily"      onclick="setBatchPill('phrase-freq-group',this,'phrase_freq')">매일</button>
          <button class="pill" data-v="every2days" onclick="setBatchPill('phrase-freq-group',this,'phrase_freq')">이틀에 1개</button>
          <button class="pill" data-v="every3days" onclick="setBatchPill('phrase-freq-group',this,'phrase_freq')">삼일에 1개</button>
        </div>
      </div>
      <div class="batch-setting-row">
        <span class="batch-setting-label">렌더링</span>
        <div class="pill-group" id="phrase-render-group">
          <button class="pill" data-v="auto"            onclick="setBatchPill('phrase-render-group',this,'phrase_render')">자동</button>
          <button class="pill" data-v="auto_if_missing" onclick="setBatchPill('phrase-render-group',this,'phrase_render')">없으면 자동</button>
          <button class="pill" data-v="manual"          onclick="setBatchPill('phrase-render-group',this,'phrase_render')">수동</button>
        </div>
      </div>
      <div class="batch-setting-row">
        <span class="batch-setting-label">일러스트</span>
        <div class="pill-group" id="phrase-illust-group">
          <button class="pill" data-v="auto"            onclick="setBatchPill('phrase-illust-group',this,'phrase_illust')">자동</button>
          <button class="pill" data-v="auto_if_missing" onclick="setBatchPill('phrase-illust-group',this,'phrase_illust')">없으면 자동</button>
          <button class="pill" data-v="manual"          onclick="setBatchPill('phrase-illust-group',this,'phrase_illust')">수동</button>
        </div>
      </div>
      <div class="batch-setting-row">
        <span class="batch-setting-label">사전 제작</span>
        <div class="batch-prebuf-row">
          <span style="font-size:.7rem;color:var(--muted);">업로드</span>
          <input id="phrase-prebuf-h" type="number" value="2" min="1" max="24" class="inp"
            style="width:46px;font-size:.72rem;padding:2px 5px;text-align:center;"
            onchange="saveBatchConfig({phrase_prebuffer_h:parseInt(this.value)||2})">
          <span style="font-size:.7rem;color:var(--muted);">시간 전 영상 미리 제작</span>
        </div>
      </div>

      <hr class="batch-divider">

      <!-- 회화 언어별 상태 -->
      <table class="batch-lang-table" id="daily-conv-table">
        <thead><tr>
          <th>언어</th><th style="text-align:center;">렌더됨</th><th style="text-align:center;">업로드됨</th>
        </tr></thead>
        <tbody id="daily-conv-tbody"></tbody>
      </table>

      <!-- 상황 ID 변경 -->
      <div style="display:flex;gap:6px;align-items:center;margin-bottom:10px;">
        <span style="font-size:.63rem;color:var(--muted2);">상황 ID:</span>
        <input id="daily-conv-id-input" class="inp" type="number" min="1" style="width:60px;font-size:.72rem;padding:2px 6px;" placeholder="ID">
        <button onclick="dailySetConv()" class="btn btn-m" style="font-size:.68rem;padding:3px 8px;">변경</button>
      </div>

      <!-- 회화 실행 버튼 -->
      <div class="batch-action-row">
        <button id="rp-render-conv" onclick="renderConvOnly()" class="btn btn-g" style="flex:1;justify-content:center;font-size:.74rem;">▶ 회화 렌더링</button>
        <button onclick="uploadPhraseToday()" class="btn btn-b" style="flex:1;justify-content:center;font-size:.74rem;">⬆ 회화 업로드</button>
      </div>
    </div>

    <!-- ═══ 통합 실행 ════════════════════════════════════════ -->
    <div class="batch-footer">
      <div style="display:flex;gap:7px;margin-bottom:10px;">
        <button id="rp-render-both" onclick="renderBatchBoth()" class="btn btn-g" style="flex:1;justify-content:center;font-size:.75rem;">▶ 단어+회화+K드라마 렌더링 (YT+릴스)</button>
        <button onclick="dailyTrigger()" class="btn btn-m" style="font-size:.75rem;padding:0 14px;">▶ 오늘</button>
      </div>

      <!-- 자동 배치 기준일 -->
      <div style="background:var(--bg2);border:1px solid var(--border);border-radius:9px;padding:12px 14px;margin-bottom:8px;">
        <div style="font-size:.72rem;font-weight:700;margin-bottom:8px;display:flex;align-items:center;gap:6px;">
          <span>📅</span><span>자동 배치 스케줄</span>
          <span id="daily-schedule-status" style="margin-left:auto;font-size:.65rem;color:var(--muted2);"></span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
          <span style="font-size:.68rem;color:var(--muted);">기준일:</span>
          <input type="date" id="auto-start-date" class="inp"
            style="font-size:.72rem;padding:3px 8px;width:130px;"
            onchange="saveBatchConfig({auto_start_date:this.value});_updateScheduleStatus()">
          <span style="font-size:.65rem;color:var(--muted2);">이 날짜부터 자동으로 렌더링·업로드 시작</span>
        </div>
        <div style="margin-top:8px;font-size:.64rem;color:var(--muted);line-height:1.5;" id="daily-schedule-desc">
          기준일을 설정하면 단어·회화 각각의 빈도 설정에 따라 자동 스케줄이 계산됩니다.
        </div>
      </div>

      <!-- 매일 자동 실행 토글 -->
      <div class="batch-auto-row">
        <div>
          <div class="batch-auto-title">자동 실행 ON/OFF</div>
          <div class="batch-auto-sub" id="daily-auto-desc">설정 로딩 중…</div>
        </div>
        <label style="position:relative;display:inline-block;width:52px;height:28px;cursor:pointer;flex-shrink:0;">
          <input type="checkbox" id="daily-auto-toggle" onchange="setDailyAuto(this.checked)" style="opacity:0;width:0;height:0;">
          <span id="daily-toggle-slider" style="position:absolute;inset:0;background:#444;border-radius:28px;transition:.3s;">
            <span id="daily-toggle-knob" style="position:absolute;left:3px;top:3px;width:22px;height:22px;background:#fff;border-radius:50%;transition:.3s;"></span>
          </span>
        </label>
      </div>
      <div style="margin-top:8px;font-size:.62rem;color:var(--muted2);text-align:center;">자동 OFF 상태에서도 수동으로 실행 가능</div>
    </div>

  </div>
  <!-- 탭 내용: 커스텀 -->
  <div id="rp-custom" style="display:none;">
    <div class="sec">렌더링 대상</div>
    <div style="margin-bottom:10px;">
      <div id="rc-targets">
        <div class="rc-target-row" style="display:flex;gap:6px;align-items:flex-end;margin-bottom:6px;">
          <div style="flex:2.5;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">시험</div>
            <select class="rc-exam inp" onchange="onExamChange(this.closest('.rc-target-row'))" style="width:100%;"><option value="TOPIK">🇰🇷 TOPIK</option><option value="TOEIC">📝 TOEIC</option><option value="JLPT">🌸 JLPT</option><option value="IELTS">🎓 IELTS</option><option value="HSK">🐉 HSK</option><option value="회화">💬 회화</option></select></div>
          <div class="rc-level-wrap" style="flex:1.5;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">등급</div>
            <select class="rc-level inp" onchange="updateCustomPreview()" style="width:100%;"><option value="1">1급</option><option value="2">2급</option><option value="3">3급</option><option value="4">4급</option><option value="5">5급</option><option value="6">6급</option></select></div>
          <div class="rc-conv-wrap" style="flex:1.5;display:none;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">화수</div>
            <input class="rc-conv-range inp" placeholder="예: 3~10, 15" oninput="updateCustomPreview()" style="width:100%;"></div>
          <div class="rc-ids-wrap" style="flex:2;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">ID <span style="font-weight:400;opacity:.7;">(숫자·범위)</span></div>
            <input class="rc-ids inp" placeholder="예: 1, 3~10, 15" oninput="updateCustomPreview()" style="width:100%;"></div>
          <div style="flex:0 0 auto;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">포맷</div>
            <div style="display:flex;gap:2px;">
              <button class="rc-row-fmt active" data-fmt="youtube" onclick="toggleRowFmt(this)" style="padding:4px 7px;font-size:.62rem;border-radius:5px;border:1px solid var(--green);background:var(--green)22;color:var(--green);cursor:pointer;white-space:nowrap;">▶본편</button>
              <button class="rc-row-fmt active" data-fmt="reels" onclick="toggleRowFmt(this)" style="padding:4px 7px;font-size:.62rem;border-radius:5px;border:1px solid var(--amber);background:var(--amber)22;color:var(--amber);cursor:pointer;white-space:nowrap;">⚡쇼츠</button>
            </div></div>
          <div style="width:28px;flex-shrink:0;"></div>
        </div>
      </div>
      <button onclick="addTargetRow()" class="btn btn-m" style="font-size:.68rem;padding:5px 12px;margin-top:4px;">＋ 추가</button>
    </div>
    <div style="margin-bottom:12px;">
      <div style="font-size:.62rem;color:var(--muted2);margin-bottom:6px;">단어 언어 <span style="color:var(--muted2);font-weight:400;">(복수 선택 가능)</span></div>
      <div id="rc-lang-btns" style="display:flex;gap:6px;flex-wrap:wrap;">
        <button class="rc-lang-btn active" data-lang="EN" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--blue);background:var(--blue)22;color:var(--blue);cursor:pointer;">🇺🇸 EN</button>
        <button class="rc-lang-btn" data-lang="JP" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;">🇯🇵 JP</button>
        <button class="rc-lang-btn" data-lang="CN" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;">🇨🇳 CN</button>
        <button class="rc-lang-btn" data-lang="VN" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;">🇻🇳 VN</button>
        <button class="rc-lang-btn" data-lang="ES" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;">🇪🇸 ES</button>
        <button class="rc-lang-btn" data-lang="KO" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;">🇰🇷 KO</button>
      </div>
    </div>
    <div style="display:flex;gap:6px;margin-bottom:6px;">
      <button id="rc-target-desktop" onclick="setCustomTarget('desktop')" class="btn btn-p" style="flex:1;justify-content:center;font-size:.72rem;">💻 GPU</button>
      <button id="rc-target-nas" onclick="setCustomTarget('nas')" class="btn btn-m" style="flex:1;justify-content:center;font-size:.72rem;">🖥 NAS CPU</button>
    </div>
    <div id="rc-time-est" style="font-size:.64rem;color:var(--muted2);margin-bottom:12px;"></div>
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
      <span class="sec" style="margin:0;">미리보기</span>
      <span id="rc-remaining" style="font-size:.62rem;color:var(--muted2);"></span>
    </div>
    <div id="rc-preview" style="margin-bottom:12px;max-height:300px;overflow-y:auto;"></div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
      <label style="font-size:.72rem;color:var(--muted);display:flex;align-items:center;gap:4px;cursor:pointer;">
        <input type="checkbox" id="rc-thumb-only"> 썸네일만 재생성
      </label>
    </div>
    <div style="display:flex;gap:8px;">
      <button id="rc-start" onclick="startCustomRender()" class="btn btn-g" style="flex:1;justify-content:center;">▶ 렌더링 시작</button>
      <button id="rc-cancel" onclick="cancelRender()" class="btn btn-d" style="display:none;padding:0 16px;">✕ 취소</button>
    </div>
  </div>
  <!-- 탭 내용: 일러스트 생성 -->
  <div id="rp-illust" style="display:none;">
    <!-- 현황 요약 -->
    <div class="card" style="margin-bottom:14px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
        <span style="font-weight:700;font-size:.88rem;">일러스트 현황</span>
        <span id="illust-view-badge" class="badge badge-m"></span>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:.74rem;color:var(--muted);margin-bottom:3px;"><span>🖼 단어</span><span id="illust-view-word-txt">–</span><span id="illust-view-word-pct" style="margin-left:auto;padding-left:8px;">0%</span></div>
      <div class="pbar-bg" style="height:5px;margin-bottom:8px;"><div id="illust-view-word-bar" class="pbar" style="height:5px;width:0%;background:linear-gradient(90deg,#f59e0b,#f97316);"></div></div>
      <div style="display:flex;justify-content:space-between;font-size:.74rem;color:var(--muted);margin-bottom:3px;"><span>📝 예문</span><span id="illust-view-sent-txt">–</span><span id="illust-view-sent-pct" style="margin-left:auto;padding-left:8px;">0%</span></div>
      <div class="pbar-bg" style="height:5px;margin-bottom:12px;"><div id="illust-view-sent-bar" class="pbar" style="height:5px;width:0%;background:linear-gradient(90deg,#818cf8,#a855f7);"></div></div>
      <div id="illust-view-summary" style="margin-bottom:8px;padding:8px 12px;background:var(--bg);border-radius:7px;border:1px solid var(--border2);font-size:.72rem;"></div>
      <div class="g6" id="illust-view-levels" style="margin-bottom:8px;"></div>
      <div id="illust-view-usage" style="background:var(--bg);border-radius:8px;padding:10px 14px;border:1px solid var(--border2);">
        <div style="display:flex;align-items:center;justify-content:space-between;">
          <span style="font-size:.76rem;font-weight:600;">오늘 Gemini API 사용량</span>
          <span id="illust-view-usage-txt" style="font-size:.82rem;font-weight:700;">–</span>
        </div>
        <div id="illust-view-usage-detail" style="font-size:.7rem;color:var(--muted);"></div>
        <div id="illust-view-exhausted" style="display:none;margin-top:6px;padding:5px 10px;border-radius:6px;background:#dc262622;border:1px solid #dc262644;font-size:.74rem;color:#f87171;font-weight:600;text-align:center;"></div>
      </div>
    </div>
    <!-- 배치 생성 -->
    <div class="card" style="margin-bottom:14px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
        <div class="sec" style="margin:0;">배치 생성</div>
        <div style="display:flex;gap:4px;">
          <button id="illust-target-nas" class="btn btn-p active" style="font-size:.72rem;padding:3px 10px;" onclick="setIllustTarget('nas')">🖥 NAS</button>
          <button id="illust-target-desktop" class="btn btn-m" style="font-size:.72rem;padding:3px 10px;" onclick="setIllustTarget('desktop')">💻 GPU</button>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
        <span style="font-size:.74rem;color:var(--muted);">ID 범위:</span>
        <input id="illust-start2" class="num-input" type="number" value="1"><span style="color:var(--muted);">~</span>
        <input id="illust-end2" class="num-input" type="number" value="100">
        <select id="illust-mode2" onchange="updateIllustCost2()" class="inp"><option value="both">단어+예문</option><option value="words">🖼 단어만</option><option value="sentences">📝 예문만</option></select>
        <button id="illust-gen-btn2" onclick="startIllustGen2()" class="btn btn-a">🎨 생성 시작</button>
        <button id="illust-cancel-btn2" onclick="cancelIllustGen()" class="btn btn-r" style="display:none;">⏹ 취소</button>
        <button id="illust-reset-btn2" onclick="resetIllustProgress()" class="btn btn-m" style="display:none;">🔄 초기화</button>
        <button onclick="setIllustRange2(1,1800)" class="btn btn-m">전체</button>
        <span id="illust-cost2" style="font-size:.72rem;color:var(--amber);font-weight:600;"></span>
      </div>
      <div id="illust-view-log" style="display:none;margin-top:10px;background:var(--bg);border-radius:6px;padding:10px;font-size:.7rem;color:var(--muted);font-family:monospace;max-height:100px;overflow:auto;white-space:pre-wrap;"></div>
    </div>
    <!-- 미리보기 / 재생성 -->
    <div class="card" style="margin-bottom:14px;">
      <div class="sec">미리보기 / 재생성</div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;flex-wrap:wrap;">
        <span style="font-size:.74rem;color:var(--muted);">등급:</span>
        <select id="illust-browse-level" class="inp" style="width:60px;" onchange="onIllustLevelChange()">
          <option value="1">1급</option><option value="2">2급</option><option value="3">3급</option>
          <option value="4">4급</option><option value="5">5급</option><option value="6">6급</option>
        </select>
        <span style="font-size:.74rem;color:var(--muted);">단어 ID:</span>
        <input id="illust-browse-id" class="num-input" type="number" value="1" min="1" max="300" style="width:70px;">
        <button onclick="loadIllustBrowse()" class="btn btn-a">조회</button>
        <button onclick="illustBrowseNav(-1)" class="btn btn-m">&lt;</button>
        <button onclick="illustBrowseNav(1)" class="btn btn-m">&gt;</button>
        <span id="illust-browse-id-range" style="font-size:.62rem;color:var(--muted2);"></span>
        <span id="illust-browse-info" style="font-size:.78rem;font-weight:600;"></span>
      </div>
      <div id="illust-browse-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;"></div>
      <div id="illust-regen-status" style="display:none;margin-top:10px;padding:8px 12px;border-radius:6px;background:var(--bg);font-size:.74rem;color:var(--amber);font-weight:600;"></div>
    </div>
    <!-- 스타일 감사 -->
    <div class="card">
      <div class="sec">🔍 스타일 감사 (VLM)</div>
      <div style="font-size:.72rem;color:var(--muted);margin-bottom:10px;">Gemini Vision으로 텍스트 침투 / 비율 / 스타일 일관성 검사</div>
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:10px;">
        <input id="audit-ids" class="inp" type="text" placeholder="감사할 ID (쉼표 구분, 예: 1,2,3)" style="width:200px;font-size:.75rem;">
        <button onclick="runStyleAudit()" class="btn btn-a" id="audit-run-btn">🔍 감사 시작</button>
        <button onclick="loadAuditResults()" class="btn btn-m">새로고침</button>
      </div>
      <div id="audit-status" style="display:none;margin-bottom:8px;font-size:.74rem;color:var(--amber);font-weight:600;"></div>
      <div id="audit-summary" style="display:none;margin-bottom:8px;padding:8px 12px;border-radius:6px;background:var(--bg);font-size:.75rem;"></div>
      <div id="audit-regen-actions" style="display:none;margin-bottom:10px;gap:8px;align-items:center;flex-wrap:wrap;">
        <button onclick="auditRegenAll()" class="btn btn-r" style="font-size:.73rem;" id="audit-regen-all-btn">✗ 실패 전체 재생성</button>
        <button onclick="auditRegenSelected()" class="btn btn-m" style="font-size:.73rem;" id="audit-regen-sel-btn">☑ 선택 재생성</button>
        <span id="audit-regen-status" style="font-size:.72rem;color:var(--amber);font-weight:600;"></span>
      </div>
      <div id="audit-results" style="display:none;overflow-x:auto;">
        <table style="width:100%;font-size:.72rem;">
          <thead><tr style="color:var(--muted);">
            <th style="padding:4px 8px;"><input type="checkbox" id="audit-check-all" onchange="auditToggleAll(this.checked)" title="실패 전체 선택" style="cursor:pointer;"></th>
            <th style="text-align:left;padding:4px 8px;">ID</th><th style="text-align:left;padding:4px 8px;">단어</th>
            <th style="text-align:left;padding:4px 8px;">급</th><th style="text-align:left;padding:4px 8px;">예문</th>
            <th style="text-align:left;padding:4px 8px;">결과</th><th style="text-align:left;padding:4px 8px;">문제</th>
          </tr></thead>
          <tbody id="audit-tbody"></tbody>
        </table>
      </div>
    </div>
  </div>
  <!-- 탭 내용: 날짜별 -->
  <div id="rp-history" style="display:none;">
    <input type="date" id="rp-date-pick" onchange="loadHistoryDate()" class="inp" style="width:100%;margin-bottom:12px;">
    <div id="rp-history-list"></div>
  </div>
  <!-- 탭 내용: 진행 상황 -->
  <div id="rp-live" style="display:none;">
    <!-- 작업 큐 -->
    <div class="card" style="margin-bottom:14px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="font-size:.8rem;font-weight:700;">작업 큐</span>
          <span id="gq-count-badge" style="font-size:.65rem;color:var(--muted2);background:var(--bg3);padding:1px 8px;border-radius:10px;"></span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span id="ql-desktop-status" style="font-size:.65rem;color:var(--muted2);"></span>
          <button id="ql-btn-desktop" onclick="setGlobalTarget('desktop')" class="btn btn-p" style="font-size:.68rem;padding:3px 10px;">💻 GPU</button>
          <button id="ql-btn-nas" onclick="setGlobalTarget('nas')" class="btn btn-m" style="font-size:.68rem;padding:3px 10px;">🖥 NAS</button>
          <button onclick="cleanupQueue()" class="btn btn-m" style="font-size:.68rem;padding:3px 10px;" title="완료/실패 작업 정리">🗑 정리</button>
        </div>
      </div>
      <div id="global-queue-list">
        <div style="font-size:.72rem;color:var(--muted2);text-align:center;padding:10px 0;">대기 중인 작업이 없습니다</div>
      </div>
    </div>
    <!-- 렌더링 진행 -->
    <div id="live-summary" style="display:none;margin-bottom:12px;padding:12px;background:var(--bg3);border-radius:8px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <span id="live-status-label" style="font-size:.8rem;font-weight:700;color:var(--green);">대기 중</span>
        <div style="display:flex;align-items:center;gap:8px;">
          <span id="live-timing" style="font-size:.62rem;color:var(--muted2);"></span>
          <button id="live-cancel-btn" onclick="cancelBatchRender()" style="display:none;font-size:.68rem;padding:3px 10px;border-radius:5px;border:none;background:#ef4444;color:#fff;cursor:pointer;font-weight:600;">⏹ 취소</button>
          <button onclick="clearBatchQueue()" style="font-size:.6rem;padding:2px 8px;border-radius:5px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;" title="진행 기록 지우기">✕ 지우기</button>
        </div>
      </div>
      <!-- 프레임 단위 진행 (상단 전역 바 대체) -->
      <div id="live-frame-prog" style="display:none;font-size:.65rem;color:var(--muted2);background:var(--bg2);border-radius:4px;padding:4px 10px;margin-bottom:6px;display:flex;align-items:center;gap:8px;">
        <span id="lfp-word" style="color:var(--accent);font-weight:600;"></span>
        <span id="lfp-step" style="flex:1;"></span>
        <div style="width:80px;background:rgba(255,255,255,.1);border-radius:3px;height:4px;"><div id="lfp-bar" style="height:4px;background:linear-gradient(90deg,#6366f1,#a855f7);border-radius:3px;width:0%;transition:width .4s;"></div></div>
        <span id="lfp-pct" style="min-width:28px;text-align:right;"></span>
      </div>
      <div style="background:rgba(255,255,255,.08);border-radius:4px;height:8px;overflow:hidden;margin-bottom:6px;">
        <div id="live-pbar" style="height:100%;background:linear-gradient(90deg,#6366f1,#3fb950);border-radius:4px;width:0%;transition:width .4s;"></div>
      </div>
      <div style="display:flex;gap:16px;font-size:.66rem;color:var(--muted2);">
        <span>✅ 완료: <b id="live-done" style="color:var(--green);">0</b></span>
        <span>⏳ 대기: <b id="live-pending" style="color:var(--amber);">0</b></span>
        <span>⟳ 진행: <b id="live-running" style="color:#58a6ff;">0</b></span>
        <span>✕ 실패: <b id="live-failed" style="color:var(--red);">0</b></span>
        <span>↷ 건너뜀: <b id="live-skipped" style="color:var(--muted);">0</b></span>
        <span style="margin-left:auto;">합계: <b id="live-total">0</b></span>
      </div>
    </div>
    <div id="live-list" style="max-height:420px;overflow-y:auto;display:flex;flex-direction:column;gap:3px;"></div>
  </div>
</div>

<!-- ══ 영상 목록 ════════════════════════════════════════ -->
<div id="view-videos" class="view">
  <div class="bc"><span class="cur">📋 영상 목록</span></div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;align-items:center;">
    <select id="vf-lang" onchange="filterVids()" class="inp"><option value="">전체 언어</option><option value="EN">🇺🇸 EN</option><option value="JP">🇯🇵 JP</option><option value="CN">🇨🇳 CN</option><option value="VN">🇻🇳 VN</option><option value="ES">🇪🇸 ES</option></select>
    <select id="vf-level" onchange="filterVids()" class="inp"><option value="">전체 등급</option><option>1</option><option>2</option><option>3</option><option>4</option><option>5</option><option>6</option></select>
    <select id="vf-fmt" onchange="filterVids()" class="inp"><option value="">전체 포맷</option><option value="youtube">▶ YouTube</option><option value="reels">📱 릴스</option></select>
    <select id="vf-music" onchange="filterVids()" class="inp"><option value="">전체 음악</option></select>
    <select id="vf-status" onchange="filterVids()" class="inp"><option value="">전체 상태</option><option value="uploaded">업로드됨</option><option value="generated">생성됨</option><option value="missing">파일 없음</option></select>
    <span id="vf-count" style="font-size:.72rem;color:var(--muted);margin-left:auto;"></span>
    <button class="btn btn-g" onclick="updateAllDescriptions(document.getElementById('vf-lang').value||null)" style="font-size:.7rem;padding:4px 10px;" title="업로드된 YouTube 본편 설명란을 10개 예문으로 업데이트">📝 설명란 업데이트(10개)</button>
  </div>
  <div class="card" style="overflow-x:auto;padding:0;">
    <table>
      <thead><tr><th>Day</th><th>ID</th><th>단어</th><th>뜻</th><th>언어</th><th>등급</th><th>포맷</th><th>음악</th><th>크기</th><th>생성</th><th>조회수</th><th>상태</th><th>액션</th></tr></thead>
      <tbody id="vids-tbody"></tbody>
    </table>
  </div>
</div>


<!-- ══ YouTube ══════════════════════════════════════════ -->
<div id="view-youtube" class="view">
  <div class="bc"><span class="cur">▶ YouTube 채널 통계</span></div>
  <div id="yt-loading" style="text-align:center;padding:24px;color:var(--muted);display:none;">채널 통계 로드 중...</div>
  <div id="yt-content"></div>
</div>

<!-- ══ YouTube 업로드 현황 ════════════════════════════════ -->
<div id="view-yt-upload" class="view">
  <div class="bc"><span class="cur">📤 YouTube 업로드 현황</span></div>
  <!-- 필터 & 액션 바 -->
  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;align-items:center;">
    <select id="ytu-lang" onchange="ytUploadFilter()" class="inp">
      <option value="">전체 언어</option>
      <option value="EN">🇺🇸 EN</option><option value="JP">🇯🇵 JP</option>
      <option value="CN">🇨🇳 CN</option><option value="VN">🇻🇳 VN</option><option value="ES">🇪🇸 ES</option>
    </select>
    <select id="ytu-fmt" onchange="ytUploadFilter()" class="inp">
      <option value="">전체 포맷</option>
      <option value="youtube">▶ YouTube</option>
      <option value="reels">📱 쇼츠</option>
    </select>
    <select id="ytu-status" onchange="ytUploadFilter()" class="inp">
      <option value="pending">업로드 대기</option>
      <option value="all">전체</option>
      <option value="uploaded">업로드 완료</option>
    </select>
    <button onclick="loadYtUpload()" class="btn btn-m">새로고침</button>
    <button onclick="reconcileUploads()" class="btn btn-m" style="font-size:.7rem;" title="YouTube 채널 스캔해서 누락된 업로드 기록 복구">🔄 로그 복구</button>
    <span id="ytu-count" style="font-size:.72rem;color:var(--muted);margin-left:auto;"></span>
  </div>
  <!-- 탭 -->
  <div style="display:flex;gap:4px;margin-bottom:10px;">
    <button id="ytu-tab-word" class="btn btn-g" style="font-size:.72rem;" onclick="ytUploadTab('word')">단어/쇼츠</button>
    <button id="ytu-tab-conv" class="btn btn-m" style="font-size:.72rem;" onclick="ytUploadTab('conv')">회화</button>
    <button id="ytu-tab-kdrama" class="btn btn-m" style="font-size:.72rem;" onclick="ytUploadTab('kdrama')">K-드라마</button>
  </div>
  <!-- 단어 영상 테이블 -->
  <div id="ytu-word-section">
    <div class="card" style="overflow-x:auto;padding:0;">
      <table>
        <thead><tr>
          <th>언어</th><th>ID</th><th>단어</th><th>뜻</th><th>등급</th><th>포맷</th><th>파일</th><th>상태</th><th style="text-align:right;">👁 조회</th><th style="text-align:right;">👍 좋아요</th><th style="text-align:right;">💬 댓글</th><th>액션</th>
        </tr></thead>
        <tbody id="ytu-word-tbody"></tbody>
      </table>
    </div>
  </div>
  <!-- 회화 영상 테이블 -->
  <div id="ytu-conv-section" style="display:none;">
    <div class="card" style="overflow-x:auto;padding:0;">
      <table>
        <thead><tr>
          <th>언어</th><th>테마 ID</th><th>포맷</th><th>파일</th><th>상태</th><th>렌더링일</th><th style="text-align:right;">👁 조회</th><th style="text-align:right;">👍 좋아요</th><th style="text-align:right;">💬 댓글</th><th>액션</th>
        </tr></thead>
        <tbody id="ytu-conv-tbody"></tbody>
      </table>
    </div>
  </div>
  <!-- K-드라마 영상 테이블 -->
  <div id="ytu-kdrama-section" style="display:none;">
    <div class="card" style="overflow-x:auto;padding:0;">
      <table>
        <thead><tr>
          <th>언어</th><th>테마 ID</th><th>포맷</th><th>파일</th><th>상태</th><th>렌더링일</th><th style="text-align:right;">👁 조회</th><th style="text-align:right;">👍 좋아요</th><th style="text-align:right;">💬 댓글</th><th>액션</th>
        </tr></thead>
        <tbody id="ytu-kdrama-tbody"></tbody>
      </table>
    </div>
  </div>
  <div id="ytu-loading" style="text-align:center;padding:24px;color:var(--muted);display:none;">로드 중...</div>
</div>

<!-- ══ Instagram ════════════════════════════════════════ -->
<div id="view-instagram" class="view">
  <div class="bc"><span class="cur">📸 Instagram 릴스</span></div>

  <!-- 연결 상태 -->
  <div class="card" style="margin-bottom:14px;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
      <span style="font-weight:700;font-size:.88rem;">📸 Instagram 연결</span>
      <span id="ig-status-badge" class="badge badge-m">미연결</span>
    </div>
    <div id="ig-account-info" style="font-size:.74rem;color:var(--muted);margin-bottom:12px;">
      Instagram Business/Creator 계정 연결 후 릴스를 업로드할 수 있습니다.
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;">
      <input id="ig-token-input" class="inp" placeholder="Instagram Access Token" style="flex:1;min-width:200px;font-size:.72rem;">
      <button onclick="igSaveToken()" class="btn btn-p" style="font-size:.72rem;">💾 저장</button>
      <button onclick="igCheckStatus()" class="btn btn-m" style="font-size:.72rem;">🔄 상태 확인</button>
    </div>
    <div style="margin-top:8px;font-size:.64rem;color:var(--muted2);">
      Meta Developer App → Instagram Graph API → 장기 액세스 토큰 발급 후 입력
    </div>
  </div>

  <!-- 업로드 준비 안내 -->
  <div style="padding:10px 14px;background:#f59e0b22;border:1px solid #f59e0b44;border-radius:8px;font-size:.72rem;color:#f59e0b;margin-bottom:14px;">
    ⚠️ 업로드 기능은 Meta Developer 앱 설정 및 크리에이터 계정 연결 후 활성화됩니다. 현재는 목록 확인만 가능합니다.
  </div>

  <!-- 릴스 업로드 -->
  <div class="card" style="margin-bottom:14px;">
    <div style="font-weight:700;font-size:.85rem;margin-bottom:12px;">🎬 릴스 목록</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;align-items:center;">
      <select id="ig-filter-lang" onchange="renderIgList()" class="inp">
        <option value="">전체 언어</option>
        <option value="EN">🇺🇸 EN</option>
        <option value="JP">🇯🇵 JP</option>
        <option value="CN">🇨🇳 CN</option>
        <option value="VN">🇻🇳 VN</option>
        <option value="ES">🇪🇸 ES</option>
      </select>
      <select id="ig-filter-status" onchange="renderIgList()" class="inp">
        <option value="">전체 상태</option>
        <option value="pending">업로드 대기</option>
        <option value="uploaded">업로드 완료</option>
      </select>
      <button onclick="loadIgData()" class="btn btn-m" style="font-size:.72rem;">↺ 새로고침</button>
      <span id="ig-count" style="font-size:.72rem;color:var(--muted);margin-left:auto;"></span>
    </div>
    <div class="card" style="overflow-x:auto;padding:0;">
      <table>
        <thead><tr>
          <th>단어</th><th>뜻</th><th>언어</th><th>등급</th><th>생성</th><th>Instagram</th><th>액션</th>
        </tr></thead>
        <tbody id="ig-tbody"></tbody>
      </table>
    </div>
    <div id="ig-empty" style="display:none;text-align:center;padding:32px;color:var(--muted);">
      <div style="font-size:2rem;margin-bottom:8px;">📸</div>
      <div>업로드할 릴스가 없습니다</div>
      <div style="font-size:.72rem;margin-top:4px;">단어 영상(쇼츠)을 먼저 렌더링하세요</div>
    </div>
  </div>
</div>

<!-- ══ 회화 영상 (기본 회화 + 일러스트 + 영상 통합) ════════════ -->
<div id="view-conv" class="view">
  <div class="bc"><span id="cv-bc-label" class="cur">💬 회화 영상</span></div>

  <!-- 기본 회화 영상 패널 -->
  <div id="cv-panel-basic">
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;align-items:center;">
      <select id="cv-filter-lang" onchange="renderConvThemes()" class="inp">
        <option value="">전체 언어</option>
        <option value="EN">🇺🇸 English</option>
        <option value="JP">🇯🇵 日本語</option>
        <option value="CN">🇨🇳 中文</option>
        <option value="VN">🇻🇳 Tiếng Việt</option>
        <option value="ES">🇪🇸 Español</option>
      </select>
      <select id="cv-filter-status" onchange="renderConvThemes()" class="inp">
        <option value="">전체 상태</option>
        <option value="rendered">YT 렌더됨</option>
        <option value="uploaded">YT 업로드됨</option>
        <option value="reels_rendered">쇼츠 렌더됨</option>
        <option value="reels_uploaded">쇼츠 업로드됨</option>
        <option value="pending">미렌더</option>
      </select>
      <div style="display:flex;gap:4px;margin-left:auto;align-items:center;">
        <span style="font-size:.7rem;color:var(--muted);">렌더:</span>
        <button id="conv-btn-nas" class="btn btn-g" onclick="convSetTarget('nas')" style="font-size:.7rem;padding:3px 8px;">🖥 NAS</button>
        <button id="conv-btn-desktop" class="btn btn-m" onclick="convSetTarget('desktop')" style="font-size:.7rem;padding:3px 8px;">💻 GPU</button>
        <button class="btn btn-m" onclick="loadConvThemes()" style="font-size:.7rem;padding:3px 8px;">↺</button>
        <span id="cv-vcount" style="font-size:.72rem;color:var(--muted);margin-left:8px;"></span>
      </div>
    </div>
    <div class="card" style="overflow-x:auto;padding:0;margin-bottom:12px;">
      <table>
        <thead><tr>
          <th style="width:36px;">#</th>
          <th>상황명</th>
          <th style="text-align:center;">구문</th>
          <th style="text-align:center;">언어</th>
          <th style="text-align:center;">▶ YouTube</th>
          <th style="text-align:center;">📱 쇼츠</th>
          <th style="text-align:center;">링크</th>
          <th style="text-align:right;padding-right:12px;">액션</th>
        </tr></thead>
        <tbody id="conv-themes-tbody"></tbody>
      </table>
    </div>
    <div id="conv-empty" style="display:none;text-align:center;padding:48px;color:var(--muted);">
      <div style="font-size:2rem;margin-bottom:10px;">📂</div>
      <div>phrases_db.json 파일이 없거나 비어 있습니다</div>
    </div>
  </div>

  <!-- 회화 일러스트 탭 -->
  <div id="cv-panel-illust" style="display:none;">
    <!-- 배치 생성 -->
    <div class="card" style="margin-bottom:14px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
        <div class="sec" style="margin:0;">배치 생성</div>
        <div style="display:flex;gap:4px;">
          <button id="ph-illust-target-nas" class="btn btn-p active" style="font-size:.72rem;padding:3px 10px;" onclick="setPhIllustTarget('nas')">🖥 NAS</button>
          <button id="ph-illust-target-desktop" class="btn btn-m" style="font-size:.72rem;padding:3px 10px;" onclick="setPhIllustTarget('desktop')">💻 GPU</button>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
        <span style="font-size:.74rem;color:var(--muted);">ID 범위:</span>
        <input id="ph-illust-start" type="number" placeholder="시작" min="1" class="num-input" style="width:80px;">
        <span style="color:var(--muted);">~</span>
        <input id="ph-illust-end" type="number" placeholder="끝" min="1" class="num-input" style="width:80px;">
        <button class="btn btn-a" onclick="startPhraseIllust(null)">🎨 생성 시작</button>
        <button class="btn btn-r" onclick="cancelPhraseIllust()">⏹ 취소</button>
        <button class="btn btn-m" onclick="loadPhraseSituations()">↺ 새로고침</button>
      </div>
      <div id="ph-illust-prog" style="display:none;margin-top:10px;">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
          <span id="ph-illust-prog-label" style="font-size:.75rem;font-weight:600;color:var(--amber);">생성 중...</span>
          <span id="ph-illust-prog-pct" style="font-size:.75rem;font-weight:700;color:var(--amber);">0%</span>
        </div>
        <div class="pbar-bg" style="height:6px;"><div id="ph-illust-prog-bar" class="pbar" style="height:6px;background:var(--amber);width:0%;"></div></div>
        <div id="ph-illust-prog-msg" style="font-size:.65rem;color:var(--muted);margin-top:3px;"></div>
      </div>
    </div>
    <!-- 미리보기 / 재생성 -->
    <div class="card" style="margin-bottom:14px;padding:0;overflow:hidden;">
      <!-- 헤더 바 -->
      <div style="padding:12px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
        <span style="font-size:.78rem;font-weight:700;color:var(--fg);flex:1;min-width:80px;">패널 뷰어</span>
        <div style="display:flex;align-items:center;gap:6px;">
          <button onclick="phBrowseNav(-1)" class="btn btn-m" style="padding:4px 10px;font-size:.8rem;" title="이전 상황">&lt;</button>
          <input id="ph-browse-id" class="num-input" type="number" value="1" min="1" style="width:56px;text-align:center;font-weight:700;">
          <button onclick="phBrowseNav(1)" class="btn btn-m" style="padding:4px 10px;font-size:.8rem;" title="다음 상황">&gt;</button>
          <button onclick="loadPhraseIllustBrowse()" class="btn btn-a" style="font-size:.75rem;padding:4px 12px;">조회</button>
        </div>
      </div>
      <!-- 상황 정보 바 -->
      <div id="ph-browse-info-bar" style="display:none;padding:10px 16px;background:var(--bg3);border-bottom:1px solid var(--border);">
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
          <span id="ph-browse-cat-chip" style="font-size:.6rem;font-weight:700;text-transform:uppercase;padding:2px 8px;border-radius:99px;background:var(--accent);color:#fff;letter-spacing:.05em;"></span>
          <div>
            <span id="ph-browse-sit-ko" style="font-size:.88rem;font-weight:700;"></span>
            <span id="ph-browse-sit-en" style="font-size:.72rem;color:var(--muted);margin-left:6px;"></span>
          </div>
          <span id="ph-browse-count" style="margin-left:auto;font-size:.68rem;color:var(--muted);white-space:nowrap;"></span>
        </div>
      </div>
      <!-- 패널 그리드 -->
      <div id="ph-browse-grid" style="padding:14px;display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px;"></div>
      <div id="ph-browse-regen-status" style="display:none;margin:0 14px 14px;padding:8px 12px;border-radius:6px;background:var(--bg);font-size:.74rem;color:var(--amber);font-weight:600;"></div>
    </div>
    <!-- 현황 요약 -->
    <div class="card" style="margin-bottom:14px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
        <span style="font-weight:700;font-size:.88rem;">회화 일러스트 현황</span>
        <span id="ph-illust-badge" class="badge badge-m"></span>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:.74rem;color:var(--muted);margin-bottom:3px;">
        <span>완성된 상황</span><span id="ph-illust-done-txt">–</span>
      </div>
      <div class="pbar-bg" style="height:5px;margin-bottom:12px;">
        <div id="ph-illust-done-bar" class="pbar" style="height:5px;width:0%;background:linear-gradient(90deg,#f59e0b,#f97316);"></div>
      </div>
      <div id="ph-illust-list" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px;"></div>
      <div id="ph-illust-empty" style="display:none;text-align:center;padding:24px;color:var(--muted);">
        <div style="font-size:2rem;margin-bottom:8px;">📂</div><div>phrases_db.json 없음</div>
      </div>
    </div>
  </div>

  <!-- 회화 영상 탭 -->
  <div id="cv-panel-video" style="display:none;">
    <div class="card" style="margin-bottom:14px;">
      <div class="sec">영상 생성</div>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px;">
        <span style="font-size:.74rem;color:var(--muted);">ID 범위:</span>
        <input id="ph-video-start" type="number" placeholder="시작" min="1" class="num-input" style="width:80px;">
        <span style="color:var(--muted);">~</span>
        <input id="ph-video-end" type="number" placeholder="끝" min="1" class="num-input" style="width:80px;">
        <button class="btn btn-a" onclick="startPhraseVideo(null)">🎬 생성 시작</button>
        <button class="btn btn-r" onclick="cancelPhraseVideo()">⏹ 취소</button>
        <button class="btn btn-m" onclick="loadPhraseSituations()">↺ 새로고침</button>
      </div>
      <div id="ph-video-prog" style="display:none;">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
          <span id="ph-video-prog-label" style="font-size:.75rem;font-weight:600;color:var(--accent);">생성 중...</span>
          <span id="ph-video-prog-pct" style="font-size:.75rem;font-weight:700;color:var(--accent);">0%</span>
        </div>
        <div class="pbar-bg" style="height:6px;"><div id="ph-video-prog-bar" class="pbar" style="height:6px;background:var(--accent);width:0%;"></div></div>
        <div id="ph-video-prog-msg" style="font-size:.65rem;color:var(--muted);margin-top:3px;"></div>
      </div>
    </div>
    <div id="ph-video-list" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;"></div>
  </div>
</div>

<!-- ══ K-드라마 view (영상 + 일러스트, 회화와 동일 구조) ═══════════ -->
<div id="view-kdrama" class="view">
  <div class="bc">
    <span onclick="nav(document.querySelector('[data-view=overview]'),'overview')">대시보드</span>
    <span style="color:var(--muted2);">›</span>
    <span class="cur" id="kd-bc-label">🎬 K-드라마</span>
  </div>

  <!-- K-드라마 일러스트 -->
  <div id="kd-panel-illust" style="display:none;">
    <div class="card" style="margin-bottom:14px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
        <div class="sec" style="margin:0;">🎨 일러스트 생성 (인트로 1장 + Phrase 10장 = 테마당 11장)</div>
        <span id="kd-illust-badge" class="badge badge-m">–</span>
      </div>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px;">
        <span style="font-size:.74rem;color:var(--muted);">ID 범위:</span>
        <input id="kd-illust-start" type="number" placeholder="시작" min="1" max="100" class="num-input" style="width:80px;">
        <span style="color:var(--muted);">~</span>
        <input id="kd-illust-end" type="number" placeholder="끝" min="1" max="100" class="num-input" style="width:80px;">
        <select id="kd-illust-mode" class="inp" style="font-size:.72rem;">
          <option value="all">전체 (인트로+Phrase)</option>
          <option value="intro_only">인트로만</option>
          <option value="phrases_only">Phrase만</option>
        </select>
        <button class="btn btn-a" onclick="kdStartIllust()">🎨 생성 시작</button>
        <button class="btn btn-m" onclick="loadKdramaIllustStatus()">↺ 새로고침</button>
        <label style="font-size:.7rem;color:var(--muted);display:flex;align-items:center;gap:3px;">
          <input type="checkbox" id="kd-illust-overwrite"> 기존 파일 덮어쓰기
        </label>
      </div>
      <div style="font-size:.64rem;color:var(--muted2);margin-bottom:8px;">
        범위 비워두면 전체 100개 / 비용: 인트로만 100장 ~$4 / 전체(11장×100) ~$44 (Gemini 3.1 Flash Image)<br>
        스타일: 단어 일러스트와 동일 (watercolor + chibi red panda)
      </div>
      <div style="display:flex;justify-content:space-between;font-size:.74rem;color:var(--muted);margin-bottom:3px;">
        <span>완성된 테마</span><span id="kd-illust-done-txt">–</span>
      </div>
      <div class="pbar-bg" style="height:6px;margin-bottom:10px;">
        <div id="kd-illust-done-bar" class="pbar" style="height:6px;width:0%;background:linear-gradient(90deg,#C77DFF,#9d4edd);"></div>
      </div>
    </div>

    <!-- 패널 뷰어 (intro + phrase 1~10) — 생성 카드 바로 아래 -->
    <div class="card" id="kd-browse-card" style="margin-bottom:14px;">
      <div style="display:flex;gap:6px;align-items:center;margin-bottom:8px;flex-wrap:wrap;">
        <span style="font-size:.78rem;font-weight:700;color:var(--fg);flex:1;min-width:80px;">패널 뷰어</span>
        <button class="btn btn-m" onclick="kdBrowseNav(-1)" style="font-size:.7rem;padding:4px 9px;">◀</button>
        <input id="kd-browse-id" type="number" min="1" max="100" value="1" onchange="loadKdramaIllustBrowse()" class="num-input" style="width:64px;">
        <button class="btn btn-m" onclick="kdBrowseNav(1)" style="font-size:.7rem;padding:4px 9px;">▶</button>
        <button class="btn btn-m" onclick="loadKdramaIllustBrowse()" style="font-size:.7rem;padding:4px 9px;">↺</button>
      </div>
      <div id="kd-browse-info-bar" style="display:none;padding:8px 10px;background:var(--bg);border-radius:6px;margin-bottom:10px;">
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
          <span id="kd-browse-cat-chip" style="font-size:.6rem;font-weight:700;padding:2px 7px;border-radius:99px;color:#fff;">–</span>
          <span id="kd-browse-sit-ko" style="font-size:.85rem;font-weight:700;"></span>
          <span id="kd-browse-sit-en" style="font-size:.7rem;color:var(--muted);"></span>
          <span id="kd-browse-count" style="margin-left:auto;font-size:.7rem;color:var(--muted);"></span>
        </div>
      </div>
      <div id="kd-browse-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;"></div>
    </div>

    <!-- 테마 카드 리스트 (회화 일러스트와 동일 패턴) -->
    <div id="kd-illust-list" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px;margin-bottom:14px;"></div>
  </div>

  <!-- K-드라마 영상 -->
  <div id="kd-panel-video" style="display:none;">
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;align-items:center;">
      <select id="kd-filter-lang" onchange="renderKdramaThemes()" class="inp">
        <option value="">전체 언어</option>
        <option value="EN">🇺🇸 English</option>
        <option value="JP">🇯🇵 日本語</option>
        <option value="CN">🇨🇳 中文</option>
        <option value="VN">🇻🇳 Tiếng Việt</option>
        <option value="ES">🇪🇸 Español</option>
      </select>
      <select id="kd-filter-status" onchange="renderKdramaThemes()" class="inp">
        <option value="">전체 상태</option>
        <option value="rendered">YT 렌더됨</option>
        <option value="uploaded">YT 업로드됨</option>
        <option value="reels_rendered">쇼츠 렌더됨</option>
        <option value="reels_uploaded">쇼츠 업로드됨</option>
        <option value="pending">미렌더</option>
      </select>
      <div style="display:flex;gap:4px;margin-left:auto;align-items:center;">
        <span style="font-size:.7rem;color:var(--muted);">렌더:</span>
        <button id="kd-btn-nas" class="btn btn-g" onclick="kdSetTarget('nas')" style="font-size:.7rem;padding:3px 8px;">🖥 NAS</button>
        <button id="kd-btn-desktop" class="btn btn-m" onclick="kdSetTarget('desktop')" style="font-size:.7rem;padding:3px 8px;">💻 GPU</button>
        <button class="btn btn-m" onclick="loadKdramaThemes()" style="font-size:.7rem;padding:3px 8px;">↺</button>
        <span id="kd-vcount" style="font-size:.72rem;color:var(--muted);margin-left:8px;"></span>
      </div>
    </div>
    <div class="card" style="overflow-x:auto;padding:0;margin-bottom:12px;">
      <table>
        <thead><tr>
          <th style="width:36px;">#</th>
          <th>테마명</th>
          <th style="text-align:center;">카테고리</th>
          <th style="text-align:center;">구문</th>
          <th style="text-align:center;">언어</th>
          <th style="text-align:center;">▶ YouTube</th>
          <th style="text-align:center;">📱 쇼츠</th>
          <th style="text-align:center;">링크</th>
          <th style="text-align:right;padding-right:12px;">액션</th>
        </tr></thead>
        <tbody id="kd-themes-tbody"></tbody>
      </table>
    </div>
    <div id="kd-empty" style="display:none;text-align:center;padding:48px;color:var(--muted);">
      <div style="font-size:2rem;margin-bottom:10px;">🎬</div>
      <div>kdrama_db.json 파일이 없거나 비어 있습니다</div>
    </div>
  </div>
</div>

</div><!-- /main -->
</div><!-- /body -->

<script>
// ── 상수 ─────────────────────────────────────────────────
const LVC={1:'#22d3ee',2:'#34d399',3:'#a3e635',4:'#fbbf24',5:'#fb923c',6:'#f87171'};
const EXAM_COLORS={TOPIK:'#818cf8',TOEIC:'#60a5fa',JLPT:'#f472b6',IELTS:'#a78bfa',HSK:'#f87171'};
const LANG_NAMES={EN:'🇺🇸 영어',CN:'🇨🇳 중국어',JP:'🇯🇵 일본어',VN:'🇻🇳 베트남어',ES:'🇪🇸 스페인어',SP:'🇪🇸 스페인어',KO:'🇰🇷 한국어',FR:'🇫🇷 프랑스어',DE:'🇩🇪 독일어'};
const _FLAGS={EN:'🇺🇸',JP:'🇯🇵',CN:'🇨🇳',VN:'🇻🇳',ES:'🇪🇸',SP:'🇪🇸',KO:'🇰🇷',FR:'🇫🇷',DE:'🇩🇪'};
const LANG_FLAGS=_FLAGS; // 전역 공용 플래그 (buildVidTable, renderIgList, renderConvThemes, renderTodayConv 공유)
const CONV_LANG_NAMES={EN:'English',JP:'日本語',CN:'中文',VN:'Tiếng Việt',ES:'Español'}; // 오늘의 회화 native 이름

let _ov=null, _node=null, _chartTL=null, _chartYT=null, _allVids=null;
let _desktopEnabled=true, _currentView='overview';

// ── 포맷 ─────────────────────────────────────────────────────
const fmt=n=>{if(!n&&n!==0)return'–';if(n>=1e6)return(n/1e6).toFixed(1)+'M';if(n>=1e3)return(n/1e3).toFixed(1)+'K';return n.toLocaleString();};
const fmtSz=b=>{if(!b)return'–';return b>1e6?(b/1e6).toFixed(1)+'MB':(b/1e3).toFixed(0)+'KB';};
const ago=iso=>{if(!iso)return'–';const s=Math.floor((Date.now()-new Date(iso.replace('T',' ')))/1000);if(s<60)return s+'초 전';if(s<3600)return Math.floor(s/60)+'분 전';if(s<86400)return Math.floor(s/3600)+'시간 전';return Math.floor(s/86400)+'일 전';};

// ── 시계 ─────────────────────────────────────────────────────
function tick(){document.getElementById('clock').textContent=new Date().toLocaleString('ko-KR',{hour12:false});}
setInterval(tick,1000);tick();

// ── 네비게이션 ──────────────────────────────────────────
function nav(el,view){
  document.querySelectorAll('.s-item').forEach(i=>i.classList.remove('active'));
  if(el) el.classList.add('active');
  document.querySelectorAll('.view').forEach(v=>v.style.display='none');
  // lv:EXAM:LEVEL:LANG → reuse lang view div
  if(view.startsWith('lv:')){
    const [,exam,lv,lang]=view.split(':');
    const langView='lang:'+exam+':'+lang;
    renderLangView(langView);
    const target=document.getElementById('view-'+langView)||document.getElementById('view-lang:TOPIK:EN');
    if(target) target.style.display='block';
    _currentView=view;
    loadNodeData(view);
    return;
  }
  const target=document.getElementById('view-'+view) || document.getElementById('view-lang:TOPIK:EN');
  if(target) target.style.display='block';
  _currentView=view;
  if(view.startsWith('lang:')) renderLangView(view);
  // exam 뷰는 API 응답 없이도 즉시 언어 카드 렌더 (API 실패해도 빈 화면 방지)
  if(view.startsWith('exam:')) renderExamView(view.split(':')[1], {});
  if(view.startsWith('lang:') || view.startsWith('exam:')) loadNodeData(view);
  if(view==='render'){loadJobQueue();loadBatchData();loadLiveStatus();loadPhraseSituations();rpTab('batch');}
  if(view==='work') loadWorkCenter();
  if(view==='conv'){loadConvThemes();loadPhraseSituations();cvTab('basic');}
  if(view==='videos') loadAllVideos();
  if(view==='youtube') loadYoutubeChannels();
  if(view==='yt-upload') loadYtUpload();
  if(view==='instagram') loadIgData();
}

function navQueueView(el){
  // 작업 큐는 렌더 진행사항에 통합됨
  navRenderTab(el,'live');
}

function navRenderTab(el,tab){
  document.querySelectorAll('.s-item').forEach(i=>i.classList.remove('active'));
  if(el) el.classList.add('active');
  document.querySelectorAll('.view').forEach(v=>v.style.display='none');
  // history 탭은 view-work의 날짜별 이력으로 연결
  if(tab==='history'){
    const target=document.getElementById('view-work');
    if(target) target.style.display='block';
    _currentView='work';
    loadWorkCenter();
    workTab('history');
    return;
  }
  const target=document.getElementById('view-render');
  if(target) target.style.display='block';
  _currentView='render';
  loadJobQueue();loadBatchData();rpTab(tab);
}

function navConvTab(el,tab){
  document.querySelectorAll('.s-item').forEach(i=>i.classList.remove('active'));
  if(el) el.classList.add('active');
  document.querySelectorAll('.view').forEach(v=>v.style.display='none');
  const target=document.getElementById('view-conv');
  if(target) target.style.display='block';
  _currentView='conv';
  loadConvThemes();loadPhraseSituations();cvTab(tab);
}

// ── K-드라마 메뉴 (영상/일러스트 분리) ─────────────────────────
function navKdramaTab(el,tab){
  document.querySelectorAll('.s-item').forEach(i=>i.classList.remove('active'));
  if(el) el.classList.add('active');
  document.querySelectorAll('.view').forEach(v=>v.style.display='none');
  const target=document.getElementById('view-kdrama');
  if(target) target.style.display='block';
  _currentView='kdrama';
  kdTab(tab);
}

function kdTab(t){
  ['video','illust'].forEach(x=>{
    const pan=document.getElementById('kd-panel-'+x);
    if(pan) pan.style.display=(x===t?'block':'none');
  });
  if(t==='video'){ loadKdramaThemes(); }
  if(t==='illust'){ loadKdramaIllustStatus(); loadKdramaIllustBrowse(); }
  const bc=document.getElementById('kd-bc-label');
  if(bc) bc.textContent = t==='illust' ? '🎨 K-드라마 일러스트' : '🎬 K-드라마 영상';
}

function toggleSGroup(name){
  const ch=document.getElementById('s-ch-'+name);
  const arr=document.getElementById('s-arr-'+name);
  if(!ch)return;
  ch.classList.toggle('open');
  if(arr) arr.style.transform=ch.classList.contains('open')?'':'rotate(-90deg)';
}

// ── 영상 작업 센터 로드 ────────────────────────────────────
function loadWorkCenter(){
  loadBatchData();
  loadJobQueue();
  loadLiveStatus();
  loadPhraseSituations();
  loadYtSched();
  loadDailyStatus();
  loadCountdown();
  workTab('today');
  _syncWorkCenterFromBatch();
}

// ── 언어별 카운트다운 ──────────────────────────────────────────
let _cdData = {};
let _cdTimer = null;

async function loadCountdown(){
  try{
    const r = await fetch('/api/daily/countdown');
    if(!r.ok) return;
    _cdData = await r.json();
    _renderCountdown();
    if(_cdTimer) clearInterval(_cdTimer);
    _cdTimer = setInterval(_tickCountdown, 1000);
  }catch(e){}
}

const _CD_FLAGS  = {EN:'🇺🇸',JP:'🇯🇵',CN:'🇨🇳',VN:'🇻🇳',ES:'🇲🇽'};
const _CD_NAMES  = {EN:'English',JP:'日本語',CN:'中文',VN:'Tiếng Việt',ES:'Español'};

function _renderCountdown(){
  const el = document.getElementById('countdown-grid');
  if(!el) return;
  const langs = ['EN','JP','CN','VN','ES'];

  // 날짜 헤더 업데이트 (첫 언어 기준 — 대표로 EN 날짜 사용)
  const firstLang = langs.find(l => _cdData[l]?.local_date);
  if(firstLang){
    const dateEl = document.getElementById('cd-upload-date');
    if(dateEl) dateEl.textContent = _cdData[firstLang].local_date + ' ·';
  }

  const ic=(ok,upl,label)=>{
    const color = upl?'var(--blue)':ok?'var(--green)':'var(--muted2)';
    const icon  = upl?'⬆':ok?'✓':'○';
    return `<span style="color:${color};font-size:.63rem;" title="${label}${upl?' (업로드됨)':ok?' (준비됨)':' (미준비)'}">${icon}${label}</span>`;
  };

  const epInput=(lang,ctype,ep,color)=>`
    <div style="display:flex;align-items:center;justify-content:center;gap:2px;">
      <span style="font-size:.55rem;color:var(--muted);">#</span>
      <input id="cd-ep-${lang}-${ctype}" type="number" min="1" value="${ep||''}"
        placeholder="−"
        style="width:44px;font-size:.72rem;font-weight:800;color:${color};
               background:transparent;border:none;border-bottom:1px solid var(--border2);
               text-align:center;padding:1px 0;outline:none;"
        onchange="setEpisode('${lang}','${ctype}',this)"
        title="${ctype==='word'?'단어':'회화'} 화수 직접 입력">
      <span style="font-size:.55rem;color:var(--muted2);">화</span>
    </div>`;

  el.innerHTML = langs.map(lang=>{
    const d    = _cdData[lang]||{};
    const vOk  = d.video_ready,  rlOk = d.reels_ready, ilOk = d.illust_ready;
    const vUp  = d.video_uploaded, rlUp = d.reels_uploaded;
    const cvUp = d.conv_uploaded;
    const wordReady = vOk || rlOk;
    const convReady = !cvUp;

    return `<div id="cd-card-${lang}"
      style="background:var(--bg3);border:1px solid var(--border);border-radius:8px;
             padding:8px 7px;text-align:center;display:flex;flex-direction:column;gap:3px;">

      <!-- 헤더: 국기 + 언어 -->
      <div style="font-size:.95rem;line-height:1;">${_CD_FLAGS[lang]||''}</div>
      <div style="font-size:.65rem;font-weight:700;color:var(--text2);">${lang}</div>

      <!-- KST 시간 -->
      <div style="font-size:.55rem;color:var(--muted);">
        =${d.kst_time||'--:--'} KST
      </div>
      <!-- 카운트다운 -->
      <div id="cd-timer-${lang}"
        style="font-size:.78rem;font-weight:700;font-family:monospace;color:var(--amber);
               border-bottom:1px solid var(--border2);padding-bottom:5px;margin-bottom:2px;">
        --:--:--
      </div>

      <!-- 단어 섹션 -->
      <div style="background:var(--bg2);border-radius:5px;padding:4px 3px;">
        <div style="font-size:.55rem;color:var(--blue);font-weight:700;margin-bottom:2px;">📚 단어</div>
        ${epInput(lang,'word', d.word_ep_num, 'var(--blue)')}
        <div style="display:flex;gap:3px;justify-content:center;margin-top:2px;">
          ${ic(vOk,vUp,'📹')}
          ${ic(rlOk,rlUp,'📱')}
          ${ic(ilOk,false,'🎨')}
        </div>
        <button onclick="uploadNow('${lang}','word',this)"
          style="margin-top:3px;width:100%;padding:3px 0;font-size:.55rem;font-weight:700;
                 background:${wordReady?'#0d2b0d':'var(--bg3)'};
                 color:${wordReady?'var(--green)':'var(--muted2)'};
                 border:1px solid ${wordReady?'var(--green)':'var(--border)'};
                 border-radius:4px;cursor:pointer;"
          ${wordReady?'':'disabled'}>
          ⚡ 올리기
        </button>
      </div>

      <!-- 회화 섹션 -->
      <div style="background:var(--bg2);border-radius:5px;padding:4px 3px;">
        <div style="font-size:.55rem;color:var(--purple,#a78bfa);font-weight:700;margin-bottom:2px;">💬 회화</div>
        ${epInput(lang,'conv', d.conv_ep_num, 'var(--purple,#a78bfa)')}
        <div style="display:flex;gap:3px;justify-content:center;margin-top:2px;">
          ${ic(!cvUp, cvUp, '📹')}
        </div>
        <button onclick="uploadNow('${lang}','conv',this)"
          style="margin-top:3px;width:100%;padding:3px 0;font-size:.55rem;font-weight:700;
                 background:${!cvUp?'#1a0d2b':'var(--bg3)'};
                 color:${!cvUp?'var(--purple,#a78bfa)':'var(--muted2)'};
                 border:1px solid ${!cvUp?'var(--purple,#a78bfa)':'var(--border)'};
                 border-radius:4px;cursor:pointer;"
          ${!cvUp?'':'disabled'}>
          ⚡ 올리기
        </button>
      </div>

    </div>`;
  }).join('');
  _tickCountdown();
}

async function uploadNow(lang, ctype, btn){
  const d = _cdData[lang]||{};
  let fmts = [];

  if(ctype === 'word'){
    if(d.video_ready  && !d.video_uploaded)  fmts.push('youtube');
    if(d.reels_ready  && !d.reels_uploaded)  fmts.push('reels');
    if(!fmts.length){ alert('업로드할 준비된 단어 영상이 없습니다.'); return; }
    if(!confirm(`[${lang}] 단어 ${fmts.join('+')} 지금 바로 업로드할까요?`)) return;

    btn.disabled=true; btn.textContent='⏳...';
    let done=0, errors=[];
    for(const fmt of fmts){
      try{
        const r=await fetch('/api/daily/upload-now',{method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({lang,fmt})});
        const rd=await r.json();
        if(r.ok) done++;
        else errors.push(rd.error||fmt);
      }catch(e){ errors.push(e.toString()); }
    }
    if(errors.length) alert(`오류: ${errors.join(', ')}`);
    else alert(`✅ [${lang}] 단어 ${done}개 업로드 완료!`);

  } else {
    // 회화 업로드 — 본편+쇼츠 둘 다 시도
    const ep = d.conv_ep_num;
    if(!ep){ alert('회화 화수를 먼저 설정하세요.'); return; }
    if(!confirm(`[${lang}] 회화 #${ep}화 본편+쇼츠 둘 다 업로드할까요?`)) return;

    btn.disabled=true; btn.textContent='⏳...';
    let convDone=0, convErrors=[];
    for(const fmt of ['youtube','reels']){
      try{
        const r=await fetch('/api/conv/upload',{method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({theme_id:String(ep),lang,fmt})});
        const rd=await r.json();
        if(r.ok) convDone++;
        else convErrors.push(`${fmt}: ${rd.error||''}`);
      }catch(e){ convErrors.push(`${fmt}: ${e}`); }
    }
    if(convErrors.length) alert(`[${lang}] 회화 #${ep}화 일부 오류:\n${convErrors.join('\n')}\n(성공 ${convDone}/2)`);
    else alert(`✅ [${lang}] 회화 #${ep}화 본편+쇼츠 ${convDone}개 업로드 완료!`);
  }

  btn.textContent='✅ 완료';
  setTimeout(()=>loadCountdown(), 5000);
}

async function setEpisode(lang, ctype, input){
  const ep = parseInt(input.value);
  if(!ep || ep < 1){
    const key = ctype==='conv' ? 'conv_ep_num' : 'word_ep_num';
    input.value = _cdData[lang]?.[key] || '';
    return;
  }
  try{
    const r=await fetch('/api/daily/set-episode',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({lang, ctype, episode_num:ep})});
    const d=await r.json();
    if(!r.ok){ alert('저장 실패: '+(d.error||'')); return; }
    if(_cdData[lang]){
      if(ctype==='conv') _cdData[lang].conv_ep_num = ep;
      else               _cdData[lang].word_ep_num = ep;
    }
  }catch(e){ alert('오류: '+e); }
}

function _tickCountdown(){
  const langs = ['EN','JP','CN','VN','ES'];
  const now = Date.now();
  langs.forEach(lang=>{
    const d = _cdData[lang];
    if(!d) return;
    const target = new Date(d.next_upload_utc).getTime();
    let diff = Math.max(0, Math.floor((target - now)/1000));
    const h = Math.floor(diff/3600);
    diff -= h*3600;
    const m = Math.floor(diff/60);
    const s = diff%60;
    const txt = diff===0&&h===0?'🔔 업로드 시간!'
      :`${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
    const el = document.getElementById(`cd-timer-${lang}`);
    if(el){
      el.textContent = txt;
      const isNear = (h===0 && m<30);
      el.style.color = h===0&&m===0&&s===0?'var(--green)':isNear?'var(--red)':'var(--amber)';
    }
  });
}

// ── 영상 작업 센터 탭 전환 ─────────────────────────────────
let _wcLivePollTimer=null;
function workTab(tab){
  ['today','custom','queue','history'].forEach(t=>{
    const btn=document.getElementById('wt-tab-'+t);
    const pan=document.getElementById('wt-panel-'+t);
    if(btn){btn.classList.toggle('on',t===tab);btn.classList.toggle('btn-g',t===tab);btn.classList.toggle('btn-m',t!==tab);}
    if(pan) pan.style.display=(t===tab?'block':'none');
  });
  if(_wcLivePollTimer){clearInterval(_wcLivePollTimer);_wcLivePollTimer=null;}
  if(tab==='queue'){
    _wcSyncLiveStatus();
    _wcLivePollTimer=setInterval(_wcSyncLiveStatus,2000);
  }
  if(tab==='history'){
    const wcd=document.getElementById('wc-date-pick');
    if(wcd){wcd.value=new Date().toISOString().slice(0,10);loadWcHistoryDate();}
  }
  if(tab==='today') _syncWorkCenterFromBatch();
}

// ── 날짜별 이력 (work 뷰용) ──────────────────────────────
async function loadWcHistoryDate(){
  const dp=document.getElementById('wc-date-pick');
  if(!dp) return;
  const date=dp.value;
  const el=document.getElementById('wc-history-list');
  if(!el) return;
  el.innerHTML='<div style="font-size:.72rem;color:var(--muted2);">로딩 중…</div>';
  try{
    const r=await fetch('/api/batch/history?date='+date);
    const d=await r.json();
    const items=d.items||[];
    if(!items.length){el.innerHTML='<div style="font-size:.72rem;color:var(--muted2);text-align:center;padding:16px;">해당 날짜에 기록이 없습니다</div>';return;}
    el.innerHTML=items.map(it=>`<div class="card" style="margin-bottom:8px;padding:10px 14px;font-size:.74rem;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span style="font-weight:600;">${it.word||it.phrase||it.id||''}</span>
        <span style="font-size:.65rem;color:var(--muted2);">${it.lang||''} ${it.format||''}</span>
      </div>
      <div style="color:var(--muted);margin-top:3px;">${it.status||''} ${it.rendered_at||it.created_at||''}</div>
    </div>`).join('');
  }catch(e){el.innerHTML='<div style="font-size:.72rem;color:var(--red);">오류: '+e.message+'</div>';}
}

// ── 작업 센터 큐/라이브 상태 동기화 (wc- 엘리먼트 업데이트) ─
async function _wcSyncLiveStatus(){
  try{
    const r=await fetch('/api/batch/today');
    if(!r.ok) return;
    const d=await r.json();
    const bq=d.queue||{};
    const items=bq.items||[];
    const status=bq.status||'idle';
    const summaryEl=document.getElementById('wc-live-summary');
    if(status!=='running'&&bq.completed_at){
      const age=Date.now()-new Date(bq.completed_at).getTime();
      if(age>10*60*1000){if(summaryEl)summaryEl.style.display='none';return;}
    }
    if(items.length>0||status==='running'){
      if(summaryEl) summaryEl.style.display='block';
    }
    const done=items.filter(i=>i.status==='done').length;
    const pending=items.filter(i=>i.status==='pending').length;
    const running=items.filter(i=>i.status==='running').length;
    const failed=items.filter(i=>i.status==='failed').length;
    const skipped=items.filter(i=>i.status==='skipped').length;
    const total=items.length;
    const setT=(id,v)=>{const e=document.getElementById(id);if(e)e.textContent=v;};
    setT('wc-live-done',done);setT('wc-live-pending',pending);setT('wc-live-running',running);
    setT('wc-live-failed',failed);setT('wc-live-skipped',skipped);setT('wc-live-total',total);
    const pbar=document.getElementById('wc-live-pbar');
    if(pbar&&total>0) pbar.style.width=Math.round((done+skipped)/total*100)+'%';
    const lbl=document.getElementById('wc-live-status-label');
    if(lbl) lbl.textContent=status==='running'?'렌더링 중':status==='done'?'완료':'대기 중';
    const cancelBtn=document.getElementById('wc-live-cancel-btn');
    if(cancelBtn) cancelBtn.style.display=status==='running'?'inline-block':'none';
  }catch(e){}
}

// ── 배치 데이터에서 작업 센터 카드 동기화 ────────────────────
function _syncWorkCenterFromBatch(){
  const langs=['EN','JP','CN','VN','ES'];
  const flags={EN:'🇺🇸',JP:'🇯🇵',CN:'🇨🇳',VN:'🇻🇳',ES:'🇪🇸'};
  ['wc-word-yt-langs','wc-word-reels-langs','wc-conv-yt-langs','wc-conv-reels-langs'].forEach(id=>{
    const el=document.getElementById(id);
    if(!el) return;
    el.innerHTML=langs.map(l=>`<div style="display:flex;align-items:center;justify-content:space-between;">
      <span>${flags[l]||''} ${l}</span>
      <span style="color:var(--muted2);">○ ○</span>
    </div>`).join('');
  });
}

// ── 업로드 스케줄 저장/실행 (work 센터용 — _getSchedEl이 wc-sched-* 우선 처리) ──
function wcSchedSave(){ ytSchedSave(); }
function wcSchedRun(){ ytSchedRun(); }

// ── 회화 탭 전환 ─────────────────────────────────────────
function cvTab(t){
  ['basic','illust','video'].forEach(x=>{
    const btn=document.getElementById('cv-tab-'+x);
    const pan=document.getElementById('cv-panel-'+x);
    if(btn){btn.classList.toggle('on',x===t);}
    if(pan) pan.style.display=(x===t?'block':'none');
  });
  if(t==='illust') loadPhraseSituations();
  if(t==='video')  loadPhraseSituations();
  // breadcrumb 업데이트
  const bc = document.getElementById('cv-bc-label');
  if(bc){
    bc.textContent = t==='illust' ? '🖼 회화 일러스트'
                    : t==='video'  ? '🎬 회화 영상 (배치)'
                    : '💬 회화 영상';
  }
}

// ── 큐 정리 (완료/실패/취소 작업 제거) ─────────────────────
async function cleanupQueue(){
  const r=await fetch('/api/queue/cleanup',{method:'POST'});
  const d=await r.json();
  loadJobQueue();
  if(d.removed>0) alert(`${d.removed}개 완료된 작업을 정리했습니다.`);
}

// ── 전역 렌더링 위치 설정 ──────────────────────────────────
async function setGlobalTarget(target){
  await fetch('/api/render-config/toggle',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({desktop_enabled: target==='desktop'})});
  loadJobQueue();
  loadOverview();
}

// ── 개별 작업 취소/삭제 ───────────────────────────────────
async function deleteJob(jobId){
  await fetch('/api/queue/delete/'+encodeURIComponent(jobId),{method:'POST'});
  loadJobQueue();
}

async function cancelJob(jobId){
  if(!confirm('이 작업을 취소할까요?')) return;
  await fetch('/api/queue/cancel/'+encodeURIComponent(jobId),{method:'POST'});
  loadJobQueue();
}

async function restartJob(jobId){
  const r=await fetch('/api/queue/restart/'+encodeURIComponent(jobId),{method:'POST'});
  const d=await r.json();
  if(!r.ok){alert('재시작 실패: '+(d.error||''));return;}
  loadJobQueue();
}

// ── 작업 대상 변경 (대기 중 작업) ─────────────────────────
async function setJobTarget(jobId, target){
  await fetch('/api/queue/target/'+encodeURIComponent(jobId),{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({target})});
  loadJobQueue();
}

// ── 시간 포맷 헬퍼 ───────────────────────────────────────
function _fmtHM(iso){
  if(!iso)return '';
  const d=new Date(iso);
  return d.toLocaleTimeString('ko-KR',{hour:'2-digit',minute:'2-digit',hour12:false});
}
function _fmtElapsed(startIso,endIso){
  if(!startIso)return '';
  const s=new Date(startIso), e=endIso?new Date(endIso):new Date();
  const sec=Math.max(0,Math.floor((e-s)/1000));
  const h=Math.floor(sec/3600), m=Math.floor((sec%3600)/60), s2=sec%60;
  if(h>0) return `${h}시간 ${m}분`;
  if(m>0) return `${m}분 ${s2}초`;
  return `${s2}초`;
}

// ── 글로벌 작업 큐 로드 ──────────────────────────────────
async function loadJobQueue(){
  try{
    const r=await fetch('/api/queue');
    const d=await r.json();
    renderJobQueue(d);
  }catch(e){}
}

// 글로벌 큐 렌더링
function renderJobQueue(d){
  const jobs=(d.jobs||[]).filter(j=>j.status!=='done'||(_recentCutoff(j)));
  const list=document.getElementById('global-queue-list');
  const wcList=document.getElementById('wc-global-queue-list');
  const badge=document.getElementById('gq-count-badge');
  const wcBadge=document.getElementById('wc-gq-count-badge');
  const cfg=d.render_config||{};
  const desktopEnabled=cfg.desktop_enabled!==false;
  const desktopBusy=d.desktop_busy;

  // 기본 렌더링 위치 버튼 업데이트 (양쪽 패널)
  for(const [dId,nId,stId] of [['ql-btn-desktop','ql-btn-nas','ql-desktop-status'],
                                 ['wc-ql-btn-desktop','wc-ql-btn-nas','wc-ql-desktop-status']]){
    const btnD=document.getElementById(dId);
    const btnN=document.getElementById(nId);
    const dSt=document.getElementById(stId);
    if(btnD) btnD.className='btn '+(desktopEnabled?'btn-p':'btn-m');
    if(btnN) btnN.className='btn '+(desktopEnabled?'btn-m':'btn-p');
    if(dSt){ dSt.textContent=desktopBusy?'💻 GPU 렌더링 중':'💻 GPU 대기 중';
             dSt.style.color=desktopBusy?'var(--amber)':'var(--green)'; }
  }

  const active=jobs.filter(j=>['queued','running'].includes(j.status));
  const finished=jobs.filter(j=>['done','failed','cancelled'].includes(j.status)).slice(-5);
  const visible=[...active,...finished];
  const badgeTxt=active.length?`${active.length}개 진행중`:'';
  if(badge) badge.textContent=badgeTxt;
  if(wcBadge) wcBadge.textContent=badgeTxt;

  const emptyHtml='<div style="font-size:.72rem;color:var(--muted2);text-align:center;padding:10px 0;">대기 중인 작업이 없습니다</div>';
  if(!visible.length){
    if(list) list.innerHTML=emptyHtml;
    if(wcList) wcList.innerHTML=emptyHtml;
    return;
  }

  const typeInfo={
    video_batch:        {label:'단어영상',  color:'var(--accent)', icon:'🎬'},
    illust:             {label:'일러스트',  color:'var(--amber)',  icon:'🎨'},
    conv_video:         {label:'회화영상',  color:'var(--green)',  icon:'💬'},
    kdrama_video:       {label:'K드라마',   color:'#C77DFF',       icon:'🎬'},
    kdrama_illust:      {label:'K드라마일러', color:'#C77DFF',      icon:'🎨'},
    phrase_video:       {label:'회화영상',  color:'var(--green)',  icon:'💬'},
    phrase_illust:      {label:'회화일러',  color:'#a855f7',       icon:'🖼'},
    phrase_illust_regen:{label:'일러재생성',color:'#f97316',       icon:'🔄'},
  };
  const statusInfo={
    queued:    {text:'대기',color:'var(--muted)'},
    running:   {text:'진행중',color:'var(--accent)'},
    done:      {text:'완료',color:'var(--green)'},
    failed:    {text:'실패',color:'var(--red)'},
    cancelled: {text:'취소됨',color:'var(--muted)'},
  };
  const targetLabel=t=>t==='desktop'?'💻 GPU':t==='nas'?'🖥 NAS':'⚡ auto';

  const queueHtml=visible.map(job=>{
    const ti=typeInfo[job.type]||{label:job.type,color:'var(--muted)',icon:'⚙️'};
    const si=statusInfo[job.status]||{text:job.status,color:'var(--muted)'};
    const isActive=['queued','running'].includes(job.status);
    const pct=job.pct||0;
    const showBar=['queued','running'].includes(job.status);
    const showPct=job.status==='running';

    const targetBtns=job.status==='queued'?`
      <div style="display:flex;gap:3px;">
        <button onclick="setJobTarget('${job.id}','desktop')" class="btn ${job.target==='desktop'?'btn-p':'btn-m'}" style="font-size:.58rem;padding:2px 6px;">💻</button>
        <button onclick="setJobTarget('${job.id}','nas')" class="btn ${job.target!=='desktop'?'btn-p':'btn-m'}" style="font-size:.58rem;padding:2px 6px;">🖥</button>
      </div>`:
      `<span style="font-size:.62rem;color:var(--muted2);">${targetLabel(job.target)}</span>`;

    const cancelBtn=isActive
      ?`<button onclick="cancelJob('${job.id}')" class="btn btn-r" style="font-size:.6rem;padding:2px 8px;">✕</button>`
      :job.status==='done'
        ?`<div style="display:flex;gap:3px;"><button onclick="openJobFolder('${job.id}')" class="btn btn-m" style="font-size:.6rem;padding:2px 6px;" title="출력 폴더 열기">📁</button><button onclick="deleteJob('${job.id}')" class="btn btn-m" style="font-size:.6rem;padding:2px 6px;opacity:.6;" title="삭제">🗑</button></div>`
        :`<div style="display:flex;gap:3px;"><button onclick="restartJob('${job.id}')" class="btn btn-g" style="font-size:.6rem;padding:2px 6px;" title="재시작">↻</button><button onclick="deleteJob('${job.id}')" class="btn btn-m" style="font-size:.6rem;padding:2px 6px;opacity:.6;" title="삭제">🗑</button></div>`;

    // batch_items가 있으면 한 줄 요약만 표시 (아래 렌더링 진행 패널이 상세 표시)
    let batchProgress='';
    if(job.type==='video_batch'&&job.status==='running'&&job.batch_items){
      const bi=job.batch_items;
      const bDone=bi.filter(x=>x.status==='done'||x.status==='rendered').length;
      const bFail=bi.filter(x=>x.status==='failed').length;
      const bRun=bi.filter(x=>x.status==='rendering').length;
      const curItem=bi.find(x=>x.status==='rendering');
      const curLabel=curItem?` · ${curItem.word||''} [${curItem.lang}]`:'';
      batchProgress=`<div style="margin-top:3px;font-size:.62rem;color:var(--muted2);">`+
        `${bDone}/${bi.length} 완료`+
        (bRun?`<span style="color:var(--amber);">${curLabel}</span>`:'') +
        (bFail?`<span style="color:var(--red);"> · 실패 ${bFail}</span>`:'') +
        `</div>`;
    }
    // illust 진행 중인 단어/예문 표시
    if(job.type==='illust'&&job.status==='running'&&job.step){
      const typeLabel = job.current_type==='sent'
        ? `예문[${(job.current_sent_idx??0)+1}]`
        : (job.current_type==='word'?'단어':'');
      const label = typeLabel ? `${typeLabel} · ${job.step}` : job.step;
      batchProgress=`<div style="margin-top:3px;font-size:.62rem;color:var(--amber);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${label}</div>`;
    }
    if((job.type==='conv_video'||job.type==='kdrama_video')&&job.status==='running'&&job.step){
      const frameInfo = (job.frame!=null&&job.total_frames)
        ? `<span style="color:var(--cyan,#22d3ee);margin-left:6px;">🎞 ${job.frame}/${job.total_frames}f</span>` : '';
      batchProgress=`<div style="margin-top:3px;font-size:.62rem;color:var(--amber);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${job.step}${frameInfo}</div>`;
    }

    return`<div style="display:flex;align-items:flex-start;gap:8px;padding:7px 0;border-bottom:1px solid var(--border);${!isActive?'opacity:.55;':''}">
      <span style="font-size:.6rem;font-weight:700;padding:2px 7px;border-radius:8px;background:${ti.color}22;color:${ti.color};white-space:nowrap;margin-top:1px;">${ti.icon} ${ti.label}</span>
      <div style="flex:1;min-width:0;">
        <div style="font-size:.74rem;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${job.description}</div>
        ${(()=>{
          const parts=[];
          if(job.started_at) parts.push('시작 '+_fmtHM(job.started_at));
          if(job.started_at && job.status==='running') parts.push('경과 '+_fmtElapsed(job.started_at,null));
          if(job.started_at && job.completed_at) parts.push('소요 '+_fmtElapsed(job.started_at,job.completed_at));
          if(!job.started_at && job.created_at) parts.push('등록 '+_fmtHM(job.created_at));
          return parts.length?`<div style="font-size:.6rem;color:var(--muted2);margin-top:2px;">${parts.join(' · ')}</div>`:'';
        })()}
        ${showBar?`<div class="pbar-bg" style="height:4px;margin-top:4px;"><div class="pbar" style="height:4px;width:${pct}%;background:${job.status==='running'?ti.color:'var(--muted)'};transition:width .5s;"></div></div>`:''}
        ${batchProgress}
        ${job.error?`<div style="font-size:.62rem;color:var(--red);margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${job.error}</div>`:''}
      </div>
      ${targetBtns}
      <span style="font-size:.62rem;font-weight:600;color:${si.color};white-space:nowrap;margin-top:1px;">${showPct?pct+'%':si.text}</span>
      ${cancelBtn}
    </div>`;
  }).join('');
  if(list) list.innerHTML=queueHtml;
  if(wcList) wcList.innerHTML=queueHtml;
}

async function openJobFolder(jobId){
  const r=await fetch('/api/open-folder',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({job_id:jobId})});
  const d=await r.json();
  if(!r.ok){alert('폴더 열기 실패: '+(d.error||''));return;}
}

function _recentCutoff(job){
  if(!job.completed_at) return true;
  return (Date.now()-new Date(job.completed_at).getTime())<300000; // 5분
}


function toggleExam(el, view){
  const parts=view.split(':'); const exam=parts[1];
  const ch=document.getElementById('ch-'+exam);
  const arr=document.getElementById('arr-'+exam);
  if(!ch)return nav(el,view);
  if(ch.classList.contains('open')){ch.classList.remove('open');if(arr)arr.textContent='▶';}
  else{ch.classList.add('open');if(arr)arr.textContent='▼';}
  nav(el,view);
}

// ── 데이터 로드 ──────────────────────────────────────────────
async function loadOverview(){
  try{
    const r=await fetch('/api/overview'); const d=await r.json();
    _ov=d;
    document.getElementById('last-upd').textContent='업데이트: '+d.now;
    renderHeader(d);
    renderOverview(d);
    renderIllustStats(d.illustration,'ov');
    if(_currentView==='overview'){}
    if(_currentView.startsWith('lang:')||_currentView.startsWith('exam:')||_currentView.startsWith('lv:')) loadNodeData(_currentView);
    if(_currentView==='youtube') renderYoutube(d);
    if(_currentView==='render') loadJobQueue();
  }catch(e){document.getElementById('last-upd').textContent='연결 오류';}
}

async function loadNodeData(view){
  try{
    const parts=view.split(':');
    let url='/api/node?';
    if(parts[0]==='exam')      url+=`category=시험용&exam=${parts[1]}`;
    else if(parts[0]==='lang') url+=`category=시험용&exam=${parts[1]}&lang=${parts[2]}`;
    else if(parts[0]==='lv')   url+=`category=시험용&exam=${parts[1]}&lang=${parts[3]}&level=${parts[2]}`;
    const r=await fetch(url); _node=await r.json();
    if(view.startsWith('exam:')) renderExamView(parts[1],_node);
    if(view.startsWith('lang:')) renderLangDetailContent(_node,parts[1],parts[2],null);
    if(view.startsWith('lv:'))   renderLangDetailContent(_node,parts[1],parts[3],parts[2]);
  }catch(e){}
}

// ── 헤더 / 진행 바 ──────────────────────────────────────
function renderHeader(d){
  const p=d.progress, run=p.status==='running';
  const row=document.getElementById('progress-row');
  const onRenderTab=_currentView==='render';
  // 렌더 탭에서는 상단 전역 바 숨기고 패널 내부에 표시
  row.style.display=(run&&!onRenderTab)?'flex':'none';
  const rs=document.getElementById('render-status');
  rs.style.display=run?'flex':'none';
  if(run){
    document.getElementById('pr-word').textContent=p.word?p.word+' ('+p.meaning+')':'렌더링 중...';
    document.getElementById('pr-step').textContent=p.step||'';
    document.getElementById('pr-bar').style.width=(p.pct||0)+'%';
    document.getElementById('pr-pct').textContent=(p.pct||0)+'%';
    document.getElementById('rs-text').textContent=p.word||'렌더링 중...';
  }
  // 렌더 패널 내부 프레임 진행 업데이트
  const lfp=document.getElementById('live-frame-prog');
  if(lfp){
    if(run&&onRenderTab){
      lfp.style.display='flex';
      const w=p.word||(p.status==='running'?'렌더링 중':'');
      document.getElementById('lfp-word').textContent=w?(w+(p.meaning?' ('+p.meaning+')':'')):'';
      document.getElementById('lfp-step').textContent=p.step||'';
      document.getElementById('lfp-bar').style.width=(p.pct||0)+'%';
      document.getElementById('lfp-pct').textContent=(p.pct||0)+'%';
    } else {
      lfp.style.display='none';
    }
  }
  const cfg=d.render_config; _desktopEnabled=cfg.desktop_enabled;
  if(!window._targetInitDone){_batchTarget=_desktopEnabled?'desktop':'nas';_customTarget=_desktopEnabled?'desktop':'nas';if(_desktopEnabled){setIllustTarget('desktop');setPhIllustTarget('desktop');}window._targetInitDone=true;}
  const btn=document.getElementById('toggle-btn');
  if(btn){
    if(_desktopEnabled){btn.textContent='💻 GPU';btn.className='btn btn-p';btn.style.fontSize='.72rem';}
    else{btn.textContent='🖥 NAS';btn.className='btn btn-g';btn.style.fontSize='.72rem';}
  }
  const q=cfg.queue||{};
  const qb=document.getElementById('queue-badge');
  if(q.status==='pending') qb.textContent='⏳';
  else if(q.status==='claimed') qb.textContent='🔄';
  else qb.textContent='';
  // 사이드바 배지
  const sb=document.getElementById('sb-render-badge');
  if(sb) sb.innerHTML=run?'<span class="pulse" style="color:var(--green);">●</span>':'';
}

// ── 전체 개요 ──────────────────────────────────────────
function renderOverview(d){
  const ov=d.overview, t=ov.total||1;
  setEl('ov-total',fmt(ov.total));
  setEl('ov-gen',fmt(ov.generated));
  setEl('ov-upl',fmt(ov.uploaded));
  setEl('ov-remain',fmt(ov.total-ov.uploaded));
  const gb=document.getElementById('ov-gen-bar');if(gb)gb.style.width=(ov.generated/t*100)+'%';
  const ub=document.getElementById('ov-upl-bar');if(ub)ub.style.width=(ov.uploaded/t*100)+'%';
  // 파이프라인
  setEl('ov-pipe-render',fmt(ov.generated)+' / '+fmt(ov.total));
  setEl('ov-pipe-upload',fmt(ov.uploaded)+' / '+fmt(ov.total));
  const prb=document.getElementById('ov-pipe-render-bar');if(prb)prb.style.width=(ov.generated/t*100)+'%';
  const pub=document.getElementById('ov-pipe-upload-bar');if(pub)pub.style.width=(ov.uploaded/t*100)+'%';
  // 타임라인
  const tl=d.timeline||{};const keys=Object.keys(tl).sort();const vals=keys.map(k=>tl[k]);
  if(keys.length){
    if(_chartTL){_chartTL.data.labels=keys;_chartTL.data.datasets[0].data=vals;_chartTL.update();}
    else _chartTL=new Chart(document.getElementById('chart-timeline'),{
      type:'line',data:{labels:keys,datasets:[{data:vals,borderColor:'#3fb950',backgroundColor:'rgba(63,185,80,.1)',fill:true,tension:.3,pointRadius:3,pointBackgroundColor:'#3fb950'}]},
      options:{responsive:true,plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#8b949e',maxTicksLimit:8},grid:{display:false}},y:{ticks:{color:'#8b949e',stepSize:1},grid:{color:'#21262d'}}}}
    });
  }
  // 음악
  const ml=document.getElementById('ov-music');if(ml){ml.innerHTML='';
  if(!d.music_files||!d.music_files.length) ml.innerHTML='<span style="color:var(--muted);font-size:.74rem;">music/ 폴더가 비어있습니다</span>';
  else d.music_files.forEach(f=>{ml.innerHTML+=`<div class="chip">🎵 ${f}</div>`;});}
}

// ── 시험 뷰 (언어 카드) ────────────────────────────────
function renderExamView(exam, stats){
  // TOPIK은 정적 HTML div 재사용, 그 외는 동적 뷰 div에서 찾음
  const el=document.getElementById('topik-lang-cards')
        ||document.querySelector(`#view-exam\\:${exam} .exam-lang-cards`);
  if(!el)return;
  const langs=['EN','CN','JP','VN','ES'];
  const col=EXAM_COLORS[exam]||'#818cf8';
  el.innerHTML=langs.map(lang=>`
    <div class="card-sm" style="cursor:pointer;border-color:${col}33;transition:.15s;"
         onmouseover="this.style.borderColor='${col}66'" onmouseout="this.style.borderColor='${col}33'"
         onclick="nav(null,'lang:${exam}:${lang}')">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
        <span style="font-size:1.1rem;">${LANG_FLAGS[lang]||''}</span>
        <span style="font-size:.9rem;font-weight:600;">${CONV_LANG_NAMES[lang]||lang}</span>
        <span class="badge badge-p" style="font-size:.6rem;">활성</span>
      </div>
      <div style="font-size:.78rem;color:var(--muted);">콘텐츠 준비됨</div>
    </div>`).join('');
}

// ── 언어 상세 뷰 ─────────────────────────────────────────────
function renderLangView(view){
  // 동적으로 뷰 div 생성
  if(!document.getElementById('view-'+view)){
    const div=document.createElement('div');
    div.id='view-'+view; div.className='view'; div.style.display='none';
    document.getElementById('main').appendChild(div);
  }
}

function renderLangDetailContent(stats, exam, lang, level){
  const col=EXAM_COLORS[exam]||'#818cf8';
  const lvCol=level?LVC[+level]:col;
  const total=stats.total||1;
  const el=document.getElementById('view-lang:'+exam+':'+lang) || document.getElementById('view-lang:TOPIK:EN');
  if(!el)return;
  // 등급별 현황 (level 지정 시 해당 급만)
  const lvKeys=level?[String(level)]:[1,2,3,4,5,6].map(String);
  const lvRows=lvKeys.map(lv=>{
    const info=stats.by_level?.[lv]||{total:0,generated:0,uploaded:0,min_id:null,max_id:null};
    const gpct=info.total?Math.round(info.generated/info.total*100):0;
    const idRange=info.min_id!=null?`#${info.min_id}~${info.max_id}`:'–';
    return `<tr>
      <td><span style="color:${LVC[+lv]||col};font-weight:700;">${lv}급</span></td>
      <td style="color:var(--muted2);font-size:.7rem;">${idRange}</td>
      <td style="color:var(--muted);">${fmt(info.total)}</td>
      <td style="color:${col};">${fmt(info.generated)} <span style="color:var(--muted2);font-size:.65rem;">(${gpct}%)</span></td>
      <td style="color:var(--green);">${fmt(info.uploaded)}</td>
      <td style="width:100px;"><div class="pbar-bg" style="height:3px;"><div class="pbar" style="height:3px;width:${gpct}%;background:${col};"></div></div></td>
    </tr>`;}).join('');
  const vidRows=(stats.video_list||[]).slice(-20).reverse().map(v=>`<tr>
    <td style="color:var(--muted);">${v.day?'#'+v.day:'–'}</td>
    <td style="color:var(--muted2);font-size:.7rem;">#${v.word_id}</td>
    <td style="font-weight:600;">${v.word}</td>
    <td><span style="color:${LVC[v.level]||col};font-weight:600;">${v.level}급</span></td>
    <td style="color:var(--muted);font-size:.72rem;">${v.music_file?'🎵 '+v.music_file:'–'}</td>
    <td style="color:var(--amber);font-weight:600;">${v.views?fmt(v.views):'–'}</td>
    <td>${v.video_id?`<a href="https://youtube.com/watch?v=${v.video_id}" target="_blank" style="color:var(--red);font-size:.72rem;">▶</a>`:'–'}</td>
  </tr>`).join('');
  const lvBadge=level?`<span style="color:${lvCol};font-weight:700;margin-left:6px;">${level}급</span>`:'';
  el.innerHTML=`
    <div class="bc">
      <span onclick="nav(document.querySelector('[data-view=overview]'),'overview')">대시보드</span>
      <span style="color:var(--muted2);">›</span>
      <span style="color:${col};">${exam}</span>
      ${level?`<span style="color:var(--muted2);">›</span><span style="color:${lvCol};">${level}급</span>`:''}
      <span style="color:var(--muted2);">›</span>
      <span class="cur">${CONV_LANG_NAMES[lang]||lang}</span>
    </div>
    <div class="g3" style="margin-bottom:14px;">
      <div class="card-sm kpi" style="border-color:${lvCol}33;"><div class="num" style="color:${lvCol};">${fmt(stats.total)}</div><div class="label">전체 단어${lvBadge}</div></div>
      <div class="card-sm kpi"><div class="num" style="color:${col};">${fmt(stats.generated)}</div><div class="label">영상 생성 (${(stats.generated/total*100).toFixed(1)}%)</div>
        <div class="pbar-bg" style="height:3px;margin-top:5px;"><div class="pbar" style="height:3px;width:${stats.generated/total*100}%;background:${col};"></div></div></div>
      <div class="card-sm kpi"><div class="num" style="color:var(--green);">${fmt(stats.uploaded)}</div><div class="label">업로드 (${(stats.uploaded/total*100).toFixed(1)}%)</div>
        <div class="pbar-bg" style="height:3px;margin-top:5px;"><div class="pbar" style="height:3px;width:${stats.uploaded/total*100}%;background:var(--green);"></div></div></div>
    </div>
    <div class="g2">
      <div class="card"><div class="sec">등급별 현황</div>
        <table><thead><tr><th>등급</th><th>ID</th><th>전체</th><th>생성</th><th>업로드</th><th>진행률</th></tr></thead>
        <tbody>${lvRows}</tbody></table></div>
      <div class="card"><div class="sec">최근 영상</div>
        <table><thead><tr><th>Day</th><th>ID</th><th>단어</th><th>등급</th><th>음악</th><th>조회수</th><th></th></tr></thead>
        <tbody>${vidRows||'<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:16px;">영상 없음</td></tr>'}</tbody></table></div>
    </div>`;
}

// ── 시험별 사이드바 동적 생성 ──────────────────────────────
function buildExamSidebar(){
  const el=document.getElementById('sb-exam-list');
  if(!el)return;
  const EXAMS=[
    {id:'TOPIK',flag:'🇰🇷',active:true},
    {id:'TOEIC',flag:'📝',active:false},
    {id:'JLPT', flag:'🌸',active:false},
    {id:'IELTS',flag:'🎓',active:false},
    {id:'HSK',  flag:'🐉',active:false},
  ];
  const LANGS=['EN','CN','JP','VN','ES'];
  const FLAGS=LANG_FLAGS;
  let html='';
  for(const exam of EXAMS){
    const ec=EXAM_COLORS[exam.id]||'#818cf8';
    if(!exam.active){
      html+=`<div class="s-item l1 dim" style="--c:${ec};"><span>${exam.flag}</span><span>${exam.id}</span></div>`;
      continue;
    }
    html+=`<div class="s-item l1" data-view="exam:${exam.id}" onclick="toggleExam(this,'exam:${exam.id}')" style="--c:${ec};">
      <span>${exam.flag}</span><span>${exam.id}</span><span class="arrow" id="arr-${exam.id}" style="margin-left:auto;">▶</span>
    </div>
    <div class="s-ch" id="ch-${exam.id}">`;
    for(let lv=1;lv<=6;lv++){
      const lc=LVC[lv]||ec;
      html+=`<div class="s-item l2" onclick="toggleSGroup('${exam.id}-${lv}')" style="--c:${lc};cursor:pointer;">
        <span style="color:${lc};font-weight:700;">${lv}급</span>
        <span class="s-arr" id="s-arr-${exam.id}-${lv}" style="margin-left:auto;">▾</span>
      </div>
      <div class="s-ch" id="s-ch-${exam.id}-${lv}">`;
      for(const lang of LANGS){
        html+=`<div class="s-item l3" data-view="lv:${exam.id}:${lv}:${lang}" onclick="nav(this,'lv:${exam.id}:${lv}:${lang}')" style="--c:${lc};">${FLAGS[lang]} ${lang}</div>`;
      }
      html+=`</div>`;
    }
    html+=`</div>`;
  }
  el.innerHTML=html;
}
document.addEventListener('DOMContentLoaded', buildExamSidebar);

// ── 일러스트 통계 공통 렌더 ──────────────────────────────────
function renderIllustStats(ill, prefix){
  if(!ill)return;
  // prefix='ov' → 'ov-illust-*',  prefix='iv' → 'illust-view-*'
  const P = prefix==='ov' ? 'ov-illust' : 'illust-view';
  const t=ill.total||1;
  const wdone=ill.word_done||0, wpct=Math.round(wdone/t*100);
  const stotal=ill.sent_total||0, sdone=ill.sent_done||0, spct=stotal?Math.round(sdone/stotal*100):0;

  // 단어 일러스트 바
  setEl(P+'-word-txt', wdone+' / '+t+' ('+wpct+'%)');
  setEl(P+'-word-pct', wpct+'%');
  const wb=document.getElementById(P+'-word-bar');
  if(wb) wb.style.width=wpct+'%';

  // 예문 일러스트 바
  setEl(P+'-sent-txt', sdone+' / '+stotal+' ('+spct+'%)');
  setEl(P+'-sent-pct', spct+'%');
  const sb=document.getElementById(P+'-sent-bar');
  if(sb) sb.style.width=spct+'%';

  // 전체 요약
  const sumEl=document.getElementById(P+'-summary');
  if(sumEl){
    const totalImg=wdone+sdone, totalAll=t+stotal;
    const totalPct=totalAll?Math.round(totalImg/totalAll*100):0;
    const cost=(totalImg*0.02).toFixed(2);
    const remain=totalAll-totalImg;
    const remainCost=(remain*0.02).toFixed(2);
    sumEl.innerHTML=`<div style="display:flex;gap:16px;flex-wrap:wrap;align-items:center;">
      <div><span style="font-size:.72rem;color:var(--muted);">전체</span> <b style="font-size:.9rem;">${totalImg}</b><span style="font-size:.72rem;color:var(--muted);">/${totalAll}장</span> <span style="font-size:.72rem;font-weight:700;color:var(--amber);">${totalPct}%</span></div>
      <div style="font-size:.72rem;color:var(--muted);">💰 사용 $${cost} · 남은 $${remainCost} (${remain}장)</div>
    </div>`;
  }

  // 등급별
  const lvEl=document.getElementById(P+'-levels');
  if(lvEl){
    lvEl.innerHTML=[1,2,3,4,5,6].map(lv=>{
      const info=ill.by_level?.[String(lv)]||{total:0,word_done:0,sent_total:0,sent_done:0};
      const wp=info.total?Math.round(info.word_done/info.total*100):0;
      const sp=info.sent_total?Math.round(info.sent_done/info.sent_total*100):0;
      const c=LVC[lv];
      const allDone=info.word_done+info.sent_done, allTotal=info.total+info.sent_total;
      return `<div style="background:#21262d;border-radius:8px;padding:8px;text-align:center;">
        <div style="color:${c};font-weight:700;font-size:.8rem;">${lv}급</div>
        <div style="font-size:.72rem;font-weight:600;margin-top:2px;">🖼 ${info.word_done}<span style="color:var(--muted);font-weight:400;">/${info.total}</span></div>
        <div class="pbar-bg" style="height:3px;margin:3px 0;"><div class="pbar" style="height:3px;width:${wp}%;background:${c};"></div></div>
        <div style="font-size:.72rem;font-weight:600;">📝 ${info.sent_done}<span style="color:var(--muted);font-weight:400;">/${info.sent_total}</span></div>
        <div class="pbar-bg" style="height:3px;margin:3px 0;"><div class="pbar" style="height:3px;width:${sp}%;background:#818cf8;"></div></div>
        <div style="font-size:.62rem;color:var(--muted);margin-top:2px;">${allDone}/${allTotal}</div>
      </div>`;}).join('');
  }

  // 진행 배지 + 게이지
  const prog=ill.progress||{};
  const badge=document.getElementById(P+'-badge');
  if(badge){
    if(prog.status==='running'){
      const step=prog.step?` — ${prog.step}`:'';
      badge.textContent=`● 생성 중 (${prog.pct||0}%)${step}`;
      badge.className='badge badge-run pulse';
    } else if(prog.status==='done'){badge.textContent='✅ 완료';badge.className='badge badge-done';}
    else if(prog.status==='cancelled'){badge.textContent='⏹ 취소됨';badge.className='badge badge-idle';}
    else{badge.textContent='대기 중';badge.className='badge badge-idle';}
  }
  // 생성/취소 버튼 토글
  if(prefix==='ov') _updateIllustButtons(prog.status);
  // 일러스트 생성 게이지
  const gp=document.getElementById('ov-illust-gen-progress');
  if(gp){
    if(prog.status==='running'){
      gp.style.display='block';
      const pct=prog.pct||0;
      setEl('ov-illust-gen-pct',pct+'%');
      setEl('ov-illust-gen-step',prog.step||'');
      setEl('ov-illust-gen-label',`🎨 일러스트 생성 중 — 단어 ${prog.done_word||0}장 · 예문 ${prog.done_sent||0}장`);
      const gb=document.getElementById('ov-illust-gen-bar');
      if(gb) gb.style.width=pct+'%';
    } else {
      gp.style.display='none';
    }
  }

  // 일일 사용량 렌더
  const usage=ill.usage||{};
  const uCalls=usage.calls||0, uOk=usage.success||0, uFail=usage.fail||0;
  const uCost=(uCalls*0.02).toFixed(2);
  [P, prefix==='ov'?'illust-view':null].filter(Boolean).forEach(pfx=>{
    const id=pfx==='ov-illust'?'ov-illust':'illust-view';
    setEl(id+'-usage-txt', uOk+'장 (API '+uCalls+'회) · $'+uCost);
    const detail=document.getElementById(id+'-usage-detail');
    if(detail) detail.textContent=uFail?'성공 '+uOk+' · 실패 '+uFail+' (검증 재시도 포함)':'성공 '+uOk+'장';
    const exEl=document.getElementById(id+'-exhausted');
    if(exEl){
      if(usage.exhausted){
        exEl.style.display='block';
        exEl.textContent='⛔ 일일 할당량 소진 ('+( usage.exhausted_at||'')+'시 초과) — 내일 자동 리셋';
      } else { exEl.style.display='none'; }
    }
  });

  // ov → illustrations view 동기화
  if(prefix==='ov'){
    renderIllustStats({...ill,progress:prog},'iv');
    const btns=['illust-gen-btn','illust-gen-btn2'];
    btns.forEach(id=>{const b=document.getElementById(id);if(b){
      const running=prog.status==='running';
      b.disabled=running;
      // 버튼이 이미 요청 중 상태면 텍스트 덮어쓰지 않음
      if(running) b.textContent='⏳ 생성 중...';
      else if(b.textContent==='⏳ 생성 중...'||b.textContent==='⏳ 요청 중...') b.textContent='🎨 생성';
    }});
  }
}

// ── 영상 목록 ────────────────────────────────────────────────
async function loadAllVideos(){
  try{
    const r=await fetch('/api/videos/all');
    const d=await r.json();
    _allVids=d.video_list||[];
    // 음악 필터 옵션 채우기
    const mu=document.getElementById('vf-music');
    const existing=new Set([...mu.options].map(o=>o.value));
    const musics=[...new Set(_allVids.map(v=>v.music_file).filter(Boolean))].sort();
    musics.forEach(m=>{if(!existing.has(m)){const o=document.createElement('option');o.value=m;o.textContent=m;mu.appendChild(o);}});
    filterVids();
  }catch(e){console.error('영상 목록 로드 실패',e);}
}

function filterVids(){
  if(!_ov)return;
  const list_src = _allVids || (_node && _node.video_list) || [];
  const lang=document.getElementById('vf-lang')?.value||'';
  const lv=document.getElementById('vf-level').value;
  const fmtF=(document.getElementById('vf-fmt')||{}).value||'';
  const mu=document.getElementById('vf-music').value;
  const st=document.getElementById('vf-status').value;
  let list=[...list_src];
  if(lang) list=list.filter(v=>(v.language||'EN')===lang);
  if(lv) list=list.filter(v=>String(v.level)===lv);
  if(fmtF) list=list.filter(v=>(v.fmt||'youtube')===fmtF);
  if(mu) list=list.filter(v=>v.music_file===mu);
  if(st==='uploaded') list=list.filter(v=>v.video_id);
  if(st==='generated') list=list.filter(v=>v.file_exists&&!v.video_id);
  if(st==='missing') list=list.filter(v=>!v.file_exists&&!v.video_id);
  buildVidTable(list);
}

function buildVidTable(list){
  document.getElementById('vf-count').textContent=list.length+'개';
  const t=document.getElementById('vids-tbody');t.innerHTML='';
  list.forEach(v=>{
    const c=LVC[v.level]||'#8b949e';
    const yt=v.video_id?`<a href="https://youtube.com/watch?v=${v.video_id}" target="_blank" style="color:#f87171;">▶</a>`:'–';
    const st=v.video_id?`<span class="badge badge-done">업로드</span>`:v.file_exists?`<span class="badge" style="background:#1a1a3a;color:#818cf8;border:1px solid #818cf8;">생성됨</span>`:`<span class="badge" style="background:#1a1a3a;color:#6b7280;border:1px solid #374151;">없음</span>`;
    const langFlag=LANG_FLAGS[v.language||'EN']||'';
    const isReels=(v.fmt||'youtube')==='reels';
    const fmtBadge=isReels
      ?`<span style="font-size:.58rem;padding:1px 5px;border-radius:4px;background:#be185d22;color:#f472b6;border:1px solid #be185d44;">📱 릴스</span>`
      :`<span style="font-size:.58rem;padding:1px 5px;border-radius:4px;background:#1e3a5f22;color:#60a5fa;border:1px solid #1e3a5f44;">▶ YT</span>`;
    t.innerHTML+=`<tr>
      <td style="color:var(--muted);">${v.day?'#'+v.day:'–'}</td>
      <td style="font-weight:600;">${v.word}</td>
      <td style="color:var(--muted);font-size:.78rem;">${v.meaning}</td>
      <td style="font-size:.72rem;">${langFlag} <span style="color:var(--muted2);">${v.language||'EN'}</span></td>
      <td><span style="color:${c};font-weight:600;">${v.level}급</span></td>
      <td>${fmtBadge}</td>
      <td style="font-size:.72rem;color:#a5b4fc;">${v.music_file?'🎵 '+v.music_file:'–'}</td>
      <td style="color:var(--muted);font-size:.72rem;">${fmtSz(v.file_size)}</td>
      <td style="color:var(--muted);font-size:.72rem;">${ago(v.generated_at)}</td>
      <td style="color:#fbbf24;font-weight:600;">${v.views?fmt(v.views):'–'}</td>
      <td>${st} ${yt}</td>
      <td style="white-space:nowrap;">
        <div style="display:flex;gap:3px;">
          <button class="btn btn-a" onclick="vidRender(${v.word_id},'${v.language||'EN'}','${v.exam||'TOPIK'}','${v.fmt||'youtube'}')" style="font-size:.62rem;padding:2px 7px;" title="렌더링">🎬</button>
          <button class="btn btn-g" onclick="vidUpload(${v.word_id},'${v.language||'EN'}','${v.exam||'TOPIK'}','${v.fmt||'youtube'}')" style="font-size:.62rem;padding:2px 7px;" ${!v.file_exists?'disabled':''} title="업로드">⬆</button>
          <button class="btn btn-p" onclick="vidRegenerate(${v.word_id},'${v.language||'EN'}','${v.exam||'TOPIK'}','${v.fmt||'youtube'}')" style="font-size:.62rem;padding:2px 7px;" title="재생성">↺</button>
          <button class="btn" onclick="vidDelete(${v.word_id},'${v.language||'EN'}','${v.exam||'TOPIK'}','${v.fmt||'youtube'}')" style="font-size:.62rem;padding:2px 7px;background:#2d1515;color:#f87171;border:1px solid #7f1d1d;" title="삭제">🗑</button>
        </div>
      </td></tr>`;});
}

async function vidRender(wordId, lang, exam, fmt='youtube'){
  const label=fmt==='reels'?'📱 릴스':'▶ YouTube';
  if(!confirm(`[${lang}] 단어 #${wordId} ${label} 렌더링할까요?`)) return;
  try{
    const r=await fetch('/api/render',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({word_id:wordId,lang:lang,exam:exam,fmt:fmt,target:'auto'})});
    const d=await r.json();
    if(!r.ok){alert('오류: '+(d.error||'')); return;}
    loadJobQueue();
  }catch(e){alert('실패: '+e);}
}
async function vidUpload(wordId, lang, exam, fmt='youtube'){
  const label=fmt==='reels'?'📱 릴스':'YouTube';
  if(!confirm(`[${lang}] 단어 #${wordId} ${label} 업로드할까요?`)) return;
  try{
    const r=await fetch('/api/render/upload',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({word_id:wordId,lang:lang,exam:exam,fmt:fmt})});
    const d=await r.json();
    if(!r.ok){alert('오류: '+(d.error||'')); return;}
    alert('업로드 시작됨');
    setTimeout(loadAllVideos, 3000);
  }catch(e){alert('실패: '+e);}
}
async function vidRegenerate(wordId, lang, exam, fmt='youtube'){
  const label=fmt==='reels'?'📱 릴스':'▶ YouTube';
  if(!confirm(`[${lang}] 단어 #${wordId} ${label} 재생성할까요?`)) return;
  try{
    const r=await fetch('/api/render',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({word_id:wordId,lang:lang,exam:exam,fmt:fmt,target:'auto'})});
    const d=await r.json();
    if(!r.ok){alert('오류: '+(d.error||'')); return;}
    loadJobQueue();
  }catch(e){alert('실패: '+e);}
}
async function vidDelete(wordId, lang, exam, fmt='youtube'){
  const label=fmt==='reels'?'📱 릴스':'▶ YouTube';
  if(!confirm(`[${lang}] 단어 #${wordId} ${label} 영상을 삭제할까요?\n(파일 및 로그에서 제거됩니다)`)) return;
  try{
    const r=await fetch('/api/video/delete',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({word_id:wordId,lang:lang,exam:exam,fmt:fmt})});
    const d=await r.json();
    if(!r.ok){alert('오류: '+(d.error||'')); return;}
    loadAllVideos();
  }catch(e){alert('실패: '+e);}
}

async function updateAllDescriptions(lang){
  const label = lang ? `[${lang}] ` : '전체 ';
  if(!confirm(`${label}업로드된 YouTube 본편 설명란을 10개 예문으로 업데이트할까요?\n(YouTube API 할당량을 사용합니다)`)) return;
  try{
    const r=await fetch('/api/update-descriptions',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({lang:lang||null})});
    const d=await r.json();
    if(!r.ok){alert('오류: '+(d.error||'')); return;}
    alert('설명란 업데이트 시작됨. 잠시 후 YouTube에서 확인하세요.');
  }catch(e){alert('실패: '+e);}
}

// ── YouTube ──────────────────────────────────────────────────
function renderYoutube(d){ /* overview poll에서 호출 — 다중채널은 loadYoutubeChannels 사용 */ }

async function loadYoutubeChannels(){
  const el=document.getElementById('yt-content');
  const ld=document.getElementById('yt-loading');
  ld.style.display='block'; el.innerHTML='';
  try{
    const r=await fetch('/api/youtube/channels');
    const d=await r.json();
    ld.style.display='none';
    const channels=(d.channels||[]);
    if(!channels.length){
      el.innerHTML='<div class="card" style="text-align:center;padding:36px;"><div style="font-size:1.8rem;margin-bottom:8px;">📺</div><div style="color:var(--muted);">연결된 채널 없음 — 각 언어 첫 업로드 시 OAuth 인증 필요</div></div>';
      return;
    }
    const ok=channels.filter(c=>!c.error);
    const totSubs=ok.reduce((s,c)=>s+c.subscribers,0);
    const totViews=ok.reduce((s,c)=>s+c.views,0);
    const totVids=ok.reduce((s,c)=>s+c.video_count,0);
    const hasPl=ok.some(c=>(c.bonpyeon||0)+(c.reels||0)+(c.phrase||0)>0);
    let html=`<div style="display:flex;justify-content:flex-end;margin-bottom:10px;">
      <button class="btn btn-a" onclick="syncPlaylists(this)" style="font-size:.72rem;padding:4px 12px;">🔄 플레이리스트 스캔</button>
      ${!hasPl?'<span style="font-size:.68rem;color:var(--amber);margin-left:10px;align-self:center;">⚠ 플레이리스트 정보 없음 — 스캔 후 본편/쇼츠/회화 표시</span>':''}
    </div>
    <div class="g3" style="margin-bottom:14px;">
      <div class="card-sm kpi"><div class="num" style="color:var(--red);">${fmt(totSubs)}</div><div class="label">총 구독자</div></div>
      <div class="card-sm kpi"><div class="num" style="color:var(--amber);">${fmt(totViews)}</div><div class="label">총 조회수</div></div>
      <div class="card-sm kpi"><div class="num" style="color:var(--blue);">${fmt(totVids)}</div><div class="label">총 영상 수</div></div>
    </div><div class="g3" style="margin-bottom:14px;">`;
    channels.forEach(ch=>{
      if(ch.error){
        html+=`<div class="card-sm" style="opacity:.5;"><div style="font-size:.75rem;font-weight:700;">${ch.flag} ${ch.lang}</div><div style="font-size:.62rem;color:var(--red);margin-top:6px;word-break:break-all;">${ch.error||'토큰 없음 또는 오류'}</div></div>`;
      } else {
        const ytUrl=`https://www.youtube.com/channel/${ch.channel_id}`;
        const hasPl=(ch.bonpyeon||0)+(ch.reels||0)+(ch.phrase||0)>0;
        html+=`<div class="card-sm">
          <div style="font-size:.78rem;font-weight:700;margin-bottom:10px;">
            <a href="${ytUrl}" target="_blank" style="color:inherit;text-decoration:none;">${ch.flag} ${ch.name}</a>
          </div>
          <div style="display:flex;gap:12px;font-size:.72rem;margin-bottom:10px;flex-wrap:wrap;">
            <div><div style="color:var(--red);font-weight:700;font-size:1rem;">${fmt(ch.subscribers)}</div><div style="color:var(--muted);">구독자</div></div>
            <div><div style="color:var(--amber);font-weight:700;font-size:1rem;">${fmt(ch.views)}</div><div style="color:var(--muted);">조회수</div></div>
            ${ch.likes!=null?`<div><div style="color:#f472b6;font-weight:700;font-size:1rem;">${fmt(ch.likes)}</div><div style="color:var(--muted);">좋아요</div></div>`:''}
            ${ch.comments!=null?`<div><div style="color:var(--green);font-weight:700;font-size:1rem;">${fmt(ch.comments)}</div><div style="color:var(--muted);">댓글</div></div>`:''}
            <div><div style="color:var(--blue);font-weight:700;font-size:1rem;">${fmt(ch.video_count)}</div><div style="color:var(--muted);">총영상</div></div>
          </div>
          <div style="display:flex;gap:8px;font-size:.68rem;border-top:1px solid var(--border);padding-top:8px;">
            <div style="flex:1;text-align:center;"><div style="font-weight:700;color:var(--green);">${ch.bonpyeon||0}</div><div style="color:var(--muted);">본편</div></div>
            <div style="flex:1;text-align:center;"><div style="font-weight:700;color:var(--purple,#a78bfa);">${ch.reels||0}</div><div style="color:var(--muted);">쇼츠</div></div>
            <div style="flex:1;text-align:center;"><div style="font-weight:700;color:var(--cyan,#22d3ee);">${ch.phrase||0}</div><div style="color:var(--muted);">회화</div></div>
          </div>
        </div>`;
      }
    });
    html+='</div>';
    el.innerHTML=html;
  }catch(e){
    ld.style.display='none';
    el.innerHTML='<div class="card" style="color:var(--red);">오류: '+e+'</div>';
  }
}

async function syncPlaylists(btn){
  const orig=btn.textContent;
  btn.disabled=true; btn.textContent='스캔 중...';
  try{
    const r=await fetch('/api/youtube/sync-playlists',{method:'POST'});
    const d=await r.json();
    btn.textContent=orig; btn.disabled=false;
    if(d.error){alert('오류: '+d.error); return;}
    const lines=Object.entries(d.synced||{}).map(([l,v])=>{
      if(v.error) return `${l}: 오류 — ${v.error}`;
      const keys=Object.keys(v);
      return `${l}: ${keys.length}개 (${keys.join(', ')})`;
    });
    alert('스캔 완료:\n'+lines.join('\n'));
    loadYoutubeChannels();
  }catch(e){btn.textContent=orig; btn.disabled=false; alert('실패: '+e);}
}

// ── YouTube 업로드 관리 ──────────────────────────────────────
let _ytuData = {word_videos:[], conv_videos:[], kdrama_videos:[]};
let _ytuTab = 'word';

// ── 업로드 스케줄 (4개 독립 설정) ──────────────────────────────
const _SCHED_TYPES=['word-yt','word-reels','conv-yt','conv-reels','kdrama-yt','kdrama-reels'];
let _schedStates={};  // {type: {enabled, interval_days, count, lang, last_run}}

function _schedEl(type, suffix){ return document.getElementById(`sched-${type}-${suffix}`); }

function _renderSchedToggle(type){
  const on=!!(_schedStates[type]||{}).enabled;
  const tog=_schedEl(type,'tog'), knob=_schedEl(type,'knob'), lbl=_schedEl(type,'lbl');
  if(tog) tog.style.background=on?'var(--green)':'#333';
  if(knob) knob.style.left=on?'20px':'2px';
  if(lbl){lbl.textContent=on?'ON':'OFF'; lbl.style.color=on?'var(--green)':'var(--muted)';}
}

function schedToggle(type){
  if(!_schedStates[type]) _schedStates[type]={};
  _schedStates[type].enabled=!_schedStates[type].enabled;
  _renderSchedToggle(type);
}

async function loadYtSched(){
  try{
    const r=await fetch('/api/youtube/upload-schedule');
    const d=await r.json();
    _SCHED_TYPES.forEach(t=>{
      const s=d[t]||{};
      _schedStates[t]={enabled:!!s.enabled,interval_days:s.interval_days||1,count:s.count||2,lang:s.lang||''};
      const setV=(sfx,v)=>{const e=_schedEl(t,sfx);if(e)e.value=String(v);};
      setV('interval',s.interval_days||1);
      setV('count',s.count||(t.startsWith('conv')||t.startsWith('kdrama')?1:2));
      setV('lang',s.lang||'');
      const lastEl=_schedEl(t,'last');
      if(lastEl) lastEl.textContent=s.last_run?`마지막: ${s.last_run}`:'';
      _renderSchedToggle(t);
    });
  }catch(e){}
}

async function saveSchedType(type){
  const getV=(sfx)=>{const e=_schedEl(type,sfx);return e?e.value:'';};
  const cfg={
    enabled:!!(_schedStates[type]||{}).enabled,
    interval_days:parseInt(getV('interval'))||1,
    count:parseInt(getV('count'))||1,
    lang:getV('lang'),
  };
  _schedStates[type]={...(_schedStates[type]||{}), ...cfg};
  try{
    await fetch('/api/youtube/upload-schedule',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({type, ...cfg})});
  }catch(e){alert('저장 실패: '+e);}
}

async function runSchedType(type, btn){
  const getV=(sfx)=>{const e=_schedEl(type,sfx);return e?e.value:'';};
  const count=parseInt(getV('count'))||1;
  const lang=getV('lang');
  const labels={'word-yt':'단어 본편','word-reels':'단어 쇼츠','conv-yt':'회화 본편','conv-reels':'회화 쇼츠','kdrama-yt':'K드라마 본편','kdrama-reels':'K드라마 쇼츠'};
  if(!confirm(`[${labels[type]||type}] ${count}개 업로드 실행할까요?`)) return;
  if(btn){btn.disabled=true;btn.textContent='업로드 중...';}
  try{
    const r=await fetch('/api/youtube/upload-run',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({type,count,lang})});
    const d=await r.json();
    if(!r.ok){alert('오류: '+(d.error||''));return;}
    alert(`완료: ${d.done}개 업로드됨${d.errors?.length?' / 오류: '+d.errors.length+'건':''}`);
    const lastEl=_schedEl(type,'last');
    if(lastEl) lastEl.textContent=`마지막: ${new Date().toISOString().slice(0,10)}`;
    loadYtUpload();
  }catch(e){alert('실패: '+e);}
  finally{if(btn){btn.disabled=false;btn.textContent='▶ 실행';}}
}

// 하위 호환 래퍼 (기존 코드에서 호출되는 경우)
function ytSchedToggle(){}
async function ytSchedSave(){}
async function ytSchedRun(){}

async function loadYtUpload(){
  const ld=document.getElementById('ytu-loading');
  if(ld) ld.style.display='block';
  try{
    const r=await fetch(`/api/youtube/upload-status?t=${Date.now()}`);
    const d=await r.json();
    _ytuData=d;
    ytUploadFilter();
    loadYtSched();
  }catch(e){
    if(ld) ld.style.display='none';
    alert('로드 실패: '+e);
  }
}

function ytUploadTab(tab){
  _ytuTab=tab;
  document.getElementById('ytu-word-section').style.display=tab==='word'?'block':'none';
  document.getElementById('ytu-conv-section').style.display=tab==='conv'?'block':'none';
  const kdSec=document.getElementById('ytu-kdrama-section');
  if(kdSec) kdSec.style.display=tab==='kdrama'?'block':'none';
  document.getElementById('ytu-tab-word').className=tab==='word'?'btn btn-g':'btn btn-m';
  document.getElementById('ytu-tab-conv').className=tab==='conv'?'btn btn-g':'btn btn-m';
  const kdBtn=document.getElementById('ytu-tab-kdrama');
  if(kdBtn) kdBtn.className=tab==='kdrama'?'btn btn-g':'btn btn-m';
  ytUploadFilter();
}

function ytUploadFilter(){
  const lang=document.getElementById('ytu-lang')?.value||'';
  const fmt=document.getElementById('ytu-fmt')?.value||'';
  const status=document.getElementById('ytu-status')?.value||'pending';
  const ld=document.getElementById('ytu-loading');
  const _LANG_FLAGS={'EN':'🇺🇸','JP':'🇯🇵','CN':'🇨🇳','VN':'🇻🇳','ES':'🇪🇸'};
  const _statsErr=(_ytuData||{}).stats_error;
  const _fmtN=(n,err)=>{
    if(err||_statsErr) return '<span style="color:#f87171;font-size:.6rem;" title="API 한도 초과">quota</span>';
    return n==null?'<span style="color:#484f58;">—</span>':`<span style="color:var(--fg);">${n.toLocaleString()}</span>`;
  };

  if(_ytuTab==='word'){
    let rows=(_ytuData.word_videos||[]);
    if(lang) rows=rows.filter(v=>v.lang===lang);
    if(fmt)  rows=rows.filter(v=>v.fmt===fmt);
    if(status==='pending')  rows=rows.filter(v=>!v.uploaded&&v.file_exists);
    if(status==='uploaded') rows=rows.filter(v=>v.uploaded);
    document.getElementById('ytu-count').textContent=rows.length+'개';
    const tbody=document.getElementById('ytu-word-tbody');
    tbody.innerHTML=rows.map(v=>{
      const flag=_LANG_FLAGS[v.lang]||'';
      const fmtLabel=v.fmt==='reels'?'<span style="color:var(--purple,#a78bfa)">📱 쇼츠</span>':'<span style="color:var(--red)">▶ YouTube</span>';
      const fileIcon=v.file_exists?'<span style="color:var(--green)">●</span>':'<span style="color:var(--red)">✗</span>';
      const statusBadge=v.uploaded?'<span class="badge badge-g" style="font-size:.65rem;">완료</span>':'<span class="badge badge-m" style="font-size:.65rem;">대기</span>';
      const vidLink=v.video_id?`<a href="https://youtube.com/watch?v=${v.video_id}" target="_blank" style="color:var(--muted);font-size:.6rem;margin-left:3px;">↗</a>`:'';
      const btn=v.file_exists
        ?`<button class="btn ${v.uploaded?'btn-r':'btn-g'}" style="font-size:.65rem;padding:2px 8px;" onclick="ytUploadWord(${v.word_id},'${v.lang}','${v.exam}','${v.fmt}',this)">${v.uploaded?'재업로드':'업로드'}</button>`
        :v.uploaded
          ?`<span style="font-size:.65rem;color:var(--muted);">업로드됨</span>`
          :`<span style="font-size:.65rem;color:var(--red);">파일없음</span>`;
      return `<tr>
        <td>${flag} ${v.lang}</td>
        <td style="color:var(--muted);">${v.word_id}</td>
        <td style="font-weight:700;">${v.word}${vidLink}</td>
        <td style="color:var(--muted);font-size:.72rem;">${v.meaning||''}</td>
        <td>Lv.${v.level}</td>
        <td>${fmtLabel}</td>
        <td>${fileIcon}</td>
        <td>${statusBadge}</td>
        <td style="text-align:right;font-size:.75rem;">${_fmtN(v.views,v.stats_error)}</td>
        <td style="text-align:right;font-size:.75rem;">${_fmtN(v.likes,v.stats_error)}</td>
        <td style="text-align:right;font-size:.75rem;">${_fmtN(v.comments,v.stats_error)}</td>
        <td>${btn}</td>
      </tr>`;
    }).join('');
  } else if(_ytuTab==='kdrama'){
    let rows=(_ytuData.kdrama_videos||[]);
    if(lang) rows=rows.filter(v=>v.lang===lang);
    if(fmt)  rows=rows.filter(v=>v.fmt===fmt);
    if(status==='pending')  rows=rows.filter(v=>!v.uploaded&&v.file_exists);
    if(status==='uploaded') rows=rows.filter(v=>v.uploaded);
    document.getElementById('ytu-count').textContent=rows.length+'개';
    const tbody=document.getElementById('ytu-kdrama-tbody');
    tbody.innerHTML=rows.map(v=>{
      const flag=_LANG_FLAGS[v.lang]||'';
      const fmtLabel=v.fmt==='reels'?'<span style="color:var(--purple,#a78bfa)">📱 쇼츠</span>':'<span style="color:var(--red)">▶ YouTube</span>';
      const fileIcon=v.file_exists?'<span style="color:var(--green)">●</span>':'<span style="color:var(--red)">✗</span>';
      const statusBadge=v.uploaded?'<span class="badge badge-g" style="font-size:.65rem;">완료</span>':'<span class="badge badge-m" style="font-size:.65rem;">대기</span>';
      const dt=v.rendered_at?v.rendered_at.substring(0,10):'';
      const vidLink=v.video_id?`<a href="https://youtube.com/watch?v=${v.video_id}" target="_blank" style="color:var(--muted);font-size:.6rem;margin-left:3px;">↗</a>`:'';
      const btn=v.file_exists
        ?`<button class="btn ${v.uploaded?'btn-r':'btn-g'}" style="font-size:.65rem;padding:2px 8px;" onclick="ytUploadKdrama('${v.theme_id}','${v.lang}','${v.fmt}',this)">${v.uploaded?'재업로드':'업로드'}</button>`
        :v.uploaded
          ?`<span style="font-size:.65rem;color:var(--muted);">업로드됨</span>`
          :`<span style="font-size:.65rem;color:var(--red);">파일없음</span>`;
      return `<tr>
        <td>${flag} ${v.lang}</td>
        <td style="font-weight:700;">${v.theme_id}${vidLink}</td>
        <td>${fmtLabel}</td>
        <td>${fileIcon}</td>
        <td>${statusBadge}</td>
        <td style="color:var(--muted);font-size:.72rem;">${dt}</td>
        <td style="text-align:right;font-size:.75rem;">${_fmtN(v.views,v.stats_error)}</td>
        <td style="text-align:right;font-size:.75rem;">${_fmtN(v.likes,v.stats_error)}</td>
        <td style="text-align:right;font-size:.75rem;">${_fmtN(v.comments,v.stats_error)}</td>
        <td>${btn}</td>
      </tr>`;
    }).join('');
  } else {
    let rows=(_ytuData.conv_videos||[]);
    if(lang) rows=rows.filter(v=>v.lang===lang);
    if(fmt)  rows=rows.filter(v=>v.fmt===fmt);
    if(status==='pending')  rows=rows.filter(v=>!v.uploaded&&v.file_exists);
    if(status==='uploaded') rows=rows.filter(v=>v.uploaded);
    document.getElementById('ytu-count').textContent=rows.length+'개';
    const tbody=document.getElementById('ytu-conv-tbody');
    tbody.innerHTML=rows.map(v=>{
      const flag=_LANG_FLAGS[v.lang]||'';
      const fmtLabel=v.fmt==='reels'?'<span style="color:var(--purple,#a78bfa)">📱 쇼츠</span>':'<span style="color:var(--red)">▶ YouTube</span>';
      const fileIcon=v.file_exists?'<span style="color:var(--green)">●</span>':'<span style="color:var(--red)">✗</span>';
      const statusBadge=v.uploaded?'<span class="badge badge-g" style="font-size:.65rem;">완료</span>':'<span class="badge badge-m" style="font-size:.65rem;">대기</span>';
      const dt=v.rendered_at?v.rendered_at.substring(0,10):'';
      const vidLink=v.video_id?`<a href="https://youtube.com/watch?v=${v.video_id}" target="_blank" style="color:var(--muted);font-size:.6rem;margin-left:3px;">↗</a>`:'';
      const btn=v.file_exists
        ?`<button class="btn ${v.uploaded?'btn-r':'btn-g'}" style="font-size:.65rem;padding:2px 8px;" onclick="ytUploadConv('${v.theme_id}','${v.lang}','${v.fmt}',this)">${v.uploaded?'재업로드':'업로드'}</button>`
        :v.uploaded
          ?`<span style="font-size:.65rem;color:var(--muted);">업로드됨</span>`
          :`<span style="font-size:.65rem;color:var(--red);">파일없음</span>`;
      return `<tr>
        <td>${flag} ${v.lang}</td>
        <td style="font-weight:700;">${v.theme_id}${vidLink}</td>
        <td>${fmtLabel}</td>
        <td>${fileIcon}</td>
        <td>${statusBadge}</td>
        <td style="color:var(--muted);font-size:.72rem;">${dt}</td>
        <td style="text-align:right;font-size:.75rem;">${_fmtN(v.views,v.stats_error)}</td>
        <td style="text-align:right;font-size:.75rem;">${_fmtN(v.likes,v.stats_error)}</td>
        <td style="text-align:right;font-size:.75rem;">${_fmtN(v.comments,v.stats_error)}</td>
        <td>${btn}</td>
      </tr>`;
    }).join('');
  }
  if(ld) ld.style.display='none';
}

async function ytUploadWord(wordId, lang, exam, fmt, btnEl){
  if(!confirm(`[${lang}] 단어 #${wordId} (${fmt==='reels'?'쇼츠':'YouTube'}) 업로드할까요?`)) return;
  btnEl.disabled=true; btnEl.textContent='업로드 중...';
  try{
    const r=await fetch('/api/render/upload',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({word_id:wordId,lang,exam,fmt})});
    const d=await r.json();
    if(!r.ok){btnEl.textContent='실패';btnEl.style.color='var(--red)';alert('오류: '+(d.error||''));return;}
    btnEl.textContent='완료';btnEl.style.color='var(--green)';
    setTimeout(()=>loadYtUpload(),1500);
  }catch(e){btnEl.textContent='오류';alert('실패: '+e);}
}

async function ytUploadConv(themeId, lang, fmt, btnEl){
  if(!confirm(`[${lang}] 회화 ${themeId} (${fmt==='reels'?'쇼츠':'YouTube'}) 업로드할까요?`)) return;
  btnEl.disabled=true; btnEl.textContent='업로드 중...';
  try{
    const r=await fetch('/api/conv/upload',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({theme_id:themeId,lang,fmt})});
    const d=await r.json();
    if(!r.ok){btnEl.textContent='실패';btnEl.style.color='var(--red)';alert('오류: '+(d.error||''));return;}
    btnEl.textContent='완료';btnEl.style.color='var(--green)';
    setTimeout(()=>loadYtUpload(),1500);
  }catch(e){btnEl.textContent='오류';alert('실패: '+e);}
}

async function reconcileUploads(){
  if(!confirm('YouTube 채널(5개 언어)을 스캔해 업로드 기록을 복구합니다.\n(읽기 전용, quota ~200 units)\n\n계속할까요?')) return;
  try{
    const r = await fetch('/api/youtube/reconcile',{method:'POST',
      headers:{'Content-Type':'application/json'}, body:'{}'});
    const d = await r.json();
    if(!r.ok||!d.ok){ alert('실패: '+(d.error||'')); return; }
    let lines = [`✅ 복구 완료`,
      `단어: +${d.added_word}`,
      `회화: +${d.added_conv}`,
      `K드라마: +${d.added_kdrama}`,
      `미매칭: ${d.unknown_total}`, ''];
    for(const L of Object.keys(d.per_lang||{})){
      const s = d.per_lang[L];
      if(s.error){ lines.push(`${L}: ❌ ${s.error}`); continue; }
      lines.push(`${L}: 스캔 ${s.scanned} / 단어 +${s.word} / 회화 +${s.conv} / K +${s.kdrama} / 이미기록 ${s.already} / 미매칭 ${s.unknown}`);
    }
    if(d.unknown_samples && Object.keys(d.unknown_samples).length){
      lines.push('', '⚠ 매칭 실패 샘플:');
      for(const L of Object.keys(d.unknown_samples)){
        for(const u of d.unknown_samples[L].slice(0,3)){
          lines.push(`  [${L}/${u.fmt}/${u.dur}s] ${u.title}`);
        }
      }
    }
    if(d.errors?.length) lines.push('', '⚠ 오류: '+d.errors.join(' | '));
    alert(lines.join('\n'));
    loadYtUpload();
  }catch(e){ alert('실패: '+e); }
}

async function ytUploadKdrama(themeId, lang, fmt, btnEl){
  if(!confirm(`[${lang}] K-드라마 ${themeId} (${fmt==='reels'?'쇼츠':'YouTube'}) 업로드할까요?`)) return;
  btnEl.disabled=true; btnEl.textContent='업로드 중...';
  try{
    const r=await fetch('/api/kdrama/upload',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({theme_id:themeId,lang,fmt})});
    const d=await r.json();
    if(!r.ok){btnEl.textContent='실패';btnEl.style.color='var(--red)';alert('오류: '+(d.error||''));return;}
    btnEl.textContent='완료';btnEl.style.color='var(--green)';
    setTimeout(()=>loadYtUpload(),1500);
  }catch(e){btnEl.textContent='오류';alert('실패: '+e);}
}

// ── Instagram ────────────────────────────────────────────────
let _igVids = [];

async function igSaveToken(){
  const token=(document.getElementById('ig-token-input').value||'').trim();
  if(!token){alert('토큰을 입력하세요');return;}
  const r=await fetch('/api/instagram/token',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token})});
  const d=await r.json();
  if(!r.ok){alert('저장 실패: '+(d.error||''));return;}
  igCheckStatus();
}

async function igCheckStatus(){
  try{
    const r=await fetch('/api/instagram/status');
    const d=await r.json();
    const badge=document.getElementById('ig-status-badge');
    const info=document.getElementById('ig-account-info');
    if(d.connected){
      if(badge){badge.textContent='✓ 연결됨';badge.className='badge badge-done';}
      if(info) info.innerHTML=`<b>${d.name||''}</b> <span style="color:var(--muted);">(${d.username||''})</span> · 팔로워 ${d.followers||0}명`;
    } else {
      if(badge){badge.textContent='미연결';badge.className='badge badge-m';}
      if(info) info.textContent='Instagram Business/Creator 계정 연결 후 릴스를 업로드할 수 있습니다.';
    }
  }catch(e){}
}

async function loadIgData(){
  igCheckStatus();
  try{
    const r=await fetch('/api/videos/all');
    const d=await r.json();
    // 쇼츠(reels) 포맷만 - file_size 있고 video_id 없는 것 (미업로드 우선)
    _igVids=(d.video_list||[]).filter(v=>v.file_size>0);
    renderIgList();
  }catch(e){}
}

function renderIgList(){
  const tbody=document.getElementById('ig-tbody');
  const empty=document.getElementById('ig-empty');
  const cnt=document.getElementById('ig-count');
  if(!tbody) return;
  const lang=(document.getElementById('ig-filter-lang')||{}).value||'';
  const st=(document.getElementById('ig-filter-status')||{}).value||'';
  let list=[..._igVids];
  if(lang) list=list.filter(v=>(v.language||'EN')===lang);
  if(st==='uploaded') list=list.filter(v=>v.ig_media_id);
  if(st==='pending') list=list.filter(v=>!v.ig_media_id);
  if(cnt) cnt.textContent=list.length+'개';
  if(!list.length){
    tbody.innerHTML='';
    if(empty) empty.style.display='block';
    return;
  }
  if(empty) empty.style.display='none';
  const LVC2={'1':'#3fb950','2':'#58a6ff','3':'#d29922','4':'#f78166','5':'#bc8cff','6':'#f87171'};
  tbody.innerHTML=list.map(v=>{
    const c=LVC2[v.level]||'#8b949e';
    const igStatus=v.ig_media_id
      ?`<a href="https://www.instagram.com/reel/${v.ig_media_id}" target="_blank" style="color:#e1306c;font-size:.72rem;">▶ 보기</a>`
      :'–';
    const uploadBtn=!v.ig_media_id
      ?`<button onclick="igUpload('${v.word_id}','${v.language||'EN'}')" class="btn btn-m" style="font-size:.65rem;padding:2px 8px;opacity:.6;" title="Meta Developer 앱 설정 후 사용 가능">📸 준비 중</button>`
      :'<span style="font-size:.65rem;color:var(--green);">✓ 완료</span>';
    return `<tr>
      <td style="font-weight:600;">${v.word}</td>
      <td style="color:var(--muted);font-size:.78rem;">${v.meaning}</td>
      <td style="font-size:.72rem;">${LANG_FLAGS[v.language||'EN']||''} ${v.language||'EN'}</td>
      <td><span style="color:${c};font-weight:600;">${v.level}급</span></td>
      <td style="color:var(--muted);font-size:.72rem;">${ago(v.generated_at)}</td>
      <td>${igStatus}</td>
      <td>${uploadBtn}</td>
    </tr>`;
  }).join('');
}

async function igUpload(wordId, lang){
  const r=await fetch('/api/instagram/upload',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({word_id:wordId,lang})});
  const d=await r.json();
  if(!r.ok){alert('업로드 실패: '+(d.error||''));return;}
  alert('업로드 완료!');
  loadIgData();
}

// ── 컨트롤 ───────────────────────────────────────────────────
async function toggleRender(){
  _desktopEnabled=!_desktopEnabled;
  await fetch('/api/render-config/toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({desktop_enabled:_desktopEnabled})});
  loadOverview();
}

async function startRender(wordId=null){
  const btn=document.getElementById('render-now-btn');
  btn.disabled=true;btn.textContent='⏳ 요청 중...';
  try{
    const r=await fetch('/api/render',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(wordId?{word_id:wordId}:{})});
    const d=await r.json();
    if(!r.ok) alert('오류: '+(d.error||'알 수 없음'));
    else loadJobQueue();
  }catch(e){alert('실패: '+e);}
  finally{btn.disabled=false;btn.textContent='▶ 지금 렌더링';loadOverview();}
}

function setIllustRange(s,e){
  document.getElementById('illust-start').value=s;
  document.getElementById('illust-end').value=e;
  updateIllustCost();
}
function setIllustRange2(s,e){
  document.getElementById('illust-start2').value=s;
  document.getElementById('illust-end2').value=e;
  updateIllustCost2();
}

function _illustCost(n,mode){
  if(mode==='words') return {cnt:n, txt:`단어 ${n}장 / 약 $${(n*0.02).toFixed(2)}`};
  if(mode==='sentences') return {cnt:n*10, txt:`예문 ~${n*10}장 / 약 $${(n*10*0.02).toFixed(2)}`};
  return {cnt:n*11, txt:`~${n*11}장 (단어 ${n} + 예문 ~${n*10}) / 약 $${(n*11*0.02).toFixed(2)}`};
}
function updateIllustCost(){
  const n=Math.max(0,(+document.getElementById('illust-end').value||1)-(+document.getElementById('illust-start').value||1)+1);
  const m=document.getElementById('illust-mode').value;
  setEl('illust-cost',_illustCost(n,m).txt);
}
function updateIllustCost2(){
  const n=Math.max(0,(+document.getElementById('illust-end2').value||1)-(+document.getElementById('illust-start2').value||1)+1);
  const m=document.getElementById('illust-mode2').value;
  setEl('illust-cost2',_illustCost(n,m).txt);
}
document.getElementById('illust-start').addEventListener('input',updateIllustCost);
document.getElementById('illust-end').addEventListener('input',updateIllustCost);
document.getElementById('illust-start2').addEventListener('input',updateIllustCost2);
document.getElementById('illust-end2').addEventListener('input',updateIllustCost2);

let _illustTarget = 'nas';
function setIllustTarget(t){
  _illustTarget = t;
  const _inN=document.getElementById('illust-target-nas'),_inD=document.getElementById('illust-target-desktop');
  if(_inN){_inN.className='btn '+(t==='nas'?'btn-p active':'btn-m');_inN.style.fontSize='.72rem';_inN.style.padding='3px 10px';}
  if(_inD){_inD.className='btn '+(t==='desktop'?'btn-p active':'btn-m');_inD.style.fontSize='.72rem';_inD.style.padding='3px 10px';}
}

async function _startIllust(start,end,mode){
  const btn=document.getElementById('illust-gen-btn2');
  const cost2=document.getElementById('illust-cost2');
  if(btn){btn.disabled=true;btn.textContent='⏳ 요청 중...';}
  try{
    const r=await fetch('/api/illustrations/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({start,end,mode,target:_illustTarget})});
    const d=await r.json();
    if(!r.ok){
      if(cost2){cost2.textContent='오류: '+(d.error||'알 수 없음');cost2.style.color='#f87171';}
      if(btn){btn.disabled=false;btn.textContent='🎨 생성';}
    } else {
      setTimeout(()=>{loadOverview();loadJobQueue();}, 500);
    }
  }catch(e){
    if(cost2){cost2.textContent='연결 오류: '+e.message;cost2.style.color='#f87171';}
    if(btn){btn.disabled=false;btn.textContent='🎨 생성';}
  }
}
async function startIllustGen(){ await _startIllust(+document.getElementById('illust-start').value||1,+document.getElementById('illust-end').value||10,document.getElementById('illust-mode').value); }
async function startIllustGen2(){ await _startIllust(+document.getElementById('illust-start2').value||1,+document.getElementById('illust-end2').value||100,document.getElementById('illust-mode2').value); }

async function cancelIllustGen(){
  const r = await fetch('/api/illustrations/cancel', {method:'POST'});
  const d = await r.json();
  if(!r.ok) alert('취소 실패: '+(d.error||'알 수 없음'));
  else { setEl('illust-cancel-btn2',''); loadOverview(); }
}

function _updateIllustButtons(status){
  const running = status === 'running';
  const genBtn = document.getElementById('illust-gen-btn2');
  const cancelBtn = document.getElementById('illust-cancel-btn2');
  const resetBtn = document.getElementById('illust-reset-btn2');
  if(genBtn) genBtn.style.display = running ? 'none' : '';
  if(cancelBtn) cancelBtn.style.display = running ? '' : 'none';
  if(resetBtn) resetBtn.style.display = running ? '' : 'none';
}

async function resetIllustProgress(){
  await fetch('/api/illustrations/reset',{method:'POST'});
  loadOverview();
}

// ── 일러스트 브라우저 ────────────────────────────────────
let _illustBrowseData=null;
let _regenPoll=null;

async function loadIllustBrowse(){
  const id=+document.getElementById('illust-browse-id').value||1;
  const lv=document.getElementById('illust-browse-level').value||1;
  const r=await fetch('/api/illustrations/word/'+id+'?level='+lv);
  if(!r.ok){document.getElementById('illust-browse-info').textContent='단어 없음';document.getElementById('illust-browse-grid').innerHTML='';return;}
  const d=await r.json();
  _illustBrowseData=d;
  const c=LVC[d.level]||'#8b949e';
  document.getElementById('illust-browse-info').innerHTML=`<span style="color:${c}">${d.level}급</span> <b>${d.word}</b> — ${d.meaning}`;
  const grid=document.getElementById('illust-browse-grid');
  const ts=Date.now();
  grid.innerHTML=d.items.map(it=>{
    const label=it.type==='word'?'단어 이미지':`예문 ${it.idx+1}`;
    const sub=it.type==='sentence'?`<div style="font-size:.6rem;color:var(--muted);margin-top:2px;margin-bottom:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${(it.ko||'')}">${it.ko||''}</div>`:'';
    const img=it.exists
      ?`<img src="${it.url}?t=${ts}" style="width:100%;aspect-ratio:1;object-fit:cover;border-radius:6px;cursor:pointer;" onclick="illustPreview('${it.url}?t=${ts}')">`
      :`<div style="width:100%;aspect-ratio:1;background:var(--bg);border-radius:6px;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:.7rem;">미생성</div>`;
    const key=it.type==='word'?'w':it.idx;
    const btnId=`regen-btn-${key}`;
    const notesId=`regen-notes-${key}`;
    const wrapId=`regen-img-wrap-${key}`;
    const genOvId=`illust-gen-overlay-${key}`;
    const delBtn=it.exists?`<button onclick="deleteWordIllust(${d.word_id},${d.level},${it.idx})" class="btn btn-r" style="margin-top:3px;font-size:.65rem;width:100%;padding:3px 0;background:var(--red);color:#fff;">🗑 삭제</button>`:'';
    return `<div id="illust-card-${key}" style="background:var(--bg3);border-radius:8px;padding:8px;text-align:center;transition:box-shadow .3s,outline .3s;">
      <div style="font-size:.7rem;font-weight:600;margin-bottom:4px;">${label}</div>
      <div id="${wrapId}" style="position:relative;">
        ${img}${sub}
        <div id="${genOvId}" style="display:none;position:absolute;inset:0;border-radius:6px;
          flex-direction:column;align-items:center;justify-content:center;gap:5px;
          background:rgba(0,0,0,.55);backdrop-filter:blur(2px);">
          <div style="width:24px;height:24px;border:3px solid rgba(255,255,255,.3);border-top-color:#a78bfa;border-radius:50%;animation:spin 1s linear infinite;"></div>
          <span style="font-size:.58rem;color:#e2e8f0;font-weight:600;">생성 중...</span>
        </div>
      </div>
      <button id="${btnId}" onclick="regenIllust(${d.word_id},${it.idx},'${notesId}')" class="btn btn-m" style="font-size:.65rem;width:100%;padding:3px 0;margin-top:6px;">🔄 재생성</button>
      ${delBtn}
      <textarea id="${notesId}" placeholder="수정 요청 (예: 카페 말고 마트로, 문 닫힌 모습 강조...)" rows="2" style="width:100%;margin-top:4px;padding:4px 6px;font-size:.62rem;background:var(--bg);color:var(--fg);border:1px solid var(--border);border-radius:5px;resize:vertical;box-sizing:border-box;"></textarea>
    </div>`;
  }).join('');

  // 단어 일러스트 실시간 오버레이 폴링 시작
  _startIllustPanelPoll(d.word_id);
}

// ── 단어 일러스트 실시간 오버레이 폴링 ──────────────────────────
let _illustPanelPollTimer = null;
let _illustPanelWordId    = null;

function _startIllustPanelPoll(wordId){
  _illustPanelWordId = wordId;
  if(_illustPanelPollTimer) clearInterval(_illustPanelPollTimer);
  _applyIllustPanelStatus();   // 즉시 1회
  _illustPanelPollTimer = setInterval(_applyIllustPanelStatus, 2000);
}

async function _applyIllustPanelStatus(){
  let data;
  try{
    const r=await fetch('/api/illustrations/live-status');
    if(!r.ok) return;
    data=await r.json();
  }catch(e){ return; }

  if(data.status !== 'running'){
    // 생성 끝 → 모든 오버레이 숨기기
    document.querySelectorAll('[id^="illust-gen-overlay-"]').forEach(ov=>{
      ov.style.display='none';
      const key=ov.id.replace('illust-gen-overlay-','');
      const card=document.getElementById('illust-card-'+key);
      if(card){ card.style.boxShadow=''; card.style.outline=''; }
    });
    if(_illustPanelPollTimer){ clearInterval(_illustPanelPollTimer); _illustPanelPollTimer=null; }
    return;
  }

  const curWordId   = data.current_word_id;
  const curType     = data.current_type;    // 'word' | 'sent'
  const curSentIdx  = data.current_sent_idx;

  // 현재 보고 있는 단어가 생성 중인 단어와 다르면 오버레이 없음
  const isMyWord = (curWordId === _illustPanelWordId);

  document.querySelectorAll('[id^="illust-gen-overlay-"]').forEach(ov=>{
    const key=ov.id.replace('illust-gen-overlay-','');
    const card=document.getElementById('illust-card-'+key);
    let active=false;
    if(isMyWord){
      if(key==='w' && curType==='word') active=true;
      else if(key!=='w' && curType==='sent' && +key===curSentIdx) active=true;
    }
    ov.style.display = active ? 'flex' : 'none';
    if(card){
      card.style.boxShadow = active ? '0 0 0 2px #a78bfa' : '';
      card.style.outline   = '';
    }
  });
}

async function deleteWordIllust(wordId,level,idx){
  const label=idx<0?'단어 이미지':`예문 ${idx+1}`;
  if(!confirm(`"${label}" 이미지를 삭제할까요?`))return;
  const r=await fetch('/api/illustrations/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({word_id:wordId,level:level,idx:idx})});
  const d=await r.json();
  if(!r.ok){alert('삭제 실패: '+(d.error||''));return;}
  const wrapKey=idx<0?'w':idx;
  const wrap=document.getElementById(`regen-img-wrap-${wrapKey}`);
  if(wrap){
    const img=wrap.querySelector('img');
    if(img) img.replaceWith(Object.assign(document.createElement('div'),{
      style:'width:100%;aspect-ratio:1;background:var(--bg);border-radius:6px;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:.7rem;',
      textContent:'미생성'
    }));
  }
}

// 등급별 전체 ID 범위 (1급:1~300, 2급:301~600 ... 6급:1501~1800)
function lvIdRange(lv){
  const n=+lv;
  return {min:(n-1)*300+1, max:n*300};
}

function onIllustLevelChange(){
  const lv=+document.getElementById('illust-browse-level').value||1;
  const {min,max}=lvIdRange(lv);
  const inp=document.getElementById('illust-browse-id');
  inp.min=min; inp.max=max; inp.value=min;
  const hint=document.getElementById('illust-browse-id-range');
  if(hint) hint.textContent=`(${min}~${max})`;
  loadIllustBrowse();
}

function illustBrowseNav(dir){
  const lv=+document.getElementById('illust-browse-level').value||1;
  const {min,max}=lvIdRange(lv);
  const inp=document.getElementById('illust-browse-id');
  inp.value=Math.min(max,Math.max(min,(+inp.value||min)+dir));
  loadIllustBrowse();
}

function illustPreview(url){
  const overlay=document.createElement('div');
  overlay.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.85);display:flex;align-items:center;justify-content:center;z-index:9999;cursor:pointer;';
  overlay.onclick=()=>overlay.remove();
  overlay.innerHTML=`<img src="${url}" style="max-width:90vw;max-height:90vh;border-radius:12px;">`;
  document.body.appendChild(overlay);
}

async function regenIllust(wordId,idx,notesId){
  const label=idx<0?'단어 이미지':`예문[${idx+1}]`;
  const btnId=idx<0?'regen-btn-w':`regen-btn-${idx}`;
  const btn=document.getElementById(btnId);
  const notesEl=notesId?document.getElementById(notesId):null;
  const notes=notesEl?notesEl.value.trim():'';
  if(btn){btn.disabled=true;btn.textContent='⏳ 생성 중...';}
  const st=document.getElementById('illust-regen-status');
  st.style.display='block';
  st.textContent=notes?`🔄 ${label} 수정 반영 재생성 중...`:`🔄 ${label} 재생성 중...`;
  const r=await fetch('/api/illustrations/regen',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({word_id:wordId,idx:idx,notes:notes})});
  const d=await r.json();
  if(!r.ok){st.textContent='오류: '+(d.error||'');if(btn){btn.disabled=false;btn.textContent='🔄 재생성';}return;}
  // 이미지 카드 위에 진행 오버레이 표시
  const key=idx<0?'w':idx;
  const wrap=document.getElementById(`regen-img-wrap-${key}`);
  if(wrap){
    const ov=document.createElement('div');
    ov.className='regen-overlay';
    ov.innerHTML=`<div class="regen-spinner"></div>
      <div style="font-size:.7rem;color:#fff;font-weight:600;">생성 중...</div>
      <div class="regen-bar-wrap"><div class="regen-bar"></div></div>`;
    wrap.appendChild(ov);
  }
  // 폴링: 완료 대기 + 실패 감지
  const _regenLv=document.getElementById('illust-browse-level').value||1;
  if(_regenPoll)clearInterval(_regenPoll);
  let _regenPollCount=0;
  _regenPoll=setInterval(async()=>{
    _regenPollCount++;
    // 매 5회(10초)마다 서버 상태도 확인
    if(_regenPollCount%5===0){
      try{
        const logR=await fetch(`/api/illustrations/regen/log?word_id=${wordId}&idx=${idx}`);
        if(logR.ok){
          const logD=await logR.json();
          if(logD.status==='failed'||logD.status==='error'||logD.status==='timeout'){
            clearInterval(_regenPoll);_regenPoll=null;
            const errRaw=logD.error||logD.log||'알 수 없는 오류';
            // 파이썬 에러는 스택 끝에 있으므로 뒤에서 자름
            const errMsg=errRaw.slice(-400);
            st.style.color='var(--red)';
            st.textContent=`❌ 재생성 실패: ${errMsg}`;
            const wrapE=document.getElementById(`regen-img-wrap-${key}`);
            if(wrapE){const ovE=wrapE.querySelector('.regen-overlay');if(ovE)ovE.remove();}
            if(btn){btn.disabled=false;btn.textContent='🔄 재생성';}
            return;
          }
        }
      }catch(e){}
    }
    const cr=await fetch('/api/illustrations/word/'+wordId+'?level='+_regenLv);
    if(!cr.ok)return;
    const cd=await cr.json();
    const item=cd.items.find(i=>i.idx===idx);
    if(item&&item.exists){
      clearInterval(_regenPoll);_regenPoll=null;
      st.style.color='';
      st.textContent=`✅ ${label} 재생성 완료!`;
      setTimeout(()=>{st.style.display='none';},3000);
      // 오버레이 제거 후 새로고침
      const wrap2=document.getElementById(`regen-img-wrap-${key}`);
      if(wrap2){const ov2=wrap2.querySelector('.regen-overlay');if(ov2)ov2.remove();}
      loadIllustBrowse();
      loadOverview();
    }
  },2000);
  // 타임아웃 10분
  setTimeout(async()=>{
    if(!_regenPoll)return;
    clearInterval(_regenPoll);_regenPoll=null;
    // 마지막으로 서버 로그 확인
    let errDetail='';
    try{
      const logR=await fetch(`/api/illustrations/regen/log?word_id=${wordId}&idx=${idx}`);
      if(logR.ok){const logD=await logR.json();errDetail=logD.error||logD.log||'';}
    }catch(e){}
    st.style.color='var(--red)';
    st.textContent=`⚠ 시간 초과${errDetail?' — '+errDetail.slice(-150):''}`;
    const wrap3=document.getElementById(`regen-img-wrap-${key}`);
    if(wrap3){const ov3=wrap3.querySelector('.regen-overlay');if(ov3)ov3.remove();}
    if(btn){btn.disabled=false;btn.textContent='🔄 재생성';}
  },600000);
}

// ── 일별 자동 시스템 ────────────────────────────────────────
const _DAILY_FLAG={'EN':'🇺🇸','CN':'🇹🇼','JP':'🇯🇵','VN':'🇻🇳','ES':'🇲🇽'};
const _DAILY_NAME={'EN':'English','CN':'中文','JP':'日本語','VN':'Tiếng Việt','ES':'Español'};
let _dailyPollTimer=null;

// ── pill 그룹 유틸 ────────────────────────────────────────────
function _activatePill(groupId, value, cls='on'){
  const g=document.getElementById(groupId);
  if(!g)return;
  g.querySelectorAll('.pill').forEach(p=>{
    p.classList.remove('on','on-green');
    if(p.dataset.v===value) p.classList.add(cls);
  });
}

async function setBatchPill(groupId, btn, key){
  const v=btn.dataset.v;
  _activatePill(groupId,v);
  await saveBatchConfig({[key]:v});
}

async function saveBatchConfig(patch){
  await fetch('/api/daily/config',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify(patch)});
}

async function saveEpStart(){
  const g=id=>{ const e=document.getElementById(id); return e?parseInt(e.value)||1:1; };
  await saveBatchConfig({
    ep_word_yt_start:    g('wc-ep-word-yt'),
    ep_word_reels_start: g('wc-ep-word-reels'),
    ep_conv_yt_start:    g('wc-ep-conv-yt'),
    ep_conv_reels_start: g('wc-ep-conv-reels'),
  });
  _updateScheduleStatus();
}

// 기준일·주기·시작화수로 오늘의 화수 계산
function calcTodayEp(startDate, startEp, freqKey, today){
  if(!startDate||!startEp) return null;
  const _int={'daily':1,'every2days':2,'every3days':3,'2perday':1,'3perday':1};
  const _cnt={'daily':1,'every2days':1,'every3days':1,'2perday':2,'3perday':3};
  const interval=_int[freqKey]||1, perDay=_cnt[freqKey]||1;
  const d0=new Date(startDate), dt=new Date(today||new Date().toISOString().slice(0,10));
  const diff=Math.round((dt-d0)/(1000*86400));
  if(diff<0) return startEp;
  const episodes=Math.floor(diff/interval)*perDay;
  return startEp+episodes;
}

// ── 자동 설명 텍스트 업데이트 ─────────────────────────────────
const _FREQ_LABEL={'daily':'매일','every2days':'이틀에 1개','every3days':'삼일에 1개',
                   '2perday':'하루 2개','3perday':'하루 3개'};
function _updateAutoDesc(s){
  const wf=_FREQ_LABEL[s.word_freq||'daily']||'매일';
  const pf=_FREQ_LABEL[s.phrase_freq||'every2days']||'이틀에 1개';
  const txt=`단어 ${wf} · 회화 ${pf} · 5개 언어 · 현지 아침 7:30`;
  ['daily-auto-desc','wc-auto-desc'].forEach(id=>{
    const el=document.getElementById(id); if(el) el.textContent=txt;
  });
}

function _updateScheduleStatus(s){
  s=s||{};
  const sd=document.getElementById('auto-start-date');
  const startDate=(sd&&sd.value)||s.auto_start_date||'';
  const statusEl=document.getElementById('daily-schedule-status');
  const descEl=document.getElementById('daily-schedule-desc');
  if(!startDate){
    if(statusEl) statusEl.textContent='기준일 미설정';
    if(descEl) descEl.textContent='기준일을 설정하면 단어·회화 각각의 빈도 설정에 따라 자동 스케줄이 계산됩니다.';
    return;
  }
  const today=new Date().toISOString().slice(0,10);
  const wf=s.word_freq||'daily';
  const pf=s.phrase_freq||'every2days';
  const _wint={'daily':1,'every2days':2,'every3days':3,'2perday':1,'3perday':1};
  const _wcnt={'daily':1,'every2days':1,'every3days':1,'2perday':2,'3perday':3};
  const _pint={'daily':1,'every2days':2,'every3days':3};
  const wi=_wint[wf]||1, wc=_wcnt[wf]||1, pi=_pint[pf]||2;
  // 오늘이 단어/회화 실행일인지 계산
  const d0=new Date(startDate), dt=new Date(today);
  const diff=Math.round((dt-d0)/(1000*86400));
  const wordRuns= diff>=0 && diff%wi===0;
  const phraseRuns= diff>=0 && diff%pi===0;
  const isAfterStart= dt>=d0;
  if(statusEl){
    if(!isAfterStart) statusEl.innerHTML=`<span style="color:var(--amber);">⏳ ${startDate} 대기 중</span>`;
    else statusEl.innerHTML=`<span style="color:var(--green);">● 진행 중 (D+${diff})</span>`;
  }
  if(descEl){
    const wNext=wordRuns?'오늘':_nextRunDate(startDate,wi,today);
    const pNext=phraseRuns?'오늘':_nextRunDate(startDate,pi,today);
    descEl.innerHTML=`단어: <b style="color:var(--blue);">${_FREQ_LABEL[wf]||wf}</b> ${wc>1?wc+'개':'1개'}/일 — 다음 실행 <b>${wNext}</b><br>`+
      `회화: <b style="color:var(--green);">${_FREQ_LABEL[pf]||pf}</b> — 다음 실행 <b>${pNext}</b>`;
  }
  // 오늘 화수 표시
  const getEpVal=(domId, stateKey)=>{
    const e=document.getElementById(domId); const fromDom=e?parseInt(e.value):NaN;
    return isNaN(fromDom)?((s&&s[stateKey])||1):fromDom;
  };
  const setEpLabel=(labelId, ep)=>{
    const el=document.getElementById(labelId);
    if(el) el.textContent = (ep!=null&&startDate) ? `→ 오늘 #${String(ep).padStart(3,'0')}` : '';
  };
  setEpLabel('wc-ep-word-yt-today',    calcTodayEp(startDate, getEpVal('wc-ep-word-yt','ep_word_yt_start'),       wf, today));
  setEpLabel('wc-ep-word-reels-today', calcTodayEp(startDate, getEpVal('wc-ep-word-reels','ep_word_reels_start'), wf, today));
  setEpLabel('wc-ep-conv-yt-today',    calcTodayEp(startDate, getEpVal('wc-ep-conv-yt','ep_conv_yt_start'),       pf, today));
  setEpLabel('wc-ep-conv-reels-today', calcTodayEp(startDate, getEpVal('wc-ep-conv-reels','ep_conv_reels_start'), pf, today));
}

function _nextRunDate(startDate, interval, today){
  try{
    const d0=new Date(startDate), dt=new Date(today);
    const diff=Math.round((dt-d0)/(1000*86400));
    const rem=diff%interval;
    const daysLeft=rem===0?0:(interval-rem);
    if(daysLeft===0) return '오늘';
    const next=new Date(dt); next.setDate(next.getDate()+daysLeft);
    return next.toISOString().slice(5,10); // MM-DD
  }catch(e){return '?';}
}

async function loadDailyStatus(){
  const r=await fetch('/api/daily/status');
  if(!r.ok)return;
  const d=await r.json();
  const s=d.state||{};
  const w=d.word;

  // 토글 상태 (daily- 및 wc- 두 패널 동기화)
  const _syncToggle=(togId,sliderId,knobId)=>{
    const tog=document.getElementById(togId);
    const slider=document.getElementById(sliderId);
    const knob=document.getElementById(knobId);
    if(tog){ tog.checked=!!s.auto_upload; }
    if(slider) slider.style.background=s.auto_upload?'var(--green)':'#444';
    if(knob) knob.style.left=s.auto_upload?'27px':'3px';
  };
  _syncToggle('daily-auto-toggle','daily-toggle-slider','daily-toggle-knob');
  _syncToggle('wc-auto-toggle','wc-toggle-slider','wc-toggle-knob');

  // 오늘의 단어
  document.getElementById('daily-word-ko').textContent=w?w.word:'—';
  document.getElementById('daily-word-meaning').textContent=w?('= '+w.meaning):'';
  const inp=document.getElementById('daily-word-id-input');
  if(inp&&s.current_word_id)inp.value=s.current_word_id;

  // Lv1 진행
  const done=s.current_word_id||0;
  document.getElementById('daily-lv1-progress').textContent=`진행 ${done} / ${d.lv1_total||300} (Lv1)`;

  // 일러스트 배지
  const ibadge=document.getElementById('daily-illust-badge');
  if(ibadge){
    if(s.illust_done)
      ibadge.innerHTML=`<span style="color:var(--green);font-weight:700;">✓ 일러스트</span>`;
    else if(d.illust_generating)
      ibadge.innerHTML=`<span style="color:var(--amber);">⏳ 일러스트 생성 중...</span>`;
    else
      ibadge.innerHTML='';
  }

  // 언어별 상태 테이블 (단어)
  const tbody=document.getElementById('daily-lang-tbody');
  const stCell=(ok,rendering)=>ok
    ?`<span style="color:var(--green);font-weight:700;">✓</span>`
    :(rendering?`<span style="color:var(--amber);">⏳</span>`:`<span style="color:var(--muted2);">○</span>`);
  const rows=_DAILY_LANGS.map(lg=>{
    const ls=(s.langs||{})[lg]||{};
    const ytOk=ls.youtube_rendered,rlOk=ls.reels_rendered;
    const ytUp=ls.youtube_uploaded;
    const isRend=d.rendering;
    const vidLink=ls.youtube_video_id?`<a href="https://youtube.com/watch?v=${ls.youtube_video_id}" target="_blank" style="color:var(--green);font-size:.62rem;">▶</a>`:'';
    const rlLink=ls.reels_video_id?`<a href="https://youtube.com/watch?v=${ls.reels_video_id}" target="_blank" style="color:var(--green);font-size:.62rem;">▶</a>`:'';
    const uplCell=ytUp
      ?`<span style="color:var(--green);font-weight:700;">✓</span> ${vidLink}${rlLink}`
      :`<span style="color:var(--muted2);">○</span>`;
    const schedCell=`<span style="font-size:.62rem;color:var(--muted2);">${ls.publish_local||ls.publish_at||'—'}</span>`;
    // 업로드 버튼: 렌더링됐지만 아직 미업로드 시
    const canUpload=(ytOk||rlOk)&&!ytUp;
    const fmts=[];
    if(ytOk&&!ls.youtube_uploaded) fmts.push('youtube');
    if(rlOk&&!ls.reels_uploaded) fmts.push('reels');
    const uploadBtn=canUpload
      ?`<button onclick="dailyUploadLang('${lg}',${JSON.stringify(fmts)},this)" class="btn btn-g" style="font-size:.6rem;padding:2px 7px;">업로드</button>`
      :(ytUp?`<span style="font-size:.6rem;color:var(--muted);">완료</span>`:'');
    return `<tr>
      <td>${_DAILY_FLAG[lg]||''} ${_DAILY_NAME[lg]||lg}</td>
      <td style="text-align:center;">${stCell(ytOk,isRend)}</td>
      <td style="text-align:center;">${stCell(rlOk,isRend)}</td>
      <td style="text-align:center;">${uplCell}</td>
      <td>${schedCell}</td>
      <td style="text-align:center;">${uploadBtn}</td>
    </tr>`;
  }).join('');
  tbody.innerHTML=rows;

  // 렌더링 상태
  const rs=document.getElementById('daily-render-status');
  if(d.rendering){rs.style.display='block';rs.textContent='⏳ 단어 렌더링 중...';}
  else rs.style.display='none';

  // ── 설정 pill 동기화 (첫 로드 시 한 번만) ──
  if(!loadDailyStatus._pillsInit){
    loadDailyStatus._pillsInit=true;
    _activatePill('word-freq-group',    s.word_freq||'daily');
    _activatePill('word-render-group',  s.word_render||'auto');
    _activatePill('word-illust-group',  s.word_illust||'auto');
    _activatePill('phrase-freq-group',  s.phrase_freq||'every2days');
    _activatePill('phrase-render-group',s.phrase_render||'auto');
    _activatePill('phrase-illust-group',s.phrase_illust||'auto');
    const pb=document.getElementById('phrase-prebuf-h');
    if(pb&&s.phrase_prebuffer_h) pb.value=s.phrase_prebuffer_h;
    const wb=document.getElementById('word-prebuf-h');
    if(wb&&s.word_prebuffer_h) wb.value=s.word_prebuffer_h;
    const sd=document.getElementById('auto-start-date');
    if(sd&&s.auto_start_date) sd.value=s.auto_start_date;
    // wc- 패널 기준일 동기화
    const wsd=document.getElementById('wc-start-date');
    if(wsd&&s.auto_start_date) wsd.value=s.auto_start_date;
    // 기준 화수 동기화
    const setEpInp=(id,val)=>{const e=document.getElementById(id);if(e&&val)e.value=val;};
    setEpInp('wc-ep-word-yt',    s.ep_word_yt_start);
    setEpInp('wc-ep-word-reels', s.ep_word_reels_start);
    setEpInp('wc-ep-conv-yt',    s.ep_conv_yt_start);
    setEpInp('wc-ep-conv-reels', s.ep_conv_reels_start);
    // wc- pill 동기화
    _activatePill('wc-word-freq-group',   s.word_freq||'daily');
    _activatePill('wc-phrase-freq-group', s.phrase_freq||'every2days');
    _updateScheduleStatus(s);
  }

  // ── 회화 다음 예정 배지 ──
  const pnb=document.getElementById('daily-phrase-next-badge');
  if(pnb){
    if(s.phrase_due) pnb.innerHTML=`<span style="color:var(--amber);">● 오늘 예정</span>`;
    else if(s.phrase_last_date) pnb.textContent=`마지막: ${s.phrase_last_date}`;
    else pnb.textContent='';
  }

  // ── 자동 설명 업데이트 ──
  _updateAutoDesc(s);
  _updateScheduleStatus(s);
}

const _DAILY_LANGS=['EN','CN','JP','VN','ES'];

async function dailyUploadLang(lang, fmts, btnEl){
  if(!confirm(`[${lang}] ${fmts.join('+')} 업로드할까요?`)) return;
  if(btnEl){btnEl.disabled=true; btnEl.textContent='업로드 중...';}
  try{
    const r=await fetch('/api/daily/upload-lang',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({lang, fmts: fmts||['youtube','reels']})});
    const d=await r.json();
    if(!r.ok){alert('오류: '+(d.error||''));if(btnEl){btnEl.disabled=false;btnEl.textContent='업로드';}return;}
    if(btnEl){btnEl.textContent='완료';btnEl.style.color='var(--green)';}
    setTimeout(()=>loadDailyStatus(),3000);
  }catch(e){alert('실패: '+e);if(btnEl){btnEl.disabled=false;btnEl.textContent='업로드';}}
}

async function dailyUploadAll(){
  const s=(_batchData||{}).status||{};
  const langs=_DAILY_LANGS.filter(lg=>{
    const ls=(s.langs||{})[lg]||{};
    return (ls.youtube_rendered||ls.reels_rendered)&&!ls.youtube_uploaded;
  });
  if(!langs.length){alert('업로드할 영상이 없습니다.');return;}
  if(!confirm(`${langs.join(', ')} (${langs.length}개 언어) 전체 업로드할까요?`)) return;
  const btn=document.getElementById('rp-upload-all-btn');
  if(btn){btn.disabled=true;btn.textContent='업로드 중...';}
  for(const lang of langs){
    const ls=(s.langs||{})[lang]||{};
    const fmts=[];
    if(ls.youtube_rendered&&!ls.youtube_uploaded) fmts.push('youtube');
    if(ls.reels_rendered&&!ls.reels_uploaded) fmts.push('reels');
    if(!fmts.length) continue;
    await fetch('/api/daily/upload-lang',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({lang,fmts})});
  }
  if(btn){btn.disabled=false;btn.textContent='⬆ 전체 업로드';}
  setTimeout(()=>loadDailyStatus(),3000);
}

async function setDailyAuto(on){
  const slider=document.getElementById('daily-toggle-slider');
  const knob=document.getElementById('daily-toggle-knob');
  slider.style.background=on?'var(--green)':'#444';
  knob.style.left=on?'27px':'3px';
  await saveBatchConfig({auto_upload:on});
  loadDailyStatus();
}

async function dailyTrigger(){
  await fetch('/api/daily/trigger',{method:'POST'});
  setTimeout(loadDailyStatus,1000);
}

async function dailySetWord(){
  const v=parseInt(document.getElementById('daily-word-id-input').value);
  if(!v||v<1||v>300){alert('1~300 사이 ID를 입력하세요');return;}
  await fetch('/api/daily/set-word',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({word_id:v})});
  loadDailyStatus();
}

async function uploadPhraseToday(){
  const btn=event.target;
  btn.disabled=true;btn.textContent='⏳ 업로드 중...';
  try{
    await fetch('/api/daily/trigger',{method:'POST'});
    setTimeout(()=>{loadDailyStatus();btn.disabled=false;btn.textContent='⬆ 회화 업로드';},1500);
  }catch(e){btn.disabled=false;btn.textContent='⬆ 회화 업로드';}
}

// 배치 탭 열릴 때 폴링 시작
function _startDailyPoll(){
  loadDailyStatus._pillsInit=false; // 탭 열릴 때마다 pill 재동기화
  loadDailyStatus();
  if(_dailyPollTimer)clearInterval(_dailyPollTimer);
  _dailyPollTimer=setInterval(loadDailyStatus,5000);
}
function _stopDailyPoll(){
  if(_dailyPollTimer){clearInterval(_dailyPollTimer);_dailyPollTimer=null;}
}

// ── 스타일 감사 ────────────────────────────────────────────
let _auditData=null;
async function runStyleAudit(){
  const raw=document.getElementById('audit-ids').value.trim();
  if(!raw){alert('감사할 단어 ID를 입력하세요 (예: 1,2,3)');return;}
  const ids=raw.split(',').map(s=>parseInt(s.trim())).filter(n=>!isNaN(n));
  if(!ids.length){alert('유효한 ID가 없습니다');return;}
  const btn=document.getElementById('audit-run-btn');
  btn.disabled=true;btn.textContent='⏳ 감사 중...';
  const st=document.getElementById('audit-status');
  st.style.display='block';st.textContent=`🔍 ${ids.length}개 이미지 감사 중... (Gemini Vision 분석)`;
  const r=await fetch('/api/illustrations/audit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({word_ids:ids})});
  const d=await r.json();
  if(!r.ok){st.textContent='오류: '+(d.error||'');btn.disabled=false;btn.textContent='🔍 감사 시작';return;}
  // 폴링
  const poll=setInterval(async()=>{
    const cr=await fetch('/api/illustrations/audit/results');
    if(!cr.ok)return;
    const cd=await cr.json();
    if(!cd.running){
      clearInterval(poll);
      btn.disabled=false;btn.textContent='🔍 감사 시작';
      st.style.display='none';
      _renderAuditResults(cd);
    }
  },2000);
}
async function loadAuditResults(){
  const r=await fetch('/api/illustrations/audit/results');
  if(!r.ok){alert('감사 결과 없음 — 먼저 감사를 실행하세요');return;}
  _renderAuditResults(await r.json());
}
function _renderAuditResults(d){
  _auditData=d;
  const summary=document.getElementById('audit-summary');
  const total=(d.pass||0)+(d.fail||0)+(d.skip||0);
  const passRate=total>0?Math.round((d.pass||0)/total*100):0;
  const color=(d.fail||0)===0?'var(--green)':(d.fail||0)>total*0.3?'var(--red)':'var(--amber)';
  summary.style.display='block';
  summary.innerHTML=`<span style="color:${color};font-weight:700;">통과 ${d.pass||0} / 실패 ${d.fail||0} / 스킵 ${d.skip||0}</span>`+
    ` <span style="color:var(--muted);">(통과율 ${passRate}%)</span>`+
    (d.audited_at?` <span style="color:var(--muted2);font-size:.68rem;">${d.audited_at.slice(0,16)}</span>`:'');
  // 실패 항목 있으면 재생성 버튼 표시
  const actions=document.getElementById('audit-regen-actions');
  if((d.fail||0)>0){actions.style.display='flex';}else{actions.style.display='none';}
  const tbody=document.getElementById('audit-tbody');
  // 문제 유형별 뱃지 색상
  const _tagColor={
    text:'#f87171', proportion:'#fb923c', scale:'#fb923c',
    perspective:'#60a5fa', style:'#a78bfa', palette:'#a78bfa',
    anatomy:'#f43f5e', physics:'#f43f5e',
  };
  const _tagLabel={
    text:'텍스트', proportion:'비율', scale:'크기불균형',
    perspective:'투시', style:'스타일', palette:'색상',
    anatomy:'해부학이상', physics:'물리오류',
  };
  const rows=(d.results||[]).map((r,i)=>{
    const ok=r.passed;
    const badge=ok
      ?`<span style="color:var(--green);font-weight:700;">✓ 확인</span>`
      :`<span style="color:var(--red);font-weight:700;">✗ 실패</span>`;
    const cbCell=ok
      ?`<td style="padding:4px 8px;"></td>`
      :`<td style="padding:4px 8px;text-align:center;"><input type="checkbox" class="audit-chk" data-idx="${i}" style="cursor:pointer;" onchange="_auditChkChange()"></td>`;
    // [anatomy,scale,...] 태그 파싱
    const tagMatch=(r.issues||'').match(/\[([^\]]+)\]/);
    const tags=tagMatch?tagMatch[1].split(',').map(s=>s.trim()):[];
    const detail=(r.issues||'').replace(/\[[^\]]+\]\s*/,'');
    const tagBadges=tags.map(t=>{
      const c=_tagColor[t]||'#8b949e';
      const l=_tagLabel[t]||t;
      return `<span style="display:inline-block;background:${c}22;color:${c};border:1px solid ${c}55;border-radius:4px;padding:1px 6px;font-size:.63rem;font-weight:700;margin-right:3px;">${l}</span>`;
    }).join('');
    const issueText=detail?`<div style="font-size:.67rem;color:var(--muted);margin-top:3px;">${detail}</div>`:'';
    const issuesCell=ok?`<span style="color:var(--muted2);">—</span>`:`${tagBadges}${issueText}`;
    const si = r.sent_idx ?? -1;
    const sentLabel = si < 0
      ? `<span style="color:var(--muted2);font-size:.65rem;">단어</span>`
      : `<span style="font-weight:700;color:var(--blue);">#${si + 1}</span>`;
    return `<tr style="border-top:1px solid var(--border);">
      ${cbCell}
      <td style="padding:4px 8px;">${r.word_id}</td>
      <td style="padding:4px 8px;font-weight:600;">${r.word}</td>
      <td style="padding:4px 8px;">${r.level}급</td>
      <td style="padding:4px 8px;text-align:center;">${sentLabel}</td>
      <td style="padding:4px 8px;">${badge}</td>
      <td style="padding:6px 8px;max-width:360px;">${issuesCell}</td>
    </tr>`;
  }).join('');
  tbody.innerHTML=rows||'<tr><td colspan="7" style="padding:12px;text-align:center;color:var(--muted);">결과 없음</td></tr>';
  document.getElementById('audit-results').style.display='block';
}
function _auditChkChange(){
  const chks=document.querySelectorAll('.audit-chk');
  const all=document.getElementById('audit-check-all');
  if(!all)return;
  const total=chks.length, checked=[...chks].filter(c=>c.checked).length;
  all.indeterminate=checked>0&&checked<total;
  all.checked=checked===total&&total>0;
}
function auditToggleAll(checked){
  document.querySelectorAll('.audit-chk').forEach(c=>{c.checked=checked;});
}
async function auditRegenAll(){
  if(!confirm('감사에서 실패한 이미지를 전체 재생성합니다. 계속할까요?'))return;
  _triggerAuditRegen({all_failed:true});
}
async function auditRegenSelected(){
  const chks=[...document.querySelectorAll('.audit-chk:checked')];
  if(!chks.length){alert('재생성할 항목을 선택하세요');return;}
  const entries=chks.map(c=>{
    const idx=parseInt(c.dataset.idx);
    const r=(_auditData.results||[])[idx];
    return {word_id:r.word_id, sent_idx:r.sent_idx??-1, issues:r.issues||''};
  });
  _triggerAuditRegen({entries});
}
async function _triggerAuditRegen(body){
  const allBtn=document.getElementById('audit-regen-all-btn');
  const selBtn=document.getElementById('audit-regen-sel-btn');
  const st=document.getElementById('audit-regen-status');
  allBtn.disabled=true;selBtn.disabled=true;
  st.textContent='⏳ 재생성 요청 중...';
  const r=await fetch('/api/illustrations/audit/regen',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const d=await r.json();
  if(!r.ok){st.textContent='오류: '+(d.error||'');allBtn.disabled=false;selBtn.disabled=false;return;}
  st.textContent='🔄 재생성 중...';
  const poll=setInterval(async()=>{
    const sr=await fetch('/api/illustrations/audit/regen/status');
    const sd=await sr.json();
    if(sd.status==='running'){
      const prog=sd.total?` (${(sd.done||0)+' / '+sd.total})`:' ';
      st.textContent=`🔄 재생성 중${prog}...`;
    } else {
      clearInterval(poll);
      allBtn.disabled=false;selBtn.disabled=false;
      if(sd.status==='done'){
        const errs=sd.errors||0;
        st.textContent=errs>0?`완료 (오류 ${errs}건)`:'✓ 재생성 완료';
        setTimeout(loadAuditResults,800);
      } else {
        st.textContent='✗ 재생성 실패';
      }
    }
  },2000);
}

function setEl(id,val){const e=document.getElementById(id);if(e)e.textContent=val;}

// ── 렌더 패널 ──────────────────────────────────────────
let _rpTab='batch', _batchData=null, _configSlots=[];
let _batchChecked=new Set();
let _batchTarget='desktop', _customTarget='desktop';
let _rpContent=new Set(['word','conv']); // 콘텐츠 선택: word, conv
let _rpFmt=new Set(['youtube','reels']); // 포맷 선택: youtube, reels
let _thumbStyle='portrait'; // 썸네일 스타일: portrait | landscape

function setThumbStyle(style){
  _thumbStyle=style;
  const p=document.getElementById('thumb-style-portrait');
  const l=document.getElementById('thumb-style-landscape');
  if(p){p.className='btn '+(style==='portrait'?'btn-g':'btn-m');}
  if(l){l.className='btn '+(style==='landscape'?'btn-p':'btn-m');}
}

let _livePollTimer=null;

function rpTab(tab){
  _rpTab=tab;
  ['batch','custom','illust','history','live'].forEach(t=>{
    const v=document.getElementById('rp-'+t);if(v)v.style.display=t===tab?'block':'none';
    const b=document.getElementById('rp-tab-'+t);
    if(b){b.classList.toggle('on',t===tab);}
  });
  if(_livePollTimer){clearInterval(_livePollTimer);_livePollTimer=null;}
  _stopDailyPoll();
  if(tab==='batch'){_startDailyPoll();}
  if(tab==='custom') updateCustomPreview();
  if(tab==='illust') loadIllustData();
  if(tab==='history'){const dp=document.getElementById('rp-date-pick');if(dp)dp.value=new Date().toISOString().slice(0,10);loadHistoryDate();}
  if(tab==='config') loadConfigSlots();
  if(tab==='live'){loadLiveStatus();_livePollTimer=setInterval(loadLiveStatus,2000);}
}

async function clearBatchQueue(){
  await fetch('/api/batch/clear',{method:'POST'});
  const s=document.getElementById('live-summary');
  const l=document.getElementById('live-list');
  if(s) s.style.display='none';
  if(l) l.innerHTML='';
}

async function loadLiveStatus(){
  try{
    const r=await fetch('/api/batch/today');
    if(!r.ok) return;
    const d=await r.json();
    const bq=d.queue||{};
    const items=bq.items||[];
    const status=bq.status||'idle';

    // 완료된 지 10분 이상 지났으면 숨김
    const summaryEl=document.getElementById('live-summary');
    if(status!=='running'&&bq.completed_at){
      const age=Date.now()-new Date(bq.completed_at).getTime();
      if(age>10*60*1000){if(summaryEl)summaryEl.style.display='none';return;}
    }
    if(summaryEl&&(status==='running'||items.length>0)) summaryEl.style.display='block';
    else if(summaryEl&&items.length===0){summaryEl.style.display='none';return;}

    // 카운트
    const done=items.filter(i=>['rendered','uploaded','generated','done'].includes(i.status)).length;
    const pending=items.filter(i=>i.status==='pending').length;
    const running=items.filter(i=>i.status==='rendering'||i.status==='uploading').length;
    const failed=items.filter(i=>i.status==='failed').length;
    const skipped=items.filter(i=>i.status==='skipped'||i.status==='cancelled').length;
    const total=items.length;
    const pct=total>0?Math.round((bq.current||0)/total*100):0;

    // 헤더
    const lbl=document.getElementById('live-status-label');
    const cancelBtn=document.getElementById('live-cancel-btn');
    if(lbl){
      if(status==='running'){
        lbl.innerHTML='<span class="pulse" style="color:#3fb950;">⟳ 렌더링 진행 중</span>';
        if(cancelBtn) cancelBtn.style.display='inline-block';
      } else {
        if(cancelBtn) cancelBtn.style.display='none';
        if(status==='done'||status==='completed') lbl.innerHTML='<span style="color:#3fb950;">✅ 완료</span>';
        else if(status==='failed') lbl.innerHTML='<span style="color:var(--red);">✕ 실패</span>';
        else if(status==='cancelled') lbl.innerHTML='<span style="color:#8b949e;">✕ 취소됨</span>';
        else lbl.innerHTML='<span style="color:var(--muted);">대기 중</span>';
      }
    }

    // 타이밍
    const timEl=document.getElementById('live-timing');
    if(timEl&&bq.started_at){
      const elapsed=Math.round((Date.now()-new Date(bq.started_at).getTime())/1000);
      const m=Math.floor(elapsed/60), s=elapsed%60;
      const tgt=bq.target==='desktop'?'💻 GPU':'🖥 NAS';
      timEl.textContent=`${tgt} · 경과 ${m}분 ${s}초`;
    } else if(timEl) timEl.textContent='';

    // 진행바
    const pb=document.getElementById('live-pbar');
    if(pb) pb.style.width=pct+'%';

    // 카운터
    const setN=(id,v)=>{const e=document.getElementById(id);if(e)e.textContent=v;};
    setN('live-done',done); setN('live-pending',pending); setN('live-running',running);
    setN('live-failed',failed); setN('live-skipped',skipped); setN('live-total',total);

    // 항목 목록
    const lvC={'1':'#3fb950','2':'#58a6ff','3':'#d29922','4':'#f78166','5':'#bc8cff','6':'#f87171'};
    const statusIcon={
      pending:'<span style="color:#f59e0b;">⏳</span>',
      rendering:'<span style="color:#58a6ff;" class="pulse">⟳</span>',
      uploading:'<span style="color:#818cf8;" class="pulse">⬆</span>',
      rendered:'<span style="color:#3fb950;">✅</span>',
      uploaded:'<span style="color:#3fb950;">✅</span>',
      generated:'<span style="color:#818cf8;">✓</span>',
      done:'<span style="color:#3fb950;">✅</span>',
      failed:'<span style="color:var(--red);">✕</span>',
      skipped:'<span style="color:#8b949e;">⏭</span>',
      cancelled:'<span style="color:#8b949e;">✕</span>',
    };
    const el=document.getElementById('live-list');
    if(el&&total>0){
      el.innerHTML=items.map((it,i)=>{
        const lv=it.level||'?';
        const c=lvC[lv]||'#8b949e';
        const ic=statusIcon[it.status]||'<span style="color:#8b949e;">·</span>';
        const bold=it.status==='rendering'||it.status==='uploading'?'font-weight:700;':'';
        const bg=it.status==='rendering'?'background:#1c3a2a;':
                 it.status==='failed'?'background:#2d1515;':'';
        const isDone=['done','rendered','generated'].includes(it.status);
        const isUploaded=it.status==='uploaded'||it.video_id;
        const isRestartable=['cancelled','failed'].includes(it.status);
        const uploadBtn=isDone&&!isUploaded
          ?`<button onclick="liveUpload(${it.word_id},'${it.lang||'EN'}','${it.exam||'TOPIK'}')"
              style="font-size:.6rem;padding:2px 8px;border-radius:4px;border:none;
                     background:var(--blue);color:#fff;cursor:pointer;white-space:nowrap;">
              ⬆ 업로드
            </button>`
          : (isUploaded
              ? (it.video_id
                  ? `<a href="https://youtube.com/watch?v=${it.video_id}" target="_blank"
                       style="font-size:.6rem;color:var(--green);">▶ 보기</a>`
                  : `<span style="font-size:.6rem;color:var(--green);">✓ 업로드됨</span>`)
              : (isRestartable
                  ? `<button onclick="renderSingle(${it.word_id},'${it.exam||'TOPIK'}','${it.lang||'EN'}',this)"
                        style="font-size:.6rem;padding:2px 8px;border-radius:4px;border:1px solid var(--green);
                               background:transparent;color:var(--green);cursor:pointer;white-space:nowrap;">
                        ↻ 재시작
                      </button>`
                  : ''));
        return `<div style="display:flex;align-items:center;gap:8px;padding:6px 10px;border-radius:6px;font-size:.72rem;${bg}">
          <span style="color:#484f58;min-width:20px;text-align:right;">${i+1}</span>
          ${ic}
          <span style="color:${c};font-weight:700;min-width:22px;">${lv}급</span>
          <span style="min-width:24px;font-size:.68rem;">${_FLAGS[it.lang||'EN']||it.lang||''}</span>
          <span style="${bold}flex:1;">${it.word||('ID '+it.word_id)}</span>
          <span style="color:var(--muted2);font-size:.62rem;">${it.exam||''} · ${it.lang||''}</span>
          ${uploadBtn}
          <span style="font-size:.66rem;color:var(--muted);">${it.status||''}</span>
        </div>`;
      }).join('');
    } else if(el){
      el.innerHTML='<div style="color:var(--muted);text-align:center;padding:20px;font-size:.78rem;">진행 중인 배치가 없습니다</div>';
    }

    // 완료되면 폴링 중단
    if(status!=='running'&&_livePollTimer){
      clearInterval(_livePollTimer);_livePollTimer=null;
    }
  }catch(e){}
}

async function loadBatchData(){
  try{ const r=await fetch('/api/batch/today'); _batchData=await r.json(); renderBatchList(_batchData); }catch(e){}
  loadTodayConv();
}

// ── 오늘의 회화 ───────────────────────────────────────────────
let _todayConvId = null;
let _todayKdramaId = null;
let _convThemesAll = [];
const CONV_LANGS = ['EN','JP','CN','VN','ES'];

async function loadTodayConv(){
  try{
    const r=await fetch('/api/conv/themes');
    const d=await r.json();
    const themes=d.themes||[];
    if(!themes.length) return;
    // 첫 번째 미완성 상황 찾기
    const next=themes.find(t=>CONV_LANGS.some(l=>!t.langs[l]?.rendered))||themes[0];
    _convThemesAll=themes;
    if(!_todayConvId) _todayConvId=next.id;
    const cur=themes.find(t=>t.id===_todayConvId)||next;
    renderTodayConv(cur);
    const inp=document.getElementById('daily-conv-id-input');
    if(inp&&!inp.value) inp.value=cur.id;
  }catch(e){}
}

function renderTodayConv(theme){
  const disp=document.getElementById('daily-conv-display');
  if(disp) disp.innerHTML=`<span style="color:var(--green);">${theme.emoji||'💬'} ${theme.title?.KR||theme.id}</span> <span style="font-size:.7rem;color:var(--muted);">${theme.title?.EN||''}</span>`;
  const tbody=document.getElementById('daily-conv-tbody');
  if(!tbody) return;
  tbody.innerHTML=CONV_LANGS.map(lang=>{
    const ls=theme.langs[lang]||{};
    const rendBadge=ls.rendered?'<span style="color:var(--green);">✓</span>':'<span style="color:var(--muted2);">○</span>';
    const uplBadge=ls.uploaded?'<span style="color:var(--green);">✓</span>':'<span style="color:var(--muted2);">○</span>';
    return `<tr>
      <td style="padding:4px 6px;">${LANG_FLAGS[lang]} <span style="font-size:.68rem;color:var(--muted);">${CONV_LANG_NAMES[lang]}</span></td>
      <td style="text-align:center;padding:4px 6px;">${rendBadge}</td>
      <td style="text-align:center;padding:4px 6px;">${uplBadge}</td>
    </tr>`;
  }).join('');
}

function dailySetConv(){
  const id=parseInt(document.getElementById('daily-conv-id-input').value)||null;
  if(!id) return;
  const themes=_convThemesAll;
  const theme=themes.find(t=>String(t.id)===String(id));
  if(!theme){alert('해당 ID의 회화가 없습니다');return;}
  _todayConvId=theme.id;
  renderTodayConv(theme);
}

async function renderConvOnly(){
  const btn=document.getElementById('rp-render-conv');
  if(!_todayConvId){alert('회화 상황을 먼저 선택하세요');return;}
  btn.disabled=true;btn.textContent='⏳ 큐잉 중...';
  try{
    for(const lang of CONV_LANGS){
      for(const fmt of ['youtube','reels']){
        await fetch('/api/conv/render',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({theme_id:String(_todayConvId),lang,fmt,target:_batchTarget||'nas'})});
      }
    }
    loadJobQueue();navRenderTab(null,'live');
  }catch(e){alert('실패: '+e);}
  finally{btn.disabled=false;btn.textContent='💬 회화 렌더링';}
}

async function renderBatchBoth(){
  const btn=document.getElementById('rp-render-both');
  btn.disabled=true;btn.textContent='⏳ 큐잉 중...';
  try{
    // 단어 렌더링
    const r=await fetch('/api/batch/today');
    const d=await r.json();
    const batch=d.batch||[];
    const pending=batch.filter(b=>b.status==='pending');
    if(pending.length){
      const body={items:pending.map(b=>({word_id:b.word_id,exam:b.exam,lang:b.lang,level:b.level,formats:['youtube','reels']})),target:_batchTarget||'nas'};
      await fetch('/api/render/batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    }
    // 회화 렌더링 (youtube + reels)
    if(_todayConvId){
      for(const lang of CONV_LANGS){
        for(const fmt of ['youtube','reels']){
          await fetch('/api/conv/render',{method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({theme_id:String(_todayConvId),lang,fmt,target:_batchTarget||'nas'})});
        }
      }
    }
    // K-드라마 렌더링 (youtube + reels)
    if(_todayKdramaId){
      for(const lang of CONV_LANGS){
        for(const fmt of ['youtube','reels']){
          await fetch('/api/kdrama/render',{method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({theme_id:String(_todayKdramaId),lang,fmt,target:_batchTarget||'nas'})});
        }
      }
    }
    loadJobQueue();navRenderTab(null,'live');
  }catch(e){alert('실패: '+e);}
  finally{btn.disabled=false;btn.textContent='▶ 단어+회화+K드라마 모두 렌더링';}
}

const _STATUS_HTML={
  pending:'<span style="color:#f59e0b;font-size:.72rem;">● 대기</span>',
  rendering:'<span style="color:#3fb950;font-size:.72rem;" class="pulse">⟳ 렌더링</span>',
  uploading:'<span style="color:#58a6ff;font-size:.72rem;" class="pulse">⟳ 업로드</span>',
  generated:'<span style="color:#818cf8;font-size:.72rem;">✓ 생성됨</span>',
  uploaded:'<span style="color:#3fb950;font-size:.72rem;">✓ 업로드</span>',
  no_word:'<span style="color:#484f58;font-size:.72rem;">— 완료</span>',
  skipped:'<span style="color:#8b949e;font-size:.72rem;">⏭ 건너뜀</span>',
  cancelled:'<span style="color:#f87171;font-size:.72rem;">✕ 취소됨</span>',
  failed:'<span style="color:#f87171;font-size:.72rem;">✕ 실패</span>',
};

function renderBatchList(d){
  const today=new Date().toLocaleDateString('ko-KR',{month:'long',day:'numeric',weekday:'short'});
  setEl('rp-today-date',today);
  const batch=d.batch||[];
  const pending=batch.filter(b=>b.status==='pending').length;
  setEl('rp-today-sub',`${batch.length}개 슬롯 · 대기 ${pending}개`);
  // 타겟 정보
  const perMin=_batchTarget==='desktop'?3:12;
  const infoEl=document.getElementById('rp-target-info');
  if(infoEl) infoEl.textContent=pending>0?`${pending}개 × ~${perMin}분 = 예상 ~${pending*perMin}분`:'';
  updateBatchTargetUI();
  const bq=d.queue||{};
  const qEl=document.getElementById('rp-batch-queue');
  if(qEl) qEl.textContent=bq.status==='running'?`배치 진행 중: ${bq.current||0}/${bq.total||0} · ${bq.target==='desktop'?'💻 GPU':'🖥 NAS'}`:'';
  // 렌더링 게이지
  const rp=document.getElementById('rp-batch-progress');
  if(rp){
    if(bq.status==='running'&&bq.total>0){
      rp.style.display='block';
      const cur=bq.current||0, tot=bq.total||1;
      const pct=Math.round(cur/tot*100);
      setEl('rp-batch-prog-pct',pct+'%');
      const gb=document.getElementById('rp-batch-prog-bar');
      if(gb) gb.style.width=pct+'%';
      // 현재 렌더링 중인 항목 이름
      const curItem=(bq.items||[]).find(it=>it.status==='rendering');
      const curWord=curItem?` — ${curItem.word||'ID '+curItem.word_id}`:'';
      setEl('rp-batch-prog-label',`🎬 렌더링 중 (${cur}/${tot})${curWord}`);
      setEl('rp-batch-prog-step',bq.target==='desktop'?'💻 GPU':'🖥 NAS CPU');
    } else {
      rp.style.display='none';
    }
  }
  // 렌더링/취소 버튼
  const isRunning=bq.status==='running';
  const btn=document.getElementById('rp-render-all');
  const cancelBtn=document.getElementById('rp-cancel-btn');
  const checkedPending=batch.filter((b,i)=>b.status==='pending'&&b.word&&_batchChecked.has(i)).length;
  const renderCount=checkedPending>0?checkedPending:pending;
  if(btn){
    btn.disabled=isRunning||renderCount===0;
    if(isRunning) btn.textContent='⏳ 진행 중...';
    else _updateRpRenderBtn();
    btn.style.display=isRunning?'none':'block';
  }
  if(cancelBtn){
    cancelBtn.style.display=isRunning?'block':'none';
  }
  // 커스텀 탭 취소 버튼도 동기화
  const rcCancel=document.getElementById('rc-cancel');
  if(rcCancel) rcCancel.style.display=isRunning?'':'none';
  // 전체선택 체크 동기화
  const selAll=document.getElementById('rp-select-all');
  if(selAll){
    const pendingIdxs=batch.map((b,i)=>b.status==='pending'&&b.word?i:-1).filter(i=>i>=0);
    selAll.checked=pendingIdxs.length>0&&pendingIdxs.every(i=>_batchChecked.has(i));
    selAll.indeterminate=!selAll.checked&&pendingIdxs.some(i=>_batchChecked.has(i));
  }
  const el=document.getElementById('rp-batch-list');
  if(!batch.length){el.innerHTML='<div style="color:#8b949e;text-align:center;padding:20px;">슬롯이 없습니다. ⚙️ 설정 탭에서 추가하세요.</div>';return;}
  const _fmtBadge=f=>f==='youtube'
    ?'<span style="font-size:.56rem;color:var(--green);border:1px solid var(--green)22;background:var(--green)11;border-radius:3px;padding:1px 4px;">YT</span>'
    :f==='reels'
    ?'<span style="font-size:.56rem;color:var(--amber);border:1px solid var(--amber)22;background:var(--amber)11;border-radius:3px;padding:1px 4px;">릴스</span>'
    :'<span style="font-size:.56rem;color:var(--accent);border:1px solid var(--accent)22;background:var(--accent)11;border-radius:3px;padding:1px 4px;">YT+릴스</span>';
  el.innerHTML=batch.map((b,i)=>{
    const w=b.word; const col=EXAM_COLORS[b.exam]||'#818cf8'; const lvC=LVC[b.level]||'#8b949e';
    const canR=b.status==='pending'&&w;
    const isGen=b.status==='generated'&&w;
    const chk=_batchChecked.has(i);
    const fmtBadge=_fmtBadge(b.fmt||'both');
    return `<div class="slot${chk?' hl':''}">
      ${canR?`<input type="checkbox" ${chk?'checked':''} onchange="toggleBatchCheck(${i})" style="accent-color:var(--green);flex-shrink:0;">`
        :`<span style="font-size:.66rem;color:var(--muted2);min-width:14px;">${i+1}</span>`}
      <span style="color:${col};font-size:.68rem;font-weight:700;min-width:40px;">${b.exam}</span>
      <span style="font-size:.78rem;">${_FLAGS[b.lang]||b.lang}</span>
      <span style="color:${lvC};font-size:.7rem;font-weight:700;">${b.level}급</span>
      ${fmtBadge}
      <div style="flex:1;min-width:0;">
        ${w?`<div style="font-weight:600;font-size:.82rem;"><span style="color:var(--muted2);font-size:.66rem;margin-right:3px;">#${w.id}</span>${w.word} ${b.has_illust?'<span style="font-size:.58rem;" title="일러스트">🖼</span>':'<span style="color:var(--muted2);font-size:.58rem;">🖼</span>'}</div><div style="color:var(--muted);font-size:.66rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${w.meaning}</div>`
          :'<div style="color:var(--muted2);font-size:.76rem;">– 완료</div>'}
      </div>
      ${_STATUS_HTML[b.status]||''}
      ${canR?`<button onclick="renderSingle(${w.id},'${b.exam}','${b.lang}',this)" class="btn btn-g" style="padding:2px 8px;font-size:.68rem;">▶</button>`:''}
      ${isGen?`<button onclick="manualUpload(${w.id},'${b.exam}','${b.lang}',this)" class="btn btn-b" style="padding:2px 7px;font-size:.64rem;" title="YouTube 업로드">⬆</button>`:''}
    </div>`;
  }).join('');
}

function toggleBatchCheck(idx){
  if(_batchChecked.has(idx)) _batchChecked.delete(idx);
  else _batchChecked.add(idx);
  if(_batchData) renderBatchList(_batchData);
}
function toggleAllBatchCheck(){
  const batch=(_batchData||{}).batch||[];
  const pendingIdxs=batch.map((b,i)=>b.status==='pending'&&b.word?i:-1).filter(i=>i>=0);
  const allChecked=pendingIdxs.every(i=>_batchChecked.has(i));
  if(allChecked) pendingIdxs.forEach(i=>_batchChecked.delete(i));
  else pendingIdxs.forEach(i=>_batchChecked.add(i));
  if(_batchData) renderBatchList(_batchData);
}

function updateBatchTargetUI(){
  const dBtn=document.getElementById('rp-target-desktop');
  const nBtn=document.getElementById('rp-target-nas');
  if(!dBtn||!nBtn) return;
  if(_batchTarget==='desktop'){dBtn.className='btn btn-p';dBtn.style.fontSize='.7rem';dBtn.style.padding='4px 10px';nBtn.className='btn btn-m';nBtn.style.fontSize='.7rem';nBtn.style.padding='4px 10px';}
  else{dBtn.className='btn btn-m';dBtn.style.fontSize='.7rem';dBtn.style.padding='4px 10px';nBtn.className='btn btn-g';nBtn.style.fontSize='.7rem';nBtn.style.padding='4px 10px';}
}

function setBatchTarget(t){
  _batchTarget=t;
  if(_batchData) renderBatchList(_batchData);
}

function toggleRpContent(key){
  if(_rpContent.has(key)) _rpContent.delete(key);
  else _rpContent.add(key);
  if(_rpContent.size===0) _rpContent.add(key); // 최소 1개
  const wBtn=document.getElementById('rp-tog-word');
  const cBtn=document.getElementById('rp-tog-conv');
  if(wBtn){wBtn.className='btn '+(_rpContent.has('word')?'btn-g':'btn-m');wBtn.style.opacity=_rpContent.has('word')?'1':'.45';}
  if(cBtn){cBtn.className='btn '+(_rpContent.has('conv')?'btn-a':'btn-m');cBtn.style.opacity=_rpContent.has('conv')?'1':'.45';}
  _updateRpRenderBtn();
}
function toggleRpFmt(key){
  if(_rpFmt.size===1 && _rpFmt.has(key)){
    // 이미 단독 선택된 상태 → 둘 다 선택으로 전환
    _rpFmt.add(key==='youtube'?'reels':'youtube');
  } else {
    // 클릭한 포맷만 단독 선택
    _rpFmt.clear();
    _rpFmt.add(key);
  }
  const yBtn=document.getElementById('rp-tog-yt');
  const rBtn=document.getElementById('rp-tog-rl');
  if(yBtn){yBtn.className='btn '+(_rpFmt.has('youtube')?'btn-g':'btn-m');yBtn.style.opacity=_rpFmt.has('youtube')?'1':'.45';}
  if(rBtn){rBtn.className='btn '+(_rpFmt.has('reels')?'btn-a':'btn-m');rBtn.style.opacity=_rpFmt.has('reels')?'1':'.45';}
  _updateRpRenderBtn();
}
function _updateRpRenderBtn(){
  const btn=document.getElementById('rp-render-all');
  if(!btn)return;
  const parts=[];
  if(_rpContent.has('word')) parts.push('단어');
  if(_rpContent.has('conv')) parts.push('회화');
  const fParts=[];
  if(_rpFmt.has('youtube')) fParts.push('YT');
  if(_rpFmt.has('reels')) fParts.push('릴스');
  btn.textContent=`▶ ${parts.join('+')} 렌더링 (${fParts.join('+')})`;
}

async function renderBatchAll(){
  const btn=document.getElementById('rp-render-all');
  btn.disabled=true;btn.textContent='⏳ 요청 중...';
  let started=false;
  try{
    const autoUpload=document.getElementById('rp-auto-upload')?.checked??false;
    const batch=(_batchData||{}).batch||[];
    const fmtList=[..._rpFmt]; // 선택된 포맷 목록

    // 단어 렌더링
    if(_rpContent.has('word')){
      // 체크된 항목만 있으면 그것만, 없으면 전체 pending
      let pendingBatch=batch.filter((b,i)=>b.status==='pending'&&b.word);
      if(_batchChecked.size>0) pendingBatch=pendingBatch.filter((_,i)=>_batchChecked.has(i));
      if(pendingBatch.length){
        // 슬롯별 포맷: 슬롯 fmt와 선택된 포맷의 교집합
        const items=pendingBatch.map(b=>{
          const slotFmts=b.fmt==='youtube'?['youtube']:b.fmt==='reels'?['reels']:['youtube','reels'];
          const fmts=slotFmts.filter(f=>fmtList.includes(f));
          return {word_id:b.word.id,exam:b.exam,lang:b.lang,level:b.level,formats:fmts.length?fmts:fmtList};
        });
        const r=await fetch('/api/render/batch',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({items,target:_batchTarget,auto_upload:autoUpload,thumb_style:_thumbStyle})});
        const d=await r.json();
        if(!r.ok){alert('단어 렌더 오류: '+(d.error||''));return;}
        started=true;
      }
    }

    // 회화 렌더링
    if(_rpContent.has('conv')&&_todayConvId){
      for(const lang of CONV_LANGS){
        await fetch('/api/conv/render',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({theme_id:String(_todayConvId),lang,target:_batchTarget||'nas'})});
      }
      started=true;
    }

    if(started){_batchChecked.clear();setTimeout(()=>{loadBatchData();loadJobQueue();},500);}
    else alert('렌더링할 항목이 없습니다');
    navRenderTab(null,'live');
  }catch(e){alert('실패: '+e);}
  finally{
    if(!started){btn.disabled=false;_updateRpRenderBtn();}
    else{btn.disabled=false;_updateRpRenderBtn();}
  }
}

async function liveUpload(wordId, lang, exam){
  const btn=event.target;
  btn.disabled=true; btn.textContent='⏳...';
  try{
    const r=await fetch('/api/render/upload',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({word_id:wordId,lang,exam})});
    const d=await r.json();
    if(!r.ok){btn.textContent='✕ 실패'; alert('업로드 오류: '+(d.error||''));}
    else{btn.textContent='✓ 완료'; setTimeout(loadLiveStatus,1000);}
  }catch(e){btn.textContent='✕ 오류'; alert(String(e));}
}

async function cancelBatchRender(){
  if(!confirm('렌더링을 취소할까요?')) return;
  try{
    const r=await fetch('/api/render/cancel',{method:'POST'});
    const d=await r.json();
    if(!r.ok) alert('오류: '+(d.error||''));
    else setTimeout(loadBatchData,500);
  }catch(e){alert('실패: '+e);}
}

async function manualUpload(wordId,exam,lang,btnEl){
  if(!confirm('이 영상을 YouTube에 업로드할까요?')) return;
  if(btnEl){btnEl.disabled=true;btnEl.textContent='⏳';btnEl.style.opacity='.5';}
  try{
    const r=await fetch('/api/upload/manual',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({word_id:wordId,exam,lang})});
    const d=await r.json();
    if(!r.ok){alert('오류: '+(d.error||''));if(btnEl){btnEl.disabled=false;btnEl.textContent='⬆';btnEl.style.opacity='1';}}
    else{
      if(btnEl){btnEl.textContent='✓';btnEl.style.color='#3fb950';btnEl.style.borderColor='#3fb950';}
      alert('업로드 완료!\\n'+d.url);
      setTimeout(loadBatchData,500);loadOverview();
    }
  }catch(e){alert('실패: '+e);if(btnEl){btnEl.disabled=false;btnEl.textContent='⬆';btnEl.style.opacity='1';}}
}

async function renderSingle(wordId,exam,lang,btnEl){
  if(btnEl){btnEl.disabled=true;btnEl.textContent='⏳';btnEl.style.opacity='.5';}
  try{
    const t=_rpTab==='custom'?_customTarget:_batchTarget;
    const body={word_id:wordId,target:t};
    if(exam) body.exam=exam;
    if(lang) body.lang=lang;
    const r=await fetch('/api/render',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const d=await r.json();
    if(!r.ok){alert('오류: '+(d.error||''));if(btnEl){btnEl.disabled=false;btnEl.textContent='▶';btnEl.style.opacity='1';}}
    else{
      if(btnEl){btnEl.textContent='⏳ 큐';btnEl.style.background='#1a1a3a';btnEl.style.color='#818cf8';btnEl.style.borderColor='#818cf8';}
      setTimeout(loadBatchData,1000);loadOverview();loadJobQueue();
    }
  }catch(e){alert('실패: '+e);if(btnEl){btnEl.disabled=false;btnEl.textContent='▶';btnEl.style.opacity='1';}}
}

// ── 커스텀 렌더링 ─────────────────────────────────────────
// 활성 패널 감지: 영상 작업 센터 커스텀 탭이면 wc-rc-* 사용, 아니면 rc-* 사용
function _activeRcPrefix(){
  const wcPanel=document.getElementById('wt-panel-custom');
  return (wcPanel&&wcPanel.style.display!=='none')?'wc-rc-':'rc-';
}
function getSelectedLangs(){
  const pfx=_activeRcPrefix();
  const container=document.getElementById(pfx+'lang-btns')||document;
  return [...container.querySelectorAll('.rc-lang-btn.active')].map(b=>b.dataset.lang);
}
function getSelectedFmts(){
  const pfx=_activeRcPrefix();
  const container=document.getElementById(pfx+'lang-btns')||document;
  return [...container.querySelectorAll('.rc-fmt-btn.active')].map(b=>b.dataset.fmt);
}
function toggleRowFmt(btn){
  const row=btn.closest('.rc-target-row');
  const allBtns=[...row.querySelectorAll('.rc-row-fmt')];
  const active=[...row.querySelectorAll('.rc-row-fmt.active')];
  const isAlreadySole=active.length===1&&btn.classList.contains('active');
  // 클릭한 포맷만 단독 선택 (이미 단독이면 둘 다 선택으로 전환)
  allBtns.forEach(b=>{
    const bFmt=b.dataset.fmt;
    const bColor=bFmt==='youtube'?'var(--green)':'var(--amber)';
    const select=isAlreadySole||(b===btn);
    if(select){
      b.classList.add('active');
      b.style.background=bColor+'22';b.style.color=bColor;b.style.borderColor=bColor;b.style.opacity='1';
    }else{
      b.classList.remove('active');
      b.style.background='transparent';b.style.color='var(--muted)';b.style.borderColor='var(--border)';b.style.opacity='.45';
    }
  });
  updateCustomPreview();
}
function toggleLangBtn(btn){
  const active=btn.classList.toggle('active');
  if(active){
    btn.style.borderColor='var(--blue)';btn.style.background='var(--blue)22';btn.style.color='var(--blue)';
  } else {
    btn.style.borderColor='var(--border)';btn.style.background='transparent';btn.style.color='var(--muted)';
  }
  if(getSelectedLangs().length===0){
    btn.classList.add('active');
    btn.style.borderColor='var(--blue)';btn.style.background='var(--blue)22';btn.style.color='var(--blue)';
  }
  updateCustomPreview();
}
function toggleFmtBtn(btn){
  const fmt=btn.dataset.fmt;
  const color=fmt==='youtube'?'var(--green)':'var(--amber)';
  const active=btn.classList.toggle('active');
  if(active){
    btn.style.borderColor=color;btn.style.background=color.replace(')',')').replace('var(','').replace(')','')+'22'.replace('22','')+'22';
    btn.style.background=color+'22';btn.style.color=color;
  } else {
    btn.style.borderColor='var(--border)';btn.style.background='transparent';btn.style.color='var(--muted)';
  }
  if(getSelectedFmts().length===0){
    btn.classList.add('active');
    btn.style.borderColor=color;btn.style.background=color+'22';btn.style.color=color;
  }
  updateCustomPreview();
}
function setCustomTarget(t){
  _customTarget=t;
  const pfx=_activeRcPrefix();
  const dBtn=document.getElementById(pfx+'target-desktop');
  const nBtn=document.getElementById(pfx+'target-nas');
  if(!dBtn||!nBtn)return;
  if(t==='desktop'){dBtn.className='btn btn-p';dBtn.style.cssText='flex:1;justify-content:center;font-size:.72rem;';nBtn.className='btn btn-m';nBtn.style.cssText='flex:1;justify-content:center;font-size:.72rem;';}
  else{dBtn.className='btn btn-m';dBtn.style.cssText='flex:1;justify-content:center;font-size:.72rem;';nBtn.className='btn btn-g';nBtn.style.cssText='flex:1;justify-content:center;font-size:.72rem;';}
  updateCustomTimeEst();
}

let _customPreviewTimer=null;
function updateCustomPreview(){
  clearTimeout(_customPreviewTimer);
  _customPreviewTimer=setTimeout(_doCustomPreview,300);
}

// ── 시험/등급/ID 다중 행 관리 ────────────────────────────────
const _EXAM_OPTS=`<option value="TOPIK">🇰🇷 TOPIK</option><option value="TOEIC">📝 TOEIC</option><option value="JLPT">🌸 JLPT</option><option value="IELTS">🎓 IELTS</option><option value="HSK">🐉 HSK</option><option value="회화">💬 회화</option>`;
const _LEVEL_OPTS=`<option value="1">1급</option><option value="2">2급</option><option value="3">3급</option><option value="4">4급</option><option value="5">5급</option><option value="6">6급</option>`;

async function onExamChange(row){
  const exam=row.querySelector('.rc-exam').value;
  const levelWrap=row.querySelector('.rc-level-wrap');
  const convWrap=row.querySelector('.rc-conv-wrap');
  const idsWrap=row.querySelector('.rc-ids-wrap');
  const isConv=exam==='회화';
  if(levelWrap) levelWrap.style.display=isConv?'none':'';
  if(convWrap) convWrap.style.display=isConv?'':'none';
  if(idsWrap) idsWrap.style.display=isConv?'none':'';
  updateCustomPreview();
}

function parseIds(str){
  if(!str||!str.trim())return[];
  const ids=new Set();
  for(const part of str.split(',')){
    const t=part.trim();
    if(!t)continue;
    const m=t.match(/^(\d+)\s*[~\-]\s*(\d+)$/);
    if(m){for(let i=+m[1];i<=+m[2];i++)ids.add(i);}
    else if(/^\d+$/.test(t))ids.add(+t);
  }
  return [...ids].sort((a,b)=>a-b);
}

function getTargetRows(){
  const pfx=_activeRcPrefix();
  return [...document.querySelectorAll(`#${pfx}targets .rc-target-row`)].map(row=>{
    const exam=row.querySelector('.rc-exam').value;
    const level=row.querySelector('.rc-level').value;
    const ids_str=(row.querySelector('.rc-ids')||{value:''}).value.trim();
    const conv_range=(row.querySelector('.rc-conv-range')||{value:''}).value.trim();
    const fmtBtns=[...row.querySelectorAll('.rc-row-fmt.active')];
    const fmts=fmtBtns.length?fmtBtns.map(b=>b.dataset.fmt):['youtube'];
    return {exam, level, ids_str, conv_range, fmts, is_conv: exam==='회화'};
  });
}

function addTargetRow(){
  const container=document.getElementById('rc-targets');
  const div=document.createElement('div');
  div.className='rc-target-row';
  div.style.cssText='display:flex;gap:6px;align-items:flex-end;margin-bottom:6px;';
  div.innerHTML=`
    <div style="flex:2.5;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">시험</div><select class="rc-exam inp" onchange="onExamChange(this.closest('.rc-target-row'))" style="width:100%;">${_EXAM_OPTS}</select></div>
    <div class="rc-level-wrap" style="flex:1.5;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">등급</div><select class="rc-level inp" onchange="updateCustomPreview()" style="width:100%;">${_LEVEL_OPTS}</select></div>
    <div class="rc-conv-wrap" style="flex:1.5;display:none;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">화수</div><input class="rc-conv-range inp" placeholder="예: 3~10, 15" oninput="updateCustomPreview()" style="width:100%;"></div>
    <div class="rc-ids-wrap" style="flex:2;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">ID</div><input class="rc-ids inp" placeholder="예: 1, 3~10, 15" oninput="updateCustomPreview()" style="width:100%;"></div>
    <div style="flex:0 0 auto;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">포맷</div><div style="display:flex;gap:2px;"><button class="rc-row-fmt active" data-fmt="youtube" onclick="toggleRowFmt(this)" style="padding:4px 7px;font-size:.62rem;border-radius:5px;border:1px solid var(--green);background:var(--green)22;color:var(--green);cursor:pointer;white-space:nowrap;">▶본편</button><button class="rc-row-fmt active" data-fmt="reels" onclick="toggleRowFmt(this)" style="padding:4px 7px;font-size:.62rem;border-radius:5px;border:1px solid var(--amber);background:var(--amber)22;color:var(--amber);cursor:pointer;white-space:nowrap;">⚡쇼츠</button></div></div>
    <button onclick="removeTargetRow(this)" class="btn btn-m" style="width:28px;padding:5px 0;font-size:.9rem;flex-shrink:0;justify-content:center;align-self:flex-end;" title="삭제">×</button>`;
  container.appendChild(div);
  updateCustomPreview();
}

function removeTargetRow(el){
  const pfxR=_activeRcPrefix();
  const rows=document.querySelectorAll(`#${pfxR}targets .rc-target-row`);
  if(rows.length<=1)return;
  el.closest('.rc-target-row').remove();
  updateCustomPreview();
}

function toggleConvSection(){
  const en=document.getElementById('rc-conv-enabled')?.checked??false;
  const detailEl=document.getElementById('rc-conv-detail');
  if(detailEl) detailEl.style.display=en?'block':'none';
  updateCustomPreview();
}

function toggleConvLang(btn){
  const active=btn.classList.toggle('active');
  if(active){btn.style.borderColor='var(--blue)';btn.style.background='var(--blue)22';btn.style.color='var(--blue)';}
  else{btn.style.borderColor='var(--border)';btn.style.background='transparent';btn.style.color='var(--muted)';}
  updateCustomPreview();
}

function getConvLangs(){
  return [...document.querySelectorAll('#rc-conv-lang-btns .rc-conv-lang.active')].map(b=>b.dataset.lang);
}

function getConvIds(){
  const raw=(document.getElementById('rc-conv-ids')?.value||'').trim();
  if(!raw) return _phSituations.map(s=>s.id);
  return parseIds(raw).filter(id=>_phSituations.some(s=>s.id===id));
}

async function _doCustomPreview(){
  const pfx=_activeRcPrefix();
  const targets=getTargetRows();
  const langs=getSelectedLangs();
  const el=document.getElementById(pfx+'preview')||document.getElementById('rc-preview');
  const remEl=document.getElementById(pfx+'remaining')||document.getElementById('rc-remaining');

  // 회화 / 단어 분리
  const convTargets=targets.filter(t=>t.is_conv);
  const wordTargets=targets.filter(t=>!t.is_conv);

  // 회화 미리보기
  if(convTargets.length>0&&wordTargets.length===0){
    let totalEp=0;
    const rows=convTargets.map(t=>{
      const epIds=parseIds(t.conv_range);
      totalEp+=epIds.length;
      const rowFmtLabel=t.fmts.length===2?'본편+쇼츠':t.fmts[0]==='youtube'?'본편':'쇼츠';
      const rangeLabel=t.conv_range||'(범위 미입력)';
      const langBadges=langs.map(l=>`<span style="font-size:.58rem;background:#818cf822;color:#818cf8;border-radius:4px;padding:1px 5px;margin-left:2px;">${l}</span>`).join('');
      return `<div style="display:flex;align-items:center;gap:8px;padding:8px 10px;background:#1c2128;border-radius:7px;margin-bottom:4px;border:1px solid #21262d;">
        <span style="color:#818cf8;font-weight:700;font-size:.8rem;">회화 ${rangeLabel}화</span>
        <span style="font-size:.68rem;color:var(--muted);">${epIds.length?epIds.length+'편':'—'}</span>
        ${langBadges}
        <span style="font-size:.62rem;color:var(--amber);">${rowFmtLabel}</span>
      </div>`;
    }).join('');
    if(remEl) remEl.textContent=`회화 ${totalEp}화 × ${langs.length}개 언어`;
    el.innerHTML=rows||'<div style="color:#484f58;text-align:center;padding:16px;font-size:.78rem;">화수 범위를 입력하세요 (예: 3~10)</div>';
    const totalFmts=convTargets.reduce((s,t)=>s+t.fmts.length,0)/Math.max(convTargets.length,1);
    const total=Math.round(totalEp*langs.length*totalFmts);
    const startEl=document.getElementById(pfx+'start')||document.getElementById('rc-start');
    if(startEl){startEl.disabled=total===0||totalEp===0;startEl.textContent=`▶ 렌더링 시작 (${totalEp}화 × ${langs.length}개 언어 = ${total}개 · ${_customTarget==='desktop'?'💻 GPU':'🖥 NAS'})`;}
    updateCustomTimeEst();return;
  }

  // 단어 미리보기 (기존 로직)
  if(!wordTargets.length){el.innerHTML='';return;}
  const {exam,level,ids_str}=wordTargets[0];
  const lang=langs[0]||'EN';
  let url=`/api/render/preview?exam=${exam}&lang=${lang}&level=${level}`;
  if(ids_str) url+=`&ids=${encodeURIComponent(ids_str)}`;
  try{
    const r=await fetch(url);
    const d=await r.json();
    if(remEl) remEl.textContent=`남은 단어: ${d.remaining||0}개`;
    const startEl2=document.getElementById(pfx+'start')||document.getElementById('rc-start');
    if(!d.words||!d.words.length){
      el.innerHTML='<div style="color:#484f58;text-align:center;padding:16px;font-size:.78rem;">렌더링할 단어가 없습니다</div>';
      if(startEl2) startEl2.disabled=true;
      return;
    }
    if(startEl2) startEl2.disabled=false;
    const lvC={'1':'#3fb950','2':'#58a6ff','3':'#d29922','4':'#f78166','5':'#bc8cff','6':'#f87171'};
    const langBadges=langs.map(l=>`<span style="font-size:.58rem;background:var(--blue)22;color:var(--blue);border-radius:4px;padding:1px 5px;margin-left:2px;">${l}</span>`).join('');
    el.innerHTML=d.words.map((w,i)=>{
      const c=lvC[w.level]||'#8b949e';
      return `<div style="display:flex;align-items:center;gap:8px;padding:8px 10px;background:#1c2128;border-radius:7px;margin-bottom:4px;border:1px solid #21262d;">
        <span style="font-size:.66rem;color:#484f58;min-width:18px;text-align:right;">${i+1}</span>
        <span style="color:${c};font-size:.68rem;font-weight:700;">Lv.${w.level}</span>
        <span style="font-weight:600;font-size:.82rem;">${w.word}</span>
        <span style="font-size:.6rem;" title="${w.has_illust?'일러스트 있음':'일러스트 없음'}">${w.has_illust?'🖼':'<span style="opacity:.3;">🖼</span>'}</span>
        ${langBadges}
        <span style="color:#8b949e;font-size:.68rem;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${w.meaning}</span>
        <span style="color:#484f58;font-size:.64rem;">ID ${w.id}</span>
      </div>`;
    }).join('');
    const totalWords=d.words.length*wordTargets.length;
    const allFmts=new Set(wordTargets.flatMap(t=>t.fmts));
    const fmtLabel=allFmts.has('youtube')&&allFmts.has('reels')?'본편+쇼츠':allFmts.has('youtube')?'본편':'쇼츠';
    const totalFmtCnt=wordTargets.reduce((s,t)=>s+t.fmts.length,0)/Math.max(wordTargets.length,1);
    const total=Math.round(totalWords*langs.length*totalFmtCnt);
    const startEl3=document.getElementById(pfx+'start')||document.getElementById('rc-start');
    if(startEl3) startEl3.textContent=`▶ 렌더링 시작 (${d.words.length}개 × ${wordTargets.length}개 시험 × ${langs.length}개 언어 × ${fmtLabel} = ${total}개 · ${_customTarget==='desktop'?'💻 GPU':'🖥 NAS'})`;
    updateCustomTimeEst();
  }catch(e){}
}

function updateCustomTimeEst(){
  const targets=getTargetRows();
  const langs=getSelectedLangs();
  const perMin=_customTarget==='desktop'?3:12;
  // ID 지정된 행은 ID수, 없으면 30으로 추정
  const totalWords=targets.reduce((s,t)=>{
    const ids=parseIds(t.ids_str);
    return s+(ids.length||30);
  },0);
  const fmtCnt=targets.length?Math.round(targets.reduce((s,t)=>s+(t.fmts?t.fmts.length:1),0)/targets.length):1;
  const total=totalWords*langs.length*fmtCnt*perMin;
  const pfxT=_activeRcPrefix();
  const el=document.getElementById(pfxT+'time-est')||document.getElementById('rc-time-est');
  if(el) el.textContent=`예상 소요: ~${total}분 (${totalWords}개 × ${langs.length}개 언어 × ${fmtCnt}개 포맷 × ${perMin}분)`;
}

async function cancelRender(){
  if(!confirm('렌더링을 취소할까요?\n현재 처리 중인 영상이 완료된 후 다음 항목부터 중단됩니다.')) return;
  try{
    const r=await fetch('/api/render/cancel',{method:'POST'});
    const d=await r.json();
    if(!r.ok){alert('취소 실패: '+(d.error||''));}
    else{
      const cc=document.getElementById('rc-cancel');
      if(cc) cc.style.display='none';
      loadBatchData();loadOverview();
    }
  }catch(e){alert('실패: '+e);}
}

async function startCustomRender(){
  const targets=getTargetRows();
  const langs=getSelectedLangs();
  const renderTarget=_customTarget;
  const convTargets=targets.filter(t=>t.is_conv);
  const wordTargets=targets.filter(t=>!t.is_conv);
  const descParts=[];
  if(wordTargets.length){
    const totalWords=wordTargets.reduce((s,t)=>{const ids=parseIds(t.ids_str);return s+(ids.length||30);},0);
    const fmtCnt=wordTargets.reduce((s,t)=>s+t.fmts.length,0)/Math.max(wordTargets.length,1);
    descParts.push(`단어 ~${Math.round(totalWords*langs.length*fmtCnt)}개`);
  }
  if(convTargets.length){
    const totalEp=convTargets.reduce((s,t)=>s+parseIds(t.conv_range).length,0);
    descParts.push(`회화 ${totalEp}화 × ${langs.length}개 언어`);
  }
  const msg=`${descParts.join('\n')}\n위치: ${renderTarget==='desktop'?'💻 GPU':'🖥 NAS CPU'}\n\n시작할까요?`;
  if(!confirm(msg)) return;
  const pfxS=_activeRcPrefix();
  const btn=document.getElementById(pfxS+'start')||document.getElementById('rc-start');
  const cancelBtn=document.getElementById(pfxS+'cancel')||document.getElementById('rc-cancel');
  btn.disabled=true;btn.textContent='⏳ 요청 중...';
  try{
    // 단어 렌더링 (per-row formats 포함)
    const pfxCheck=_activeRcPrefix();
    const thumbOnlyEl=document.getElementById(pfxCheck+'thumb-only')||document.getElementById('rc-thumb-only');
    const thumbOnly=thumbOnlyEl?thumbOnlyEl.checked:false;
    if(wordTargets.length){
      const body={targets:wordTargets,langs,target:renderTarget,thumb_only:thumbOnly};
      const r=await fetch('/api/render/custom',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify(body)});
      const d=await r.json();
      if(!r.ok){alert('단어 렌더링 오류: '+(d.error||''));btn.disabled=false;btn.textContent='▶ 렌더링 시작';return;}
    }
    // 회화 렌더링 (선택된 포맷만)
    for(const t of convTargets){
      const epIds=parseIds(t.conv_range);
      for(const epId of epIds){
        for(const lang of langs){
          for(const fmt of (t.fmts||['youtube'])){
            await fetch('/api/conv/render',{method:'POST',headers:{'Content-Type':'application/json'},
              body:JSON.stringify({theme_id:String(epId),lang,target:renderTarget,fmt})});
          }
        }
      }
    }
    if(cancelBtn) cancelBtn.style.display='';
    loadJobQueue();rpTab('batch');loadOverview();
  }catch(e){alert('실패: '+e);}
  finally{btn.disabled=false;updateCustomPreview();}
}

async function loadHistoryDate(){
  const date=document.getElementById('rp-date-pick').value;
  if(!date)return;
  try{
    const r=await fetch('/api/batch/date?date='+date);
    const items=await r.json();
    const el=document.getElementById('rp-history-list');
    if(!items.length){el.innerHTML='<div style="color:#8b949e;text-align:center;padding:20px;">이 날 생성된 영상이 없습니다</div>';return;}
    el.innerHTML=items.map(v=>{
      const c=LVC[v.level]||'#8b949e';
      return `<div style="display:flex;align-items:center;gap:8px;padding:10px 12px;background:#1c2128;border-radius:8px;margin-bottom:5px;border:1px solid #21262d;">
        <span style="color:${c};font-weight:700;font-size:.72rem;">${v.level}급</span>
        <span style="color:#484f58;font-size:.66rem;">#${v.word_id}</span>
        <div style="flex:1;"><div style="font-weight:600;font-size:.84rem;">${v.word}</div><div style="color:#8b949e;font-size:.68rem;">${v.exam}/${v.lang}</div></div>
        ${v.video_id?`<a href="https://youtube.com/watch?v=${v.video_id}" target="_blank" style="color:#f87171;font-size:.78rem;">▶ YT</a>`
          :`<button onclick="manualUpload(${v.word_id},'${v.exam}','${v.lang}',this)" style="padding:3px 8px;background:#0d1b2b;color:#58a6ff;border:1px solid #58a6ff;border-radius:5px;cursor:pointer;font-size:.68rem;" title="YouTube 업로드">⬆ 업로드</button>`}
        <span style="color:#484f58;font-size:.68rem;">${(v.generated_at||'').slice(11,16)}</span>
      </div>`;
    }).join('');
  }catch(e){}
}

async function loadConfigSlots(){
  try{const r=await fetch('/api/schedule');const d=await r.json();_configSlots=[...(d.slots||[])];renderConfigSlots();}catch(e){}
}

function renderConfigSlots(){
  const el=document.getElementById('rp-config-slots');
  if(!el)return;
  const exams=['TOPIK','TOEIC','JLPT','IELTS','HSK'];
  const langs=['EN','JP','CN','VN','ES','KO','FR','DE'];
  const levels=[1,2,3,4,5,6];
  const fmtOpts=[['both','▶+📱 둘다'],['youtube','▶ YouTube'],['reels','📱 릴스']];
  el.innerHTML=_configSlots.map((s,i)=>{
    const sf=s.fmt||'both';
    return `
    <div class="slot">
      <span style="color:var(--muted2);font-size:.66rem;min-width:14px;">${i+1}</span>
      <select onchange="_configSlots[${i}].exam=this.value" class="inp" style="padding:3px 5px;font-size:.7rem;">
        ${exams.map(e=>`<option${s.exam===e?' selected':''}>${e}</option>`).join('')}
      </select>
      <select onchange="_configSlots[${i}].lang=this.value" class="inp" style="padding:3px 5px;font-size:.7rem;">
        ${langs.map(l=>`<option${s.lang===l?' selected':''}>${l}</option>`).join('')}
      </select>
      <select onchange="_configSlots[${i}].level=+this.value" class="inp" style="padding:3px 5px;font-size:.7rem;">
        ${levels.map(lv=>`<option${s.level===lv?' selected':''}>${lv}</option>`).join('')}
      </select>
      <select onchange="_configSlots[${i}].fmt=this.value" class="inp" style="padding:3px 5px;font-size:.7rem;color:${sf==='reels'?'var(--amber)':sf==='youtube'?'var(--green)':'var(--accent)'};">
        ${fmtOpts.map(([v,t])=>`<option value="${v}"${sf===v?' selected':''}>${t}</option>`).join('')}
      </select>
      <span style="font-size:.7rem;">${_FLAGS[s.lang]||''}</span>
      <button onclick="_configSlots.splice(${i},1);renderConfigSlots()" style="margin-left:auto;background:none;border:none;color:var(--red);cursor:pointer;font-size:.82rem;">✕</button>
    </div>`}).join('');
}

function addSlot(){_configSlots.push({exam:'TOPIK',lang:'EN',level:1,fmt:'both'});renderConfigSlots();}

async function saveSchedule(){
  const r=await fetch('/api/schedule',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({slots:_configSlots})});
  if(r.ok){alert('저장됐습니다!');loadBatchData();}else alert('저장 실패');
}

function resetSchedule(){
  _configSlots=[
    {exam:'TOPIK',lang:'EN',level:1,fmt:'both'},{exam:'TOPIK',lang:'EN',level:2,fmt:'both'},{exam:'TOPIK',lang:'EN',level:3,fmt:'both'},
    {exam:'TOPIK',lang:'JP',level:1,fmt:'both'},{exam:'TOPIK',lang:'JP',level:2,fmt:'both'},{exam:'TOPIK',lang:'JP',level:3,fmt:'both'},
    {exam:'TOPIK',lang:'ES',level:1,fmt:'both'},{exam:'TOPIK',lang:'ES',level:2,fmt:'both'},{exam:'TOPIK',lang:'ES',level:3,fmt:'both'},
  ];
  renderConfigSlots();
}

// ── 초기화 ──────────────────────────────────────────────
updateIllustCost2();
loadOverview();
// 일러스트 browse 초기화: 1급 시작 ID(1) + 범위 힌트
(()=>{
  const lv=+document.getElementById('illust-browse-level').value||1;
  const {min,max}=lvIdRange(lv);
  const inp=document.getElementById('illust-browse-id');
  inp.min=min; inp.max=max; inp.value=min;
  const hint=document.getElementById('illust-browse-id-range');
  if(hint) hint.textContent=`(${min}~${max})`;
})();
setInterval(loadOverview,5000);
setInterval(()=>{
  if(_currentView==='render'){loadJobQueue();if(_rpTab==='batch')loadBatchData();loadLiveStatus();}
  if(_currentView==='work'){loadJobQueue();loadLiveStatus();}
},3000);
setInterval(()=>{if(_currentView==='conv')pollConvProgress();},3000);

// ── 기본 회화 ────────────────────────────────────────────────
let _convLang = 'EN';
let _convThemes = [];

function convSetLang(lang){
  _convLang = lang;
  document.querySelectorAll('.conv-lang-btn').forEach(b=>{
    b.className = 'btn conv-lang-btn ' + (b.dataset.lang===lang ? 'btn-p active' : 'btn-m');
  });
  renderConvThemes();
}

async function loadConvThemes(){
  try{
    const r = await fetch('/api/conv/themes');
    const d = await r.json();
    _convThemes = d.themes || [];
    _convThemesAll = _convThemes; // 오늘의 회화와 공유
    renderConvThemes();
    const emptyEl = document.getElementById('conv-empty');
    const themesEl = document.getElementById('conv-themes');
    if(emptyEl) emptyEl.style.display = _convThemes.length ? 'none' : 'block';
    if(themesEl) themesEl.style.display = _convThemes.length ? 'grid' : 'none';
  }catch(e){
    const emptyEl = document.getElementById('conv-empty');
    const themesEl = document.getElementById('conv-themes');
    if(emptyEl) emptyEl.style.display = 'block';
    if(themesEl) themesEl.style.display = 'none';
  }
}

function renderConvThemes(){
  const tbody = document.getElementById('conv-themes-tbody');
  const empty = document.getElementById('conv-empty');
  if(!tbody) return;
  const LANGS = CONV_LANGS;
  const filterLang   = (document.getElementById('cv-filter-lang')  ||{}).value || '';
  const filterStatus = (document.getElementById('cv-filter-status')||{}).value || '';
  let rows = [];
  for(const t of _convThemes){
    const ko = t.title.KR || t.title.ko || t.id;
    for(const lang of LANGS){
      if(filterLang && lang !== filterLang) continue;
      const ls = t.langs[lang] || {};
      if(filterStatus==='rendered'       && !ls.rendered)       continue;
      if(filterStatus==='uploaded'       && !ls.uploaded)       continue;
      if(filterStatus==='reels_rendered' && !ls.reels_rendered) continue;
      if(filterStatus==='reels_uploaded' && !ls.reels_uploaded) continue;
      if(filterStatus==='pending'        && (ls.rendered||ls.reels_rendered)) continue;
      const vid = ls.video_id;
      const ytSt = `<div style="display:flex;flex-direction:column;align-items:center;gap:2px;font-size:.62rem;">
        <span class="badge ${ls.rendered?'badge-g':'badge-m'}" title="렌더됨">${ls.rendered?'렌더✓':'렌더○'}</span>
        <span class="badge ${ls.uploaded?'badge-done':'badge-m'}" title="업로드됨">${ls.uploaded?'업로드✓':'업로드○'}</span>
      </div>`;
      const rlSt = `<div style="display:flex;flex-direction:column;align-items:center;gap:2px;font-size:.62rem;">
        <span class="badge ${ls.reels_rendered?'badge-g':'badge-m'}" title="렌더됨">${ls.reels_rendered?'렌더✓':'렌더○'}</span>
        <span class="badge ${ls.reels_uploaded?'badge-done':'badge-m'}" title="업로드됨">${ls.reels_uploaded?'업로드✓':'업로드○'}</span>
      </div>`;
      rows.push(`<tr>
        <td style="color:var(--muted2);font-size:.7rem;">${t.id}</td>
        <td>
          <span style="margin-right:6px;">${t.emoji}</span>
          <span style="font-weight:600;">${ko}</span>
        </td>
        <td style="text-align:center;color:var(--muted);">${t.phrase_count}</td>
        <td style="text-align:center;">${LANG_FLAGS[lang]} <span style="font-size:.72rem;color:var(--muted);">${lang}</span></td>
        <td style="text-align:center;">${ytSt}</td>
        <td style="text-align:center;">${rlSt}</td>
        <td style="text-align:center;">
          ${vid?`<a href="https://youtube.com/watch?v=${vid}" target="_blank" style="color:var(--red);font-size:.72rem;">▶</a>`:'–'}
        </td>
        <td style="text-align:right;padding-right:8px;">
          <div style="display:flex;gap:3px;justify-content:flex-end;flex-wrap:wrap;">
            <button class="btn btn-a" onclick="convRenderLang('${t.id}','${lang}','youtube')" style="font-size:.62rem;padding:2px 7px;" title="YouTube 렌더링">▶ ${ls.rendered?'재렌더':'렌더'}</button>
            <button class="btn btn-g" onclick="convUploadLang('${t.id}','${lang}','youtube')" style="font-size:.62rem;padding:2px 7px;" ${!ls.rendered?'disabled':''} title="YouTube 업로드">▶ 업로드</button>
            <button class="btn" onclick="convRenderLang('${t.id}','${lang}','reels')" style="font-size:.62rem;padding:2px 7px;background:#4a1942;color:#f0abfc;border:1px solid #6b21a8;" title="쇼츠 렌더링">📱 ${ls.reels_rendered?'재렌더':'렌더'}</button>
            <button class="btn" onclick="convUploadLang('${t.id}','${lang}','reels')" style="font-size:.62rem;padding:2px 7px;background:#1a2d3a;color:#67e8f9;border:1px solid #0e7490;" ${!ls.reels_rendered?'disabled':''} title="쇼츠 업로드">📱 업로드</button>
            <button class="btn" onclick="convDelete('${t.id}','${lang}')" style="font-size:.62rem;padding:2px 7px;background:#2d1515;color:#f87171;border:1px solid #7f1d1d;" ${(!ls.rendered&&!ls.reels_rendered)?'disabled':''} title="삭제">🗑</button>
          </div>
        </td>
      </tr>`);
    }
  }
  if(!_convThemes.length){
    tbody.innerHTML='';
    if(empty) empty.style.display='block';
  } else {
    if(empty) empty.style.display='none';
    tbody.innerHTML = rows.join('');
  }
  const cnt = document.getElementById('cv-vcount');
  if(cnt) cnt.textContent = rows.length+'개';
}

let _convTarget = 'nas';

function convSetTarget(t){
  _convTarget=t;
  document.getElementById('conv-btn-nas').className='btn '+(t==='nas'?'btn-g':'btn-m');
  document.getElementById('conv-btn-desktop').className='btn '+(t==='desktop'?'btn-p':'btn-m');
}

async function convRender(themeId){
  await convRenderLang(themeId, _convLang);
}
async function convRenderLang(themeId, lang, fmt='youtube'){
  const label = fmt==='reels'?'📱 쇼츠':'▶ YouTube';
  if(!confirm(`[${lang}] "${themeId}" ${label} 렌더링할까요? (${_convTarget==='desktop'?'💻 GPU':'🖥 NAS'})`)) return;
  try{
    const r = await fetch('/api/conv/render',{method:'POST',headers:{'Content-Type':'application/json'},
      body: JSON.stringify({theme_id:themeId, lang:lang, fmt:fmt, target:_convTarget})});
    const d = await r.json();
    if(!r.ok){ alert('오류: '+(d.error||'')); return; }
    loadJobQueue();
  }catch(e){ alert('실패: '+e); }
}

async function convUpload(themeId){
  await convUploadLang(themeId, _convLang);
}
async function convUploadLang(themeId, lang, fmt='youtube'){
  const label = fmt==='reels'?'📱 쇼츠':'▶ YouTube';
  if(!confirm(`[${lang}] "${themeId}" ${label} 업로드할까요?`)) return;
  try{
    const r = await fetch('/api/conv/upload',{method:'POST',headers:{'Content-Type':'application/json'},
      body: JSON.stringify({theme_id:themeId, lang:lang, fmt:fmt})});
    const d = await r.json();
    if(!r.ok){ alert('오류: '+(d.error||'')); return; }
    alert(`업로드 완료!\nhttps://youtube.com/watch?v=${d.video_id}`);
    loadConvThemes();
  }catch(e){ alert('실패: '+e); }
}
async function convDelete(themeId, lang){
  if(!confirm(`[${lang}] "${themeId}" 회화 영상을 삭제할까요?\n(파일 및 로그에서 제거됩니다)`)) return;
  try{
    const r = await fetch('/api/conv/delete',{method:'POST',headers:{'Content-Type':'application/json'},
      body: JSON.stringify({theme_id:themeId, lang:lang})});
    const d = await r.json();
    if(!r.ok){ alert('오류: '+(d.error||'')); return; }
    loadConvThemes();
  }catch(e){ alert('실패: '+e); }
}

// ── K-드라마 ─────────────────────────────────────────────
let _kdramaThemes = [];
let _kdTarget = 'nas';

function kdSetTarget(t){
  _kdTarget=t;
  document.getElementById('kd-btn-nas').className='btn '+(t==='nas'?'btn-g':'btn-m');
  document.getElementById('kd-btn-desktop').className='btn '+(t==='desktop'?'btn-p':'btn-m');
}

async function loadKdramaThemes(){
  try{
    const r = await fetch('/api/kdrama/themes');
    const d = await r.json();
    _kdramaThemes = d.themes || [];
    renderKdramaThemes();
  }catch(e){
    document.getElementById('kd-empty').style.display='block';
  }
  // 일러스트 상태도 같이 로드
  loadKdramaIllustStatus();
}

// ── K-드라마 일러스트 상태/생성 ────────────────────────────
let _kdItems = [];

async function loadKdramaIllustStatus(){
  try{
    const r = await fetch('/api/kdrama/illust/status');
    const d = await r.json();
    _kdItems = d.items||[];
    const total = d.total||0, intro = d.intro_done||0;
    const phrasesTotal = d.phrases_total||(total*10);
    const phrasesDone = d.phrases_done||0;
    const allDone = d.all_done||0;
    const introPct = total ? Math.round(intro/total*100) : 0;
    const phrasePct = phrasesTotal ? Math.round(phrasesDone/phrasesTotal*100) : 0;
    const badge = document.getElementById('kd-illust-badge');
    const doneTxt = document.getElementById('kd-illust-done-txt');
    const bar  = document.getElementById('kd-illust-done-bar');
    if(badge) badge.textContent = `완성 ${allDone}/${total}`;
    if(doneTxt) doneTxt.textContent = `인트로 ${intro}/${total} (${introPct}%) · Phrase ${phrasesDone}/${phrasesTotal} (${phrasePct}%)`;
    if(bar) bar.style.width = introPct+'%';
    // 테마 카드 리스트 (회화 일러스트와 동일 패턴)
    const list = document.getElementById('kd-illust-list');
    if(list){
      list.innerHTML = _kdItems.map(it=>{
        const total11 = 11;
        const done = (it.intro_done?1:0) + (it.phrases_done||0);
        const pct = Math.round(done/total11*100);
        const allDone = it.all_done;
        const barCol = allDone ? 'var(--green)' : pct>50 ? 'var(--amber)' : 'var(--accent)';
        const col = '#C77DFF';
        return `<div style="background:var(--bg3);border-radius:10px;border:1px solid var(--border);overflow:hidden;display:flex;flex-direction:column;">
          <div style="height:3px;background:${col};"></div>
          <div style="padding:10px 12px;flex:1;">
            <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:6px;margin-bottom:8px;">
              <div style="min-width:0;flex:1;">
                <span style="font-size:.58rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:${col};display:block;margin-bottom:3px;">${it.category||''}</span>
                <div style="font-size:.85rem;font-weight:700;line-height:1.3;overflow-wrap:break-word;word-break:keep-all;">${it.situation||''}</div>
              </div>
              <span style="font-size:.6rem;background:var(--bg);border:1px solid var(--border);padding:2px 7px;border-radius:99px;white-space:nowrap;flex-shrink:0;color:var(--muted);font-weight:600;">ID ${it.id}</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;font-size:.65rem;color:var(--muted);margin-bottom:4px;">
              <span>일러스트</span>
              <span style="font-weight:700;color:${allDone?'var(--green)':'var(--fg)'};">${done}<span style="color:var(--muted);font-weight:400;">/${total11}</span></span>
            </div>
            <div style="height:4px;background:var(--bg);border-radius:2px;margin-bottom:10px;overflow:hidden;">
              <div style="height:100%;width:${pct}%;background:${barCol};border-radius:2px;transition:width .3s;"></div>
            </div>
            <div style="display:flex;gap:5px;">
              <button class="btn btn-p" style="flex:1;font-size:.72rem;padding:5px 0;" onclick="kdStartIllustOne(${it.id})">
                ${allDone?'↺ 재생성':'▶ 생성'}
              </button>
              <button class="btn btn-m" style="font-size:.72rem;padding:5px 10px;" onclick="kdBrowseTheme(${it.id})" title="패널 뷰어">&#9654;</button>
            </div>
          </div>
        </div>`;
      }).join('');
    }
  }catch(e){}
}

function kdBrowseTheme(tid){
  const inp=document.getElementById('kd-browse-id');
  if(inp) inp.value=tid;
  loadKdramaIllustBrowse();
  setTimeout(()=>{
    const card=document.getElementById('kd-browse-card');
    if(card) card.scrollIntoView({behavior:'smooth',block:'start'});
  },120);
}

function kdBrowseNav(dir){
  const inp=document.getElementById('kd-browse-id');
  if(!inp) return;
  const ids=_kdItems.map(i=>i.id);
  const min=ids.length?Math.min(...ids):1;
  const max=ids.length?Math.max(...ids):100;
  inp.value=Math.min(max,Math.max(min,(+inp.value||1)+dir));
  loadKdramaIllustBrowse();
}

async function kdStartIllustOne(tid){
  if(!confirm(`테마 #${tid} 일러스트 11장(인트로+Phrase 10) 생성/재생성?`)) return;
  try{
    const r=await fetch('/api/kdrama/illust/start',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({theme_id:tid, overwrite:true})});
    const d=await r.json();
    if(!r.ok){ alert('오류: '+(d.error||'')); return; }
    alert(`큐에 추가됨 (job ${d.job_id})`);
    loadJobQueue();
  }catch(e){ alert('실패: '+e); }
}

async function loadKdramaIllustBrowse(){
  const id=+(document.getElementById('kd-browse-id')||{}).value||1;
  const r=await fetch('/api/kdrama/illust/browse/'+id);
  const grid=document.getElementById('kd-browse-grid');
  const infoBar=document.getElementById('kd-browse-info-bar');
  if(!grid) return;
  if(!r.ok){
    if(infoBar) infoBar.style.display='none';
    grid.innerHTML=`<div style="grid-column:1/-1;text-align:center;padding:32px;color:var(--muted);font-size:.8rem;">테마를 찾을 수 없습니다.</div>`;
    return;
  }
  const d=await r.json();
  const col='#C77DFF';
  if(infoBar){
    infoBar.style.display='block';
    document.getElementById('kd-browse-cat-chip').textContent=d.category||'';
    document.getElementById('kd-browse-cat-chip').style.background=col;
    document.getElementById('kd-browse-sit-ko').textContent=d.situation||'';
    document.getElementById('kd-browse-sit-en').textContent=d.situation_en||'';
    const existCount=(d.items||[]).filter(i=>i.exists).length;
    document.getElementById('kd-browse-count').textContent=`${existCount} / ${(d.items||[]).length} 패널`;
  }
  const ts=Date.now();
  grid.innerHTML=(d.items||[]).map((it,i)=>{
    const img=it.exists
      ?`<img src="${it.url}?t=${ts}" loading="lazy"
           style="width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:8px;cursor:pointer;display:block;"
           onclick="window.open('${it.url}?t=${ts}','_blank')">`
      :`<div style="width:100%;aspect-ratio:1/1;background:var(--bg);border-radius:8px;
               display:flex;flex-direction:column;align-items:center;justify-content:center;
               gap:6px;color:var(--muted);">
          <span style="font-size:1.6rem;">🎬</span>
          <span style="font-size:.65rem;">미생성</span>
        </div>`;
    const labelKo = it.ko ? `<div style="font-size:.7rem;font-weight:600;line-height:1.35;margin-top:5px;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;" title="${(it.ko||'').replace(/"/g,'&quot;')}">${it.ko}</div>` : '';
    const labelEn = it.en ? `<div style="font-size:.6rem;color:var(--muted);margin-top:1px;line-height:1.3;overflow:hidden;display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;">${it.en}</div>` : '';
    const delBtn = it.exists
      ? `<button class="btn" style="font-size:.6rem;padding:2px 6px;background:#2d1515;color:#f87171;border:1px solid #7f1d1d;" onclick="kdDeletePanel(${d.id},'${it.key}')" title="이 패널 삭제">🗑</button>`
      : '';
    return `<div style="background:var(--bg3);border-radius:10px;border:1px solid var(--border);padding:8px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;gap:4px;">
        <span style="font-size:.62rem;font-weight:700;color:${it.exists?'var(--green)':'var(--muted)'};">${it.label||it.key}</span>
        <div style="display:flex;gap:3px;">
          <button class="btn btn-m" style="font-size:.6rem;padding:2px 6px;" onclick="kdRegenPanel(${d.id},'${it.key}')" title="이 패널만 재생성">↺</button>
          ${delBtn}
        </div>
      </div>
      ${img}
      ${labelKo}
      ${labelEn}
    </div>`;
  }).join('');
}

async function kdDeletePanel(tid, key){
  if(!confirm(`테마 #${tid} 의 ${key} 패널 이미지를 삭제할까요?`)) return;
  try{
    const r=await fetch('/api/kdrama/illust/delete',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({theme_id:tid, key:key})});
    const d=await r.json();
    if(!r.ok){ alert('오류: '+(d.error||'')); return; }
    // 뷰어와 상태 새로고침
    loadKdramaIllustBrowse();
    loadKdramaIllustStatus();
  }catch(e){ alert('실패: '+e); }
}

async function kdRegenPanel(tid, key){
  // intro / phrase_1~10 단일 재생성 — 백엔드는 전체 재생성 기반이므로 overwrite=true로 단일 idx 호출
  if(!confirm(`테마 #${tid} 의 ${key} 패널 재생성?`)) return;
  try{
    const body={theme_id:tid, overwrite:true};
    if(key==='intro') body.intro_only=true;
    else if(key.startsWith('phrase_')) body.phrases_only=true;  // (백엔드가 단일 phrase 미지원이면 전체 phrase 재생성)
    const r=await fetch('/api/kdrama/illust/start',{method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    const d=await r.json();
    if(!r.ok){ alert('오류: '+(d.error||'')); return; }
    alert(`큐에 추가됨 (job ${d.job_id})`);
    loadJobQueue();
  }catch(e){ alert('실패: '+e); }
}

async function kdStartIllust(){
  const s = document.getElementById('kd-illust-start').value;
  const e = document.getElementById('kd-illust-end').value;
  const overwrite = document.getElementById('kd-illust-overwrite').checked;
  const mode = document.getElementById('kd-illust-mode').value || 'all';
  let body = {overwrite};
  if(s && e){ body.start = parseInt(s); body.end = parseInt(e); }
  if(mode === 'intro_only')  body.intro_only = true;
  if(mode === 'phrases_only') body.phrases_only = true;
  const scope = (s&&e) ? `#${s}~${e}` : '전체 100개';
  const modeLabel = {all:'인트로+Phrase 11장씩', intro_only:'인트로만 1장씩', phrases_only:'Phrase 10장씩'}[mode];
  const perTheme = mode==='all'?11 : (mode==='intro_only'?1 : 10);
  const themes = (s&&e) ? (parseInt(e)-parseInt(s)+1) : 100;
  const cost = (themes * perTheme * 0.04).toFixed(2);
  if(!confirm(`K-드라마 일러스트 ${scope} ${modeLabel} 생성.\n총 ${themes*perTheme}장, 예상 비용 ~$${cost}\n\n계속할까요?`)) return;
  try{
    const r = await fetch('/api/kdrama/illust/start',{method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    const d = await r.json();
    if(!r.ok){ alert('오류: '+(d.error||'')); return; }
    alert(`큐에 추가됨 (job ${d.job_id})\n작업 센터에서 진행률 확인 가능합니다.`);
    loadJobQueue();
  }catch(e){ alert('실패: '+e); }
}

const KD_CAT_COLOR={
  '연애/고백/이별':'#FF6B9D','감탄/반응':'#FFB347','드라마 클리셰':'#C77DFF',
  '싸움/갈등/화해':'#FF6B6B','감정 표현':'#74B9FF','일상 구어체':'#55EFC4',
  '직장/학교':'#636E72','가족/관계':'#FDCB6E','속어/유행어':'#00CEC9'
};

function renderKdramaThemes(){
  const tbody = document.getElementById('kd-themes-tbody');
  const empty = document.getElementById('kd-empty');
  if(!tbody) return;
  const LANGS = ['EN','JP','CN','VN','ES'];
  const filterLang   = (document.getElementById('kd-filter-lang')  ||{}).value || '';
  const filterStatus = (document.getElementById('kd-filter-status')||{}).value || '';
  let rows = [];
  for(const t of _kdramaThemes){
    for(const lang of LANGS){
      if(filterLang && lang !== filterLang) continue;
      const ls = (t.langs && t.langs[lang]) || {};
      if(filterStatus==='rendered'       && !ls.rendered)       continue;
      if(filterStatus==='uploaded'       && !ls.uploaded)       continue;
      if(filterStatus==='reels_rendered' && !ls.reels_rendered) continue;
      if(filterStatus==='reels_uploaded' && !ls.reels_uploaded) continue;
      if(filterStatus==='pending'        && (ls.rendered||ls.reels_rendered)) continue;
      const vid = ls.video_id;
      const titleKo = (t.title && (t.title.ko || t.title.KR)) || t.situation || t.id;
      const catColor = KD_CAT_COLOR[t.category] || '#888';
      const catChip = `<span style="font-size:.58rem;padding:1px 6px;border-radius:99px;background:${catColor}22;color:${catColor};border:1px solid ${catColor}55;white-space:nowrap;">${t.category||''}</span>`;
      const ytSt = `<div style="display:flex;flex-direction:column;align-items:center;gap:2px;font-size:.62rem;">
        <span class="badge ${ls.rendered?'badge-g':'badge-m'}">${ls.rendered?'렌더✓':'렌더○'}</span>
        <span class="badge ${ls.uploaded?'badge-done':'badge-m'}">${ls.uploaded?'업로드✓':'업로드○'}</span>
      </div>`;
      const rlSt = `<div style="display:flex;flex-direction:column;align-items:center;gap:2px;font-size:.62rem;">
        <span class="badge ${ls.reels_rendered?'badge-g':'badge-m'}">${ls.reels_rendered?'렌더✓':'렌더○'}</span>
        <span class="badge ${ls.reels_uploaded?'badge-done':'badge-m'}">${ls.reels_uploaded?'업로드✓':'업로드○'}</span>
      </div>`;
      rows.push(`<tr>
        <td style="color:var(--muted2);font-size:.7rem;">${t.id}</td>
        <td><span style="margin-right:4px;">${t.emoji||''}</span><span style="font-weight:600;">${titleKo}</span></td>
        <td style="text-align:center;">${catChip}</td>
        <td style="text-align:center;color:var(--muted);">${t.phrase_count||0}</td>
        <td style="text-align:center;">${LANG_FLAGS[lang]} <span style="font-size:.72rem;color:var(--muted);">${lang}</span></td>
        <td style="text-align:center;">${ytSt}</td>
        <td style="text-align:center;">${rlSt}</td>
        <td style="text-align:center;">${vid?`<a href="https://youtube.com/watch?v=${vid}" target="_blank" style="color:var(--red);font-size:.72rem;">▶</a>`:'–'}</td>
        <td style="text-align:right;padding-right:8px;">
          <div style="display:flex;gap:3px;justify-content:flex-end;flex-wrap:wrap;">
            <button class="btn btn-a" onclick="kdRenderLang('${t.id}','${lang}','youtube')" style="font-size:.62rem;padding:2px 7px;">▶ ${ls.rendered?'재렌더':'렌더'}</button>
            <button class="btn btn-g" onclick="kdUploadLang('${t.id}','${lang}','youtube')" style="font-size:.62rem;padding:2px 7px;" ${!ls.rendered?'disabled':''}>▶ 업로드</button>
            <button class="btn" onclick="kdRenderLang('${t.id}','${lang}','reels')" style="font-size:.62rem;padding:2px 7px;background:#4a1942;color:#f0abfc;border:1px solid #6b21a8;">📱 ${ls.reels_rendered?'재렌더':'렌더'}</button>
            <button class="btn" onclick="kdUploadLang('${t.id}','${lang}','reels')" style="font-size:.62rem;padding:2px 7px;background:#1a2d3a;color:#67e8f9;border:1px solid #0e7490;" ${!ls.reels_rendered?'disabled':''}>📱 업로드</button>
          </div>
        </td>
      </tr>`);
    }
  }
  if(!_kdramaThemes.length){
    tbody.innerHTML='';
    if(empty) empty.style.display='block';
  } else {
    if(empty) empty.style.display='none';
    tbody.innerHTML = rows.join('');
  }
  const cnt = document.getElementById('kd-vcount');
  if(cnt) cnt.textContent = rows.length+'개';
}

async function kdRenderLang(themeId, lang, fmt='youtube'){
  const label = fmt==='reels'?'📱 쇼츠':'▶ YouTube';
  if(!confirm(`[${lang}] K-드라마 #${themeId} ${label} 렌더링할까요? (${_kdTarget==='desktop'?'💻 GPU':'🖥 NAS'})`)) return;
  try{
    const r = await fetch('/api/kdrama/render',{method:'POST',headers:{'Content-Type':'application/json'},
      body: JSON.stringify({theme_id:themeId, lang:lang, fmt:fmt, target:_kdTarget})});
    const d = await r.json();
    if(!r.ok){ alert('오류: '+(d.error||'')); return; }
    loadJobQueue();
  }catch(e){ alert('실패: '+e); }
}

async function kdUploadLang(themeId, lang, fmt='youtube'){
  const label = fmt==='reels'?'📱 쇼츠':'▶ YouTube';
  if(!confirm(`[${lang}] K-드라마 #${themeId} ${label} 업로드할까요?`)) return;
  try{
    const r = await fetch('/api/kdrama/upload',{method:'POST',headers:{'Content-Type':'application/json'},
      body: JSON.stringify({theme_id:themeId, lang:lang, fmt:fmt})});
    const d = await r.json();
    if(!r.ok){ alert('오류: '+(d.error||'')); return; }
    alert(`업로드 완료!\nhttps://youtube.com/watch?v=${d.video_id}`);
    loadKdramaThemes();
  }catch(e){ alert('실패: '+e); }
}

async function pollConvProgress(){
  try{
    const r = await fetch('/api/conv/render/status');
    const d = await r.json();
    const prog = document.getElementById('conv-progress');
    if(!prog) return;
    if(d.status === 'idle'){ prog.style.display='none'; return; }
    prog.style.display = 'block';
    const pct = d.pct || 0;
    document.getElementById('conv-prog-bar').style.width = pct+'%';
    document.getElementById('conv-prog-pct').textContent = pct+'%';
    document.getElementById('conv-prog-msg').textContent = d.msg || '';
    if(d.status === 'done'){
      document.getElementById('conv-prog-label').textContent = '✓ 렌더링 완료';
      document.getElementById('conv-prog-label').style.color = 'var(--green)';
      document.getElementById('conv-prog-bar').style.background = 'var(--green)';
      document.getElementById('conv-prog-pct').style.color = 'var(--green)';
      setTimeout(()=>{ prog.style.display='none'; loadConvThemes(); }, 3000);
    } else if(d.status === 'failed'){
      document.getElementById('conv-prog-label').textContent = '✗ 렌더링 실패';
      document.getElementById('conv-prog-label').style.color = 'var(--red)';
    } else {
      document.getElementById('conv-prog-label').textContent = `🎬 렌더링 중... [${d.lang||''}] ${d.theme_id||''}`;
      document.getElementById('conv-prog-label').style.color = 'var(--amber)';
    }
  }catch(e){}
}

// ── 회화 일러스트·영상 ──────────────────────────────────────
let _phSituations = [];
let _phTab = 'illust';
let _phIllustPollTimer = null;
let _phVideoPollTimer  = null;
let _phBrowseData  = null;
let _phRegenPoll   = null;

// 일러스트 탭 데이터 로드
async function loadIllustData(){
  try{
    const r=await fetch('/api/overview');
    const d=await r.json();
    if(d.illustration) renderIllustStats(d.illustration,'iv');
  }catch(e){}
}

async function loadPhraseSituations(){
  try{
    const r = await fetch('/api/phrase/situations');
    const d = await r.json();
    _phSituations = d.situations || [];
    renderPhraseIllustList();
    renderPhraseVideoList();
    // 현황 요약 바 업데이트
    const total = _phSituations.length;
    const done  = _phSituations.filter(s=>s.illust_done>=s.illust_total&&s.illust_total>0).length;
    const pct   = total ? Math.round(done/total*100) : 0;
    const txt   = document.getElementById('ph-illust-done-txt');
    const bar   = document.getElementById('ph-illust-done-bar');
    const badge = document.getElementById('ph-illust-badge');
    if(txt)   txt.textContent = `${done} / ${total} 상황 (${pct}%)`;
    if(bar)   bar.style.width = pct+'%';
    if(badge) { badge.textContent=pct+'%'; badge.className='badge '+(pct>=100?'badge-g':pct>50?'badge-p':'badge-m'); }
    if(!_phSituations.length){
      document.getElementById('ph-illust-empty').style.display='';
    } else {
      document.getElementById('ph-illust-empty').style.display='none';
    }
    pollPhraseIllustProg();
    pollPhraseVideoProg();
  }catch(e){console.error('phrase situations load error',e);}
}

const _CAT_COLORS={'여행':'#4682b4','식사':'#c86450','쇼핑':'#b464b4','의료':'#50a078','인사':'#dca03c','일상':'#648cc8','주거':'#8c7864','여가':'#50b4a0','비즈니스':'#3c5080','K-Culture':'#c85078'};

function renderPhraseIllustList(){
  const el = document.getElementById('ph-illust-list');
  if(!_phSituations.length){el.innerHTML='';return;}
  el.innerHTML = _phSituations.map(s=>{
    const pct = s.illust_total ? Math.round(s.illust_done/s.illust_total*100) : 0;
    const col = _CAT_COLORS[s.category]||'#818cf8';
    const done = pct===100;
    const barCol = done ? 'var(--green)' : pct>50 ? 'var(--amber)' : 'var(--accent)';
    // 상황명 글자 수에 따라 폰트 크기 조정
    const koLen = (s.situation||'').length;
    const koFs = koLen > 16 ? '.75rem' : koLen > 12 ? '.8rem' : '.85rem';
    const enLen = (s.situation_en||'').length;
    const enFs = enLen > 28 ? '.62rem' : '.68rem';
    return `<div style="background:var(--bg3);border-radius:10px;border:1px solid var(--border);overflow:hidden;display:flex;flex-direction:column;">
      <div style="height:3px;background:${col};"></div>
      <div style="padding:10px 12px;flex:1;">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:6px;margin-bottom:8px;">
          <div style="min-width:0;flex:1;">
            <span style="font-size:.58rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:${col};display:block;margin-bottom:3px;">${s.category}</span>
            <div style="font-size:${koFs};font-weight:700;line-height:1.3;overflow-wrap:break-word;word-break:keep-all;">${s.situation}</div>
            <div style="font-size:${enFs};color:var(--muted);margin-top:2px;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;">${s.situation_en||''}</div>
          </div>
          <span style="font-size:.6rem;background:var(--bg);border:1px solid var(--border);padding:2px 7px;border-radius:99px;white-space:nowrap;flex-shrink:0;color:var(--muted);font-weight:600;">ID ${s.id}</span>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;font-size:.65rem;color:var(--muted);margin-bottom:4px;">
          <span>일러스트</span>
          <span style="font-weight:700;color:${done?'var(--green)':'var(--fg)'};">${s.illust_done}<span style="color:var(--muted);font-weight:400;">/${s.illust_total}</span></span>
        </div>
        <div style="height:4px;background:var(--bg);border-radius:2px;margin-bottom:10px;overflow:hidden;">
          <div style="height:100%;width:${pct}%;background:${barCol};border-radius:2px;transition:width .3s;"></div>
        </div>
        <div style="display:flex;gap:5px;">
          <button class="btn btn-p" style="flex:1;font-size:.72rem;padding:5px 0;" onclick="startPhraseIllust(${s.id})">
            ${done?'↺ 재생성':'▶ 생성'}
          </button>
          <button class="btn btn-m" style="font-size:.72rem;padding:5px 10px;" onclick="phBrowseSit(${s.id})" title="패널 뷰어">&#9654;</button>
        </div>
      </div>
    </div>`;
  }).join('');
}

function renderPhraseVideoList(){
  const el = document.getElementById('ph-video-list');
  if(!_phSituations.length){el.innerHTML='';return;}
  el.innerHTML = _phSituations.map(s=>{
    const col = _CAT_COLORS[s.category]||'#818cf8';
    const hasVideo = s.video_exists;
    const genAt = s.video_generated_at ? ago(s.video_generated_at) : null;
    const koLen = (s.situation||'').length;
    const koFs = koLen > 16 ? '.75rem' : koLen > 12 ? '.8rem' : '.85rem';
    const enLen = (s.situation_en||'').length;
    const enFs = enLen > 28 ? '.62rem' : '.68rem';
    return `<div style="background:var(--bg3);border-radius:10px;border:1px solid var(--border);overflow:hidden;">
      <div style="height:3px;background:${col};"></div>
      <div style="padding:10px 12px;">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:6px;margin-bottom:8px;">
          <div style="min-width:0;flex:1;">
            <span style="font-size:.58rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:${col};display:block;margin-bottom:3px;">${s.category}</span>
            <div style="font-size:${koFs};font-weight:700;line-height:1.3;overflow-wrap:break-word;word-break:keep-all;">${s.situation}</div>
            <div style="font-size:${enFs};color:var(--muted);margin-top:2px;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;">${s.situation_en||''}</div>
          </div>
          <span style="font-size:.6rem;background:var(--bg);border:1px solid var(--border);padding:2px 7px;border-radius:99px;white-space:nowrap;flex-shrink:0;color:var(--muted);font-weight:600;">ID ${s.id}</span>
        </div>
        ${hasVideo
          ? `<div style="display:flex;align-items:center;gap:5px;font-size:.67rem;color:var(--green);font-weight:600;margin-bottom:8px;">
               <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><circle cx="6" cy="6" r="5.5" stroke="currentColor" stroke-width="1"/><path d="M4.5 3.5l4 2.5-4 2.5V3.5z" fill="currentColor"/></svg>
               영상 있음${genAt?' · '+genAt:''}</div>`
          : `<div style="font-size:.67rem;color:var(--muted);margin-bottom:8px;">영상 없음</div>`
        }
        <button class="btn btn-p" style="width:100%;font-size:.72rem;padding:5px 0;" onclick="startPhraseVideo(${s.id})">
          ${hasVideo?'↺ 재생성':'▶ 생성'}
        </button>
      </div>
    </div>`;
  }).join('');
}

function phBrowseSit(sitId){
  document.getElementById('ph-browse-id').value=sitId;
  loadPhraseIllustBrowse();
  setTimeout(()=>{
    const bar=document.getElementById('ph-browse-info-bar');
    if(bar) bar.scrollIntoView({behavior:'smooth',block:'start'});
  },120);
}

function phBrowseNav(dir){
  const inp=document.getElementById('ph-browse-id');
  const ids=_phSituations.map(s=>s.id);
  const min=ids.length?Math.min(...ids):1;
  const max=ids.length?Math.max(...ids):99;
  inp.value=Math.min(max,Math.max(min,(+inp.value||1)+dir));
  loadPhraseIllustBrowse();
}

async function loadPhraseIllustBrowse(){
  const id=+document.getElementById('ph-browse-id').value||1;
  const r=await fetch('/api/phrase/illust/browse/'+id);
  const grid=document.getElementById('ph-browse-grid');
  const infoBar=document.getElementById('ph-browse-info-bar');
  if(!r.ok){
    infoBar.style.display='none';
    grid.innerHTML=`<div style="grid-column:1/-1;text-align:center;padding:32px;color:var(--muted);font-size:.8rem;">상황을 찾을 수 없습니다.</div>`;
    return;
  }
  const d=await r.json();
  _phBrowseData=d;
  const col=_CAT_COLORS[d.category]||'#818cf8';

  // 상황 정보 바 업데이트
  infoBar.style.display='block';
  const catChip=document.getElementById('ph-browse-cat-chip');
  catChip.textContent=d.category;
  catChip.style.background=col;
  document.getElementById('ph-browse-sit-ko').textContent=d.situation;
  document.getElementById('ph-browse-sit-en').textContent=d.situation_en||'';
  const existCount=d.items.filter(i=>i.exists).length;
  document.getElementById('ph-browse-count').textContent=`${existCount} / ${d.items.length} 패널`;

  const ts=Date.now();

  // 텍스트 길이에 따라 폰트 크기 반환
  function koFontSize(text){
    const l=(text||'').length;
    if(l>28) return '.62rem';
    if(l>20) return '.68rem';
    if(l>14) return '.73rem';
    return '.78rem';
  }

  grid.innerHTML=d.items.map((it,i)=>{
    const isIntro=it.key==='intro';
    const btnId=`ph-regen-btn-${it.key}`;
    const wrapId=`ph-regen-wrap-${it.key}`;

    const img=it.exists
      ?`<img src="${it.url}?t=${ts}" loading="lazy"
           style="width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:8px;cursor:pointer;display:block;transition:transform .2s;"
           onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform=''"
           onclick="phIllustPreview('${it.url}?t=${ts}')">`
      :`<div style="width:100%;aspect-ratio:1/1;background:var(--bg);border-radius:8px;
               display:flex;flex-direction:column;align-items:center;justify-content:center;
               gap:6px;color:var(--muted);">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
          <span style="font-size:.65rem;">미생성</span>
        </div>`;
    // 생성 중 오버레이 슬롯 (JS가 나중에 채움)
    const genOverlayId=`ph-gen-overlay-${it.key}`;

    // 말풍선 스타일 대화 텍스트
    const koText=it.ko
      ?`<div style="font-size:${koFontSize(it.ko)};font-weight:600;line-height:1.45;
                    color:var(--fg);overflow-wrap:break-word;word-break:keep-all;
                    overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;"
              title="${(it.ko||'').replace(/"/g,'&quot;')}">${it.ko}</div>`:'';
    const enText=it.en
      ?`<div style="font-size:.6rem;color:var(--muted);margin-top:2px;line-height:1.35;
                    overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;"
              title="${(it.en||'').replace(/"/g,'&quot;')}">${it.en}</div>`:'';

    // 레이블 배지 — 인트로는 카테고리 색, 대화는 중립 다크
    const badgeBg=isIntro?col:'rgba(0,0,0,.5)';
    const labelBadge=`<span style="position:absolute;top:7px;left:7px;
        font-size:.58rem;font-weight:700;letter-spacing:.04em;
        background:${badgeBg};color:#fff;padding:2px 8px;border-radius:99px;
        backdrop-filter:blur(4px);">${it.label}</span>`;

    const delBtn=it.exists
      ?`<button onclick="deletePhraseIllust(${d.sit_id},'${it.key}')"
           style="background:transparent;border:1px solid var(--red);color:var(--red);
                  border-radius:6px;font-size:.62rem;padding:4px 8px;cursor:pointer;
                  transition:all .15s;flex-shrink:0;"
           onmouseover="this.style.background='var(--red)';this.style.color='#fff'"
           onmouseout="this.style.background='transparent';this.style.color='var(--red)'"
           title="삭제">&#10005;</button>`:'';

    const cardBorder=isIntro?`border:1px solid ${col}44;`:'border:1px solid var(--border);';
    return `<div id="ph-card-${it.key}" style="background:var(--bg3);border-radius:10px;${cardBorder}overflow:hidden;display:flex;flex-direction:column;transition:box-shadow .3s,border-color .3s;">
      <div id="${wrapId}" style="position:relative;">
        ${img}${labelBadge}
        <div id="${genOverlayId}" style="display:none;position:absolute;inset:0;border-radius:8px;
          display:none;flex-direction:column;align-items:center;justify-content:center;gap:6px;
          background:rgba(0,0,0,.55);backdrop-filter:blur(2px);">
          <div style="width:28px;height:28px;border:3px solid rgba(255,255,255,.3);border-top-color:#a78bfa;border-radius:50%;animation:spin 1s linear infinite;"></div>
          <span style="font-size:.6rem;color:#e2e8f0;font-weight:600;letter-spacing:.04em;">생성 중...</span>
        </div>
      </div>
      <div style="padding:8px 10px;flex:1;display:flex;flex-direction:column;gap:3px;">
        ${koText}${enText}
        <div style="display:flex;gap:5px;margin-top:auto;padding-top:7px;">
          <button id="${btnId}" onclick="regenPhraseIllust(${d.sit_id},'${it.key}')"
              style="flex:1;background:var(--bg);border:1px solid var(--border);color:var(--fg);
                     border-radius:6px;font-size:.62rem;padding:4px 0;cursor:pointer;
                     transition:all .15s;"
              onmouseover="this.style.borderColor='var(--accent)';this.style.color='var(--accent)'"
              onmouseout="this.style.borderColor='var(--border)';this.style.color='var(--fg)'">
            &#8635; 재생성
          </button>
          ${delBtn}
        </div>
      </div>
    </div>`;
  }).join('');

  // 패널 생성 현황 실시간 폴링 시작
  _startPhPanelPoll(id);
}

// ── 패널 뷰어 실시간 오버레이 폴링 ─────────────────────────────
let _phPanelPollTimer = null;
let _phPanelPollSitId = null;

function _startPhPanelPoll(sitId){
  _phPanelPollSitId = sitId;
  if(_phPanelPollTimer) clearInterval(_phPanelPollTimer);
  _applyPhPanelStatus(sitId);  // 즉시 1회
  _phPanelPollTimer = setInterval(()=>_applyPhPanelStatus(_phPanelPollSitId), 2000);
}

function _stopPhPanelPoll(){
  if(_phPanelPollTimer){ clearInterval(_phPanelPollTimer); _phPanelPollTimer=null; }
}

async function _applyPhPanelStatus(sitId){
  if(!sitId) return;
  let data;
  try{
    const r=await fetch(`/api/phrase/illust/panel-status/${sitId}`);
    if(!r.ok) return;
    data=await r.json();
  }catch(e){ return; }

  const completed = new Set(data.completed||[]);
  const failed    = data.failed||{};
  const cur       = data.current;  // {sit_id, key} or null
  const isCurSit  = cur && cur.sit_id===sitId;

  // 각 패널 카드 오버레이 업데이트
  const grid=document.getElementById('ph-browse-grid');
  if(!grid) return;

  grid.querySelectorAll('[id^="ph-gen-overlay-"]').forEach(overlay=>{
    const key=overlay.id.replace('ph-gen-overlay-','');
    const card=document.getElementById('ph-card-'+key);

    if(isCurSit && cur.key===key){
      // 현재 생성 중
      overlay.style.display='flex';
      if(card){ card.style.boxShadow='0 0 0 2px #a78bfa'; card.style.borderColor='#a78bfa88'; }
    } else if(failed[key]){
      // 실패
      overlay.style.display='none';
      if(card){ card.style.boxShadow='0 0 0 2px #f87171'; card.style.borderColor='#f8717188'; }
    } else if(completed.has(key)){
      // 완료 — 오버레이 없음, 테두리 복원 (이미지 자동 갱신은 다음 loadPhraseIllustBrowse에서)
      overlay.style.display='none';
      if(card){ card.style.boxShadow=''; card.style.borderColor=''; }
    } else {
      overlay.style.display='none';
      if(card){ card.style.boxShadow=''; card.style.borderColor=''; }
    }
  });

  // 생성 완료 패널의 이미지 자동 갱신 (미생성 → 완료 전환)
  grid.querySelectorAll('[id^="ph-regen-wrap-"]').forEach(wrap=>{
    const key=wrap.id.replace('ph-regen-wrap-','');
    if(completed.has(key) && wrap.querySelector('div[style*="미생성"], span')){
      // 미생성 div가 있으면 이미지로 교체
      const hasImg=wrap.querySelector('img');
      if(!hasImg && _phBrowseData){
        const item=_phBrowseData.items.find(x=>x.key===key);
        if(item){
          item.exists=true;
          const ts2=Date.now();
          const sitBase=`/api/phrase/illust/${_phPanelPollSitId}`;
          const url=`${sitBase}/${key}.png`;
          item.url=url;
          // 이미지 엘리먼트로 교체 (오버레이 div 보존)
          const overlay2=document.getElementById('ph-gen-overlay-'+key);
          wrap.innerHTML='';
          const img2=document.createElement('img');
          img2.src=url+'?t='+ts2;
          img2.loading='lazy';
          img2.style.cssText='width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:8px;cursor:pointer;display:block;transition:transform .2s;';
          img2.onmouseover=()=>img2.style.transform='scale(1.02)';
          img2.onmouseout=()=>img2.style.transform='';
          img2.onclick=()=>phIllustPreview(url+'?t='+ts2);
          wrap.appendChild(img2);
          // 레이블 배지 복원
          const col2=_CAT_COLORS[_phBrowseData.category]||'#818cf8';
          const isIntro2=key==='intro';
          const badge2=document.createElement('span');
          badge2.style.cssText=`position:absolute;top:7px;left:7px;font-size:.58rem;font-weight:700;letter-spacing:.04em;background:${isIntro2?col2:'rgba(0,0,0,.5)'};color:#fff;padding:2px 8px;border-radius:99px;backdrop-filter:blur(4px);`;
          badge2.textContent=item.label||key;
          wrap.appendChild(badge2);
          if(overlay2) wrap.appendChild(overlay2);
        }
      }
    }
  });

  // 이 상황이 모두 완료됐으면 폴링 중지
  if(!isCurSit && _phBrowseData){
    const allKeys=_phBrowseData.items.map(x=>x.key);
    const allDone=allKeys.every(k=>completed.has(k)||failed[k]);
    if(allDone) _stopPhPanelPoll();
  }
}

async function deletePhraseIllust(sitId,key){
  if(!confirm(`"${key}" 이미지를 삭제할까요?`))return;
  const r=await fetch('/api/phrase/illust/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sit_id:sitId,key:key})});
  const d=await r.json();
  if(!r.ok){alert('삭제 실패: '+(d.error||''));return;}
  loadPhraseIllustBrowse();
  loadPhraseSituations();
}

function phIllustPreview(url){
  const ov=document.createElement('div');
  ov.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.85);display:flex;align-items:center;justify-content:center;z-index:9999;cursor:pointer;';
  ov.onclick=()=>ov.remove();
  ov.innerHTML=`<img src="${url}" style="max-width:90vw;max-height:90vh;border-radius:12px;">`;
  document.body.appendChild(ov);
}

const _phRegenPolls={};   // key → intervalId
const _phRegenJobIds={};  // key → job_id

async function regenPhraseIllust(sitId,key){
  const btnId=`ph-regen-btn-${key}`;
  const btn=document.getElementById(btnId);
  if(btn){btn.disabled=true;btn.textContent='⏳ 큐 추가 중...';}
  const r=await fetch('/api/phrase/illust/regen',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sit_id:sitId,key:key})});
  const d=await r.json();
  if(!r.ok){
    const st=document.getElementById('ph-browse-regen-status');
    if(st){st.style.display='block';st.style.color='var(--red)';st.textContent='오류: '+(d.error||'');}
    if(btn){btn.disabled=false;btn.textContent='🔄 재생성';}
    return;
  }
  const jobId=d.job_id;
  _phRegenJobIds[key]=jobId;
  if(btn)btn.textContent='⏳ 대기 중...';
  // 카드 오버레이
  const wrap=document.getElementById(`ph-regen-wrap-${key}`);
  if(wrap&&!wrap.querySelector('.regen-overlay')){
    const ov=document.createElement('div');ov.className='regen-overlay';
    ov.innerHTML=`<div class="regen-spinner"></div><div class="ph-regen-ov-label" style="font-size:.7rem;color:#fff;font-weight:600;">대기 중...</div>`;
    wrap.appendChild(ov);
  }
  // 기존 폴 클리어
  if(_phRegenPolls[key])clearInterval(_phRegenPolls[key]);
  _phRegenPolls[key]=setInterval(async()=>{
    try{
      const qr=await fetch('/api/queue');
      if(!qr.ok)return;
      const qd=await qr.json();
      const job=qd.jobs.find(j=>j.id===jobId);
      if(!job)return;
      const lbl=wrap&&wrap.querySelector('.ph-regen-ov-label');
      if(job.status==='queued'){
        if(btn)btn.textContent='⏳ 대기 중...';
        if(lbl)lbl.textContent='대기 중...';
      }else if(job.status==='running'){
        if(btn)btn.textContent='⏳ 생성 중...';
        if(lbl)lbl.textContent='생성 중...';
      }else if(job.status==='done'){
        clearInterval(_phRegenPolls[key]);delete _phRegenPolls[key];delete _phRegenJobIds[key];
        const st=document.getElementById('ph-browse-regen-status');
        if(st){st.style.display='block';st.style.color='';st.textContent=`✅ ${key} 재생성 완료!`;setTimeout(()=>{st.style.display='none';},3000);}
        const wrap2=document.getElementById(`ph-regen-wrap-${key}`);
        if(wrap2){const ov2=wrap2.querySelector('.regen-overlay');if(ov2)ov2.remove();}
        if(btn){btn.disabled=false;btn.textContent='🔄 재생성';}
        loadPhraseIllustBrowse();loadPhraseSituations();
      }else if(job.status==='failed'||job.status==='cancelled'){
        clearInterval(_phRegenPolls[key]);delete _phRegenPolls[key];delete _phRegenJobIds[key];
        const st=document.getElementById('ph-browse-regen-status');
        if(st){st.style.display='block';st.style.color='var(--red)';st.textContent=`❌ ${key} 재생성 ${job.status==='cancelled'?'취소':'실패'}: `+(job.error||'');}
        const wrapE=document.getElementById(`ph-regen-wrap-${key}`);
        if(wrapE){const ovE=wrapE.querySelector('.regen-overlay');if(ovE)ovE.remove();}
        if(btn){btn.disabled=false;btn.textContent='🔄 재생성';}
      }
    }catch(e){}
  },2000);
  // 10분 타임아웃
  setTimeout(()=>{
    if(!_phRegenPolls[key])return;
    clearInterval(_phRegenPolls[key]);delete _phRegenPolls[key];
    const st=document.getElementById('ph-browse-regen-status');
    if(st){st.style.display='block';st.style.color='var(--red)';st.textContent='⚠ 시간 초과';}
    const wrap3=document.getElementById(`ph-regen-wrap-${key}`);
    if(wrap3){const ov3=wrap3.querySelector('.regen-overlay');if(ov3)ov3.remove();}
    if(btn){btn.disabled=false;btn.textContent='🔄 재생성';}
  },600000);
}

let _phIllustTarget = 'nas';
function setPhIllustTarget(t){
  _phIllustTarget = t;
  const _piN=document.getElementById('ph-illust-target-nas'),_piD=document.getElementById('ph-illust-target-desktop');
  if(_piN) _piN.className='btn '+(t==='nas'?'btn-p active':'btn-m');
  if(_piD) _piD.className='btn '+(t==='desktop'?'btn-p active':'btn-m');
}

async function startPhraseIllust(sitId){
  const body = {target: _phIllustTarget};
  if(sitId !== null){
    body.sit_id = sitId;
  } else {
    const s = parseInt(document.getElementById('ph-illust-start').value||'');
    const e = parseInt(document.getElementById('ph-illust-end').value||'');
    if(!isNaN(s) && !isNaN(e)){ body.start=s; body.end=e; }
    else{ alert('시작/끝 ID를 입력하세요'); return; }
  }
  try{
    const r = await fetch('/api/phrase/illust/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const d = await r.json();
    if(!r.ok){alert('오류: '+(d.error||'')); return;}
    loadJobQueue();
  }catch(e){alert('실패: '+e);}
}

async function cancelPhraseIllust(){
  await fetch('/api/phrase/illust/cancel',{method:'POST'});
  loadJobQueue();
}

let _phIllustPolling = false;
async function pollPhraseIllustProg(){
  if(_phIllustPolling) return;
  _phIllustPolling = true;
  try{
    const r = await fetch('/api/phrase/illust/progress');
    const d = await r.json();
    const prog = document.getElementById('ph-illust-prog');
    if(d.running || d.status==='running'){
      prog.style.display='';
      const pct = d.pct||0;
      document.getElementById('ph-illust-prog-bar').style.width=pct+'%';
      document.getElementById('ph-illust-prog-pct').textContent=pct+'%';
      document.getElementById('ph-illust-prog-label').textContent='생성 중...';
      document.getElementById('ph-illust-prog-msg').textContent=d.msg||'';
      _phIllustPolling=false;
      setTimeout(pollPhraseIllustProg, 2000);
    } else if(d.status==='done'){
      prog.style.display='';
      document.getElementById('ph-illust-prog-bar').style.width='100%';
      document.getElementById('ph-illust-prog-bar').style.background='var(--green)';
      document.getElementById('ph-illust-prog-pct').textContent='100%';
      document.getElementById('ph-illust-prog-label').textContent='✓ 완료';
      document.getElementById('ph-illust-prog-label').style.color='var(--green)';
      document.getElementById('ph-illust-prog-pct').style.color='var(--green)';
      _phIllustPolling=false;
      setTimeout(()=>{ prog.style.display='none'; loadPhraseSituations(); },3000);
    } else if(d.status==='failed'){
      prog.style.display='';
      document.getElementById('ph-illust-prog-label').textContent='✗ 실패';
      document.getElementById('ph-illust-prog-label').style.color='var(--red)';
      document.getElementById('ph-illust-prog-msg').textContent=d.msg||'';
      _phIllustPolling=false;
    } else {
      prog.style.display='none';
      _phIllustPolling=false;
    }
  }catch(e){_phIllustPolling=false;}
}

async function startPhraseVideo(sitId){
  const body = {};
  if(sitId !== null){
    body.sit_id = sitId;
  } else {
    const s = parseInt(document.getElementById('ph-video-start').value||'');
    const e = parseInt(document.getElementById('ph-video-end').value||'');
    if(!isNaN(s) && !isNaN(e)){ body.start=s; body.end=e; }
    else{ alert('시작/끝 ID를 입력하세요'); return; }
  }
  try{
    const r = await fetch('/api/phrase/video/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const d = await r.json();
    if(!r.ok){alert('오류: '+(d.error||'')); return;}
    loadJobQueue();
  }catch(e){alert('실패: '+e);}
}

async function cancelPhraseVideo(){
  await fetch('/api/phrase/video/cancel',{method:'POST'});
  document.getElementById('ph-video-prog').style.display='none';
}

let _phVideoPolling = false;
async function pollPhraseVideoProg(){
  if(_phVideoPolling) return;
  _phVideoPolling = true;
  try{
    const r = await fetch('/api/phrase/video/progress');
    const d = await r.json();
    const prog = document.getElementById('ph-video-prog');
    if(d.running || d.status==='running'){
      prog.style.display='';
      const pct = d.pct||0;
      document.getElementById('ph-video-prog-bar').style.width=pct+'%';
      document.getElementById('ph-video-prog-pct').textContent=pct+'%';
      document.getElementById('ph-video-prog-label').textContent='생성 중...';
      document.getElementById('ph-video-prog-msg').textContent=d.msg||'';
      _phVideoPolling=false;
      setTimeout(pollPhraseVideoProg, 2000);
    } else if(d.status==='done'){
      prog.style.display='';
      document.getElementById('ph-video-prog-bar').style.width='100%';
      document.getElementById('ph-video-prog-bar').style.background='var(--green)';
      document.getElementById('ph-video-prog-pct').textContent='100%';
      document.getElementById('ph-video-prog-label').textContent='✓ 완료';
      document.getElementById('ph-video-prog-label').style.color='var(--green)';
      document.getElementById('ph-video-prog-pct').style.color='var(--green)';
      _phVideoPolling=false;
      setTimeout(()=>{ prog.style.display='none'; loadPhraseSituations(); },3000);
    } else if(d.status==='failed'){
      prog.style.display='';
      document.getElementById('ph-video-prog-label').textContent='✗ 실패';
      document.getElementById('ph-video-prog-label').style.color='var(--red)';
      document.getElementById('ph-video-prog-msg').textContent=d.msg||'';
      _phVideoPolling=false;
    } else {
      prog.style.display='none';
      _phVideoPolling=false;
    }
  }catch(e){_phVideoPolling=false;}
}


</script>


</body>
</html>"""

@app.route("/")
def index(): return render_template_string(HTML)

if __name__ == "__main__":
    # 재시작 시 stale 'running' 상태 정리
    prog = load_json(ILLUST_PROG_F, {})
    if prog.get("status") == "running":
        save_json(ILLUST_PROG_F, {**prog, "status": "cancelled",
                                  "cancelled_at": datetime.now().isoformat()})
    # global_queue.json의 stale 'running' 잡 정리
    gq = load_global_queue()
    stale_fixed = False
    for j in gq.get("jobs", []):
        if j.get("status") == "running":
            j["status"] = "cancelled"
            j["completed_at"] = datetime.now().isoformat()
            stale_fixed = True
    if stale_fixed:
        save_global_queue(gq)
    app.run(host="0.0.0.0", port=8765, debug=False)
