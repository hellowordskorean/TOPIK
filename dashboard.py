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
BATCH_QUEUE_F   = f"{BASE}/logs/batch_queue.json"
ILLUST_USAGE_F  = f"{BASE}/logs/illust_usage.json"
DAILY_AUTO_F    = f"{BASE}/logs/daily_auto.json"
PHRASES_DB_PATH   = f"{BASE}/data/Conversation/phrases_db.json"   # 단일 정규 경로
CONV_DB_PATH    = PHRASES_DB_PATH   # 하위 호환 별칭
CONV_LOG_F      = f"{BASE}/logs/conv_log.json"
PHRASE_DB_F     = PHRASES_DB_PATH   # 하위 호환 별칭
PHRASE_ILLUST_DIR = f"{BASE}/assets/phrase_illustrations"
PHRASE_ILLUST_PROG= f"{BASE}/logs/phrase_illust_progress.json"
PHRASE_VIDEO_DIR  = f"{BASE}/output/phrases"
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
        # ES → SP 폴더 매핑 (스페인어 데이터는 SP/ 디렉토리에 저장)
        folder = "SP" if lang == "ES" else lang
        path = f"{LT}/TOPIK/{folder}/topik_{level}.json"
        return path if os.path.exists(path) else fallback
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
    """topik_{level}.json (EN)에서 최신 예문 반환. 없으면 빈 리스트."""
    path = f"{DATA_ROOT}/LanguageTest/TOPIK/EN/topik_{level}.json"
    data = load_json(path, {})
    words = data.get("words", [])
    w = next((x for x in words if x["id"] == word_id), None)
    return w.get("examples", []) if w else []

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
    upl = [u for u in uploaded if match({"exam":u.get("exam","TOPIK"),"language":u.get("language","EN")})]

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

    results = []
    for lang in ["EN", "JP", "CN", "VN", "ES"]:
        token_path = uy._token_path_for_lang(lang)
        if not os.path.exists(token_path):
            continue
        try:
            yt = uy.get_youtube_client(lang)
            ch = yt.channels().list(part="statistics,snippet", mine=True).execute()
            if ch.get("items"):
                s    = ch["items"][0]["statistics"]
                snip = ch["items"][0]["snippet"]
                results.append({
                    "lang":        lang,
                    "flag":        _LANG_FLAGS_YT.get(lang, ""),
                    "name":        snip.get("title", lang),
                    "channel_id":  ch["items"][0]["id"],
                    "subscribers": int(s.get("subscriberCount", 0)),
                    "views":       int(s.get("viewCount", 0)),
                    "video_count": int(s.get("videoCount", 0)),
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
                        if u.get("exam", "TOPIK") == exam and u.get("language", "EN") == lang}
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
def write_queue_job(word_id, db_path=None, exam="TOPIK", lang="EN", fmt="youtube"):
    if not db_path:
        db_path = "/app/data/LanguageTest/words_db.json"
    job_id = f"{word_id}_{lang}_{fmt}_{int(time.time()*1000)}"
    save_json(QUEUE_FILE,{"job_id":job_id,"word_id":word_id,"db_path":db_path,
        "exam":exam,"lang":lang,"fmt":fmt,
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
            save_json(BATCH_QUEUE_F, {
                "status": "running", "total": len(queue_items), "current": 0,
                "items": queue_items, "target": target,
                "started_at": datetime.now().isoformat()
            })
            run_batch_render(
                word_ids=[], target=target, exam=exam, lang=lang,
                job_items=job_items, auto_upload=auto_upload, words_map=words_map
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

        elif jtype in ("conv_video", "phrase_video", "phrase_illust"):
            cfg = get_render_config()
            if target == "desktop" and cfg.get("desktop_enabled"):
                _dispatch_to_desktop_phrase(job_id, jtype, params)
                # conv_video 완료 시 conv_log 업데이트
                if jtype == "conv_video":
                    q_check = load_global_queue()
                    j_check = next((j for j in q_check["jobs"] if j["id"] == job_id), None)
                    if j_check and j_check["status"] == "done":
                        tid  = str(params.get("theme_id"))
                        lang = params.get("lang", "EN")
                        vp   = f"{OUTPUT_DIR}/conversation/{lang}/conv_{tid}_{lang}.mp4"
                        clog = load_conv_log()
                        clog = [x for x in clog if not (str(x.get("theme_id")) == tid and x.get("lang") == lang)]
                        clog.append({"theme_id": tid, "lang": lang, "video_path": vp,
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
            elif jtype == "phrase_video":
                cmd = [sys.executable, "/app/make_video_phrases.py",
                       "--db", PHRASE_DB_F, "--output", PHRASE_VIDEO_DIR]
                sit_id = params.get("sit_id")
                start  = params.get("start")
                end    = params.get("end")
                if sit_id is not None:
                    cmd += ["--id", str(sit_id)]
                elif start is not None and end is not None:
                    cmd += ["--start", str(start), "--end", str(end)]
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
                # conv_video 완료 시 conv_log 업데이트
                if jtype == "conv_video":
                    tid  = str(params.get("theme_id"))
                    lang = params.get("lang", "EN")
                    vp   = f"{OUTPUT_DIR}/conversation/{lang}/conv_{tid}_{lang}.mp4"
                    clog = load_conv_log()
                    clog = [x for x in clog if not (str(x.get("theme_id")) == tid and x.get("lang") == lang)]
                    clog.append({"theme_id": tid, "lang": lang, "video_path": vp,
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
                     exam="TOPIK", lang="EN", words_map=None, job_items=None):
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
                    render_ok = run_render_nas(word_id, job_db_path, exam=exam, lang=job_lang, fmt=job_fmt)
                else:
                    # job_id로 내 작업 완료 여부 추적
                    job_id = write_queue_job(word_id, job_db_path, exam=exam, lang=job_lang, fmt=job_fmt)
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
                        render_ok = run_render_nas(word_id, job_db_path, exam=exam, lang=job_lang, fmt=job_fmt)
                    else:
                        rq = load_json(QUEUE_FILE, {})
                        render_ok = rq.get("status") == "done"
            else:
                render_ok = run_render_nas(word_id, job_db_path, exam=exam, lang=job_lang, fmt=job_fmt)

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

def run_render_nas(word_id, db_path=None, exam="TOPIK", lang="EN", fmt="youtube") -> bool:
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

def run_upload(word, video_path, exam="TOPIK", lang="EN", publish_at=None):
    """렌더링 완료된 영상을 YouTube에 업로드"""
    try:
        sys.path.insert(0, os.path.dirname(__file__) or "/app")
        from upload_youtube import get_youtube_client, generate_metadata, upload_video, load_upload_log, save_upload_log

        log_path = f"{BASE}/logs/uploads.json"
        upload_log = load_upload_log(log_path)
        day_number = upload_log.get("last_day", 0) + 1

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

        if not publish_at:
            upload_log["last_day"] = day_number
            upload_log["last_word_id"] = word["id"]
        upload_log.setdefault("uploaded", []).append({
            "day": day_number,
            "word_id": word["id"],
            "word": word["word"],
            "meaning": word.get("meaning", ""),
            "lang": lang,
            "video_id": video_id,
            "youtube_url": f"https://youtube.com/watch?v={video_id}",
            "scheduled_at": publish_at.isoformat() if publish_at else None,
            "uploaded_at": datetime.now().isoformat(),
        })
        save_upload_log(upload_log, log_path)
        return video_id
    except Exception as e:
        print(f"  업로드 실패: {e}")
        import traceback; traceback.print_exc()
        return None

# ─── 회화 영상 렌더링·업로드 ──────────────────────────────────
_CONV_CAT_STYLE = {
    "여행":      ("#4F8EF7", "✈️"),
    "식사":      ("#F77C4F", "🍜"),
    "쇼핑":      ("#F7C44F", "🛍️"),
    "인사":      ("#4FF7A0", "👋"),
    "일상":      ("#A04FF7", "💬"),
    "비즈니스":  ("#4FD4F7", "💼"),
    "K-Culture": ("#F74FA0", "🎭"),
    "의료":      ("#F74F4F", "🏥"),
    "주거":      ("#7EF74F", "🏠"),
    "여가":      ("#F7A04F", "🎮"),
}

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
                video_path = f"{OUTPUT_DIR}/conversation/{lang}/conv_{theme_id}_{lang}.mp4"
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

def run_phrase_video_bg(sit_id: int | None, start: int | None, end: int | None):
    global _phrase_video_thread, _phrase_video_progress
    if _phrase_video_thread and _phrase_video_thread.is_alive():
        return False, "이미 영상 생성 중입니다"
    def _run():
        global _phrase_video_progress
        _phrase_video_progress = {"status": "running", "sit_id": sit_id, "pct": 10, "msg": "영상 생성 시작..."}
        try:
            cmd = [sys.executable, "/app/make_video_phrases.py",
                   "--db", PHRASE_DB_F,
                   "--output", PHRASE_VIDEO_DIR]
            if sit_id is not None:
                cmd += ["--id", str(sit_id)]
            elif start is not None and end is not None:
                cmd += ["--start", str(start), "--end", str(end)]
            _phrase_video_progress["pct"] = 20
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0:
                _phrase_video_progress = {"status": "done", "sit_id": sit_id, "pct": 100, "msg": "완료"}
            else:
                _phrase_video_progress = {"status": "failed", "sit_id": sit_id,
                                          "pct": 0, "msg": r.stderr[-400:]}
        except Exception as e:
            _phrase_video_progress = {"status": "failed", "sit_id": sit_id, "pct": 0, "msg": str(e)}
    _phrase_video_thread = threading.Thread(target=_run, daemon=True)
    _phrase_video_thread.start()
    return True, "영상 생성 시작"

def run_conv_upload(theme_id: str, lang: str):
    """회화 영상 YouTube 업로드"""
    try:
        video_path = f"{OUTPUT_DIR}/conversation/{lang}/conv_{theme_id}_{lang}.mp4"
        if not os.path.exists(video_path):
            return None, "영상 파일이 없습니다 — 먼저 렌더링하세요"

        db = load_conv_db()
        theme = next((t for t in db["themes"] if t["id"] == theme_id), None)
        if not theme:
            return None, f"테마 '{theme_id}'를 찾을 수 없습니다"

        sys.path.insert(0, os.path.dirname(__file__) or "/app")
        from upload_youtube import get_youtube_client, upload_video, load_upload_log, save_upload_log

        lang_key = lang.lower()
        ko_title = theme["title"].get("ko", theme_id)
        local_title = theme["title"].get(lang_key, ko_title)
        search_title = theme.get("search_title", {}).get(lang_key, local_title)
        emoji = theme.get("emoji", "💬")

        _CONV_HOOKS = {
            "EN": f"Learn real Korean phrases for everyday situations! {emoji}",
            "JP": f"韓国語の実践フレーズを1テーマずつ学ぼう！{emoji}",
            "CN": f"一起学习韩语日常会话！{emoji}",
            "VN": f"Học hội thoại tiếng Hàn thực tế mỗi ngày！{emoji}",
            "ES": f"¡Aprende frases coreanas para situaciones reales! {emoji}",
        }
        _CONV_TAGS = {
            "EN": ["learn korean", "korean conversation", "korean phrases", "speak korean", "korean for beginners", search_title, ko_title],
            "JP": ["韓国語会話", "韓国語フレーズ", "韓国語初心者", "K-POP韓国語", search_title, ko_title],
            "CN": ["韩语日常会话", "韩语短语", "学韩语", "韩语教程", search_title, ko_title],
            "VN": ["học tiếng Hàn", "hội thoại tiếng Hàn", "tiếng Hàn giao tiếp", search_title, ko_title],
            "ES": ["coreano conversación", "frases en coreano", "aprender coreano", search_title, ko_title],
        }

        hook = _CONV_HOOKS.get(lang, _CONV_HOOKS["EN"])
        tags = _CONV_TAGS.get(lang, _CONV_TAGS["EN"])
        tags_str = ",".join(t for t in tags if t)[:490]

        metadata = {
            "title": f"{emoji} {search_title}",
            "description": f"{hook}\n\n{ko_title} | Korean Conversation Series\n\n#한국어 #Korean #{lang}",
            "tags": tags_str,
            "categoryId": "27",
            "privacyStatus": "public",
        }

        youtube = get_youtube_client(lang=lang)
        video_id = upload_video(youtube, video_path, metadata, publish_at=None, thumbnail_path=None)

        log_path = f"{BASE}/logs/uploads.json"
        upload_log = load_upload_log(log_path)
        upload_log.setdefault("uploaded", []).append({
            "type": "conversation",
            "theme_id": theme_id,
            "lang": lang,
            "video_id": video_id,
            "youtube_url": f"https://youtube.com/watch?v={video_id}",
            "uploaded_at": datetime.now().isoformat(),
        })
        save_upload_log(upload_log, log_path)

        # conv_log 업데이트
        clog = load_conv_log()
        for e in clog:
            if e.get("theme_id") == theme_id and e.get("lang") == lang:
                e["uploaded"] = True
                e["video_id"] = video_id
        save_conv_log(clog)

        return video_id, None
    except Exception as e:
        import traceback; traceback.print_exc()
        return None, str(e)

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

def _phrase_video_exists(sit_id: int) -> bool:
    """회화 영상 파일 존재 여부 확인"""
    try:
        vdir = Path(PHRASE_VIDEO_DIR)
        for f in vdir.iterdir():
            if f.name.startswith(f"phrases_sit{sit_id:03d}") and f.suffix == ".mp4":
                return f.stat().st_size > 0
    except Exception:
        pass
    return False

_phrase_rendering = False
_phrase_render_lock = threading.Lock()

def _phrase_render_job(sit_id: int):
    """회화 영상 렌더링 (NAS 직접)"""
    global _phrase_rendering
    try:
        cmd = [sys.executable, "/app/make_video_phrases.py",
               "--db", PHRASES_DB_PATH, "--id", str(sit_id),
               "--output", PHRASE_VIDEO_DIR]
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"  [phrase_render] 오류: {e}")
    _phrase_rendering = False

def _phrase_upload_job(sit_id: int):
    """회화 영상 5개 언어 채널 업로드"""
    try:
        # 영상 파일 찾기
        vdir = Path(PHRASE_VIDEO_DIR)
        vpath = None
        for f in vdir.iterdir():
            if f.name.startswith(f"phrases_sit{sit_id:03d}") and f.suffix == ".mp4":
                vpath = str(f); break
        if not vpath:
            print(f"  [phrase_upload] 영상 없음: sit_{sit_id}")
            return

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
    vid = run_upload(word, vpath, exam="TOPIK", lang=lang, publish_at=pub)
    s = load_json(DAILY_AUTO_F, {})
    ku = "youtube_uploaded" if fmt == "youtube" else "reels_uploaded"
    kv = "youtube_video_id"  if fmt == "youtube" else "reels_video_id"
    if lang in s.get("langs", {}):
        s["langs"][lang][ku] = bool(vid)
        if vid: s["langs"][lang][kv] = vid
        save_json(DAILY_AUTO_F, s)

def _daily_auto_tick():
    global _daily_rendering, _phrase_rendering
    try:
        s = load_json(DAILY_AUTO_F, {})
        today = datetime.now().strftime("%Y-%m-%d")
        if s.get("today") != today:
            next_id = _next_lv1_word_id(s.get("current_word_id", 0))

            # 회화 이틀 주기 확인
            last_phrase_date = s.get("phrase_last_date", "")
            phrase_due = False
            if last_phrase_date:
                try:
                    delta = (datetime.strptime(today, "%Y-%m-%d") -
                             datetime.strptime(last_phrase_date, "%Y-%m-%d")).days
                    phrase_due = delta >= 2
                except Exception:
                    phrase_due = True
            else:
                phrase_due = True  # 최초 실행

            # 회화 due면 다음 상황 ID 설정
            if phrase_due:
                next_sit = _next_sit_id(s.get("current_sit_id", 0))
            else:
                next_sit = s.get("current_sit_id", 1)

            s = {"auto_upload":       s.get("auto_upload", False),
                 "current_word_id":   next_id,
                 "today":             today,
                 "illust_done":       False,
                 "langs":             _daily_init_langs(),
                 # 회화 관련 유지
                 "current_sit_id":    next_sit,
                 "phrase_last_date":  s.get("phrase_last_date", ""),
                 "phrase_due":        phrase_due,
                 "phrase_rendered":   False,
                 "phrase_langs":      {lg: {"uploaded": False} for lg in DAILY_LANGS}
                                      if phrase_due else s.get("phrase_langs", {}),
                 }
            save_json(DAILY_AUTO_F, s)
        if not s.get("auto_upload"): return
        word_id = s.get("current_word_id")
        if not word_id: return
        # 일러스트 확인
        if not s.get("illust_done"):
            if _illust_exists_for(word_id):
                s["illust_done"] = True; save_json(DAILY_AUTO_F, s)
            # 없으면 이미 실행 중이 아닐 때만 생성 요청
            elif _illust_proc is None:
                threading.Thread(target=run_illustration_generation,
                    args=(word_id, word_id), kwargs={"mode":"both"}, daemon=True).start()
            return
        if _daily_rendering: return
        db = get_words_db()
        word = next((w for w in db if w["id"] == word_id), None)
        if not word: return
        # 렌더링 (언어별 youtube → reels 순)
        for lg in DAILY_LANGS:
            ls = s["langs"].get(lg, {})
            for fmt in ("youtube", "reels"):
                key = f"{fmt}_rendered"
                if not ls.get(key):
                    with _daily_render_lock:
                        if _daily_rendering: return
                        _daily_rendering = True
                    threading.Thread(target=_daily_render_job,
                        args=(word_id, lg, fmt), daemon=True).start()
                    return
        # 업로드
        for lg in DAILY_LANGS:
            ls = s["langs"].get(lg, {})
            for fmt in ("youtube", "reels"):
                if ls.get(f"{fmt}_rendered") and not ls.get(f"{fmt}_uploaded"):
                    threading.Thread(target=_daily_upload_job,
                        args=(word, lg, fmt), daemon=True).start()
                    time.sleep(1)

        # ── 회화 이틀 주기 처리 ──────────────────────────────
        if s.get("phrase_due") and s.get("auto_upload"):
            sit_id = s.get("current_sit_id")
            if sit_id:
                # 렌더링 확인
                if not s.get("phrase_rendered"):
                    if _phrase_video_exists(sit_id):
                        s["phrase_rendered"] = True
                        save_json(DAILY_AUTO_F, s)
                    elif not _phrase_rendering:
                        with _phrase_render_lock:
                            if not _phrase_rendering:
                                _phrase_rendering = True
                        threading.Thread(target=_phrase_render_job,
                            args=(sit_id,), daemon=True).start()
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

    except Exception as e:
        print(f"  [daily_tick] {e}")

def _daily_scheduler_loop():
    while True:
        time.sleep(60)
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
    upl_map = {(u.get("word_id"), u.get("language","EN"), u.get("exam","TOPIK")): u for u in uploaded}
    result = []
    for v in sorted(videos, key=lambda x: (x.get("exam",""), x.get("language",""), x.get("word_id",0))):
        key = (v["word_id"], v.get("language","EN"), v.get("exam","TOPIK"))
        ul = upl_map.get(key)
        # fmt 필드: 신규 로그는 직접, 구형 로그는 output_path로 추론
        _path = v.get("output_path", "")
        _fmt = v.get("fmt") or ("reels" if "/reels/" in _path or "_reels" in _path else "youtube")
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
               if (not exam or u.get("exam","TOPIK") == exam) and (not lang or u.get("language","EN") == lang)}
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
                job["pct"] = int(current / total * 100)
                job["step"] = f"{current}/{total}"
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
            elif job["type"] in ("conv_video", "phrase_video"):
                # progress.json 에서 실시간 진행률 주입
                p = load_json(PROGRESS_F, {})
                if p.get("status") == "running":
                    job["pct"] = p.get("pct", 0)
                    job["step"] = p.get("step", "")
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
    if job["status"] == "running" and _gq_active_job_id == job_id:
        _gq_cancel_requested = True
        job["status"] = "cancelled"
        job["completed_at"] = datetime.now().isoformat()
        save_global_queue(q)
        # 실행 중인 프로세스 종료
        for proc in [_nas_proc, _illust_proc, _gq_active_proc]:
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    try: proc.kill()
                    except Exception: pass
        # batch_queue.json도 취소 처리
        bq = load_json(BATCH_QUEUE_F, {})
        if bq.get("status") == "running":
            bq["status"] = "cancelled"
            bq["completed_at"] = datetime.now().isoformat()
            save_json(BATCH_QUEUE_F, bq)
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
@app.route("/api/daily/config", methods=["GET","POST"])
def api_daily_config():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        s = load_json(DAILY_AUTO_F, {})
        if "auto_upload" in data: s["auto_upload"] = bool(data["auto_upload"])
        save_json(DAILY_AUTO_F, s)
        if data.get("auto_upload"):
            threading.Thread(target=_daily_auto_tick, daemon=True).start()
        return jsonify({"ok": True})
    return jsonify(load_json(DAILY_AUTO_F, {}))

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
    return jsonify({"state": s, "word": word, "rendering": _daily_rendering,
                    "lv1_total": lv1_total})

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
    job_id = enqueue_job("video_batch", desc, target=target, params={
        "job_items":   [list(j) for j in job_items],
        "queue_items": queue_items,
        "words_map":   {str(k): v for k, v in words_map.items()},
        "auto_upload": auto_upload,
        "exam": "TOPIK", "lang": langs_str,
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
    # fmt에 따라 경로 결정
    if fmt == "reels":
        vpath = f"/app/output/{exam}/{lang}/lv{lv}/reels/{exam.lower()}_{word_id:04d}_{word['word']}_{lang}_reels.mp4"
    else:
        vpath = f"/app/output/{exam}/{lang}/lv{lv}/video/{exam.lower()}_{word_id:04d}_{word['word']}_{lang}.mp4"
    if not os.path.exists(vpath):
        return jsonify({"error": f"영상 파일 없음: {vpath}"}), 404
    def _do_upload():
        vid = run_upload(word, vpath, exam=exam, lang=lang)
        if vid:
            bq = load_json(BATCH_QUEUE_F, {})
            for it in bq.get("items", []):
                if it.get("word_id") == word_id and it.get("lang", "EN") == lang:
                    it["status"] = "uploaded"
                    it["video_id"] = vid
            save_json(BATCH_QUEUE_F, bq)
    threading.Thread(target=_do_upload, daemon=True).start()
    return jsonify({"ok": True, "video_path": vpath})

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
    vp = f"{OUTPUT_DIR}/conversation/{lang}/conv_{theme_id}_{lang}.mp4"
    deleted_file = False
    if os.path.exists(vp):
        try: os.remove(vp); deleted_file = True
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
                    "ids_str": t.get("ids_str","")} for t in raw_targets]
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
    job_id = enqueue_job("video_batch", desc, target=target, params={
        "job_items":   [list(j) for j in job_items],
        "queue_items": queue_items,
        "words_map":   all_words_map,
        "auto_upload": False,
        "exam": first_exam, "lang": base_lang,
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
    # 최신 예문은 topik_{level}.json 우선, fallback: words_db sentences
    sents = get_topik_examples(lv, word_id) or word.get("sentences", [])
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
    log_map = {(str(e["theme_id"]), e["lang"]): e for e in clog}
    themes = []
    for t in db.get("themes", []):
        langs = {}
        for lang in ["EN", "JP", "CN", "VN", "ES"]:
            entry = log_map.get((str(t["id"]), lang))
            langs[lang] = {
                "rendered": bool(entry and os.path.exists(entry.get("video_path", ""))),
                "uploaded": bool(entry and entry.get("uploaded")),
                "video_id": entry.get("video_id") if entry else None,
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
    desc = f"회화영상 {theme_id} [{lang}]"
    job_id = enqueue_job("conv_video", desc, target=target,
                         params={"theme_id": theme_id, "lang": lang})
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
    if not theme_id:
        return jsonify({"error": "theme_id 필요"}), 400
    video_id, err = run_conv_upload(theme_id, lang)
    if err:
        return jsonify({"error": err}), 500
    return jsonify({"status": "ok", "video_id": video_id,
                    "youtube_url": f"https://youtube.com/watch?v={video_id}"})

# ─── 회화 일러스트·영상 API ───────────────────────────────────
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
    target = data.get("target", "nas")
    if sit_id is not None:
        desc = f"회화영상 상황#{sit_id}"
    else:
        desc = f"회화영상 {start}~{end}"
    job_id = enqueue_job("phrase_video", desc, target=target,
                         params={"sit_id": sit_id, "start": start, "end": end})
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

  <!-- 렌더링 -->
  <div class="s-group tog" onclick="toggleSGroup('rend')">
    <span>⚙️ 렌더링</span><span id="sb-render-badge" style="font-size:.6rem;margin-left:6px;"></span><span class="s-arr" id="s-arr-rend">▾</span>
  </div>
  <div class="s-ch open" id="s-ch-rend">
    <div class="s-item l2" data-view="render-live" onclick="navRenderTab(this,'live')" style="--c:#3fb950;">
      <span>📊</span><span>렌더 진행사항</span>
    </div>
    <div class="s-item l2" data-view="render-batch" onclick="navRenderTab(this,'batch')" style="--c:#3fb950;">
      <span>📅</span><span>오늘의 배치</span>
    </div>
    <div class="s-item l2" data-view="render-history" onclick="navRenderTab(this,'history')" style="--c:#3fb950;">
      <span>🗓</span><span>날짜별</span>
    </div>
    <div class="s-item l2" data-view="render-custom" onclick="navRenderTab(this,'custom')" style="--c:#3fb950;">
      <span>🎬</span><span>영상 커스텀</span>
    </div>
    <div class="s-item l2" data-view="render-config" onclick="navRenderTab(this,'config')" style="--c:#3fb950;">
      <span>⚙️</span><span>설정</span>
    </div>
  </div>

  <!-- YouTube -->
  <div class="s-group tog" onclick="toggleSGroup('yt')">
    <span>▶ YouTube</span><span class="s-arr" id="s-arr-yt">▾</span>
  </div>
  <div class="s-ch open" id="s-ch-yt">
    <div class="s-item l2" data-view="youtube" onclick="nav(this,'youtube')" style="--c:#f87171;">
      <span>▶</span><span>YouTube</span>
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

<!-- ══ 렌더링 (통합 페이지) ═════════════════════════════ -->
<div id="view-render" class="view">
  <!-- 탭 내용: 배치 (일별 자동 시스템) -->
  <div id="rp-batch">
    <!-- 자동 업로드 토글 -->
    <div style="display:flex;align-items:center;justify-content:space-between;background:var(--bg);border-radius:10px;padding:12px 16px;margin-bottom:12px;">
      <div>
        <div style="font-weight:700;font-size:.85rem;">매일 자동 렌더링 & 업로드</div>
        <div style="font-size:.68rem;color:var(--muted);margin-top:2px;">Lv1 단어 1개 · 본편+쇼츠 · 5개 언어 · 현지 아침 7:30</div>
      </div>
      <label style="position:relative;display:inline-block;width:52px;height:28px;cursor:pointer;">
        <input type="checkbox" id="daily-auto-toggle" onchange="setDailyAuto(this.checked)" style="opacity:0;width:0;height:0;">
        <span id="daily-toggle-slider" style="position:absolute;inset:0;background:#444;border-radius:28px;transition:.3s;">
          <span id="daily-toggle-knob" style="position:absolute;left:3px;top:3px;width:22px;height:22px;background:#fff;border-radius:50%;transition:.3s;"></span>
        </span>
      </label>
    </div>

    <!-- 오늘의 단어 -->
    <div style="background:var(--bg);border-radius:10px;padding:12px 16px;margin-bottom:12px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
        <div style="font-size:.72rem;color:var(--muted);font-weight:600;">오늘의 단어 · Lv1</div>
        <div id="daily-lv1-progress" style="font-size:.68rem;color:var(--muted2);"></div>
      </div>
      <div id="daily-word-display" style="display:flex;align-items:center;gap:12px;">
        <div style="font-size:1.6rem;font-weight:700;color:var(--blue);" id="daily-word-ko">—</div>
        <div style="font-size:.82rem;color:var(--muted);" id="daily-word-meaning"></div>
      </div>
      <div style="display:flex;gap:6px;margin-top:8px;align-items:center;">
        <span style="font-size:.65rem;color:var(--muted2);">ID:</span>
        <input id="daily-word-id-input" class="inp" type="number" min="1" max="300" style="width:70px;font-size:.72rem;padding:2px 6px;" placeholder="ID">
        <button onclick="dailySetWord()" class="btn btn-m" style="font-size:.68rem;padding:3px 10px;">단어 변경</button>
        <span id="daily-illust-badge" style="margin-left:auto;font-size:.65rem;"></span>
      </div>
    </div>

    <!-- 언어별 상태 -->
    <div style="background:var(--bg);border-radius:10px;padding:10px 14px;margin-bottom:12px;">
      <div style="font-size:.7rem;color:var(--muted);font-weight:600;margin-bottom:8px;">언어별 렌더링 & 업로드</div>
      <table style="width:100%;font-size:.7rem;border-collapse:collapse;" id="daily-lang-table">
        <thead><tr style="color:var(--muted2);font-size:.65rem;">
          <th style="text-align:left;padding:3px 6px;">언어</th>
          <th style="text-align:center;padding:3px 6px;">본편</th>
          <th style="text-align:center;padding:3px 6px;">쇼츠</th>
          <th style="text-align:left;padding:3px 6px;">업로드 예약</th>
        </tr></thead>
        <tbody id="daily-lang-tbody"></tbody>
      </table>
    </div>

    <!-- 렌더링 현황 -->
    <div id="daily-render-status" style="display:none;padding:8px 12px;background:var(--bg);border-radius:8px;margin-bottom:10px;font-size:.72rem;color:var(--amber);font-weight:600;"></div>

    <!-- 오늘의 회화 -->
    <div style="background:var(--bg);border-radius:10px;padding:12px 16px;margin-bottom:12px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
        <div style="font-size:.72rem;color:var(--muted);font-weight:600;">오늘의 회화</div>
        <div style="display:flex;align-items:center;gap:6px;">
          <span style="font-size:.62rem;color:var(--muted2);">상황 ID:</span>
          <input id="daily-conv-id-input" class="inp" type="number" min="1" style="width:60px;font-size:.72rem;padding:2px 6px;" placeholder="ID">
          <button onclick="dailySetConv()" class="btn btn-m" style="font-size:.68rem;padding:3px 8px;">변경</button>
        </div>
      </div>
      <div id="daily-conv-display" style="font-size:.9rem;font-weight:700;color:var(--green);margin-bottom:8px;">—</div>
      <table style="width:100%;font-size:.7rem;border-collapse:collapse;" id="daily-conv-table">
        <thead><tr style="color:var(--muted2);font-size:.65rem;">
          <th style="text-align:left;padding:3px 6px;">언어</th>
          <th style="text-align:center;padding:3px 6px;">렌더됨</th>
          <th style="text-align:center;padding:3px 6px;">업로드됨</th>
        </tr></thead>
        <tbody id="daily-conv-tbody"></tbody>
      </table>
    </div>

    <!-- 수동 트리거 -->
    <div style="display:flex;gap:6px;align-items:center;margin-bottom:8px;flex-wrap:wrap;">
      <span style="font-size:.65rem;color:var(--muted2);white-space:nowrap;">콘텐츠:</span>
      <button id="rp-tog-word" onclick="toggleRpContent('word')" class="btn btn-g" style="font-size:.68rem;padding:3px 10px;">🎬 단어</button>
      <button id="rp-tog-conv" onclick="toggleRpContent('conv')" class="btn btn-m" style="font-size:.68rem;padding:3px 10px;">💬 회화</button>
      <span style="font-size:.65rem;color:var(--muted2);margin-left:6px;white-space:nowrap;">포맷:</span>
      <button id="rp-tog-yt" onclick="toggleRpFmt('youtube')" class="btn btn-g" style="font-size:.68rem;padding:3px 10px;">▶ YouTube</button>
      <button id="rp-tog-rl" onclick="toggleRpFmt('reels')" class="btn btn-m" style="font-size:.68rem;padding:3px 10px;">📱 릴스</button>
    </div>
    <div style="display:flex;gap:8px;margin-bottom:6px;">
      <button id="rp-render-all" onclick="renderBatchAll()" class="btn btn-g" style="flex:1;justify-content:center;font-size:.75rem;">▶ 렌더링</button>
      <button onclick="dailyTrigger()" class="btn btn-m" style="font-size:.75rem;padding:0 10px;">▶ 오늘</button>
      <button id="rp-cancel-btn" onclick="cancelRender()" class="btn btn-d" style="display:none;font-size:.75rem;padding:0 12px;">✕ 취소</button>
    </div>
    <div style="margin-top:6px;font-size:.65rem;color:var(--muted2);text-align:center;">자동 OFF 상태에서도 수동으로 실행 가능</div>
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
  <!-- 탭 내용: 설정 -->
  <div id="rp-config" style="display:none;">
    <div style="font-size:.74rem;color:var(--muted);margin-bottom:10px;">하루 분량 설정 (시험/언어/등급별 슬롯)</div>
    <div id="rp-config-slots"></div>
    <button onclick="addSlot()" class="btn btn-m" style="width:100%;margin-top:8px;justify-content:center;">+ 슬롯 추가</button>
    <div style="display:flex;gap:8px;margin-top:12px;">
      <button onclick="saveSchedule()" class="btn btn-g" style="flex:1;justify-content:center;">💾 저장</button>
      <button onclick="resetSchedule()" class="btn btn-m">기본값</button>
    </div>
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
  <div class="bc"><span class="cur">▶ YouTube 통계</span></div>
  <div id="yt-loading" style="text-align:center;padding:24px;color:var(--muted);display:none;">채널 통계 로드 중...</div>
  <div id="yt-content"></div>
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
  <div class="bc"><span class="cur">💬 회화 영상</span></div>

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
        <option value="rendered">렌더됨</option>
        <option value="uploaded">업로드됨</option>
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
          <th style="text-align:center;">렌더됨</th>
          <th style="text-align:center;">업로드됨</th>
          <th style="text-align:center;">YouTube</th>
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
  if(view==='conv'){loadConvThemes();loadPhraseSituations();cvTab('basic');}
  if(view==='videos') loadAllVideos();
  if(view==='youtube') loadYoutubeChannels();
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

function toggleSGroup(name){
  const ch=document.getElementById('s-ch-'+name);
  const arr=document.getElementById('s-arr-'+name);
  if(!ch)return;
  ch.classList.toggle('open');
  if(arr) arr.style.transform=ch.classList.contains('open')?'':'rotate(-90deg)';
}

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
  const badge=document.getElementById('gq-count-badge');
  const cfg=d.render_config||{};
  const desktopEnabled=cfg.desktop_enabled!==false;
  const desktopBusy=d.desktop_busy;

  // 기본 렌더링 위치 버튼 업데이트
  const btnD=document.getElementById('ql-btn-desktop');
  const btnN=document.getElementById('ql-btn-nas');
  if(btnD){btnD.className='btn '+(desktopEnabled?'btn-p':'btn-m');}
  if(btnN){btnN.className='btn '+(desktopEnabled?'btn-m':'btn-p');}
  const dSt=document.getElementById('ql-desktop-status');
  if(dSt) dSt.textContent=desktopBusy?'💻 GPU 렌더링 중':'💻 GPU 대기 중';
  if(dSt) dSt.style.color=desktopBusy?'var(--amber)':'var(--green)';

  const active=jobs.filter(j=>['queued','running'].includes(j.status));
  const finished=jobs.filter(j=>['done','failed','cancelled'].includes(j.status)).slice(-5);
  const visible=[...active,...finished];
  if(badge) badge.textContent=active.length?`${active.length}개 진행중`:'';

  if(!visible.length){
    list.innerHTML='<div style="font-size:.72rem;color:var(--muted2);text-align:center;padding:10px 0;">대기 중인 작업이 없습니다</div>';
    return;
  }

  const typeInfo={
    video_batch:        {label:'단어영상',  color:'var(--accent)', icon:'🎬'},
    illust:             {label:'일러스트',  color:'var(--amber)',  icon:'🎨'},
    conv_video:         {label:'회화영상',  color:'var(--green)',  icon:'💬'},
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

  list.innerHTML=visible.map(job=>{
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
    let html=`<div class="g3" style="margin-bottom:14px;">
      <div class="card-sm kpi"><div class="num" style="color:var(--red);">${fmt(totSubs)}</div><div class="label">총 구독자</div></div>
      <div class="card-sm kpi"><div class="num" style="color:var(--amber);">${fmt(totViews)}</div><div class="label">총 조회수</div></div>
      <div class="card-sm kpi"><div class="num" style="color:var(--blue);">${fmt(totVids)}</div><div class="label">총 영상 수</div></div>
    </div><div class="g3" style="margin-bottom:14px;">`;
    channels.forEach(ch=>{
      if(ch.error){
        html+=`<div class="card-sm" style="opacity:.5;"><div style="font-size:.75rem;font-weight:700;">${ch.flag} ${ch.lang}</div><div style="font-size:.65rem;color:var(--red);margin-top:6px;">토큰 없음 또는 오류</div></div>`;
      } else {
        const ytUrl=`https://www.youtube.com/channel/${ch.channel_id}`;
        html+=`<div class="card-sm">
          <div style="font-size:.78rem;font-weight:700;margin-bottom:10px;">
            <a href="${ytUrl}" target="_blank" style="color:inherit;text-decoration:none;">${ch.flag} ${ch.name}</a>
          </div>
          <div style="display:flex;gap:16px;font-size:.72rem;">
            <div><div style="color:var(--red);font-weight:700;font-size:1rem;">${fmt(ch.subscribers)}</div><div style="color:var(--muted);">구독자</div></div>
            <div><div style="color:var(--amber);font-weight:700;font-size:1rem;">${fmt(ch.views)}</div><div style="color:var(--muted);">조회수</div></div>
            <div><div style="color:var(--blue);font-weight:700;font-size:1rem;">${fmt(ch.video_count)}</div><div style="color:var(--muted);">영상</div></div>
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

async function loadDailyStatus(){
  const r=await fetch('/api/daily/status');
  if(!r.ok)return;
  const d=await r.json();
  const s=d.state||{};
  const w=d.word;

  // 토글 상태
  const tog=document.getElementById('daily-auto-toggle');
  const slider=document.getElementById('daily-toggle-slider');
  const knob=document.getElementById('daily-toggle-knob');
  if(tog){
    tog.checked=!!s.auto_upload;
    slider.style.background=s.auto_upload?'var(--green)':'#444';
    knob.style.left=s.auto_upload?'27px':'3px';
  }

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
  if(ibadge) ibadge.innerHTML=s.illust_done
    ?`<span style="color:var(--green);font-weight:700;">✓ 일러스트</span>`
    :`<span style="color:var(--amber);">⏳ 일러스트 생성 중...</span>`;

  // 언어별 상태 테이블
  const tbody=document.getElementById('daily-lang-tbody');
  const stCell=(ok,rendering)=>ok
    ?`<span style="color:var(--green);font-weight:700;">✓</span>`
    :(rendering?`<span style="color:var(--amber);">⏳</span>`:`<span style="color:var(--muted2);">○</span>`);
  const rows=_DAILY_LANGS.map(lg=>{
    const ls=(s.langs||{})[lg]||{};
    const ytOk=ls.youtube_rendered,rlOk=ls.reels_rendered;
    const ytUp=ls.youtube_uploaded,rlUp=ls.reels_uploaded;
    const isRend=d.rendering;
    const vidLink=ls.youtube_video_id?`<a href="https://youtube.com/watch?v=${ls.youtube_video_id}" target="_blank" style="color:var(--green);font-size:.65rem;">▶</a>`:'';
    const rlLink=ls.reels_video_id?`<a href="https://youtube.com/watch?v=${ls.reels_video_id}" target="_blank" style="color:var(--green);font-size:.65rem;">▶</a>`:'';
    const uploadCell=ytUp?`<span style="color:var(--green);font-size:.65rem;">✓ 예약완료 ${vidLink}${rlLink}</span>`
      :`<span style="color:var(--muted2);font-size:.65rem;">${ls.publish_local||ls.publish_at||''}</span>`;
    return `<tr style="border-top:1px solid var(--border);">
      <td style="padding:4px 6px;">${_DAILY_FLAG[lg]||''} ${_DAILY_NAME[lg]||lg}</td>
      <td style="text-align:center;padding:4px 6px;">${stCell(ytOk,isRend)}</td>
      <td style="text-align:center;padding:4px 6px;">${stCell(rlOk,isRend)}</td>
      <td style="padding:4px 6px;">${uploadCell}</td>
    </tr>`;
  }).join('');
  tbody.innerHTML=rows;

  // 렌더링 상태
  const rs=document.getElementById('daily-render-status');
  if(d.rendering){
    rs.style.display='block';
    rs.textContent='⏳ 렌더링 중...';
  } else {
    rs.style.display='none';
  }
}

const _DAILY_LANGS=['EN','CN','JP','VN','ES'];

async function setDailyAuto(on){
  const slider=document.getElementById('daily-toggle-slider');
  const knob=document.getElementById('daily-toggle-knob');
  slider.style.background=on?'var(--green)':'#444';
  knob.style.left=on?'27px':'3px';
  await fetch('/api/daily/config',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({auto_upload:on})});
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

// 배치 탭 열릴 때 폴링 시작
function _startDailyPoll(){
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

let _livePollTimer=null;

function rpTab(tab){
  _rpTab=tab;
  ['batch','custom','illust','history','live','config'].forEach(t=>{
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
      await fetch('/api/conv/render',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({theme_id:String(_todayConvId),lang,target:_batchTarget||'nas'})});
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
    // 회화 렌더링
    if(_todayConvId){
      for(const lang of CONV_LANGS){
        await fetch('/api/conv/render',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({theme_id:String(_todayConvId),lang,target:_batchTarget||'nas'})});
      }
    }
    loadJobQueue();navRenderTab(null,'live');
  }catch(e){alert('실패: '+e);}
  finally{btn.disabled=false;btn.textContent='▶ 단어 + 회화 모두 렌더링';}
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
  if(_rpFmt.has(key)) _rpFmt.delete(key);
  else _rpFmt.add(key);
  if(_rpFmt.size===0) _rpFmt.add(key); // 최소 1개
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
    const autoUpload=document.getElementById('rp-auto-upload').checked;
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
          body:JSON.stringify({items,target:_batchTarget,auto_upload:autoUpload})});
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
function getSelectedLangs(){
  return [...document.querySelectorAll('.rc-lang-btn.active')].map(b=>b.dataset.lang);
}
function getSelectedFmts(){
  return [...document.querySelectorAll('.rc-fmt-btn.active')].map(b=>b.dataset.fmt);
}
function toggleRowFmt(btn){
  const row=btn.closest('.rc-target-row');
  const active=[...row.querySelectorAll('.rc-row-fmt.active')];
  const isActive=btn.classList.contains('active');
  if(isActive&&active.length<=1)return; // 최소 1개 유지
  const fmt=btn.dataset.fmt;
  const color=fmt==='youtube'?'var(--green)':'var(--amber)';
  if(isActive){
    btn.classList.remove('active');
    btn.style.background='transparent';btn.style.color='var(--muted)';btn.style.borderColor='var(--border)';btn.style.opacity='.45';
  }else{
    btn.classList.add('active');
    btn.style.background=color+'22';btn.style.color=color;btn.style.borderColor=color;btn.style.opacity='1';
  }
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
  const dBtn=document.getElementById('rc-target-desktop');
  const nBtn=document.getElementById('rc-target-nas');
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
  return [...document.querySelectorAll('#rc-targets .rc-target-row')].map(row=>{
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
  const rows=document.querySelectorAll('#rc-targets .rc-target-row');
  if(rows.length<=1)return;
  el.closest('.rc-target-row').remove();
  updateCustomPreview();
}

function toggleConvSection(){
  const en=document.getElementById('rc-conv-enabled').checked;
  document.getElementById('rc-conv-detail').style.display=en?'block':'none';
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
  const targets=getTargetRows();
  const langs=getSelectedLangs();
  const el=document.getElementById('rc-preview');
  const remEl=document.getElementById('rc-remaining');

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
    document.getElementById('rc-start').disabled=total===0||totalEp===0;
    document.getElementById('rc-start').textContent=`▶ 렌더링 시작 (${totalEp}화 × ${langs.length}개 언어 = ${total}개 · ${_customTarget==='desktop'?'💻 GPU':'🖥 NAS'})`;
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
    if(!d.words||!d.words.length){
      el.innerHTML='<div style="color:#484f58;text-align:center;padding:16px;font-size:.78rem;">렌더링할 단어가 없습니다</div>';
      document.getElementById('rc-start').disabled=true;
      return;
    }
    document.getElementById('rc-start').disabled=false;
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
    document.getElementById('rc-start').textContent=`▶ 렌더링 시작 (${d.words.length}개 × ${wordTargets.length}개 시험 × ${langs.length}개 언어 × ${fmtLabel} = ${total}개 · ${_customTarget==='desktop'?'💻 GPU':'🖥 NAS'})`;
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
  const el=document.getElementById('rc-time-est');
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
  const btn=document.getElementById('rc-start');
  const cancelBtn=document.getElementById('rc-cancel');
  btn.disabled=true;btn.textContent='⏳ 요청 중...';
  try{
    // 단어 렌더링 (per-row formats 포함)
    if(wordTargets.length){
      const body={targets:wordTargets,langs,target:renderTarget};
      const r=await fetch('/api/render/custom',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify(body)});
      const d=await r.json();
      if(!r.ok){alert('단어 렌더링 오류: '+(d.error||''));btn.disabled=false;btn.textContent='▶ 렌더링 시작';return;}
    }
    // 회화 렌더링 (범위 확장)
    for(const t of convTargets){
      const epIds=parseIds(t.conv_range);
      for(const epId of epIds){
        for(const lang of langs){
          await fetch('/api/conv/render',{method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({theme_id:String(epId),lang,target:renderTarget})});
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
setInterval(()=>{if(_currentView==='render'){loadJobQueue();if(_rpTab==='batch')loadBatchData();loadLiveStatus();}},3000);
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
      if(filterStatus==='rendered'  && !ls.rendered) continue;
      if(filterStatus==='uploaded'  && !ls.uploaded) continue;
      if(filterStatus==='pending'   &&  ls.rendered) continue;
      const vid = ls.video_id;
      rows.push(`<tr>
        <td style="color:var(--muted2);font-size:.7rem;">${t.id}</td>
        <td>
          <span style="margin-right:6px;">${t.emoji}</span>
          <span style="font-weight:600;">${ko}</span>
        </td>
        <td style="text-align:center;color:var(--muted);">${t.phrase_count}</td>
        <td style="text-align:center;">${LANG_FLAGS[lang]} <span style="font-size:.72rem;color:var(--muted);">${lang}</span></td>
        <td style="text-align:center;">
          <span class="badge ${ls.rendered?'badge-g':'badge-m'}" style="font-size:.65rem;">${ls.rendered?'✓':'○'}</span>
        </td>
        <td style="text-align:center;">
          <span class="badge ${ls.uploaded?'badge-g':'badge-m'}" style="font-size:.65rem;">${ls.uploaded?'✓':'○'}</span>
        </td>
        <td style="text-align:center;">
          ${vid?`<a href="https://youtube.com/watch?v=${vid}" target="_blank" style="color:var(--red);font-size:.72rem;">▶</a>`:'–'}
        </td>
        <td style="text-align:right;padding-right:8px;">
          <div style="display:flex;gap:4px;justify-content:flex-end;flex-wrap:wrap;">
            <button class="btn btn-a" onclick="convRenderLang('${t.id}','${lang}')" style="font-size:.68rem;padding:3px 8px;">
              🎬 ${ls.rendered?'재렌더':'렌더링'}
            </button>
            <button class="btn btn-g" onclick="convUploadLang('${t.id}','${lang}')" style="font-size:.68rem;padding:3px 8px;" ${!ls.rendered?'disabled':''}>
              ⬆ 업로드
            </button>
            <button class="btn btn-p" onclick="convRenderLang('${t.id}','${lang}')" style="font-size:.68rem;padding:3px 8px;">
              ↺ 재생성
            </button>
            <button class="btn" onclick="convDelete('${t.id}','${lang}')" style="font-size:.68rem;padding:3px 8px;background:#2d1515;color:#f87171;border:1px solid #7f1d1d;" ${!ls.rendered?'disabled':''}>
              🗑 삭제
            </button>
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
async function convRenderLang(themeId, lang){
  if(!confirm(`[${lang}] "${themeId}" 테마를 렌더링할까요? (${_convTarget==='desktop'?'💻 GPU':'🖥 NAS'})`)) return;
  try{
    const r = await fetch('/api/conv/render',{method:'POST',headers:{'Content-Type':'application/json'},
      body: JSON.stringify({theme_id:themeId, lang:lang, target:_convTarget})});
    const d = await r.json();
    if(!r.ok){ alert('오류: '+(d.error||'')); return; }
    loadJobQueue();
  }catch(e){ alert('실패: '+e); }
}

async function convUpload(themeId){
  await convUploadLang(themeId, _convLang);
}
async function convUploadLang(themeId, lang){
  if(!confirm(`[${lang}] "${themeId}" 영상을 YouTube에 업로드할까요?`)) return;
  try{
    const r = await fetch('/api/conv/upload',{method:'POST',headers:{'Content-Type':'application/json'},
      body: JSON.stringify({theme_id:themeId, lang:lang})});
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
    app.run(host="0.0.0.0", port=8765, debug=False)
