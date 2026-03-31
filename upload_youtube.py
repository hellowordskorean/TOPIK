#!/usr/bin/env python3
"""
STEP 3: 유튜브 자동 업로드
- YouTube Data API v3 사용
- 제목/설명/태그 자동 생성
- 예약 발행 지원

사전 준비:
1. Google Cloud Console에서 YouTube Data API v3 활성화
2. OAuth 2.0 자격증명 생성 → credentials.json 저장
3. pip install google-auth google-auth-oauthlib google-api-python-client
"""

import json
import os
import sys
import io
import pickle
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Windows cp949 인코딩 문제 방지
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube",
          "https://www.googleapis.com/auth/youtube.upload"]
SECRETS_DIR = os.path.join(os.path.dirname(__file__) or ".", "secrets")
CREDENTIALS_FILE = os.path.join(SECRETS_DIR, "credentials.json")
CHANNELS_FILE = os.path.join(SECRETS_DIR, "youtube_channels.json")
PLAYLISTS_FILE = os.path.join(SECRETS_DIR, "youtube_playlists.json")

def _token_path_for_lang(lang: str = "EN") -> str:
    """언어별 토큰 파일 경로 반환"""
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, encoding="utf-8") as f:
            channels = json.load(f)
        entry = channels.get(lang, {})
        rel = entry.get("token", f"tokens/token_{lang}.pickle")
        return os.path.join(SECRETS_DIR, rel)
    return os.path.join(SECRETS_DIR, "tokens", f"token_{lang}.pickle")

# ─── 인증 ────────────────────────────────────────────────────
def get_youtube_client(lang: str = "EN"):
    """언어별 YouTube 채널 클라이언트 반환"""
    token_file = _token_path_for_lang(lang)
    creds = None
    if os.path.exists(token_file):
        with open(token_file, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print(f"  [{lang}] YouTube 인증 필요 - 브라우저에서 로그인하세요")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)
        os.makedirs(os.path.dirname(token_file), exist_ok=True)
        with open(token_file, "wb") as f:
            pickle.dump(creds, f)

    return build("youtube", "v3", credentials=creds)

# ─── 재생목록 관리 ──────────────────────────────────────────
PLAYLIST_TITLES = {
    "EN": "TOPIK Level {level} - Korean Vocabulary",
    "JP": "TOPIK {level}級 - 韓国語単語",
    "CN": "TOPIK {level}级 - 韩语词汇",
    "VN": "TOPIK Cấp {level} - Từ vựng tiếng Hàn",
    "ES": "TOPIK Nivel {level} - Vocabulario coreano",
}

PLAYLIST_DESCS = {
    "EN": "TOPIK Level {level} Korean vocabulary words with example sentences and illustrations.",
    "JP": "TOPIK {level}級の韓国語単語を例文とイラストで学びます。",
    "CN": "TOPIK {level}级韩语词汇，配有例句和插图。",
    "VN": "Từ vựng tiếng Hàn TOPIK cấp {level} với câu ví dụ và minh họa.",
    "ES": "Vocabulario coreano TOPIK nivel {level} con oraciones de ejemplo e ilustraciones.",
}


def load_playlists() -> dict:
    """재생목록 ID 캐시 로드: { "EN": { "1": "PLxxxx", ... }, ... }"""
    if os.path.exists(PLAYLISTS_FILE):
        with open(PLAYLISTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_playlists(data: dict):
    """재생목록 ID 캐시 저장"""
    os.makedirs(os.path.dirname(PLAYLISTS_FILE), exist_ok=True)
    with open(PLAYLISTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_or_create_playlist(youtube, lang: str, level: int) -> str:
    """레벨별 재생목록 ID를 반환. 없으면 생성."""
    playlists = load_playlists()
    lang_playlists = playlists.get(lang, {})
    level_key = str(level)

    # 캐시에 있으면 바로 반환
    if level_key in lang_playlists:
        playlist_id = lang_playlists[level_key]
        # 유효성 검증 (삭제된 재생목록 대비)
        try:
            youtube.playlists().list(
                part="id", id=playlist_id
            ).execute()
            return playlist_id
        except Exception:
            pass  # 삭제된 경우 아래에서 재생성

    # 기존 재생목록에서 검색
    title_tmpl = PLAYLIST_TITLES.get(lang, PLAYLIST_TITLES["EN"])
    target_title = title_tmpl.format(level=level)

    next_page = None
    while True:
        resp = youtube.playlists().list(
            part="snippet", mine=True, maxResults=50, pageToken=next_page
        ).execute()
        for item in resp.get("items", []):
            if item["snippet"]["title"] == target_title:
                playlist_id = item["id"]
                lang_playlists[level_key] = playlist_id
                playlists[lang] = lang_playlists
                save_playlists(playlists)
                print(f"  [재생목록] 기존 발견: {target_title} ({playlist_id})")
                return playlist_id
        next_page = resp.get("nextPageToken")
        if not next_page:
            break

    # 없으면 새로 생성
    desc_tmpl = PLAYLIST_DESCS.get(lang, PLAYLIST_DESCS["EN"])
    body = {
        "snippet": {
            "title": target_title,
            "description": desc_tmpl.format(level=level),
        },
        "status": {"privacyStatus": "public"},
    }
    resp = youtube.playlists().insert(part="snippet,status", body=body).execute()
    playlist_id = resp["id"]
    print(f"  [재생목록] 새로 생성: {target_title} ({playlist_id})")

    lang_playlists[level_key] = playlist_id
    playlists[lang] = lang_playlists
    save_playlists(playlists)
    return playlist_id


def add_to_playlist(youtube, playlist_id: str, video_id: str):
    """영상을 재생목록에 추가"""
    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id,
                },
            }
        },
    ).execute()
    print(f"  [OK] 재생목록에 추가 완료 (playlist: {playlist_id})")


