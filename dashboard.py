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
            has_illust = os.path.exists(f"{ILLUST_DIR}/lv{lv}/{word['word']}/word.png")
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
def write_queue_job(word_id, db_path=None, exam="TOPIK", lang="EN"):
    if not db_path:
        db_path = "/app/data/LanguageTest/words_db.json"
    save_json(QUEUE_FILE,{"word_id":word_id,"db_path":db_path,
        "exam":exam,"lang":lang,
        "status":"pending","claimed_by":None,"claimed_at":None,
        "created_at":datetime.now().isoformat(),"completed_at":None})

_render_thread = None
_illust_thread = None
_batch_thread  = None

def _is_batch_cancelled():
    bq = load_json(BATCH_QUEUE_F, {})
    return bq.get("status") == "cancelled"

def run_batch_render(word_ids, target="auto", db_path=None, auto_upload=False,
                     exam="TOPIK", lang="EN", words_map=None):
    """target: "desktop", "nas", "auto"(글로벌 토글 따름)
    auto_upload: True면 렌더링 후 YouTube 자동 업로드"""
    global _batch_thread
    for i, word_id in enumerate(word_ids):
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

        try:
            bq = load_json(BATCH_QUEUE_F, {})
            bq["current"] = i
            for item in bq.get("items", []):
                if item["word_id"] == word_id:
                    item["status"] = "rendering"
            save_json(BATCH_QUEUE_F, bq)

            write_queue_job(word_id, db_path, exam=exam, lang=lang)
            cfg = get_render_config()
            use_desktop = (target == "desktop") if target != "auto" else cfg.get("desktop_enabled")

            if use_desktop:
                deadline = time.time() + 30 * 60
                finished = False
                while time.time() < deadline:
                    if _is_batch_cancelled(): break
                    time.sleep(15)
                    rq = load_json(QUEUE_FILE, {})
                    if rq.get("status") in ("done", "failed"):
                        finished = True; break
                if _is_batch_cancelled(): continue
                if not finished:
                    run_render_nas(word_id, db_path, exam=exam, lang=lang)
            else:
                run_render_nas(word_id, db_path, exam=exam, lang=lang)

            # 렌더링 후 자동 업로드
            if auto_upload and words_map and word_id in words_map:
                bq2 = load_json(BATCH_QUEUE_F, {})
                for item in bq2.get("items", []):
                    if item["word_id"] == word_id:
                        item["status"] = "uploading"
                save_json(BATCH_QUEUE_F, bq2)

                word = words_map[word_id]
                lv = word.get("level", 1)
                video_path = f"/app/output/{exam}/{lang}/lv{lv}/video/{exam.lower()}_{word_id:04d}_{word['word']}.mp4"
                if not os.path.exists(video_path):
                    video_path = f"/app/output/topik_{word_id:04d}_{word['word']}.mp4"
                if os.path.exists(video_path):
                    vid = run_upload(word, video_path, exam=exam, lang=lang)
                    if vid:
                        for item in bq2.get("items", []):
                            if item["word_id"] == word_id:
                                item["video_id"] = vid
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

def run_render_nas(word_id, db_path=None, exam="TOPIK", lang="EN"):
    if not db_path:
        db_path = "/app/data/LanguageTest/words_db.json"
    try:
        q = load_json(QUEUE_FILE,{})
        q.update({"status":"claimed","claimed_by":"nas","claimed_at":datetime.now().isoformat()})
        save_json(QUEUE_FILE,q)
        r = subprocess.run([sys.executable,"/app/make_video.py",
            "--db",db_path,
            "--id",str(word_id),"--output","/app/output/",
            "--exam",exam,"--lang",lang])
        q = load_json(QUEUE_FILE,{})
        q.update({"status":"done" if r.returncode==0 else "failed","completed_at":datetime.now().isoformat()})
        save_json(QUEUE_FILE,q)
    except Exception as e:
        save_json(QUEUE_FILE,{**load_json(QUEUE_FILE,{}),"status":"failed","error":str(e)})

