"""
TOPIK Level 1 - 단어 20개 품질 검증 스크립트
검증 항목:
  1. 한국어 예문 문법/자연스러움 (level 1 학습자용)
  2. 영어 번역 정확도
  3. 일러스트 프롬프트 적절성 (단어/예문 표현력)
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import anthropic

# Windows CP949 터미널 인코딩 문제 해결
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ── 경로 설정 ───────────────────────────────────────────────
BASE = Path(__file__).parent
load_dotenv(BASE / ".env")

TOPIK1_EN   = BASE.parent / "data/LanguageTest/TOPIK/EN/topik_1.json"
PROMPTS_JSON = BASE.parent / "data/LanguageTest/illustration_prompts.json"
REPORT_OUT   = BASE / "logs/verify_topik_l1_report.json"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    sys.exit("❌  ANTHROPIC_API_KEY not found in .env")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── 데이터 로드 ─────────────────────────────────────────────
with open(TOPIK1_EN, encoding="utf-8") as f:
    topik_data = json.load(f)

with open(PROMPTS_JSON, encoding="utf-8") as f:
    prompts_data = json.load(f)

words_20 = topik_data["words"][:20]   # 앞 20개

# ── 검증 프롬프트 생성 ────────────────────────────────────────
def build_verification_prompt(word_entry: dict, prompt_entry: dict | None) -> str:
    word = word_entry["word"]
    pos  = word_entry["pos"]
    meaning = word_entry["meaning"]
    examples = word_entry["examples"]

    lines = [
        f"## 검증 대상: [{word}] ({pos}) — '{meaning}'",
        "",
        "### 한국어 예문 & 영어 번역",
    ]
    for i, ex in enumerate(examples, 1):
        lines.append(f"{i}. KO: {ex['ko']}")
        lines.append(f"   EN: {ex['en']}")
        lines.append(f"   상황: {ex['situation']}")

    if prompt_entry:
        lines += [
            "",
            "### 일러스트 프롬프트",
            f"단어 이미지: {prompt_entry.get('word_prompt', '(없음)')}",
            "",
            "예문 이미지 프롬프트:",
        ]
        for i, sp in enumerate(prompt_entry.get("sentences", []), 1):
            lines.append(f"{i}. {sp}")

    return "\n".join(lines)


SYSTEM_PROMPT = """당신은 TOPIK 한국어 교재 품질 검수 전문가입니다.
아래 항목을 **냉정하게** 검토하고, 문제가 있으면 구체적으로 지적해 주세요.

검토 기준:
1. **한국어 문법** — 조사, 어미, 시제가 올바른가? TOPIK 1 수준(초급)에 맞는 어휘/문형인가?
2. **영어 번역** — 뜻이 정확한가? 자연스러운 영어인가?
3. **일러스트 프롬프트** — 단어/예문의 핵심 의미를 시각적으로 잘 표현하는가?
   모호하거나 잘못된 프롬프트가 있으면 지적하세요.

응답 형식 (JSON):
{
  "word": "단어",
  "overall_score": 1~10,
  "issues": [
    {
      "type": "grammar|translation|prompt",
      "item_index": 예문 번호(1~N) 또는 "word_prompt",
      "severity": "error|warning|suggestion",
      "description": "문제 설명",
      "original": "원문",
      "suggested": "개선안 (있는 경우)"
    }
  ],
  "summary": "전체 한줄 요약"
}

문제가 없으면 issues는 빈 배열 []로 반환하세요.
반드시 valid JSON만 반환하세요. 마크다운 코드블록 없이."""


def verify_word(word_entry: dict, prompt_entry: dict | None) -> dict:
    user_content = build_verification_prompt(word_entry, prompt_entry)
    raw = ""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        raw = response.content[0].text.strip()
        # 마크다운 코드블록 제거
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rstrip("`").strip()
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {
            "word": word_entry["word"],
            "overall_score": None,
            "issues": [],
            "summary": f"JSON 파싱 오류: {e}",
            "_raw": raw,
        }
    except Exception as e:
        return {
            "word": word_entry["word"],
            "overall_score": None,
            "issues": [],
            "summary": f"API 오류: {e}",
        }


# ── 메인 실행 ─────────────────────────────────────────────────
def main():
    results = []
    total = len(words_20)
    print(f"\n[START] TOPIK Level 1 검증 시작 - {total}개 단어\n" + "-"*50)

    for idx, word_entry in enumerate(words_20, 1):
        word = word_entry["word"]
        word_id = str(word_entry["id"])
        prompt_entry = prompts_data.get(word_id)

        print(f"[{idx:02d}/{total}] {word} ... ", end="", flush=True)
        result = verify_word(word_entry, prompt_entry)
        results.append(result)

        score = result.get("overall_score", "?")
        issue_count = len(result.get("issues", []))
        summary = result.get('summary', '')
        print(f"score {score}/10  |  issues {issue_count}  |  {summary}")

    # 리포트 저장
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 요약 출력
    print("\n" + "-"*50)
    print(f"[DONE] 검증 완료 -> {REPORT_OUT}")

    errors   = sum(1 for r in results for i in r.get("issues", []) if i["severity"] == "error")
    warnings = sum(1 for r in results for i in r.get("issues", []) if i["severity"] == "warning")
    suggestions = sum(1 for r in results for i in r.get("issues", []) if i["severity"] == "suggestion")
    scored = [r["overall_score"] for r in results if r.get("overall_score")]
    avg_score = sum(scored) / len(scored) if scored else 0

    print(f"\n[SUMMARY]")
    print(f"  avg score  : {avg_score:.1f} / 10")
    print(f"  Error      : {errors}")
    print(f"  Warning    : {warnings}")
    print(f"  Suggestion : {suggestions}")

    print("\n[ERRORS]")
    found_error = False
    for r in results:
        for issue in r.get("issues", []):
            if issue["severity"] == "error":
                found_error = True
                desc = issue['description']
                print(f"  [{r['word']}] #{issue.get('item_index','')} {issue['type'].upper()}: {desc}")
                if issue.get("suggested"):
                    print(f"    => {issue['suggested']}")
    if not found_error:
        print("  (없음)")


if __name__ == "__main__":
    main()
