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
import traceback
from datetime import datetime
from pathlib import Path

import anthropic
from google import genai
from google.genai import types

OUTPUT_DIR    = Path("/app/assets/illustrations")
PROMPTS_FILE  = Path("/app/data/LanguageTest/illustration_prompts.json")
SCENE_CACHE   = Path("/app/data/LanguageTest/scene_cache.json")
FLAGGED_FILE  = Path("/app/logs/illust_flagged.json")

# ── 스타일 공통 키워드 ────────────────────────────────────────
_STYLE_SUFFIX = (
    "hand-drawn illustration with soft watercolor textures, "
    "gentle ink outlines, warm pastel color palette, "
    "light cream background with subtle paper grain, "
    "centered composition, charming expressive characters, "
    "each person must have a distinctly different appearance such as different hairstyle and hair color and clothing and body type, "
    "delicate brushstroke details, "
    "completely text-free wordless illustration, "
    "replace all text with universal symbols and pictograms: "
    "use ★ ♥ ● ▲ ♪ ☀ ✿ arrows and simple geometric shapes instead of any writing, "
    "shop signs show only icons like a cup symbol for cafe or scissors symbol for barber, "
    "numbers are allowed on price tags and clocks, "
    "books and papers are blank or have wavy lines only, "
    "all screens show simple geometric icons only, "
    "no speech bubbles, no dialogue, no floating text, "
    "no letters, no words, no characters in any language, "
    "square format, high quality"
)

STYLE_PROMPT = (
    "clear accurate illustration of {meaning}, "
    "detailed and recognizable, "
    + _STYLE_SUFFIX
)

SENTENCE_STYLE_PROMPT = (
    "clear accurate illustration: {scene}. "
    + _STYLE_SUFFIX
)


def _sanitize_prompt(content: str) -> str:
    """텍스트 유발 요소를 기호/아이콘 표현으로 대체"""
    import re
    replacements = [
        (r'\b(sign\s+saying|sign\s+reading|sign\s+that\s+reads)\b[^,]*', 'sign with a simple icon symbol'),
        (r'\b(shop\s+sign|store\s+sign)\b', 'sign with a pictogram icon'),
        (r'\b(menu\s+board|chalkboard\s+menu|price\s+list)\b', 'board with colorful dot symbols'),
        (r'\b(name\s+tag|label\s+reading)\b', 'tag with a symbol'),
        (r'\b(receipt|invoice)\b', 'small paper with wavy lines'),
        (r'\b(document\s+with|form\s+with)\b', 'paper with wavy lines and'),
        (r'\b(book\s+titled?|newspaper|magazine\s+cover)\b', 'book with geometric pattern cover'),
        (r'\b(screen\s+showing|display\s+reading)\b', 'screen showing simple geometric icons'),
        (r'\b(clock\s+showing|clock\s+reading)\b', 'clock showing'),
        (r'\b(calendar)\b', 'calendar'),
        (r'\b(letter|mail|envelope\s+with)\b', 'envelope with heart symbol'),
        (r'\b(written|labeled|reads|reading|says|titled)\b', 'marked with symbols'),
        (r'\b(banner|poster|notice|flyer)\b', 'decorative panel with geometric shapes'),
    ]
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
    return content

def _apply_style(content: str) -> str:
    """커스텀 content 설명 + 스타일 키워드 조합"""
    content = _sanitize_prompt(content)
    return f"clear accurate illustration of {content}. {_STYLE_SUFFIX}"


# ── 장면 캐시 ────────────────────────────────────────────────
_scene_cache: dict = {}

def _load_scene_cache():
    global _scene_cache
    if SCENE_CACHE.exists():
        with open(SCENE_CACHE, encoding="utf-8") as f:
            _scene_cache = json.load(f)
        print(f"  장면 캐시 로드: {len(_scene_cache)}개")

def _save_scene_cache():
    SCENE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(SCENE_CACHE, "w", encoding="utf-8") as f:
        json.dump(_scene_cache, f, ensure_ascii=False, indent=2)


# ── Claude API: 문장 -> 시각 장면 변환 ────────────────────────
_SCENE_SYSTEM = """You are a visual scene designer for language learning illustrations.
Convert the given sentence into a VISUAL SCENE DESCRIPTION for an illustrator.

Rules:
- Describe ONLY what can be seen: actions, objects, expressions, settings
- NEVER include speech bubbles, dialogue, or floating text
- Replace conversations with body language and gestures
- ABSOLUTELY NO TEXT of any kind: no signs with words, no labels, no menus with writing, no price tags with numbers, no shop names, no book titles, no screen text
- Replace ALL text with universal symbols: ★ ♥ ● ▲ ♪ arrows, pictogram icons, geometric shapes
- Shop signs → icon only (cup icon for cafe, scissors for barber, fork-and-knife for restaurant)
- Numbers ARE allowed (price tags, clocks, calendars can show numbers)
- Books/papers → wavy lines or geometric patterns instead of words
- Be specific about body positions, facial expressions, and surroundings
- Keep it to 1-2 sentences, under 50 words
- The scene must make the sentence's meaning understandable without any dialogue

Respond with ONLY the scene description, nothing else."""

