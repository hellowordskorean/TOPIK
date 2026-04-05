#!/usr/bin/env python3
"""
IELTS Example Generator
Generates exactly 10 examples per word for all three IELTS JSON files.
Uses Claude via claude-agent-sdk.
"""

import json
import sys
import time
import re
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

PYTHON = sys.executable
DATA_DIR = r"D:\MakingApps\Youtube\Hellowords\data\IELTS"

LEVEL_GUIDELINES = {
    "5": "IELTS Band 5: Moderate complexity, clear and direct sentences, general academic topics. Vocabulary should be accessible but demonstrate range. Sentence structures should be mostly simple to compound.",
    "6": "IELTS Band 6: Upper-intermediate level, academic writing style, varied vocabulary. Use complex sentence structures occasionally. Topics should relate to academic, professional, or social contexts.",
    "7": "IELTS Band 7: Advanced academic English, sophisticated sentence structures, complex ideas. Use a wide range of vocabulary precisely. Demonstrate ability to discuss abstract concepts, research findings, and nuanced arguments."
}

BATCH_SIZE = 25


def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_words_needing_examples(data):
    """Return list of (index, word_obj) for words with fewer than 10 examples."""
    words = data['words']
    return [(i, w) for i, w in enumerate(words) if len(w.get('examples', [])) < 10]


def build_prompt(word_obj, level_num, num_needed):
    """Build prompt to generate examples for a word."""
    word = word_obj['word']
    pos = word_obj.get('pos', '')
    meaning = word_obj.get('meaning', '')
    level_guide = LEVEL_GUIDELINES[str(level_num)]

    existing_examples = word_obj.get('examples', [])
    existing_situations = [ex.get('situation', '') for ex in existing_examples]

    situations_text = ""
    if existing_situations:
        situations_text = f"""
EXISTING SITUATIONS (DO NOT REPEAT these contexts):
{chr(10).join(f'- {s}' for s in existing_situations)}
"""

    prompt = f"""Generate exactly {num_needed} new example sentences for the English word "{word}" ({pos}: {meaning}) for an IELTS vocabulary learning app.

Level: IELTS Band {level_num}
{level_guide}

{situations_text}

Requirements:
1. Each example must use "{word}" naturally in context
2. Situations must be DIFFERENT from existing ones listed above
3. Contexts should include: academic essays, research reports, professional discussions, social issues, science, technology, economics, education, environment, health, culture, etc.
4. Korean translations must be accurate and natural
5. The "situation" field should be a brief Korean description (5-15 characters)

Return ONLY a valid JSON array with exactly {num_needed} objects. No other text.
Each object must have exactly these three fields:
- "situation": brief Korean description of context (e.g., "학술 연구", "환경 정책", "직장 환경")
- "en": English example sentence at IELTS Band {level_num} level
- "ko": Accurate Korean translation of the English sentence

Example format:
[
  {{
    "situation": "환경 정책 토론",
    "en": "Example sentence using {word} here.",
    "ko": "여기에 정확한 한국어 번역."
  }}
]

Generate exactly {num_needed} examples now:"""

    return prompt


def parse_json_from_response(text):
    """Extract and parse JSON array from response text."""
    # Try direct parse first
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON array in the text
    # Look for [...] pattern
    match = re.search(r'\[\s*\{.*?\}\s*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Try to find from first [ to last ]
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from response: {text[:200]}")


async def generate_examples_for_word(word_obj, level_num, num_needed, retries=3):
    """Generate new examples for a word using Claude."""
    prompt = build_prompt(word_obj, level_num, num_needed)

    for attempt in range(retries):
        try:
            result_text = None
            async for msg in query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    model="claude-opus-4-6"
                )
            ):
                if isinstance(msg, ResultMessage):
                    result_text = msg.result

            if result_text:
                examples = parse_json_from_response(result_text)
                # Validate structure
                validated = []
                for ex in examples:
                    if isinstance(ex, dict) and 'situation' in ex and 'en' in ex and 'ko' in ex:
                        validated.append({
                            'situation': str(ex['situation']),
                            'en': str(ex['en']),
                            'ko': str(ex['ko'])
                        })
                if len(validated) >= num_needed:
                    return validated[:num_needed]
                elif len(validated) > 0:
                    # Got fewer than needed but some valid ones
                    print(f"    Warning: got {len(validated)} of {num_needed} needed examples")
                    return validated

        except Exception as e:
            print(f"    Attempt {attempt+1} failed for '{word_obj['word']}': {e}")
            if attempt < retries - 1:
                time.sleep(2)

    return []


