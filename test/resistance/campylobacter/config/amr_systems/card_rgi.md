# CARD RGI — AMR Test Case Configuration

## Overview

CARD RGI (Resistance Gene Identifier) detects resistance genes using the CARD (Comprehensive Antibiotic Resistance Database) ontology. Uses protein homolog models, protein variant models, and rRNA mutation models.

- **Input:** Nucleotide or protein FASTA
- **Output:** JSON + TSV
- **Detection scope:** Acquired genes + chromosomal mutations
- **Model types:** Perfect, Strict, Loose (use Strict+ for validation)
- **Current version:** 6.0.0+

## Tool Configuration Template

```json
"CARD_RGI": {
  "input_type": "assembly",
  "version_min": "6.0.0",
  "run_cmd": "mkdir -p actual/card_rgi && rgi main --input_sequence data/contigs.fa --output_file actual/card_rgi/rgi --input_type contig --clean",
  "reference_output": "expected/card_rgi/rgi.json"
}
```

## Validation Logic

| Result | Criteria |
|--------|----------|
| PASS | Perfect or Strict hits for all expected drug classes at ≥95% identity |
| PARTIAL | Expected drug classes present but only at Loose threshold, or incomplete gene set |
| FAIL | No hits in positive case; or Strict hits in susceptible control |

## Known Differences

- CARD ARO terms differ from ResFinder/AMRFinderPlus gene names — use drug class for cross-tool comparison
- OXA family: CARD uses ARO accessions; multiple OXA paralogs may resolve to same ARO term
- `--clean` removes intermediate files; omit if debugging
