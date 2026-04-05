#!/usr/bin/env python3
"""
IELTS 5 Only Example Generator
Brings all words in ielts_5.json to exactly 10 examples.
Reports after each batch of 50.
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import time
import re
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

DATA_DIR = r"D:\MakingApps\Youtube\Hellowords\data\IELTS"
FILEPATH = rf"{DATA_DIR}\ielts_5.json"
LOG_FILE = rf"{DATA_DIR}\gen5_log.txt"

BATCH_SIZE = 50

LEVEL_GUIDE = "IELTS Band 5: Moderate complexity, clear and direct sentences, general/academic topics. Accessible but varied vocabulary. Mix of simple and compound sentence structures."


def log(msg):
    print(msg, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')


def load_json():
    with open(FILEPATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data):
    with open(FILEPATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_words_needing_examples(data):
    words = data['words']
    return [(i, w) for i, w in enumerate(words) if len(w.get('examples', [])) < 10]


def build_prompt(word_obj, num_needed):
    word = word_obj['word']
    pos = word_obj.get('pos', '')
    meaning = word_obj.get('meaning', '')
    existing = word_obj.get('examples', [])
    existing_situations = [ex.get('situation', '') for ex in existing]

    sit_text = ""
    if existing_situations:
        sit_text = "AVOID these existing contexts:\n" + \
                   "\n".join(f"- {s}" for s in existing_situations) + "\n\n"

    return f"""Generate exactly {num_needed} IELTS Band 5 example sentences for "{word}" ({pos}: {meaning}).

{LEVEL_GUIDE}

{sit_text}Use varied topics: academic writing, work/business, social issues, science, education, environment, health, culture, technology, travel.

Return ONLY a raw JSON array (no markdown, no explanation):
[{{"situation": "Korean context (5-15 chars)", "en": "English sentence with {word}", "ko": "Korean translation"}}]

JSON array:"""


def parse_json_response(text):
    text = text.strip()
    text = re.sub(r'```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```', '', text, flags=re.MULTILINE)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Cannot parse: {text[:200]}")


async def generate_examples(word_obj, num_needed, label, retries=3):
    word = word_obj['word']
    prompt = build_prompt(word_obj, num_needed)

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
            log(f"    [{label}] Attempt {attempt+1} failed for '{word}': {type(e).__name__}: {str(e)[:100]}")
            if attempt < retries - 1:
                await anyio.sleep(3)

    return []


async def main():
    # Init log
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"IELTS 5 Generator\nStarted: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    log("=" * 60)
    log("IELTS 5 ONLY Generator")
    log("Target: 10 examples per word in ielts_5.json")
    log("=" * 60)

    data = load_json()
    words_needing = get_words_needing_examples(data)
    total_needing = len(words_needing)
    total_words = len(data['words'])

    log(f"Total words: {total_words}")
    log(f"Already at 10: {total_words - total_needing}")
    log(f"Still need examples: {total_needing}")

    if total_needing == 0:
        log("All words already have 10 examples!")
        return

    processed = 0
    errors = 0
    batch_num = 0
    start_time = time.time()

    for batch_start in range(0, total_needing, BATCH_SIZE):
        batch = words_needing[batch_start:batch_start + BATCH_SIZE]
        batch_num += 1
        batch_end = min(batch_start + BATCH_SIZE, total_needing)
        log(f"\n--- Batch {batch_num}: words {batch_start+1} to {batch_end} of {total_needing} ---")

        for idx, (word_idx, word_obj) in enumerate(batch):
            current_count = len(word_obj.get('examples', []))
            num_needed = 10 - current_count
            word = word_obj['word']
            global_num = batch_start + idx + 1
            label = f"{global_num}/{total_needing}"

            log(f"  [{label}] '{word}': has {current_count}, need {num_needed} more")

            new_examples = await generate_examples(word_obj, num_needed, label)

            if new_examples:
                data['words'][word_idx]['examples'].extend(new_examples)
                actual = len(data['words'][word_idx]['examples'])
                log(f"    OK: added {len(new_examples)}, total={actual}")
                processed += 1
            else:
                log(f"    FAILED: '{word}'")
                errors += 1

        # Save after each batch
        save_json(data)

        # Report batch completion
        elapsed = time.time() - start_time
        done_count = processed + errors
        words_left = total_needing - done_count
        words_with_10 = total_words - len(get_words_needing_examples(data))
        log(f"\n  BATCH {batch_num} COMPLETE - Saved ielts_5.json")
        log(f"  Progress: {words_with_10}/{total_words} words now have 10 examples")
        log(f"  Processed: {processed} OK, {errors} errors")
        log(f"  Elapsed: {elapsed:.0f}s")
        if done_count > 0 and words_left > 0:
            rate = elapsed / done_count
            eta = rate * words_left
            log(f"  ETA: ~{eta:.0f}s more ({words_left} words remaining)")

    # Final verification
    final_data = load_json()
    still_needing = get_words_needing_examples(final_data)
    total_elapsed = time.time() - start_time

    log(f"\n{'='*60}")
    log(f"ielts_5.json COMPLETE!")
    log(f"Total time: {total_elapsed:.0f}s")
    log(f"Words processed: {processed}")
    log(f"Words with errors: {errors}")
    log(f"Words still under 10: {len(still_needing)}")
    if still_needing:
        log(f"Missing: {[w['word'] for _, w in still_needing]}")
    log(f"{'='*60}")

    # Final stats
    words = final_data['words']
    counts = [len(w.get('examples', [])) for w in words]
    log(f"\nFinal stats:")
    log(f"  Total: {len(words)} words")
    log(f"  At exactly 10: {sum(1 for c in counts if c == 10)}")
    log(f"  Average: {sum(counts)/len(counts):.1f}")
    log(f"  Min: {min(counts)}, Max: {max(counts)}")


if __name__ == "__main__":
    anyio.run(main)
