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
CONV_DB_PATH    = f"{BASE}/phrases_db.json"
CONV_LOG_F      = f"{BASE}/logs/conv_log.json"
PHRASE_DB_F       = f"{BASE}/data/Conversation/phrases_db.json"
PHRASE_ILLUST_DIR = f"{BASE}/assets/phrase_illustrations"
PHRASE_ILLUST_PROG= f"{BASE}/logs/phrase_illust_progress.json"
PHRASE_VIDEO_DIR  = f"{BASE}/output/phrases"
PHRASE_VIDEO_LOG  = f"{BASE}/logs/phrase_videos_log.json"

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
    {"exam":"TOPIK","lang":"EN","level":1},
    {"exam":"TOPIK","lang":"EN","level":2},
    {"exam":"TOPIK","lang":"EN","level":3},
    {"exam":"TOPIK","lang":"JP","level":1},
    {"exam":"TOPIK","lang":"JP","level":2},
    {"exam":"TOPIK","lang":"JP","level":3},
    {"exam":"TOPIK","lang":"ES","level":1},
    {"exam":"TOPIK","lang":"ES","level":2},
    {"exam":"TOPIK","lang":"ES","level":3},
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
                      "word": word, "status": status, "has_illust": has_illust})
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
_batch_thread  = None

def _desktop_is_busy() -> bool:
    """데스크탑이 현재 렌더링 작업을 처리 중인지 확인"""
    q = load_json(QUEUE_FILE, {})
    if q.get("status") == "claimed":
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
            # 다중 언어: (word_id, lang) 쌍으로 매칭
            for item in bq.get("items", []):
                if item["word_id"] == word_id and item.get("lang", lang) == job_lang:
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
                    run_render_nas(word_id, job_db_path, exam=exam, lang=job_lang, fmt=job_fmt)
                    rq = load_json(QUEUE_FILE, {})
                    render_ok = rq.get("status") == "done"
                else:
                    # job_id로 내 작업 완료 여부 추적
                    job_id = write_queue_job(word_id, job_db_path, exam=exam, lang=job_lang, fmt=job_fmt)
                    deadline = time.time() + 40 * 60
                    finished = False
                    while time.time() < deadline:
                        if _is_batch_cancelled(): break
                        time.sleep(15)
                        rq = load_json(QUEUE_FILE, {})
                        # 내 job_id가 완료됐는지 확인
                        if (rq.get("job_id") == job_id and
                                rq.get("status") in ("done", "failed")):
                            finished = True; break
                    if _is_batch_cancelled(): continue
                    if not finished:
                        print(f"  [batch] 데스크탑 타임아웃 → NAS 폴백 ({job_lang}/{job_fmt})")
                        run_render_nas(word_id, job_db_path, exam=exam, lang=job_lang, fmt=job_fmt)
                    rq = load_json(QUEUE_FILE, {})
                    render_ok = rq.get("status") == "done"
            else:
                run_render_nas(word_id, job_db_path, exam=exam, lang=job_lang, fmt=job_fmt)
                rq = load_json(QUEUE_FILE, {})
                render_ok = rq.get("status") == "done"

            # 렌더링 후 자동 업로드
            if render_ok and auto_upload and words_map and word_id in words_map:
                bq2 = load_json(BATCH_QUEUE_F, {})
                for item in bq2.get("items", []):
                    if item["word_id"] == word_id and item.get("lang", lang) == job_lang:
                        item["status"] = "uploading"
                save_json(BATCH_QUEUE_F, bq2)

                word = words_map[word_id]
                lv = word.get("level", 1)
                video_path = f"/app/output/{exam}/{job_lang}/lv{lv}/video/{exam.lower()}_{word_id:04d}_{word['word']}_{job_lang}.mp4"
                if not os.path.exists(video_path):
                    video_path = f"/app/output/topik_{word_id:04d}_{word['word']}_{job_lang}.mp4"
                if os.path.exists(video_path):
                    vid = run_upload(word, video_path, exam=exam, lang=job_lang)
                    if vid:
                        for item in bq2.get("items", []):
                            if item["word_id"] == word_id and item.get("lang", lang) == job_lang:
                                item["video_id"] = vid
        except Exception as e:
            render_ok = False

        bq = load_json(BATCH_QUEUE_F, {})
        for item in bq.get("items", []):
            if item["word_id"] == word_id and item.get("lang", lang) == job_lang:
                item["status"] = "done" if render_ok else "failed"
                break
        bq["current"] = i + 1
        save_json(BATCH_QUEUE_F, bq)

    bq = load_json(BATCH_QUEUE_F, {})
    bq["status"] = "done"
    bq["completed_at"] = datetime.now().isoformat()
    save_json(BATCH_QUEUE_F, bq)

def run_render_nas(word_id, db_path=None, exam="TOPIK", lang="EN", fmt="youtube"):
    if not db_path:
        db_path = "/app/data/LanguageTest/words_db.json"
    try:
        q = load_json(QUEUE_FILE,{})
        q.update({"status":"claimed","claimed_by":"nas","claimed_at":datetime.now().isoformat()})
        save_json(QUEUE_FILE,q)
        cmd = [sys.executable,"/app/make_video.py",
            "--db",db_path,"--id",str(word_id),
            "--output","/app/output/","--exam",exam,"--lang",lang]
        if fmt == "reels":
            cmd += ["--format","reels"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  [NAS render FAIL] {lang}/{fmt} id={word_id}\n{r.stderr[-800:]}")
        q = load_json(QUEUE_FILE,{})
        q.update({"status":"done" if r.returncode==0 else "failed",
                  "error": r.stderr[-400:] if r.returncode!=0 else None,
                  "completed_at":datetime.now().isoformat()})
        save_json(QUEUE_FILE,q)
    except Exception as e:
        save_json(QUEUE_FILE,{**load_json(QUEUE_FILE,{}),"status":"failed","error":str(e)})

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
def load_conv_db():
    return load_json(CONV_DB_PATH, {"themes": []})

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
            while time.time() < deadline:
                time.sleep(15)
                rq = load_json(QUEUE_FILE, {})
                if rq.get("status") in ("done", "failed"): break
            if load_json(QUEUE_FILE, {}).get("status") != "done":
                run_render_nas(word_id, db_path, exam="TOPIK", lang=lang, fmt=fmt)
        else:
            run_render_nas(word_id, db_path, exam="TOPIK", lang=lang, fmt=fmt)
        ok = load_json(QUEUE_FILE, {}).get("status") == "done"
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
    global _daily_rendering
    try:
        s = load_json(DAILY_AUTO_F, {})
        today = datetime.now().strftime("%Y-%m-%d")
        if s.get("today") != today:
            next_id = _next_lv1_word_id(s.get("current_word_id", 0))
            s = {"auto_upload": s.get("auto_upload", False),
                 "current_word_id": next_id, "today": today,
                 "illust_done": False, "langs": _daily_init_langs()}
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
    except Exception as e:
        print(f"  [daily_tick] {e}")

def _daily_scheduler_loop():
    while True:
        time.sleep(60)
        _daily_auto_tick()

threading.Thread(target=_daily_scheduler_loop, daemon=True).start()

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
        _illust_proc = subprocess.Popen(cmd)
        _illust_proc.wait()
        rc = _illust_proc.returncode
        _illust_proc = None
        final = load_json(ILLUST_PROG_F, {})
        if final.get("status") == "running":
            save_json(ILLUST_PROG_F, {**final,
                "status": "cancelled" if rc == -15 else ("done" if rc == 0 else "failed"),
                "pct": final.get("pct", 0),
                "completed_at": datetime.now().isoformat()})
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
        "overview": {"total":len(db),"generated":len(videos),"uploaded":len(uploaded),"last_day":last_day},
        "illustration": get_illustration_stats(),
        "music_files": get_music_files(),
        "timeline": timeline,
        "youtube": yt,
        "structure": STRUCTURE,
    })

@app.route("/api/node")
def api_node():
    cat  = request.args.get("category","시험용")
    exam = request.args.get("exam")
    lang = request.args.get("lang")
    stats = get_node_stats(cat, exam, lang)
    videos = get_videos_log()
    uploaded, _ = get_uploads()
    upl_map = {u["word_id"]:u for u in uploaded
               if (not exam or u.get("exam","TOPIK") == exam) and (not lang or u.get("language","EN") == lang)}
    vid_map = {v["word_id"]:v for v in videos
               if (not exam or v.get("exam","TOPIK") == exam) and (not lang or v.get("language","EN") == lang)}
    db = get_db(cat, exam or "TOPIK", lang or "EN")
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
    return jsonify({**stats,"video_list":video_list[-200:],"db_path":db_path_for(cat,exam,lang)})

@app.route("/api/render-config/toggle", methods=["POST"])
def api_toggle_render():
    data = request.get_json(silent=True) or {}
    enabled = data.get("desktop_enabled", True)
    set_render_config(enabled)
    return jsonify({"desktop_enabled": enabled})

