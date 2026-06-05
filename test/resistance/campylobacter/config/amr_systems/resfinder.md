# ResFinder — AMR Test Case Configuration

## Overview

ResFinder detects acquired antimicrobial resistance genes by alignment against the ResFinder database (curated by CGE, DTU). It also supports PointFinder for chromosomal point mutations and DisinFinder for disinfectant resistance.

- **Input:** FASTA assembly or FASTQ reads (via KMA)
- **Output:** JSON (`resfinder.json`) + tabular reports
- **Detection scope:** Acquired resistance genes + point mutations (PointFinder)
- **Species-aware:** Narrows relevant phenotypes to organism-specific antimicrobials
- **Current version:** 4.6.0+

## Selection Strategy

Target 15-20 Campylobacter jejuni cases covering:
- Susceptible controls (3): True negatives; verify no false positives
- Single resistance — beta-lactam (2): blaOXA variants only
- Single resistance — tetracycline (2): tet(O) only
- Multi-drug — AMP+TET (3): Core clinically relevant profile
- Fluoroquinolone resistance (3): gyrA point mutations (requires PointFinder)
- MDR (2): 3+ drug classes
- Edge cases (3): truncated gene, novel variant below threshold, borderline identity

## Target List

### Susceptible Controls (3 cases)

- **NCTC11351** (priority: critical) — Type strain, confirmed susceptible. Any resistance call = false positive.
- **additional_sus_1** (priority: high) — Independent susceptible isolate from low-AMR environment
- **additional_sus_2** (priority: medium) — Susceptible isolate from a different source (poultry vs clinical)

### Beta-Lactam Only (2 cases)

- **blaOXA_single** (priority: high) — Single OXA gene; tests sensitivity at minimum resistance
- **blaOXA_multiple** (priority: high) — Multiple OXA paralogs (like UCLA_1626); tests whether all variants reported

### Tetracycline Only (2 cases)

- **tet_O_only** (priority: high) — tet(O) classic; most common tetracycline resistance in Campylobacter
- **tet_W_alt** (priority: medium) — tet(W) if available; tests alternate tet gene detection

### Multi-Drug AMP+TET (3 cases)

- **UCLA_1626** (priority: critical) — blaOXA+tet(O); existing case, serves as positive control
- **amp_tet_alt_SRR** (priority: high) — Independent AMP+TET isolate from different source
- **amp_tet_clinical_SRR** (priority: high) — Clinical outbreak isolate with documented phenotype

### Fluoroquinolone Resistance — PointFinder (3 cases)

- **gyrA_C257T** (priority: critical) — T86I substitution (C257T nucleotide); most common FQ resistance
- **gyrA_C257T_plus_amp** (priority: high) — FQ + beta-lactam combination
- **gyrA_parC_double** (priority: medium) — Double mutation; higher-level FQ resistance

### Edge Cases (3 cases)

- **truncated_blaOXA** (priority: high) — OXA gene split at contig boundary; tests boundary detection
- **novel_OXA_variant** (priority: medium) — OXA variant at ~85% identity; tests threshold behavior
- **borderline_tet_coverage** (priority: medium) — tet(O) with ~65% coverage; tests coverage threshold

## Discovery Parameters

NCBI BioSample search:
```
"Campylobacter jejuni"[Organism] AND ("antibiogram"[Attribute] OR "resistance_phenotype"[Attribute])
```

SRA filter: must have reads (for future reads-based testing)
Assembly filter: RefSeq or INSDC complete/scaffold

Metadata fields:
- `antibiogram`: MIC-formatted table (preferred)
- `resistance_phenotype`: text description
- `isolation_source`: clinical > food > environmental for priority

## Ground Truth Schema

```json
"ground_truth": {
  "amr": {
    "phenotype_summary": "AMP_TET",
    "resistant_phenotypes": {
      "ampicillin": {
        "amr_resistant": true,
        "genes": ["blaOXA-61"],
        "amr_class": "beta-lactam",
        "identity": 99.87,
        "coverage": 100.0
      }
    },
    "susceptible_phenotypes": ["ciprofloxacin", "erythromycin"],
    "detected_genes": ["blaOXA-61", "tet(O)"],
    "amr_database_evidence": {
      "source": "ResFinder v4.6.0 (ResFinder-2.4.0 DB)"
    }
  }
}
```

## Validation Logic

| Result | Criteria |
|--------|----------|
| PASS | All expected genes detected; all expected phenotypes flagged resistant; no unexpected resistance in susceptible controls |
| PARTIAL | Correct drug classes detected but not all individual gene variants; or expected genes detected but phenotype missing |
| FAIL | Any expected drug class missed entirely; or any resistance call in susceptible control |

## Tool Configuration Template

```json
"ResFinder": {
  "input_type": "assembly",
  "version_min": "4.6.0",
  "run_cmd": "python -m resfinder -ifa data/contigs.fa -o actual/resfinder -j actual/resfinder/resfinder.json -s 'Campylobacter jejuni' -acq",
  "reference_output": "expected/resfinder/resfinder.json"
}
```

For PointFinder (fluoroquinolone cases), add `-c` flag:
```json
"run_cmd": "python -m resfinder -ifa data/contigs.fa -o actual/resfinder -j actual/resfinder/resfinder.json -s 'Campylobacter jejuni' -acq -c"
```

## Known Tool Behaviors

- OXA variants: ResFinder reports all detected OXA paralogs separately; some tools collapse to the "best" match
- Database versioning: ResFinder-2.x vs 3.x vs 4.x databases have different gene coverage; record DB version in ground truth
- Species flag: `-s 'Campylobacter jejuni'` is required for species-relevant phenotype filtering
- Coverage threshold: default 60%; genes at 60-80% coverage are in a gray zone — document explicitly in edge cases
