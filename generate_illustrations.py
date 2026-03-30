#!/usr/bin/env python3
"""
단어별 귀여운 일러스트 배치 생성 (최초 1회)
- Google Imagen 4 Fast 사용 ($0.02/장)
- assets/illustrations/{한국어단어}.png 에 저장 (기존 파일 스킵)
- 한국어 단어가 같으면 EN/CN/JP/VN 어느 DB든 동일 이미지 재사용
- 비용: $0.02/장 × 1800 = ~$36

준비:
  1. https://aistudio.google.com 에서 API 키 발급
  2. .env 에 GEMINI_API_KEY=... 추가

실행:
  docker compose run --rm topik-bot python3 generate_illustrations.py
  docker compose run --rm topik-bot python3 generate_illustrations.py --start 1 --end 10
"""

import json
import os
import time
import argparse
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types

OUTPUT_DIR   = Path("/app/assets/illustrations")
PROMPTS_FILE = Path("/app/data/LanguageTest/illustration_prompts.json")

# ── 스타일 공통 키워드 ────────────────────────────────────────
# 모든 일러스트에 동일하게 적용 → 일관성 유지
_STYLE_SUFFIX = (
    "hand-drawn style with soft watercolor textures, "
    "gentle ink outlines with slight imperfections, "
    "warm pastel color palette with watercolor bleeds, "
    "light cream-tinted background with subtle paper grain, "
    "centered subject, accurate and clear depiction, "
    "charming expressive characters with cozy warmth, "
    "delicate brushstroke details, soft color washes, "
    "no text, no letters, no watermark, "
    "square composition, high quality hand-painted illustration"
)

# 기본 프롬프트 (커스텀 없을 때 fallback)
STYLE_PROMPT = (
    "clear accurate illustration of {meaning}, "
    "detailed and recognizable, "
    + _STYLE_SUFFIX
)

SENTENCE_STYLE_PROMPT = (
    "clear accurate illustration of a scene: {scene}. "
    + _STYLE_SUFFIX
)


def _apply_style(content: str) -> str:
    """커스텀 content 설명 + 스타일 키워드 조합"""
    return f"clear accurate illustration of {content}. {_STYLE_SUFFIX}"


# ── 커스텀 프롬프트 로드 ──────────────────────────────────────
_custom_prompts: dict = {}

def _load_custom_prompts():
    global _custom_prompts
    if PROMPTS_FILE.exists():
        with open(PROMPTS_FILE, encoding="utf-8") as f:
            _custom_prompts = json.load(f)
        print(f"  커스텀 프롬프트 로드: {len(_custom_prompts)}개 단어")
    else:
        print(f"  커스텀 프롬프트 없음 ({PROMPTS_FILE})")


def get_word_custom_prompt(word_id: int) -> str | None:
    """단어 ID로 커스텀 word_prompt 반환 (없으면 None)"""
    entry = _custom_prompts.get(str(word_id))
    if entry and entry.get("word_prompt"):
        return _apply_style(entry["word_prompt"])
    return None


def get_sentence_custom_prompt(word_id: int, sent_idx: int) -> str | None:
    """단어 ID + 예문 인덱스로 커스텀 sentence prompt 반환 (없으면 None)"""
    entry = _custom_prompts.get(str(word_id))
    if entry:
        sentences = entry.get("sentences", [])
        if sent_idx < len(sentences) and sentences[sent_idx]:
            return _apply_style(sentences[sent_idx])
    return None


def word_dir(korean_word: str, level: int) -> Path:
    """단어별 폴더: illustrations/lv{level}/{word}/"""
    return OUTPUT_DIR / f"lv{level}" / korean_word


def word_img_path(korean_word: str, level: int) -> Path:
    """단어 일러스트: illustrations/lv{level}/{word}/word.png"""
    return word_dir(korean_word, level) / "word.png"


def sent_img_path(korean_word: str, level: int, idx: int) -> Path:
    """예문 일러스트: illustrations/lv{level}/{word}/{idx}.png"""
    return word_dir(korean_word, level) / f"{idx}.png"


