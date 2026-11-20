# Bioinformatics VCF Benchmark

## Overview

**bioinformatics-vcf-benchmark v0.1.0** evaluates whether an AI Agent can identify and rank an author-specified causal Mendelian variant from VCF genotypes, family relationships and available phenotypes. It contains exactly two teaching/methodology cases. It is independent of the DEG benchmark and follows its task-level documentation / download links / reference organization.

Only final variant identity and rank are scored. There is no LLM judge, process score, required software, required filtering threshold or prescribed analysis pipeline. **Overall MRR is the primary leaderboard metric.** Gene names alone never earn variant-level credit.

| Task | Author example | Assembly | Original input | Family |
|---|---|---|---|---|
| [task_01](task_01/README.md) | SnpEff Example 1: Coding variants | GRCh37 | 743,154 records on chromosomes 7 and 17 | 17 members; 3 affected siblings |
| [task_02](task_02/README.md) | Exomiser Pfeiffer quartet | hg19 / b37 | 300,036 records in the actual quartet file | Affected daughter and 3 unaffected relatives |

These record counts were measured from the downloaded files, not inferred from generic descriptions of the tutorials. Both causal alleles and their sample genotypes have been checked against the real VCFs.

## Repository structure

- `README.md`: use and evaluation protocol.
- `eval_config.yaml`: tasks, hashes, case variables, schema, metrics and environment recommendations. It uses JSON syntax, a valid YAML 1.2 subset, to keep the scripts dependency-free.
- `agent_prompt.md`: one shared English prompt; only `{{CASE_INFORMATION}}` changes.
- `task_01/` and `task_02/`: each contains `README.md`, `filelink.md`, `reference.json`.
- `scripts/validate_output.py`: strict JSON validation and normalization.
- `scripts/evaluate.py`: deterministic single-task and two-task scoring.
- `scripts/prepare_inputs.py`: verified source-to-input preparation, with no variant prioritization.
- `scripts/test_benchmark.py`: scoring and validation regression tests.

Raw VCFs, source archives and large analysis databases are downloaded separately. No synthetic replacement cases are supplied. Unit-test fixtures only exercise scoring/normalization and are not additional tasks.

## Environment

The **benchmark utilities require only Python 3.11+**, with no third-party packages; Python 3.12 is a recommended baseline. They were executed with Python 3.14.6. An uncompressed matching FASTA plus `.fai` is additionally required when a submitted candidate is an indel. SNV-only submissions can be scored without a genome download.

