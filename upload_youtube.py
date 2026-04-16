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
            creds = flow.run_local_server(port=0)  # 0 = 사용 가능한 포트 자동 선택
        os.makedirs(os.path.dirname(token_file), exist_ok=True)
        with open(token_file, "wb") as f:
            pickle.dump(creds, f)

    return build("youtube", "v3", credentials=creds)

# ─── 재생목록 관리 ──────────────────────────────────────────
# ── 본편: TOPIK 레벨별 ──────────────────────────────────────
PLAYLIST_TITLES = {
    "EN": "🇰🇷 TOPIK Lv.{level} Korean Word of the Day",
    "JP": "🇰🇷 TOPIK {level}級 韓国語 今日の一語",
    "CN": "🇰🇷 TOPIK {level}级 每日韩语单词",
    "VN": "🇰🇷 TOPIK Cấp {level} - Tiếng Hàn mỗi ngày",
    "ES": "🇰🇷 TOPIK N{level} - Coreano del día",
}

# ── 릴스(Shorts) ─────────────────────────────────────────────
PLAYLIST_TITLES_SHORTS = {
    "EN": "🇰🇷 Korean Shorts — Word of the Day",
    "JP": "🇰🇷 韓国語 Shorts — 今日の一語",
    "CN": "🇰🇷 韩语 Shorts — 每日单词",
    "VN": "🇰🇷 Tiếng Hàn Shorts — Từ mỗi ngày",
    "ES": "🇰🇷 Coreano Shorts — Palabra del día",
}
PLAYLIST_DESCS_SHORTS = {
    "EN": "Quick 60-second Korean vocabulary shorts! One word a day — perfect for TOPIK prep on the go. 🔔 Subscribe for daily updates!",
    "JP": "1日1語！60秒で学ぶ韓国語単語ショート動画。TOPIK対策にも最適。🔔 チャンネル登録で毎日更新！",
    "CN": "每天60秒学一个韩语词汇！TOPIK备考首选短视频。🔔 订阅每日更新！",
    "VN": "Mỗi ngày 1 từ tiếng Hàn trong 60 giây! Học tiếng Hàn siêu nhanh. 🔔 Đăng ký để nhận video mỗi ngày!",
    "ES": "¡Un vocabulario coreano nuevo cada día en 60 segundos! Ideal para preparar el TOPIK. 🔔 ¡Suscríbete!",
}

# ── 회화(Conversation) ───────────────────────────────────────
PLAYLIST_TITLES_PHRASE = {
    "EN": "🇰🇷 Korean Conversation — Real Phrases",
    "JP": "🇰🇷 韓国語会話 — すぐ使えるフレーズ",
    "CN": "🇰🇷 韩语对话 — 实用短句",
    "VN": "🇰🇷 Hội thoại tiếng Hàn — Câu thực tế",
    "ES": "🇰🇷 Conversación en coreano — Frases reales",
}
PLAYLIST_DESCS_PHRASE = {
    "EN": "Real Korean conversations for everyday situations! Each video covers 10 essential phrases for travel, daily life, and work in Korea. 🔔 New episode every week!",
    "JP": "実際の韓国語会話シーン別必須フレーズ集！旅行・日常生活・仕事で使える10フレーズを毎週更新。🔔 チャンネル登録で最新動画を受け取ろう！",
    "CN": "真实韩语对话场景！每期10句实用短语，涵盖旅游、生活、工作各种情境。🔔 每周更新，订阅不错过！",
    "VN": "Hội thoại tiếng Hàn thực tế cho mọi tình huống! Mỗi video 10 câu thiết yếu cho du lịch, cuộc sống, công việc tại Hàn Quốc. 🔔 Cập nhật mỗi tuần!",
    "ES": "¡Conversaciones reales en coreano para cada situación! 10 frases esenciales por video — viajes, vida cotidiana y trabajo en Corea. 🔔 ¡Nuevo episodio cada semana!",
}

