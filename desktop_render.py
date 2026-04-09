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

# FFmpeg 경로 (winget 설치 위치)
_FFMPEG_DIR = Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
_FFMPEG_BIN = None
for p in _FFMPEG_DIR.glob("Gyan.FFmpeg*/ffmpeg*/bin"):
    if (p / "ffmpeg.exe").exists():
        _FFMPEG_BIN = str(p)
        break

def _get_env():
    """FFmpeg 경로 + APP_BASE + GCP 인증을 환경변수에 추가"""
    env = os.environ.copy()
    if _FFMPEG_BIN:
        env["PATH"] = _FFMPEG_BIN + os.pathsep + env.get("PATH", "")
    env["APP_BASE"] = str(NAS_DRIVE)
    # GCP 서비스 계정 인증 (TTS 등)
    gcp_key = NAS_DRIVE / "secrets" / "gcp_service_account.json"
    if gcp_key.exists():
        env["GOOGLE_APPLICATION_CREDENTIALS"] = str(gcp_key)
    return env


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
def render(word_id: int, db_path: str, exam: str = "TOPIK", lang: str = "EN", fmt: str = "youtube") -> bool:
    # Docker 컨테이너 경로 → 로컬 경로 변환
    # /app/data/ → Z:\Hellowords\data\ (공유 데이터는 youtube 상위 폴더)
    local_db = db_path.replace("/app/data/", str(NAS_DRIVE.parent / "data") + "/").replace("/app/", str(NAS_DRIVE) + "/").replace("/", os.sep)
    if not Path(local_db).exists():
        # fallback: 기본 DB 경로
        local_db = str(NAS_DRIVE.parent / "data" / "LanguageTest" / "words_db.json")
    local_output = str(NAS_DRIVE / "output")

    # pythonw.exe는 stdout/stderr=None이라 make_video.py가 즉시 충돌함
    # → python.exe를 명시적으로 사용
    python_exe = sys.executable.replace("pythonw.exe", "python.exe").replace("pythonw", "python")

    cmd = [
        python_exe, str(NAS_DRIVE / "make_video.py"),
        "--db", local_db,
        "--id", str(word_id),
        "--output", local_output,
        "--exam", exam,
        "--lang", lang,
        "--format", fmt,
    ]
    log(f"렌더링 시작: word_id={word_id}  (native Python + FFmpeg)")
    log(f"명령어: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(NAS_DRIVE), env=_get_env(),
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode == 0:
        log(f"렌더링 완료: word_id={word_id}")
        return True
    else:
        log(f"렌더링 실패: returncode={result.returncode}")
        if result.stderr:
            log(f"오류 내용: {result.stderr[-500:]}")
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
                exam = q.get("exam", "TOPIK")
                lang = q.get("lang", "EN")
                fmt  = q.get("fmt", "youtube")
                log(f"대기 중인 작업 발견: word_id={word_id} ({exam}/{lang}/{fmt})")

                if claim_job(q):
                    success = render(word_id, db_path, exam, lang, fmt)
                    q = read_queue()  # 다시 읽기 (NAS가 중간에 변경했을 수 있음)
                    if success:
                        mark_done(q)
                        log(f"완료 처리: word_id={word_id}")
                    else:
                        mark_failed(q, "렌더링 실패")
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
