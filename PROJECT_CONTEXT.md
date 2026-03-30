# Hellowords YouTube 자동화 프로젝트

> 이 문서는 Claude와의 대화 내용을 정리한 것으로, 새 세션에서 이어서 작업할 때 참고합니다.
> 마지막 업데이트: 2026-03-30

---

## 1. 프로젝트 개요

TOPIK(한국어능력시험) 단어 1800개를 기반으로 YouTube Shorts 영상을 자동 생성·업로드하는 시스템.
Synology NAS(Docker)에서 매일 자동 실행되며, Windows 데스크탑 GPU를 선택적으로 활용.

### 콘텐츠 구조

```
시험용 (📚)
├── TOPIK 🇰🇷  (1~6급, 언어: EN/CN/JP/VN/SP)  ← 현재 활성
├── TOEIC 📝  (LC/RC, 언어: KO/CN/JP/VN)      ← 준비 중
├── JLPT 🌸   (N5~N1, 언어: KO/EN/CN/VN)      ← 준비 중
├── IELTS 🎓  (4-5~8-9, 언어: KO/CN/JP/VN)    ← 준비 중
└── HSK 🐉    (1~6급, 언어: KO/EN/JP/VN)       ← 준비 중

여행용 (✈️)
└── EN/CN/JP/VN/SP/KO/FR/DE                    ← 준비 중
```

### 하루 분량 (기본 설정)

9개 영상/일: TOPIK × (EN, JP, SP) × (1급, 2급, 3급)
대시보드 설정 탭에서 슬롯 편집 가능 (`logs/schedule_config.json`)

---

## 2. 파일 구조 및 역할

### 핵심 파이프라인 (순서대로)

| # | 파일 | 역할 |
|---|------|------|
| 0 | `prepare_db.py` | TOPIK 원본 데이터 → `words_db.json` 변환 |
| 1 | `generate_sentences.py` | Claude API로 단어당 예문 10개 생성 |
| 2 | `generate_illustrations.py` | Imagen 4로 단어/예문 일러스트 생성 |
| 3 | `make_video.py` | 영상 렌더링 (1080×1920, 30fps) |
| 4 | `upload_youtube.py` | YouTube Data API v3로 업로드 |
| 5 | `daily_run.py` | 매일 cron으로 3→4 자동 실행 |

### 인프라

| 파일 | 역할 |
|------|------|
| `dashboard.py` | Flask 웹 대시보드 (포트 8765) |
| `desktop_render.py` | Windows GPU 렌더링 워처 (1분 폴링) |
| `start_desktop_render.bat` | Windows 시작 시 워처 자동 실행 |
| `docker-compose.yml` | NAS 서비스 정의 (bot + dashboard) |
| `docker-compose.gpu.yml` | NVIDIA GPU 오버라이드 |
| `requirements.txt` | Python 패키지 목록 |

### 데이터/설정 파일 (자동 생성)

```
data/LanguageTest/words_db.json          # 단어 DB (1800개, 예문 포함)
data/LanguageTest/illustration_prompts.json  # 커스텀 일러스트 프롬프트
logs/uploads.json                        # 업로드 기록
logs/videos_log.json                     # 영상 생성 기록 (음악 포함)
logs/progress.json                       # 실시간 렌더링 진행률
logs/render_queue.json                   # 렌더링 작업 큐
logs/render_config.json                  # {desktop_enabled: bool}
logs/batch_queue.json                    # 배치 렌더링 큐
logs/schedule_config.json                # 하루 분량 슬롯 설정
logs/illust_progress.json                # 일러스트 생성 진행률
assets/music/                            # Suno에서 만든 배경음악 (.mp3)
assets/illustrations/lv{N}/{단어}/       # 일러스트 (word.png, 0.png~9.png)
secrets/                                 # GCP 키, OAuth 토큰
output/                                  # 생성된 영상 파일
```

---

## 3. 주요 구현 사항

### 3-1. 영상 렌더링 (`make_video.py`)

- **세로 영상**: 1080×1920, 30fps
- **구성**: 단어 카드 → 예문 10개 → 아웃트로
- **발음**: 한글 문장 아래에 로마자 표기 (`korean_romanizer`)
- **음악**: `assets/music/`에서 영상 길이에 맞는 트랙 자동 선택
  - 영상 길이 ≥ 음악 → 가장 짧은 적합 트랙
  - 영상 > 모든 트랙 → 가장 긴 트랙 (aloop으로 반복)
  - FFmpeg: `aloop=loop=-1:size=2e+09,atrim=duration=TOTAL,volume=0.12`