def run_upload(word, video_path, exam="TOPIK", lang="EN"):
    """렌더링 완료된 영상을 YouTube에 업로드"""
    try:
        sys.path.insert(0, os.path.dirname(__file__) or "/app")
        from upload_youtube import get_youtube_client, generate_metadata, upload_video, load_upload_log, save_upload_log

        log_path = f"{BASE}/logs/uploads.json"
        upload_log = load_upload_log(log_path)
        day_number = upload_log.get("last_day", 0) + 1

        metadata = generate_metadata(word, day_number, lang=lang)
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
                                thumbnail_path=thumb_path if thumb_path and os.path.exists(thumb_path) else None)

        upload_log["last_day"] = day_number
        upload_log["last_word_id"] = word["id"]
        upload_log.setdefault("uploaded", []).append({
            "day": day_number,
            "word_id": word["id"],
            "word": word["word"],
            "meaning": word.get("meaning", ""),
            "video_id": video_id,
            "youtube_url": f"https://youtube.com/watch?v={video_id}",
            "uploaded_at": datetime.now().isoformat(),
        })
        save_upload_log(upload_log, log_path)
        return video_id
    except Exception as e:
        print(f"  업로드 실패: {e}")
        import traceback; traceback.print_exc()
        return None

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
        f"{OUTPUT_DIR}/{exam}/{lang}/lv{lv}/video/{exam.lower()}_{word_id:04d}_{word['word']}.mp4",
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
    count    = int(request.args.get("count", 30))
    start_id = request.args.get("start_id", type=int)
    end_id   = request.args.get("end_id", type=int)
    words = get_next_words_for_custom(exam, lang, level, min(count, 30), start_id, end_id)
    # 일러스트 존재 여부 추가
    for w in words:
        lv = str(w.get("level", 1))
        w["has_illust"] = os.path.exists(f"{ILLUST_DIR}/lv{lv}/{w['word']}/word.png")
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
    wmap = {w["id"]: w["word"] for w in words}
    items = [{"word_id": wid, "word": wmap.get(wid, ""), "status": "pending"} for wid in word_ids]
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
    <button class="tab" id="rp-tab-config" onclick="rpTab('config')">⚙️ 설정</button>
  </div>
  <!-- 탭 내용: 배치 -->
  <div id="rp-batch">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
      <div><div id="rp-today-date" style="font-weight:700;font-size:.86rem;"></div><div id="rp-today-sub" style="font-size:.68rem;color:var(--muted);"></div></div>
      <div style="display:flex;gap:6px;">
        <button id="rp-target-desktop" onclick="setBatchTarget('desktop')" class="btn btn-p" style="font-size:.7rem;padding:4px 10px;">💻 GPU</button>
        <button id="rp-target-nas" onclick="setBatchTarget('nas')" class="btn btn-m" style="font-size:.7rem;padding:4px 10px;">🖥 NAS</button>
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
      <label style="font-size:.72rem;color:var(--muted);cursor:pointer;display:flex;align-items:center;gap:5px;">
        <input type="checkbox" id="rp-select-all" onchange="toggleAllBatchCheck()" style="accent-color:var(--green);">전체 선택
      </label>
      <div id="rp-batch-queue" style="margin-left:auto;font-size:.68rem;color:var(--muted);"></div>
    </div>
    <div id="rp-batch-list"></div>
    <div style="display:flex;align-items:center;gap:8px;margin-top:12px;">
      <label style="font-size:.72rem;color:var(--muted);cursor:pointer;display:flex;align-items:center;gap:5px;">
        <input type="checkbox" id="rp-auto-upload" style="accent-color:var(--green);">렌더링 후 YouTube 자동 업로드
      </label>
    </div>
    <div style="display:flex;gap:8px;margin-top:8px;">
      <button id="rp-render-all" onclick="renderBatchAll()" class="btn btn-g" style="flex:1;justify-content:center;">▶ 전체 렌더링</button>
      <button id="rp-cancel-btn" onclick="cancelBatchRender()" class="btn btn-r" style="display:none;flex:1;justify-content:center;">⏹ 렌더링 취소</button>
    </div>
  </div>
  <!-- 탭 내용: 커스텀 -->
  <div id="rp-custom" style="display:none;">
    <div class="sec">렌더링 대상</div>
    <div class="g4" style="margin-bottom:12px;">
      <div><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">시험</div>
        <select id="rc-exam" onchange="updateCustomPreview()" class="inp" style="width:100%;"><option value="TOPIK">🇰🇷 TOPIK</option><option value="TOEIC">📝 TOEIC</option><option value="JLPT">🌸 JLPT</option><option value="IELTS">🎓 IELTS</option><option value="HSK">🐉 HSK</option></select></div>
      <div><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">언어</div>
        <select id="rc-lang" onchange="updateCustomPreview()" class="inp" style="width:100%;"><option value="EN">🇺🇸 EN</option><option value="JP">🇯🇵 JP</option><option value="CN">🇨🇳 CN</option><option value="VN">🇻🇳 VN</option><option value="ES">🇪🇸 ES</option></select></div>
      <div><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">등급</div>
        <select id="rc-level" onchange="updateCustomPreview()" class="inp" style="width:100%;"><option value="1">1급</option><option value="2">2급</option><option value="3">3급</option><option value="4">4급</option><option value="5">5급</option><option value="6">6급</option></select></div>
      <div><div style="font-size:.62rem;color:var(--muted2);margin-bottom:3px;">수량</div>
        <input type="number" id="rc-count" value="10" min="1" max="30" onchange="updateCustomPreview()" oninput="updateCustomPreview()" class="inp" style="width:100%;"></div>
    </div>
    <div class="card-sm" style="margin-bottom:14px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <span style="font-size:.68rem;color:var(--muted2);font-weight:600;">ID 범위 (선택)</span>
        <span id="rc-id-range-hint" style="font-size:.6rem;color:var(--muted2);"></span>
      </div>
      <div style="display:flex;align-items:center;gap:6px;">
        <input type="number" id="rc-start-id" placeholder="시작" onchange="updateCustomPreview()" oninput="updateCustomPreview()" class="inp" style="flex:1;">
        <span style="color:var(--muted2);">~</span>
        <input type="number" id="rc-end-id" placeholder="끝" onchange="updateCustomPreview()" oninput="updateCustomPreview()" class="inp" style="flex:1;">
        <button onclick="document.getElementById('rc-start-id').value='';document.getElementById('rc-end-id').value='';updateCustomPreview();" class="btn btn-m" style="font-size:.66rem;padding:4px 8px;">초기화</button>
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
    <div class="g6" id="illust-view-levels" style="margin-bottom:14px;"></div>
    <div id="illust-view-log" style="display:none;background:var(--bg);border-radius:6px;padding:10px;font-size:.7rem;color:var(--muted);font-family:monospace;max-height:100px;overflow:auto;margin-bottom:14px;white-space:pre-wrap;"></div>
  </div>
  <div class="card">
    <div class="sec">일러스트 생성</div>
    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
      <span style="font-size:.74rem;color:var(--muted);">ID 범위:</span>
      <input id="illust-start2" class="num-input" type="number" value="1"><span style="color:var(--muted);">~</span>
      <input id="illust-end2" class="num-input" type="number" value="100">
      <select id="illust-mode2" onchange="updateIllustCost2()" class="inp"><option value="both">단어+예문</option><option value="words">🖼 단어만</option><option value="sentences">📝 예문만</option></select>
      <button id="illust-gen-btn2" onclick="startIllustGen2()" class="btn btn-a">🎨 생성</button>
      <button onclick="setIllustRange2(1,1800)" class="btn btn-m">전체</button>
      <span id="illust-cost2" style="font-size:.72rem;color:var(--amber);font-weight:600;"></span>
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

  // 진행 배지 + 게이지
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