Agent analysis tools are optional choices. A suggested Linux/WSL environment is Python 3.12, bcftools 1.22, pysam 0.24.1 and SnpEff 5.2, with Exomiser 15.1.1 and Java 21+ as optional additions. VEP, ANNOVAR, R or other reasonable tools may be substituted. See the official [bcftools](https://samtools.github.io/bcftools/bcftools.html), [pysam](https://pysam.readthedocs.io/en/stable/installation.html), [SnpEff](https://pcingola.github.io/SnpEff/download/) and [Exomiser](https://exomiser.readthedocs.io/en/latest/installation.html) documentation. This is a recommended tool list, not a tested full environment lock.

Prepare GRCh37-compatible reference sequences, transcript annotations and, if desired, population-frequency, ClinVar, HPO and phenotype resources. One reference option is [Ensembl GRCh37 release 75 primary assembly FASTA](https://ftp.ensembl.org/pub/grch37/release-75/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.75.dna.primary_assembly.fa.gz). After decompression, an index can be created with `samtools faidx genome.fa` (samtools is optional for index creation, not scoring). SnpEff's tutorial uses `GRCh37.75`; Exomiser requires compatible hg19 and phenotype bundles. Do not substitute hg38 or assume every non-primary/mitochondrial sequence is interchangeable between b37 and UCSC hg19. Both benchmark answers are autosomal SNVs.

Before a comparative Agent run, freeze and record installed versions, database releases/checksums, permitted network access, CPU/RAM/time limits and available storage. Use the same resources for the Agents being compared. The delivered project does not install or run a full annotation stack.

## Workflow

**Clone repository → Download original data → Prepare input files → Run Agent → Save result.json → Run evaluator → View scores**

### 1. Obtain the project and author data

Clone the repository and enter the project directory:

```bash
git clone https://github.com/LIUYaowen-surfer/bioinformatics-vcf-benchmark.git
cd bioinformatics-vcf-benchmark
```

Download the exact files listed in [task_01/filelink.md](task_01/filelink.md) and [task_02/filelink.md](task_02/filelink.md) into an evaluator-owned `downloads/` directory. Do not download the singleton Pfeiffer example as a substitute.

The SnpEff tutorial's S3 link currently returns HTTP 404. Its author's SourceForge `protocols.zip` remains available and was used for verification. File hashes in the configuration pin the actual input bytes. Exomiser downloads are pinned to an immutable Git commit.

### 2. Prepare isolated Agent inputs

From the project root, with author files arranged as in the download instructions:

```bash
python scripts/prepare_inputs.py --task task_01 --source-dir downloads --output-dir ../agent_workspace_01
python scripts/prepare_inputs.py --task task_02 --source-dir downloads --output-dir ../agent_workspace_02
```

Each destination must be new or empty and outside the repository. The tool verifies source SHA-256 values, assembly evidence, all sample IDs, affected status, record count and causal-site genotypes. Preparation logs go to stdout for the evaluator; do not redirect them into an Agent workspace.

The resulting workspace has four files: `prompt.md`, `input/variants.vcf`, `input/family.ped`, `input/case.json`. The task READMEs distinguish research documentation from the safe case-information excerpt; the preparation script inserts that same case information into the common template.

**Input profile `gt_only_v1`:** all original variant records, their order, CHROM/POS/REF/ALT, sample identifiers/order and GT strings are preserved. For every record uniformly, ID/QUAL/FILTER/INFO become `.`, FORMAT becomes `GT`, and other per-sample fields are omitted. Input metadata is rebuilt with the assembly and original contig/ALT definitions. Unknown parent `NA` in the original TFAM is represented as `0` in the derived PED. Missing genotype `.` remains missing.

This preparation is necessary because the original Pfeiffer target is explicitly marked `SPIKED` and `DiseaseGene`; the rest of that file also carries precomputed effect annotations that the target lacks. Removing only the two tags would leave an obvious annotation-pattern shortcut. The uniform GT-only view removes these explicit labels and asymmetric annotations, without generating variants or altering genotypes. It does not provide read-level depth, quality or allele-balance evidence and is not a sequencing QC benchmark. Keep the untouched original files for audit, outside the Agent environment.

### 3. Run the Agent

Mount only the prepared workspace and general reference/software resources in a separate container/VM or restricted account. Give the Agent `prompt.md`. Do not mount the project, its parent directory, source archives, source YAMLs, publications, file links, author results, reference answers, tests, verification reports, evaluator tools or logs. Merely using a different directory on a filesystem the Agent can still read does **not** enforce isolation.

For formal isolated runs, stage general databases first and disable general web/source browsing. Tools, algorithms and analysis parameters remain unrestricted within the declared resources. If online database access is allowed, document the allowlist and avoid source tutorial/result pages. Do not compare different resource policies as if they were one controlled setting. Public teaching cases may already be memorized; isolation cannot remove that limitation.

Have the Agent save `result.json`. No analysis narrative is required or scored.

### 4. Validate and score

Copy the final result to the evaluator's results directory. The evaluator runs **outside** the Agent environment and reads the reference files there.

```bash
python scripts/validate_output.py results/task_01/result.json
python scripts/evaluate.py --task task_01 --result results/task_01/result.json
python scripts/evaluate.py --results-dir results --output scores.json
```

The final command requires both `results/task_01/result.json` and `results/task_02/result.json`. Missing or invalid files produce exit code 2 and a structured error on stderr, without numerical scores; no task is silently omitted from the denominator. Single-task scoring emits `overall: null`.

If **any submitted candidate is an indel**, pass the matching uncompressed indexed FASTA to both commands:

```bash
python scripts/validate_output.py results/task_01/result.json --fasta /resources/genome.fa
python scripts/evaluate.py --results-dir results --fasta /resources/genome.fa --output scores.json
```

The Python scorer checks REF against FASTA when supplied and left-aligns indels. It performs no network access, tool invocation, stochastic sampling or liftover. Use the same reference resource across a leaderboard. Do not supply a different assembly just to make a REF check pass.

## JSON output contract

```json
{
  "variants": [
    {"chrom": "7", "pos": 123456, "ref": "A", "alt": "G", "gene": "EXAMPLE"}
  ]
}
```

This is a schema illustration, not an answer. Return 0–10 candidates, ranked highest to lowest. Required fields are `chrom` (string), `pos` (positive integer), `ref` and `alt`; `gene` is optional. Positions are VCF 1-based. Each candidate contains one explicit A/C/G/T ALT allele. No extra keys, confidence scores, duplicate JSON keys, Markdown or prose are accepted. Structural/symbolic alleles, breakends and ambiguous bases are outside the output schema for these two small-variant cases.

Primary chromosome aliases such as `chr7`/`7`, `chrX`/`X` and `chrM`/`MT` are harmonized; other contig names are preserved exactly. Alleles are uppercased, shared padding is trimmed, and indels are left-aligned when the mandatory FASTA is supplied. Equivalent variants are rejected as duplicates, even if their gene fields differ; the evaluator never reorders or silently deduplicates a submission. MNVs are not atomized into separate SNVs: a larger haplotype is not automatically credited as the exact causal allele.

## Metrics

For each task there is exactly one author-defined causal variant. A match requires the entire normalized tuple **CHROM + POS + REF + ALT** in the task's assembly; gene names do not affect this match.

| Metric | Per-task definition |
|---|---|
| Top-1 Accuracy | 1 if the correct allele is first; otherwise 0 |
| Recall@5 | 1 if it occurs within ranks 1–5; otherwise 0 |
| MRR contribution | `1 / r` at rank `r` (1–10); 0 if absent |
| Gene-level Accuracy | Auxiliary **top-1** reported gene-symbol match, case-insensitive; 0 for empty results, `null` if the first candidate omits `gene` |

Gene-level Accuracy uses the Agent's reported symbol, not a new annotation pipeline; it does not prove that the reported gene is consistent with the coordinate. Thus a different variant reported in the correct gene can have gene accuracy 1 and variant accuracy 0. Missing optional gene fields never penalize variant metrics. Overall gene accuracy is `null` if either task's gene metric is unavailable.

`Overall MRR = (MRR_task_01 + MRR_task_02) / 2`.

Overall Top-1 Accuracy and Recall@5 are the same equal-weight arithmetic means. Reports include each task's rank and metrics and input/reference result hashes. There is no biological-plausibility or workflow-completion score. Invalid outputs must be resolved according to the stated format protocol before leaderboard ingestion, rather than silently scored on a surviving subset.

## Tests and limitations

Run `python scripts/test_benchmark.py`. The tests cover ranks 1/2/5/10, absent alleles, gene-only matches, empty output, aliases, malformed JSON, duplicate candidates and JSON keys, indel normalization and byte-identical repeated scoring. These are evaluator tests, not Agent performance measurements.

- Both examples contain known disease variants inserted by their authors into background data. They test variant localization and prioritization; they do **not** establish real-world clinical diagnostic ability.
- There are only two cases and one reference allele per case: no statistical generalization, compound-heterozygous pair scoring, multiple diagnoses or structural-variant benchmark is claimed.
- GT-only preparation deliberately removes read-quality evidence. Artificial genotype patterns and public sample IDs can still permit shortcuts or source recognition. Public knowledge/memorization cannot be excluded.
- Task 01 has missing calls in six unaffected relatives at the target site. Unaffected status is not a guarantee of a known reference genotype.
- The complete Agent analysis environment, database releases and resource limits need to be frozen by the evaluator. Full SnpEff/Exomiser analyses and live Agent sandbox enforcement were not tested in this build.
- Reference JSONs are public for reproducibility and auditing; access separation must be enforced by the external runner.

## Sources

1. [SnpEff official examples, Example 1: Coding variants](https://pcingola.github.io/SnpEff/examples/) and [author-hosted protocols.zip](https://sourceforge.net/projects/snpeff/files/protocols.zip/download).
2. Smedley D, Jacobsen JOB, Jager M, et al. **Next-generation diagnostics and disease-gene discovery with the Exomiser.** Nature Protocols 10, 2004–2015 (2015). [DOI](https://doi.org/10.1038/nprot.2015.124), [full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC5467691/), especially Box 1B, Box 2 and Anticipated Results.
3. [Exomiser input documentation](https://exomiser.readthedocs.io/en/latest/input_files_and_options.html), [author result interpretation](https://exomiser.readthedocs.io/en/latest/result_interpretation.html) and the pinned official source files in [task_02/filelink.md](task_02/filelink.md).

Original data/software remain subject to their authors' applicable terms. This project supplies links and small audit metadata rather than redistributing complete source archives.