def generate_image(prompt: str, output_path: Path, client) -> bool:
    """프롬프트로 이미지 생성 → output_path 저장"""
    if output_path.exists():
        return True
    try:
        response = client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",
            ),
        )
        if response.generated_images:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            response.generated_images[0].image.save(str(output_path))
            return True
        print(f"  이미지 없음 (응답 비어있음)")
        return False
    except Exception as e:
        print(f"  오류: {e}")
        return False


def generate_one(word_id: int, korean_word: str, meaning: str, level: int, client) -> bool:
    """단어 일러스트 생성 → illustrations/lv{level}/{word}/word.png"""
    custom = get_word_custom_prompt(word_id)
    if custom:
        prompt = custom
        print(f"  [커스텀] {korean_word}")
    else:
        keyword = meaning.split(",")[0].strip().split()[0]
        prompt = STYLE_PROMPT.format(meaning=keyword)
    return generate_image(prompt, word_img_path(korean_word, level), client)


def build_sentence_prompt(word: dict, sent: dict, sent_idx: int = -1) -> str:
    """예문 장면 프롬프트 생성 — 커스텀 우선, 없으면 기본 생성"""
    if sent_idx >= 0:
        custom = get_sentence_custom_prompt(word["id"], sent_idx)
        if custom:
            return custom

    situation = sent.get("situation", "")
    en = sent.get("en", "")
    word_meaning = word["meaning"].split(",")[0].strip()

    if situation and en:
        scene = f"{situation.lower()}: {en.lower()} The word is '{word_meaning}'."
    elif situation:
        scene = f"{situation.lower()}, related to '{word_meaning}'"
    elif en:
        scene = f"{en.lower()}"
    else:
        scene = word_meaning

    return SENTENCE_STYLE_PROMPT.format(scene=scene)


def generate_sentences(word: dict, client) -> tuple[int, int]:
    """예문 일러스트 생성 → illustrations/lv{level}/{word}/{idx}.png"""
    done, fail = 0, 0
    for idx, sent in enumerate(word.get("sentences", [])):
        output_path = sent_img_path(word["word"], word["level"], idx)
        situation = sent.get("situation", "")
        en = sent.get("en", "")
        prompt = build_sentence_prompt(word, sent, sent_idx=idx)
        src = "커스텀" if get_sentence_custom_prompt(word["id"], idx) else "기본"
        print(f"  [{idx+1}/10] [{src}] '{situation}' / '{en[:35]}...' → 생성 중...")
        if generate_image(prompt, output_path, client):
            done += 1
            print(f"    저장: {output_path}")
        else:
            fail += 1
        time.sleep(0.3)
    return done, fail


PROG_FILE = Path("/app/logs/illust_progress.json")