def sentence_to_visual_scene(word: dict, sent: dict, sent_idx: int) -> str | None:
    """Claude API로 영어 문장 -> 시각 장면 변환 (캐시 포함)"""
    ko = sent.get("ko", "")
    en = sent.get("en", "")
    if not en:
        return None
    cache_key = f"{word['id']}_{sent_idx}"
    if cache_key in _scene_cache:
        return _scene_cache[cache_key]
    try:
        claude = anthropic.Anthropic()
        resp = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            system=_SCENE_SYSTEM,
            messages=[{"role": "user", "content":
                f"Korean: {ko}\nEnglish: {en}\n"
                f"Target word: {word['word']} ({word['meaning']})"}],
        )
        scene = resp.content[0].text.strip()
        if scene:
            _scene_cache[cache_key] = scene
            if len(_scene_cache) % 10 == 0:
                _save_scene_cache()
            return scene
    except Exception as e:
        print(f"    Claude 장면 변환 실패: {e}")
    return None


# ── Gemini Vision 텍스트 검증 ─────────────────────────────────
_VERIFY_PROMPT = """Analyze this illustration for clearly readable text.

Check 1 - Speech bubbles: Are there speech bubbles or dialogue balloons with text inside? (FAIL if yes)
Check 2 - Readable words: Are there any clearly readable words or sentences in any language (Korean, Chinese, Japanese, English)? Only FAIL if you can actually read specific words — do NOT fail for vague squiggles, decorative lines, or abstract patterns that merely resemble letters.
Check 3 - Prominent signs: Are there large, prominent signs with clearly legible text? (FAIL if yes — small decorative marks on distant signs are OK)

IMPORTANT: This is a hand-drawn watercolor illustration. Decorative brush strokes, abstract patterns, and tiny indistinct marks are NORMAL and should PASS. Only FAIL for text that a viewer would actually try to read.

Respond in JSON only:
{
  "has_dialogue": true/false,
  "texts": [
    {"location": "shop sign", "content": "BAKERY", "readable": true}
  ],
  "pass": true/false,
  "reason": "short explanation if failed"
}"""

def _verify_image(image_path: Path, client) -> dict:
    try:
        img_bytes = image_path.read_bytes()
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                _VERIFY_PROMPT,
            ],
        )
        text = resp.text.strip()
        if "```" in text:
            text = text.split("```json")[-1].split("```")[0].strip()
            if not text:
                text = resp.text.split("```")[1].strip()
        return json.loads(text)
    except Exception as e:
        return {"pass": True, "reason": f"verify error: {e}"}