PLAYLIST_DESCS = {
    "EN": (
        "Master TOPIK Level {level} Korean vocabulary one word at a time! "
        "Daily videos with example sentences, pronunciation, and illustrations. "
        "Perfect for beginners and TOPIK exam prep. 🔔 Subscribe for daily updates!"
    ),
    "JP": (
        "TOPIK {level}級の必須単語を毎日1語ずつマスターしよう！"
        "例文・発音・イラスト付きで楽しく学べます。"
        "韓国語検定対策・旅行・K-POP好きにおすすめ。🔔 チャンネル登録で毎日更新通知！"
    ),
    "CN": (
        "每天一个TOPIK {level}级韩语词汇！配例句、发音和插图，轻松学韩语。"
        "适合TOPIK考试备考、韩国留学、打工族。🔔 订阅频道每日更新！"
    ),
    "VN": (
        "Học từ vựng tiếng Hàn TOPIK cấp {level} mỗi ngày — 1 từ, 1 video, miễn phí! "
        "Có câu ví dụ, phát âm và hình minh họa. Phù hợp EPS-TOPIK, du học, K-pop. "
        "🔔 Đăng ký để nhận video mỗi ngày!"
    ),
    "ES": (
        "¡Aprende vocabulario coreano TOPIK N{level} cada día! "
        "1 palabra, oraciones de ejemplo, pronunciación e ilustraciones. "
        "Ideal para fans de K-pop, K-drama y quienes preparan el TOPIK. "
        "🔔 ¡Suscríbete para no perderte ningún video!"
    ),
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


def get_or_create_typed_playlist(youtube, lang: str, ptype: str) -> str:
    """타입별(shorts|phrase) 재생목록 ID 반환. 없으면 생성.
    ptype: 'shorts' | 'phrase'
    캐시 키: 'shorts' / 'phrase'
    """
    playlists = load_playlists()
    lang_playlists = playlists.get(lang, {})

    if ptype in lang_playlists:
        pid = lang_playlists[ptype]
        try:
            youtube.playlists().list(part="id", id=pid).execute()
            return pid
        except Exception:
            pass

    if ptype == "shorts":
        title = PLAYLIST_TITLES_SHORTS.get(lang, PLAYLIST_TITLES_SHORTS["EN"])
        desc  = PLAYLIST_DESCS_SHORTS.get(lang, PLAYLIST_DESCS_SHORTS["EN"])
    elif ptype == "phrase":
        title = PLAYLIST_TITLES_PHRASE.get(lang, PLAYLIST_TITLES_PHRASE["EN"])
        desc  = PLAYLIST_DESCS_PHRASE.get(lang, PLAYLIST_DESCS_PHRASE["EN"])
    else:
        raise ValueError(f"알 수 없는 playlist type: {ptype}")

    # 기존 재생목록 검색
    next_page = None
    while True:
        resp = youtube.playlists().list(
            part="snippet", mine=True, maxResults=50, pageToken=next_page
        ).execute()
        for item in resp.get("items", []):
            if item["snippet"]["title"] == title:
                pid = item["id"]
                lang_playlists[ptype] = pid
                playlists[lang] = lang_playlists
                save_playlists(playlists)
                print(f"  [재생목록] 기존 발견: {title} ({pid})")
                return pid
        next_page = resp.get("nextPageToken")
        if not next_page:
            break

    # 새로 생성
    resp = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {"title": title, "description": desc},
            "status":  {"privacyStatus": "public"},
        }
    ).execute()
    pid = resp["id"]
    print(f"  [재생목록] 새로 생성: {title} ({pid})")
    lang_playlists[ptype] = pid
    playlists[lang] = lang_playlists
    save_playlists(playlists)
    return pid


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
# 타깃별 전략:
#   EN  — K-드라마·K-팝 팬, TOPIK 시험 준비생, 한국 여행/유학 희망자
#   JP  — 한국어 검정 준비생, K-팝 팬, 한국 여행·거주자 (일본 최대 학습층)
#   CN  — 한국 유학·취업 준비생, TOPIK 시험 응시자, 한류 팬
#   VN  — EPS-TOPIK 취업 목적 학습자, 한국 유학생, K-팝·K-드라마 팬
#   ES  — K-팝·K-드라마 팬 (멕시코·중남미), 한국 문화 관심층