// ── 렌더 패널 ──────────────────────────────────────────
let _rpTab='batch', _batchData=null, _configSlots=[];
let _batchChecked=new Set();
let _batchTarget='desktop', _customTarget='desktop';

function rpTab(tab){
  _rpTab=tab;
  ['batch','custom','history','config'].forEach(t=>{
    const v=document.getElementById('rp-'+t);if(v)v.style.display=t===tab?'block':'none';
    const b=document.getElementById('rp-tab-'+t);
    if(b){b.classList.toggle('on',t===tab);}
  });
  if(tab==='batch') loadBatchData();
  if(tab==='custom') updateCustomPreview();
  if(tab==='history'){const dp=document.getElementById('rp-date-pick');if(dp)dp.value=new Date().toISOString().slice(0,10);loadHistoryDate();}
  if(tab==='config') loadConfigSlots();
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
    else{_batchChecked.clear();setTimeout(loadBatchData,500);}
  }catch(e){alert('실패: '+e);}
  finally{btn.disabled=false;btn.textContent='▶ 전체 렌더링';}
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
        <span style="font-size:.6rem;" title="${w.has_illust?'일러스트 있음':'일러스트 없음'}">${w.has_illust?'🖼':'<span style="opacity:.3;">🖼</span>'}</span>
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
setInterval(loadOverview,5000);
setInterval(()=>{if(_currentView==='render'&&_rpTab==='batch')loadBatchData();},5000);
</script>


</body>
</html>"""

@app.route("/")
def index(): return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765, debug=False)
