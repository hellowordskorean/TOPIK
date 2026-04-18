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
NAS_DRIVE           = Path("Z:/Hellowords/youtube")
QUEUE_FILE          = NAS_DRIVE / "logs" / "render_queue.json"
DESKTOP_PHRASE_Q    = NAS_DRIVE / "logs" / "desktop_phrase_queue.json"
OPEN_FOLDER_REQ_F   = NAS_DRIVE / "logs" / "open_folder_request.json"
LOG_FILE            = NAS_DRIVE / "logs" / "desktop_render.log"
LOCK_FILE           = NAS_DRIVE / "logs" / "desktop_render.lock"
POLL_INTERVAL       = 15   # 초 (15초마다 확인)
HOSTNAME            = "desktop"
RENDER_CONFIG       = NAS_DRIVE / "logs" / "render_config.json"


# ─── 단일 인스턴스 락 ─────────────────────────────────────────
def _pid_alive(pid: int) -> bool:
    """PID가 살아있는지 확인 (Windows 전용)"""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5
        )
        return str(pid) in result.stdout
    except Exception:
        return False


def acquire_lock() -> bool:
    """PID 락 파일로 단일 인스턴스 보장. 이미 실행 중이면 False 반환."""
    my_pid = os.getpid()
    if LOCK_FILE.exists():
        try:
            old_pid = int(LOCK_FILE.read_text().strip())
            if old_pid != my_pid and _pid_alive(old_pid):
                return False  # 다른 인스턴스가 실행 중
        except Exception:
            pass  # 파일 읽기 오류 → 락 덮어씀
    LOCK_FILE.write_text(str(my_pid))
    return True


def release_lock():
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception:
        pass

# Docker /app 경로 → Windows 로컬 경로 변환
def _docker_to_win(path: str) -> str:
    if path.startswith("/app/data/"):
        data_root = str(NAS_DRIVE.parent / "data") + os.sep
        return path.replace("/app/data/", data_root).replace("/", os.sep)
    if path.startswith("/app/"):
        return path.replace("/app/", str(NAS_DRIVE) + "/").replace("/", os.sep)
    return path

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
    env["PYTHONIOENCODING"] = "utf-8"
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


# ─── 폴더 열기 요청 처리 ──────────────────────────────────────
def check_open_folder():
    if not OPEN_FOLDER_REQ_F.exists():
        return
    try:
        with open(OPEN_FOLDER_REQ_F, encoding="utf-8") as f:
            req = json.load(f)
        OPEN_FOLDER_REQ_F.unlink()  # 즉시 삭제 (중복 방지)
        docker_path = req.get("path", "")
        if not docker_path:
            return
        win_path = _docker_to_win(docker_path)
        p = Path(win_path)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(["explorer", str(p)])
        log(f"📁 폴더 열기: {p}")
    except Exception as e:
        log(f"폴더 열기 오류: {e}")