async def process_file(filename, level_num):
    """Process a single IELTS file, adding examples to reach 10 per word."""
    filepath = f"{DATA_DIR}/{filename}"
    print(f"\n{'='*60}")
    print(f"Processing {filename} (IELTS Level {level_num})")
    print(f"{'='*60}")

    data = load_json(filepath)
    words_needing = get_words_needing_examples(data)
    total_needing = len(words_needing)
    print(f"Words needing examples: {total_needing}")

    if total_needing == 0:
        print("All words already have 10 examples!")
        return

    processed = 0
    errors = 0

    # Process in batches
    batch_num = 0
    for batch_start in range(0, total_needing, BATCH_SIZE):
        batch = words_needing[batch_start:batch_start + BATCH_SIZE]
        batch_num += 1
        print(f"\nBatch {batch_num}: words {batch_start+1}-{min(batch_start+BATCH_SIZE, total_needing)} of {total_needing}")

        for idx, (word_idx, word_obj) in enumerate(batch):
            current_count = len(word_obj.get('examples', []))
            num_needed = 10 - current_count
            word = word_obj['word']

            print(f"  [{batch_start+idx+1}/{total_needing}] '{word}': {current_count} -> 10 (need {num_needed})")

            new_examples = await generate_examples_for_word(word_obj, level_num, num_needed)

            if new_examples:
                # Add new examples to the word
                data['words'][word_idx]['examples'].extend(new_examples)
                actual_count = len(data['words'][word_idx]['examples'])
                print(f"    Added {len(new_examples)} examples. Total: {actual_count}")
                processed += 1
            else:
                print(f"    ERROR: Failed to generate examples for '{word}'")
                errors += 1

        # Save after each batch
        save_json(filepath, data)
        print(f"\n  Batch {batch_num} complete. File saved.")

        # Brief pause between batches to be respectful
        if batch_start + BATCH_SIZE < total_needing:
            time.sleep(1)

    # Final verification
    final_data = load_json(filepath)
    final_words_needing = get_words_needing_examples(final_data)

    print(f"\n{'='*60}")
    print(f"File {filename} COMPLETE")
    print(f"  Words processed: {processed}")
    print(f"  Words with errors: {errors}")
    print(f"  Words still needing examples: {len(final_words_needing)}")

    if final_words_needing:
        print(f"  Remaining: {[w['word'] for _, w in final_words_needing[:10]]}")
    print(f"{'='*60}")

    return len(final_words_needing) == 0


async def main():
    files = [
        ("ielts_5.json", 5),
        ("ielts_6.json", 6),
        ("ielts_7.json", 7),
    ]

    print("IELTS Example Generator")
    print("Target: exactly 10 examples per word in all files")
    print(f"Processing {len(files)} files...\n")

    for filename, level_num in files:
        success = await process_file(filename, level_num)
        if success:
            print(f"\n✓ {filename} - All words now have 10 examples!")
        else:
            print(f"\n⚠ {filename} - Some words may still need attention")

    print("\n\nAll files processed!")

    # Final summary
    print("\nFinal Summary:")
    for filename, level_num in files:
        filepath = f"{DATA_DIR}/{filename}"
        data = load_json(filepath)
        words = data['words']
        counts = [len(w.get('examples', [])) for w in words]
        avg = sum(counts) / len(counts)
        still_needing = sum(1 for c in counts if c < 10)
        print(f"  {filename}: avg={avg:.1f}, words_under_10={still_needing}, min={min(counts)}, max={max(counts)}")


if __name__ == "__main__":
    anyio.run(main)
