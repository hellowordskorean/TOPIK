#!/usr/bin/env python3
"""
데스크탑 렌더링 워처 (Windows에서 실행)
- Z:\Hellowords\youtube\logs\render_queue.json 를 1분마다 확인
- 대기 중인 작업이 있으면 GPU로 렌더링
- Windows 시작 시 자동 실행: start_desktop_render.bat 등록

실행:
  pythonw desktop_render.py   (백그라운드 실행, 창 없음)
  python desktop_render.py    (터미널에서 확인용)
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ─── 설정 ────────────────────────────────────────────────────
NAS_DRIVE      = Path("Z:/Hellowords/youtube")
QUEUE_FILE     = NAS_DRIVE / "logs" / "render_queue.json"
LOG_FILE       = NAS_DRIVE / "logs" / "desktop_render.log"
POLL_INTERVAL  = 60   # 초 (1분마다 확인)
HOSTNAME       = "desktop"
RENDER_CONFIG  = NAS_DRIVE / "logs" / "render_config.json"

DOCKER_CMD_BASE = [
    "docker", "compose",
    "-f", str(NAS_DRIVE / "docker-compose.yml"),
    "-f", str(NAS_DRIVE / "docker-compose.gpu.yml"),
    "run", "--rm", "topik-bot",
    "python3", "make_video.py",
    "--output", "/app/output/",
]


# ─── 로그 ────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [desktop] {msg}"
    print(line)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ─── 큐 조작 ─────────────────────────────────────────────────
def is_desktop_enabled() -> bool:
    """대시보드에서 데스크탑 렌더링이 활성화됐는지 확인"""
    try:
        with open(RENDER_CONFIG, encoding="utf-8") as f:
            return json.load(f).get("desktop_enabled", True)
    except Exception:
        return True  # 파일 없으면 기본값 활성화


def read_queue() -> dict:
    try:
        with open(QUEUE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def write_queue(data: dict):
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def claim_job(q: dict) -> bool:
    """작업을 데스크탑이 가져감"""
    if q.get("status") != "pending":
        return False
    q["status"]     = "claimed"
    q["claimed_by"] = HOSTNAME
    q["claimed_at"] = datetime.now().isoformat()
    write_queue(q)
    return True

def mark_done(q: dict):
    q["status"]       = "done"
    q["completed_at"] = datetime.now().isoformat()
    write_queue(q)

def mark_failed(q: dict, reason: str):
    q["status"]       = "failed"
    q["error"]        = reason
    q["completed_at"] = datetime.now().isoformat()
    write_queue(q)


# ─── 렌더링 ──────────────────────────────────────────────────
def render(word_id: int, db_path: str) -> bool:
    cmd = DOCKER_CMD_BASE + [
        "--db", db_path,
        "--id", str(word_id),
    ]
    log(f"렌더링 시작: word_id={word_id}  GPU(h264_nvenc)")
    log(f"명령어: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(NAS_DRIVE))
    if result.returncode == 0:
        log(f"렌더링 완료: word_id={word_id}")
        return True
    else:
        log(f"렌더링 실패: returncode={result.returncode}")
        return False


# ─── 메인 루프 ───────────────────────────────────────────────
def main():
    log("=" * 50)
    log("데스크탑 렌더링 워처 시작")
    log(f"큐 파일: {QUEUE_FILE}")
    log(f"폴링 간격: {POLL_INTERVAL}초")
    log("=" * 50)

    while True:
        try:
            if not QUEUE_FILE.exists():
                time.sleep(POLL_INTERVAL)
                continue

            q = read_queue()

            if q.get("status") == "pending":
                if not is_desktop_enabled():
                    log("데스크탑 렌더링 비활성화 상태 — NAS에 위임")
                    time.sleep(POLL_INTERVAL)
                    continue

                word_id = q.get("word_id")
                db_path = q.get("db_path", "/app/data/LanguageTest/words_db.json")
                log(f"대기 중인 작업 발견: word_id={word_id}")

                if claim_job(q):
                    success = render(word_id, db_path)
                    q = read_queue()  # 다시 읽기 (NAS가 중간에 변경했을 수 있음)
                    if success:
                        mark_done(q)
                        log(f"완료 처리: word_id={word_id}")
                    else:
                        mark_failed(q, "Docker 렌더링 실패")
            elif q.get("status") == "claimed" and q.get("claimed_by") == HOSTNAME:
                log(f"이전 작업이 claimed 상태로 남아있음 (word_id={q.get('word_id')}) - 재시도")
                q["status"] = "pending"
                q["claimed_by"] = None
                write_queue(q)

        except KeyboardInterrupt:
            log("워처 종료")
            break
        except Exception as e:
            log(f"오류: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
