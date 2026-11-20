#!/usr/bin/env python3
"""Executable scoring/validation regression tests; fixtures are not benchmark cases."""
import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evaluate import ROOT, aggregate, score_task
from validate_output import Fasta, ValidationError, load_json, normalize_variant, validate_output


class BenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.refs = [load_json(ROOT / task / "reference.json") for task in ("task_01", "task_02")]

    def ranked(self, ref, rank):
        variants = [{"chrom": "1", "pos": i + 100, "ref": "A", "alt": "C", "gene": "OTHER"}
                    for i in range(10)]
        if rank:
            variants[rank - 1] = copy.deepcopy(ref["causal_variants"][0])
        return {"variants": variants}

    def check_rank(self, rank):
        for ref in self.refs:
            with self.subTest(task=ref["task_id"]):
                score = score_task(self.ranked(ref, rank), ref)
                self.assertEqual(score["causal_variant_rank"], rank)
                self.assertEqual(score["top1_accuracy"], int(rank == 1))
                self.assertEqual(score["recall_at_5"], int(rank <= 5))
                self.assertEqual(score["mrr"], 1 / rank)

    def test_rank_1(self): self.check_rank(1)
    def test_rank_2(self): self.check_rank(2)
    def test_rank_5(self): self.check_rank(5)
    def test_rank_10(self): self.check_rank(10)

    def test_no_hit(self):
        for ref in self.refs:
            score = score_task(self.ranked(ref, None), ref)
            self.assertEqual((score["top1_accuracy"], score["recall_at_5"], score["mrr"]), (0, 0, 0))

    def test_empty_output(self):
        for ref in self.refs:
            self.assertEqual(score_task({"variants": []}, ref)["mrr"], 0)

    def test_gene_only_correct(self):
        for ref in self.refs:
            result = self.ranked(ref, 1)
            result["variants"][0]["alt"] = "C" if ref["task_id"] == "task_01" else "A"
            score = score_task(result, ref)
            self.assertEqual(score["gene_level_accuracy"], 1)
            self.assertEqual((score["top1_accuracy"], score["recall_at_5"], score["mrr"]), (0, 0, 0))

    def test_chr_alias_and_allele_case(self):
        ref = self.refs[0]
        result = self.ranked(ref, 1)
        result["variants"][0].update(chrom="chr7", ref="g", alt="t", gene="cftr")
        self.assertEqual(score_task(result, ref)["mrr"], 1)

    def test_duplicate_normalized_variant_rejected(self):
        v = self.refs[0]["causal_variants"][0]
        for duplicate in (dict(v), dict(v, chrom="chr7"), dict(v, ref="g", alt="t", gene="OTHER")):
            with self.assertRaises(ValidationError):
                validate_output({"variants": [v, duplicate]})

    def test_padded_snv_and_duplicate(self):
        v = self.refs[0]["causal_variants"][0]
        padded = dict(v, pos=v["pos"] - 1, ref="AGA", alt="ATA")
        self.assertEqual(score_task({"variants": [padded]}, self.refs[0])["mrr"], 1)
        with self.assertRaises(ValidationError):
            validate_output({"variants": [v, padded]})

    def test_optional_gene(self):
        result = self.ranked(self.refs[0], 1)
        del result["variants"][0]["gene"]
        score = score_task(result, self.refs[0])
        self.assertEqual(score["mrr"], 1)
        self.assertIsNone(score["gene_level_accuracy"])

    def test_invalid_shapes(self):
        v = self.refs[0]["causal_variants"][0]
        bad = [[], {}, {"variants": {}}, {"variants": [], "comment": "x"},
               {"variants": [v] * 11}, {"variants": [None]},
               {"variants": [{k: value for k, value in v.items() if k != "alt"}]}]
        for result in bad:
            with self.subTest(result=result), self.assertRaises(ValidationError):
                validate_output(result)

    def test_invalid_fields(self):
        v = self.refs[0]["causal_variants"][0]
        replacements = [("pos", x) for x in (True, 0, -1, 1.0, "1")]
        replacements += [("alt", x) for x in ("T,C", "<DEL>", "*", "N", "G", "")]
        replacements += [("chrom", x) for x in (7, "", "chr7 ")]
        replacements += [("gene", x) for x in (None, [], "", " CFTR")]
        replacements += [("confidence", 1)]
        for key, value in replacements:
            with self.subTest(key=key, value=value), self.assertRaises(ValidationError):
                validate_output({"variants": [dict(v, **{key: value})]})

    def test_json_syntax_duplicate_keys_nan(self):
        bad = ['{"variants": [}', '{"variants": [], "variants": []}',
               '{"variants": [], "x": NaN}', '```json\n{"variants": []}\n```',
               '{"variants": []} prose', '{"variants": [{"pos": 1, "pos": 2}]}']
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            for text in bad:
                path.write_text(text)
                with self.subTest(text=text), self.assertRaises(ValidationError):
                    load_json(path)

    def test_indels_require_reference(self):
        with self.assertRaises(ValidationError):
            validate_output({"variants": [{"chrom": "1", "pos": 3, "ref": "AA", "alt": "A"}]})

    def test_indel_left_alignment_and_ref_check(self):
        # Small synthetic sequence used only to test normalization, never as case data.
        with tempfile.TemporaryDirectory() as tmp:
            fa = Path(tmp) / "test.fa"
            fa.write_bytes(b">chr1\nCAAAAT\n")
            Path(str(fa) + ".fai").write_text("chr1\t6\t6\t6\t7\n")
            fasta = Fasta(fa)
            try:
                deletion = {"chrom": "1", "pos": 3, "ref": "AA", "alt": "A"}
                insertion = {"chrom": "1", "pos": 4, "ref": "A", "alt": "AA"}
                self.assertEqual(normalize_variant(deletion, fasta), {"chrom": "1", "pos": 1, "ref": "CA", "alt": "C"})
                self.assertEqual(normalize_variant(insertion, fasta), {"chrom": "1", "pos": 1, "ref": "C", "alt": "CA"})
                with self.assertRaises(ValidationError):
                    validate_output({"variants": [deletion, dict(deletion, pos=2)]}, fasta)
                with self.assertRaises(ValidationError):
                    normalize_variant(dict(deletion, ref="TT"), fasta)
                self.assertEqual(fasta.sequence("1", 2, 4), "AAAA")
            finally:
                fasta.close()

    def test_two_task_equal_weight(self):
        scores = [score_task(self.ranked(ref, rank), ref) for ref, rank in zip(self.refs, [1, 5])]
        overall = aggregate(scores)
        self.assertEqual(overall["overall_mrr"], 0.6)
        self.assertEqual(overall["overall_top1_accuracy"], 0.5)
        self.assertEqual(overall["overall_recall_at_5"], 1)
        with self.assertRaises(ValidationError): aggregate(scores[:1])
        with self.assertRaises(ValidationError): aggregate([scores[0], scores[0]])

    def test_cli_and_deterministic_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            for ref in self.refs:
                path = tmp / ref["task_id"] / "result.json"
                path.parent.mkdir()
                path.write_text(json.dumps(self.ranked(ref, 2)))
            command = [sys.executable, str(ROOT / "scripts/evaluate.py"), "--results-dir", str(tmp)]
            first = subprocess.run(command, capture_output=True, check=True)
            second = subprocess.run(command, capture_output=True, check=True)
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(json.loads(first.stdout)["overall"]["overall_mrr"], 0.5)
            result = tmp / "task_01/result.json"
            valid = subprocess.run([sys.executable, str(ROOT / "scripts/validate_output.py"), str(result)], capture_output=True)
            self.assertEqual(valid.returncode, 0)
            result.write_text('{"variants": [}')
            invalid = subprocess.run(command, capture_output=True)
            self.assertEqual(invalid.returncode, 2)
            self.assertEqual(invalid.stdout, b"")
            self.assertFalse(json.loads(invalid.stderr)["valid"])
            result.unlink()
            missing = subprocess.run(command, capture_output=True)
            self.assertEqual(missing.returncode, 2)
            self.assertEqual(missing.stdout, b"")

    def test_config_reference_case_consistency(self):
        config = load_json(ROOT / "eval_config.yaml")
        self.assertEqual(config["task_ids"], [r["task_id"] for r in self.refs])
        self.assertEqual(config["max_candidates"], 10)
        for ref in self.refs:
            task = config["tasks"][ref["task_id"]]
            self.assertEqual(task["assembly"], ref["assembly"])
            self.assertEqual(task["inputs"][0]["sha256"], ref["verification"]["input_vcf_sha256"])
            samples = set(task["case"]["affected_samples"]) | set(task["case"]["unaffected_samples"])
            self.assertEqual(samples, set(ref["verification"]["sample_genotypes"]))
            readme = (ROOT / ref["task_id"] / "README.md").read_text(encoding="utf-8")
            block = re.search(r"<!-- BEGIN AGENT CASE -->\s*```json\s*(.*?)\s*```", readme, re.S)
            self.assertIsNotNone(block)
            self.assertEqual(json.loads(block.group(1)), task["case"])
            links = (ROOT / ref["task_id"] / "filelink.md").read_text(encoding="utf-8")
            for item in task["inputs"]:
                self.assertIn(item["sha256"], links)

    def test_case_prompt_does_not_reveal_truth(self):
        config = load_json(ROOT / "eval_config.yaml")
        template = (ROOT / "agent_prompt.md").read_text(encoding="utf-8")
        for ref in self.refs:
            prompt = template.replace("{{CASE_INFORMATION}}", json.dumps(config["tasks"][ref["task_id"]]["case"]))
            for secret in (str(ref["causal_variants"][0]["pos"]), ref["causal_variants"][0]["gene"], "Gly542", "SPIKED", "DiseaseGene"):
                self.assertNotIn(secret, prompt)

    def test_contig_preservation(self):
        result = validate_output({"variants": [{"chrom": "GL000192.1", "pos": 5, "ref": "A", "alt": "C"}]})
        self.assertEqual(result["variants"][0]["chrom"], "GL000192.1")

    def test_indel_at_contig_start_and_multiline_fasta(self):
        with tempfile.TemporaryDirectory() as tmp:
            fa = Path(tmp) / "test.fa"
            fa.write_bytes(b">1\nAAA\nAAT\n")
            Path(str(fa) + ".fai").write_text("1\t6\t3\t3\t4\n")
            fasta = Fasta(fa)
            try:
                self.assertEqual(fasta.sequence("1", 2, 4), "AAAA")
                self.assertEqual(normalize_variant({"chrom": "1", "pos": 3, "ref": "AA", "alt": "A"}, fasta),
                                 {"chrom": "1", "pos": 1, "ref": "AA", "alt": "A"})
                with self.assertRaises(ValidationError):
                    fasta.sequence("1", 6, 2)
            finally:
                fasta.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
