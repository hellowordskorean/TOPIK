#!/usr/bin/env python3
"""
words_db.json 및 illustration_prompts.json 통합 정리 스크립트.

처리 항목:
  A) DB 예문 placeholder/템플릿 검출
     - 영문 "(Example using ...)" 패턴
     - 한국어 템플릿 패턴 ("내일 꼭 ~기로 결심했다" 등 10여종)
     - 어색한 한국어 ("하ㄹ", "하ㅂ" 등)
  B) 검출된 단어의 예문 10개를 Gemini로 전면 재생성 (KO + EN + situation)
  C) illustration_prompts.json 재생성 대상:
     - placeholder 프롬프트가 있는 단어 (id=1207, 1326)
     - DB가 새로 갱신된 단어들 (Phase B 결과)
     - LV5-6 템플릿 재생성 64개 단어 (logs/template_word_ids.json)

실행:
  python fix_db_and_prompts.py --dry-run            # 검출만 (실제 호출 X)
  python fix_db_and_prompts.py --phase db           # DB만 재생성
  python fix_db_and_prompts.py --phase prompts      # 프롬프트만 재생성
  python fix_db_and_prompts.py                      # 전체 (DB → 프롬프트)
  python fix_db_and_prompts.py --resume             # 진행 기록 이어서
"""
import argparse, io, json, os, re, sys, time
from datetime import datetime
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except AttributeError:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# ── 경로 ─────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).parent

def _find_data_root() -> Path:
    for cand in [
        os.environ.get("DATA_ROOT", ""),
        "/app/data",
        str(_SCRIPT_DIR.parent / "data"),
    ]:
        if cand:
            p = Path(cand) / "LanguageTest" / "words_db.json"
            if p.exists():
                return Path(cand)
    raise RuntimeError("words_db.json 못 찾음")

DATA_ROOT    = _find_data_root()
WORDS_DB     = DATA_ROOT / "LanguageTest" / "words_db.json"
PROMPTS_FILE = DATA_ROOT / "LanguageTest" / "illustration_prompts.json"
TEMPLATE_IDS = _SCRIPT_DIR / "logs" / "template_word_ids.json"
PROGRESS_F   = _SCRIPT_DIR / "logs" / "fix_db_prompts_progress.json"
LOG_F        = _SCRIPT_DIR / "logs" / "fix_db_prompts.log"

# ── 검출 패턴 ───────────────────────────────────────────────
EN_PLACEHOLDER = re.compile(r'\(Example using')

# 한국어 템플릿 패턴 (단어 부분은 ___로 정규화 후 매칭)
KO_TEMPLATES = [
    "선생님이 학생에게 ___",
    "이번 주말에 ___",
    "내일 꼭 ___",
    "국가 간에 이 문제를 ___",
    "그녀는 혼자서 ___",
    "그는 매일 ___",
    "결과를 ___ 위해 추가 조사를 실시했다",
    "우리 모두 함께 ___",
    "___ 것은 쉬운 일이 아니다",
    "이 방법으로 문제를 ___",
]

# 어색한 한국어 어법 ('하ㄹ 수 있다', '되ㅁ' 등)
WEIRD_KO = re.compile(r'[하되]ㄹ|[하되]ㅂ|[하되]ㅁ')

# 이전 LV5-6 템플릿 패턴 (이미 수정되었을 수도 있지만 혹시)
OLD_TEMPLATES = [
    r'국제 사회에서 중요한 역할',
    r'양국은 이 문제를.*합의했다',
    r'전문가들은 상황을.*주장했다',
]


def _ko_norm(ko: str, word: str) -> str:
    """한국어 예문에서 단어 부분을 ___로 치환해 패턴 매칭용으로 정규화"""
    base = word[:-1] if word.endswith('다') else word
    if not base:
        return ko
    norm = re.sub(re.escape(base) + r'[가-힣]?', '___', ko)
    return norm


def is_bad_sentence(sent: dict, word: str) -> str:
    """예문이 placeholder/템플릿인지 판별. 사유 반환 (정상이면 빈 문자열)"""
    en = sent.get('en', '')
    ko = sent.get('ko', '')
    if EN_PLACEHOLDER.search(en):
        return "EN_placeholder"
    if WEIRD_KO.search(ko):
        return "어색한_한국어"
    norm = _ko_norm(ko, word)
    for tpl in KO_TEMPLATES:
        if tpl in norm:
            return f"KO_템플릿:{tpl[:20]}"
    for pat in OLD_TEMPLATES:
        if re.search(pat, ko):
            return f"OLD_템플릿:{pat[:20]}"
    return ""