def _write_prog(pct: int, step: str = "", done_word: int = 0, done_sent: int = 0):
    try:
        PROG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROG_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "status": "running", "pct": pct, "step": step,
                "done_word": done_word, "done_sent": done_sent,
                "updated_at": datetime.now().isoformat(),
            }, f, ensure_ascii=False)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="TOPIK 일러스트 생성 (단어 + 예문)")
    parser.add_argument("--db", default="/app/data/LanguageTest/words_db.json")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end",   type=int, default=1800)
    parser.add_argument("--words-only",     action="store_true", help="단어 일러스트만")
    parser.add_argument("--sentences-only", action="store_true", help="예문 일러스트만")
    parser.add_argument("--sentences-for-id", type=int, default=None,
                        help="특정 단어 ID의 예문 일러스트만 생성")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("오류: GEMINI_API_KEY 환경변수가 없습니다.")
        return

    client = genai.Client(api_key=api_key)
    _load_custom_prompts()

    with open(args.db, encoding="utf-8") as f:
        db = json.load(f)

    # ── 특정 단어 예문 모드 ───────────────────────────────────
    if args.sentences_for_id is not None:
        word = next((w for w in db if w["id"] == args.sentences_for_id), None)
        if not word:
            print(f"단어 ID {args.sentences_for_id}를 찾을 수 없습니다.")
            return
        print(f"예문 일러스트 생성: {word['word']} ({word['meaning']})")
        print(f"예상 비용: ${len(word.get('sentences',[])) * 0.02:.2f}\n")
        done, fail = generate_sentences(word, client)
        print(f"\n완료! 생성 {done}개 | 실패 {fail}개")
        print(f"총 비용: ${done * 0.02:.2f}")
        return

    # ── 배치 모드 (단어 + 예문) ──────────────────────────────
    words = [w for w in db if args.start <= w["id"] <= args.end]

    # 생성 필요한 수 계산
    need_word = [] if args.sentences_only else [
        w for w in words if not word_img_path(w["word"], w["level"]).exists()
    ]
    need_sent = [] if args.words_only else [
        (w, idx, sent)
        for w in words
        for idx, sent in enumerate(w.get("sentences", []))
        if not sent_img_path(w["word"], w["level"], idx).exists()
    ]
    total = len(need_word) + len(need_sent)

    print(f"단어 일러스트 생성 필요: {len(need_word)}개")
    print(f"예문 일러스트 생성 필요: {len(need_sent)}개")
    print(f"총 예상 비용: ${total * 0.02:.2f}\n")

    done_word = 0
    done_sent = 0
    fail = 0
    completed = 0

    for i, word in enumerate(words):
        step_base = f"[{i+1}/{len(words)}] {word['word']}"

        # ── 단어 일러스트 ──────────────────────────────────
        if not args.sentences_only:
            wpath = word_img_path(word["word"], word["level"])
            if not wpath.exists():
                custom = get_word_custom_prompt(word["id"])
                if custom:
                    prompt = custom
                    print(f"{step_base} [단어/커스텀] 생성 중...")
                else:
                    keyword = word["meaning"].split(",")[0].strip().split()[0]
                    prompt = STYLE_PROMPT.format(meaning=keyword)
                    print(f"{step_base} [단어] '{keyword}' 생성 중...")
                if generate_image(prompt, wpath, client):
                    done_word += 1
                    print(f"  ✓ {wpath.name}")
                else:
                    fail += 1
                    print(f"  ✗ 실패 (스킵)")
                completed += 1
                time.sleep(0.3)
                pct = int(completed / total * 100) if total else 100
                _write_prog(pct, f"단어: {word['word']}", done_word, done_sent)

        # ── 예문 일러스트 ──────────────────────────────────
        if not args.words_only:
            sents = word.get("sentences", [])
            for idx, sent in enumerate(sents):
                spath = sent_img_path(word["word"], word["level"], idx)
                if spath.exists():
                    continue
                prompt = build_sentence_prompt(word, sent, sent_idx=idx)
                src = "커스텀" if get_sentence_custom_prompt(word["id"], idx) else "기본"
                situation = sent.get("situation", "")
                print(f"  [예문 {idx+1}/{len(sents)}] [{src}] {situation[:35]}")
                if generate_image(prompt, spath, client):
                    done_sent += 1
                    print(f"    ✓ {spath.name}")
                else:
                    fail += 1
                    print(f"    ✗ 실패 (스킵)")
                completed += 1
                time.sleep(0.3)
                pct = int(completed / total * 100) if total else 100
                _write_prog(pct, f"예문: {word['word']} [{idx+1}/{len(sents)}]", done_word, done_sent)

        if (done_word + done_sent) > 0 and (done_word + done_sent) % 20 == 0:
            print(f"\n--- 누계: 단어 {done_word}개, 예문 {done_sent}개 / ${(done_word+done_sent)*0.02:.2f} ---\n")

    # 완료 기록
    try:
        PROG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROG_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "status": "done", "pct": 100,
                "done_word": done_word, "done_sent": done_sent,
                "completed_at": datetime.now().isoformat(),
            }, f, ensure_ascii=False)
    except Exception:
        pass

    print(f"\n=== 완료 ===")
    print(f"  단어 일러스트: {done_word}개 생성")
    print(f"  예문 일러스트: {done_sent}개 생성")
    print(f"  실패: {fail}개")
    print(f"  총 비용: ${(done_word+done_sent)*0.02:.2f}")


if __name__ == "__main__":
    main()
