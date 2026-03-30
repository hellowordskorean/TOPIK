#!/usr/bin/env python3
"""Hellowords 대시보드  —  http://NAS-IP:8765"""
import glob, json, os, subprocess, sys, threading, time
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, jsonify, render_template_string, request

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

DEFAULT_SCHEDULE = {"slots": [
    {"exam":"TOPIK","lang":"EN","level":1},
    {"exam":"TOPIK","lang":"EN","level":2},
    {"exam":"TOPIK","lang":"EN","level":3},
    {"exam":"TOPIK","lang":"JP","level":1},
    {"exam":"TOPIK","lang":"JP","level":2},
    {"exam":"TOPIK","lang":"JP","level":3},
    {"exam":"TOPIK","lang":"SP","level":1},
    {"exam":"TOPIK","lang":"SP","level":2},
    {"exam":"TOPIK","lang":"SP","level":3},
]}

# ─── 전체 콘텐츠 구조 정의 ───────────────────────────────────
STRUCTURE = {
    "시험용": {
        "icon": "📚", "color": "#6366f1",
        "exams": {
            "TOPIK":  {"flag":"🇰🇷","color":"#818cf8","levels":[1,2,3,4,5,6],
                       "langs":["EN","CN","JP","VN","SP"]},
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
        "langs": ["EN","CN","JP","VN","SP","KO","FR","DE"],
    }
}

LANG_META = {
    "EN":{"flag":"🇺🇸","name":"영어"},   "CN":{"flag":"🇨🇳","name":"중국어"},
    "JP":{"flag":"🇯🇵","name":"일본어"},  "VN":{"flag":"🇻🇳","name":"베트남어"},
    "SP":{"flag":"🇪🇸","name":"스페인어"},"KO":{"flag":"🇰🇷","name":"한국어"},
    "FR":{"flag":"🇫🇷","name":"프랑스어"},"DE":{"flag":"🇩🇪","name":"독일어"},
}

# ─── 유틸 ────────────────────────────────────────────────────
def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except: return default

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
    if exam == "TOPIK":
        return f"{LT}/TOPIK/{lang}/topik_{level}.json"
    # 다른 시험: 파일명에서 level 매칭
    exam_dir = f"{LT}/{exam}"
    if os.path.isdir(exam_dir):
        level_str = str(level).lower().replace("-", "_")
        for fname in sorted(os.listdir(exam_dir)):
            if fname.endswith(".json") and not fname.endswith(".bak"):
                if level_str in fname.lower():
                    return f"{exam_dir}/{fname}"
    return f"{LT}/words_db.json"

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

def get_illustration_stats():
    db = get_db()
    stats = {"total": len(db), "word_done": 0, "sent_done": 0, "sent_total": 0, "by_level": {}}
    for w in db:
        lv = str(w.get("level", 1))
        num_sents = len(w.get("sentences", []))
        stats["by_level"].setdefault(lv, {"total": 0, "word_done": 0, "sent_total": 0, "sent_done": 0})
        stats["by_level"][lv]["total"] += 1
        stats["by_level"][lv]["sent_total"] += num_sents
        stats["sent_total"] += num_sents
        if os.path.exists(f"{ILLUST_DIR}/lv{lv}/{w['word']}/word.png"):
            stats["word_done"] += 1
            stats["by_level"][lv]["word_done"] += 1
        for i in range(num_sents):
            if os.path.exists(f"{ILLUST_DIR}/lv{lv}/{w['word']}/{i}.png"):
                stats["sent_done"] += 1
                stats["by_level"][lv]["sent_done"] += 1
    stats["progress"] = load_json(ILLUST_PROG_F, {"status": "idle", "pct": 0})
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
    by_level = defaultdict(lambda:{"total":0,"generated":0,"uploaded":0})
    gen_ids = {v["word_id"] for v in gen}
    upl_ids = {u["word_id"] for u in upl}
    for w in db:
        lv = str(w.get("level","?"))
        by_level[lv]["total"] += 1
        if w["id"] in gen_ids: by_level[lv]["generated"] += 1
        if w["id"] in upl_ids: by_level[lv]["uploaded"] += 1

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
    db = get_db("시험용", exam, lang)
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

def get_level_id_range(exam, lang, level):
    """해당 등급의 ID 범위 반환 (min_id, max_id, total)"""
    db = get_db("시험용", exam, lang)
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
    rendered = {v["word_id"] for v in videos
                if v.get("exam", "TOPIK") == exam and v.get("language", "EN") == lang}
    for w in sorted(db, key=lambda x: x["id"]):
        if w.get("level") == level and w["id"] not in rendered:
            return w
    return None

def get_batch_today():
    slots  = get_schedule().get("slots", [])
    videos = get_videos_log()
    uploaded, _ = get_uploads()
    upl_ids = {u["word_id"] for u in uploaded}
    vid_ids = {v["word_id"] for v in videos}
    seen_words: set = set()          # 같은 단어 중복 방지
    batch = []
    for i, slot in enumerate(slots):
        exam  = slot.get("exam", "TOPIK")
        lang  = slot.get("lang", "EN")
        level = slot.get("level", 1)
        word  = get_next_word_for_slot(exam, lang, level)
        # 이미 다른 슬롯에서 선택된 단어면 다음으로
        if word and word["id"] in seen_words:
            db    = get_db("시험용", exam, lang)
            vids  = {v["word_id"] for v in videos if v.get("exam") == exam and v.get("language") == lang}
            for w in sorted(db, key=lambda x: x["id"]):
                if w.get("level") == level and w["id"] not in vids and w["id"] not in seen_words:
                    word = w; break
            else:
                word = None
        if word:
            seen_words.add(word["id"])
        status = ("uploaded" if word and word["id"] in upl_ids
                  else "generated" if word and word["id"] in vid_ids
                  else "pending"   if word
                  else "no_word")
        batch.append({"slot": i, "exam": exam, "lang": lang, "level": level,
                      "word": word, "status": status})
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
def write_queue_job(word_id, db_path=None):
    if not db_path:
        db_path = "/app/data/LanguageTest/words_db.json"
    save_json(QUEUE_FILE,{"word_id":word_id,"db_path":db_path,
        "status":"pending","claimed_by":None,"claimed_at":None,
        "created_at":datetime.now().isoformat(),"completed_at":None})

_render_thread = None
_illust_thread = None
_batch_thread  = None

def run_batch_render(word_ids, target="auto", db_path=None):
    """target: "desktop", "nas", "auto"(글로벌 토글 따름)"""
    global _batch_thread
    for i, word_id in enumerate(word_ids):
        try:
            bq = load_json(BATCH_QUEUE_F, {})
            bq["current"] = i
            for item in bq.get("items", []):
                if item["word_id"] == word_id:
                    item["status"] = "rendering"
            save_json(BATCH_QUEUE_F, bq)

            write_queue_job(word_id, db_path)
            cfg = get_render_config()
            use_desktop = (target == "desktop") if target != "auto" else cfg.get("desktop_enabled")

            if use_desktop:
                deadline = time.time() + 30 * 60
                finished = False
                while time.time() < deadline:
                    time.sleep(15)
                    rq = load_json(QUEUE_FILE, {})
                    if rq.get("status") in ("done", "failed"):
                        finished = True; break
                if not finished:
                    run_render_nas(word_id, db_path)
            else:
                run_render_nas(word_id, db_path)
        except Exception:
            pass

        bq = load_json(BATCH_QUEUE_F, {})
        for item in bq.get("items", []):
            if item["word_id"] == word_id:
                item["status"] = "done"
        bq["current"] = i + 1
        save_json(BATCH_QUEUE_F, bq)

    bq = load_json(BATCH_QUEUE_F, {})
    bq["status"] = "done"
    bq["completed_at"] = datetime.now().isoformat()
    save_json(BATCH_QUEUE_F, bq)

def run_render_nas(word_id, db_path=None):
    if not db_path:
        db_path = "/app/data/LanguageTest/words_db.json"
    try:
        q = load_json(QUEUE_FILE,{})
        q.update({"status":"claimed","claimed_by":"nas","claimed_at":datetime.now().isoformat()})
        save_json(QUEUE_FILE,q)
        r = subprocess.run([sys.executable,"/app/make_video.py",
            "--db",db_path,
            "--id",str(word_id),"--output","/app/output/"])
        q = load_json(QUEUE_FILE,{})
        q.update({"status":"done" if r.returncode==0 else "failed","completed_at":datetime.now().isoformat()})
        save_json(QUEUE_FILE,q)
    except Exception as e:
        save_json(QUEUE_FILE,{**load_json(QUEUE_FILE,{}),"status":"failed","error":str(e)})

def run_illustration_generation(start, end, mode="both"):
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
        r = subprocess.run(cmd)
        final = load_json(ILLUST_PROG_F, {})
        if final.get("status") == "running":
            save_json(ILLUST_PROG_F, {**final,
                "status":"done" if r.returncode==0 else "failed",
                "pct":100,"completed_at":datetime.now().isoformat()})
    except Exception as e:
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
    upl_map = {u["word_id"]:u for u in uploaded}
    vid_map = {v["word_id"]:v for v in videos}
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
    if not word_id: return jsonify({"error":"렌더링할 단어가 없습니다"}),400
    q = load_json(QUEUE_FILE,{})
    if q.get("status") in ("pending","claimed"):
        return jsonify({"error":"이미 렌더링 중입니다","queue":q}),409
    write_queue_job(word_id)
    cfg = get_render_config()
    use_desktop = (target == "desktop") if target != "auto" else cfg.get("desktop_enabled")
    if use_desktop:
        return jsonify({"status":"queued","host":"desktop","word_id":word_id})
    _render_thread = threading.Thread(target=run_render_nas,args=(word_id,),daemon=True)
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
    word_ids = data.get("word_ids", [])
    target   = data.get("target", "auto")   # "desktop", "nas", "auto"
    if not word_ids:
        batch    = get_batch_today()
        word_ids = [b["word"]["id"] for b in batch if b.get("word") and b.get("status") == "pending"]
    if not word_ids:
        return jsonify({"error": "렌더링할 단어가 없습니다"}), 400
    bq = load_json(BATCH_QUEUE_F, {})
    if bq.get("status") == "running":
        return jsonify({"error": "이미 배치 렌더링 중"}), 409
    items = [{"word_id": wid, "status": "pending"} for wid in word_ids]
    save_json(BATCH_QUEUE_F, {"status":"running","total":len(items),"current":0,
        "items":items,"target":target,"started_at":datetime.now().isoformat()})
    _batch_thread = threading.Thread(target=run_batch_render, args=(word_ids,target), daemon=True)
    _batch_thread.start()
    return jsonify({"status": "started", "count": len(word_ids), "target": target})

@app.route("/api/render/preview")
def api_render_preview():
    """커스텀 렌더링 미리보기 — ID 범위 지원"""
    exam     = request.args.get("exam", "TOPIK")
    lang     = request.args.get("lang", "EN")
    level    = int(request.args.get("level", 1))
    count    = int(request.args.get("count", 30))
    start_id = request.args.get("start_id", type=int)
    end_id   = request.args.get("end_id", type=int)
    words = get_next_words_for_custom(exam, lang, level, min(count, 30), start_id, end_id)
    # 남은 수 계산
    db = get_db("시험용", exam, lang)
    videos = get_videos_log()
    rendered = {v["word_id"] for v in videos
                if v.get("exam", "TOPIK") == exam and v.get("language", "EN") == lang}
    remaining = sum(1 for w in db if w.get("level") == level and w["id"] not in rendered)
    # 등급 ID 범위
    min_id, max_id, total = get_level_id_range(exam, lang, level)
    return jsonify({"words": words, "count": len(words), "remaining": remaining,
                    "level_min_id": min_id, "level_max_id": max_id, "level_total": total})

@app.route("/api/render/custom", methods=["POST"])
def api_render_custom():
    """커스텀 렌더링 — 시험/언어/등급/ID범위/위치 지정"""
    global _batch_thread
    data     = request.get_json(silent=True) or {}
    exam     = data.get("exam", "TOPIK")
    lang     = data.get("lang", "EN")
    level    = int(data.get("level", 1))
    count    = int(data.get("count", 30))
    start_id = data.get("start_id")
    end_id   = data.get("end_id")
    target   = data.get("target", "auto")
    words  = get_next_words_for_custom(exam, lang, level, min(count, 30), start_id, end_id)
    if not words:
        return jsonify({"error": "렌더링할 단어가 없습니다"}), 400
    bq = load_json(BATCH_QUEUE_F, {})
    if bq.get("status") == "running":
        return jsonify({"error": "이미 렌더링 중"}), 409
    db_path = render_db_path_for(exam, lang, level)
    word_ids = [w["id"] for w in words]
    items = [{"word_id": wid, "status": "pending"} for wid in word_ids]
    save_json(BATCH_QUEUE_F, {"status":"running","total":len(items),"current":0,
        "items":items,"target":target,"exam":exam,"lang":lang,"level":level,
        "started_at":datetime.now().isoformat()})
    _batch_thread = threading.Thread(target=run_batch_render, args=(word_ids,target,db_path), daemon=True)
    _batch_thread.start()
    return jsonify({"status":"started","count":len(word_ids),"target":target,
                    "words":[{"id":w["id"],"word":w["word"]} for w in words]})

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

# ─── HTML ─────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hellowords</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
:root{
  --bg:#0d1117;--sidebar:#0d1117;--card:#161b22;--border:#21262d;
  --border2:#30363d;--text:#e6edf3;--muted:#8b949e;--muted2:#484f58;
}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;display:flex;flex-direction:column;height:100vh;overflow:hidden;}
/* HEADER */
#header{background:#161b22;border-bottom:1px solid var(--border);padding:0 20px;height:52px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;z-index:100;}
/* BODY */
#body{display:flex;flex:1;overflow:hidden;}
/* SIDEBAR */
#sidebar{width:220px;background:var(--sidebar);border-right:1px solid var(--border);overflow-y:auto;flex-shrink:0;padding:8px 0;}
#sidebar::-webkit-scrollbar{width:4px;}
#sidebar::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px;}
.s-section{padding:6px 12px 2px;font-size:.65rem;color:var(--muted2);text-transform:uppercase;letter-spacing:.08em;margin-top:8px;}
.s-item{display:flex;align-items:center;gap:8px;padding:6px 16px;cursor:pointer;font-size:.82rem;color:var(--muted);border-left:2px solid transparent;transition:.15s;user-select:none;}
.s-item:hover{background:#161b22;color:var(--text);}
.s-item.active{background:#161b22;color:var(--text);border-left-color:var(--accent-color,#6366f1);}
.s-item.level2{padding-left:28px;font-size:.79rem;}
.s-item.level3{padding-left:42px;font-size:.76rem;}
.s-badge{font-size:.6rem;padding:1px 6px;border-radius:10px;margin-left:auto;font-weight:600;}
.s-arrow{margin-left:auto;font-size:.65rem;transition:.2s;color:var(--muted2);}
.s-children{display:none;}
.s-children.open{display:block;}
/* MAIN */
#main{flex:1;overflow-y:auto;padding:20px 24px;}
#main::-webkit-scrollbar{width:6px;}
#main::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px;}
/* CARDS */
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:18px;}
.card-sm{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px;}
/* PROGRESS */
.pbar-bg{background:#21262d;border-radius:6px;overflow:hidden;}
.pbar{border-radius:6px;transition:width .4s ease;}
/* TABLE */
table{width:100%;border-collapse:collapse;}
th{color:var(--muted);font-size:.68rem;text-transform:uppercase;padding:8px 12px;border-bottom:1px solid var(--border);text-align:left;font-weight:500;}
td{padding:8px 12px;border-bottom:1px solid var(--border);font-size:.82rem;}
tr:hover td{background:#1c2128;}
/* BADGES */
.badge{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:20px;font-size:.68rem;font-weight:600;}
.badge-run{background:#0d2b0d;color:#3fb950;border:1px solid #3fb950;}
.badge-idle{background:#1c2128;color:var(--muted);border:1px solid var(--border2);}
.badge-done{background:#0d2b0d;color:#3fb950;border:1px solid #3fb950;}
.badge-soon{background:#1c1c2e;color:#6366f1;border:1px solid #6366f1;}
/* CONTROLS */
.ctrl-btn{padding:5px 14px;border-radius:7px;font-size:.78rem;font-weight:600;cursor:pointer;border:1px solid;transition:.15s;}
.ctrl-btn:hover{filter:brightness(1.2);}
/* BREADCRUMB */
#breadcrumb{font-size:.78rem;color:var(--muted);margin-bottom:18px;display:flex;align-items:center;gap:6px;}
#breadcrumb span{cursor:pointer;color:var(--muted);}
#breadcrumb span:hover{color:var(--text);}
#breadcrumb span.active{color:var(--text);font-weight:600;}
/* INPUT */
.num-input{background:#21262d;border:1px solid var(--border2);border-radius:6px;color:var(--text);padding:4px 8px;font-size:.8rem;width:70px;}
/* STAT NUM */
.stat-n{font-size:1.8rem;font-weight:700;line-height:1;}
/* GRID */
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;}
.grid-4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.grid-6{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;}
/* SECTION TITLE */
.sec-title{font-size:.78rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.07em;margin-bottom:12px;}
/* PULSE */
.pulse{animation:pulse 1.8s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
/* LANG CARD */
.lang-card{background:#1c2128;border:1px solid var(--border);border-radius:10px;padding:12px;cursor:pointer;transition:.15s;}
.lang-card:hover{border-color:var(--border2);background:#21262d;}
.lang-card.available{border-color:var(--card-color,var(--border));}
/* CHIP */
.chip{display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:20px;font-size:.72rem;background:#21262d;border:1px solid var(--border2);}
</style>
</head>
<body>

<!-- ══ HEADER ══════════════════════════════════════════════ -->
<div id="header">
  <div style="display:flex;align-items:center;gap:12px;">
    <span style="font-size:1.3rem;">🌍</span>
    <div>
      <div style="font-weight:700;font-size:.95rem;letter-spacing:-.01em;">Hellowords</div>
      <div id="breadcrumb-mini" style="font-size:.65rem;color:var(--muted);">Dashboard</div>
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:10px;">
    <!-- 렌더링 토글 -->
    <div style="display:flex;align-items:center;gap:6px;background:#21262d;border:1px solid var(--border2);border-radius:8px;padding:5px 10px;">
      <span style="font-size:.7rem;color:var(--muted);">렌더링</span>
      <button id="toggle-btn" onclick="toggleRender()" class="ctrl-btn" style="padding:3px 10px;font-size:.72rem;"></button>
      <span id="queue-badge" style="font-size:.68rem;color:var(--muted);"></span>
    </div>
    <!-- 지금 렌더링 -->
    <button id="render-now-btn" onclick="toggleRenderPanel()" class="ctrl-btn"
      style="background:#0d2b0d;color:#3fb950;border-color:#3fb950;">▶ 지금 렌더링</button>
    <!-- 클럭 -->
    <div style="text-align:right;min-width:130px;">
      <div id="clock" style="font-size:.8rem;color:var(--muted);font-variant-numeric:tabular-nums;"></div>
      <div id="last-upd" style="font-size:.62rem;color:var(--muted2);"></div>
    </div>
  </div>
</div>

<!-- 현재 작업 바 (렌더링 중일 때만 표시) -->
<div id="progress-row" style="display:none;background:#161b22;border-bottom:1px solid var(--border);padding:8px 20px;display:flex;align-items:center;gap:12px;flex-shrink:0;">
  <span id="pr-word" style="font-weight:700;color:#818cf8;font-size:.9rem;min-width:120px;"></span>
  <span id="pr-step" style="font-size:.75rem;color:var(--muted);flex:0 0 200px;"></span>
  <div class="pbar-bg" style="flex:1;height:6px;">
    <div id="pr-bar" class="pbar" style="width:0%;height:6px;background:linear-gradient(90deg,#6366f1,#a855f7);"></div>
  </div>
  <span id="pr-pct" style="font-size:.75rem;color:var(--muted);min-width:32px;text-align:right;"></span>
</div>

<!-- ══ BODY ════════════════════════════════════════════════ -->
<div id="body">

<!-- ── SIDEBAR ── -->
<div id="sidebar">
  <div class="s-item active" data-view="overview" onclick="nav(this,'overview')" style="--accent-color:#6366f1;">
    <span>📊</span><span>전체 개요</span>
  </div>

  <div class="s-section">시험용</div>
  <div class="s-item" data-view="cat:시험용" onclick="nav(this,'cat:시험용')" style="--accent-color:#6366f1;">
    <span>📚</span><span>시험 전체</span>
  </div>
  <!-- TOPIK -->
  <div class="s-item level2" data-view="exam:TOPIK" onclick="toggleExam(this,'exam:TOPIK')" style="--accent-color:#818cf8;">
    <span>🇰🇷</span><span>TOPIK</span><span class="s-arrow" id="arr-TOPIK">▶</span>
  </div>
  <div class="s-children" id="ch-TOPIK">
    <div class="s-item level3" data-view="lang:TOPIK:EN" onclick="nav(this,'lang:TOPIK:EN')" style="--accent-color:#818cf8;">🇺🇸 영어 (EN)</div>
    <div class="s-item level3" data-view="lang:TOPIK:CN" onclick="nav(this,'lang:TOPIK:CN')" style="--accent-color:#818cf8;">🇨🇳 중국어 (CN)</div>
    <div class="s-item level3" data-view="lang:TOPIK:JP" onclick="nav(this,'lang:TOPIK:JP')" style="--accent-color:#818cf8;">🇯🇵 일본어 (JP)</div>
    <div class="s-item level3" data-view="lang:TOPIK:VN" onclick="nav(this,'lang:TOPIK:VN')" style="--accent-color:#818cf8;">🇻🇳 베트남어 (VN)</div>
    <div class="s-item level3" data-view="lang:TOPIK:SP" onclick="nav(this,'lang:TOPIK:SP')" style="--accent-color:#818cf8;">🇪🇸 스페인어 (SP)</div>
  </div>
  <!-- TOEIC -->
  <div class="s-item level2" data-view="exam:TOEIC" onclick="toggleExam(this,'exam:TOEIC')" style="--accent-color:#60a5fa;">
    <span>📝</span><span>TOEIC</span><span class="s-arrow" id="arr-TOEIC">▶</span>
  </div>
  <div class="s-children" id="ch-TOEIC">
    <div class="s-item level3" style="color:var(--muted2);cursor:default;">🚧 준비 중</div>
  </div>
  <!-- JLPT -->
  <div class="s-item level2" data-view="exam:JLPT" onclick="toggleExam(this,'exam:JLPT')" style="--accent-color:#f472b6;">
    <span>🌸</span><span>JLPT</span><span class="s-arrow" id="arr-JLPT">▶</span>
  </div>
  <div class="s-children" id="ch-JLPT">
    <div class="s-item level3" style="color:var(--muted2);cursor:default;">🚧 준비 중</div>
  </div>
  <!-- IELTS -->
  <div class="s-item level2" data-view="exam:IELTS" onclick="toggleExam(this,'exam:IELTS')" style="--accent-color:#a78bfa;">
    <span>🎓</span><span>IELTS</span><span class="s-arrow" id="arr-IELTS">▶</span>
  </div>
  <div class="s-children" id="ch-IELTS">
    <div class="s-item level3" style="color:var(--muted2);cursor:default;">🚧 준비 중</div>
  </div>
  <!-- HSK -->
  <div class="s-item level2" data-view="exam:HSK" onclick="toggleExam(this,'exam:HSK')" style="--accent-color:#f87171;">
    <span>🐉</span><span>HSK</span><span class="s-arrow" id="arr-HSK">▶</span>
  </div>
  <div class="s-children" id="ch-HSK">
    <div class="s-item level3" style="color:var(--muted2);cursor:default;">🚧 준비 중</div>
  </div>

  <div class="s-section">여행용</div>
  <div class="s-item" data-view="cat:여행용" onclick="nav(this,'cat:여행용')" style="--accent-color:#10b981;">
    <span>✈️</span><span>여행 전체</span>
  </div>
  <div class="s-item level2" style="color:var(--muted2);cursor:default;font-size:.75rem;padding:4px 28px;">🚧 준비 중</div>

  <div class="s-section">관리</div>
  <div class="s-item" data-view="videos" onclick="nav(this,'videos')" style="--accent-color:#22d3ee;">
    <span>🎬</span><span>영상 목록</span>
  </div>
  <div class="s-item" data-view="illustrations" onclick="nav(this,'illustrations')" style="--accent-color:#f59e0b;">
    <span>🎨</span><span>일러스트</span>
  </div>
  <div class="s-item" data-view="youtube" onclick="nav(this,'youtube')" style="--accent-color:#f87171;">
    <span>▶</span><span>YouTube</span>
  </div>
</div>

<!-- ── MAIN ── -->
<div id="main">

<!-- == 전체 개요 == -->
<div id="view-overview" class="view">
  <div id="breadcrumb" class="breadcrumb-bar">
    <span class="active">📊 전체 개요</span>
  </div>
  <div class="grid-4" style="margin-bottom:16px;">
    <div class="card-sm" style="text-align:center;">
      <div id="ov-total" class="stat-n" style="color:var(--muted);">–</div>
      <div style="font-size:.72rem;color:var(--muted);margin-top:4px;">전체 단어</div>
    </div>
    <div class="card-sm" style="text-align:center;">
      <div id="ov-gen" class="stat-n" style="color:#818cf8;">–</div>
      <div style="font-size:.72rem;color:var(--muted);margin-top:4px;">영상 생성</div>
      <div class="pbar-bg" style="height:4px;margin-top:6px;"><div id="ov-gen-bar" class="pbar" style="height:4px;background:#818cf8;width:0%;"></div></div>
    </div>
    <div class="card-sm" style="text-align:center;">
      <div id="ov-upl" class="stat-n" style="color:#3fb950;">–</div>
      <div style="font-size:.72rem;color:var(--muted);margin-top:4px;">업로드 완료</div>
      <div class="pbar-bg" style="height:4px;margin-top:6px;"><div id="ov-upl-bar" class="pbar" style="height:4px;background:#3fb950;width:0%;"></div></div>
    </div>
    <div class="card-sm" style="text-align:center;">
      <div id="ov-remain" class="stat-n" style="color:#f0883e;">–</div>
      <div style="font-size:.72rem;color:var(--muted);margin-top:4px;">남은 영상</div>
    </div>
  </div>
  <div class="grid-2" style="margin-bottom:16px;">
    <div class="card">
      <div class="sec-title">콘텐츠 카테고리</div>
      <div style="display:flex;flex-direction:column;gap:10px;">
        <div onclick="nav(document.querySelector('[data-view=cat\\:시험용]'),'cat:시험용')" style="cursor:pointer;background:#1c2128;border-radius:8px;padding:12px;border-left:3px solid #6366f1;display:flex;align-items:center;justify-content:space-between;">
          <div style="display:flex;align-items:center;gap:8px;"><span>📚</span><span style="font-weight:600;">시험용</span></div>
          <div style="font-size:.75rem;color:var(--muted);">TOPIK · TOEIC · JLPT · IELTS · HSK</div>
        </div>
        <div onclick="nav(document.querySelector('[data-view=cat\\:여행용]'),'cat:여행용')" style="cursor:pointer;background:#1c2128;border-radius:8px;padding:12px;border-left:3px solid #10b981;display:flex;align-items:center;justify-content:space-between;">
          <div style="display:flex;align-items:center;gap:8px;"><span>✈️</span><span style="font-weight:600;">여행용</span></div>
          <div style="font-size:.75rem;color:var(--muted);">EN · CN · JP · VN · SP ···</div>
        </div>
      </div>
    </div>
    <div class="card">
      <div class="sec-title">업로드 타임라인 (30일)</div>
      <canvas id="chart-timeline" height="120"></canvas>
    </div>
  </div>
  <div class="grid-2">
    <!-- 일러스트 현황 -->
    <div class="card">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
        <div class="sec-title" style="margin:0;">🎨 일러스트 현황</div>
        <span id="ov-illust-badge" class="badge badge-idle"></span>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:.72rem;color:var(--muted);margin-bottom:3px;">
        <span>🖼 단어</span><span id="ov-illust-word-txt">–</span><span id="ov-illust-word-pct" style="margin-left:auto;padding-left:8px;">0%</span>
      </div>
      <div class="pbar-bg" style="height:5px;margin-bottom:8px;">
        <div id="ov-illust-word-bar" class="pbar" style="height:5px;width:0%;background:linear-gradient(90deg,#f59e0b,#f97316);"></div>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:.72rem;color:var(--muted);margin-bottom:3px;">
        <span>📝 예문</span><span id="ov-illust-sent-txt">–</span><span id="ov-illust-sent-pct" style="margin-left:auto;padding-left:8px;">0%</span>
      </div>
      <div class="pbar-bg" style="height:5px;margin-bottom:12px;">
        <div id="ov-illust-sent-bar" class="pbar" style="height:5px;width:0%;background:linear-gradient(90deg,#818cf8,#a855f7);"></div>
      </div>
      <div class="grid-6" id="ov-illust-levels"></div>
      <div id="ov-illust-log" style="display:none;background:#0d1117;border-radius:6px;padding:8px;font-size:.68rem;color:var(--muted);font-family:monospace;max-height:60px;overflow:auto;margin-top:10px;"></div>
      <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:12px;">
        <span style="font-size:.72rem;color:var(--muted);">ID</span>
        <input id="illust-start" class="num-input" type="number" value="1" min="1" max="1800">
        <span style="color:var(--muted);font-size:.8rem;">~</span>
        <input id="illust-end" class="num-input" type="number" value="10" min="1" max="1800">
        <select id="illust-mode" onchange="updateIllustCost()" style="background:#21262d;color:var(--text);border:1px solid var(--border2);border-radius:6px;padding:4px 8px;font-size:.75rem;">
          <option value="both">단어+예문</option>
          <option value="words">🖼 단어만</option>
          <option value="sentences">📝 예문만</option>
        </select>
        <button id="illust-gen-btn" onclick="startIllustGen()" class="ctrl-btn" style="background:#2d1f00;color:#f59e0b;border-color:#f59e0b;">🎨 생성</button>
        <button onclick="setIllustRange(1,1800)" class="ctrl-btn" style="background:transparent;color:var(--muted);border-color:var(--border2);">전체</button>
        <span id="illust-cost" style="font-size:.7rem;color:var(--muted);"></span>
      </div>
    </div>
    <!-- 음악 -->
    <div class="card">
      <div class="sec-title">🎵 배경 음악 풀</div>
      <div id="ov-music" style="display:flex;flex-wrap:wrap;gap:6px;"></div>
    </div>
  </div>
</div>

<!-- == 시험 카테고리 == -->
<div id="view-cat:시험용" class="view" style="display:none;">
  <div class="breadcrumb-bar"><span onclick="nav(document.querySelector('[data-view=overview]'),'overview')">📊 개요</span><span style="color:var(--muted2);">›</span><span class="active">📚 시험용</span></div>
  <div class="sec-title">시험 종류</div>
  <div class="grid-3" id="exam-cards-view"></div>
</div>

<!-- == 여행 카테고리 == -->
<div id="view-cat:여행용" class="view" style="display:none;">
  <div class="breadcrumb-bar"><span onclick="nav(document.querySelector('[data-view=overview]'),'overview')">📊 개요</span><span style="color:var(--muted2);">›</span><span class="active">✈️ 여행용</span></div>
  <div class="card" style="text-align:center;padding:40px;">
    <div style="font-size:2.5rem;margin-bottom:12px;">✈️</div>
    <div style="font-weight:700;font-size:1.1rem;margin-bottom:8px;">여행용 콘텐츠</div>
    <div style="color:var(--muted);font-size:.85rem;">EN · CN · JP · VN · SP · KO · FR · DE</div>
    <div class="badge badge-soon" style="margin:16px auto;display:inline-flex;">🚧 준비 중</div>
  </div>
</div>

<!-- == 시험별 뷰 (TOPIK/TOEIC/...) == -->
<div id="view-exam:TOPIK" class="view" style="display:none;">
  <div class="breadcrumb-bar">
    <span onclick="nav(document.querySelector('[data-view=overview]'),'overview')">📊 개요</span>
    <span style="color:var(--muted2);">›</span>
    <span onclick="nav(document.querySelector('[data-view=cat\\:시험용]'),'cat:시험용')">📚 시험용</span>
    <span style="color:var(--muted2);">›</span>
    <span class="active">🇰🇷 TOPIK</span>
  </div>
  <div class="sec-title" style="color:#818cf8;">학습 언어별 현황</div>
  <div id="topik-lang-cards" class="grid-3" style="margin-bottom:16px;"></div>
</div>

<!-- == 언어별 상세 뷰 == -->
<div id="view-lang:TOPIK:EN" class="view" style="display:none;">
  <div class="breadcrumb-bar">
    <span onclick="nav(document.querySelector('[data-view=overview]'),'overview')">📊 개요</span>
    <span style="color:var(--muted2);">›</span>
    <span onclick="nav(document.querySelector('[data-view=cat\\:시험용]'),'cat:시험용')">📚 시험용</span>
    <span style="color:var(--muted2);">›</span>
    <span onclick="nav(document.querySelector('[data-view=exam\\:TOPIK]'),'exam:TOPIK')">🇰🇷 TOPIK</span>
    <span style="color:var(--muted2);">›</span>
    <span class="active">🇺🇸 영어 (EN)</span>
  </div>
  <div id="lang-detail-content"></div>
</div>

<!-- 나머지 언어들은 JS로 동적 생성 -->

<!-- == 영상 목록 == -->
<div id="view-videos" class="view" style="display:none;">
  <div class="breadcrumb-bar"><span class="active">🎬 영상 목록</span></div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px;align-items:center;">
    <select id="vf-level" onchange="filterVids()" style="background:#21262d;color:var(--text);border:1px solid var(--border2);border-radius:6px;padding:5px 8px;font-size:.78rem;">
      <option value="">전체 등급</option>
      <option>1</option><option>2</option><option>3</option>
      <option>4</option><option>5</option><option>6</option>
    </select>
    <select id="vf-music" onchange="filterVids()" style="background:#21262d;color:var(--text);border:1px solid var(--border2);border-radius:6px;padding:5px 8px;font-size:.78rem;">
      <option value="">전체 음악</option>
    </select>
    <select id="vf-status" onchange="filterVids()" style="background:#21262d;color:var(--text);border:1px solid var(--border2);border-radius:6px;padding:5px 8px;font-size:.78rem;">
      <option value="">전체 상태</option>
      <option value="uploaded">업로드됨</option>
      <option value="generated">생성만</option>
    </select>
    <span id="vf-count" style="font-size:.75rem;color:var(--muted);margin-left:auto;"></span>
  </div>
  <div style="overflow-x:auto;">
    <table>
      <thead><tr><th>Day</th><th>단어</th><th>뜻</th><th>등급</th><th>음악</th><th>크기</th><th>생성</th><th>조회수</th><th>상태</th></tr></thead>
      <tbody id="vids-tbody"></tbody>
    </table>
  </div>
</div>

<!-- == 일러스트 == -->
<div id="view-illustrations" class="view" style="display:none;">
  <div class="breadcrumb-bar"><span class="active">🎨 일러스트 관리</span></div>
  <div class="card">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
      <div style="font-weight:600;">일러스트 생성 현황</div>
      <span id="illust-view-badge" class="badge badge-idle"></span>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:.75rem;color:var(--muted);margin-bottom:3px;">
      <span>🖼 단어 일러스트</span><span id="illust-view-word-txt">–</span><span id="illust-view-word-pct" style="margin-left:auto;padding-left:8px;">0%</span>
    </div>
    <div class="pbar-bg" style="height:7px;margin-bottom:8px;">
      <div id="illust-view-word-bar" class="pbar" style="height:7px;width:0%;background:linear-gradient(90deg,#f59e0b,#f97316);"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:.75rem;color:var(--muted);margin-bottom:3px;">
      <span>📝 예문 일러스트</span><span id="illust-view-sent-txt">–</span><span id="illust-view-sent-pct" style="margin-left:auto;padding-left:8px;">0%</span>
    </div>
    <div class="pbar-bg" style="height:7px;margin-bottom:16px;">
      <div id="illust-view-sent-bar" class="pbar" style="height:7px;width:0%;background:linear-gradient(90deg,#818cf8,#a855f7);"></div>
    </div>
    <div class="grid-6" id="illust-view-levels" style="margin-bottom:16px;"></div>
    <div id="illust-view-log" style="display:none;background:#0d1117;border-radius:8px;padding:12px;font-size:.72rem;color:var(--muted);font-family:monospace;max-height:100px;overflow:auto;margin-bottom:16px;white-space:pre-wrap;"></div>
    <div style="background:#21262d;border-radius:8px;padding:14px;">
      <div style="font-size:.78rem;font-weight:600;margin-bottom:10px;">일러스트 생성</div>
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
        <span style="font-size:.78rem;color:var(--muted);">단어 ID 범위:</span>
        <input id="illust-start2" class="num-input" type="number" value="1"><span style="color:var(--muted);">~</span>
        <input id="illust-end2" class="num-input" type="number" value="100">
        <select id="illust-mode2" onchange="updateIllustCost2()" style="background:#21262d;color:var(--text);border:1px solid var(--border2);border-radius:6px;padding:4px 8px;font-size:.75rem;">
          <option value="both">단어+예문</option>
          <option value="words">🖼 단어만</option>
          <option value="sentences">📝 예문만</option>
        </select>
        <button id="illust-gen-btn2" onclick="startIllustGen2()" class="ctrl-btn" style="background:#2d1f00;color:#f59e0b;border-color:#f59e0b;">🎨 일러스트 생성</button>
        <button onclick="setIllustRange2(1,1800)" class="ctrl-btn" style="background:transparent;color:var(--muted);border-color:var(--border2);">전체 (1800장)</button>
        <span id="illust-cost2" style="font-size:.75rem;color:#f59e0b;font-weight:600;"></span>
      </div>
    </div>
  </div>
</div>

<!-- == YouTube == -->
<div id="view-youtube" class="view" style="display:none;">
  <div class="breadcrumb-bar"><span class="active">▶ YouTube 통계</span></div>
  <div id="yt-no-key" class="card" style="text-align:center;padding:40px;">
    <div style="font-size:2rem;margin-bottom:10px;">📺</div>
    <div style="color:var(--muted);margin-bottom:8px;">YouTube API 키가 필요합니다</div>
    <code style="background:#21262d;padding:4px 10px;border-radius:6px;font-size:.78rem;">.env → YOUTUBE_API_KEY=AIza...</code>
  </div>
  <div id="yt-content" style="display:none;">
    <div class="grid-3" style="margin-bottom:16px;">
      <div class="card-sm" style="text-align:center;"><div id="yt-subs" class="stat-n" style="color:#f87171;">–</div><div style="font-size:.72rem;color:var(--muted);margin-top:4px;">구독자</div></div>
      <div class="card-sm" style="text-align:center;"><div id="yt-views" class="stat-n" style="color:#fbbf24;">–</div><div style="font-size:.72rem;color:var(--muted);margin-top:4px;">총 조회수</div></div>
      <div class="card-sm" style="text-align:center;"><div id="yt-vcnt" class="stat-n" style="color:#60a5fa;">–</div><div style="font-size:.72rem;color:var(--muted);margin-top:4px;">영상 수</div></div>
    </div>
    <div class="card" style="margin-bottom:16px;">
      <div class="sec-title">영상별 조회수 TOP 20</div>
      <canvas id="chart-yt-views" height="130"></canvas>
    </div>
    <div class="card">
      <div class="sec-title">영상 통계</div>
      <div style="overflow-x:auto;">
        <table><thead><tr><th>Day</th><th>단어</th><th>등급</th><th>조회수</th><th>좋아요</th><th>YouTube</th></tr></thead>
        <tbody id="yt-tbody"></tbody></table>
      </div>
    </div>
  </div>
</div>

</div><!-- /main -->
</div><!-- /body -->

<script>
// ── 상수 ─────────────────────────────────────────────────────
const LVC={1:'#22d3ee',2:'#34d399',3:'#a3e635',4:'#fbbf24',5:'#fb923c',6:'#f87171'};
const EXAM_COLORS={TOPIK:'#818cf8',TOEIC:'#60a5fa',JLPT:'#f472b6',IELTS:'#a78bfa',HSK:'#f87171'};
const LANG_NAMES={EN:'🇺🇸 영어',CN:'🇨🇳 중국어',JP:'🇯🇵 일본어',VN:'🇻🇳 베트남어',SP:'🇪🇸 스페인어',KO:'🇰🇷 한국어',FR:'🇫🇷 프랑스어',DE:'🇩🇪 독일어'};

let _ov=null, _node=null, _chartTL=null, _chartYT=null;
let _desktopEnabled=true, _currentView='overview';

// ── 포맷 ─────────────────────────────────────────────────────
const fmt=n=>{if(!n&&n!==0)return'–';if(n>=1e6)return(n/1e6).toFixed(1)+'M';if(n>=1e3)return(n/1e3).toFixed(1)+'K';return n.toLocaleString();};
const fmtSz=b=>{if(!b)return'–';return b>1e6?(b/1e6).toFixed(1)+'MB':(b/1e3).toFixed(0)+'KB';};
const ago=iso=>{if(!iso)return'–';const s=Math.floor((Date.now()-new Date(iso.replace('T',' ')))/1000);if(s<60)return s+'초 전';if(s<3600)return Math.floor(s/60)+'분 전';if(s<86400)return Math.floor(s/3600)+'시간 전';return Math.floor(s/86400)+'일 전';};

// ── 시계 ─────────────────────────────────────────────────────
function tick(){document.getElementById('clock').textContent=new Date().toLocaleString('ko-KR',{hour12:false});}
setInterval(tick,1000);tick();

// ── 네비게이션 ───────────────────────────────────────────────
function nav(el,view){
  document.querySelectorAll('.s-item').forEach(i=>i.classList.remove('active'));
  if(el) el.classList.add('active');
  document.querySelectorAll('.view').forEach(v=>v.style.display='none');
  const target=document.getElementById('view-'+view) || document.getElementById('view-lang:TOPIK:EN');
  if(target) target.style.display='block';
  _currentView=view;
  // 언어 뷰 동적 렌더
  if(view.startsWith('lang:')) renderLangView(view);
  // 노드 데이터 로드
  if(view.startsWith('lang:') || view.startsWith('exam:')) loadNodeData(view);
}

function toggleExam(el, view){
  const parts=view.split(':'); const exam=parts[1];
  const ch=document.getElementById('ch-'+exam);
  const arr=document.getElementById('arr-'+exam);
  if(ch.classList.contains('open')){
    ch.classList.remove('open'); arr.textContent='▶';
  } else {
    ch.classList.add('open'); arr.textContent='▼';
  }
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

// ── 헤더 / 진행 바 ───────────────────────────────────────────
function renderHeader(d){
  const p=d.progress, run=p.status==='running';
  const row=document.getElementById('progress-row');
  row.style.display=run?'flex':'none';
  if(run){
    document.getElementById('pr-word').textContent=p.word?p.word+' ('+p.meaning+')':'렌더링 중...';
    document.getElementById('pr-step').textContent=p.step||'';
    document.getElementById('pr-bar').style.width=(p.pct||0)+'%';
    document.getElementById('pr-pct').textContent=(p.pct||0)+'%';
  }
  // 렌더링 토글 — 초기 타겟 동기화
  const cfg=d.render_config; _desktopEnabled=cfg.desktop_enabled;
  if(!window._targetInitDone){_batchTarget=_desktopEnabled?'desktop':'nas';_customTarget=_desktopEnabled?'desktop':'nas';window._targetInitDone=true;}
  const btn=document.getElementById('toggle-btn');
  if(_desktopEnabled){btn.textContent='💻 데스크탑';btn.style.cssText='padding:3px 10px;font-size:.72rem;background:#1a1a3a;color:#818cf8;border:1px solid #818cf8;border-radius:6px;cursor:pointer;';}
  else{btn.textContent='🖥 NAS';btn.style.cssText='padding:3px 10px;font-size:.72px;background:#0d2b0d;color:#3fb950;border:1px solid #3fb950;border-radius:6px;cursor:pointer;font-size:.72rem;';}
  const q=cfg.queue||{};
  const qb=document.getElementById('queue-badge');
  if(q.status==='pending') qb.textContent='⏳ 대기';
  else if(q.status==='claimed') qb.textContent='🔄 '+q.claimed_by;
  else if(q.status==='done') qb.textContent='✅';
  else qb.textContent='';
}

// ── 전체 개요 ────────────────────────────────────────────────
function renderOverview(d){
  const ov=d.overview, t=ov.total||1;
  document.getElementById('ov-total').textContent=fmt(ov.total);
  document.getElementById('ov-gen').textContent=fmt(ov.generated);
  document.getElementById('ov-upl').textContent=fmt(ov.uploaded);
  document.getElementById('ov-remain').textContent=fmt(ov.total-ov.uploaded);
  document.getElementById('ov-gen-bar').style.width=(ov.generated/t*100)+'%';
  document.getElementById('ov-upl-bar').style.width=(ov.uploaded/t*100)+'%';
  // 타임라인
  const tl=d.timeline||{};const keys=Object.keys(tl).sort();const vals=keys.map(k=>tl[k]);
  if(keys.length){
    if(_chartTL){_chartTL.data.labels=keys;_chartTL.data.datasets[0].data=vals;_chartTL.update();}
    else _chartTL=new Chart(document.getElementById('chart-timeline'),{
      type:'line',data:{labels:keys,datasets:[{data:vals,borderColor:'#3fb950',backgroundColor:'rgba(63,185,80,.1)',fill:true,tension:.3,pointRadius:3,pointBackgroundColor:'#3fb950'}]},
      options:{responsive:true,plugins:{legend:{display:false}},scales:{x:{ticks:{color:var_muted(),maxTicksLimit:8},grid:{display:false}},y:{ticks:{color:var_muted(),stepSize:1},grid:{color:'#21262d'}}}}
    });
  }
  // 음악
  const ml=document.getElementById('ov-music');ml.innerHTML='';
  if(!d.music_files||!d.music_files.length) ml.innerHTML='<span style="color:var(--muted);font-size:.78rem;">assets/music/ 폴더가 비어 있습니다</span>';
  else d.music_files.forEach(f=>{ml.innerHTML+=`<div class="chip">🎵 ${f}</div>`;});
  // 시험 카테고리 카드
  renderExamCategoryCards(d);
}

function var_muted(){return '#8b949e';}

function renderExamCategoryCards(d){
  const el=document.getElementById('exam-cards-view');
  if(!el)return;
  const exams=[
    {id:'TOPIK',flag:'🇰🇷',name:'TOPIK',color:'#818cf8',desc:'한국어능력시험'},
    {id:'TOEIC',flag:'📝',name:'TOEIC',color:'#60a5fa',desc:'비즈니스 영어',soon:true},
    {id:'JLPT',flag:'🌸',name:'JLPT',color:'#f472b6',desc:'일본어능력시험',soon:true},
    {id:'IELTS',flag:'🎓',name:'IELTS',color:'#a78bfa',desc:'국제영어시험',soon:true},
    {id:'HSK',flag:'🐉',name:'HSK',color:'#f87171',desc:'중국어능력시험',soon:true},
  ];
  el.innerHTML=exams.map(e=>`
    <div onclick="${e.soon?'':'nav(document.querySelector(\"[data-view=exam\\\\:'+e.id+']\"),\"exam:'+e.id+'\")'}"
         style="background:var(--card);border:1px solid ${e.soon?'var(--border)':e.color+'44'};border-radius:12px;padding:18px;cursor:${e.soon?'default':'pointer'};transition:.15s;${e.soon?'opacity:.5':''}">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="font-size:1.5rem;">${e.flag}</span>
          <div><div style="font-weight:700;color:${e.color};">${e.name}</div><div style="font-size:.7rem;color:var(--muted);">${e.desc}</div></div>
        </div>
        ${e.soon?'<span class="badge badge-soon">준비 중</span>':'<span style="color:'+e.color+';font-size:1rem;">›</span>'}
      </div>
      ${e.soon?'':`<div style="font-size:.75rem;color:var(--muted);">EN · CN · JP · VN · SP</div>`}
    </div>`).join('');
}

// ── 시험 뷰 (언어 카드) ─────────────────────────────────────
function renderExamView(exam, stats){
  const el=document.getElementById('topik-lang-cards');
  if(!el)return;
  const langs=['EN','CN','JP','VN','SP'];
  const col=EXAM_COLORS[exam]||'#818cf8';
  el.innerHTML=langs.map(lang=>`
    <div class="lang-card available" style="--card-color:${col}44;border-color:${lang==='EN'?col+'66':'var(--border)'};"
         onclick="nav(document.querySelector('[data-view=lang\\:${exam}\\:${lang}]')||createLangView('${exam}','${lang}'),'lang:${exam}:${lang}')">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
        <div style="font-size:1.2rem;">${LANG_NAMES[lang]||lang}</div>
        ${lang==='EN'?`<span class="badge" style="background:${col}22;color:${col};border:1px solid ${col}44;">활성</span>`:'<span class="badge badge-soon">준비 중</span>'}
      </div>
      ${lang==='EN'?`
      <div style="font-size:1.4rem;font-weight:700;color:${col};">${fmt(stats.generated||0)}</div>
      <div style="font-size:.7rem;color:var(--muted);">영상 생성 / ${fmt(stats.total||0)} 전체</div>
      <div class="pbar-bg" style="height:4px;margin-top:8px;"><div class="pbar" style="height:4px;width:${stats.total?(stats.generated/stats.total*100).toFixed(1):0}%;background:${col};"></div></div>
      `:`<div style="font-size:.8rem;color:var(--muted2);">콘텐츠 준비 중</div>`}
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

  // 등급별 바
  const lvRows=[1,2,3,4,5,6].map(lv=>{
    const info=stats.by_level?.[String(lv)]||{total:0,generated:0,uploaded:0};
    const gpct=info.total?Math.round(info.generated/info.total*100):0;
    const upct=info.total?Math.round(info.uploaded/info.total*100):0;
    return `<tr>
      <td><span style="color:${LVC[lv]};font-weight:700;">${lv}급</span></td>
      <td style="color:var(--muted);">${fmt(info.total)}</td>
      <td style="color:${col};">${fmt(info.generated)} <span style="color:var(--muted2);font-size:.7rem;">(${gpct}%)</span></td>
      <td style="color:#3fb950;">${fmt(info.uploaded)} <span style="color:var(--muted2);font-size:.7rem;">(${upct}%)</span></td>
      <td style="width:120px;"><div class="pbar-bg" style="height:4px;"><div class="pbar" style="height:4px;width:${gpct}%;background:${col};"></div></div></td>
    </tr>`;}).join('');

  // 최근 영상
  const vidRows=(stats.video_list||[]).slice(-20).reverse().map(v=>`<tr>
    <td style="color:var(--muted);">${v.day?'#'+v.day:'–'}</td>
    <td style="font-weight:600;">${v.word}</td>
    <td><span style="color:${LVC[v.level]};font-weight:600;">${v.level}급</span></td>
    <td style="color:var(--muted);font-size:.75rem;">${v.music_file?'🎵 '+v.music_file:'–'}</td>
    <td style="color:#fbbf24;font-weight:600;">${v.views?fmt(v.views):'–'}</td>
    <td>${v.video_id?`<a href="https://youtube.com/watch?v=${v.video_id}" target="_blank" style="color:#f87171;font-size:.75rem;">▶</a>`:'–'}</td>
  </tr>`).join('');

  el.innerHTML=`
    <div class="breadcrumb-bar">
      <span onclick="nav(document.querySelector('[data-view=overview]'),'overview')">📊 개요</span>
      <span style="color:var(--muted2);">›</span>
      <span onclick="nav(document.querySelector('[data-view=cat\\\\:시험용]'),'cat:시험용')">📚 시험용</span>
      <span style="color:var(--muted2);">›</span>
      <span onclick="nav(document.querySelector('[data-view=exam\\\\:${exam}]'),'exam:${exam}')">🇰🇷 ${exam}</span>
      <span style="color:var(--muted2);">›</span>
      <span class="active">${LANG_NAMES[lang]||lang}</span>
    </div>
    <div class="grid-3" style="margin-bottom:16px;">
      <div class="card-sm" style="text-align:center;border-color:${col}44;">
        <div class="stat-n" style="color:${col};">${fmt(stats.total)}</div>
        <div style="font-size:.72rem;color:var(--muted);margin-top:4px;">전체 단어</div>
      </div>
      <div class="card-sm" style="text-align:center;">
        <div class="stat-n" style="color:${col};">${fmt(stats.generated)}</div>
        <div style="font-size:.72rem;color:var(--muted);margin-top:4px;">영상 생성 (${total?(stats.generated/total*100).toFixed(1):0}%)</div>
        <div class="pbar-bg" style="height:4px;margin-top:6px;"><div class="pbar" style="height:4px;width:${total?(stats.generated/total*100):0}%;background:${col};"></div></div>
      </div>
      <div class="card-sm" style="text-align:center;">
        <div class="stat-n" style="color:#3fb950;">${fmt(stats.uploaded)}</div>
        <div style="font-size:.72rem;color:var(--muted);margin-top:4px;">업로드 완료 (${total?(stats.uploaded/total*100).toFixed(1):0}%)</div>
        <div class="pbar-bg" style="height:4px;margin-top:6px;"><div class="pbar" style="height:4px;width:${total?(stats.uploaded/total*100):0}%;background:#3fb950;"></div></div>
      </div>
    </div>
    <div class="grid-2" style="margin-bottom:16px;">
      <div class="card">
        <div class="sec-title">등급별 현황</div>
        <table><thead><tr><th>등급</th><th>전체</th><th>생성</th><th>업로드</th><th>진행률</th></tr></thead>
        <tbody>${lvRows}</tbody></table>
      </div>
      <div class="card">
        <div class="sec-title">최근 영상</div>
        <table><thead><tr><th>Day</th><th>단어</th><th>등급</th><th>음악</th><th>조회수</th><th></th></tr></thead>
        <tbody>${vidRows||'<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:20px;">영상 없음</td></tr>'}</tbody></table>
      </div>
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
  setEl(P+'-word-txt', wdone+' / '+t);
  setEl(P+'-word-pct', wpct+'%');
  const wb=document.getElementById(P+'-word-bar');
  if(wb) wb.style.width=wpct+'%';

  // 예문 일러스트 바
  setEl(P+'-sent-txt', sdone+' / '+stotal);
  setEl(P+'-sent-pct', spct+'%');
  const sb=document.getElementById(P+'-sent-bar');
  if(sb) sb.style.width=spct+'%';

  // 등급별
  const lvEl=document.getElementById(P+'-levels');
  if(lvEl){
    lvEl.innerHTML=[1,2,3,4,5,6].map(lv=>{
      const info=ill.by_level?.[String(lv)]||{total:0,word_done:0,sent_total:0,sent_done:0};
      const wp=info.total?Math.round(info.word_done/info.total*100):0;
      const sp=info.sent_total?Math.round(info.sent_done/info.sent_total*100):0;
      const c=LVC[lv];
      return `<div style="background:#21262d;border-radius:8px;padding:8px;text-align:center;">
        <div style="color:${c};font-weight:700;font-size:.8rem;">${lv}급</div>
        <div style="font-size:.75rem;font-weight:600;margin-top:2px;">🖼 ${info.word_done}</div>
        <div style="font-size:.65rem;color:var(--muted);">${wp}%</div>
        <div class="pbar-bg" style="height:2px;margin:3px 0;"><div class="pbar" style="height:2px;width:${wp}%;background:${c};"></div></div>
        <div style="font-size:.75rem;font-weight:600;">📝 ${info.sent_done}</div>
        <div style="font-size:.65rem;color:var(--muted);">${sp}%</div>
        <div class="pbar-bg" style="height:2px;margin-top:3px;"><div class="pbar" style="height:2px;width:${sp}%;background:#818cf8;"></div></div>
      </div>`;}).join('');
  }

  // 진행 배지
  const prog=ill.progress||{};
  const badge=document.getElementById(P+'-badge');
  if(badge){
    if(prog.status==='running'){
      const step=prog.step?` — ${prog.step}`:'';
      badge.textContent=`● 생성 중 (${prog.pct||0}%)${step}`;
      badge.className='badge badge-run pulse';
    } else if(prog.status==='done'){badge.textContent='✅ 완료';badge.className='badge badge-done';}
    else{badge.textContent='대기 중';badge.className='badge badge-idle';}
  }

  // ov → illustrations view 동기화
  if(prefix==='ov'){
    renderIllustStats({...ill,progress:prog},'iv');
    const btns=['illust-gen-btn','illust-gen-btn2'];
    btns.forEach(id=>{const b=document.getElementById(id);if(b){
      b.disabled=prog.status==='running';
      b.textContent=prog.status==='running'?'⏳ 생성 중...':'🎨 생성';
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
  const labels={both:'단어+예문',words:'단어만',sentences:'예문만'};
  const c=_illustCost(end-start+1,mode);
  if(!confirm(`ID ${start}~${end} — ${labels[mode]}\n예상 ${c.cnt}장 / $${(c.cnt*0.02).toFixed(2)}\n계속할까요?`))return;
  const r=await fetch('/api/illustrations/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({start,end,mode})});
  const d=await r.json();
  if(!r.ok) alert('오류: '+(d.error||'알 수 없음'));
  else loadOverview();
}
async function startIllustGen(){ await _startIllust(+document.getElementById('illust-start').value||1,+document.getElementById('illust-end').value||10,document.getElementById('illust-mode').value); }
async function startIllustGen2(){ await _startIllust(+document.getElementById('illust-start2').value||1,+document.getElementById('illust-end2').value||100,document.getElementById('illust-mode2').value); }

function setEl(id,val){const e=document.getElementById(id);if(e)e.textContent=val;}

// ── 렌더 패널 ───────────────────────────────────────────────
let _rpOpen=false, _rpTab='batch', _batchData=null, _configSlots=[];
let _batchTarget='desktop', _customTarget='desktop';

function toggleRenderPanel(){
  _rpOpen=!_rpOpen;
  document.getElementById('render-panel').style.transform=_rpOpen?'translateX(0)':'translateX(100%)';
  if(_rpOpen){ loadBatchData(); rpTab('batch'); }
}

function rpTab(tab){
  _rpTab=tab;
  ['batch','custom','history','config'].forEach(t=>{
    const v=document.getElementById('rp-'+t);if(v)v.style.display=t===tab?'block':'none';
    const b=document.getElementById('rp-tab-'+t);
    if(b){b.style.borderBottomColor=t===tab?'#3fb950':'transparent';b.style.color=t===tab?'#e6edf3':'#8b949e';}
  });
  if(tab==='batch') loadBatchData();
  if(tab==='custom') updateCustomPreview();
  if(tab==='history'){document.getElementById('rp-date-pick').value=new Date().toISOString().slice(0,10);loadHistoryDate();}
  if(tab==='config') loadConfigSlots();
}

async function loadBatchData(){
  try{ const r=await fetch('/api/batch/today'); _batchData=await r.json(); renderBatchList(_batchData); }catch(e){}
}

const _FLAGS={EN:'🇺🇸',JP:'🇯🇵',CN:'🇨🇳',VN:'🇻🇳',SP:'🇪🇸',KO:'🇰🇷',FR:'🇫🇷',DE:'🇩🇪'};
const _STATUS_HTML={
  pending:'<span style="color:#f59e0b;font-size:.72rem;">● 대기</span>',
  rendering:'<span style="color:#3fb950;font-size:.72rem;" class="pulse">⟳ 렌더링</span>',
  generated:'<span style="color:#818cf8;font-size:.72rem;">✓ 생성됨</span>',
  uploaded:'<span style="color:#3fb950;font-size:.72rem;">✓ 업로드</span>',
  no_word:'<span style="color:#484f58;font-size:.72rem;">— 완료</span>',
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
  const btn=document.getElementById('rp-render-all');
  if(btn){btn.disabled=bq.status==='running'||pending===0;btn.textContent=bq.status==='running'?'⏳ 진행 중...':'▶ 전체 렌더링 ('+pending+'개 · '+(_batchTarget==='desktop'?'💻 GPU':'🖥 NAS')+')';}
  const el=document.getElementById('rp-batch-list');
  if(!batch.length){el.innerHTML='<div style="color:#8b949e;text-align:center;padding:20px;">슬롯이 없습니다. ⚙️ 설정 탭에서 추가하세요.</div>';return;}
  el.innerHTML=batch.map((b,i)=>{
    const w=b.word; const col=EXAM_COLORS[b.exam]||'#818cf8'; const lvC=LVC[b.level]||'#8b949e';
    const canR=b.status==='pending'&&w;
    return `<div style="display:flex;align-items:center;gap:8px;padding:10px 12px;background:#1c2128;border-radius:8px;margin-bottom:5px;border:1px solid #21262d;">
      <span style="font-size:.68rem;color:#484f58;min-width:14px;">${i+1}</span>
      <span style="color:${col};font-size:.7rem;font-weight:700;min-width:42px;">${b.exam}</span>
      <span style="font-size:.82rem;">${_FLAGS[b.lang]||b.lang}</span>
      <span style="color:${lvC};font-size:.72rem;font-weight:700;">${b.level}급</span>
      <div style="flex:1;min-width:0;">
        ${w?`<div style="font-weight:600;font-size:.84rem;">${w.word}</div><div style="color:#8b949e;font-size:.68rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${w.meaning}</div>`
          :'<div style="color:#484f58;font-size:.78rem;">– 모든 단어 완료</div>'}
      </div>
      ${_STATUS_HTML[b.status]||''}
      ${canR?`<button onclick="renderSingle(${w.id})" style="padding:3px 10px;background:#0d2b0d;color:#3fb950;border:1px solid #3fb950;border-radius:5px;cursor:pointer;font-size:.72rem;">▶</button>`:''}
    </div>`;
  }).join('');
}

function updateBatchTargetUI(){
  const dBtn=document.getElementById('rp-target-desktop');
  const nBtn=document.getElementById('rp-target-nas');
  if(!dBtn||!nBtn) return;
  if(_batchTarget==='desktop'){
    dBtn.style.cssText='flex:1;padding:6px;border-radius:6px;cursor:pointer;font-size:.74rem;font-weight:600;border:1px solid #818cf8;background:#1a1a3a;color:#818cf8;transition:.15s;';
    nBtn.style.cssText='flex:1;padding:6px;border-radius:6px;cursor:pointer;font-size:.74rem;font-weight:600;border:1px solid #30363d;background:transparent;color:#8b949e;transition:.15s;';
  }else{
    dBtn.style.cssText='flex:1;padding:6px;border-radius:6px;cursor:pointer;font-size:.74rem;font-weight:600;border:1px solid #30363d;background:transparent;color:#8b949e;transition:.15s;';
    nBtn.style.cssText='flex:1;padding:6px;border-radius:6px;cursor:pointer;font-size:.74rem;font-weight:600;border:1px solid #3fb950;background:#0d2b0d;color:#3fb950;transition:.15s;';
  }
}

function setBatchTarget(t){
  _batchTarget=t;
  if(_batchData) renderBatchList(_batchData);
}

async function renderBatchAll(){
  const btn=document.getElementById('rp-render-all');
  btn.disabled=true;btn.textContent='⏳ 요청 중...';
  try{
    const r=await fetch('/api/render/batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({target:_batchTarget})});
    const d=await r.json();
    if(!r.ok) alert('오류: '+(d.error||''));
    else setTimeout(loadBatchData,500);
  }catch(e){alert('실패: '+e);}
  finally{btn.disabled=false;btn.textContent='▶ 전체 렌더링';}
}

async function renderSingle(wordId){
  try{
    const t=_rpTab==='custom'?_customTarget:_batchTarget;
    const r=await fetch('/api/render',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({word_id:wordId,target:t})});
    const d=await r.json();
    if(!r.ok) alert('오류: '+(d.error||''));
    else{setTimeout(loadBatchData,500);loadOverview();}
  }catch(e){alert('실패: '+e);}
}

// ── 커스텀 렌더링 ─────────────────────────────────────────
function setCustomTarget(t){
  _customTarget=t;
  const dBtn=document.getElementById('rc-target-desktop');
  const nBtn=document.getElementById('rc-target-nas');
  if(t==='desktop'){
    dBtn.style.cssText='flex:1;padding:8px;border-radius:6px;cursor:pointer;font-size:.76rem;font-weight:600;border:1px solid #818cf8;background:#1a1a3a;color:#818cf8;transition:.15s;';
    nBtn.style.cssText='flex:1;padding:8px;border-radius:6px;cursor:pointer;font-size:.76rem;font-weight:600;border:1px solid #30363d;background:transparent;color:#8b949e;transition:.15s;';
  }else{
    dBtn.style.cssText='flex:1;padding:8px;border-radius:6px;cursor:pointer;font-size:.76rem;font-weight:600;border:1px solid #30363d;background:transparent;color:#8b949e;transition:.15s;';
    nBtn.style.cssText='flex:1;padding:8px;border-radius:6px;cursor:pointer;font-size:.76rem;font-weight:600;border:1px solid #3fb950;background:#0d2b0d;color:#3fb950;transition:.15s;';
  }
  updateCustomTimeEst();
}

let _customPreviewTimer=null;
function updateCustomPreview(){
  clearTimeout(_customPreviewTimer);
  _customPreviewTimer=setTimeout(_doCustomPreview,300);
}

async function _doCustomPreview(){
  const exam=document.getElementById('rc-exam').value;
  const lang=document.getElementById('rc-lang').value;
  const level=document.getElementById('rc-level').value;
  const count=Math.max(1,Math.min(30,+document.getElementById('rc-count').value||10));
  const startId=document.getElementById('rc-start-id').value;
  const endId=document.getElementById('rc-end-id').value;
  let url=`/api/render/preview?exam=${exam}&lang=${lang}&level=${level}&count=${count}`;
  if(startId) url+=`&start_id=${startId}`;
  if(endId) url+=`&end_id=${endId}`;
  try{
    const r=await fetch(url);
    const d=await r.json();
    const el=document.getElementById('rc-preview');
    const remEl=document.getElementById('rc-remaining');
    const hintEl=document.getElementById('rc-id-range-hint');
    if(remEl) remEl.textContent=`남은 단어: ${d.remaining||0}개`;
    if(hintEl && d.level_min_id!=null) hintEl.textContent=`이 등급 범위: ID ${d.level_min_id} ~ ${d.level_max_id} (${d.level_total}개)`;
    if(!d.words||!d.words.length){
      el.innerHTML='<div style="color:#484f58;text-align:center;padding:16px;font-size:.78rem;">렌더링할 단어가 없습니다</div>';
      document.getElementById('rc-start').disabled=true;
      return;
    }
    document.getElementById('rc-start').disabled=false;
    const lvC={'1':'#3fb950','2':'#58a6ff','3':'#d29922','4':'#f78166','5':'#bc8cff','6':'#f87171'};
    el.innerHTML=d.words.map((w,i)=>{
      const c=lvC[w.level]||'#8b949e';
      return `<div style="display:flex;align-items:center;gap:8px;padding:8px 10px;background:#1c2128;border-radius:7px;margin-bottom:4px;border:1px solid #21262d;">
        <span style="font-size:.66rem;color:#484f58;min-width:18px;text-align:right;">${i+1}</span>
        <span style="color:${c};font-size:.68rem;font-weight:700;">Lv.${w.level}</span>
        <span style="font-weight:600;font-size:.82rem;">${w.word}</span>
        <span style="color:#8b949e;font-size:.68rem;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${w.meaning}</span>
        <span style="color:#484f58;font-size:.64rem;">ID ${w.id}</span>
      </div>`;
    }).join('');
    document.getElementById('rc-start').textContent=`▶ 렌더링 시작 (${d.words.length}개 · ${_customTarget==='desktop'?'💻 GPU':'🖥 NAS'})`;
    updateCustomTimeEst();
  }catch(e){}
}

function updateCustomTimeEst(){
  const count=Math.max(1,+document.getElementById('rc-count').value||1);
  const perMin=_customTarget==='desktop'?3:12;
  const total=count*perMin;
  const el=document.getElementById('rc-time-est');
  if(el) el.textContent=`예상 소요: ~${total}분 (${count}개 × ${perMin}분)`;
}

async function startCustomRender(){
  const exam=document.getElementById('rc-exam').value;
  const lang=document.getElementById('rc-lang').value;
  const level=+document.getElementById('rc-level').value;
  const count=Math.max(1,Math.min(30,+document.getElementById('rc-count').value||10));
  const startId=+document.getElementById('rc-start-id').value||null;
  const endId=+document.getElementById('rc-end-id').value||null;
  const target=_customTarget;
  let range=startId||endId?` (ID ${startId||'?'}~${endId||'?'})`:'';
  const msg=`${exam} ${lang} ${level}급 × 최대 ${count}개${range}\n위치: ${target==='desktop'?'💻 데스크탑 GPU':'🖥 NAS CPU'}\n\n시작할까요?`;
  if(!confirm(msg)) return;
  const btn=document.getElementById('rc-start');
  btn.disabled=true;btn.textContent='⏳ 요청 중...';
  try{
    const body={exam,lang,level,count,target};
    if(startId) body.start_id=startId;
    if(endId) body.end_id=endId;
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
        <div style="flex:1;"><div style="font-weight:600;font-size:.84rem;">${v.word}</div><div style="color:#8b949e;font-size:.68rem;">${v.exam}/${v.lang}</div></div>
        ${v.video_id?`<a href="https://youtube.com/watch?v=${v.video_id}" target="_blank" style="color:#f87171;font-size:.78rem;">▶ YT</a>`:'<span style="color:#818cf8;font-size:.72rem;">생성됨</span>'}
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
  const exams=['TOPIK','TOEIC','JLPT','IELTS','HSK'];
  const langs=['EN','JP','CN','VN','SP','KO','FR','DE'];
  const levels=[1,2,3,4,5,6];
  el.innerHTML=_configSlots.map((s,i)=>`
    <div style="display:flex;align-items:center;gap:5px;margin-bottom:5px;background:#1c2128;padding:7px 10px;border-radius:7px;border:1px solid #21262d;">
      <span style="color:#484f58;font-size:.68rem;min-width:16px;">${i+1}</span>
      <select onchange="_configSlots[${i}].exam=this.value" style="background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:5px;padding:3px 5px;font-size:.72rem;">
        ${exams.map(e=>`<option${s.exam===e?' selected':''}>${e}</option>`).join('')}
      </select>
      <select onchange="_configSlots[${i}].lang=this.value" style="background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:5px;padding:3px 5px;font-size:.72rem;">
        ${langs.map(l=>`<option${s.lang===l?' selected':''}>${l}</option>`).join('')}
      </select>
      <select onchange="_configSlots[${i}].level=+this.value" style="background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:5px;padding:3px 5px;font-size:.72rem;">
        ${levels.map(lv=>`<option${s.level===lv?' selected':''}>${lv}</option>`).join('')}
      </select>
      <span style="font-size:.72rem;">${_FLAGS[s.lang]||''}</span>
      <button onclick="_configSlots.splice(${i},1);renderConfigSlots()" style="margin-left:auto;background:none;border:none;color:#f87171;cursor:pointer;font-size:.85rem;">✕</button>
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
    {exam:'TOPIK',lang:'SP',level:1},{exam:'TOPIK',lang:'SP',level:2},{exam:'TOPIK',lang:'SP',level:3},
  ];
  renderConfigSlots();
}

// ── 초기화 ───────────────────────────────────────────────────
updateIllustCost(); updateIllustCost2();
loadOverview();
setInterval(loadOverview,5000);
// 패널 열려있으면 자동갱신
setInterval(()=>{if(_rpOpen){if(_rpTab==='batch')loadBatchData();}},5000);
</script>

<!-- ══ 렌더 패널 (우측 드로어) ══════════════════════════════ -->
<div id="render-panel" style="position:fixed;top:52px;right:0;width:460px;height:calc(100vh - 52px);background:#161b22;border-left:1px solid #21262d;transform:translateX(100%);transition:transform .3s ease;z-index:200;display:flex;flex-direction:column;box-shadow:-8px 0 24px rgba(0,0,0,.4);">
  <div style="display:flex;align-items:center;padding:0 14px;height:42px;border-bottom:1px solid #21262d;flex-shrink:0;">
    <span style="font-weight:700;font-size:.88rem;">렌더링 대기열</span>
    <div style="display:flex;margin-left:12px;gap:0;">
      <button onclick="rpTab('batch')" id="rp-tab-batch" style="padding:4px 10px;background:transparent;border:none;color:#e6edf3;cursor:pointer;font-size:.73rem;border-bottom:2px solid #3fb950;" class="rp-tab-btn">📅 오늘</button>
      <button onclick="rpTab('custom')" id="rp-tab-custom" style="padding:4px 10px;background:transparent;border:none;color:#8b949e;cursor:pointer;font-size:.73rem;border-bottom:2px solid transparent;" class="rp-tab-btn">🎬 커스텀</button>
      <button onclick="rpTab('history')" id="rp-tab-history" style="padding:4px 10px;background:transparent;border:none;color:#8b949e;cursor:pointer;font-size:.73rem;border-bottom:2px solid transparent;" class="rp-tab-btn">🗓 날짜별</button>
      <button onclick="rpTab('config')" id="rp-tab-config" style="padding:4px 10px;background:transparent;border:none;color:#8b949e;cursor:pointer;font-size:.73rem;border-bottom:2px solid transparent;" class="rp-tab-btn">⚙️ 설정</button>
    </div>
    <button onclick="toggleRenderPanel()" style="margin-left:auto;background:none;border:none;color:#8b949e;cursor:pointer;font-size:1.1rem;padding:4px;">✕</button>
  </div>
  <!-- 오늘 분량 -->
  <div id="rp-batch" style="flex:1;overflow-y:auto;padding:14px;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
      <div><div id="rp-today-date" style="font-weight:700;font-size:.88rem;"></div><div id="rp-today-sub" style="font-size:.7rem;color:#8b949e;"></div></div>
    </div>
    <!-- 렌더링 위치 선택 -->
    <div style="background:#1c2128;border:1px solid #21262d;border-radius:8px;padding:10px 12px;margin-bottom:12px;">
      <div style="font-size:.68rem;color:#484f58;margin-bottom:6px;font-weight:600;">렌더링 위치</div>
      <div style="display:flex;gap:6px;margin-bottom:6px;">
        <button id="rp-target-desktop" onclick="setBatchTarget('desktop')" style="flex:1;padding:6px;border-radius:6px;cursor:pointer;font-size:.74rem;font-weight:600;border:1px solid #818cf8;background:#1a1a3a;color:#818cf8;transition:.15s;">💻 데스크탑 <span style="font-weight:400;font-size:.65rem;">GPU</span></button>
        <button id="rp-target-nas" onclick="setBatchTarget('nas')" style="flex:1;padding:6px;border-radius:6px;cursor:pointer;font-size:.74rem;font-weight:600;border:1px solid #30363d;background:transparent;color:#8b949e;transition:.15s;">🖥 NAS <span style="font-weight:400;font-size:.65rem;">CPU</span></button>
      </div>
      <div id="rp-target-info" style="font-size:.66rem;color:#484f58;"></div>
    </div>
    <div id="rp-batch-list"></div>
    <div id="rp-batch-queue" style="margin-top:10px;font-size:.72rem;color:#8b949e;"></div>
    <button id="rp-render-all" onclick="renderBatchAll()" style="width:100%;margin-top:10px;background:#0d2b0d;color:#3fb950;border:1px solid #3fb950;border-radius:7px;padding:8px 14px;font-size:.78rem;font-weight:600;cursor:pointer;">▶ 전체 렌더링</button>
  </div>
  <!-- 커스텀 렌더링 -->
  <div id="rp-custom" style="display:none;flex:1;overflow-y:auto;padding:14px;">
    <!-- 렌더링 대상 -->
    <div style="font-size:.72rem;color:#8b949e;margin-bottom:8px;font-weight:600;">🎯 렌더링 대상</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px;">
      <div>
        <div style="font-size:.64rem;color:#484f58;margin-bottom:3px;">시험</div>
        <select id="rc-exam" onchange="updateCustomPreview()" style="width:100%;background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:6px 8px;font-size:.78rem;">
          <option value="TOPIK">🇰🇷 TOPIK</option><option value="TOEIC">📝 TOEIC</option><option value="JLPT">🌸 JLPT</option><option value="IELTS">🎓 IELTS</option><option value="HSK">🐉 HSK</option>
        </select>
      </div>
      <div>
        <div style="font-size:.64rem;color:#484f58;margin-bottom:3px;">언어</div>
        <select id="rc-lang" onchange="updateCustomPreview()" style="width:100%;background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:6px 8px;font-size:.78rem;">
          <option value="EN">🇺🇸 EN</option><option value="JP">🇯🇵 JP</option><option value="CN">🇨🇳 CN</option><option value="VN">🇻🇳 VN</option><option value="SP">🇪🇸 SP</option>
        </select>
      </div>
      <div>
        <div style="font-size:.64rem;color:#484f58;margin-bottom:3px;">등급</div>
        <select id="rc-level" onchange="updateCustomPreview()" style="width:100%;background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:6px 8px;font-size:.78rem;">
          <option value="1">1급</option><option value="2">2급</option><option value="3">3급</option><option value="4">4급</option><option value="5">5급</option><option value="6">6급</option>
        </select>
      </div>
      <div>
        <div style="font-size:.64rem;color:#484f58;margin-bottom:3px;">에피소드 수</div>
        <input type="number" id="rc-count" value="10" min="1" max="30" onchange="updateCustomPreview()" oninput="updateCustomPreview()" style="width:100%;background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:6px 8px;font-size:.78rem;">
      </div>
    </div>
    <!-- ID 범위 -->
    <div style="background:#1c2128;border:1px solid #21262d;border-radius:7px;padding:8px 10px;margin-bottom:14px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <span style="font-size:.68rem;color:#484f58;font-weight:600;">단어 ID 범위 (선택)</span>
        <span id="rc-id-range-hint" style="font-size:.62rem;color:#484f58;"></span>
      </div>
      <div style="display:flex;align-items:center;gap:6px;">
        <input type="number" id="rc-start-id" placeholder="시작" onchange="updateCustomPreview()" oninput="updateCustomPreview()" style="flex:1;background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:5px 8px;font-size:.78rem;">
        <span style="color:#484f58;font-size:.72rem;">~</span>
        <input type="number" id="rc-end-id" placeholder="끝" onchange="updateCustomPreview()" oninput="updateCustomPreview()" style="flex:1;background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:5px 8px;font-size:.78rem;">
        <button onclick="document.getElementById('rc-start-id').value='';document.getElementById('rc-end-id').value='';updateCustomPreview();" style="padding:4px 8px;background:#21262d;border:1px solid #30363d;border-radius:5px;color:#8b949e;cursor:pointer;font-size:.68rem;white-space:nowrap;">초기화</button>
      </div>
    </div>
    <!-- 렌더링 위치 -->
    <div style="font-size:.72rem;color:#8b949e;margin-bottom:8px;font-weight:600;">🖥 렌더링 위치</div>
    <div style="display:flex;gap:6px;margin-bottom:6px;">
      <button id="rc-target-desktop" onclick="setCustomTarget('desktop')" style="flex:1;padding:8px;border-radius:6px;cursor:pointer;font-size:.76rem;font-weight:600;border:1px solid #818cf8;background:#1a1a3a;color:#818cf8;transition:.15s;">💻 데스크탑<div style="font-size:.62rem;font-weight:400;margin-top:2px;">GPU · ~3분/편</div></button>
      <button id="rc-target-nas" onclick="setCustomTarget('nas')" style="flex:1;padding:8px;border-radius:6px;cursor:pointer;font-size:.76rem;font-weight:600;border:1px solid #30363d;background:transparent;color:#8b949e;transition:.15s;">🖥 NAS<div style="font-size:.62rem;font-weight:400;margin-top:2px;">CPU · ~12분/편</div></button>
    </div>
    <div id="rc-time-est" style="font-size:.66rem;color:#484f58;margin-bottom:14px;"></div>
    <!-- 미리보기 -->
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
      <span style="font-size:.72rem;color:#8b949e;font-weight:600;">📋 미리보기</span>
      <span id="rc-remaining" style="font-size:.64rem;color:#484f58;"></span>
    </div>
    <div id="rc-preview" style="margin-bottom:14px;max-height:240px;overflow-y:auto;"></div>
    <!-- 시작 버튼 -->
    <button id="rc-start" onclick="startCustomRender()" style="width:100%;padding:10px;background:#0d2b0d;color:#3fb950;border:1px solid #3fb950;border-radius:8px;cursor:pointer;font-size:.82rem;font-weight:700;">▶ 렌더링 시작</button>
  </div>
  <!-- 날짜별 -->
  <div id="rp-history" style="display:none;flex:1;overflow-y:auto;padding:14px;">
    <input type="date" id="rp-date-pick" onchange="loadHistoryDate()" style="background:#21262d;border:1px solid #30363d;border-radius:6px;color:#e6edf3;padding:6px 10px;font-size:.82rem;width:100%;margin-bottom:12px;">
    <div id="rp-history-list"></div>
  </div>
  <!-- 설정 -->
  <div id="rp-config" style="display:none;flex:1;overflow-y:auto;padding:14px;">
    <div style="font-size:.76rem;color:#8b949e;margin-bottom:10px;">하루 분량 설정 (시험/언어/등급별 슬롯)</div>
    <div id="rp-config-slots"></div>
    <button onclick="addSlot()" style="width:100%;margin-top:8px;padding:8px;background:#1c2128;border:1px dashed #30363d;border-radius:7px;color:#8b949e;cursor:pointer;font-size:.78rem;">+ 슬롯 추가</button>
    <div style="display:flex;gap:8px;margin-top:12px;">
      <button onclick="saveSchedule()" style="flex:1;padding:8px;background:#0d2b0d;color:#3fb950;border:1px solid #3fb950;border-radius:7px;cursor:pointer;font-weight:600;font-size:.8rem;">💾 저장</button>
      <button onclick="resetSchedule()" style="padding:8px 14px;background:transparent;color:#8b949e;border:1px solid #30363d;border-radius:7px;cursor:pointer;font-size:.8rem;">기본값</button>
    </div>
  </div>
</div>

</body>
</html>"""

@app.route("/")
def index(): return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765, debug=False)