def detect_bad_words(words: list) -> dict:
    """단어 ID → 사유 목록 반환.
    판정 기준 (False positive 방지):
      - EN placeholder, 어색한_한국어, OLD_템플릿: 1건만 발견되어도 즉시 재생성
      - KO_템플릿: 같은 단어 내 2건 이상 일치할 때만 재생성 (단일 매칭은 우연 가능)
    """
    bad = {}
    for w in words:
        wid = w['id']
        reasons = []
        ko_template_hits = []
        force = False
        for i, s in enumerate(w.get('sentences', [])):
            r = is_bad_sentence(s, w['word'])
            if not r:
                continue
            if r.startswith("KO_템플릿"):
                ko_template_hits.append((i, r))
            else:
                reasons.append((i, r))
                force = True
        if ko_template_hits and (force or len(ko_template_hits) >= 2):
            reasons.extend(ko_template_hits)
        if reasons:
            bad[wid] = reasons
    return bad


# ── Gemini 클라이언트 ───────────────────────────────────────
_client = None

def _get_client():
    global _client
    if _client is None:
        from google import genai
        key = os.environ.get("GEMINI_API_KEY", "")
        if not key:
            raise RuntimeError("GEMINI_API_KEY 환경변수 없음")
        _client = genai.Client(api_key=key)
    return _client


def _gemini_call(prompt: str, model: str = "gemini-2.5-flash-lite",
                 retries: int = 3) -> str | None:
    client = _get_client()
    last_err = None
    for attempt in range(retries):
        try:
            resp = client.models.generate_content(model=model, contents=[prompt])
            return resp.text.strip()
        except Exception as e:
            last_err = str(e)[:200]
            wait = 5 * (attempt + 1)
            print(f"    Gemini 오류({attempt+1}/{retries}): {last_err} → {wait}s 대기")
            time.sleep(wait)
    return None


# ── DB 예문 재생성 ──────────────────────────────────────────
def _build_sentence_prompt(word: str, meaning: str, level: int, pos: str = "") -> str:
    pos_hint = f" (품사: {pos})" if pos else ""
    return f"""You are a Korean language education expert.
Generate exactly 10 natural, realistic Korean example sentences for the word "{word}"{pos_hint} (meaning: {meaning}, TOPIK level {level}).

CRITICAL Requirements:
- Each sentence MUST naturally and CORRECTLY use the word "{word}" — verify Korean grammar conjugation
- Sentences must reflect REAL situations where this word would be used in everyday Korean life
- Each sentence MUST be DIFFERENT in structure, context, and scenario (NO repetitive templates)
- FORBIDDEN templates: "내일 꼭 ~기로 결심했다", "선생님이 학생에게 ~라고 말했다",
  "우리 모두 함께 ~하는 것이 좋다", "~하는 것은 쉬운 일이 아니다",
  "그녀는 혼자서 ~기 시작했다", "그는 매일 ~려고 노력한다",
  "이 방법으로 문제를 ~ㄹ 수 있다", "이번 주말에 ~ㄹ 계획이다",
  "국가 간에 이 문제를 ~", "결과를 ~ 위해 추가 조사를 실시했다"
- English translation must be natural, fluent, and accurately reflect the Korean
- Provide a brief English situation label (e.g., "in a cafe", "at the office")

Return ONLY a JSON array of 10 objects, no other text:
[
  {{"situation": "brief English situation label", "ko": "Korean sentence", "en": "English translation"}},
  ...
]"""


def regenerate_db_sentences(word: dict) -> list | None:
    prompt = _build_sentence_prompt(
        word['word'], word.get('meaning', ''),
        word.get('level', 5), word.get('pos', '')
    )
    text = _gemini_call(prompt)
    if not text:
        return None
    m = re.search(r'\[.*\]', text, re.DOTALL)
    if not m:
        print(f"    JSON 추출 실패")
        return None
    try:
        data = json.loads(m.group())
        if isinstance(data, list) and len(data) >= 5:
            return data[:10]
    except json.JSONDecodeError as e:
        print(f"    JSON 파싱 실패: {e}")
    return None


# ── 일러스트 프롬프트 재생성 ─────────────────────────────────
def _build_prompts_prompt(word: dict) -> str:
    sents_block = "\n".join(
        f"  {i+1}. KO: {s.get('ko','')}\n     EN: {s.get('en','')}"
        for i, s in enumerate(word.get('sentences', []))
    )
    return f"""You are an illustration art director for a Korean vocabulary learning app.

Generate 10 ENGLISH illustration prompts (one per example sentence) plus 1 word-level prompt for the Korean word below. Each prompt should describe a SINGLE concrete visual scene that depicts the SPECIFIC content of the corresponding sentence.

Korean word: {word['word']} (meaning: {word.get('meaning','')}, TOPIK level {word.get('level',1)})
Part of speech: {word.get('pos','')}

Example sentences:
{sents_block}

CRITICAL Requirements:
- Each sentence prompt must show the EXACT scene described — concrete objects, actions, locations from THAT sentence
- Use modern Korean settings (apartments, cafes, offices, schools, subway, parks) — NO traditional hanok
- Prompts describe REAL human scenes — the illustrator will adapt to chibi animal style separately
- 2-3 sentences per prompt, hyper-specific (objects, gestures, environment)
- DO NOT use generic placeholders like "depicting the concept"
- The "word_prompt" should depict the CORE meaning of the word in one canonical scene

Return ONLY a JSON object, no other text:
{{
  "word_prompt": "...",
  "sentences": [
    "prompt for sentence 1",
    "prompt for sentence 2",
    ...
    "prompt for sentence 10"
  ]
}}"""