- **GPU 가속**: `has_nvenc()` → `h264_nvenc` 자동 감지, fallback `libx264`
- **진행률**: `logs/progress.json`에 5%~100% 단계별 기록
- **로그**: `logs/videos_log.json`에 음악, 파일 크기 등 기록

### 3-2. 일러스트 (`generate_illustrations.py`)

- **2종류**: 단어 일러스트 (`word.png`) + 예문 일러스트 (`0.png`~`9.png`)
- **모드**: `--words-only`, `--sentences-only`, 기본은 둘 다 생성
- **커스텀 프롬프트**: `illustration_prompts.json` 참조 (word_prompt, sentences[])
- **스타일**: warm Korean indie lifestyle, hand-drawn outlines, flat color, ivory bg
- **비용**: $0.02/장 (Imagen 4 Fast)
- **진행률**: `logs/illust_progress.json`에 실시간 기록 (`done_word`, `done_sent`)

### 3-3. 하이브리드 렌더링 (Desktop + NAS)

```
daily_run.py (NAS cron)
  → render_queue.json에 작업 등록 (status: pending)
  → 30분 대기

desktop_render.py (Windows, 1분 폴링)
  → pending 발견 → claimed → Docker GPU 렌더링 → done

타임아웃 시:
  → NAS가 직접 libx264로 렌더링 (느리지만 확실)
```

**토글**: `render_config.json`의 `desktop_enabled` — 대시보드 헤더에서 💻/🖥 전환
데스크탑 켜져 있어도 토글 off하면 NAS로 렌더링됨

### 3-4. 대시보드 (`dashboard.py`)

**구조**: 좌측 사이드바(220px) + 메인 콘텐츠 + 우측 렌더 패널(460px 드로어)

**헤더 컨트롤**:
- 렌더링 토글: 💻 데스크탑 / 🖥 NAS
- ▶ 지금 렌더링: 우측 렌더 패널 열림
- 실시간 시계

**사이드바 메뉴**:
- 📊 전체 개요
- 📚 시험용 → TOPIK (EN/CN/JP/VN/SP 하위) / TOEIC / JLPT / IELTS / HSK
- ✈️ 여행용
- 🎬 영상 목록 / 🎨 일러스트 / ▶ YouTube

**렌더 패널 (우측 드로어)**:
- 📅 오늘 분량: 설정된 슬롯별 다음 단어 + 상태 + 개별/전체 렌더링
- 🗓 날짜별: 날짜 선택 → 그날 생성된 영상 목록
- ⚙️ 설정: 하루 분량 슬롯 편집 (시험/언어/등급 조합)

**일러스트 관리**:
- 단어/예문 일러스트 별도 진행바
- 생성 모드 선택: 단어+예문 / 단어만 / 예문만
- 등급별 현황 카드

**API 엔드포인트**:
```
GET  /api/overview              전체 대시보드 데이터
GET  /api/node?category&exam&lang  노드별 통계
GET  /api/schedule              하루 분량 설정 조회
POST /api/schedule              하루 분량 설정 저장
GET  /api/batch/today           오늘 배치 (슬롯별 다음 단어)
GET  /api/batch/date?date=      특정 날짜 영상 목록
POST /api/render                단일 렌더링
POST /api/render/batch          배치 렌더링 (전체 슬롯)
POST /api/render-config/toggle  데스크탑/NAS 토글
POST /api/illustrations/generate  일러스트 생성 (mode: both/words/sentences)
```

---

## 4. 환경 설정

### 필수 환경변수 (.env)

```env
ANTHROPIC_API_KEY=sk-ant-...      # Claude API (예문 생성)
GEMINI_API_KEY=AIza...             # Imagen 4 (일러스트)
YOUTUBE_API_KEY=AIza...            # YouTube 통계 (대시보드용)
YOUTUBE_CHANNEL_ID=UC...           # 채널 통계 (대시보드용)
```

### 필수 파일

```
secrets/gcp_service_account.json   # Google Cloud TTS + YouTube 업로드
secrets/credentials.json           # YouTube OAuth
secrets/token.pickle               # YouTube 토큰 (자동 생성)
```

