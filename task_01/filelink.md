# task_01 — original author files

Preparation/audit only. Do not expose this page, archives or author results to the Agent.

## Download

The [official SnpEff tutorial](https://pcingola.github.io/SnpEff/examples/) links `protocols.zip`. The current tutorial S3 path, `https://datasetsnpeff-public.s3.amazonaws.com/dataset/protocols.zip`, returned HTTP 404 (NoSuchKey), including with the tutorial's query string, on 2026-11-17.

Use the **same named archive in the author's SourceForge project**, maintained by `pcingola`: [download page](https://sourceforge.net/projects/snpeff/files/protocols.zip/download), [direct download](https://downloads.sourceforge.net/project/snpeff/protocols.zip). The archive is 480,782,027 bytes; SourceForge's published SHA-256 is `4842273552fbfa6cb7e99acef26b7a025fc7efc3def1e6ac3e7bc9cf2c2d15ce`. This build retrieved the required complete members using HTTP byte ranges and verified ZIP member CRC32 plus local SHA-256, rather than downloading all conservation tracks in the archive. The whole-archive SHA-256 above is publisher-reported, not independently recomputed here.

```bash
mkdir -p downloads
curl -fL --retry 3 https://downloads.sourceforge.net/project/snpeff/protocols.zip -o downloads/protocols.zip
unzip downloads/protocols.zip protocols/ex1.vcf protocols/pedigree.tfam protocols/ex1.filtered.vcf -d downloads
```

On Windows, `curl.exe` and `Expand-Archive` may be used; keep the same resulting paths. Run `prepare_inputs.py` from the repository root with `--source-dir downloads` to verify the required input hashes automatically.

| File inside archive | Role | Bytes | Verified member SHA-256 |
|---|---|---:|---|
| `protocols/ex1.vcf` | Required original multisample VCF | 64,431,656 | `ed1d589c61a10744dfbc39f16cee11553bcf617888782720fb829fc680a6125d` |
| `protocols/pedigree.tfam` | Required family and affected status | 606 | `36f781af9ac2f0107c16fe4cffeddfe2223164a9a86a42e986fd673b6e96cabb` |
| `protocols/ex1.filtered.vcf` | Author's final filtered results; audit only | 10,172 | `f25a4c8097f2deed94874cd51bb0222ebe4254821f13f13678c8e988452726c5` |

No other archive member is required as benchmark input. `annotate_example_1.sh`, annotated VCFs, charts and ClinVar-filtered outputs reveal answers and must remain evaluator-only. General annotation/reference resources can be staged independently; the Agent need not reproduce the author's pipeline.

Do not substitute `protocols_sample.zip`, recreate the case, randomly introduce mutations, or silently accept changed file hashes. Investigate any hash mismatch before a formal run. The verified input is the full original `ex1.vcf`, including both chromosomes 7 and 17.