def regenerate_prompts(word: dict) -> dict | None:
    prompt = _build_prompts_prompt(word)
    text = _gemini_call(prompt, model="gemini-2.5-flash-lite")
    if not text:
        return None
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group())
        if 'word_prompt' in data and 'sentences' in data and len(data['sentences']) >= 5:
            sents = data['sentences'][:10]
            while len(sents) < 10:
                sents.append("")
            return {"word_prompt": data['word_prompt'], "sentences": sents}
    except json.JSONDecodeError as e:
        print(f"    JSON 파싱 실패: {e}")
    return None


# ── 진행 기록 ───────────────────────────────────────────────
def _load_progress() -> dict:
    if PROGRESS_F.exists():
        try: return json.loads(PROGRESS_F.read_text(encoding='utf-8'))
        except: pass
    return {"db_done": [], "db_failed": {}, "prompts_done": [], "prompts_failed": {}}


def _save_progress(d: dict):
    PROGRESS_F.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_F.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')


def _log(msg: str):
    LOG_F.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_F, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}\n")


# ── 백업 ────────────────────────────────────────────────────
def _backup(path: Path) -> Path:
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = path.with_suffix(path.suffix + f'.bak_{ts}')
    bak.write_bytes(path.read_bytes())
    return bak


# ── 메인 ────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="DB + 프롬프트 통합 재생성")
    parser.add_argument("--dry-run", action="store_true", help="검출만 (Gemini 호출 X)")
    parser.add_argument("--phase", choices=["db", "prompts", "all"], default="all")
    parser.add_argument("--resume", action="store_true", help="진행 기록 이어서")
    parser.add_argument("--limit", type=int, default=0, help="처리 최대 단어 수 (0=무제한)")
    parser.add_argument("--id", type=int, default=None, help="특정 단어 ID 1개만 처리")
    args = parser.parse_args()

    print(f"DB: {WORDS_DB}")
    print(f"Prompts: {PROMPTS_FILE}")

    # ─── 로드 ───
    db_raw = json.loads(WORDS_DB.read_text(encoding='utf-8'))
    words = db_raw if isinstance(db_raw, list) else db_raw.get('words', [])
    wmap = {w['id']: w for w in words}
    prompts_raw = json.loads(PROMPTS_FILE.read_text(encoding='utf-8'))

    template_ids = []
    if TEMPLATE_IDS.exists():
        template_ids = json.loads(TEMPLATE_IDS.read_text(encoding='utf-8'))
        print(f"LV5-6 템플릿 단어 (참고): {len(template_ids)}개")

    # ─── DB 검출 ───
    bad_db_words = detect_bad_words(words)
    print(f"\n[검출] DB 재생성 필요 단어: {len(bad_db_words)}개")
    if bad_db_words:
        # 사유별 통계
        from collections import Counter
        reason_counter = Counter()
        for wid, reasons in bad_db_words.items():
            for _, r in reasons:
                reason_counter[r.split(':')[0]] += 1
        for k, n in reason_counter.most_common():
            print(f"  - {k}: {n}건")

    # ─── 프롬프트 placeholder 검출 ───
    prompt_ph_ids = []
    PH_PATS = ["A professional scene depicting the concept",
               "A scene depicting the concept",
               "depicting the concept through concrete actions"]
    for pid_str, entry in prompts_raw.items():
        for p in entry.get('sentences', []):
            if p and any(pat in p for pat in PH_PATS):
                prompt_ph_ids.append(int(pid_str))
                break
    print(f"\n[검출] 프롬프트 placeholder 단어: {len(prompt_ph_ids)}개 (id={prompt_ph_ids})")

    # ─── 프롬프트 재생성 대상 = bad_db_words + prompt_ph_ids + template_ids ───
    prompt_targets = set(bad_db_words.keys()) | set(prompt_ph_ids) | set(template_ids)
    print(f"\n[검출] 프롬프트 재생성 총 대상: {len(prompt_targets)}개")

    if args.id is not None:
        bad_db_words = {args.id: bad_db_words.get(args.id, [])}
        prompt_targets = {args.id}
        print(f"\n[--id 모드] {args.id}만 처리")

    if args.dry_run:
        print(f"\n[Dry-run 종료]")
        # 샘플 1개 보여주기
        if bad_db_words:
            sample_id = next(iter(bad_db_words))
            w = wmap.get(sample_id)
            print(f"\n샘플 (id={sample_id} {w['word']}):")
            for i, r in bad_db_words[sample_id][:3]:
                s = w['sentences'][i]
                print(f"  [{i}] {r}")
                print(f"      KO: {s.get('ko','')}")
                print(f"      EN: {s.get('en','')}")
        return

    progress = _load_progress() if args.resume else {"db_done": [], "db_failed": {}, "prompts_done": [], "prompts_failed": {}}

    # ─── Phase A: DB 재생성 ───
    if args.phase in ("db", "all") and bad_db_words:
        print(f"\n=== Phase A: DB 예문 재생성 ===")
        bak = _backup(WORDS_DB)
        print(f"백업: {bak.name}")
        targets = [wid for wid in sorted(bad_db_words.keys()) if wid not in progress["db_done"]]
        if args.limit > 0:
            targets = targets[:args.limit]
        for i, wid in enumerate(targets, 1):
            w = wmap[wid]
            print(f"[{i}/{len(targets)}] id={wid} {w['word']} ({w.get('meaning','')[:30]}) — 재생성 중...")
            new_sents = regenerate_db_sentences(w)
            if new_sents:
                w['sentences'] = new_sents
                progress["db_done"].append(wid)
                progress["db_failed"].pop(str(wid), None)
                _save_progress(progress)
                # 매 10개마다 DB 저장
                if i % 10 == 0:
                    WORDS_DB.write_text(json.dumps(words, ensure_ascii=False, indent=2), encoding='utf-8')
                    print(f"  [중간 저장] {i}/{len(targets)}")
                _log(f"DB OK id={wid} {w['word']}")
                print(f"  ✓ {len(new_sents)}개 예문 갱신")
            else:
                progress["db_failed"][str(wid)] = "regenerate failed"
                _save_progress(progress)
                _log(f"DB FAIL id={wid} {w['word']}")
                print(f"  ✗ 실패")
            time.sleep(1)
        # 최종 저장
        WORDS_DB.write_text(json.dumps(words, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\nDB 저장 완료: 성공 {len(progress['db_done'])} / 실패 {len(progress['db_failed'])}")

    # ─── Phase B: 프롬프트 재생성 ───
    if args.phase in ("prompts", "all") and prompt_targets:
        print(f"\n=== Phase B: 일러스트 프롬프트 재생성 ===")
        bak = _backup(PROMPTS_FILE)
        print(f"백업: {bak.name}")
        # DB 재생성 후 wmap이 이미 갱신되어 있음
        targets = [wid for wid in sorted(prompt_targets) if wid not in progress["prompts_done"]]
        if args.limit > 0:
            targets = targets[:args.limit]
        for i, wid in enumerate(targets, 1):
            w = wmap.get(wid)
            if not w:
                print(f"[{i}/{len(targets)}] id={wid} — DB 없음, 스킵")
                continue
            print(f"[{i}/{len(targets)}] id={wid} {w['word']} ({w.get('meaning','')[:30]}) — 프롬프트 생성 중...")
            new_p = regenerate_prompts(w)
            if new_p:
                prompts_raw[str(wid)] = new_p
                progress["prompts_done"].append(wid)
                progress["prompts_failed"].pop(str(wid), None)
                _save_progress(progress)
                if i % 10 == 0:
                    PROMPTS_FILE.write_text(json.dumps(prompts_raw, ensure_ascii=False, indent=2), encoding='utf-8')
                    print(f"  [중간 저장] {i}/{len(targets)}")
                _log(f"PROMPT OK id={wid} {w['word']}")
                print(f"  ✓ word + 10 sentence 프롬프트 갱신")
            else:
                progress["prompts_failed"][str(wid)] = "regenerate failed"
                _save_progress(progress)
                _log(f"PROMPT FAIL id={wid} {w['word']}")
                print(f"  ✗ 실패")
            time.sleep(1)
        # 최종 저장
        PROMPTS_FILE.write_text(json.dumps(prompts_raw, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\n프롬프트 저장 완료: 성공 {len(progress['prompts_done'])} / 실패 {len(progress['prompts_failed'])}")

    print(f"\n=== 전체 완료 ===")
    print(f"  DB 재생성: {len(progress['db_done'])}개 성공, {len(progress['db_failed'])}개 실패")
    print(f"  프롬프트 재생성: {len(progress['prompts_done'])}개 성공, {len(progress['prompts_failed'])}개 실패")


if __name__ == "__main__":
    main()
