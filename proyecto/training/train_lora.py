#!/usr/bin/env python3
"""Native LoRA Fine-Tuning Pipeline for Edge Clean Copilot

Supports:
- Dual-mode execution: --dry-run (Cold Staging on CPU) and full training (Hot Burst on DGX Spark)
- Native PyTorch training loop with AdamW, gradient accumulation, and loss tracking
- ChatML dataset tokenization with Qwen-2.5-Coder chat templates
- Adapter checkpoint saving and optional full merge (--merge) for llama.cpp GGUF quantization
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune Small Language Models with LoRA for Clean Architecture."
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default="Qwen/Qwen2.5-Coder-1.5B-Instruct",
        help="Hugging Face base model repository or local path."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=str(Path(__file__).parent.parent / "dataset" / "train.jsonl"),
        help="Path to JSONL dataset formatted in ChatML."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(Path(__file__).parent / "output"),
        help="Directory to save LoRA adapters and checkpoints."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute exactly 1 training step on CPU/GPU to validate the pipeline."
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of full training epochs."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=2,
        help="Per-device batch size."
    )
    parser.add_argument(
        "--grad-accum",
        type=int,
        default=4,
        help="Gradient accumulation steps."
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=2e-4,
        help="Learning rate for AdamW optimizer."
    )
    parser.add_argument(
        "--max-seq-len",
        type=int,
        default=1024,
        help="Maximum sequence token length."
    )
    parser.add_argument(
        "--lora-r",
        type=int,
        default=16,
        help="LoRA rank dimension."
    )
    parser.add_argument(
        "--lora-alpha",
        type=int,
        default=32,
        help="LoRA scaling factor alpha."
    )
    parser.add_argument(
        "--lora-dropout",
        type=float,
        default=0.05,
        help="LoRA dropout rate."
    )
    parser.add_argument(
        "--max-time-minutes",
        type=float,
        default=None,
        help="Maximum training time in minutes before stopping gracefully (e.g. 5.0)."
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge LoRA adapters into base model weights after training."
    )
    return parser.parse_args()


class ChatDataset:
    """PyTorch-compatible dataset for ChatML JSONL samples."""

    def __init__(self, tokenized_samples: List[Dict[str, List[int]]]):
        self.samples = tokenized_samples

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, List[int]]:
        return self.samples[idx]


def collate_fn_factory(pad_token_id: int):
    """Creates a collate function that pads tensors dynamically to the longest sequence in the batch."""
    import torch

    def collate_fn(batch: List[Dict[str, List[int]]]) -> Dict[str, torch.Tensor]:
        max_len = max(len(item["input_ids"]) for item in batch)
        input_ids_list = []
        attention_mask_list = []
        labels_list = []

        for item in batch:
            input_ids = item["input_ids"]
            padding_len = max_len - len(input_ids)

            padded_input_ids = input_ids + [pad_token_id] * padding_len
            padded_mask = [1] * len(input_ids) + [0] * padding_len
            # Mask out padding tokens with -100 so loss ignores them
            padded_labels = input_ids + [-100] * padding_len

            input_ids_list.append(padded_input_ids)
            attention_mask_list.append(padded_mask)
            labels_list.append(padded_labels)

        return {
            "input_ids": torch.tensor(input_ids_list, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask_list, dtype=torch.long),
            "labels": torch.tensor(labels_list, dtype=torch.long),
        }

    return collate_fn


def load_dataset(dataset_path: str, tokenizer: Any, max_seq_len: int, dry_run: bool = False):
    """Loads ChatML JSONL and tokenizes using the tokenizer's chat template."""
    import torch
    from torch.utils.data import DataLoader

    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found at: {dataset_path}")

    tokenized_samples: List[Dict[str, List[int]]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            messages = entry.get("messages", [])

            # Apply Qwen ChatML template
            formatted_text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
            )

            tokens = tokenizer(
                formatted_text,
                truncation=True,
                max_length=max_seq_len,
                add_special_tokens=False,
            )
            tokenized_samples.append({"input_ids": tokens["input_ids"]})

            if dry_run and len(tokenized_samples) >= 2:
                break

    print(f"Loaded {len(tokenized_samples)} samples from {dataset_path}")

    pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    collate = collate_fn_factory(pad_id)
    dataset = ChatDataset(tokenized_samples)
    return DataLoader(dataset, batch_size=2 if dry_run else 1, shuffle=not dry_run, collate_fn=collate)


