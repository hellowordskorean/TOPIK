#!/usr/bin/env python3
"""Runner script for IELTS example generation with file-based logging."""

import sys
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import time
import re
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

DATA_DIR = r"D:\MakingApps\Youtube\Hellowords\data\IELTS"
LOG_FILE = rf"{DATA_DIR}\gen_log.txt"

def log(msg):
    print(msg, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

LEVEL_GUIDELINES = {
    5: "IELTS Band 5: Moderate complexity, clear and direct sentences, general academic topics. Vocabulary should be accessible but demonstrate range.",
    6: "IELTS Band 6: Upper-intermediate level, academic writing style, varied vocabulary. Use complex sentence structures. Topics relate to academic, professional, or social contexts.",
    7: "IELTS Band 7: Advanced academic English, sophisticated sentence structures, complex ideas. Use a wide range of vocabulary precisely. Discuss abstract concepts, research findings, and nuanced arguments."
}

BATCH_SIZE = 25


def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_words_needing_examples(data):
    words = data['words']
    return [(i, w) for i, w in enumerate(words) if len(w.get('examples', [])) < 10]


def build_prompt(word_obj, level_num, num_needed):
    word = word_obj['word']
    pos = word_obj.get('pos', '')
    meaning = word_obj.get('meaning', '')
    level_guide = LEVEL_GUIDELINES[level_num]
    existing = word_obj.get('examples', [])
    existing_situations = [ex.get('situation', '') for ex in existing]

    sit_text = ""
    if existing_situations:
        sit_text = "EXISTING SITUATIONS (DO NOT REPEAT these contexts):\n" + \
                   "\n".join(f"- {s}" for s in existing_situations) + "\n"

    return f"""Generate exactly {num_needed} new example sentences for the English word "{word}" ({pos}: {meaning}) for an IELTS vocabulary learning app.

Level: IELTS Band {level_num}
{level_guide}

{sit_text}
Requirements:
1. Each example must use "{word}" naturally
2. Use different contexts: academic essays, research, professional settings, social issues, science, economics, education, environment, health, culture, history
3. Korean translations must be accurate and natural
4. The "situation" field: brief Korean description (5-15 chars, e.g., "학술 연구", "환경 정책")

Return ONLY a valid JSON array with exactly {num_needed} objects. No markdown code blocks, no explanation, just the raw JSON array.
Each object: {{"situation": "Korean context", "en": "English sentence", "ko": "Korean translation"}}

JSON array:"""


def parse_json_response(text):
    text = text.strip()
    # Remove markdown code blocks
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find JSON array
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Cannot parse JSON: {text[:300]}")


async def generate_examples(word_obj, level_num, num_needed, retries=3):
    word = word_obj['word']
    prompt = build_prompt(word_obj, level_num, num_needed)

    for attempt in range(retries):
        try:
            result_text = None
            async for msg in query(
                prompt=prompt,
                options=ClaudeAgentOptions(model="claude-opus-4-6")
            ):
                if isinstance(msg, ResultMessage):
                    result_text = msg.result

            if result_text:
                examples = parse_json_response(result_text)
                validated = []
                for ex in examples:
                    if isinstance(ex, dict) and all(k in ex for k in ('situation', 'en', 'ko')):
                        validated.append({
                            'situation': str(ex['situation']),
                            'en': str(ex['en']),
                            'ko': str(ex['ko'])
                        })
                if validated:
                    return validated[:num_needed]

        except Exception as e:
            log(f"    Attempt {attempt+1} failed for '{word}': {type(e).__name__}: {e}")
            if attempt < retries - 1:
                time.sleep(3)

    return []


async def process_file(filename, level_num):
    filepath = rf"{DATA_DIR}\{filename}"
    log(f"\n{'='*60}")
    log(f"Processing {filename} (IELTS Level {level_num})")
    log(f"{'='*60}")

    data = load_json(filepath)
    words_needing = get_words_needing_examples(data)
    total_needing = len(words_needing)
    log(f"Words needing examples: {total_needing}")

    if total_needing == 0:
        log("All words already have 10 examples!")
        return True

    processed = 0
    errors = 0
    batch_num = 0

    for batch_start in range(0, total_needing, BATCH_SIZE):
        batch = words_needing[batch_start:batch_start + BATCH_SIZE]
        batch_num += 1
        log(f"\nBatch {batch_num}: words {batch_start+1}-{min(batch_start+BATCH_SIZE, total_needing)} of {total_needing}")

        for idx, (word_idx, word_obj) in enumerate(batch):
            current_count = len(word_obj.get('examples', []))
            num_needed = 10 - current_count
            word = word_obj['word']

            log(f"  [{batch_start+idx+1}/{total_needing}] '{word}': {current_count} -> 10 (need {num_needed})")

            new_examples = await generate_examples(word_obj, level_num, num_needed)

            if new_examples:
                data['words'][word_idx]['examples'].extend(new_examples)
                actual = len(data['words'][word_idx]['examples'])
                log(f"    OK: added {len(new_examples)}, total now {actual}")
                processed += 1
            else:
                log(f"    FAILED: could not generate examples for '{word}'")
                errors += 1

        # Save after each batch
        save_json(filepath, data)
        log(f"\n  [Batch {batch_num} saved to {filename}]")

        if batch_start + BATCH_SIZE < total_needing:
            time.sleep(1)

    # Final check
    final_data = load_json(filepath)
    still_needing = get_words_needing_examples(final_data)

    log(f"\n{'='*60}")
    log(f"COMPLETE: {filename}")
    log(f"  Processed: {processed}, Errors: {errors}")
    log(f"  Words still under 10: {len(still_needing)}")
    if still_needing:
        log(f"  Remaining: {[w['word'] for _, w in still_needing[:10]]}")
    log(f"{'='*60}")

    return len(still_needing) == 0


async def main():
    # Clear/create log file
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("IELTS Example Generator Log\n")
        f.write(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    log("IELTS Example Generator")
    log("Target: exactly 10 examples per word")

    files = [
        ("ielts_5.json", 5),
        ("ielts_6.json", 6),
        ("ielts_7.json", 7),
    ]

    for filename, level_num in files:
        success = await process_file(filename, level_num)
        log(f"\n{'OK' if success else 'INCOMPLETE'}: {filename}")

    log("\n\nAll files processed!")
    log(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Final summary
    log("\nFinal Summary:")
    for filename, level_num in files:
        filepath = rf"{DATA_DIR}\{filename}"
        data = load_json(filepath)
        words = data['words']
        counts = [len(w.get('examples', [])) for w in words]
        avg = sum(counts) / len(counts)
        still_under = sum(1 for c in counts if c < 10)
        log(f"  {filename}: avg={avg:.1f}, under_10={still_under}, min={min(counts)}, max={max(counts)}")


if __name__ == "__main__":
    anyio.run(main)
