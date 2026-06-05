# AMRFinderPlus — AMR Test Case Configuration

## Overview

AMRFinderPlus (NCBI) detects acquired resistance genes, resistance-associated point mutations, and virulence factors. It is organism-aware and uses the NCBI Reference Gene Catalog.

- **Input:** Nucleotide FASTA, protein FASTA, or GFF3 + FASTA
- **Output:** TSV with gene name, element type, drug class, %identity, %coverage
- **Detection scope:** Acquired genes + point mutations (--plus flag)
- **Organism-aware:** --organism flag enables species-specific mutation calling
- **Current version:** 3.12.0+

## Tool Configuration Template

```json
"AMRFinderPlus": {
  "input_type": "assembly",
  "version_min": "3.12.0",
  "run_cmd": "mkdir -p actual/amrfinderplus && amrfinder --nucleotide data/contigs.fa --organism Campylobacter --output actual/amrfinderplus/amrfinder.tsv --plus",
  "reference_output": "expected/amrfinderplus/amrfinder.tsv"
}
```

## Validation Logic

| Result | Criteria |
|--------|----------|
| PASS | TSV contains rows for all expected drug classes; gene names may differ from ResFinder |
| PARTIAL | Some drug classes detected but not others |
| FAIL | No hits in positive case; or any hit in susceptible control |

## Known Differences from ResFinder

- Gene names follow NCBI nomenclature (may differ from ResFinder/CARD)
- OXA family: AMRFinderPlus may report fewer OXA paralogs if they share high identity
- PointFinder equivalent: enabled via `--plus` flag with `--organism` specified
- Output includes "Element type" (AMR, VIRULENCE, STRESS) and "Method" (EXACTX, BLASTX, HMM)
