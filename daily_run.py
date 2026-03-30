#!/usr/bin/env python3
"""
STEP 4: 마스터 자동화 스크립트 (매일 cron으로 실행)
- 오늘의 단어 선택
- 영상 생성
- 유튜브 업로드
- 로그 기록

cron 설정 예시 (매일 오전 6시 실행):
0 6 * * * cd /opt/topik_youtube && python daily_run.py >> logs/cron.log 2>&1
"""

import json
import os
import sys
import time
import tempfile
import traceback
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ─── 설정 ────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "LanguageTest" / "words_db.json"
LOG_PATH = BASE_DIR / "logs" / "uploads.json"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"
QUEUE_FILE = BASE_DIR / "logs" / "render_queue.json"

# 유튜브 업로드 예약 (실행 후 N시간 뒤 공개)
PUBLISH_DELAY_HOURS = 3   # 오전 6시 실행 → 오전 9시 공개

# 데스크탑 렌더링 대기 시간 (초)
# 이 시간 안에 데스크탑이 클레임하지 않으면 NAS가 직접 렌더링
DESKTOP_TIMEOUT = 30 * 60  # 30분

# ─── 헬퍼 ────────────────────────────────────────────────────
def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    
    LOG_DIR.mkdir(exist_ok=True)
    with open(LOG_DIR / "daily_run.log", "a") as f:
        f.write(line + "\n")

def load_log() -> dict:
    if LOG_PATH.exists():
        with open(LOG_PATH) as f:
            return json.load(f)
    return {"uploaded": [], "last_day": 0, "last_word_id": 0}

def pick_today_word(db: list, upload_log: dict) -> dict:
    """오늘 업로드할 단어 선택 (마지막 업로드 다음 단어)"""
    last_word_id = upload_log.get("last_word_id", 0)
    
    # id 순 정렬
    db_sorted = sorted(db, key=lambda w: w["id"])
    
    # 마지막 단어 이후 단어 찾기
    for word in db_sorted:
        if word["id"] > last_word_id:
            return word
    
    # 모두 완료 시 처음부터 (순환)
    log("⚠️ 모든 단어 완료, 처음부터 재시작")
    return db_sorted[0]