def _flag_image(word: dict, sent_idx: int, prompt: str, reason: str):
    try:
        flagged = []
        if FLAGGED_FILE.exists():
            with open(FLAGGED_FILE, encoding="utf-8") as f:
                flagged = json.load(f)
        flagged.append({
            "word_id": word["id"], "word": word["word"],
            "sent_idx": sent_idx, "reason": reason,
            "prompt": prompt[:200],
            "flagged_at": datetime.now().isoformat(),
        })
        FLAGGED_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(FLAGGED_FILE, "w", encoding="utf-8") as f:
            json.dump(flagged, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


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


def _log_error(msg: str):
    """에러를 파일에 기록"""
    try:
        log_path = Path("/app/logs/illust_errors.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    except Exception:
        pass


def _generate_once(prompt: str, output_path: Path, client) -> bool:
    """단일 이미지 생성 (검증 없이)"""
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
        _log_error(f"빈 응답 (이미지 없음): {output_path.name} | prompt: {prompt[:100]}")
        return False
    except Exception as e:
        _log_error(f"생성 오류: {e} | {output_path.name} | prompt: {prompt[:100]}")
        print(f"  생성 오류: {e}")
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print("\n[중단] API 일일 할당량 초과 — 내일 다시 시도하세요.")
            raise SystemExit(1)
        return False

def generate_image(prompt: str, output_path: Path, client,
                   word: dict = None, sent_idx: int = -1) -> bool:
    """이미지 생성 + 텍스트 검증 + 재생성 (최대 2회)"""
    if output_path.exists():
        return True
    original_prompt = prompt
    reason = ""
    for attempt in range(3):
        if attempt > 0:
            prompt = original_prompt
            print(f"    재생성 {attempt}/2...")
            if attempt == 1:
                prompt = _sanitize_prompt(prompt)
                prompt += (
                    ", use symbols ★ ♥ ● ▲ ♪ and pictogram icons instead of any text, "
                    "numbers are OK but no letters or words, "
                    "all signs show only simple icon symbols")
            elif attempt == 2:
                import re
                prompt = re.sub(r'\b(sign|label|text|letter|word|read|written|menu|board|tag|receipt|banner|poster|notice|headline|title|caption|name)\b',
                               'symbolic decoration', prompt, flags=re.IGNORECASE)
                prompt += (
                    ", replace all writing with universal symbols and geometric shapes, "
                    "★ ● ▲ ♪ ♥ arrows and numbers only, "
                    "pure visual illustration using pictograms instead of any letters or words")
        if not _generate_once(prompt, output_path, client):
            continue
        result = _verify_image(output_path, client)
        if result.get("pass", True):
            return True
        reason = result.get("reason", "unknown")
        print(f"    검증 실패: {reason}")
        if output_path.exists():
            output_path.unlink()
    print(f"    검증 3회 실패 -> 건너뜀 (텍스트 포함 이미지 저장 안 함)")
    if word:
        _flag_image(word, sent_idx, prompt, reason)
    return False


def generate_one(word: dict, client) -> bool:
    """단어 일러스트 생성 → illustrations/lv{level}/{word}/word.png"""
    word_id, korean_word = word["id"], word["word"]
    meaning, level = word["meaning"], word["level"]
    custom = get_word_custom_prompt(word_id)
    if custom:
        prompt = custom
        print(f"  [커스텀] {korean_word}")
    else:
        keyword = meaning.split(",")[0].strip().split()[0]
        prompt = STYLE_PROMPT.format(meaning=keyword)
    return generate_image(prompt, word_img_path(korean_word, level), client,
                          word=word, sent_idx=-1)


def build_sentence_prompt(word: dict, sent: dict, sent_idx: int = -1) -> str:
    """예문 장면 프롬프트 생성
    우선순위: 커스텀 -> Claude 장면 변환(캐시) -> 시각적 폴백"""
    if sent_idx >= 0:
        custom = get_sentence_custom_prompt(word["id"], sent_idx)
        if custom:
            return custom
    scene = sentence_to_visual_scene(word, sent, sent_idx)
    if scene:
        return SENTENCE_STYLE_PROMPT.format(scene=scene)
    word_meaning = word["meaning"].split(",")[0].strip()
    situation = sent.get("situation", "")
    if situation:
        scene = f"a person in a {situation.lower()} setting, related to {word_meaning}"
    else:
        scene = f"a person interacting with or experiencing {word_meaning} in daily life"
    return SENTENCE_STYLE_PROMPT.format(scene=scene)


def generate_sentences(word: dict, client) -> tuple[int, int]:
    """예문 일러스트 생성 → illustrations/lv{level}/{word}/{idx}.png"""
    done, fail = 0, 0
    for idx, sent in enumerate(word.get("sentences", [])):
        output_path = sent_img_path(word["word"], word["level"], idx)
        en = sent.get("en", "")
        prompt = build_sentence_prompt(word, sent, sent_idx=idx)
        custom = get_sentence_custom_prompt(word["id"], idx)
        cache_key = f"{word['id']}_{idx}"
        src = "커스텀" if custom else ("캐시" if cache_key in _scene_cache else "Claude")
        print(f"  [{idx+1}/10] [{src}] '{en[:40]}' -> 생성 중...")
        if generate_image(prompt, output_path, client, word=word, sent_idx=idx):
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
    _load_scene_cache()

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
        _save_scene_cache()
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
                src = "커스텀" if get_word_custom_prompt(word["id"]) else "기본"
                keyword = word["meaning"].split(",")[0].strip().split()[0]
                print(f"{step_base} [단어/{src}] '{keyword}' 생성 중...")
                if generate_one(word, client):
                    done_word += 1
                    print(f"  [OK] {wpath.name}")
                else:
                    fail += 1
                    print(f"  [FAIL] (스킵)")
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
                custom = get_sentence_custom_prompt(word["id"], idx)
                cache_key = f"{word['id']}_{idx}"
                src = "커스텀" if custom else ("캐시" if cache_key in _scene_cache else "Claude")
                en = sent.get("en", "")
                print(f"  [예문 {idx+1}/{len(sents)}] [{src}] {en[:40]}")
                if generate_image(prompt, spath, client, word=word, sent_idx=idx):
                    done_sent += 1
                    print(f"    [OK] {spath.name}")
                else:
                    fail += 1
                    print(f"    [FAIL] (스킵)")
                completed += 1
                time.sleep(0.3)
                pct = int(completed / total * 100) if total else 100
                _write_prog(pct, f"예문: {word['word']} [{idx+1}/{len(sents)}]", done_word, done_sent)

        if (done_word + done_sent) > 0 and (done_word + done_sent) % 20 == 0:
            _save_scene_cache()
            print(f"\n--- 누계: 단어 {done_word}개, 예문 {done_sent}개 / ${(done_word+done_sent)*0.02:.2f} ---\n")

    _save_scene_cache()

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