# ─── 언어별 메타데이터 템플릿 ────────────────────────────────
LANG_META = {
    "EN": {
        "sent_key": "en",
        "default_lang": "ko",
        "level_fmt": lambda lv: f"{lv}급",
        "title":   "[TOPIK {level}] {word} = {meaning} | Korean Word of the Day #{day}",
        "heading": "Korean Word of the Day",
        "word_label": "단어 | Word",
        "sent_label": "예문 | Example Sentences",
        "meaning_label": "Meaning",
        "pron_label": "Pronunciation",
        "pos_label": "Part of Speech",
        "study":     "📚 Study more vocabulary at: https://studioroomkr.com/HW/topik/en/",
        "comment":   '💬 Leave a comment with your own sentence using "{word}"!',
        "subscribe": "🔔 Subscribe for daily TOPIK vocabulary videos!",
        "hashtags":  "#Korean #{word} #TOPIK #LearnKorean #KoreanVocabulary #한국어 #토픽 #KoreanWordOfTheDay",
        "tags": ["Korean", "TOPIK", "Learn Korean", "Korean vocabulary",
                 "Korean word of the day", "Korean for beginners", "Korean language",
                 "Korean study", "Korean lessons", "한국어", "토픽", "토픽단어", "한국어 공부"],
    },
    "JP": {
        "sent_key": "jp",
        "default_lang": "ko",
        "level_fmt": lambda lv: f"{lv}級",
        "title":   "[TOPIK {level}] {word} = {meaning} | 毎日の韓国語単語 #{day}",
        "heading": "毎日の韓国語単語",
        "word_label": "단어 | 単語",
        "sent_label": "예문 | 例文",
        "meaning_label": "意味",
        "pron_label": "発音",
        "pos_label": "品詞",
        "study":     "📚 もっと単語を勉強する: https://studioroomkr.com/HW/topik/jp/",
        "comment":   '💬 「{word}」を使って文を作ってみよう！',
        "subscribe": "🔔 チャンネル登録で毎日韓国語を学ぼう！",
        "hashtags":  "#韓国語 #{word} #TOPIK #韓国語勉強 #韓国語単語 #한국어 #토픽 #毎日韓国語",
        "tags": ["韓国語", "TOPIK", "韓国語勉強", "韓国語単語", "毎日韓国語",
                 "韓国語初心者", "トピック", "한국어", "토픽", "토픽단어",
                 "韓国語講座", "韓国語学習"],
    },
    "CN": {
        "sent_key": "cn",
        "default_lang": "ko",
        "level_fmt": lambda lv: f"{lv}级",
        "title":   "[TOPIK {level}] {word} = {meaning} | 每日韩语单词 #{day}",
        "heading": "每日韩语单词",
        "word_label": "단어 | 单词",
        "sent_label": "예문 | 例句",
        "meaning_label": "意思",
        "pron_label": "发音",
        "pos_label": "词性",
        "study":     "📚 学习更多词汇: https://studioroomkr.com/HW/topik/cn/",
        "comment":   '💬 用「{word}」造一个句子吧！',
        "subscribe": "🔔 订阅频道，每天学习韩语词汇！",
        "hashtags":  "#韩语 #{word} #TOPIK #学韩语 #韩语单词 #한국어 #토픽 #每日韩语",
        "tags": ["韩语", "TOPIK", "学韩语", "韩语单词", "每日韩语",
                 "韩语入门", "韩语学习", "한국어", "토픽", "토픽단어",
                 "韩语词汇", "韩语课程"],
    },
    "VN": {
        "sent_key": "vn",
        "default_lang": "ko",
        "level_fmt": lambda lv: f"Cấp {lv}",
        "title":   "[TOPIK {level}] {word} = {meaning} | Từ vựng tiếng Hàn #{day}",
        "heading": "Từ vựng tiếng Hàn mỗi ngày",
        "word_label": "단어 | Từ vựng",
        "sent_label": "예문 | Câu ví dụ",
        "meaning_label": "Nghĩa",
        "pron_label": "Phát âm",
        "pos_label": "Loại từ",
        "study":     "📚 Học thêm từ vựng: https://studioroomkr.com/HW/topik/vn/",
        "comment":   '💬 Hãy đặt câu với từ "{word}" nhé!',
        "subscribe": "🔔 Đăng ký kênh để học tiếng Hàn mỗi ngày!",
        "hashtags":  "#tiếngHàn #{word} #TOPIK #họctiếngHàn #từvựngtiếngHàn #한국어 #토픽",
        "tags": ["tiếng Hàn", "TOPIK", "học tiếng Hàn", "từ vựng tiếng Hàn",
                 "tiếng Hàn mỗi ngày", "tiếng Hàn cho người mới",
                 "한국어", "토픽", "토픽단어", "tiếng Hàn cơ bản"],
    },
    "ES": {
        "sent_key": "es",
        "default_lang": "ko",
        "level_fmt": lambda lv: f"Nivel {lv}",
        "title":   "[TOPIK {level}] {word} = {meaning} | Palabra coreana del día #{day}",
        "heading": "Palabra coreana del día",
        "word_label": "단어 | Palabra",
        "sent_label": "예문 | Oraciones de ejemplo",
        "meaning_label": "Significado",
        "pron_label": "Pronunciación",
        "pos_label": "Categoría",
        "study":     "📚 Estudia más vocabulario: https://studioroomkr.com/HW/topik/sp/",
        "comment":   '💬 ¡Escribe una oración usando "{word}"!',
        "subscribe": "🔔 ¡Suscríbete para videos diarios de vocabulario coreano!",
        "hashtags":  "#coreano #{word} #TOPIK #aprenderCoreano #vocabularioCoreano #한국어 #토픽",
        "tags": ["coreano", "TOPIK", "aprender coreano", "vocabulario coreano",
                 "palabra coreana del día", "coreano para principiantes",
                 "한국어", "토픽", "토픽단어", "idioma coreano"],
    },
}

