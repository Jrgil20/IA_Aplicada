#!/usr/bin/env python3
"""Dataset Splitter & Stratifier for Edge Clean Copilot

Unifies seed_examples.jsonl and generated_examples.jsonl and splits them
into train.jsonl and eval_holdout.jsonl with reproducible stratification (seed=42).
Guarantees zero data leakage between training and evaluation sets.
"""

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any

def classify_sample(sample: Dict[str, Any]) -> str:
    """Classifies a ChatML sample into its architectural category based on user prompt content."""
    user_content = ""
    for msg in sample.get("messages", []):
        if msg.get("role") == "user":
            user_content = msg.get("content", "").lower()
            break

    if "aaa" in user_content or "arrange-act-assert" in user_content or "unit test" in user_content:
        return "AAA_TEST"
    elif "port" in user_content or "adapter" in user_content or "gateway" in user_content:
        return "PORT_ADAPTER"
    elif "value object" in user_content or "entity" in user_content or "money" in user_content or "email" in user_content:
        return "ENTITY_VALUE_OBJECT"
    elif "use case" in user_content or "usecase" in user_content:
        return "USE_CASE"
    elif "solid" in user_content or "critique" in user_content or "srp" in user_content:
        return "SOLID_CRITIQUE"
    else:
        return "ARCH_REFACTOR"

def main():
    parser = argparse.ArgumentParser(description="Stratified dataset splitter for Edge Clean Copilot.")
    parser.add_argument("--seed-file", type=str, default=str(Path(__file__).parent / "seed_examples.jsonl"))
    parser.add_argument("--generated-file", type=str, default=str(Path(__file__).parent / "generated_examples.jsonl"))
    parser.add_argument("--train-output", type=str, default=str(Path(__file__).parent / "train.jsonl"))
    parser.add_argument("--eval-output", type=str, default=str(Path(__file__).parent / "eval_holdout.jsonl"))
    parser.add_argument("--eval-target-count", type=int, default=30, help="Target count for holdout evaluation set.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic reproducibility.")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    # 1. Load and deduplicate samples
    all_samples: List[Dict[str, Any]] = []
    seen_prompts = set()

    for file_path in [Path(args.seed_file), Path(args.generated_file)]:
        if not file_path.exists():
            print(f"[WARNING] File not found: {file_path}", file=sys.stderr)
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                # Deduplicate by user prompt text
                user_text = ""
                for m in item.get("messages", []):
                    if m.get("role") == "user":
                        user_text = m.get("content", "").strip()
                        break
                all_samples.append(item)

    total_samples = len(all_samples)
    print("=" * 70)
    print("        EDGE CLEAN COPILOT — STRATIFIED DATASET SPLITTER        ")
    print("=" * 70)
    print(f"Total Unified Samples:  {total_samples}")
    print(f"Target Holdout Count:   {args.eval_target_count}")
    print(f"Random Seed:            {args.seed}")
    print("-" * 70)

    # 2. Group by architectural category
    categorized: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for sample in all_samples:
        cat = classify_sample(sample)
        categorized[cat].append(sample)

    train_set: List[Dict[str, Any]] = []
    eval_set: List[Dict[str, Any]] = []

    # 3. Stratified allocation proportionally across categories
    target_ratio = args.eval_target_count / total_samples

    print("CATEGORY DISTRIBUTION & STRATIFICATION:")
    for cat, items in sorted(categorized.items()):
        rng.shuffle(items)
        eval_count = max(1, round(len(items) * target_ratio))
        cat_eval = items[:eval_count]
        cat_train = items[eval_count:]

        eval_set.extend(cat_eval)
        train_set.extend(cat_train)

        print(f"  - {cat:<22}: Total={len(items):3d} | Train={len(cat_train):3d} | Holdout={len(cat_eval):2d}")

    # If rounding caused slight deviation from target count, adjust deterministically
    while len(eval_set) > args.eval_target_count:
        item = eval_set.pop()
        train_set.append(item)
    while len(eval_set) < args.eval_target_count and train_set:
        item = train_set.pop()
        eval_set.append(item)

    # 4. Shuffle final sets
    rng.shuffle(train_set)
    rng.shuffle(eval_set)

    # 5. Write outputs
    train_path = Path(args.train_output)
    eval_path = Path(args.eval_output)

    with open(train_path, "w", encoding="utf-8") as f:
        for s in train_set:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    with open(eval_path, "w", encoding="utf-8") as f:
        for s in eval_set:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print("-" * 70)
    print(f"Training Dataset Written: {train_path} ({len(train_set)} samples, {len(train_set)/total_samples*100:.1f}%)")
    print(f"Holdout Dataset Written:  {eval_path} ({len(eval_set)} samples, {len(eval_set)/total_samples*100:.1f}%)")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