LANG_META = {
    "EN": {
        "sent_key": "en",
        "default_lang": "ko",
        "level_fmt": lambda lv: f"Lv.{lv}",
        # 제목: 단어=의미 → 검색 노출 + 호기심 유발
        "title": "🇰🇷 {word} = {meaning} | Korean Word of the Day #{day:03d} [TOPIK {level}]",
        # 설명 첫 줄(검색 결과에 노출되는 핵심 훅)
        "hook": "You'll hear this word EVERY DAY in Korea 🔥 Master it in 60 seconds!",
        "word_label": "📌 TODAY'S WORD",
        "sent_label": "📖 Example Sentences",
        "meaning_label": "Meaning",
        "pron_label": "Pronunciation",
        "pos_label": "Part of Speech",
        "comment_hook": '🗣️ Challenge: Write your own sentence using "{word}" in the comments! The best one gets pinned 📌',
        "subscribe": "🔔 New Korean word dropped EVERY DAY — Subscribe so you never miss one!",
        "study": "📚 Full word list + flashcards → https://studioroomkr.com/HW/topik/en/",
        "hashtags": (
            "#KoreanWordOfTheDay #LearnKorean #TOPIK #Korean #KoreanVocabulary "
            "#한국어 #토픽 #KoreanStudy #KoreanForBeginners #KDrama #KPop "
            "#KoreanLanguage #한국어공부 #StudyKorean #DailyKorean"
        ),
        "tags": [
            "Korean word of the day", "learn Korean", "Korean vocabulary", "TOPIK",
            "Korean for beginners", "Korean language", "Korean study", "daily Korean",
            "TOPIK vocabulary", "Korean words", "Korean lessons", "speak Korean",
            "K-pop Korean", "K-drama Korean", "Korean pronunciation", "Hangul",
            "한국어", "한국어 공부", "토픽", "토픽단어", "토픽 단어장",
            "Korean tutorial", "Korean alphabet", "Korean culture",
        ],
    },

    "JP": {
        "sent_key": "jp",
        "default_lang": "ko",
        "level_fmt": lambda lv: f"{lv}級",
        # 제목: 【TOPIK級】형식 + 일본어 의미 명시 (검색 최적화)
        "title": "【TOPIK{level}】{word}＝{meaning}｜韓国語 今日の一語 #{day:03d}",
        "hook": "ネイティブが毎日使う必須単語！1日1語で韓国語をマスターしよう🔥",
        "word_label": "📌 今日の単語",
        "sent_label": "📖 例文",
        "meaning_label": "意味",
        "pron_label": "発音",
        "pos_label": "品詞",
        "comment_hook": '🗣️ 「{word}」を使って例文を作ってみよう！コメントに書いてね👇 上手な文はピン留めするよ📌',
        "subscribe": "🔔 毎日新しい韓国語単語を投稿中！チャンネル登録＆ベルマークで通知をONに！",
        "study": "📚 単語一覧＆フラッシュカード → https://studioroomkr.com/HW/topik/jp/",
        "hashtags": (
            "#韓国語 #韓国語単語 #TOPIK #韓国語勉強 #韓国語検定 "
            "#한국어 #토픽 #毎日韓国語 #韓国語初心者 #ハングル "
            "#韓国語日常会話 #韓国語学習 #韓流 #韓国語講座"
        ),
        "tags": [
            "韓国語", "韓国語単語", "TOPIK", "韓国語勉強", "韓国語検定",
            "毎日韓国語", "韓国語初心者", "ハングル", "韓国語日常会話",
            "韓国語学習", "韓国語講座", "トピック", "韓国語発音",
            "한국어", "토픽", "토픽단어", "韓国語会話", "K-POP韓国語",
            "韓流", "韓国旅行", "韓国留学", "TOPIK1級", "TOPIK2級",
        ],
    },

    "CN": {
        "sent_key": "cn",
        "default_lang": "ko",
        "level_fmt": lambda lv: f"{lv}级",
        # 제목: TOPIK 시험 키워드 강조 (중국인 학습 동기의 핵심)
        "title": "【TOPIK{level}】{word}＝{meaning} | 每日韩语单词 #{day:03d}",
        "hook": "这个韩语词你会吗？韩国人天天说！一天一词，轻松通过TOPIK🔥",
        "word_label": "📌 今日单词",
        "sent_label": "📖 例句",
        "meaning_label": "意思",
        "pron_label": "发音",
        "pos_label": "词性",
        "comment_hook": '🗣️ 用「{word}」造个句子，写在评论区吧！优秀例句会被置顶📌',
        "subscribe": "🔔 每天更新韩语单词！订阅频道，开启通知，不错过任何一个词！",
        "study": "📚 全部单词表＋单词卡 → https://studioroomkr.com/HW/topik/cn/",
        "hashtags": (
            "#韩语 #韩语单词 #TOPIK #学韩语 #韩语入门 "
            "#한국어 #토픽 #每日韩语 #韩语能力考试 #韩语学习 "
            "#韩语词汇 #韩流 #韩语初学者 #TOPIK考试"
        ),
        "tags": [
            "韩语", "韩语单词", "TOPIK", "学韩语", "韩语入门",
            "每日韩语", "韩语能力考试", "韩语学习", "韩语词汇",
            "韩语初学者", "韩语课程", "TOPIK考试", "韩语发音",
            "한국어", "토픽", "토픽단어", "韩流", "韩语留学",
            "韩国留学", "韩语打工", "K-POP韩语", "韩语对话",
        ],
    },

    "VN": {
        "sent_key": "vn",
        "default_lang": "ko",
        "level_fmt": lambda lv: f"Cấp {lv}",
        # 제목: EPS-TOPIK 키워드 포함 (베트남 최대 학습 동기)
        "title": "{word} = {meaning} | Tiếng Hàn mỗi ngày #{day:03d} | TOPIK {level}",
        "hook": "Học 1 từ tiếng Hàn mỗi ngày — dễ nhớ, dễ dùng, miễn phí! 🇰🇷🔥",
        "word_label": "📌 Từ hôm nay",
        "sent_label": "📖 Câu ví dụ",
        "meaning_label": "Nghĩa",
        "pron_label": "Phát âm",
        "pos_label": "Loại từ",
        "comment_hook": '🗣️ Thử đặt câu với từ "{word}" và viết vào bình luận nhé! Câu hay nhất sẽ được ghim📌',
        "subscribe": "🔔 Mỗi ngày 1 từ mới — Đăng ký và bật thông báo để không bỏ lỡ!",
        "study": "📚 Danh sách từ đầy đủ + flashcard → https://studioroomkr.com/HW/topik/vn/",
        "hashtags": (
            "#tiếngHàn #họctiếngHàn #TOPIK #từvựngtiếngHàn #EPStiếngHàn "
            "#한국어 #토픽 #tiếngHànmỗingày #tiếngHàncơbản #họctiếngHànmiễnphí "
            "#tiếngHàngiaotiếp #đihànquốc #EPSTOPIK"
        ),
        "tags": [
            "tiếng Hàn", "học tiếng Hàn", "TOPIK", "từ vựng tiếng Hàn",
            "tiếng Hàn mỗi ngày", "tiếng Hàn cơ bản", "EPS tiếng Hàn",
            "EPSTOPIK", "tiếng Hàn giao tiếp", "học tiếng Hàn miễn phí",
            "tiếng Hàn cho người mới", "đi Hàn Quốc", "tiếng Hàn xuất khẩu lao động",
            "한국어", "토픽", "토픽단어", "tiếng Hàn online", "K-pop tiếng Hàn",
            "tiếng Hàn thực tế", "tiếng Hàn du học", "ngữ pháp tiếng Hàn",
        ],
    },

    "ES": {
        "sent_key": "es",
        "default_lang": "ko",
        "level_fmt": lambda lv: f"N{lv}",
        # 제목: K-팝 팬 유입 + TOPIK 키워드
        "title": "🇰🇷 {word} = {meaning} | Coreano del día #{day:03d} [TOPIK {level}]",
        "hook": "¿Sabes esta palabra coreana? ¡La escucharás en TODOS los K-dramas! 🔥",
        "word_label": "📌 La palabra de hoy",
        "sent_label": "📖 Oraciones de ejemplo",
        "meaning_label": "Significado",
        "pron_label": "Pronunciación",
        "pos_label": "Categoría gramatical",
        "comment_hook": '🗣️ ¡Escribe una oración con "{word}" en los comentarios! La mejor se fija arriba📌',
        "subscribe": "🔔 Nueva palabra coreana CADA DÍA — ¡Suscríbete y activa la campanita!",
        "study": "📚 Lista completa de palabras + flashcards → https://studioroomkr.com/HW/topik/sp/",
        "hashtags": (
            "#ApenderCoreano #CoreanoDelDía #TOPIK #Coreano #VocabularioCoreano "
            "#한국어 #토픽 #CoreanoParaPrincipiantes #KpopEspañol #KdramaEspañol "
            "#IdiomasCoreano #CoreanoGratis #LearnKorean"
        ),
        "tags": [
            "aprender coreano", "coreano del día", "TOPIK", "vocabulario coreano",
            "coreano para principiantes", "idioma coreano", "coreano gratis",
            "coreano kpop", "coreano kdrama", "coreano básico",
            "aprender coreano desde cero", "coreano México", "coreano latino",
            "한국어", "토픽", "토픽단어", "K-pop español", "BTS coreano",
            "coreano pronunciación", "frases en coreano", "hangul",
        ],
    },
}


