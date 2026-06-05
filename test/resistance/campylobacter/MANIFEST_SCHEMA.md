# Manifest Schema Reference

Each test case directory contains a `manifest.json` with the following structure.

## Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `organism` | string | Full organism name (e.g., "Campylobacter jejuni") |
| `strain` | string | Strain or isolate identifier |
| `curation` | object | Curation metadata and evidence |
| `ground_truth` | object | Expected tool results |
| `data_sources` | object | How to obtain sequence data |
| `tools` | object | Tool configurations and run commands |
| `validation_instructions` | object | Per-tool validation guidance |
| `difficulty` | string | `common`, `edge_case`, `rare` |
| `case_category` | string | `susceptible_control`, `single_resistance`, `multi_resistance`, `mdr`, `edge_case` |
| `notes` | string | Free-text notes |

## curation

```json
{
  "date": "2026-06-05",
  "ncbi_accessions": {
    "biosample": "SAMN...",
    "sra": "SRR...",
    "assembly": "GCA_..."
  },
  "metadata_confidence": "high | medium | low | bootstrapped",
  "amr_evidence": [
    {
      "source": "ResFinder_v4.6.0 | NARMS | Literature | BioSample_antibiogram",
      "genes": ["blaOXA-61", "tet(O)"],
      "phenotypes_resistant": ["ampicillin", "tetracycline"],
      "note": "optional"
    }
  ],
  "phenotypic_mic_data": null,
  "quality_metrics": {
    "has_reads": false,
    "has_assembly": true,
    "submitter": "NCTC | FDA-CFSAN | UCLA",
    "notes": ""
  }
}
```

**metadata_confidence values:**
- `high` — MIC-based phenotypic data or multiple concordant sources
- `medium` — Single tool output or unverified metadata
- `low` — Inferred or conflicting evidence
- `bootstrapped` — Ground truth derived from tool output (no independent phenotypic data)

## ground_truth.amr

```json
{
  "phenotype_summary": "AMP_TET",
  "resistant_phenotypes": {
    "<drug_name>": {
      "amr_resistant": true,
      "genes": ["blaOXA-61"],
      "amr_class": "beta-lactam",
      "identity": 99.87,
      "coverage": 100.0,
      "note": "optional"
    }
  },
  "susceptible_phenotypes": ["ciprofloxacin", "erythromycin"],
  "detected_genes": ["blaOXA-61", "tet(O)"],
  "amr_database_evidence": {
    "source": "ResFinder v4.6.0 (ResFinder-2.4.0 DB)",
    "note": ""
  }
}
```

## data_sources

```json
{
  "reads": {
    "sra_accession": "SRR...",
    "download_cmd": "fasterq-dump --gzip --outdir data/ SRR... && mv ..."
  },
  "assembly": {
    "accession": "GCA_...",
    "download_cmd": "datasets download genome accession GCA_... --include genome ...",
    "note": "pre-loaded in data/contigs.fa"
  }
}
```

## tools

```json
{
  "ResFinder": {
    "input_type": "assembly | reads | both",
    "version_min": "4.6.0",
    "run_cmd": "python -m resfinder -ifa data/contigs.fa ...",
    "reference_output": "expected/resfinder/resfinder.json"
  }
}
```

## validation_instructions

Keyed by lowercase tool name (snake_case). Each value is a string describing PASS/PARTIAL/FAIL criteria for that tool on this specific case.

```json
{
  "resfinder": "Expect blaOXA-61 and tet(O). PASS if both detected. PARTIAL if only one.",
  "amrfinderplus": "Expect beta-lactam and tetracycline drug classes. PASS if both rows present.",
  "card_rgi": "Expect Strict hits for OXA and tet. PASS if identity >= 95%.",
  "abricate": "Expect hits in resfinder and card DBs. PASS if both drug classes hit."
}
```
