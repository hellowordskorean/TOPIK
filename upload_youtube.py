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
import pickle
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CREDENTIALS_FILE = "credentials.json"   # OAuth 자격증명 파일
TOKEN_FILE = "token.pickle"              # 저장된 토큰

# ─── 인증 ────────────────────────────────────────────────────
def get_youtube_client():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            # 서버 환경: 포트 지정해서 로컬 리다이렉트
            creds = flow.run_local_server(port=8080)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
    
    return build("youtube", "v3", credentials=creds)

# ─── 메타데이터 생성 ─────────────────────────────────────────
def generate_metadata(word: dict, day_number: int) -> dict:
    """단어 정보로 유튜브 메타데이터 자동 생성"""
    
    level = word["level"]
    ko_word = word["word"]
    meaning = word["meaning"]
    roman = word["romanization"]
    pos = word["part_of_speech"]
    
    # 제목
    title = f"[TOPIK {level}급] {ko_word} = {meaning} | Korean Word of the Day #{day_number}"
    
    # 설명
    sentences_text = "\n".join(
        f"  {i+1}. {s['ko']}\n     → {s['en']}"
        for i, s in enumerate(word["sentences"])
    )
    
    description = f"""✅ Korean Word of the Day #{day_number}

━━━━━━━━━━━━━━━━━━━━
단어 | Word
━━━━━━━━━━━━━━━━━━━━
🇰🇷 한국어: {ko_word}
📖 뜻 (Meaning): {meaning}
🔤 발음 (Pronunciation): [{roman}]
📝 품사 (Part of Speech): {pos}
📊 TOPIK Level: {level}급

━━━━━━━━━━━━━━━━━━━━
예문 | Example Sentences
━━━━━━━━━━━━━━━━━━━━
{sentences_text}

━━━━━━━━━━━━━━━━━━━━
📚 Study more vocabulary at: https://studioroomkr.com/HW/topik/en/
💬 Leave a comment with your own sentence using "{ko_word}"!
🔔 Subscribe for daily TOPIK vocabulary videos!

#Korean #{ko_word} #TOPIK #LearnKorean #KoreanVocabulary #한국어 #토픽 #KoreanWordOfTheDay
"""
    
    # 태그 (500자 이내)
    tags = [
        "Korean", "TOPIK", "Learn Korean", "Korean vocabulary",
        "Korean word of the day", "한국어", "토픽", "토픽단어",
        ko_word, meaning,
        f"TOPIK level {level}", f"TOPIK {level}급",
        "Korean for beginners", "Korean language",
        pos, roman,
        "Korean study", "Korean lessons", "한국어 공부",
    ]
    
    # 썸네일용 정보도 반환 (별도 처리 필요 시)
    return {
        "title": title[:100],  # 유튜브 제목 100자 제한
        "description": description,
        "tags": tags[:30],     # 태그 최대 30개
        "category_id": "27",   # Education 카테고리
        "default_language": "ko",
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
    print(f"  ✓ 업로드 완료: https://youtube.com/watch?v={video_id}")
    
    # 썸네일 설정 (있는 경우)
    if thumbnail_path and os.path.exists(thumbnail_path):
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path)
        ).execute()
        print(f"  ✓ 썸네일 설정 완료")
    
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
    args = parser.parse_args()
    
    # 단어 로드
    with open(args.db) as f:
        db = json.load(f)
    word = next((w for w in db if w["id"] == args.word_id), None)
    if not word:
        print(f"단어 ID {args.word_id}를 찾을 수 없습니다")
        sys.exit(1)
    
    # 로그 로드
    log = load_upload_log(args.log)
    day_number = log["last_day"] + 1
    
    # 메타데이터 생성
    metadata = generate_metadata(word, day_number)
    
    # 예약 시간 계산
    publish_at = None
    if args.schedule_hours > 0:
        publish_at = datetime.now(timezone.utc) + timedelta(hours=args.schedule_hours)
        print(f"예약 발행: {publish_at.strftime('%Y-%m-%d %H:%M UTC')}")
    
    # 유튜브 클라이언트
    youtube = get_youtube_client()
    
    # 업로드
    video_id = upload_video(
        youtube, args.video, metadata,
        publish_at=publish_at,
        thumbnail_path=args.thumbnail
    )
    
    # 로그 저장
    log["last_day"] = day_number
    log["uploaded"].append({
        "day": day_number,
        "word_id": args.word_id,
        "word": word["word"],
        "video_id": video_id,
        "uploaded_at": datetime.now().isoformat(),
        "publish_at": publish_at.isoformat() if publish_at else "immediate",
    })
    save_upload_log(log, args.log)
    
    print(f"\n✓ 완료! Day #{day_number}: {word['word']} = {word['meaning']}")