@app.route("/api/render", methods=["POST"])
def api_render():
    global _render_thread
    data = request.get_json(silent=True) or {}
    word_id = data.get("word_id") or get_next_word_id()
    target  = data.get("target", "auto")
    exam    = data.get("exam", "TOPIK")
    lang    = data.get("lang", "EN")
    if not word_id: return jsonify({"error":"렌더링할 단어가 없습니다"}),400
    q = load_json(QUEUE_FILE,{})
    if q.get("status") in ("pending","claimed"):
        return jsonify({"error":"이미 렌더링 중입니다","queue":q}),409
    # 단어의 level 찾아서 정확한 DB 경로 결정
    db = get_db("시험용", exam, lang)
    word_level = None
    for w in db:
        if w["id"] == word_id:
            word_level = w.get("level", 1)
            break
    db_path = render_db_path_for(exam, lang, word_level or 1)
    write_queue_job(word_id, db_path, exam=exam, lang=lang)
    cfg = get_render_config()
    use_desktop = (target == "desktop") if target != "auto" else cfg.get("desktop_enabled")
    if use_desktop:
        return jsonify({"status":"queued","host":"desktop","word_id":word_id})
    _render_thread = threading.Thread(target=run_render_nas,args=(word_id,db_path,exam,lang),daemon=True)
    _render_thread.start()
    return jsonify({"status":"rendering","host":"nas","word_id":word_id})

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

@app.route("/api/batch/date")
def api_batch_date():
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    return jsonify(get_batch_for_date(date_str))

@app.route("/api/render/batch", methods=["POST"])
def api_render_batch():
    global _batch_thread
    data = request.get_json(silent=True) or {}
    word_ids    = data.get("word_ids", [])
    target      = data.get("target", "auto")
    auto_upload = data.get("auto_upload", False)
    if not word_ids:
        batch    = get_batch_today()
        word_ids = [b["word"]["id"] for b in batch if b.get("word") and b.get("status") == "pending"]
    if not word_ids:
        return jsonify({"error": "렌더링할 단어가 없습니다"}), 400
    bq = load_json(BATCH_QUEUE_F, {})
    if bq.get("status") == "running":
        return jsonify({"error": "이미 배치 렌더링 중"}), 409
    # words_map 구성 (업로드 시 단어 정보 필요)
    db = get_db()
    words_map = {w["id"]: w for w in db if w["id"] in word_ids}
    items = [{"word_id": wid, "word": words_map[wid]["word"] if wid in words_map else "", "status": "pending"} for wid in word_ids]
    save_json(BATCH_QUEUE_F, {"status":"running","total":len(items),"current":0,
        "items":items,"target":target,"auto_upload":auto_upload,
        "started_at":datetime.now().isoformat()})
    _batch_thread = threading.Thread(target=run_batch_render,
        args=(word_ids, target), kwargs={"auto_upload": auto_upload, "words_map": words_map},
        daemon=True)
    _batch_thread.start()
    return jsonify({"status": "started", "count": len(word_ids), "target": target, "auto_upload": auto_upload})

@app.route("/api/render/upload", methods=["POST"])
def api_render_upload():
    """렌더링 완료된 영상 수동 업로드"""
    data = request.get_json(silent=True) or {}
    word_id = data.get("word_id")
    lang    = data.get("lang", "EN")
    exam    = data.get("exam", "TOPIK")
    if not word_id:
        return jsonify({"error": "word_id 필요"}), 400
    db = get_words_db()
    word = next((w for w in db if w["id"] == word_id), None)
    if not word:
        return jsonify({"error": f"단어 {word_id} 없음"}), 404
    lv = word.get("level", 1)
    # 영상 경로 탐색 (youtube → reels 순)
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