# ─── 데스크탑 Phrase/Conv 큐 ─────────────────────────────────
def read_phrase_queue() -> dict:
    try:
        with open(DESKTOP_PHRASE_Q, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def write_phrase_queue(data: dict):
    DESKTOP_PHRASE_Q.parent.mkdir(parents=True, exist_ok=True)
    with open(DESKTOP_PHRASE_Q, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def handle_phrase_job(dq: dict) -> bool:
    """phrase_illust / phrase_video / conv_video / phrase_illust_regen 를 Windows에서 실행"""
    jtype  = dq.get("type")
    params = dq.get("params", {})
    python_exe = sys.executable.replace("pythonw.exe", "python.exe").replace("pythonw", "python")
    phrase_db  = _docker_to_win("/app/data/Conversation/phrases_db.json")

    if jtype == "conv_video":
        cmd = [python_exe, str(NAS_DRIVE / "make_conversation.py"),
               "--db", phrase_db,
               "--theme", str(params.get("theme_id")),
               "--lang", params.get("lang", "EN"),
               "--output", str(NAS_DRIVE / "output")]
        if params.get("fmt") == "reels":
            cmd += ["--format", "reels"]
    elif jtype == "phrase_video":
        cmd = [python_exe, str(NAS_DRIVE / "make_video_phrases.py"),
               "--db", phrase_db,
               "--output", str(NAS_DRIVE / "output" / "phrases")]
        sit_id = params.get("sit_id")
        start  = params.get("start")
        end    = params.get("end")
        if sit_id is not None:
            cmd += ["--id", str(sit_id)]
        elif start is not None and end is not None:
            cmd += ["--start", str(start), "--end", str(end)]
    elif jtype in ("phrase_illust", "phrase_illust_regen"):
        cmd = [python_exe, str(NAS_DRIVE / "generate_phrase_illustrations.py"),
               "--db", phrase_db]
        sit_id = params.get("sit_id")
        start  = params.get("start")
        end    = params.get("end")
        key    = params.get("key")
        if sit_id is not None:
            cmd += ["--situation-id", str(sit_id)]
            if key == "intro":
                cmd += ["--intro-only"]
            if jtype == "phrase_illust_regen" and key:
                file_to_del = NAS_DRIVE / "assets" / "phrase_illustrations" / f"sit_{sit_id}" / f"{key}.png"
                if file_to_del.exists():
                    try:
                        file_to_del.unlink()
                        log(f"[regen] 기존 파일 삭제: {file_to_del.name}")
                    except Exception as e:
                        log(f"[regen] 파일 삭제 실패: {file_to_del}: {e}")
        elif start is not None and end is not None:
            cmd += ["--start", str(start), "--end", str(end)]
    elif jtype == "illust":
        words_db = str(NAS_DRIVE.parent / "data" / "LanguageTest" / "words_db.json")
        start    = params.get("start", 1)
        end      = params.get("end", 10)
        mode     = params.get("mode", "both")
        cmd = [python_exe, str(NAS_DRIVE / "generate_illustrations.py"),
               "--db", words_db, "--start", str(start), "--end", str(end)]
        if mode == "words":
            cmd.append("--words-only")
        elif mode == "sentences":
            cmd.append("--sentences-only")
    else:
        log(f"알 수 없는 작업 타입: {jtype}")
        return False

    log(f"[{jtype}] 시작: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, cwd=str(NAS_DRIVE), env=_get_env(),
            timeout=7200
        )
        if result.returncode == 0:
            log(f"[{jtype}] 완료")
            return True
        else:
            log(f"[{jtype}] 실패 (returncode={result.returncode})")
            if result.stderr:
                log(f"오류: {result.stderr[-500:]}")
            return False
    except subprocess.TimeoutExpired:
        log(f"[{jtype}] 2시간 초과 (timeout)")
        return False
    except Exception as e:
        log(f"[{jtype}] 예외: {e}")
        return False


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
    proc = subprocess.Popen(cmd, cwd=str(NAS_DRIVE), env=_get_env())
    # 렌더링 중 2초마다 취소 신호 확인
    while proc.poll() is None:
        time.sleep(2)
        rq = read_queue()
        if rq.get("status") in ("cancelled", "failed"):
            log(f"취소 신호 감지 — 렌더링 프로세스 강제 종료")
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
            return False
    if proc.returncode == 0:
        log(f"렌더링 완료: word_id={word_id}")
        return True
    else:
        log(f"렌더링 실패: returncode={proc.returncode}")
        return False


# ─── 메인 루프 ───────────────────────────────────────────────
def main():
    if not acquire_lock():
        print(f"[desktop_render] 이미 실행 중인 인스턴스가 있습니다. 종료합니다.")
        sys.exit(0)

    try:
        _main_loop()
    finally:
        release_lock()


def _main_loop():
    log("=" * 50)
    log("데스크탑 렌더링 워처 시작")
    log(f"단어 큐: {QUEUE_FILE}")
    log(f"회화/일러스트 큐: {DESKTOP_PHRASE_Q}")
    log(f"폴링 간격: {POLL_INTERVAL}초")
    log("=" * 50)

    while True:
        try:
            enabled = is_desktop_enabled()

            # ── 1) 단어 영상 큐 (render_queue.json) ──────────────
            if QUEUE_FILE.exists():
                q = read_queue()
                if q.get("status") == "pending":
                    if not enabled:
                        log("데스크탑 렌더링 비활성화 상태 — 단어 큐 패스")
                    else:
                        word_id = q.get("word_id")
                        db_path = q.get("db_path", "/app/data/LanguageTest/words_db.json")
                        exam = q.get("exam", "TOPIK")
                        lang = q.get("lang", "EN")
                        fmt  = q.get("fmt", "youtube")
                        log(f"단어 작업 발견: word_id={word_id} ({exam}/{lang}/{fmt})")
                        if claim_job(q):
                            success = render(word_id, db_path, exam, lang, fmt)
                            q = read_queue()
                            if success:
                                mark_done(q)
                                log(f"완료: word_id={word_id}")
                            else:
                                mark_failed(q, "렌더링 실패")
                elif q.get("status") == "claimed" and q.get("claimed_by") == HOSTNAME:
                    log(f"이전 작업이 claimed 상태로 남아있음 (word_id={q.get('word_id')}) - 재시도")
                    q["status"] = "pending"
                    q["claimed_by"] = None
                    write_queue(q)

            # ── 2) 회화/일러스트 큐 (desktop_phrase_queue.json) ──
            if DESKTOP_PHRASE_Q.exists():
                dq = read_phrase_queue()
                if dq.get("status") == "pending":
                    if not enabled:
                        log("데스크탑 렌더링 비활성화 상태 — Phrase 큐 패스")
                    else:
                        jtype  = dq.get("type", "?")
                        job_id = dq.get("job_id", "?")
                        log(f"Phrase 작업 발견: {jtype} (job_id={job_id})")
                        dq["status"]     = "claimed"
                        dq["claimed_by"] = HOSTNAME
                        dq["claimed_at"] = datetime.now().isoformat()
                        write_phrase_queue(dq)
                        try:
                            success = handle_phrase_job(dq)
                            dq = read_phrase_queue()
                            if success:
                                dq["status"]       = "done"
                                dq["completed_at"] = datetime.now().isoformat()
                            else:
                                dq["status"]       = "failed"
                                dq["error"]        = "처리 실패 (로그 확인)"
                                dq["completed_at"] = datetime.now().isoformat()
                            write_phrase_queue(dq)
                            log(f"Phrase 작업 {'완료' if success else '실패'}: {jtype}")
                        except Exception as e:
                            dq["status"]       = "failed"
                            dq["error"]        = str(e)
                            dq["completed_at"] = datetime.now().isoformat()
                            write_phrase_queue(dq)
                            log(f"Phrase 작업 예외: {e}")
                elif dq.get("status") == "claimed" and dq.get("claimed_by") == HOSTNAME:
                    log(f"이전 Phrase 작업 claimed 상태 남아있음 - 재시도")
                    dq["status"]     = "pending"
                    dq["claimed_by"] = None
                    write_phrase_queue(dq)

            # ── 3) 폴더 열기 요청 확인 ───────────────────────────
            check_open_folder()

            # ── 4) YouTube 토큰 주기적 갱신 (45분마다) ───────────
            _refresh_youtube_tokens_if_needed()

        except KeyboardInterrupt:
            log("워처 종료")
            break
        except Exception as e:
            log(f"오류: {e}")

        time.sleep(POLL_INTERVAL)


_last_token_refresh = 0.0

def _refresh_youtube_tokens_if_needed():
    """YouTube OAuth 토큰을 45분마다 갱신 (access_token 1시간 만료 대응)"""
    global _last_token_refresh
    now = time.time()
    if now - _last_token_refresh < 45 * 60:
        return
    _last_token_refresh = now
    try:
        import pickle
        sys.path.insert(0, str(NAS_DRIVE))
        from google.auth.transport.requests import Request
        from google.auth.exceptions import RefreshError
        tokens_dir = NAS_DRIVE / "secrets" / "tokens"
        refreshed, failed = [], []
        for token_file in tokens_dir.glob("token_*.pickle"):
            lang = token_file.stem.replace("token_", "")
            try:
                with open(token_file, "rb") as f:
                    creds = pickle.load(f)
                if not creds.valid:
                    creds.refresh(Request())
                    with open(token_file, "wb") as f:
                        pickle.dump(creds, f)
                    refreshed.append(lang)
            except RefreshError:
                failed.append(lang)
            except Exception:
                pass
        if refreshed:
            log(f"[token] 갱신 완료: {', '.join(refreshed)}")
        if failed:
            log(f"[token] 갱신 실패 (재인증 필요): {', '.join(failed)}")
    except Exception as e:
        log(f"[token] 갱신 오류: {e}")


def install_startup():
    """Windows 작업 스케줄러에 로그인 시 자동 실행 등록"""
    import shutil
    script = Path(__file__).resolve()
    pythonw = Path(sys.executable).parent / "pythonw.exe"
    if not pythonw.exists():
        pythonw = Path(sys.executable)  # 없으면 python.exe 사용

    task_name = "HellowordsDesktopRender"
    xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <LogonTrigger><Enabled>true</Enabled></LogonTrigger>
  </Triggers>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions>
    <Exec>
      <Command>{pythonw}</Command>
      <Arguments>"{script}"</Arguments>
      <WorkingDirectory>{script.parent}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

    xml_path = Path(os.environ.get("TEMP", ".")) / "hw_render_task.xml"
    xml_path.write_text(xml, encoding="utf-16")
    result = subprocess.run(
        ["schtasks", "/Create", "/F", "/TN", task_name, "/XML", str(xml_path)],
        capture_output=True, text=True
    )
    xml_path.unlink(missing_ok=True)
    if result.returncode == 0:
        print(f"[OK] 작업 스케줄러 등록 완료: {task_name}")
        print(f"     다음 로그인부터 자동으로 백그라운드 실행됩니다.")
    else:
        print(f"[ERROR] 등록 실패: {result.stderr.strip()}")
        print("       관리자 권한으로 다시 실행해보세요.")


def uninstall_startup():
    """작업 스케줄러에서 제거"""
    task_name = "HellowordsDesktopRender"
    result = subprocess.run(
        ["schtasks", "/Delete", "/F", "/TN", task_name],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"[OK] 작업 스케줄러에서 제거됨: {task_name}")
    else:
        print(f"[ERROR] 제거 실패: {result.stderr.strip()}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--install":
            install_startup()
        elif sys.argv[1] == "--uninstall":
            uninstall_startup()
        else:
            print(f"알 수 없는 옵션: {sys.argv[1]}")
            print("사용법: python desktop_render.py [--install | --uninstall]")
    else:
        main()