# ─── 메타데이터 생성 ─────────────────────────────────────────
def generate_metadata(word: dict, day_number: int, lang: str = "EN") -> dict:
    """단어 정보로 유튜브 메타데이터 자동 생성 (다국어 지원)"""

    L = LANG_META.get(lang, LANG_META["EN"])
    level = word["level"]
    ko_word = word["word"]
    meaning = word["meaning"]
    roman = word["romanization"]
    pos = word["part_of_speech"]
    level_str = L["level_fmt"](level)
    sent_key = L["sent_key"]

    # 제목
    title = L["title"].format(level=level_str, word=ko_word, meaning=meaning, day=day_number)

    # 예문 (해당 언어 키 → en 폴백)
    sentences_text = "\n".join(
        f"  {i+1}. {s['ko']}\n     → {s.get(sent_key, s.get('en', ''))}"
        for i, s in enumerate(word["sentences"])
    )

    description = f"""✅ {L['heading']} #{day_number}

━━━━━━━━━━━━━━━━━━━━
{L['word_label']}
━━━━━━━━━━━━━━━━━━━━
🇰🇷 한국어: {ko_word}
📖 {L['meaning_label']}: {meaning}
🔤 {L['pron_label']}: [{roman}]
📝 {L['pos_label']}: {pos}
📊 TOPIK Level: {level_str}

━━━━━━━━━━━━━━━━━━━━
{L['sent_label']}
━━━━━━━━━━━━━━━━━━━━
{sentences_text}

━━━━━━━━━━━━━━━━━━━━
{L['study']}
{L['comment'].format(word=ko_word)}
{L['subscribe']}

{L['hashtags'].format(word=ko_word)}
"""

    # 태그: 공통 + 언어별 + 단어 고유
    tags = L["tags"] + [
        ko_word, meaning, roman, pos,
        f"TOPIK {level_str}",
    ]

    return {
        "title": title[:100],
        "description": description,
        "tags": tags[:30],
        "category_id": "27",
        "default_language": L["default_lang"],
    }

