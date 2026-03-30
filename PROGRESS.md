# TOPIK YouTube 자동화 — 작업 진행 기록

## 프로젝트 개요
- TOPIK 단어 1800개(Lv.1~6) → 매일 1개씩 YouTube Shorts 영상 자동 생성·업로드
- 스택: Python + Docker (Synology NAS), Google Cloud TTS, YouTube Data API v3, Google Imagen 4
- NAS 경로: `/volume1/docker/Hellowords/youtube/`
- Windows 드라이브: `Z:\Hellowords\youtube\`

---

## 파일 구조

```
youtube/
├── make_video.py          # 영상 생성 (핵심)
├── generate_illustrations.py  # Imagen 4로 일러스트 생성
├── prepare_db.py          # 원본 TOPIK JSON → words_db.json 변환
├── upload_youtube.py      # YouTube 업로드
├── daily_run.py           # 매일 실행 스케줄러
├── generate_sentences.py  # (미사용)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env                   # API 키 (ANTHROPIC, GEMINI)
├── crontab
├── data/
│   ├── words_db.json      # 변환된 단어 DB (1800개, situation 포함)
│   └── TOPIK/EN/          # 원본 데이터 topik_1.json ~ topik_6.json
├── assets/
│   └── illustrations/     # 생성된 일러스트 PNG
│       ├── lv1/           # 급수별 폴더
│       │   └── 가게/      # 단어별 폴더
│       │       ├── word.png   # 단어 일러스트
│       │       └── 0~9.png    # 예문 일러스트
│       ├── lv2/
│       └── lv3~lv6/
├── output/                # 생성된 영상 MP4
├── logs/
└── secrets/
    └── gcp_service_account.json
```

---

## 데이터 구조

### 원본 (`data/TOPIK/EN/topik_1.json`)
```json
{
  "level": 1,
  "words": [
    {
      "id": 1,
      "word": "가게",
      "pos": "명사",
      "meaning": "store, shop",
      "examples": [
        {
          "situation": "When buying an item",
          "ko": "이 가게에서 과일을 팔아요.",
          "en": "This store sells fruit."
        }
      ]
    }
  ]
}
```

### 변환 후 (`data/words_db.json`)
```json
{
  "id": 1,
  "word": "가게",
  "romanization": "gage",
  "meaning": "store, shop",
  "part_of_speech": "명사",
  "level": 1,
  "sentences": [
    {
      "situation": "When buying an item",
      "ko": "이 가게에서 과일을 팔아요.",
      "en": "This store sells fruit."
    }
  ]
}
```

---

## 영상 스펙
- 해상도: **1080×1920** (YouTube Shorts 세로)
- FPS: 30
- 오디오: Google Cloud TTS (ko-KR-Neural2-A, en-US-Neural2-F)

---

## 현재 레이아웃 디자인 (라이트 테마)

### 색상 팔레트
```python
"bg":            (248, 242, 234)  # 크림 배경
"card_bg":       (255, 255, 255)  # 흰 카드
"accent":        (50,  92,  200)  # 파란색 (단어, 하이라이트)
"accent_warm":   (108,  60,  58)  # 다크 마룬 (TOPIK 헤더)
"accent_pink":   (220, 155, 155)  # 소프트 핑크 (비활성 도트)
"text_primary":  (38,   32,  30)  # 거의 검정 (한국어 예문)
"text_secondary":(108,  96,  90)  # 중간 회색 (영어)
"text_muted":    (158, 148, 142)  # 연한 회색 (#상황)
"divider":       (215, 205, 198)  # 구분선
```

### 단어 카드 (첫 페이지) — `draw_word_card()`
```
[크림 배경]
┌──────────────────────────────┐ y=80 흰 카드 h=760
│   TOPIK  LV.1                │ 마룬 bold 34px
│   001                        │ 마룬 28px
│   ─────────                  │ 구분선
│   명사                        │ 회색 34px
│                              │
│        가게                   │ 파란색 bold 190px
│      [ gage ]                │ 파란색 38px
│   ────────────               │ 구분선
│     store, shop              │ 그레이 이탤릭 48px
└──────────────────────────────┘ y=840

[크림 배경 위 일러스트 — 정사각형 1:1]
     ╭──────────────╮  y=890
     │  일러스트 PNG  │  ~950×950 (가용 공간 내 최대)
     ╰──────────────╯
```

### 예문 카드 — `draw_sentence_card()`
```
[크림 배경]
[가게] LV.1 - 001   ●●●●●○○○○○   y=52 (파란 pill + 도트)