def write_queue(data: dict):
    QUEUE_FILE.parent.mkdir(exist_ok=True)
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def read_queue() -> dict:
    try:
        with open(QUEUE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def wait_for_render(word_id: int) -> str:
    """데스크탑이 렌더링해주길 기다림. 타임아웃 시 'nas' 반환, 완료 시 'done' 반환"""
    log(f"데스크탑 렌더링 대기 중... (최대 {DESKTOP_TIMEOUT//60}분)")
    deadline = datetime.now().timestamp() + DESKTOP_TIMEOUT
    while datetime.now().timestamp() < deadline:
        time.sleep(30)
        q = read_queue()
        status = q.get("status")
        claimed_by = q.get("claimed_by", "")
        if status == "done":
            log(f"데스크탑({claimed_by})이 렌더링 완료!")
            return "done"
        if status == "claimed":
            remaining = int((deadline - datetime.now().timestamp()) / 60)
            log(f"데스크탑이 렌더링 중... (남은 대기: {remaining}분)")
    log(f"{DESKTOP_TIMEOUT//60}분 경과 — NAS가 직접 렌더링합니다")
    return "nas"


def send_notification(msg: str):
    """슬랙/텔레그램 알림 (선택사항)"""
    # 텔레그램 예시:
    # TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    # TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
    # if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
    #     import requests
    #     requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
    #                   data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    pass

# ─── 메인 ────────────────────────────────────────────────────
def main():
    log("=" * 50)
    log("TOPIK 유튜브 자동화 시작")
    
    # 환경 변수 체크
    required_env = ["GOOGLE_APPLICATION_CREDENTIALS", "ANTHROPIC_API_KEY"]
    for env in required_env:
        if not os.environ.get(env):
            log(f"⚠️ 환경변수 없음: {env} (계속 진행)")
    
    # DB 로드
    if not DB_PATH.exists():
        log(f"❌ 단어 DB 없음: {DB_PATH}")
        sys.exit(1)
    
    with open(DB_PATH) as f:
        db = json.load(f)
    log(f"단어 DB 로드: {len(db)}개")
    
    # 오늘 단어 선택
    upload_log = load_log()
    word = pick_today_word(db, upload_log)
    log(f"오늘의 단어: {word['word']} = {word['meaning']} (ID: {word['id']})")
    
    # 이미 오늘 업로드했는지 확인
    today_str = datetime.now().strftime("%Y-%m-%d")
    already_done = any(
        u.get("uploaded_at", "").startswith(today_str)
        for u in upload_log.get("uploaded", [])
    )
    if already_done:
        log("⚠️ 오늘 이미 업로드 완료. 종료.")
        return
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / f"topik_{word['id']:04d}_{word['word']}.mp4"
    
    success = False
    try:
        # Step 1: 렌더링 — 데스크탑 우선, 타임아웃 시 NAS
        log("렌더링 작업 등록 중...")
        write_queue({
            "word_id":    word["id"],
            "db_path":    "/app/data/LanguageTest/words_db.json",
            "status":     "pending",
            "claimed_by": None,
            "claimed_at": None,
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
        })

        render_result = wait_for_render(word["id"])

        if render_result == "nas":
            # 데스크탑 미응답 → NAS 직접 렌더링
            log("NAS 직접 렌더링 시작...")
            write_queue({**read_queue(), "status": "claimed", "claimed_by": "nas", "claimed_at": datetime.now().isoformat()})
            with tempfile.TemporaryDirectory() as tmpdir:
                sys.path.insert(0, str(BASE_DIR))
                from make_video import create_video
                create_video(word, str(output_path), tmpdir)
            write_queue({**read_queue(), "status": "done", "completed_at": datetime.now().isoformat()})

        log(f"영상 생성 완료: {output_path}")
        
        # Step 2: 유튜브 업로드
        log("유튜브 업로드 시작...")
        from upload_youtube import (
            get_youtube_client, generate_metadata,
            upload_video, load_upload_log, save_upload_log
        )
        
        day_number = upload_log["last_day"] + 1
        metadata = generate_metadata(word, day_number, lang="EN")
        
        publish_at = None
        if PUBLISH_DELAY_HOURS > 0:
            publish_at = datetime.now(timezone.utc) + timedelta(hours=PUBLISH_DELAY_HOURS)
        
        youtube = get_youtube_client()
        thumb_path = str(output_path).rsplit(".", 1)[0] + "_thumb.png"
        video_id = upload_video(youtube, str(output_path), metadata,
                                publish_at=publish_at,
                                thumbnail_path=thumb_path if os.path.exists(thumb_path) else None)
        
        # Step 3: 로그 업데이트
        upload_log["last_day"] = day_number
        upload_log["last_word_id"] = word["id"]
        upload_log["uploaded"].append({
            "day": day_number,
            "word_id": word["id"],
            "word": word["word"],
            "meaning": word["meaning"],
            "video_id": video_id,
            "youtube_url": f"https://youtube.com/watch?v={video_id}",
            "uploaded_at": datetime.now().isoformat(),
            "publish_at": publish_at.isoformat() if publish_at else "immediate",
        })
        save_upload_log(upload_log, str(LOG_PATH))
        
        success = True
        msg = f"✅ Day #{day_number}: {word['word']} = {word['meaning']}\nhttps://youtube.com/watch?v={video_id}"
        log(msg)
        send_notification(msg)
        
        # 영상 파일 정리 (디스크 절약, 선택사항)
        # os.remove(output_path)
        
    except Exception as e:
        error_msg = f"❌ 오류 발생: {e}\n{traceback.format_exc()}"
        log(error_msg)
        send_notification(f"TOPIK 자동화 오류!\n{word['word']}\n{str(e)[:200]}")
        sys.exit(1)
    
    log(f"완료! 성공: {success}")
    log("=" * 50)


if __name__ == "__main__":
    main()