# ─── 업로드 ──────────────────────────────────────────────────
def upload_video(
    youtube,
    video_path: str,
    metadata: dict,
    publish_at: datetime = None,  # None이면 즉시 공개
    thumbnail_path: str = None,
) -> str:
    """영상 업로드 및 ID 반환"""
    
    # 공개 상태 설정
    if publish_at:
        # 예약 발행 (UTC)
        status = {
            "privacyStatus": "private",
            "publishAt": publish_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "selfDeclaredMadeForKids": False,
        }
    else:
        status = {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        }
    
    body = {
        "snippet": {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "categoryId": metadata["category_id"],
            "defaultLanguage": metadata["default_language"],
        },
        "status": status,
    }
    
    print(f"  업로드 중: {metadata['title']}")
    
    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024 * 10  # 10MB 청크
    )
    
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status_resp, response = request.next_chunk()
        if status_resp:
            progress = int(status_resp.progress() * 100)
            print(f"    업로드 진행: {progress}%")
    
    video_id = response["id"]
    print(f"  [OK] 업로드 완료: https://youtube.com/watch?v={video_id}")
    
    # 썸네일 설정 (있는 경우)
    if thumbnail_path and os.path.exists(thumbnail_path):
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path)
        ).execute()
        print(f"  [OK] 썸네일 설정 완료")
    
    return video_id


# ─── 업로드 로그 관리 ────────────────────────────────────────
def load_upload_log(log_path: str = "logs/uploads.json") -> dict:
    if os.path.exists(log_path):
        with open(log_path) as f:
            return json.load(f)
    return {"uploaded": [], "last_day": 0}

def save_upload_log(log: dict, log_path: str = "logs/uploads.json"):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


# ─── 엔트리포인트 ────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="유튜브 업로드")
    parser.add_argument("--video", required=True, help="MP4 파일 경로")
    parser.add_argument("--word-id", type=int, required=True, help="단어 ID")
    parser.add_argument("--db", default="data/LanguageTest/words_db.json")
    parser.add_argument("--log", default="logs/uploads.json")
    parser.add_argument("--schedule-hours", type=int, default=0,
                        help="N시간 후 예약 발행 (0=즉시)")
    parser.add_argument("--thumbnail", default=None, help="썸네일 이미지 경로")
    parser.add_argument("--lang", default="EN", choices=["EN","JP","CN","VN","ES"],
                        help="대상 언어 (제목/설명/태그 언어)")
    args = parser.parse_args()

    # 단어 로드
    with open(args.db, encoding="utf-8") as f:
        db = json.load(f)
    word = next((w for w in db if w["id"] == args.word_id), None)
    if not word:
        print(f"단어 ID {args.word_id}를 찾을 수 없습니다")
        sys.exit(1)

    # 로그 로드
    log = load_upload_log(args.log)
    day_number = log["last_day"] + 1

    # 메타데이터 생성
    metadata = generate_metadata(word, day_number, lang=args.lang)
    
    # 예약 시간 계산
    publish_at = None
    if args.schedule_hours > 0:
        publish_at = datetime.now(timezone.utc) + timedelta(hours=args.schedule_hours)
        print(f"예약 발행: {publish_at.strftime('%Y-%m-%d %H:%M UTC')}")
    
    # 유튜브 클라이언트
    youtube = get_youtube_client(lang=args.lang)
    
    # 업로드
    video_id = upload_video(
        youtube, args.video, metadata,
        publish_at=publish_at,
        thumbnail_path=args.thumbnail
    )

    # 레벨별 재생목록에 추가
    try:
        playlist_id = get_or_create_playlist(youtube, args.lang, word["level"])
        add_to_playlist(youtube, playlist_id, video_id)
    except Exception as e:
        print(f"  [WARN] 재생목록 추가 실패: {e}")

    # 로그 저장
    log["last_day"] = day_number
    log["uploaded"].append({
        "day": day_number,
        "word_id": args.word_id,
        "word": word["word"],
        "level": word["level"],
        "video_id": video_id,
        "uploaded_at": datetime.now().isoformat(),
        "publish_at": publish_at.isoformat() if publish_at else "immediate",
    })
    save_upload_log(log, args.log)
    
    print(f"\n[DONE] Day #{day_number}: {word['word']} = {word['meaning']}")
