# Challenge Manifest Schema

Each challenge directory contains a `manifest.json` defining the pathological condition, data sources, and sample roles. This schema is independent from `test/typing/` manifests.

## Complete Example

```json
{
  "name": "ecoli_to_seqsero2",
  "phenomenon": "wrong_organism",
  "challenge_tags": ["wrong_organism", "in_silico_typing", "confident_wrong_call"],
  "mechanism": "An E. coli assembly is submitted to SeqSero2, which expects Salmonella input. SeqSero2 has no organism guard — it searches for Salmonella antigen genes against any assembly. Conserved housekeeping k-mers shared between E. coli and Salmonella produce partial matches, and the tool returns a confident (wrong) serotype call rather than rejecting the input.",
  "tool_categories": ["in_silico_typing"],
  "tool_families": ["seqsero2", "sistr"],
  "known_behaviors": [
    {
      "tool": "SeqSero2",
      "version_tested": "1.3.1",
      "behavior": "Returns a Salmonella serotype call with no warning or rejection. The predicted serotype varies by E. coli strain but is consistently wrong. Exit code 0."
    }
  ],
  "samples": [
    {
      "id": "ecoli_k12",
      "role": "subject",
      "description": "E. coli K-12 MG1655 reference assembly",
      "source_type": "ncbi_assembly",
      "accession": "GCF_000005845.2",
      "files": {
        "assembly": "assembly.fasta"
      },
      "download": {
        "command": "datasets download genome accession GCF_000005845.2 --include genome",
        "tool": "ncbi-datasets-cli"
      }
    }
  ],
  "curation": {
    "curator": "Justin Payne",
    "date": "2026-06-02",
    "confidence": "high",
    "notes": "E. coli K-12 MG1655 is the canonical E. coli reference; its behavior with SeqSero2 is representative of the general wrong-organism case."
  }
}
```

---

## Field Reference

### Top-Level Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Slug matching the directory name |
| `phenomenon` | string | yes | Parent phenomenon category (matches directory name) |
| `challenge_tags` | string[] | yes | Queryable tags describing the challenge. Include the phenomenon, affected tool categories, and failure behavior type |
| `mechanism` | string | yes | Prose explanation of *why* this dataset is adversarial: what assumption it violates, how the tool is likely to fail, and what makes the failure hard to diagnose |
| `tool_categories` | string[] | yes | Broad tool categories challenged. Values: `alignment`, `assembly`, `gene_prediction`, `in_silico_typing`, `population_variant_analysis`, `amr_detection`, `qc` |
| `tool_families` | string[] | yes | Specific tool families for which layout templates exist. See `README.md` for valid values |
| `known_behaviors` | object[] | no | Optional: documented tool-specific responses. Version-dependent; may go stale. See schema below |
| `samples` | object[] | yes | One entry per sample. See schema below |
| `curation` | object | yes | Provenance metadata. See schema below |

---

### `known_behaviors[]`

Documents observed behavior of specific tools against this challenge. Optional — omit if unknown or untested.

| Field | Type | Required | Description |
|---|---|---|---|
| `tool` | string | yes | Tool name (e.g., "SeqSero2", "snippy-core") |
| `version_tested` | string | no | Tool version this behavior was observed on |
| `behavior` | string | yes | What the tool does: crash, wrong output, silent empty output, etc. Include exit code if known |

---

### `samples[]`

One entry per sample in the challenge. Single-sample challenges have one entry; multi-sample challenges (e.g., SNP cohorts) have multiple.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Short identifier, unique within this manifest. Used as the `data/` subdirectory name |
| `role` | string | yes | Sample's function in the challenge. See **Role Vocabulary** below |
| `description` | string | yes | Human-readable description of what this sample is |
| `source_type` | string | yes | `ncbi_assembly`, `sra`, `url`, or `recipe` |
| `accession` | string | conditional | NCBI accession (required for `ncbi_assembly` and `sra` source types) |
| `url` | string | conditional | Direct download URL (required for `url` source type) |
| `files` | object | yes | Maps file roles to filenames within `data/{id}/`. See **File Role Keys** below |
| `download` | object | yes | Download instructions. See schema below |
| `recipe` | object | conditional | Required when `source_type` is `recipe`. See schema below |

#### Role Vocabulary

| Role | Usage |
|---|---|
| `subject` | The sample being analyzed (single-sample challenges) |
| `reference` | Reference genome for alignment or SNP calling |
| `ingroup` | Closely related sample in a population (SNP cohort challenges) |
| `outlier` | The adversarial sample — the one that breaks tool assumptions |
| `contaminant` | The contaminating organism in a mixed-sample challenge |

#### File Role Keys

| Key | Description |
|---|---|
| `assembly` | FASTA assembly file |
| `reads_1` | Forward reads (R1) FASTQ |
| `reads_2` | Reverse reads (R2) FASTQ |
| `reads_unpaired` | Single-end reads FASTQ |
| `reads_long` | Long reads (ONT or PacBio) FASTQ |

---

### `samples[].download`

| Field | Type | Required | Description |
|---|---|---|---|
| `command` | string | yes | Shell command to download the data. Should write into the current directory (the `acquire.py` script sets cwd to `data/{sample_id}/` before running) |
| `tool` | string | yes | Tool required: `ncbi-datasets-cli`, `sra-tools`, `wget`, `curl` |

---

### `samples[].recipe`

Used when `source_type` is `recipe` — no public dataset captures the exact pathological condition, so it must be constructed.

| Field | Type | Required | Description |
|---|---|---|---|
| `description` | string | yes | Human-readable description of what the recipe produces |
| `inputs` | string[] | yes | Sample IDs (from this manifest) that must be downloaded before the recipe runs |
| `tools_required` | string[] | yes | Tools needed to execute the recipe |
| `command` | string | yes | Shell command(s) to construct the synthetic dataset |

---

### `curation`

| Field | Type | Required | Description |
|---|---|---|---|
| `curator` | string | yes | Name of person who curated this challenge |
| `date` | string | yes | ISO 8601 date of curation (YYYY-MM-DD) |
| `confidence` | string | yes | `high`, `medium`, or `low` — confidence that this dataset genuinely exhibits the claimed challenge |
| `notes` | string | no | Free-text curation notes, known limitations, or suggested improvements |

---

## Challenge Tag Vocabulary

Use these tags consistently to enable filtering. Combine freely.

**Phenomenon tags:** `wrong_organism`, `contamination`, `sample_swap`, `degenerate_input`, `low_coverage`, `extreme_gc`, `repetitive_genome`, `mixed_population`, `wrong_reference`, `fragmented_assembly`, `platform_mismatch`, `file_format_edge_case`

**Tool category tags:** `alignment`, `assembly`, `gene_prediction`, `in_silico_typing`, `population_variant_analysis`, `amr_detection`, `qc`

**Failure behavior tags:** `confident_wrong_call`, `silent_wrong_output`, `silent_empty_output`, `crash`, `core_genome_collapse`, `inflated_snp_count`, `false_negative`, `false_positive`
