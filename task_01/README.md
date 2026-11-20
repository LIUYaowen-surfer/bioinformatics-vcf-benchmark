# task_01 — SnpEff cystic fibrosis family

## Research documentation (evaluator only)

Source: [SnpEff official tutorial, Example 1: Coding variants](https://pcingola.github.io/SnpEff/examples/). The author inserted a known recessive disease allele into a real CEPH_1463 background. The family comprises four grandparents, two parents and eleven siblings. This benchmark uses the author's original files, without regenerating or randomly simulating a case.

The original `protocols/ex1.vcf` has 17 samples and **743,154 records: 499,080 on chromosome 7 and 244,074 on chromosome 17**. Its reference header is `##source_GENOME_REFERENCE=NCBI build 37`, consistent with the tutorial's GRCh37.75 annotation database. Use GRCh37 coordinates. The generic tutorial description of approximately 500,000 variants is not the count of this whole file.

The six-column `protocols/pedigree.tfam` supplies family ID, sample ID, father, mother, sex and phenotype. The source represents absent parents as `NA`; the prepared PED uses standard `0`. Phenotype 1 means unaffected, 2 affected. All eleven siblings have father NA12877 and mother NA12878. NA12877's parents are NA12889/NA12890; NA12878's parents are NA12891/NA12892.

| Role | Sample IDs | Status |
|---|---|---|
| Grandparents | NA12889, NA12890, NA12891, NA12892 | Unaffected |
| Parents | NA12877, NA12878 | Unaffected |
| Affected siblings | NA12879, NA12885, NA12886 | Affected |
| Other siblings | NA12880, NA12881, NA12882, NA12883, NA12884, NA12887, NA12888, NA12893 | Unaffected |

The analysis goal is to rank the specific allele explaining the affected siblings under the author's autosomal-recessive model. No detailed HPO observations are provided by this example; none are invented. The benchmark does not require the use of SnpEff.

[Download links and hashes](filelink.md) identify the source inputs and author final filtered file. [reference.json](reference.json) records the explicit author answer, original-source evidence, assembly and all target-site genotypes. The three affected siblings are homozygous alternate and both parents are heterozygous. Six unaffected relatives have missing calls at that locus; these must not be treated as reference homozygotes. The author's filtered result contains two candidates, but the official explanation identifies one as the known disease allele; only that allele is the single reference answer.

## Agent task information (safe excerpt)

The JSON below supplies the case variables in the single [common prompt](../agent_prompt.md). During preparation the script adds `input/variants.vcf`, `input/family.ped` and the assembly. Provide the generated `prompt.md` and input files, not this entire research page or any linked source.

<!-- BEGIN AGENT CASE -->
```json
{
  "affected_samples": [
    "NA12879",
    "NA12885",
    "NA12886"
  ],
  "unaffected_samples": [
    "NA12877",
    "NA12878",
    "NA12880",
    "NA12881",
    "NA12882",
    "NA12883",
    "NA12884",
    "NA12887",
    "NA12888",
    "NA12889",
    "NA12890",
    "NA12891",
    "NA12892",
    "NA12893"
  ],
  "inheritance": "Autosomal recessive (author-specified working model).",
  "phenotypes": [],
  "clinical_context": "Three affected siblings in a 17-member family; other members are unaffected. No additional structured clinical observations are supplied. Treat missing genotypes as unknown, not homozygous reference."
}
```
<!-- END AGENT CASE -->

Return up to ten distinct normalized variants in `result.json`, using the shared schema. Only the complete allele identity and ranking are scored; no explanatory prose is required.
