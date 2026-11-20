# task_02 — original author files

Preparation/audit only. Use the official **quartet**, not `Pfeiffer.vcf` or a small unit-test fixture.

Downloads are pinned to Exomiser commit `98f4e0b6f2f3f5bf790a9f955808c98968559996` and were successfully fetched on 2026-11-17. The data VCF/PED live under `exomiser-cli/src/main/resources/vcf/`; the phenotype/assembly example lives under `exomiser-cli/src/main/resources/examples/`. Both are distributed as examples by the author project.

| Original filename | Role | Bytes | Download |
|---|---|---:|---|
| `Pfeiffer-quartet.vcf.gz` | Required four-sample VCF | 22,846,251 | [Author VCF](https://raw.githubusercontent.com/exomiser/Exomiser/98f4e0b6f2f3f5bf790a9f955808c98968559996/exomiser-cli/src/main/resources/vcf/Pfeiffer-quartet.vcf.gz) |
| `Pfeiffer-quartet.ped` | Required family/affected status | 140 | [Author PED](https://raw.githubusercontent.com/exomiser/Exomiser/98f4e0b6f2f3f5bf790a9f955808c98968559996/exomiser-cli/src/main/resources/vcf/Pfeiffer-quartet.ped) |
| `test-analysis-multisample.yml` | Required provenance for assembly, proband and four HPO terms; preparation only | 4,963 | [Author case configuration](https://raw.githubusercontent.com/exomiser/Exomiser/98f4e0b6f2f3f5bf790a9f955808c98968559996/exomiser-cli/src/main/resources/examples/test-analysis-multisample.yml) |

```bash
mkdir -p downloads
base=https://raw.githubusercontent.com/exomiser/Exomiser/98f4e0b6f2f3f5bf790a9f955808c98968559996/exomiser-cli/src/main/resources
curl -fL --retry 3 "$base/vcf/Pfeiffer-quartet.vcf.gz" -o downloads/Pfeiffer-quartet.vcf.gz
curl -fL --retry 3 "$base/vcf/Pfeiffer-quartet.ped" -o downloads/Pfeiffer-quartet.ped
curl -fL --retry 3 "$base/examples/test-analysis-multisample.yml" -o downloads/test-analysis-multisample.yml
```

On Windows use `curl.exe` with the full table URLs. Keep files byte-for-byte; do not rewrite PED/YAML line endings before verification.

| File | Verified SHA-256 |
|---|---|
| `Pfeiffer-quartet.vcf.gz` | `db5fa80abb740672405bd57a5fc3daf1748f373e3f2589310fd3a5d9053b17b7` |
| `Pfeiffer-quartet.ped` | `4e357bcdab7e79dd9e643a2a0cba5b739030fa13d39b21340c0a54cd1ce0ae64` |
| `test-analysis-multisample.yml` | `2dbb35b7b9a736c2e3230950ce533cacf93278d6760437930e2dc8aa258dc234` |

`prepare_inputs.py` checks all three hashes and copies only case facts into the common prompt. It does not expose the author's pipeline YAML. The four HPO terms come from the paper's Box 1B and this multisample configuration; do not substitute a singleton phenopacket that may describe a different six-term profile.

The VCF has embedded answer markers. Never give this unmodified source to the Agent in a formal run; use the documented `gt_only_v1` preparation. A source `.tbi` index is unnecessary for preparation. If the Agent needs indexed input, it can bgzip/tabix the prepared VCF; an index for the original file cannot be reused.

Sources: [2015 paper](https://doi.org/10.1038/nprot.2015.124), [official input instructions](https://exomiser.readthedocs.io/en/latest/input_files_and_options.html).
