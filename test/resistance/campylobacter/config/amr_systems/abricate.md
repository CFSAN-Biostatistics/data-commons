# abricate — AMR Test Case Configuration

## Overview

abricate screens contigs against multiple AMR databases (ResFinder, CARD, ARG-ANNOT, NCBI, MEGARES, PlasmidFinder, VFDB). Lightweight BLAST-based screen; no point mutation detection.

- **Input:** Nucleotide FASTA
- **Output:** TSV per database run
- **Detection scope:** Acquired genes only (no point mutations)
- **Current version:** 1.0.0+

## Tool Configuration Template

```json
"abricate": {
  "input_type": "assembly",
  "version_min": "1.0.0",
  "run_cmd": "mkdir -p actual/abricate && abricate --db resfinder data/contigs.fa > actual/abricate/abricate_resfinder.tsv && abricate --db card data/contigs.fa > actual/abricate/abricate_card.tsv",
  "reference_output": "expected/abricate/abricate_resfinder.tsv"
}
```

## Validation Logic

| Result | Criteria |
|--------|----------|
| PASS | Hits for all expected genes at ≥80% identity and ≥80% coverage |
| PARTIAL | Some expected genes hit but below thresholds, or card DB catches what resfinder misses |
| FAIL | No hits in positive case; or hits in susceptible control above threshold |

## Known Behaviors

- Runs databases sequentially — validate resfinder and card outputs separately
- Default thresholds: `--minid 80 --mincov 80`
- No species-aware filtering — all hits reported regardless of clinical relevance
- Header-only output = no hits (verify with `wc -l`)
