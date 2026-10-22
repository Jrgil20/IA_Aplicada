#!/usr/bin/env python3
"""Automated Clean Architecture Evaluation & Benchmark Harness for Edge Clean Copilot

Evaluates code outputs against the 4 core architectural metrics:
1. Domain Boundary Score (30%): Zero prohibited framework/database imports in core layers.
2. Invariant & Result Pattern Safety (25%): Strict constructor validation & functional Result<T, E>.
3. Ports & Adapters Decoupling (25%): Abstract interface contracts & dependency injection.
4. Any-Type Penalty (20%): Strict avoidance of explicit TypeScript `any` (-5 pts per occurrence).

Supports dual execution modes:
- Offline Mode: Evaluates pre-generated ChatML JSONL sample files.
- Live Mode: Queries an HTTP llama-server/OpenAI endpoint and benchmarks responses in real-time.
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
import urllib.request
import urllib.error

PROHIBITED_IMPORTS = [
    r"express",
    r"fastapi",
    r"typeorm",
    r"prisma",
    r"@prisma/client",
    r"axios",
    r"mongoose",
    r"sqlalchemy",
    r"sqlite3",
    r"pg",
    r"mysql",
    r"mysql2",
    r"flask",
    r"django",
    r"node-fetch",
    r"got",
    r"superagent",
    r"mongodb",
    r"ioredis",
    r"redis",
]

def strip_comments_and_strings(code: str) -> str:
    """Removes single-line comments, block comments, and string literals to prevent false positives."""
    # Remove block comments /* ... */
    clean = re.sub(r"/\*[\s\S]*?\*/", "", code)
    # Remove single-line comments // ...
    clean = re.sub(r"//.*", "", clean)
    # Remove single and double quoted strings and template literals for type checking
    clean = re.sub(r"'(?:\\.|[^'\\])*'", "''", clean)
    clean = re.sub(r'"(?:\\.|[^"\\])*"', '""', clean)
    clean = re.sub(r"`(?:\\.|[^`\\])*`", "``", clean)
    return clean

def evaluate_domain_boundary(code: str) -> Tuple[float, List[str]]:
    """Evaluates Rule 1 (30 pts): Zero prohibited framework or database imports."""
    violations = []
    # Strip comments to avoid catching commented-out imports
    clean_code = re.sub(r"/\*[\s\S]*?\*/", "", code)
    clean_code = re.sub(r"//.*", "", clean_code)

    for lib in PROHIBITED_IMPORTS:
        # Match import ... from 'lib' or require('lib')
        pattern = rf"""(?:import\s+.*?from\s+['"]{lib}['"]|require\s*\(\s*['"]{lib}['"]\s*\))"""
        if re.search(pattern, clean_code, re.IGNORECASE):
            violations.append(f"Prohibited import detected: '{lib}'")

    if len(violations) == 0:
        return 30.0, []
    elif len(violations) == 1:
        return 15.0, violations
    else:
        return 0.0, violations

def evaluate_invariant_safety(code: str) -> Tuple[float, List[str]]:
    """Evaluates Rule 2 (25 pts): Functional Result<T, E> error handling and invariant checks."""
    score = 0.0
    notes = []

    # Check for Result pattern usage (15 pts)
    has_result_type = bool(re.search(r"\bResult\s*<", code))
    has_result_methods = bool(re.search(r"\bResult\.(ok|fail)\b", code))
    if has_result_type or has_result_methods:
        score += 15.0
    else:
        notes.append("Missing Result<T, E> functional return type pattern.")

    # Check for invariant validation in constructor or factory method (10 pts)
    has_validation_logic = bool(
        re.search(r"(throw\s+new\s+(?:Validation|Domain)Error|if\s*\(.*?length.*?\)|if\s*\(.*?!.*?\)\s*(?:return|throw))", code)
    )
    if has_validation_logic:
        score += 10.0
    else:
        notes.append("No explicit invariant validation guard or factory constructor found.")

    return score, notes

def evaluate_port_decoupling(code: str) -> Tuple[float, List[str]]:
    """Evaluates Rule 3 (25 pts): Port interfaces and dependency injection."""
    score = 0.0
    notes = []

    # Check for Port interface definition (15 pts)
    has_port_interface = bool(
        re.search(r"\binterface\s+I[A-Z][A-Za-z0-9]*(?:Repository|Port|Service|Gateway|Publisher)\b", code)
        or re.search(r"\binterface\s+[A-Za-z0-9]*(?:Repository|Port|Gateway)\b", code)
    )
    if has_port_interface:
        score += 15.0
    else:
        notes.append("No explicit Port/Repository abstraction interface found.")

    # Check for dependency injection or adapter implementation (10 pts)
    has_di = bool(
        re.search(r"constructor\s*\(\s*(?:private|public|protected)?\s*(?:readonly)?\s*\w+\s*:\s*I[A-Z]", code)
        or re.search(r"\bimplements\s+[A-Za-z0-9]*(?:Repository|Port|Gateway|Service)\b", code)
    )
    if has_di:
        score += 10.0
    else:
        notes.append("Missing constructor dependency injection or adapter implementation.")

    return score, notes

def evaluate_any_type_penalty(code: str) -> Tuple[float, List[str]]:
    """Evaluates Rule 4 (20 pts): Strict TypeScript typing without `any`."""
    clean_code = strip_comments_and_strings(code)
    notes = []

    # Match explicit `any` in TypeScript typing positions (: any, <any>, as any)
    any_matches = re.findall(r"(?::\s*any\b|<any>|\bas\s+any\b)", clean_code)
    any_count = len(any_matches)

    base_score = 20.0
    penalty = any_count * 5.0
    final_score = max(0.0, base_score - penalty)

    if any_count > 0:
        notes.append(f"Detected {any_count} explicit TypeScript `any` usage(s) (-{penalty:.1f} pts).")

    return final_score, notes

def evaluate_code_sample(code: str) -> Dict[str, Any]:
    """Computes full architectural evaluation metrics for a single code sample."""
    score_boundary, notes_boundary = evaluate_domain_boundary(code)
    score_invariant, notes_invariant = evaluate_invariant_safety(code)
    score_ports, notes_ports = evaluate_port_decoupling(code)
    score_any, notes_any = evaluate_any_type_penalty(code)

    total_score = round(score_boundary + score_invariant + score_ports + score_any, 2)
    grade = (
        "A (Clean Architecture Certified)" if total_score >= 85
        else "B (Partially Clean)" if total_score >= 70
        else "C (Architectural Violations)" if total_score >= 50
        else "F (Coupled / Anti-Pattern)"
    )

    all_notes = notes_boundary + notes_invariant + notes_ports + notes_any

    return {
        "total_score": total_score,
        "grade": grade,
        "metrics": {
            "domain_boundary": {"score": score_boundary, "max": 30.0, "violations": notes_boundary},
            "invariant_safety": {"score": score_invariant, "max": 25.0, "violations": notes_invariant},
            "ports_decoupling": {"score": score_ports, "max": 25.0, "violations": notes_ports},
            "any_penalty": {"score": score_any, "max": 20.0, "violations": notes_any},
        },
        "all_notes": all_notes,
    }

def print_ascii_table(results: List[Dict[str, Any]], elapsed_seconds: float):
    """Renders formatted ASCII summary table to stdout."""
    total_samples = len(results)
    avg_score = sum(r["total_score"] for r in results) / total_samples if total_samples > 0 else 0
    avg_boundary = sum(r["metrics"]["domain_boundary"]["score"] for r in results) / total_samples if total_samples > 0 else 0
    avg_invariants = sum(r["metrics"]["invariant_safety"]["score"] for r in results) / total_samples if total_samples > 0 else 0
    avg_ports = sum(r["metrics"]["ports_decoupling"]["score"] for r in results) / total_samples if total_samples > 0 else 0
    avg_any = sum(r["metrics"]["any_penalty"]["score"] for r in results) / total_samples if total_samples > 0 else 0

    passed_count = sum(1 for r in results if r["total_score"] >= 80)
    pass_rate = (passed_count / total_samples * 100) if total_samples > 0 else 0

    print("\n" + "=" * 80)
    print("           EDGE CLEAN COPILOT — ARCHITECTURAL BENCHMARK REPORT           ")
    print("=" * 80)
    print(f"Total Evaluated Samples: {total_samples}")
    print(f"Evaluation Duration:     {elapsed_seconds:.2f} seconds")
    print(f"Compliance Pass Rate:    {pass_rate:.1f}% ({passed_count}/{total_samples} samples >= 80 pts)")
    print("-" * 80)
    print("METRIC DIMENSION              SCORE / MAX    WEIGHT    COMPLIANCE")
    print("-" * 80)
    print(f"1. Domain Boundary Isolation:   {avg_boundary:5.1f} / 30.0     (30%)     {avg_boundary/30.0*100:5.1f}%")
    print(f"2. Invariant & Result Safety:   {avg_invariants:5.1f} / 25.0     (25%)     {avg_invariants/25.0*100:5.1f}%")
    print(f"3. Port & Adapter Decoupling:   {avg_ports:5.1f} / 25.0     (25%)     {avg_ports/25.0*100:5.1f}%")
    print(f"4. TypeScript Type Rigor:       {avg_any:5.1f} / 20.0     (20%)     {avg_any/20.0*100:5.1f}%")
    print("=" * 80)
    print(f"COMPOSITE CLEAN ARCHITECTURE SCORE:  {avg_score:5.1f} / 100.0")
    print("=" * 80 + "\n")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Edge Clean Copilot Architectural Benchmark Evaluator."
    )
    parser.add_argument("--offline", type=str, default=None, help="Path to JSONL dataset to evaluate offline.")
    parser.add_argument("--url", type=str, default=None, help="llama-server endpoint (e.g. http://127.0.0.1:8085/v1/chat/completions).")
    parser.add_argument("--prompts", type=str, default=None, help="Path to prompts JSONL file for live evaluation.")
    parser.add_argument("--output", type=str, default="benchmark_report.json", help="Path to export JSON report.")
    return parser.parse_args()

def main():
    args = parse_args()
    start_time = time.time()

    if not args.offline and not args.url:
        print("[ERROR] Please specify either --offline <jsonl_file> or --url <endpoint>", file=sys.stderr)
        sys.exit(1)

    eval_results = []

    if args.offline:
        offline_path = Path(args.offline)
        if not offline_path.exists():
            print(f"[ERROR] Offline file not found: {offline_path}", file=sys.stderr)
            sys.exit(1)

        print(f"--> Running Offline Benchmark Evaluation on: {offline_path}")
        with open(offline_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)

                # Extract code content from assistant message or direct 'code' field
                if "messages" in item:
                    content = ""
                    for m in item["messages"]:
                        if m.get("role") == "assistant":
                            content = m.get("content", "")
                            break
                elif "code" in item:
                    content = item["code"]
                elif "assistant" in item:
                    content = item["assistant"]
                else:
                    content = json.dumps(item)

                eval_data = evaluate_code_sample(content)
                eval_data["sample_index"] = idx
                eval_data["label"] = item.get("label", f"Sample #{idx}")
                eval_results.append(eval_data)

    elif args.url:
        if not args.prompts:
            print("[ERROR] When using --url, --prompts <file.jsonl> is required.", file=sys.stderr)
            sys.exit(1)
        prompts_path = Path(args.prompts)
        if not prompts_path.exists():
            print(f"[ERROR] Prompts file not found: {prompts_path}", file=sys.stderr)
            sys.exit(1)

        print(f"--> Running Live Benchmark Evaluation against endpoint: {args.url}")
        with open(prompts_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                prompt_text = item.get("prompt") or item.get("user")

                payload = {
                    "messages": [{"role": "user", "content": prompt_text}],
                    "temperature": 0.1,
                    "max_tokens": 1024,
                }
                req = urllib.request.Request(
                    args.url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                try:
                    with urllib.request.urlopen(req, timeout=120) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                        assistant_response = res["choices"][0]["message"]["content"]
                        eval_data = evaluate_code_sample(assistant_response)
                        eval_data["sample_index"] = idx
                        eval_data["label"] = item.get("label", f"Live Sample #{idx}")
                        eval_results.append(eval_data)
                except Exception as e:
                    print(f"  [ERROR] Prompt #{idx} failed: {e}", file=sys.stderr)

    elapsed = time.time() - start_time
    print_ascii_table(eval_results, elapsed)

    output_path = Path(args.output)
    report_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_samples": len(eval_results),
        "duration_seconds": round(elapsed, 2),
        "average_score": round(sum(r["total_score"] for r in eval_results) / len(eval_results), 2) if eval_results else 0,
        "results": eval_results,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"Report exported to: {output_path.resolve()}\n")

if __name__ == "__main__":
    main()
