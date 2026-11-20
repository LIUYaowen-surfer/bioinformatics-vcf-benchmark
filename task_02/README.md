# task_02 — Exomiser Pfeiffer syndrome quartet

## Research documentation (evaluator only)

Smedley et al., [Next-generation diagnostics and disease-gene discovery with the Exomiser](https://doi.org/10.1038/nprot.2015.124), Nature Protocols 10, 2004–2015 (2015). [Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC5467691/): Box 1B demonstrates family analysis; Box 2 gives the quartet PED; Anticipated Results explicitly specifies the causative allele. The [current official input documentation](https://exomiser.readthedocs.io/en/latest/input_files_and_options.html) also supports this multisample example.

Use **Pfeiffer-quartet.vcf.gz**, not the singleton `Pfeiffer.vcf`, with its corresponding PED. The pinned official quartet file contains **300,036 records and four samples**; do not apply the approximately 37,709-record singleton count from the paper to this file. Its contigs declare `assembly=b37` and its reference path ends in `human_g1k_v37.fasta`. The author's family-analysis YAML specifies `genomeAssembly: hg19`, which is consistent at the autosomal target locus. No coordinate conversion is performed.

| Family | Sample | Father | Mother | Sex | Status |
|---|---|---|---|---|---|
| FAM1 | ISDBM322016 | 0 | 0 | Male | Unaffected father |
| FAM1 | ISDBM322018 | 0 | 0 | Female | Unaffected mother |
| FAM1 | ISDBM322015 | ISDBM322016 | ISDBM322018 | Male | Unaffected brother |
| FAM1 | ISDBM322017 | ISDBM322016 | ISDBM322018 | Female | Affected daughter / proband |

| HPO ID | Phenotype from the family example |
|---|---|
| HP:0001156 | Brachydactyly |
| HP:0001363 | Craniosynostosis |
| HP:0011304 | Broad thumb |
| HP:0010055 | Broad hallux |

These four identifiers appear in paper Box 1B and `test-analysis-multisample.yml`. The example's working inheritance model is autosomal dominant, allowing a de novo allele. Do not replace this profile with the separate singleton phenopacket. The analysis goal is to rank specific alleles using genotype segregation and phenotype relevance; Exomiser, VEP, ANNOVAR, bcftools, Python/R and other reasonable tools are optional routes.

[Download links and hashes](filelink.md) pin the author VCF, PED and phenotype source to a commit. [reference.json](reference.json) records the allele explicitly stated in the paper and reproduced in the official example. The actual quartet contains it as a heterozygous call in the affected daughter and as reference homozygous calls in the other three samples. No prediction software was run to invent the truth label.

The original record is explicitly marked `SPIKED` and `DiseaseGene`; it also has artificial quality fields that should not be treated as independent experimental evidence. Formal inputs use the uniform GT-only preparation described in the [project README](../README.md). This author-constructed teaching case is not an independently diagnosed clinical quartet.

## Agent task information (safe excerpt)

The JSON below supplies the case variables in the single [common prompt](../agent_prompt.md). During preparation the script adds `input/variants.vcf`, `input/family.ped` and the assembly. Provide the generated `prompt.md` and input files, not this entire research page or any linked source.

<!-- BEGIN AGENT CASE -->
```json
{
  "proband": "ISDBM322017",
  "affected_samples": [
    "ISDBM322017"
  ],
  "unaffected_samples": [
    "ISDBM322016",
    "ISDBM322018",
    "ISDBM322015"
  ],
  "inheritance": "Autosomal dominant (author-specified working model); allow a de novo allele.",
  "phenotypes": [
    {
      "id": "HP:0001156",
      "label": "Brachydactyly"
    },
    {
      "id": "HP:0001363",
      "label": "Craniosynostosis"
    },
    {
      "id": "HP:0011304",
      "label": "Broad thumb"
    },
    {
      "id": "HP:0010055",
      "label": "Broad hallux"
    }
  ],
  "clinical_context": "Affected daughter, unaffected father, mother and brother. Phenotype terms are from the authors' family-analysis example, not the separate singleton phenopacket."
}
```
<!-- END AGENT CASE -->

Return up to ten distinct normalized variants in `result.json`, using the shared schema. Only the complete allele identity and ranking are scored; no explanatory prose is required.
