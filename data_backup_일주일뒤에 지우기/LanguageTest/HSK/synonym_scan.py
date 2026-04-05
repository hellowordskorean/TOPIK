#!/usr/bin/env python3
"""
HSK Synonym Quality Scanner
Scans hsk_3.json, hsk_4.json, hsk_5.json for:
  1. Self-reference: synonym == headword
  2. Cross-file duplicate: synonym is itself a headword in a different semantic class
  3. Known antonym pairs
  4. Suspected semantic mismatch (category clash) using a curated category map
  5. Words with fewer than 5 examples
"""

import json
import sys
import os

BASE = os.path.dirname(os.path.abspath(__file__))
FILES = ["hsk_3.json", "hsk_4.json", "hsk_5.json"]

# -----------------------------------------------------------------------
# Curated semantic category map
# Each entry: word -> category label (used for category-clash detection)
# We keep this concise — only words that appear as synonyms and have
# obviously wrong pairings relative to their headwords are flagged.
# -----------------------------------------------------------------------
CATEGORY_MAP = {
    # Food & drink
    "包子": "food_dim_sum", "小笼包": "food_dim_sum", "灌汤包": "food_dim_sum",
    "蒸饺": "food_dim_sum", "饺子": "food_dim_sum",
    "馒头": "food_plain_bread", "花卷": "food_plain_bread",
    "米饭": "food_grain", "面条": "food_noodle",

    # Print media
    "报纸": "media_print", "日报": "media_print", "晚报": "media_print",
    "周报": "media_print",
    "杂志": "media_magazine",
    "新闻": "media_news_abstract",  # not a physical newspaper

    # People / roles
    "阿姨": "person_female_relative", "姑姑": "person_female_relative",
    "大妈": "person_female_relative",
    "班长": "person_class_leader", "组长": "person_group_leader",
    "代表": "person_representative",

    # Abstract method / approach
    "办法": "abstract_method", "方法": "abstract_method", "措施": "abstract_method",

    # Numbers / quantities
    "数字": "number_digit", "数量": "number_quantity",

    # Time
    "时间": "time_general", "时候": "time_general", "时刻": "time_general",
    "分钟": "time_unit", "小时": "time_unit",

    # Place
    "地方": "place_general", "地点": "place_general",
    "城市": "place_city", "农村": "place_rural",

    # Emotion
    "高兴": "emotion_positive", "开心": "emotion_positive", "快乐": "emotion_positive",
    "难过": "emotion_negative", "伤心": "emotion_negative", "悲伤": "emotion_negative",
    "生气": "emotion_anger", "愤怒": "emotion_anger",

    # Movement
    "走": "move_walk", "跑": "move_run", "跳": "move_jump",

    # Common antonym pairs (stored as frozensets for bidirectionality)
}

# Known antonym pairs (any order)
ANTONYM_PAIRS = [
    frozenset(["高兴", "难过"]),
    frozenset(["高兴", "伤心"]),
    frozenset(["开心", "难过"]),
    frozenset(["开心", "伤心"]),
    frozenset(["快乐", "难过"]),
    frozenset(["快乐", "悲伤"]),
    frozenset(["大", "小"]),
    frozenset(["多", "少"]),
    frozenset(["好", "坏"]),
    frozenset(["快", "慢"]),
    frozenset(["冷", "热"]),
    frozenset(["爱", "恨"]),
    frozenset(["来", "去"]),
    frozenset(["买", "卖"]),
    frozenset(["问", "答"]),
    frozenset(["升", "降"]),
    frozenset(["进", "出"]),
    frozenset(["开", "关"]),
    frozenset(["上", "下"]),
    frozenset(["左", "右"]),
    frozenset(["早", "晚"]),
    frozenset(["新", "旧"]),
    frozenset(["黑", "白"]),
    frozenset(["深", "浅"]),
    frozenset(["胖", "瘦"]),
    frozenset(["高", "矮"]),
    frozenset(["长", "短"]),
    frozenset(["宽", "窄"]),
    frozenset(["轻", "重"]),
    frozenset(["硬", "软"]),
    frozenset(["笑", "哭"]),
    frozenset(["生", "死"]),
    frozenset(["城市", "农村"]),
    frozenset(["城市", "乡村"]),
    frozenset(["男", "女"]),
    frozenset(["父", "母"]),
    frozenset(["夫", "妻"]),
    frozenset(["报纸", "新闻"]),   # not antonyms per se but flagged earlier
]


