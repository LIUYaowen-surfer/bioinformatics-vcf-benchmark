#!/usr/bin/env python3
"""Prepare an answer-free GT-only input view from verified original author files."""
import argparse
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

from validate_output import ValidationError, load_json

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def open_text(path):
    return gzip.open(path, "rt", encoding="utf-8") if str(path).endswith(".gz") else Path(path).open(encoding="utf-8")


def read_pedigree(path):
    rows = []
    with open_text(path) as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            row = line.split()
            if len(row) != 6:
                raise ValidationError("PED/TFAM must contain six columns")
            row[2:4] = ["0" if parent == "NA" else parent for parent in row[2:4]]
            rows.append(row)
    if len({row[1] for row in rows}) != len(rows):
        raise ValidationError("Duplicate pedigree sample ID")
    return rows


def prepare(task_id, source_dir, output_dir):
    task = load_json(ROOT / "eval_config.yaml")["tasks"][task_id]
    reference = load_json(ROOT / task_id / "reference.json")
    if reference["verification"]["status"] != "verified":
        raise ValidationError("Task source verification is incomplete")
    out = Path(output_dir).resolve()
    if out == ROOT or ROOT in out.parents:
        raise ValidationError("Agent workspace must be outside the benchmark repository")
    # Avoid leaking unrelated files into an ostensibly clean Agent workspace.
    if out.exists() and any(out.iterdir()):
        raise ValidationError("Output workspace must be new or empty")
    sources = {}
    for item in task["inputs"]:
        path = Path(source_dir) / item["source_path"]
        if not path.is_file() or sha256(path) != item["sha256"]:
            raise ValidationError(f"Missing/changed original input: {path}")
        sources[item["role"]] = path
    rows = read_pedigree(sources["pedigree"])
    expected = reference["verification"]["sample_genotypes"]
    if {r[1] for r in rows} != set(expected):
        raise ValidationError("Pedigree samples do not match verified author data")
    affected = [r[1] for r in rows if r[5] == "2"]
    if sorted(affected) != sorted(task["case"]["affected_samples"]):
        raise ValidationError("Affected-status mismatch")
    out.mkdir(parents=True, exist_ok=True)
    inputs = out / "input"
    inputs.mkdir()
    (inputs / "family.ped").write_text("".join("\t".join(r) + "\n" for r in rows), encoding="utf-8")
    counts, found, samples = 0, 0, []
    truth = reference["causal_variants"][0]
    projection_before, projection_after = hashlib.sha256(), hashlib.sha256()
    assembly_seen = False
    with open_text(sources["vcf"]) as src, (inputs / "variants.vcf").open("w", encoding="utf-8", newline="\n") as dst:
        dst.write('##fileformat=VCFv4.2\n##reference=GRCh37\n')
        dst.write('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n')
        for line in src:
            if line.startswith("##"):
                if "NCBI build 37" in line or "assembly=b37" in line or "human_g1k_v37.fasta" in line:
                    assembly_seen = True
                if line.startswith("##contig=") or line.startswith("##ALT="):
                    dst.write(line)
                continue
            if line.startswith("#CHROM"):
                samples = line.rstrip("\r\n").split("\t")[9:]
                if set(samples) != set(expected) or len(samples) != len(expected):
                    raise ValidationError("VCF sample IDs differ from pedigree")
                dst.write(line.rstrip("\r\n") + "\n")
                continue
            if not samples:
                raise ValidationError("Missing VCF column header")
            fields = line.rstrip("\r\n").split("\t")
            if len(fields) != 9 + len(samples):
                raise ValidationError("VCF column count mismatch")
            fmt = fields[8].split(":")
            if "GT" not in fmt:
                raise ValidationError("VCF record lacks GT")
            gi = fmt.index("GT")
            gts = []
            for sample in fields[9:]:
                values = sample.split(":")
                gt = values[gi] if gi < len(values) else "."
                if not re.fullmatch(r"(?:\d+|\.)(?:[/|](?:\d+|\.))*", gt):
                    raise ValidationError(f"Malformed genotype: {gt}")
                gts.append(gt)
            projected = [fields[0], fields[1], fields[3], fields[4], *gts]
            projection_before.update(("\t".join(projected) + "\n").encode())
            output = [fields[0], fields[1], ".", fields[3], fields[4], ".", ".", ".", "GT", *gts]
            dst.write("\t".join(output) + "\n")
            projection_after.update(("\t".join([output[0], output[1], output[3], output[4], *output[9:]]) + "\n").encode())
            counts += 1
            if (fields[0].removeprefix("chr"), int(fields[1]), fields[3], fields[4]) == (
                    truth["chrom"], truth["pos"], truth["ref"], truth["alt"]):
                found += 1
                if dict(zip(samples, gts)) != expected:
                    raise ValidationError("Causal-site genotypes differ from the verified original")
    if not assembly_seen or found != 1 or counts != reference["verification"]["variant_records"]:
        raise ValidationError("Assembly/causal-variant/record-count verification failed")
    if projection_before.digest() != projection_after.digest():
        raise ValidationError("Input projection changed biological fields")
    case = dict(task["case"])
    case.update({"assembly": task["assembly"], "vcf": "input/variants.vcf", "pedigree": "input/family.ped",
                 "input_note": "GT-only VCF: all original variant records, alleles, sample order and genotypes are retained; read-level quality fields and prior annotations are not supplied."})
    (inputs / "case.json").write_text(json.dumps(case, indent=2) + "\n", encoding="utf-8")
    template = (ROOT / "agent_prompt.md").read_text(encoding="utf-8")
    prompt = template.replace("{{CASE_INFORMATION}}", json.dumps(case, indent=2))
    if "{{" in prompt:
        raise ValidationError("Unresolved prompt variable")
    (out / "prompt.md").write_text(prompt, encoding="utf-8")
    # Return evaluator-side audit details; never write them into the Agent workspace.
    return {"task_id": task_id, "status": "verified", "variant_records": counts,
            "sample_count": len(samples), "projection_sha256": projection_before.hexdigest(),
            "prepared_vcf_sha256": sha256(inputs / "variants.vcf"),
            "pedigree_sha256": sha256(inputs / "family.ped"),
            "prompt_sha256": sha256(out / "prompt.md"),
            "raw_input_hashes": {role: sha256(path) for role, path in sources.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, choices=("task_01", "task_02"))
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.task, args.source_dir, args.output_dir), indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc),
                          "action": "Do not use a partially prepared workspace; retry in a new empty directory."}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
