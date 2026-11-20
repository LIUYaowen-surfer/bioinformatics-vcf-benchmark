#!/usr/bin/env python3
"""Strict result validation and deterministic small-variant normalization (stdlib)."""
import argparse
import json
import re
import sys
from pathlib import Path


class ValidationError(ValueError):
    pass


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValidationError(f"Duplicate JSON key: {key}")
        obj[key] = value
    return obj


def _invalid_constant(value):
    raise ValidationError(f"Non-JSON numeric constant: {value}")


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"),
                          object_pairs_hook=_unique_object,
                          parse_constant=_invalid_constant)
    except (OSError, UnicodeError, ValueError) as exc:
        raise ValidationError(f"{path}: {exc}") from exc


def normalize_chrom(value):
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValidationError("chrom must be a nonempty string without surrounding spaces")
    chrom = re.sub(r"^chr", "", value, flags=re.I).upper()
    if chrom in {"M", "MT"}:
        return "MT"
    if chrom in {"X", "Y"}:
        return chrom
    if re.fullmatch(r"[0-9]+", chrom) and 1 <= int(chrom) <= 22:
        return str(int(chrom))
    if re.fullmatch(r"[A-Za-z0-9_.-]+", value):
        return value  # Non-primary contig identifiers are preserved exactly.
    raise ValidationError("Invalid chromosome/contig identifier")


class Fasta:
    """Random-access uncompressed FASTA with samtools-compatible .fai index."""
    def __init__(self, path):
        self.path = Path(path)
        self.index = {}
        try:
            for line in Path(str(path) + ".fai").read_text().splitlines():
                name, length, offset, bases, width, *_ = line.split("\t")
                try:
                    chrom = normalize_chrom(name)
                except ValidationError:
                    continue  # decoys/alternate contigs are outside this benchmark
                if chrom in self.index:
                    raise ValidationError(f"Ambiguous FASTA chromosome alias: {chrom}")
                record = tuple(map(int, (length, offset, bases, width)))
                if record[0] < 1 or record[1] < 0 or record[2] < 1 or record[3] < record[2]:
                    raise ValidationError("Malformed FASTA index")
                self.index[chrom] = record
            self.handle = self.path.open("rb")
        except (OSError, ValueError) as exc:
            raise ValidationError(f"Cannot open indexed FASTA {path}: {exc}") from exc

    def close(self):
        self.handle.close()

    def sequence(self, chrom, pos, length):
        if chrom not in self.index:
            raise ValidationError(f"FASTA lacks chromosome {chrom}")
        total, offset, bases, width = self.index[chrom]
        start = pos - 1
        if start < 0 or start + length > total:
            raise ValidationError(f"Variant outside FASTA bounds: {chrom}:{pos}")
        pieces = []
        while length:
            count = min(length, bases - start % bases)
            self.handle.seek(offset + (start // bases) * width + start % bases)
            pieces.append(self.handle.read(count).decode("ascii").upper())
            start += count
            length -= count
        seq = "".join(pieces)
        if not re.fullmatch(r"[ACGTN]+", seq):
            raise ValidationError("FASTA/index mismatch or unsupported reference bases")
        return seq


def normalize_variant(variant, fasta=None):
    if not isinstance(variant, dict):
        raise ValidationError("Each variant must be an object")
    required = {"chrom", "pos", "ref", "alt"}
    if not required <= variant.keys() or variant.keys() - required - {"gene"}:
        raise ValidationError("Variant requires chrom,pos,ref,alt; only gene is optional")
    chrom = normalize_chrom(variant["chrom"])
    pos = variant["pos"]
    if type(pos) is not int or pos < 1:
        raise ValidationError("pos must be a positive JSON integer (not bool/float/string)")
    for field in ("ref", "alt"):
        if not isinstance(variant[field], str) or not re.fullmatch(r"[ACGTacgt]+", variant[field]):
            raise ValidationError(f"{field} must be one explicit A/C/G/T allele; split multi-allelic records")
    ref, alt = variant["ref"].upper(), variant["alt"].upper()
    if ref == alt:
        raise ValidationError("REF and ALT must differ")
    if "gene" in variant and (not isinstance(variant["gene"], str)
            or not variant["gene"].strip() or variant["gene"] != variant["gene"].strip()):
        raise ValidationError("gene, when supplied, must be a nonempty string without outer spaces")
    if fasta and fasta.sequence(chrom, pos, len(ref)) != ref:
        raise ValidationError(f"REF mismatch against FASTA at {chrom}:{pos}")
    if len(ref) != len(alt) and fasta is None:
        raise ValidationError("Indel normalization requires --fasta and its .fai index")
    # Right-trim common sequence; extend left when an allele would become empty.
    # This also rotates indels through repeat sequence to their leftmost position.
    while ref[-1] == alt[-1]:
        if min(len(ref), len(alt)) == 1:
            if fasta is None or pos == 1:
                break
            previous = fasta.sequence(chrom, pos - 1, 1)
            if previous not in "ACGT":
                raise ValidationError("Cannot normalize through an ambiguous reference base")
            ref, alt, pos = previous + ref, previous + alt, pos - 1
        ref, alt = ref[:-1], alt[:-1]
    while len(ref) > 1 and len(alt) > 1 and ref[0] == alt[0]:
        ref, alt, pos = ref[1:], alt[1:], pos + 1
    result = {"chrom": chrom, "pos": pos, "ref": ref, "alt": alt}
    if "gene" in variant:
        result["gene"] = variant["gene"].upper()
    return result


def variant_key(variant):
    return tuple(variant[field] for field in ("chrom", "pos", "ref", "alt"))


def validate_output(data, fasta=None, max_candidates=10):
    if not isinstance(data, dict) or set(data) != {"variants"}:
        raise ValidationError("Top-level object must contain exactly 'variants'")
    if not isinstance(data["variants"], list) or len(data["variants"]) > max_candidates:
        raise ValidationError(f"variants must be an array with 0-{max_candidates} entries")
    normalized, seen = [], set()
    for rank, variant in enumerate(data["variants"], 1):
        try:
            item = normalize_variant(variant, fasta)
        except ValidationError as exc:
            raise ValidationError(f"Candidate {rank}: {exc}") from exc
        key = variant_key(item)
        if key in seen:
            raise ValidationError(f"Duplicate normalized variant at rank {rank}: {key}")
        seen.add(key)
        normalized.append(item)
    return {"variants": normalized}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--fasta", type=Path, help="Matching GRCh37/hg19 FASTA; required for indels")
    args = parser.parse_args()
    fasta = None
    try:
        fasta = Fasta(args.fasta) if args.fasta else None
        normalized = validate_output(load_json(args.result), fasta)
        print(json.dumps({"valid": True, "candidate_count": len(normalized["variants"]),
                          "normalized_result": normalized}, indent=2))
        return 0
    except (ValidationError, OSError, UnicodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}), file=sys.stderr)
        return 2
    finally:
        if fasta:
            fasta.close()


if __name__ == "__main__":
    sys.exit(main())