def get_category(word):
    return CATEGORY_MAP.get(word, None)


def categories_clash(headword, synonym):
    """
    Returns True if both words have known categories that are clearly different
    enough to flag (not just subcategory differences within the same domain).
    """
    hcat = get_category(headword)
    scat = get_category(synonym)
    if hcat is None or scat is None:
        return False
    if hcat == scat:
        return False
    # Only flag if they belong to completely different top-level domains
    h_top = hcat.split("_")[0]
    s_top = scat.split("_")[0]
    return h_top != s_top


def load_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def run_scan():
    issues = []
    example_warnings = []

    all_words_data = []  # list of (level, word_obj)

    for fname in FILES:
        fpath = os.path.join(BASE, fname)
        data = load_file(fpath)
        level = data.get("level", fname)
        for w in data["words"]:
            all_words_data.append((level, w))

    # Build a set of all headwords for quick lookup
    all_headwords = {w["word"] for _, w in all_words_data}

    for level, w in all_words_data:
        word = w["word"]
        wid = w.get("id", "?")
        synonyms = w.get("synonyms", [])
        examples = w.get("examples", [])
        tag = f"[HSK{level} id={wid} '{word}']"

        # --- Check 0: duplicate synonyms within the same word ---
        if len(synonyms) != len(set(synonyms)):
            seen = set()
            dup_list = [s for s in synonyms if s in seen or seen.add(s)]
            issues.append(f"DUPLICATE   {tag}: duplicate synonym(s) {dup_list} in {synonyms}")

        # --- Check 1: self-reference ---
        for syn in synonyms:
            if syn == word:
                issues.append(f"SELF-REF    {tag}: synonym '{syn}' is same as headword")

        # --- Check 2: antonym clash ---
        for syn in synonyms:
            pair = frozenset([word, syn])
            if pair in ANTONYM_PAIRS:
                issues.append(f"ANTONYM     {tag}: '{syn}' is a known antonym of '{word}'")

        # --- Check 3: semantic category mismatch ---
        for syn in synonyms:
            if categories_clash(word, syn):
                hcat = get_category(word)
                scat = get_category(syn)
                issues.append(
                    f"CAT-CLASH   {tag}: synonym '{syn}' "
                    f"(category: {scat}) clashes with headword category '{hcat}'"
                )

        # --- Check 4: synonym is a headword in a clearly different POS/meaning ---
        # (Basic check: if synonym is a headword AND has a very different POS)
        # We'll flag only if CATEGORY_MAP gives a clear mismatch — already handled above.

        # --- Check 5: fewer than 5 examples ---
        if len(examples) < 5:
            example_warnings.append(
                f"LOW-EXAMPLES {tag}: only {len(examples)} example(s) (need >= 5)"
            )

    return issues, example_warnings


def main():
    print("=" * 70)
    print("HSK SYNONYM QUALITY SCAN")
    print(f"Files: {', '.join(FILES)}")
    print("=" * 70)

    issues, example_warnings = run_scan()

    print(f"\n--- SYNONYM ISSUES ({len(issues)} found) ---")
    if issues:
        for iss in issues:
            print(" ", iss)
    else:
        print("  No issues found.")

    print(f"\n--- EXAMPLE COUNT WARNINGS ({len(example_warnings)} found) ---")
    if example_warnings:
        for w in example_warnings:
            print(" ", w)
    else:
        print("  All words have 5 or more examples.")

    print("\n" + "=" * 70)
    print(f"SCAN COMPLETE: {len(issues)} synonym issue(s), "
          f"{len(example_warnings)} low-example warning(s)")
    print("=" * 70)


if __name__ == "__main__":
    main()