### Docker 관련

```bash
# NAS에서 컨테이너 시작
sudo docker compose up -d

# 대시보드만 재시작 (코드 변경 후)
sudo docker compose restart topik-dashboard

# 패키지 변경 후 리빌드
sudo docker compose build topik-bot && sudo docker compose up -d

# GPU 렌더링 테스트 (Windows)
docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm topik-bot python3 make_video.py --id 1
```

### Windows 데스크탑 설정

1. Docker Desktop 설치 (WSL2 + NVIDIA GPU)
2. `start_desktop_render.bat`을 `shell:startup`에 등록
3. NAS Z: 드라이브 마운트 확인

---

## 5. 알려진 이슈 및 참고

### 해결된 이슈
- ~~대시보드 일러스트 통계 표시 안됨~~ → HTML 요소 ID 불일치 수정 완료
- ~~대시보드 변경 반영 안됨~~ → Flask non-debug 모드이므로 `docker compose restart` 필요
- ~~대시보드에서 render_queue 쓰기 실패~~ → 볼륨 마운트 `:ro` 제거
- ~~발음기호 영어 문장 아래에 표시~~ → 한글 문장 아래로 이동, `korean_romanizer` 사용

### 현재 상태
- TOPIK EN 데이터만 활성 (words_db.json에 1800단어 + 예문)
- 다른 시험/언어 DB는 아직 미생성 (대시보드에 "준비 중" 표시)
- 일러스트 10개 생성 완료 (ID 1~10)
- 배경음악은 Suno에서 수동 생성 → `assets/music/`에 배치
- YouTube OAuth 설정 필요 (업로드 기능)

### 비용 참고
- 일러스트: $0.02/장 (Imagen 4 Fast)
  - 단어만: 1800 × $0.02 = $36
  - 단어+예문: 1800 × 11 × $0.02 = $396
- 예문 생성: Claude API 사용량에 따라 (1회성)
- TTS: Google Cloud 무료 할당량 내

---

## 6. 다음 할 일 (TODO)

- [ ] 나머지 일러스트 생성 (ID 11~1800)
- [ ] YouTube OAuth 설정 → 자동 업로드 테스트
- [ ] Docker Desktop GPU 연동 테스트
- [ ] `start_desktop_render.bat` → Windows 시작 등록
- [ ] Suno 배경음악 생성 → `assets/music/`에 배치
- [ ] TOPIK JP/SP/CN/VN 데이터 준비
- [ ] TOEIC/JLPT/IELTS/HSK 데이터 준비
- [ ] 여행용 콘텐츠 기획 및 DB 구축

---

## 7. 대화 이력 요약

### 세션 1 (이전 대화 — 컨텍스트 압축됨)
1. 발음기호 위치 변경 (영어→한글 문장 아래) + `korean_romanizer` 적용
2. AI 배경음악 논의 → Suno 수동 생성으로 결정
3. 영상 길이에 맞는 음악 자동 선택 로직 구현
4. 로컬 대시보드 (Flask) 최초 생성
5. 대시보드 기능 확장: 시험별/나라별/등급별 현황, 영상별 음악, 차트
6. 일러스트 상태 + 생성 버튼 추가
7. 데스크탑 GPU 렌더링 논의 → RTX 4070 Ti 활용
8. 하이브리드 렌더링 구현 (desktop_render.py + render_queue.json)
9. 수동 토글 (데스크탑 on/off) 구현
10. 대시보드에서 렌더링 트리거 기능
11. 전체 UX 리디자인: 사이드바 + 콘텐츠 구조 반영

### 세션 2 (현재 대화)
1. 일러스트를 단어/예문 2종으로 분리
   - `generate_illustrations.py`: 배치 모드에서 word.png + 0~9.png 동시 생성
   - `--words-only`, `--sentences-only` 플래그 추가
   - 대시보드에 단어/예문 별도 진행바
2. 일러스트 통계 표시 버그 수정 (HTML ID 불일치)
3. 단어/예문 분리 생성 UI (모드 드롭다운)
4. 렌더 패널 구현 (우측 드로어)
   - 오늘 분량 슬롯 표시 (9개 기본)
   - 날짜별 히스토리
   - 하루 분량 설정 편집
   - `schedule_config.json`, `batch_queue.json` 추가
   - 배치 렌더링 API (`/api/render/batch`)
5. 이 문서 작성
