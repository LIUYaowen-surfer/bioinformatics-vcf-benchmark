You are given genomic variant data in VCF format, together with relevant family and/or phenotype information.

Your task is to identify and rank the variants most likely to explain the affected individual's or family's condition.

You may use any appropriate bioinformatics tools, databases, algorithms, or analysis strategies available in your environment. No particular pipeline is required.

Return up to 10 candidate variants, ranked from most to least likely to be causal.

Save the final result as `result.json` using this JSON structure:

```json
{"variants": [{"chrom": "1", "pos": 123456, "ref": "A", "alt": "G", "gene": "EXAMPLE"}]}
```

The example illustrates the schema only. Each candidate must contain `chrom` (string), `pos` (positive integer, VCF 1-based coordinate), `ref` and `alt` (single explicit DNA alleles). `gene` is an optional single gene symbol. Do not add other keys or confidence values. Use the supplied genome assembly; do not lift over coordinates. Split multi-allelic sites into separate candidates. Normalize alleles, including left alignment of indels against the matching reference genome. Do not repeat equivalent variants. An empty `variants` array is allowed. Symbolic alleles and breakends are outside this benchmark's output schema.

Do not include explanatory prose or Markdown fences in the final JSON output.

Case information (the pedigree contains all sample IDs, parents, sex, and affected status; PED codes 1 = unaffected, 2 = affected, 0 = unknown parent):

```json
{{CASE_INFORMATION}}
```