# ─── 메타데이터 생성 ─────────────────────────────────────────
def generate_metadata(word: dict, day_number: int, lang: str = "EN",
                      lang_meaning: str = None) -> dict:
    """단어 정보로 유튜브 메타데이터 자동 생성 (다국어 지원)
    lang_meaning: 언어별 의미 (없으면 word['meaning'] 사용)
    """
    L = LANG_META.get(lang, LANG_META["EN"])
    level    = word["level"]
    ko_word  = word["word"]
    meaning  = lang_meaning or word.get("meaning", "")
    roman    = word.get("romanization", "")
    pos      = word.get("part_of_speech", word.get("pos", ""))
    level_str = L["level_fmt"](level)
    sent_key  = L["sent_key"]

    # ── 제목 (100자 제한) ───────────────────────────────────
    title = L["title"].format(
        level=level_str, word=ko_word, meaning=meaning, day=day_number
    )

    # ── 예문 텍스트 (최대 5개, 너무 길면 설명 잘림 방지) ──
    sents = (word.get("sentences") or word.get("examples") or [])[:5]
    sentences_text = "\n".join(
        f"  {i+1}. {s['ko']}\n     → {s.get(sent_key) or s.get('en', '')}"
        for i, s in enumerate(sents)
    )

    # ── 발음/품사 줄 (없으면 생략) ─────────────────────────
    pron_line = f"🔤 {L['pron_label']}: [{roman}]\n" if roman else ""
    pos_line  = f"📝 {L['pos_label']}: {pos}\n"      if pos   else ""

    # ── 설명 본문 ──────────────────────────────────────────
    description = (
        f"{L['hook']}\n\n"
        f"{'─'*36}\n"
        f"{L['word_label']}\n"
        f"{'─'*36}\n"
        f"🇰🇷 {ko_word}\n"
        f"💡 {L['meaning_label']}: {meaning}\n"
        f"{pron_line}"
        f"{pos_line}"
        f"📊 TOPIK {level_str}\n\n"
        f"{'─'*36}\n"
        f"{L['sent_label']}\n"
        f"{'─'*36}\n"
        f"{sentences_text}\n\n"
        f"{'─'*36}\n"
        f"{L['comment_hook'].format(word=ko_word)}\n\n"
        f"{L['subscribe']}\n"
        f"{L['study']}\n\n"
        f"{L['hashtags']}"
    )

    # ── 태그: 기본 + 단어 고유 (500자 제한 내) ────────────
    word_tags = [t for t in [ko_word, meaning, f"TOPIK {level_str}"] if t]
    all_tags  = L["tags"] + word_tags
    # 500자 초과 시 뒤에서부터 제거
    selected, total = [], 0
    for t in all_tags:
        if total + len(t) + 1 <= 498:
            selected.append(t)
            total += len(t) + 1
        if len(selected) >= 30:
            break

    return {
        "title":            title[:100],
        "description":      description[:4900],
        "tags":             selected,
        "category_id":      "27",   # Education
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


# ─── 회화 영상 메타데이터 ────────────────────────────────────
PHRASE_LANG_META = {
    "EN": {
        "lang_key": "en",
        "sit_key":  "situation_en",
        "default_lang": "en",
        "title":    "🇰🇷 Korean Conversation #{num:03d}: {situation} | Real Korean Phrases",
        "hook":     "Real Korean conversations you'll actually use! 🔥 Learn 10 essential phrases for {situation}.",
        "phrase_label": "📖 Phrases in this video",
        "subscribe": "🔔 New Korean conversation every week — Subscribe so you never miss one!",
        "study":    "📚 Full phrase list → https://studioroomkr.com/HW/conversation/en/",
        "hashtags": "#LearnKorean #KoreanConversation #KoreanPhrases #Korean #한국어 #KoreanForTravel #KoreanStudy #KDrama #KPop #한국어회화",
        "tags": ["learn Korean", "Korean conversation", "Korean phrases", "Korean for travel",
                 "Korean for beginners", "Korean language", "Korean study", "daily Korean",
                 "Korean dialogue", "speak Korean", "한국어", "한국어 회화", "Korean tutorial"],
    },
    "JP": {
        "lang_key": "jp",
        "sit_key":  "situation_jp",
        "default_lang": "ko",
        "title":    "🇰🇷 韓国語会話 #{num:03d}：{situation}｜すぐ使える10フレーズ",
        "hook":     "ネイティブが実際に使う韓国語会話！{situation}で使える必須10フレーズ 🔥",
        "phrase_label": "📖 今回のフレーズ",
        "subscribe": "🔔 毎週新しい韓国語会話を投稿！チャンネル登録＆通知ON！",
        "study":    "📚 フレーズ一覧 → https://studioroomkr.com/HW/conversation/jp/",
        "hashtags": "#韓国語会話 #韓国語フレーズ #韓国語 #韓国語勉強 #ハングル #韓国旅行 #한국어 #韓国語初心者 #韓流 #韓国語学習",
        "tags": ["韓国語会話", "韓国語フレーズ", "韓国語", "韓国語勉強", "ハングル",
                 "韓国旅行", "韓国語初心者", "韓流", "韓国語学習", "한국어", "韓国語日常会話"],
    },
    "CN": {
        "lang_key": "cn",
        "sit_key":  "situation_cn",
        "default_lang": "ko",
        "title":    "🇰🇷 韩语对话 #{num:03d}：{situation} | 实用10句",
        "hook":     "韩国人真实对话场景！{situation}必用10句，拿来就用 🔥",
        "phrase_label": "📖 本期短语",
        "subscribe": "🔔 每周更新韩语对话！订阅频道不错过！",
        "study":    "📚 短语列表 → https://studioroomkr.com/HW/conversation/cn/",
        "hashtags": "#韩语对话 #韩语短语 #韩语 #学韩语 #韩国语 #韩国旅游 #한국어 #韩语学习 #韩流 #韩语会话",
        "tags": ["韩语对话", "韩语短语", "韩语", "学韩语", "韩国语", "韩国旅游",
                 "韩语学习", "韩流", "韩语会话", "한국어", "TOPIK"],
    },
    "VN": {
        "lang_key": "vn",
        "sit_key":  "situation_vn",
        "default_lang": "ko",
        "title":    "🇰🇷 Hội thoại tiếng Hàn #{num:03d}: {situation} | 10 câu thực tế",
        "hook":     "Hội thoại tiếng Hàn thực tế nhất! {situation} — 10 câu không thể thiếu 🔥",
        "phrase_label": "📖 Các câu trong video",
        "subscribe": "🔔 Video hội thoại mới mỗi tuần — Đăng ký để không bỏ lỡ!",
        "study":    "📚 Danh sách câu → https://studioroomkr.com/HW/conversation/vn/",
        "hashtags": "#tiếngHàn #hộithoạitiếngHàn #họctiếngHàn #한국어 #tiếngHànthựctế #HànQuốc #EPS_TOPIK #KPop #KDrama #tiếngHàndulich",
        "tags": ["tiếng Hàn", "hội thoại tiếng Hàn", "học tiếng Hàn", "tiếng Hàn thực tế",
                 "Hàn Quốc", "EPS TOPIK", "한국어", "tiếng Hàn du lịch", "câu tiếng Hàn"],
    },
    "ES": {
        "lang_key": "es",
        "sit_key":  "situation_es",
        "default_lang": "ko",
        "title":    "🇰🇷 Conversación en coreano #{num:03d}: {situation} | 10 frases reales",
        "hook":     "¡Conversaciones reales en coreano! {situation} — las 10 frases que sí necesitas 🔥",
        "phrase_label": "📖 Frases de este video",
        "subscribe": "🔔 Nueva conversación en coreano cada semana — ¡Suscríbete!",
        "study":    "📚 Lista de frases → https://studioroomkr.com/HW/conversation/es/",
        "hashtags": "#coreano #aprendecoreano #conversaciónEnCoreano #한국어 #coreanoPráctico #KPop #KDrama #coreanoDesdeCero #frasesEnCoreano #viajeCorea",
        "tags": ["coreano", "aprende coreano", "conversación en coreano", "frases en coreano",
                 "coreano práctico", "한국어", "KPop", "KDrama", "viaje a Corea", "coreano desde cero"],
    },
}


def generate_phrase_metadata(situation: dict, num: int, lang: str = "EN") -> dict:
    """회화 상황 정보로 유튜브 메타데이터 생성 (다국어 지원)"""
    L = PHRASE_LANG_META.get(lang, PHRASE_LANG_META["EN"])
    lk = L["lang_key"]
    sit_key = L["sit_key"]

    situation_name = situation.get(sit_key) or situation.get("situation_en") or situation.get("situation", "")

    title = L["title"].format(num=num, situation=situation_name)

    # 대화 목록 (최대 10개)
    phrases = situation.get("phrases", [])[:10]
    phrase_lines = "\n".join(
        f"  {i+1}. {p['my_line']['ko']}  →  {p['my_line'].get(lk, p['my_line'].get('en',''))}"
        for i, p in enumerate(phrases)
        if p.get("my_line")
    )

    description = (
        f"{L['hook'].format(situation=situation_name)}\n\n"
        f"{'─'*36}\n"
        f"{L['phrase_label']}\n"
        f"{'─'*36}\n"
        f"{phrase_lines}\n\n"
        f"{'─'*36}\n"
        f"{L['subscribe']}\n"
        f"{L['study']}\n\n"
        f"{L['hashtags']}"
    )

    # 태그 500자 제한
    sit_tags = [situation_name, situation.get("situation_en", ""), "Korean conversation"]
    all_tags = L["tags"] + [t for t in sit_tags if t]
    selected, total = [], 0
    for t in all_tags:
        if total + len(t) + 1 <= 498:
            selected.append(t)
            total += len(t) + 1
        if len(selected) >= 30:
            break

    return {
        "title":            title[:100],
        "description":      description[:4900],
        "tags":             selected,
        "category_id":      "27",
        "default_language": L["default_lang"],
    }


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
    parser.add_argument("--auth-only", action="store_true", help="OAuth 인증만 수행 (업로드 없음)")
    parser.add_argument("--type", default="word", choices=["word","phrase"], help="영상 유형 (word|phrase)")
    parser.add_argument("--shorts", action="store_true", help="릴스(Shorts) 재생목록에 추가")
    parser.add_argument("--video", help="MP4 파일 경로")
    parser.add_argument("--word-id", type=int, help="단어 ID (--type word)")
    parser.add_argument("--sit-id", type=int, help="회화 상황 ID (--type phrase)")
    parser.add_argument("--db", default="/app/data/LanguageTest/words_db.json")
    parser.add_argument("--phrases-db", default=str(Path(__file__).parent.parent / "data" / "Conversation" / "phrases_db.json"))
    parser.add_argument("--log", default="logs/uploads.json")
    parser.add_argument("--schedule-hours", type=int, default=0,
                        help="N시간 후 예약 발행 (0=즉시)")
    parser.add_argument("--thumbnail", default=None, help="썸네일 이미지 경로")
    parser.add_argument("--lang", default="EN", choices=["EN","JP","CN","VN","ES"],
                        help="대상 언어 (제목/설명/태그 언어)")
    args = parser.parse_args()

    # 인증만 수행
    if args.auth_only:
        print(f"[{args.lang}] YouTube OAuth 인증을 시작합니다. 브라우저에서 로그인하세요...")
        get_youtube_client(lang=args.lang)
        print(f"[{args.lang}] 인증 완료! 토큰 저장됨.")
        sys.exit(0)

    if not args.video:
        parser.error("--video 가 필요합니다")

    # 예약 시간 계산
    publish_at = None
    if args.schedule_hours > 0:
        publish_at = datetime.now(timezone.utc) + timedelta(hours=args.schedule_hours)
        print(f"예약 발행: {publish_at.strftime('%Y-%m-%d %H:%M UTC')}")

    # 유튜브 클라이언트
    youtube = get_youtube_client(lang=args.lang)

    # ── 회화 영상 업로드 ─────────────────────────────────────
    if args.type == "phrase":
        if not args.sit_id:
            parser.error("--type phrase 는 --sit-id 가 필요합니다")
        with open(args.phrases_db, encoding="utf-8") as f:
            phrases_db = json.load(f)
        situation = next((s for s in phrases_db if s["id"] == args.sit_id), None)
        if not situation:
            print(f"상황 ID {args.sit_id}를 찾을 수 없습니다")
            sys.exit(1)

        phrase_log_path = f"logs/uploads_phrase_{args.lang.lower()}.json"
        log = load_upload_log(phrase_log_path)
        num = log["last_day"] + 1
        metadata = generate_phrase_metadata(situation, num, lang=args.lang)

        video_id = upload_video(
            youtube, args.video, metadata,
            publish_at=publish_at,
            thumbnail_path=args.thumbnail
        )

        # 회화 재생목록에 추가
        try:
            playlist_id = get_or_create_typed_playlist(youtube, args.lang, "phrase")
            add_to_playlist(youtube, playlist_id, video_id)
        except Exception as e:
            print(f"  [WARN] 회화 재생목록 추가 실패: {e}")

        log["last_day"] = num
        log.setdefault("uploaded", []).append({
            "num": num,
            "sit_id": args.sit_id,
            "situation": situation.get("situation", ""),
            "video_id": video_id,
            "lang": args.lang,
            "uploaded_at": datetime.now().isoformat(),
        })
        save_upload_log(log, phrase_log_path)
        print(f"[완료] 회화 #{num:03d} {args.lang} 업로드: https://youtube.com/watch?v={video_id}")
        sys.exit(0)

    # ── 단어 영상 업로드 ─────────────────────────────────────
    if not args.word_id:
        parser.error("--type word 는 --word-id 가 필요합니다")

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

    # 업로드
    video_id = upload_video(
        youtube, args.video, metadata,
        publish_at=publish_at,
        thumbnail_path=args.thumbnail
    )

    # 재생목록에 추가 — 릴스는 shorts 재생목록, 본편은 레벨별 재생목록
    try:
        if args.shorts:
            playlist_id = get_or_create_typed_playlist(youtube, args.lang, "shorts")
        else:
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