def train_loop(
    model: Any,
    dataloader: Any,
    optimizer: Any,
    device: Any,
    epochs: int,
    grad_accum: int,
    dry_run: bool = False,
    max_time_minutes: float = None,
):
    """Native PyTorch optimization loop with explicit loss calculation and backpropagation."""
    import time
    import torch

    model.train()
    step_count = 0
    running_loss = 0.0
    start_time = time.time()

    print("\n--- Starting Training Loop ---")
    if max_time_minutes:
        print(f"Time limit active: {max_time_minutes} minute(s)")

    for epoch in range(1 if dry_run else epochs):
        print(f"\n>>> Epoch {epoch + 1}/{1 if dry_run else epochs}")
        optimizer.zero_grad()

        for step, batch in enumerate(dataloader, start=1):
            if max_time_minutes and (time.time() - start_time) >= (max_time_minutes * 60):
                print(f"\n[TIME LIMIT REACHED] Stopped gracefully after {max_time_minutes} minute(s).")
                return

            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )
            loss = outputs.loss / grad_accum
            loss.backward()
            running_loss += loss.item() * grad_accum

            if step % grad_accum == 0 or step == len(dataloader):
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()
                optimizer.zero_grad()
                step_count += 1

                avg_loss = running_loss / (grad_accum if step % grad_accum == 0 else step % grad_accum)
                print(f"  Step {step_count} | Batch {step}/{len(dataloader)} | Loss: {avg_loss:.4f}")
                running_loss = 0.0

            if dry_run:
                print("  [Dry-Run] 1 training step completed successfully.")
                return


def main():
    args = parse_args()

    print("=" * 60)
    print("Edge Clean Copilot — LoRA Fine-Tuning Pipeline")
    print(f"Base Model:     {args.model_id}")
    print(f"Dataset:        {args.dataset}")
    print(f"Execution Mode: {'DRY-RUN (Cold Staging)' if args.dry_run else 'HOT BURST (Training)'}")
    print(f"LoRA Rank (r):  {args.lora_r} | Alpha: {args.lora_alpha}")
    print("=" * 60)

    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from peft import LoraConfig, get_peft_model, TaskType
    except ImportError as e:
        print(f"\n[ERROR] Missing required ML dependencies: {e}", file=sys.stderr)
        print("Please install requirements using: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device selected: {device}")

    # Determine optimal dtype for DGX Spark (bfloat16) vs CPU (float32)
    torch_dtype = torch.bfloat16 if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else torch.float32

    print(f"Loading tokenizer: {args.model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dataloader = load_dataset(args.dataset, tokenizer, args.max_seq_len, dry_run=args.dry_run)

    print(f"Loading base model: {args.model_id} (dtype: {torch_dtype})...")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        torch_dtype=torch_dtype,
        trust_remote_code=True,
    ).to(device)

    # Configure LoRA targets (Attention projections + MLP layers)
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none",
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

    # Run native optimization loop
    train_loop(
        model=model,
        dataloader=dataloader,
        optimizer=optimizer,
        device=device,
        epochs=args.epochs,
        grad_accum=args.grad_accum,
        dry_run=args.dry_run,
        max_time_minutes=args.max_time_minutes,
    )

    # Save trained LoRA adapters
    output_path = Path(args.output_dir)
    adapter_path = output_path / "lora_adapters"
    adapter_path.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving LoRA adapters to: {adapter_path}")
    model.save_pretrained(str(adapter_path))
    tokenizer.save_pretrained(str(adapter_path))

    # Optional weight merge for GGUF quantization
    if args.merge:
        print("\nMerging LoRA adapter weights into base model...")
        merged_model = model.merge_and_unload()
        merged_path = output_path / "merged_model"
        merged_path.mkdir(parents=True, exist_ok=True)
        print(f"Saving merged 16-bit model to: {merged_path}")
        merged_model.save_pretrained(str(merged_path))
        tokenizer.save_pretrained(str(merged_path))
        print("Model merged successfully. Ready for llama.cpp GGUF conversion.")

    print("\n[SUCCESS] Pipeline finished.")


if __name__ == "__main__":
    main()