╭──────────────────────────────╮ y=152 흰 카드 (일러스트)
│     일러스트 PNG 860×860       │ 1:1 정사각형
╰──────────────────────────────╯ y=1012

#When buying an item           y=1056 (회색 muted)

이 가게에서 과일을 팔아요        y=~1174 (bold 82px, 가게=파란색)

This store sells fruit.        y=~1374 (46px, store=파란색)
```

### 아웃트로 — `draw_outro()`
```
[크림 배경]
┌──────────────────────────────┐ y=480 흰 카드
│  TOPIK LV.1 · 001            │
│  ──────                      │
│         가게                  │ 파란색 180px
│   = store, shop              │ 그레이 50px
└──────────────────────────────┘ y=1060
  Like & Subscribe...          y=1120
```

---

## 일러스트 생성 (`generate_illustrations.py`)

### 단어 일러스트 (기본)
```bash
# ID 1~10 단어 일러스트 생성
sudo docker compose run --rm topik-bot python3 generate_illustrations.py --start 1 --end 10

# 전체 1800개 ($36)
sudo docker compose run --rm topik-bot python3 generate_illustrations.py
```
- 저장: `assets/illustrations/{단어}.png`
- 비용: $0.02/장

### 예문별 일러스트 (선택)
```bash
# ID=1 단어의 예문 10개 생성 ($0.20)
sudo docker compose run --rm topik-bot python3 generate_illustrations.py --sentences-for-id 1
```
- 저장: `assets/illustrations/{단어}_{인덱스}.png` (예: `가게_0.png`)
- 프롬프트: situation + 영어 예문 조합
- 없으면 단어 일러스트로 fallback

---

## 배경 우선순위 (`get_background()`)
1. `{단어}/{예문인덱스}.png` — 예문별 일러스트
2. `{단어}/word.png` — 단어 일러스트
3. `None` → 크림 단색 배경

---

## 실행 명령어

### DB 재생성 (situation 필드 포함)
```bash
cd /volume1/docker/Hellowords/youtube
sudo docker compose run --rm topik-bot python3 prepare_db.py
```

### 영상 테스트
```bash
sudo docker compose run --rm topik-bot python3 make_video.py \
  --db /app/data/words_db.json --id 1 --output /app/output/
```

### Docker 이미지 재빌드 (requirements.txt 변경 시)
```bash
sudo docker compose build topik-bot
```

### 전체 자동화 시작 (cron)
```bash
sudo docker compose up -d
```

---

## 해결된 주요 오류들

| 오류 | 원인 | 해결 |
|------|------|------|
| `supercronic` apt 설치 실패 | Debian 패키지 아님 | apt 목록에서 제거 (curl로 별도 설치) |
| `assets` 볼륨 마운트 실패 | 폴더 미생성 | `mkdir -p .../assets` |
| TTS `ko-KR-Neural2-C is male` | 잘못된 보이스 이름 | `Neural2-C` → `Neural2-A` |
| FFmpeg `[0:a] matches no streams` | 입력 인덱스 오류 | silence=[1:a], 오디오=[a_idx+2:a] |
| 한국어+영어 동시 재생 | 동일 adelay | audio_timeline 분리, EN=KO+0.8s |
| POS □□ 박스 표시 | 영어 폰트로 한국어 렌더링 | `english` → `korean` 폰트 |
| `negative_prompt` API 오류 | Imagen에서 미지원 | 파라미터 제거 |
| `ImportError: google.genai` | 이미지 미설치 | `docker compose build` |
| `--db` 인자 누락 | 터미널 줄바꿈 | `cd` 후 짧은 명령어 사용 |

---

## 남은 작업

- [ ] 영상 최종 확인 (현재 라이트 테마 레이아웃)
- [ ] 일러스트 1800개 전체 생성 (~$36)
- [ ] YouTube 업로드 설정 (OAuth 토큰, 채널 설정)
- [ ] cron 자동화 테스트 (`daily_run.py`)
- [ ] 아웃트로 개선 (구독 CTA 디자인)
- [ ] 예문 일러스트 전체 생성 여부 결정 (~$360)

---

## 폰트 경로 (Docker 컨테이너 내부)
```
/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf  # korean_bold
/usr/share/fonts/truetype/nanum/NanumGothic.ttf       # korean
/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf       # english
/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf  # english_bold
```

---

## API 키 위치
- `.env` 파일: `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`
- GCP 서비스 계정: `secrets/gcp_service_account.json`
