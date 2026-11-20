# Verification record — 2026-11-17

This document and `test_results.json` are evaluator-only. Tests below are implementation checks, not measured Agent performance.

## Original sources and reference answers

| Check | task_01 | task_02 |
|---|---|---|
| Author input obtained | Complete `protocols/ex1.vcf` and `pedigree.tfam` members from the author's SourceForge ZIP | Complete official `Pfeiffer-quartet.vcf.gz`, PED and multisample YAML at pinned commit |
| Variant found in actual input | `7:117227832 G>T` | `10:123256215 T>G` |
| Author-specific causal evidence | Official Example 1 final-filter explanation and `ex1.filtered.vcf` | 2015 paper, Anticipated Results: explicit allele; quartet's author-supplied SPIKED/DiseaseGene record confirms the same allele |
| Assembly evidence | `source_GENOME_REFERENCE=NCBI build 37`; tutorial GRCh37.75 | VCF `assembly=b37` and `human_g1k_v37.fasta`; family YAML `genomeAssembly: hg19` |
| Independent reference-base check | UCSC hg19 chr7 interval `[117227831,117227832)` returned `G` | UCSC hg19 chr10 interval `[123256214,123256215)` returned `T` |
| Actual VCF size | 743,154 records / 17 samples | 300,036 records / 4 samples |
| Genotype finding | Affected NA12879/NA12885/NA12886: `1/1`; both parents: `1/0` | Affected daughter ISDBM322017: `1/0`; other three: `0/0` |

Assembly and target-base checks use two independent kinds of evidence; the FASTA was not silently lifted over. Exact source URLs, SHA-256 values and target genotypes are retained in each `reference.json` and `filelink.md`. A reference base lookup corroborates allele orientation; it is not the source of the disease truth label.

For task_01, eight unaffected relatives are heterozygous at the target and six have missing `.` calls: NA12880, NA12881, NA12887, NA12890, NA12891, NA12893. No nonmissing unaffected individual is homozygous alternate. The source's affected status was checked against TFAM, independently of genotype interpretation.

For task_02, the paper's exact-allele description is in its anticipated singleton results; the paper also explicitly supplies a quartet in Box 1B and Box 2. The benchmark's actual family input was independently checked for that same allele and the family genotypes. The family file was not replaced by the singleton. HPO identifiers were read from the official family-analysis YAML and checked against Box 1B.

## Download issues and resolution

- SnpEff's current tutorial S3 link returned HTTP 404, `NoSuchKey`. The archive remains accessible from the author's SourceForge project, with the same name and matching tutorial contents.
- The SourceForge archive contains 480,782,027 bytes, including large conservation tracks not needed for this task. For this audit its ZIP central directory and complete required members were obtained by HTTP byte-range requests. Decompressed size and ZIP CRC32 were checked: `ex1.vcf` 64,431,656 bytes / CRC32 619755039; `pedigree.tfam` 606 bytes / CRC32 1500460635; `ex1.filtered.vcf` 10,172 bytes / CRC32 1258351450. Local SHA-256 values are recorded in filelink/config/reference metadata.
- SourceForge publishes whole-archive SHA-256 `4842273552fbfa6cb7e99acef26b7a025fc7efc3def1e6ac3e7bc9cf2c2d15ce`; this was **not** independently calculated for the entire ZIP in this build. Full-archive download/extraction commands are provided for users.
- Exomiser inputs were read from official commit `98f4e0b6f2f3f5bf790a9f955808c98968559996`; all required source files were available. Occasional transfer timeouts were resolved by retrying the original sources.

No source-data or reference-answer verification blocker remains. No replacement data or prediction-derived truth was created.

## Input separation checks

`prepare_inputs.py` ran successfully on both real inputs. A separate streaming verification compared **every** original and prepared CHROM/POS/REF/ALT and per-sample GT, in order; both comparisons were identical. All original records and sample IDs were retained. The prepared TFAM/PED transformation changes only unknown-parent representation from `NA` to `0` where necessary.

The prepared VCFs contain only GT sample values; all records uniformly omit ID/QUAL/FILTER/INFO content. This removes `SPIKED`, `DiseaseGene` and precomputed effect annotations without selectively treating the answer. Header and prompt scans found no answer gene/protein strings or spiking markers; prompt scans also found no causal coordinates. Coordinates naturally remain in the VCF among all variants.

Only `prompt.md`, `input/variants.vcf`, `input/family.ped` and `input/case.json` were present in each prepared workspace. The case-information blocks in task READMEs match the configuration exactly. Input hashes in the download pages, configuration and reference verification agree. The selected resource profile and its loss of quality fields are disclosed in the project README.

This validates the **contents** of prepared workspaces. An external runner must still enforce filesystem/network isolation; no live Agent session was run to prove sandbox permissions.

## Executed scoring tests

Executed with Python 3.14.6: **22 unittest methods passed, zero failures and zero errors**. Several methods cover multiple invalid-input cases and both tasks. Run `python scripts/test_benchmark.py` to reproduce.

For each of the two real reference answers, the following artificial candidate-list tests passed:

| Candidate-list scenario | Top-1 | Recall@5 | MRR |
|---|---:|---:|---:|
| Correct allele rank 1 | 1 | 1 | 1 |
| Correct allele rank 2 | 0 | 1 | 0.5 |
| Correct allele rank 5 | 0 | 1 | 0.2 |
| Correct allele rank 10 | 0 | 0 | 0.1 |
| Correct allele absent | 0 | 0 | 0 |
| Correct gene, wrong ALT | 0 | 0 | 0 |
| Empty list | 0 | 0 | 0 |

Gene-only matching gave auxiliary gene accuracy 1 and no variant credit. Further passing tests include chromosome/allele-case equivalence, optional gene omission, padded SNV matching, normalized duplicates, malformed JSON, duplicate object keys, NaN, invalid types/fields, excessive candidates, symbolic alleles, missing task outputs, indel left alignment, REF mismatch, chromosome-start boundary and multiline FASTA access.

The two-task aggregation test used ranks 1 and 5: overall Top-1 = 0.5, Recall@5 = 1, MRR = 0.6. Repeated CLI scoring with identical inputs produced byte-identical JSON. Invalid CLI input returned exit 2, a structured error on stderr and no score on stdout.

The detailed executed log, per-task scenario values and prepared-input audit hashes are in [test_results.json](test_results.json). The full optional bioinformatics tool environment, annotation databases and end-to-end Agent diagnostic performance were not tested. Those remain deployment choices, not unresolved causal-variant evidence.