@app.route("/api/render/cancel", methods=["POST"])
def api_render_cancel():
    """배치/단일 렌더링 취소"""
    bq = load_json(BATCH_QUEUE_F, {})
    if bq.get("status") == "running":
        bq["status"] = "cancelled"
        save_json(BATCH_QUEUE_F, bq)
        # 단일 렌더 큐도 취소
        q = load_json(QUEUE_FILE, {})
        if q.get("status") in ("pending", "claimed"):
            q["status"] = "failed"
            q["error"] = "cancelled"
            save_json(QUEUE_FILE, q)
        return jsonify({"status": "cancelled"})
    # 단일 렌더만 진행 중
    q = load_json(QUEUE_FILE, {})
    if q.get("status") in ("pending", "claimed"):
        q["status"] = "failed"
        q["error"] = "cancelled"
        save_json(QUEUE_FILE, q)
        return jsonify({"status": "cancelled"})
    return jsonify({"error": "취소할 렌더링이 없습니다"}), 400

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
    global _batch_thread
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
    bq = load_json(BATCH_QUEUE_F, {})
    if bq.get("status") == "running":
        return jsonify({"error": "이미 렌더링 중"}), 409
    base_lang = langs[0]
    # 모든 시험×등급 조합에서 단어 수집
    job_items = []
    queue_items = []
    all_words = []
    for t in targets:
        exam_t    = t["exam"]
        level_t   = t["level"]
        ids_str_t = t.get("ids_str", "")
        if ids_str_t:
            ids_list = parse_ids_str(ids_str_t)
            words_t  = get_words_by_ids(exam_t, base_lang, level_t, ids_list)
        else:
            words_t = get_next_words_for_custom(exam_t, base_lang, level_t, 30, None, None)
        all_words.extend(words_t)
        for lg in langs:
            db_path = render_db_path_for(exam_t, lg, level_t)
            for w in words_t:
                for fmt in formats:
                    job_items.append((w["id"], lg, db_path, w["word"], fmt))
                    fmt_label = "" if fmt == "youtube" else " [릴스]"
                    queue_items.append({"word_id": w["id"], "word": w["word"] + fmt_label,
                                         "exam": exam_t, "level": level_t,
                                         "lang": lg, "fmt": fmt, "status": "pending"})
    if not job_items:
        return jsonify({"error": "렌더링할 단어가 없습니다"}), 400
    first_exam  = targets[0]["exam"]
    first_level = targets[0]["level"]
    save_json(BATCH_QUEUE_F, {"status":"running","total":len(queue_items),"current":0,
        "items":queue_items,"target":target,"exam":first_exam,"langs":langs,"level":first_level,
        "started_at":datetime.now().isoformat()})
    _batch_thread = threading.Thread(
        target=run_batch_render,
        kwargs={"word_ids": [], "target": target, "exam": first_exam,
                "lang": base_lang, "job_items": job_items},
        daemon=True)
    _batch_thread.start()
    return jsonify({"status":"started","count":len(job_items),"target":target,
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
    global _illust_thread
    if load_json(ILLUST_PROG_F,{"status":"idle"}).get("status") == "running":
        return jsonify({"error":"이미 생성 중"}),409
    data = request.get_json(silent=True) or {}
    start,end = int(data.get("start",1)),int(data.get("end",10))
    mode = data.get("mode", "both")  # "both", "words", "sentences"
    _illust_thread = threading.Thread(target=run_illustration_generation,args=(start,end,mode),daemon=True)
    _illust_thread.start()
    return jsonify({"status":"started","start":start,"end":end,"mode":mode})

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
    log_map = {(e["theme_id"], e["lang"]): e for e in clog}
    themes = []
    for t in db.get("themes", []):
        langs = {}
        for lang in ["EN", "JP", "CN", "VN", "ES"]:
            entry = log_map.get((t["id"], lang))
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
    ok, msg = run_conv_render_bg(theme_id, lang)
    if not ok:
        return jsonify({"error": msg}), 409
    return jsonify({"status": "started", "theme_id": theme_id, "lang": lang})

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
    ok, msg = run_phrase_illust_bg(sit_id, start, end)
    if not ok:
        return jsonify({"error": msg}), 409
    return jsonify({"status": "started"})

@app.route("/api/phrase/illust/progress")
def api_phrase_illust_progress():
    running = bool(_phrase_illust_thread and _phrase_illust_thread.is_alive())
    prog = load_json(PHRASE_ILLUST_PROG, {})
    return jsonify({**_phrase_illust_progress, "running": running,
                    "file_progress": prog})

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
    ok, msg = run_phrase_video_bg(sit_id, start, end)
    if not ok:
        return jsonify({"error": msg}), 409
    return jsonify({"status": "started"})

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
.s-group{padding:4px 14px 2px;font-size:.6rem;color:var(--muted2);text-transform:uppercase;letter-spacing:.1em;margin-top:10px;}
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
  <div class="s-group">콘텐츠</div>
  <div class="s-item l2" data-view="exam:TOPIK" onclick="toggleExam(this,'exam:TOPIK')" style="--c:#818cf8;">
    <span>🇰🇷</span><span>TOPIK</span><span class="arrow" id="arr-TOPIK">▶</span>
  </div>
  <div class="s-ch" id="ch-TOPIK">
    <div class="s-item l3" data-view="lang:TOPIK:EN" onclick="nav(this,'lang:TOPIK:EN')" style="--c:#818cf8;">🇺🇸 English</div>
    <div class="s-item l3" data-view="lang:TOPIK:CN" onclick="nav(this,'lang:TOPIK:CN')" style="--c:#818cf8;">🇨🇳 中文</div>
    <div class="s-item l3" data-view="lang:TOPIK:JP" onclick="nav(this,'lang:TOPIK:JP')" style="--c:#818cf8;">🇯🇵 日本語</div>
    <div class="s-item l3" data-view="lang:TOPIK:VN" onclick="nav(this,'lang:TOPIK:VN')" style="--c:#818cf8;">🇻🇳 Tiếng Việt</div>
    <div class="s-item l3" data-view="lang:TOPIK:ES" onclick="nav(this,'lang:TOPIK:ES')" style="--c:#818cf8;">🇪🇸 Español</div>
  </div>
  <div class="s-item l2 dim" style="--c:#60a5fa;"><span>📝</span><span>TOEIC</span></div>
  <div class="s-item l2 dim" style="--c:#f472b6;"><span>🌸</span><span>JLPT</span></div>
  <div class="s-item l2 dim" style="--c:#a78bfa;"><span>🎓</span><span>IELTS</span></div>
  <div class="s-item l2 dim" style="--c:#f87171;"><span>🐉</span><span>HSK</span></div>
  <div class="s-sep"></div>
  <div class="s-group">작업</div>
  <div class="s-item" data-view="render" onclick="nav(this,'render')" style="--c:#3fb950;">
    <span>🎬</span><span>렌더링</span><span id="sb-render-badge" style="margin-left:auto;font-size:.6rem;"></span>
  </div>
  <div class="s-item" data-view="illustrations" onclick="nav(this,'illustrations')" style="--c:#f59e0b;">
    <span>🎨</span><span>일러스트</span>
  </div>
  <div class="s-item" data-view="videos" onclick="nav(this,'videos')" style="--c:#22d3ee;">
    <span>📋</span><span>영상 목록</span>
  </div>
  <div class="s-item" data-view="youtube" onclick="nav(this,'youtube')" style="--c:#f87171;">
    <span>▶</span><span>YouTube</span>
  </div>
  <div class="s-sep"></div>
  <div class="s-group">회화</div>
  <div class="s-item" data-view="conv" onclick="nav(this,'conv')" style="--c:#ec4899;">
    <span>💬</span><span>기본 회화</span>
  </div>
  <div class="s-item" data-view="phrase" onclick="nav(this,'phrase')" style="--c:#a78bfa;">
    <span>📖</span><span>회화 일러스트·영상</span>
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
  <!-- 상단: 렌더 설정 + 상태 -->
  <div class="g2" style="margin-bottom:14px;">
    <div class="card" style="display:flex;align-items:center;gap:12px;">
      <div style="font-weight:600;font-size:.85rem;">렌더링 위치</div>
      <button id="toggle-btn" onclick="toggleRender()" class="btn btn-p" style="font-size:.72rem;"></button>
      <span id="rp-target-info" style="font-size:.66rem;color:var(--muted);"></span>
    </div>
    <div class="card" id="rp-batch-progress" style="display:flex;align-items:center;gap:10px;">
      <span id="rp-batch-prog-label" style="font-size:.72rem;font-weight:600;color:var(--green);white-space:nowrap;">대기 중</span>
      <div class="pbar-bg" style="flex:1;height:6px;"><div id="rp-batch-prog-bar" class="pbar" style="height:6px;width:0%;background:var(--green);"></div></div>
      <span id="rp-batch-prog-pct" style="font-size:.72rem;font-weight:700;color:var(--green);min-width:32px;text-align:right;">0%</span>
      <span id="rp-batch-prog-step" style="font-size:.62rem;color:var(--muted);white-space:nowrap;"></span>
    </div>
  </div>
  <!-- 탭 -->
  <div class="tabs">
    <button class="tab on" id="rp-tab-batch" onclick="rpTab('batch')">📅 오늘 배치</button>
    <button class="tab" id="rp-tab-custom" onclick="rpTab('custom')">🎬 커스텀</button>
    <button class="tab" id="rp-tab-history" onclick="rpTab('history')">🗓 날짜별</button>
    <button class="tab" id="rp-tab-live" onclick="rpTab('live')">📊 진행 상황</button>
    <button class="tab" id="rp-tab-config" onclick="rpTab('config')">⚙️ 설정</button>
  </div>
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

    <!-- 수동 트리거 -->
    <div style="display:flex;gap:8px;">
      <button onclick="dailyTrigger()" class="btn btn-g" style="flex:1;justify-content:center;font-size:.78rem;">▶ 지금 렌더링 시작</button>
    </div>
    <div style="margin-top:6px;font-size:.65rem;color:var(--muted2);text-align:center;">자동 OFF 상태에서도 수동으로 실행 가능</div>
  </div>
  <!-- 탭 내용: 커스텀 -->
  <div id="rp-custom" style="display:none;">
    <div class="sec">렌더링 대상</div>
    <div style="margin-bottom:10px;">
      <div id="rc-targets">
        <div class="rc-target-row" style="display:flex;gap:6px;align-items:flex-end;margin-bottom:6px;">
          <div style="flex:3;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">시험</div>
            <select class="rc-exam inp" onchange="updateCustomPreview()" style="width:100%;"><option value="TOPIK">🇰🇷 TOPIK</option><option value="TOEIC">📝 TOEIC</option><option value="JLPT">🌸 JLPT</option><option value="IELTS">🎓 IELTS</option><option value="HSK">🐉 HSK</option></select></div>
          <div style="flex:2;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">등급</div>
            <select class="rc-level inp" onchange="updateCustomPreview()" style="width:100%;"><option value="1">1급</option><option value="2">2급</option><option value="3">3급</option><option value="4">4급</option><option value="5">5급</option><option value="6">6급</option></select></div>
          <div style="flex:2.5;"><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">ID <span style="font-weight:400;opacity:.7;">(숫자·범위·쉼표)</span></div>
            <input class="rc-ids inp" placeholder="예: 1, 3~10, 15" oninput="updateCustomPreview()" style="width:100%;"></div>
          <div style="width:28px;flex-shrink:0;"></div>
        </div>
      </div>
      <button onclick="addTargetRow()" class="btn btn-m" style="font-size:.68rem;padding:5px 12px;margin-top:4px;">＋ 추가</button>
    </div>
    <div style="margin-bottom:12px;">
      <div style="font-size:.62rem;color:var(--muted2);margin-bottom:6px;">언어 <span style="color:var(--muted2);font-weight:400;">(복수 선택 가능)</span></div>
      <div id="rc-lang-btns" style="display:flex;gap:6px;flex-wrap:wrap;">
        <button class="rc-lang-btn active" data-lang="EN" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--blue);background:var(--blue)22;color:var(--blue);cursor:pointer;">🇺🇸 EN</button>
        <button class="rc-lang-btn" data-lang="JP" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;">🇯🇵 JP</button>
        <button class="rc-lang-btn" data-lang="CN" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;">🇨🇳 CN</button>
        <button class="rc-lang-btn" data-lang="VN" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;">🇻🇳 VN</button>
        <button class="rc-lang-btn" data-lang="ES" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;">🇪🇸 ES</button>
        <button class="rc-lang-btn" data-lang="KO" onclick="toggleLangBtn(this)" style="padding:5px 12px;font-size:.72rem;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;">🇰🇷 KO</button>
      </div>
    </div>
    <div style="margin-bottom:12px;">
      <div style="font-size:.62rem;color:var(--muted2);margin-bottom:6px;">포맷 <span style="color:var(--muted2);font-weight:400;">(복수 선택 가능)</span></div>
      <div style="display:flex;gap:6px;">
        <button class="rc-fmt-btn active" data-fmt="youtube" onclick="toggleFmtBtn(this)"
          style="padding:5px 16px;font-size:.72rem;border-radius:6px;border:1px solid var(--green);background:var(--green)22;color:var(--green);cursor:pointer;flex:1;">
          ▶ 본편 (YouTube)
        </button>
        <button class="rc-fmt-btn active" data-fmt="reels" onclick="toggleFmtBtn(this)"
          style="padding:5px 16px;font-size:.72rem;border-radius:6px;border:1px solid var(--amber);background:var(--amber)22;color:var(--amber);cursor:pointer;flex:1;">
          ⚡ 릴스 (Shorts)
        </button>
      </div>
    </div>
    <div style="display:flex;gap:6px;margin-bottom:6px;">
      <button id="rc-target-desktop" onclick="setCustomTarget('desktop')" class="btn btn-p" style="flex:1;justify-content:center;font-size:.72rem;">💻 데스크탑 GPU</button>
      <button id="rc-target-nas" onclick="setCustomTarget('nas')" class="btn btn-m" style="flex:1;justify-content:center;font-size:.72rem;">🖥 NAS CPU</button>
    </div>
    <div id="rc-time-est" style="font-size:.64rem;color:var(--muted2);margin-bottom:12px;"></div>
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
      <span class="sec" style="margin:0;">미리보기</span>
      <span id="rc-remaining" style="font-size:.62rem;color:var(--muted2);"></span>
    </div>
    <div id="rc-preview" style="margin-bottom:12px;max-height:300px;overflow-y:auto;"></div>
    <button id="rc-start" onclick="startCustomRender()" class="btn btn-g" style="width:100%;justify-content:center;">▶ 렌더링 시작</button>
  </div>
  <!-- 탭 내용: 날짜별 -->
  <div id="rp-history" style="display:none;">
    <input type="date" id="rp-date-pick" onchange="loadHistoryDate()" class="inp" style="width:100%;margin-bottom:12px;">
    <div id="rp-history-list"></div>
  </div>
  <!-- 탭 내용: 진행 상황 -->
  <div id="rp-live" style="display:none;">
    <div id="live-summary" style="margin-bottom:12px;padding:12px;background:var(--bg3);border-radius:8px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
        <span id="live-status-label" style="font-size:.8rem;font-weight:700;color:var(--green);">대기 중</span>
        <div style="display:flex;align-items:center;gap:8px;">
          <span id="live-timing" style="font-size:.62rem;color:var(--muted2);"></span>
          <button id="live-cancel-btn" onclick="cancelBatchRender()" style="display:none;font-size:.68rem;padding:3px 10px;border-radius:5px;border:none;background:#ef4444;color:#fff;cursor:pointer;font-weight:600;">⏹ 취소</button>
        </div>
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
    <select id="vf-level" onchange="filterVids()" class="inp"><option value="">전체 등급</option><option>1</option><option>2</option><option>3</option><option>4</option><option>5</option><option>6</option></select>
    <select id="vf-music" onchange="filterVids()" class="inp"><option value="">전체 음악</option></select>
    <select id="vf-status" onchange="filterVids()" class="inp"><option value="">전체 상태</option><option value="uploaded">업로드됨</option><option value="generated">생성만</option></select>
    <span id="vf-count" style="font-size:.72rem;color:var(--muted);margin-left:auto;"></span>
  </div>
  <div class="card" style="overflow-x:auto;padding:0;">
    <table>
      <thead><tr><th>Day</th><th>ID</th><th>단어</th><th>뜻</th><th>등급</th><th>음악</th><th>크기</th><th>생성</th><th>조회수</th><th>상태</th></tr></thead>
      <tbody id="vids-tbody"></tbody>
    </table>
  </div>
</div>

<!-- ══ 일러스트 ═════════════════════════════════════════ -->
<div id="view-illustrations" class="view">
  <div class="bc"><span class="cur">🎨 일러스트 관리</span></div>
  <div class="card" style="margin-bottom:14px;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
      <div style="font-weight:600;font-size:.88rem;">일러스트 생성 현황</div>
      <span id="illust-view-badge" class="badge badge-m"></span>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:.74rem;color:var(--muted);margin-bottom:3px;"><span>🖼 단어 일러스트</span><span id="illust-view-word-txt">–</span><span id="illust-view-word-pct" style="margin-left:auto;padding-left:8px;">0%</span></div>
    <div class="pbar-bg" style="height:6px;margin-bottom:10px;"><div id="illust-view-word-bar" class="pbar" style="height:6px;width:0%;background:linear-gradient(90deg,#f59e0b,#f97316);"></div></div>
    <div style="display:flex;justify-content:space-between;font-size:.74rem;color:var(--muted);margin-bottom:3px;"><span>📝 예문 일러스트</span><span id="illust-view-sent-txt">–</span><span id="illust-view-sent-pct" style="margin-left:auto;padding-left:8px;">0%</span></div>
    <div class="pbar-bg" style="height:6px;margin-bottom:14px;"><div id="illust-view-sent-bar" class="pbar" style="height:6px;width:0%;background:linear-gradient(90deg,#818cf8,#a855f7);"></div></div>
    <div id="illust-view-summary" style="margin-bottom:10px;padding:8px 12px;background:var(--bg);border-radius:7px;border:1px solid var(--border2);"></div>
    <div class="g6" id="illust-view-levels" style="margin-bottom:14px;"></div>
    <div id="illust-view-log" style="display:none;background:var(--bg);border-radius:6px;padding:10px;font-size:.7rem;color:var(--muted);font-family:monospace;max-height:100px;overflow:auto;margin-bottom:14px;white-space:pre-wrap;"></div>
    <!-- 일일 사용량 (일러스트 뷰) -->
    <div id="illust-view-usage" style="margin-top:14px;background:var(--bg);border-radius:8px;padding:12px 14px;border:1px solid var(--border2);">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
        <span style="font-size:.78rem;font-weight:600;">오늘 Gemini API 사용량</span>
        <span id="illust-view-usage-txt" style="font-size:.82rem;font-weight:700;">–</span>
      </div>
      <div id="illust-view-usage-detail" style="font-size:.7rem;color:var(--muted);"></div>
      <div id="illust-view-exhausted" style="display:none;margin-top:8px;padding:6px 10px;border-radius:6px;background:#dc262622;border:1px solid #dc262644;font-size:.75rem;color:#f87171;font-weight:600;text-align:center;"></div>
    </div>
  </div>
  <!-- 개별 일러스트 브라우저 -->
  <div class="card" style="margin-bottom:14px;">
    <div class="sec">일러스트 미리보기 / 재생성</div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;flex-wrap:wrap;">
      <span style="font-size:.74rem;color:var(--muted);">등급:</span>
      <select id="illust-browse-level" class="inp" style="width:60px;" onchange="onIllustLevelChange()">
        <option value="1">1급</option><option value="2">2급</option><option value="3">3급</option>
        <option value="4">4급</option><option value="5">5급</option><option value="6">6급</option>
      </select>
      <span style="font-size:.74rem;color:var(--muted);">단어 ID:</span>
      <input id="illust-browse-id" class="num-input" type="number" value="1" min="1" max="300" style="width:70px;">
      <button onclick="loadIllustBrowse()" class="btn btn-a">조회</button>
      <button onclick="illustBrowseNav(-1)" class="btn btn-m">&lt; 이전</button>
      <button onclick="illustBrowseNav(1)" class="btn btn-m">다음 &gt;</button>
      <span id="illust-browse-id-range" style="font-size:.62rem;color:var(--muted2);"></span>
      <span id="illust-browse-info" style="font-size:.78rem;font-weight:600;margin-left:8px;"></span>
    </div>
    <div id="illust-browse-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;"></div>
    <div id="illust-regen-status" style="display:none;margin-top:10px;padding:8px 12px;border-radius:6px;background:var(--bg);font-size:.74rem;color:var(--amber);font-weight:600;"></div>
  </div>
  <div class="card">
    <div class="sec">일러스트 배치 생성</div>
    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
      <span style="font-size:.74rem;color:var(--muted);">ID 범위:</span>
      <input id="illust-start2" class="num-input" type="number" value="1"><span style="color:var(--muted);">~</span>
      <input id="illust-end2" class="num-input" type="number" value="100">
      <select id="illust-mode2" onchange="updateIllustCost2()" class="inp"><option value="both">단어+예문</option><option value="words">🖼 단어만</option><option value="sentences">📝 예문만</option></select>
      <button id="illust-gen-btn2" onclick="startIllustGen2()" class="btn btn-a">🎨 생성</button>
      <button id="illust-cancel-btn2" onclick="cancelIllustGen()" class="btn btn-d" style="display:none;">⏹ 취소</button>
      <button id="illust-reset-btn2" onclick="resetIllustProgress()" class="btn btn-d" style="display:none;background:#7c3aed;">🔄 상태 초기화</button>
      <button onclick="setIllustRange2(1,1800)" class="btn btn-m">전체</button>
      <span id="illust-cost2" style="font-size:.72rem;color:var(--amber);font-weight:600;"></span>
    </div>
  </div>
  <!-- 스타일 감사 -->
  <div class="card">
    <div class="sec">🔍 스타일 감사 (VLM 하네스)</div>
    <div style="font-size:.72rem;color:var(--muted);margin-bottom:10px;">
      생성된 이미지를 Gemini Vision으로 분석 — 텍스트 침투 / 인물 비율 / 투시 / 스타일 일관성 검사
    </div>
    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:10px;">
      <span style="font-size:.74rem;color:var(--muted);">감사할 ID (콤마 구분):</span>
      <input id="audit-ids" class="inp" type="text" placeholder="예: 1,2,3,5,10" style="width:180px;font-size:.75rem;">
      <button onclick="runStyleAudit()" class="btn btn-a" id="audit-run-btn">🔍 감사 시작</button>
      <button onclick="loadAuditResults()" class="btn btn-m">결과 새로고침</button>
    </div>
    <div id="audit-status" style="display:none;margin-bottom:8px;font-size:.74rem;color:var(--amber);font-weight:600;"></div>
    <div id="audit-summary" style="display:none;margin-bottom:8px;padding:8px 12px;border-radius:6px;background:var(--bg);font-size:.75rem;"></div>
    <div id="audit-regen-actions" style="display:none;margin-bottom:10px;padding:6px 0;gap:8px;align-items:center;flex-wrap:wrap;">
      <button onclick="auditRegenAll()" class="btn" style="background:#ef4444;color:#fff;font-size:.73rem;padding:4px 12px;" id="audit-regen-all-btn">✗ 실패 전체 재생성</button>
      <button onclick="auditRegenSelected()" class="btn btn-m" style="font-size:.73rem;padding:4px 12px;" id="audit-regen-sel-btn">☑ 선택 재생성</button>
      <span id="audit-regen-status" style="font-size:.72rem;color:var(--amber);font-weight:600;"></span>
    </div>
    <div id="audit-results" style="display:none;overflow-x:auto;">
      <table style="width:100%;font-size:.72rem;">
        <thead><tr style="color:var(--muted);">
          <th style="padding:4px 8px;"><input type="checkbox" id="audit-check-all" onchange="auditToggleAll(this.checked)" title="실패 전체 선택" style="cursor:pointer;"></th>
          <th style="text-align:left;padding:4px 8px;">ID</th>
          <th style="text-align:left;padding:4px 8px;">단어</th>
          <th style="text-align:left;padding:4px 8px;">급</th>
          <th style="text-align:left;padding:4px 8px;">예문</th>
          <th style="text-align:left;padding:4px 8px;">결과</th>
          <th style="text-align:left;padding:4px 8px;">문제</th>
        </tr></thead>
        <tbody id="audit-tbody"></tbody>
      </table>
    </div>
  </div>
</div>

<!-- ══ YouTube ══════════════════════════════════════════ -->
<div id="view-youtube" class="view">
  <div class="bc"><span class="cur">▶ YouTube 통계</span></div>
  <div id="yt-no-key" class="card" style="text-align:center;padding:36px;">
    <div style="font-size:1.8rem;margin-bottom:8px;">📺</div>
    <div style="color:var(--muted);margin-bottom:6px;">YouTube API 키가 필요합니다</div>
    <code style="background:var(--border);padding:4px 10px;border-radius:5px;font-size:.76rem;">.env → YOUTUBE_API_KEY=AIza...</code>
  </div>
  <div id="yt-content" style="display:none;">
    <div class="g3" style="margin-bottom:14px;">
      <div class="card-sm kpi"><div id="yt-subs" class="num" style="color:var(--red);">–</div><div class="label">구독자</div></div>
      <div class="card-sm kpi"><div id="yt-views" class="num" style="color:var(--amber);">–</div><div class="label">총 조회수</div></div>
      <div class="card-sm kpi"><div id="yt-vcnt" class="num" style="color:var(--blue);">–</div><div class="label">영상 수</div></div>
    </div>
    <div class="card" style="margin-bottom:14px;"><div class="sec">영상별 조회수 TOP 20</div><canvas id="chart-yt-views" height="130"></canvas></div>
    <div class="card"><div class="sec">영상 통계</div><div style="overflow-x:auto;"><table><thead><tr><th>Day</th><th>단어</th><th>등급</th><th>조회수</th><th>좋아요</th><th>YouTube</th></tr></thead><tbody id="yt-tbody"></tbody></table></div></div>
  </div>
</div>

<!-- ══ 기본 회화 ══════════════════════════════════════════ -->
<div id="view-conv" class="view">
  <div class="bc"><span class="cur">💬 기본 회화</span></div>
  <!-- 언어 선택 -->
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
    <span style="font-size:.76rem;color:var(--muted);">언어:</span>
    <div id="conv-lang-btns" style="display:flex;gap:6px;">
      <button class="btn btn-p conv-lang-btn active" data-lang="EN" onclick="convSetLang('EN')">🇺🇸 EN</button>
      <button class="btn btn-m conv-lang-btn" data-lang="JP" onclick="convSetLang('JP')">🇯🇵 JP</button>
      <button class="btn btn-m conv-lang-btn" data-lang="CN" onclick="convSetLang('CN')">🇨🇳 CN</button>
      <button class="btn btn-m conv-lang-btn" data-lang="VN" onclick="convSetLang('VN')">🇻🇳 VN</button>
      <button class="btn btn-m conv-lang-btn" data-lang="ES" onclick="convSetLang('ES')">🇪🇸 ES</button>
    </div>
    <button class="btn btn-m" onclick="loadConvThemes()" style="margin-left:auto;">↺ 새로고침</button>
  </div>
  <!-- 렌더링 진행 상태 -->
  <div id="conv-progress" style="display:none;background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:14px;margin-bottom:16px;">
    <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
      <span id="conv-prog-label" style="font-size:.78rem;font-weight:600;color:var(--amber);">렌더링 중...</span>
      <span id="conv-prog-pct" style="font-size:.78rem;font-weight:700;color:var(--amber);">0%</span>
    </div>
    <div class="pbar-bg" style="height:6px;"><div id="conv-prog-bar" class="pbar" style="height:6px;background:var(--amber);width:0%;"></div></div>
    <div id="conv-prog-msg" style="font-size:.66rem;color:var(--muted);margin-top:5px;"></div>
  </div>
  <!-- 테마 그리드 -->
  <div id="conv-themes" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;"></div>
  <div id="conv-empty" style="display:none;text-align:center;padding:48px;color:var(--muted);">
    <div style="font-size:2rem;margin-bottom:10px;">📂</div>
    <div>conversations_db.json 파일이 없거나 비어 있습니다</div>
  </div>
</div>

<!-- ══ 회화 일러스트·영상 ═══════════════════════════════════ -->
<div id="view-phrase" class="view">
  <div class="bc"><span class="cur">📖 회화 일러스트·영상</span></div>

  <!-- 탭 -->
  <div style="display:flex;gap:8px;margin-bottom:16px;">
    <button id="ph-tab-illust" class="btn btn-p" onclick="phTab('illust')" style="flex:1;">🖼 일러스트 생성</button>
    <button id="ph-tab-video"  class="btn btn-m" onclick="phTab('video')"  style="flex:1;">🎬 영상 생성</button>
  </div>

  <!-- 일러스트 탭 -->
  <div id="ph-panel-illust">
    <!-- 일러스트 생성 컨트롤 -->
    <div class="card" style="margin-bottom:14px;">
      <div class="sec">일러스트 생성</div>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px;">
        <span style="font-size:.74rem;color:var(--muted);">범위:</span>
        <input id="ph-illust-start" type="number" placeholder="시작 ID" min="1"
               style="width:90px;padding:5px 8px;border-radius:6px;border:1px solid var(--border);background:var(--bg2);color:var(--text);font-size:.8rem;">
        <span style="color:var(--muted);">~</span>
        <input id="ph-illust-end" type="number" placeholder="끝 ID" min="1"
               style="width:90px;padding:5px 8px;border-radius:6px;border:1px solid var(--border);background:var(--bg2);color:var(--text);font-size:.8rem;">
        <button class="btn btn-p" onclick="startPhraseIllust(null)" style="margin-left:auto;">▶ 범위 생성</button>
        <button class="btn btn-m" onclick="cancelPhraseIllust()">✕ 취소</button>
        <button class="btn btn-m" onclick="loadPhraseSituations()">↺ 새로고침</button>
      </div>
      <!-- 진행 바 -->
      <div id="ph-illust-prog" style="display:none;">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
          <span id="ph-illust-prog-label" style="font-size:.75rem;font-weight:600;color:var(--amber);">생성 중...</span>
          <span id="ph-illust-prog-pct"   style="font-size:.75rem;font-weight:700;color:var(--amber);">0%</span>
        </div>
        <div class="pbar-bg" style="height:6px;"><div id="ph-illust-prog-bar" class="pbar" style="height:6px;background:var(--amber);width:0%;"></div></div>
        <div id="ph-illust-prog-msg" style="font-size:.65rem;color:var(--muted);margin-top:3px;"></div>
      </div>
    </div>
    <!-- 상황 목록 -->
    <div id="ph-illust-list" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;"></div>
    <div id="ph-illust-empty" style="display:none;text-align:center;padding:48px;color:var(--muted);">
      <div style="font-size:2rem;margin-bottom:8px;">📂</div>
      <div>phrases_db.json 파일이 없거나 비어 있습니다</div>
    </div>
  </div>

  <!-- 영상 탭 -->
  <div id="ph-panel-video" style="display:none;">
    <!-- 영상 생성 컨트롤 -->
    <div class="card" style="margin-bottom:14px;">
      <div class="sec">영상 생성</div>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px;">
        <span style="font-size:.74rem;color:var(--muted);">범위:</span>
        <input id="ph-video-start" type="number" placeholder="시작 ID" min="1"
               style="width:90px;padding:5px 8px;border-radius:6px;border:1px solid var(--border);background:var(--bg2);color:var(--text);font-size:.8rem;">
        <span style="color:var(--muted);">~</span>
        <input id="ph-video-end" type="number" placeholder="끝 ID" min="1"
               style="width:90px;padding:5px 8px;border-radius:6px;border:1px solid var(--border);background:var(--bg2);color:var(--text);font-size:.8rem;">
        <button class="btn btn-p" onclick="startPhraseVideo(null)" style="margin-left:auto;">▶ 범위 생성</button>
        <button class="btn btn-m" onclick="cancelPhraseVideo()">✕ 취소</button>
        <button class="btn btn-m" onclick="loadPhraseSituations()">↺ 새로고침</button>
      </div>
      <!-- 진행 바 -->
      <div id="ph-video-prog" style="display:none;">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
          <span id="ph-video-prog-label" style="font-size:.75rem;font-weight:600;color:var(--accent);">생성 중...</span>
          <span id="ph-video-prog-pct"   style="font-size:.75rem;font-weight:700;color:var(--accent);">0%</span>
        </div>
        <div class="pbar-bg" style="height:6px;"><div id="ph-video-prog-bar" class="pbar" style="height:6px;background:var(--accent);width:0%;"></div></div>
        <div id="ph-video-prog-msg" style="font-size:.65rem;color:var(--muted);margin-top:3px;"></div>
      </div>
    </div>
    <!-- 상황 목록 -->
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

let _ov=null, _node=null, _chartTL=null, _chartYT=null;
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
  const target=document.getElementById('view-'+view) || document.getElementById('view-lang:TOPIK:EN');
  if(target) target.style.display='block';
  _currentView=view;
  if(view.startsWith('lang:')) renderLangView(view);
  if(view.startsWith('lang:') || view.startsWith('exam:')) loadNodeData(view);
  if(view==='render'){loadBatchData();rpTab('batch');}
  if(view==='conv') loadConvThemes();
  if(view==='phrase') loadPhraseSituations();
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
function toggleRenderPanel(){nav(document.querySelector('[data-view=render]'),'render');}

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
    if(_currentView.startsWith('lang:')||_currentView.startsWith('exam:')) loadNodeData(_currentView);
    if(_currentView==='youtube') renderYoutube(d);
  }catch(e){document.getElementById('last-upd').textContent='연결 오류';}
}

