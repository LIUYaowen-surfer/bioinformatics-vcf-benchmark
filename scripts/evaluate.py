#!/usr/bin/env python3
"""Evaluate one task or both equal-weight tasks; Python standard library only."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from validate_output import (Fasta, ValidationError, load_json, normalize_variant,
                             validate_output, variant_key)

ROOT = Path(__file__).resolve().parents[1]
TASKS = ("task_01", "task_02")


def score_task(result, reference, fasta=None):
    if reference.get("task_id") not in TASKS:
        raise ValidationError("Unknown reference task_id")
    if reference.get("assembly") not in {"GRCh37", "hg19"}:
        raise ValidationError("Unsupported reference assembly; no liftover is performed")
    causal = reference.get("causal_variants")
    if not isinstance(causal, list) or len(causal) != 1:
        raise ValidationError("This benchmark requires exactly one causal variant per task")
    truth = normalize_variant(causal[0], fasta)
    variants = validate_output(result, fasta)["variants"]
    rank = next((i for i, v in enumerate(variants, 1) if variant_key(v) == variant_key(truth)), None)
    # Auxiliary TOP-1 reported-symbol match, not a coordinate-to-gene annotation engine.
    gene = (int(variants[0]["gene"] == truth["gene"])
            if variants and "gene" in variants[0] and "gene" in truth else None)
    if not variants:
        gene = 0
    return {"task_id": reference["task_id"], "assembly": reference["assembly"],
            "candidate_count": len(variants), "causal_variant_rank": rank,
            "top1_accuracy": int(rank == 1), "recall_at_5": int(rank is not None and rank <= 5),
            "mrr": 1 / rank if rank else 0.0, "gene_level_accuracy": gene}


def aggregate(scores):
    if {s["task_id"] for s in scores} != set(TASKS) or len(scores) != 2:
        raise ValidationError("Overall metrics require exactly task_01 and task_02")
    genes = [s["gene_level_accuracy"] for s in scores]
    return {"overall_top1_accuracy": sum(s["top1_accuracy"] for s in scores) / 2,
            "overall_recall_at_5": sum(s["recall_at_5"] for s in scores) / 2,
            "overall_mrr": sum(s["mrr"] for s in scores) / 2,
            "overall_gene_level_accuracy": sum(genes) / 2 if None not in genes else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--task", choices=TASKS)
    mode.add_argument("--results-dir", type=Path, help="Contains task_01/result.json and task_02/result.json")
    parser.add_argument("--result", type=Path, help="Required with --task")
    parser.add_argument("--fasta", type=Path, help="Matching uncompressed GRCh37/hg19 FASTA with .fai")
    parser.add_argument("--output", type=Path, help="Also write scores as JSON")
    args = parser.parse_args()
    if bool(args.task) != bool(args.result):
        parser.error("--task and --result must be supplied together")
    fasta = None
    try:
        config = load_json(ROOT / "eval_config.yaml")  # JSON is a YAML 1.2 subset.
        if config["task_ids"] != list(TASKS) or config["max_candidates"] != 10:
            raise ValidationError("Config does not match this benchmark version")
        fasta = Fasta(args.fasta) if args.fasta else None
        scores, hashes = [], {}
        task_ids = [args.task] if args.task else TASKS
        for task_id in task_ids:
            result_path = args.result if args.task else args.results_dir / task_id / "result.json"
            ref_path = ROOT / task_id / "reference.json"
            reference = load_json(ref_path)
            if reference["task_id"] != task_id:
                raise ValidationError("Reference task_id/path mismatch")
            scores.append(score_task(load_json(result_path), reference, fasta))
            hashes[task_id] = {"result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
                               "reference_sha256": hashlib.sha256(ref_path.read_bytes()).hexdigest()}
        report = {"benchmark": config["benchmark"], "version": config["version"],
                  "primary_metric": "overall_mrr", "tasks": scores, "file_hashes": hashes,
                  "overall": aggregate(scores) if not args.task else None}
        serialized = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.output:
            args.output.write_text(serialized, encoding="utf-8")
        print(serialized, end="")
        return 0
    except (ValidationError, OSError, UnicodeError, KeyError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}), file=sys.stderr)
        return 2
    finally:
        if fasta:
            fasta.close()


if __name__ == "__main__":
    sys.exit(main())
