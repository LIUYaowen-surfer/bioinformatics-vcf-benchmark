Identify and rank the variants most likely to cause the affected individual's or family's condition using the provided files:

- `input/variants.vcf`: Genomic variants
- `input/family.ped`: Family relationships and affected status
- `input/case.json`: Case information, phenotypes, and genome assembly

You may use any available tools, databases, or analysis methods.

Save up to 10 candidate variants, ranked from most to least likely, in `result.json`:

```json
{
  "variants": [
    {
      "chrom": "1",
      "pos": 123456,
      "ref": "A",
      "alt": "G",
      "gene": "EXAMPLE"
    }
  ]
}
```

Output requirements:

- `chrom`, `pos`, `ref`, and `alt` are required; `gene` is optional.
- Use 1-based VCF coordinates and the original genome assembly.
- Report explicit DNA alleles, normalize variants, and avoid duplicates.
- Return at most 10 candidates. An empty list is allowed.
- Do not include additional fields or explanatory text in the JSON file.