async function loadNodeData(view){
  try{
    const parts=view.split(':');
    let url='/api/node?';
    if(parts[0]==='exam') url+=`category=시험용&exam=${parts[1]}`;
    else if(parts[0]==='lang') url+=`category=시험용&exam=${parts[1]}&lang=${parts[2]}`;
    const r=await fetch(url); _node=await r.json();
    if(view.startsWith('exam:')) renderExamView(parts[1],_node);
    if(view.startsWith('lang:')) renderLangDetailContent(_node,parts);
  }catch(e){}
}

// ── 헤더 / 진행 바 ──────────────────────────────────────
function renderHeader(d){
  const p=d.progress, run=p.status==='running';
  const row=document.getElementById('progress-row');
  row.style.display=run?'flex':'none';
  const rs=document.getElementById('render-status');
  rs.style.display=run?'flex':'none';
  if(run){
    document.getElementById('pr-word').textContent=p.word?p.word+' ('+p.meaning+')':'렌더링 중...';
    document.getElementById('pr-step').textContent=p.step||'';
    document.getElementById('pr-bar').style.width=(p.pct||0)+'%';
    document.getElementById('pr-pct').textContent=(p.pct||0)+'%';
    document.getElementById('rs-text').textContent=p.word||'렌더링 중...';
  }
  const cfg=d.render_config; _desktopEnabled=cfg.desktop_enabled;
  if(!window._targetInitDone){_batchTarget=_desktopEnabled?'desktop':'nas';_customTarget=_desktopEnabled?'desktop':'nas';window._targetInitDone=true;}
  const btn=document.getElementById('toggle-btn');
  if(btn){
    if(_desktopEnabled){btn.textContent='💻 데스크탑';btn.className='btn btn-p';btn.style.fontSize='.72rem';}
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
  const el=document.getElementById('topik-lang-cards');
  if(!el)return;
  const langs=['EN','CN','JP','VN','ES'];
  const col=EXAM_COLORS[exam]||'#818cf8';
  el.innerHTML=langs.map(lang=>`
    <div class="card-sm" style="cursor:pointer;border-color:${col}33;transition:.15s;"
         onmouseover="this.style.borderColor='${col}66'" onmouseout="this.style.borderColor='${col}33'"
         onclick="nav(null,'lang:${exam}:${lang}')">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
        <span style="font-size:1rem;">${LANG_NAMES[lang]||lang}</span>
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

function renderLangDetailContent(stats, parts){
  const [,exam,lang]=parts;
  const col=EXAM_COLORS[exam]||'#818cf8';
  const total=stats.total||1;
  const el=document.getElementById('view-lang:'+exam+':'+lang) || document.getElementById('view-lang:TOPIK:EN');
  if(!el)return;
  const lvRows=[1,2,3,4,5,6].map(lv=>{
    const info=stats.by_level?.[String(lv)]||{total:0,generated:0,uploaded:0,min_id:null,max_id:null};
    const gpct=info.total?Math.round(info.generated/info.total*100):0;
    const idRange=info.min_id!=null?`#${info.min_id}~${info.max_id}`:'–';
    return `<tr>
      <td><span style="color:${LVC[lv]};font-weight:700;">${lv}급</span></td>
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
    <td><span style="color:${LVC[v.level]};font-weight:600;">${v.level}급</span></td>
    <td style="color:var(--muted);font-size:.72rem;">${v.music_file?'🎵 '+v.music_file:'–'}</td>
    <td style="color:var(--amber);font-weight:600;">${v.views?fmt(v.views):'–'}</td>
    <td>${v.video_id?`<a href="https://youtube.com/watch?v=${v.video_id}" target="_blank" style="color:var(--red);font-size:.72rem;">▶</a>`:'–'}</td>
  </tr>`).join('');
  el.innerHTML=`
    <div class="bc">
      <span onclick="nav(document.querySelector('[data-view=overview]'),'overview')">대시보드</span>
      <span style="color:var(--muted2);">›</span>
      <span onclick="nav(document.querySelector('[data-view=exam\\\\:${exam}]'),'exam:${exam}')">TOPIK</span>
      <span style="color:var(--muted2);">›</span>
      <span class="cur">${LANG_NAMES[lang]||lang}</span>
    </div>
    <div class="g3" style="margin-bottom:14px;">
      <div class="card-sm kpi" style="border-color:${col}33;"><div class="num" style="color:${col};">${fmt(stats.total)}</div><div class="label">전체 단어</div></div>
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
function filterVids(){
  if(!_ov)return;
  // video_list는 노드 API에서 가져오므로 로컬 필터
  if(!_node)return;
  const lv=document.getElementById('vf-level').value;
  const mu=document.getElementById('vf-music').value;
  const st=document.getElementById('vf-status').value;
  let list=_node.video_list||[];
  if(lv) list=list.filter(v=>String(v.level)===lv);
  if(mu) list=list.filter(v=>v.music_file===mu);
  if(st==='uploaded') list=list.filter(v=>v.video_id);
  if(st==='generated') list=list.filter(v=>!v.video_id);
  buildVidTable(list);
}

function buildVidTable(list){
  document.getElementById('vf-count').textContent=list.length+'개';
  const t=document.getElementById('vids-tbody');t.innerHTML='';
  list.forEach(v=>{
    const c=LVC[v.level]||'#8b949e';
    const yt=v.video_id?`<a href="https://youtube.com/watch?v=${v.video_id}" target="_blank" style="color:#f87171;">▶</a>`:'–';
    const st=v.video_id?`<span class="badge badge-done">업로드</span>`:`<span class="badge" style="background:#1a1a3a;color:#818cf8;border:1px solid #818cf8;">생성됨</span>`;
    t.innerHTML+=`<tr>
      <td style="color:var(--muted);">${v.day?'#'+v.day:'–'}</td>
      <td style="font-weight:600;">${v.word}</td>
      <td style="color:var(--muted);font-size:.78rem;">${v.meaning}</td>
      <td><span style="color:${c};font-weight:600;">${v.level}급</span></td>
      <td style="font-size:.72rem;color:#a5b4fc;">${v.music_file?'🎵 '+v.music_file:'–'}</td>
      <td style="color:var(--muted);font-size:.72rem;">${fmtSz(v.file_size)}</td>
      <td style="color:var(--muted);font-size:.72rem;">${ago(v.generated_at)}</td>
      <td style="color:#fbbf24;font-weight:600;">${v.views?fmt(v.views):'–'}</td>
      <td>${st} ${yt}</td></tr>`;});
}

// ── YouTube ──────────────────────────────────────────────────
function renderYoutube(d){
  const yt=d.youtube;
  if(!yt){document.getElementById('yt-no-key').style.display='block';document.getElementById('yt-content').style.display='none';return;}
  document.getElementById('yt-no-key').style.display='none';
  document.getElementById('yt-content').style.display='block';
  if(yt.channel){
    setEl('yt-subs',fmt(yt.channel.subscribers));
    setEl('yt-views',fmt(yt.channel.views));
    setEl('yt-vcnt',fmt(yt.channel.video_count));
  }
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

async function _startIllust(start,end,mode){
  const btn=document.getElementById('illust-gen-btn2');
  const cost2=document.getElementById('illust-cost2');
  if(btn){btn.disabled=true;btn.textContent='⏳ 요청 중...';}
  try{
    const r=await fetch('/api/illustrations/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({start,end,mode})});
    const d=await r.json();
    if(!r.ok){
      if(cost2){cost2.textContent='오류: '+(d.error||'알 수 없음');cost2.style.color='#f87171';}
      if(btn){btn.disabled=false;btn.textContent='🎨 생성';}
    } else {
      // 1.5초 후 overview 갱신 (subprocess가 running 상태로 바뀔 시간 확보)
      setTimeout(loadOverview, 1500);
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
    return `<div style="background:var(--bg3);border-radius:8px;padding:8px;text-align:center;">
      <div style="font-size:.7rem;font-weight:600;margin-bottom:4px;">${label}</div>
      <div id="${wrapId}" style="position:relative;">${img}${sub}</div>
      <button id="${btnId}" onclick="regenIllust(${d.word_id},${it.idx},'${notesId}')" class="btn btn-m" style="margin-top:6px;font-size:.65rem;width:100%;padding:3px 0;">🔄 재생성</button>
      <textarea id="${notesId}" placeholder="수정 요청 (예: 카페 말고 마트로, 문 닫힌 모습 강조...)" rows="2" style="width:100%;margin-top:4px;padding:4px 6px;font-size:.62rem;background:var(--bg);color:var(--fg);border:1px solid var(--border);border-radius:5px;resize:vertical;box-sizing:border-box;"></textarea>
    </div>`;
  }).join('');
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

let _livePollTimer=null;

function rpTab(tab){
  _rpTab=tab;
  ['batch','custom','history','live','config'].forEach(t=>{
    const v=document.getElementById('rp-'+t);if(v)v.style.display=t===tab?'block':'none';
    const b=document.getElementById('rp-tab-'+t);
    if(b){b.classList.toggle('on',t===tab);}
  });
  if(_livePollTimer){clearInterval(_livePollTimer);_livePollTimer=null;}
  _stopDailyPoll();
  if(tab==='batch'){_startDailyPoll();}
  if(tab==='custom') updateCustomPreview();
  if(tab==='history'){const dp=document.getElementById('rp-date-pick');if(dp)dp.value=new Date().toISOString().slice(0,10);loadHistoryDate();}
  if(tab==='config') loadConfigSlots();
  if(tab==='live'){loadLiveStatus();_livePollTimer=setInterval(loadLiveStatus,2000);}
}

async function loadLiveStatus(){
  try{
    const r=await fetch('/api/batch/today');
    if(!r.ok) return;
    const d=await r.json();
    const bq=d.queue||{};
    const items=bq.items||[];
    const status=bq.status||'idle';

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
              : '');
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
  if(qEl) qEl.textContent=bq.status==='running'?`배치 진행 중: ${bq.current||0}/${bq.total||0} · ${bq.target==='desktop'?'💻 데스크탑':'🖥 NAS'}`:'';
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
      setEl('rp-batch-prog-step',bq.target==='desktop'?'💻 데스크탑 GPU':'🖥 NAS CPU');
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
    btn.textContent=isRunning?'⏳ 진행 중...':`▶ ${checkedPending>0?'선택':'전체'} 렌더링 (${renderCount}개 · ${_batchTarget==='desktop'?'💻 GPU':'🖥 NAS'})`;
    btn.style.display=isRunning?'none':'block';
  }
  if(cancelBtn){
    cancelBtn.style.display=isRunning?'block':'none';
  }
  // 전체선택 체크 동기화
  const selAll=document.getElementById('rp-select-all');
  if(selAll){
    const pendingIdxs=batch.map((b,i)=>b.status==='pending'&&b.word?i:-1).filter(i=>i>=0);
    selAll.checked=pendingIdxs.length>0&&pendingIdxs.every(i=>_batchChecked.has(i));
    selAll.indeterminate=!selAll.checked&&pendingIdxs.some(i=>_batchChecked.has(i));
  }
  const el=document.getElementById('rp-batch-list');
  if(!batch.length){el.innerHTML='<div style="color:#8b949e;text-align:center;padding:20px;">슬롯이 없습니다. ⚙️ 설정 탭에서 추가하세요.</div>';return;}
  el.innerHTML=batch.map((b,i)=>{
    const w=b.word; const col=EXAM_COLORS[b.exam]||'#818cf8'; const lvC=LVC[b.level]||'#8b949e';
    const canR=b.status==='pending'&&w;
    const isGen=b.status==='generated'&&w;
    const chk=_batchChecked.has(i);
    return `<div class="slot${chk?' hl':''}">
      ${canR?`<input type="checkbox" ${chk?'checked':''} onchange="toggleBatchCheck(${i})" style="accent-color:var(--green);flex-shrink:0;">`
        :`<span style="font-size:.66rem;color:var(--muted2);min-width:14px;">${i+1}</span>`}
      <span style="color:${col};font-size:.68rem;font-weight:700;min-width:40px;">${b.exam}</span>
      <span style="font-size:.78rem;">${_FLAGS[b.lang]||b.lang}</span>
      <span style="color:${lvC};font-size:.7rem;font-weight:700;">${b.level}급</span>
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

async function renderBatchAll(){
  const btn=document.getElementById('rp-render-all');
  btn.disabled=true;btn.textContent='⏳ 요청 중...';
  let started=false;
  try{
    const autoUpload=document.getElementById('rp-auto-upload').checked;
    const batch=(_batchData||{}).batch||[];
    // 체크된 항목만 있으면 그것만, 없으면 전체 pending
    let selectedIds=[];
    if(_batchChecked.size>0){
      selectedIds=batch.filter((b,i)=>_batchChecked.has(i)&&b.status==='pending'&&b.word).map(b=>b.word.id);
    }
    const body={target:_batchTarget,auto_upload:autoUpload};
    if(selectedIds.length>0) body.word_ids=selectedIds;
    const r=await fetch('/api/render/batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const d=await r.json();
    if(!r.ok) alert('오류: '+(d.error||''));
    else{started=true;_batchChecked.clear();setTimeout(loadBatchData,500);}
  }catch(e){alert('실패: '+e);}
  finally{
    // 시작 성공하면 loadBatchData가 버튼 상태를 갱신하므로 여기서 리셋 안 함
    if(!started){btn.disabled=false;btn.textContent='▶ 전체 렌더링';}
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
      if(btnEl){btnEl.textContent='✓';btnEl.style.background='#1a1a3a';btnEl.style.color='#818cf8';btnEl.style.borderColor='#818cf8';}
      setTimeout(loadBatchData,1000);loadOverview();
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
const _EXAM_OPTS=`<option value="TOPIK">🇰🇷 TOPIK</option><option value="TOEIC">📝 TOEIC</option><option value="JLPT">🌸 JLPT</option><option value="IELTS">🎓 IELTS</option><option value="HSK">🐉 HSK</option>`;
const _LEVEL_OPTS=`<option value="1">1급</option><option value="2">2급</option><option value="3">3급</option><option value="4">4급</option><option value="5">5급</option><option value="6">6급</option>`;

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
  return [...document.querySelectorAll('#rc-targets .rc-target-row')].map(row=>({
    exam:row.querySelector('.rc-exam').value,
    level:row.querySelector('.rc-level').value,
    ids_str:(row.querySelector('.rc-ids')||{value:''}).value.trim()
  }));
}

function addTargetRow(){
  const container=document.getElementById('rc-targets');
  const div=document.createElement('div');
  div.className='rc-target-row';
  div.style.cssText='display:flex;gap:6px;align-items:flex-end;margin-bottom:6px;';
  div.innerHTML=`
    <div style="flex:3;"><select class="rc-exam inp" onchange="updateCustomPreview()" style="width:100%;">${_EXAM_OPTS}</select></div>
    <div style="flex:2;"><select class="rc-level inp" onchange="updateCustomPreview()" style="width:100%;">${_LEVEL_OPTS}</select></div>
    <div style="flex:2.5;"><input class="rc-ids inp" placeholder="예: 1, 3~10, 15" oninput="updateCustomPreview()" style="width:100%;"></div>
    <button onclick="removeTargetRow(this)" class="btn btn-m" style="width:28px;padding:5px 0;font-size:.9rem;flex-shrink:0;justify-content:center;" title="삭제">×</button>`;
  container.appendChild(div);
  updateCustomPreview();
}

function removeTargetRow(el){
  const rows=document.querySelectorAll('#rc-targets .rc-target-row');
  if(rows.length<=1)return;
  el.closest('.rc-target-row').remove();
  updateCustomPreview();
}

async function _doCustomPreview(){
  const targets=getTargetRows();
  const langs=getSelectedLangs();
  const {exam,level,ids_str}=targets[0];
  const lang=langs[0]||'EN';
  let url=`/api/render/preview?exam=${exam}&lang=${lang}&level=${level}`;
  if(ids_str) url+=`&ids=${encodeURIComponent(ids_str)}`;
  try{
    const r=await fetch(url);
    const d=await r.json();
    const el=document.getElementById('rc-preview');
    const remEl=document.getElementById('rc-remaining');
    if(remEl) remEl.textContent=`남은 단어: ${d.remaining||0}개`;
    if(!d.words||!d.words.length){
      el.innerHTML='<div style="color:#484f58;text-align:center;padding:16px;font-size:.78rem;">렌더링할 단어가 없습니다</div>';
      document.getElementById('rc-start').disabled=true;
      return;
    }
    document.getElementById('rc-start').disabled=false;
    const lvC={'1':'#3fb950','2':'#58a6ff','3':'#d29922','4':'#f78166','5':'#bc8cff','6':'#f87171'};
    const langBadges=langs.map(l=>`<span style="font-size:.58rem;background:var(--blue)22;color:var(--blue);border-radius:4px;padding:1px 5px;margin-left:2px;">${l}</span>`).join('');
    const extraLabel=targets.length>1?`<span style="font-size:.6rem;color:var(--muted2);margin-left:4px;">+${targets.length-1}개 시험</span>`:'';
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
    const fmts=getSelectedFmts();
    const fmtLabel=fmts.length===2?'본편+릴스':fmts[0]==='youtube'?'본편':'릴스';
    const totalWords=d.words.length*targets.length;
    const total=totalWords*langs.length*fmts.length;
    document.getElementById('rc-start').textContent=`▶ 렌더링 시작 (${d.words.length}개 × ${targets.length}개 시험 × ${langs.length}개 언어 × ${fmtLabel} = ${total}개 · ${_customTarget==='desktop'?'💻 GPU':'🖥 NAS'})`;
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
  const fmtCnt=(getSelectedFmts()||[1]).length||1;
  const total=totalWords*langs.length*fmtCnt*perMin;
  const el=document.getElementById('rc-time-est');
  if(el) el.textContent=`예상 소요: ~${total}분 (${totalWords}개 × ${langs.length}개 언어 × ${fmtCnt}개 포맷 × ${perMin}분)`;
}

async function startCustomRender(){
  const targets=getTargetRows();
  const langs=getSelectedLangs();
  const fmts=getSelectedFmts();
  const renderTarget=_customTarget;
  const targetDesc=targets.map(t=>{
    const ids=parseIds(t.ids_str);
    return `${t.exam} ${t.level}급${ids.length?` [ID: ${t.ids_str}]`:''}`;
  }).join(', ');
  const fmtLabel=fmts.length===2?'본편+릴스':fmts[0]==='youtube'?'본편':'릴스';
  const totalWords=targets.reduce((s,t)=>{const ids=parseIds(t.ids_str);return s+(ids.length||30);},0);
  const msg=`[${targetDesc}]\n언어: [${langs.join(', ')}]\n포맷: ${fmtLabel}\n총 약 ${totalWords*langs.length*fmts.length}개 렌더링\n위치: ${renderTarget==='desktop'?'💻 데스크탑 GPU':'🖥 NAS CPU'}\n\n시작할까요?`;
  if(!confirm(msg)) return;
  const btn=document.getElementById('rc-start');
  btn.disabled=true;btn.textContent='⏳ 요청 중...';
  try{
    const body={targets,langs,formats:fmts,target:renderTarget};
    const r=await fetch('/api/render/custom',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(body)});
    const d=await r.json();
    if(!r.ok) alert('오류: '+(d.error||''));
    else{rpTab('batch');loadOverview();}
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
  el.innerHTML=_configSlots.map((s,i)=>`
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
      <span style="font-size:.7rem;">${_FLAGS[s.lang]||''}</span>
      <button onclick="_configSlots.splice(${i},1);renderConfigSlots()" style="margin-left:auto;background:none;border:none;color:var(--red);cursor:pointer;font-size:.82rem;">✕</button>
    </div>`).join('');
}

function addSlot(){_configSlots.push({exam:'TOPIK',lang:'EN',level:1});renderConfigSlots();}

async function saveSchedule(){
  const r=await fetch('/api/schedule',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({slots:_configSlots})});
  if(r.ok){alert('저장됐습니다!');loadBatchData();}else alert('저장 실패');
}

function resetSchedule(){
  _configSlots=[
    {exam:'TOPIK',lang:'EN',level:1},{exam:'TOPIK',lang:'EN',level:2},{exam:'TOPIK',lang:'EN',level:3},
    {exam:'TOPIK',lang:'JP',level:1},{exam:'TOPIK',lang:'JP',level:2},{exam:'TOPIK',lang:'JP',level:3},
    {exam:'TOPIK',lang:'ES',level:1},{exam:'TOPIK',lang:'ES',level:2},{exam:'TOPIK',lang:'ES',level:3},
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
setInterval(()=>{if(_currentView==='render'&&_rpTab==='batch')loadBatchData();},5000);
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
    renderConvThemes();
    document.getElementById('conv-empty').style.display = _convThemes.length ? 'none' : 'block';
    document.getElementById('conv-themes').style.display = _convThemes.length ? 'grid' : 'none';
  }catch(e){
    document.getElementById('conv-empty').style.display = 'block';
    document.getElementById('conv-themes').style.display = 'none';
  }
}

function renderConvThemes(){
  const el = document.getElementById('conv-themes');
  if(!el) return;
  el.innerHTML = _convThemes.map(t => {
    const ls = t.langs[_convLang] || {};
    const rendered = ls.rendered;
    const uploaded = ls.uploaded;
    const vid = ls.video_id;
    const ko = t.title.ko || t.id;
    const local = t.title[_convLang.toLowerCase()] || ko;
    return `<div class="card" style="border-left:3px solid ${t.color};">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
        <span style="font-size:1.4rem;">${t.emoji}</span>
        <div>
          <div style="font-weight:700;font-size:.9rem;">${ko}</div>
          <div style="font-size:.72rem;color:var(--muted);">${local} · ${t.phrase_count}개 구문</div>
        </div>
      </div>
      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;">
        <span class="badge ${rendered?'badge-g':'badge-m'}">${rendered?'✓ 렌더됨':'○ 미렌더'}</span>
        <span class="badge ${uploaded?'badge-g':'badge-m'}">${uploaded?'✓ 업로드':'○ 미업로드'}</span>
        ${vid?`<a href="https://youtube.com/watch?v=${vid}" target="_blank" class="badge badge-p">▶ YT</a>`:''}
      </div>
      <div style="display:flex;gap:6px;">
        <button class="btn btn-a" onclick="convRender('${t.id}')" style="flex:1;" ${rendered?'title="재렌더링"':''}>
          🎬 ${rendered?'재렌더':'렌더링'}
        </button>
        <button class="btn btn-g" onclick="convUpload('${t.id}')" style="flex:1;" ${!rendered?'disabled title="먼저 렌더링 필요"':''}>
          ⬆ 업로드
        </button>
      </div>
    </div>`;
  }).join('');
}

async function convRender(themeId){
  if(!confirm(`[${_convLang}] "${themeId}" 테마를 렌더링할까요?`)) return;
  try{
    const r = await fetch('/api/conv/render',{method:'POST',headers:{'Content-Type':'application/json'},
      body: JSON.stringify({theme_id:themeId, lang:_convLang})});
    const d = await r.json();
    if(!r.ok) { alert('오류: '+(d.error||'')); return; }
    document.getElementById('conv-progress').style.display = 'block';
  }catch(e){ alert('실패: '+e); }
}

async function convUpload(themeId){
  if(!confirm(`[${_convLang}] "${themeId}" 영상을 YouTube에 업로드할까요?`)) return;
  try{
    const r = await fetch('/api/conv/upload',{method:'POST',headers:{'Content-Type':'application/json'},
      body: JSON.stringify({theme_id:themeId, lang:_convLang})});
    const d = await r.json();
    if(!r.ok) { alert('오류: '+(d.error||'')); return; }
    alert(`업로드 완료!\nhttps://youtube.com/watch?v=${d.video_id}`);
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

function phTab(tab){
  _phTab = tab;
  document.getElementById('ph-panel-illust').style.display = tab==='illust' ? '' : 'none';
  document.getElementById('ph-panel-video').style.display  = tab==='video'  ? '' : 'none';
  document.getElementById('ph-tab-illust').className = 'btn ' + (tab==='illust' ? 'btn-p' : 'btn-m');
  document.getElementById('ph-tab-video').className  = 'btn ' + (tab==='video'  ? 'btn-p' : 'btn-m');
}

async function loadPhraseSituations(){
  try{
    const r = await fetch('/api/phrase/situations');
    const d = await r.json();
    _phSituations = d.situations || [];
    renderPhraseIllustList();
    renderPhraseVideoList();
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
    return `<div class="card" style="border-top:3px solid ${col};">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <div>
          <span style="font-size:.65rem;color:${col};font-weight:700;text-transform:uppercase;">${s.category}</span>
          <div style="font-size:.85rem;font-weight:700;margin-top:2px;">${s.situation}</div>
          <div style="font-size:.7rem;color:var(--muted);">${s.situation_en}</div>
        </div>
        <span style="font-size:.7rem;background:var(--bg3);padding:2px 8px;border-radius:99px;white-space:nowrap;">ID ${s.id}</span>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:.68rem;color:var(--muted);margin-bottom:3px;">
        <span>일러스트</span><span>${s.illust_done}/${s.illust_total}</span>
      </div>
      <div class="pbar-bg" style="height:5px;margin-bottom:10px;">
        <div class="pbar" style="height:5px;width:${pct}%;background:${pct===100?'var(--green)':'var(--amber)'};"></div>
      </div>
      <button class="btn btn-p" style="width:100%;font-size:.75rem;" onclick="startPhraseIllust(${s.id})">
        ${pct===100?'↺ 재생성':'▶ 생성'} (ID ${s.id})
      </button>
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
    return `<div class="card" style="border-top:3px solid ${col};">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <div>
          <span style="font-size:.65rem;color:${col};font-weight:700;text-transform:uppercase;">${s.category}</span>
          <div style="font-size:.85rem;font-weight:700;margin-top:2px;">${s.situation}</div>
          <div style="font-size:.7rem;color:var(--muted);">${s.situation_en}</div>
        </div>
        <span style="font-size:.7rem;background:var(--bg3);padding:2px 8px;border-radius:99px;white-space:nowrap;">ID ${s.id}</span>
      </div>
      ${hasVideo ? `<div style="font-size:.68rem;color:var(--green);margin-bottom:8px;">✓ 영상 있음${genAt?' ('+genAt+')':''}</div>` : ''}
      <div style="display:flex;gap:6px;">
        <button class="btn btn-p" style="flex:1;font-size:.75rem;" onclick="startPhraseVideo(${s.id})">
          ${hasVideo?'↺ 재생성':'▶ 생성'} (ID ${s.id})
        </button>
      </div>
    </div>`;
  }).join('');
}

async function startPhraseIllust(sitId){
  const body = {};
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
    document.getElementById('ph-illust-prog').style.display='';
    pollPhraseIllustProg();
  }catch(e){alert('실패: '+e);}
}

async function cancelPhraseIllust(){
  await fetch('/api/phrase/illust/cancel',{method:'POST'});
  document.getElementById('ph-illust-prog').style.display='none';
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
    document.getElementById('ph-video-prog').style.display='';
    pollPhraseVideoProg();
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
