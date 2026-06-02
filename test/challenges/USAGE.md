# Challenges Library — Usage Reference

A quick-reference for working with the `test/challenges/` adversarial stimulus library. For design rationale and manifest schema, see [`README.md`](README.md) and [`MANIFEST_SCHEMA.md`](MANIFEST_SCHEMA.md). For the catalog of failure modes the challenges target, see [`FAILURE_MODES.md`](FAILURE_MODES.md).

---

## Quick Start

```bash
# Download data for one challenge
python3 acquire.py --challenge wrong_organism/ecoli_to_seqsero2

# Render a tool-ready layout in an external directory
python3 layout.py --challenge wrong_organism/ecoli_to_seqsero2 --tool seqsero2 --out /tmp/run

# Run the tool (example)
seqsero2 -m k -t 4 -i /tmp/run/assembly.fasta

# Download + layout for an alignment challenge
python3 acquire.py --challenge platform_mismatch/ont_reads_short_read_aligner
python3 layout.py --challenge platform_mismatch/ont_reads_short_read_aligner --tool bwa-family --out /tmp/ont_run
bwa mem /tmp/ont_run/reference.fasta /tmp/ont_run/reads_1.fq.gz /tmp/ont_run/reads_2.fq.gz > /tmp/ont_run/aligned.sam
```

---

## acquire.py

Downloads sequence data for challenges based on their `manifest.json`. Handles NCBI assembly downloads (`ncbi-datasets-cli`), SRA read downloads (`sra-tools`), and recipe-based synthetic data generation (`python3`, `seqtk`, etc.).

```
python3 acquire.py --all
python3 acquire.py --challenge PHENOMENON/INSTANCE
python3 acquire.py --phenomenon PHENOMENON
python3 acquire.py --challenge PHENOMENON/INSTANCE --force
```

| Flag | Effect |
|---|---|
| `--all` | Download/generate data for every challenge in the library |
| `--challenge PHENOMENON/INSTANCE` | One specific challenge (e.g. `contamination/sample_swap_ecoli_in_typhimurium`) |
| `--phenomenon SLUG` | All challenges under a phenomenon directory (e.g. `amr_detection`) |
| `--force` | Re-download/regenerate even if data files already exist |

**Downloaded data** lands in `PHENOMENON/INSTANCE/data/`. This directory is gitignored — no bulk sequence data is committed.

**Recipe challenges** run a shell command (Python, seqtk, etc.) to generate synthetic data locally. Required tools must be installed. The manifest's `recipe.tools_required` field lists what's needed.

**Tool name mapping:**

| Manifest `tool` value | Binary expected |
|---|---|
| `ncbi-datasets-cli` | `datasets` |
| `sra-tools` | `fasterq-dump` |
| `python3` | `python3` |
| `seqtk` | `seqtk` |
| `gzip` | `gzip` |

---

## layout.py

Creates a symlink tree in an external `--out` directory so downloaded data appears in the directory structure each tool family expects. Data is not copied — symlinks point back to `data/` in the challenge directory. The `--out` directory (and any subdirectories) are created automatically.

```
python3 layout.py --challenge PHENOMENON/INSTANCE --tool TOOL_FAMILY --out /path/to/dir
python3 layout.py --list-tools
```

| Flag | Effect |
|---|---|
| `--challenge PHENOMENON/INSTANCE` | Which challenge to render |
| `--tool TOOL_FAMILY` | Tool family layout to apply (see below) |
| `--out PATH` | Directory to write symlinks into (created if absent) |
| `--list-tools` | Print all available tool families with invocation hints |

**Notes:**
- Run `acquire.py` before `layout.py`. If source data is missing, `layout.py` prints the `acquire.py` command needed and exits non-zero.
- Each call to `layout.py` overwrites the `--out` directory.
- The `--out` path is independent of the challenge directory — use a temp dir or a scratch workspace. Layouts are gitignored.
- `layout.py` warns if the requested tool family is not listed in the manifest's `tool_families` field, but proceeds anyway.

---

## Tool Families

| Family | Tools | Invocation hint |
|---|---|---|
| `bwa-family` | BWA-MEM, BWA-MEM2, Bowtie2 | `bwa index reference.fasta && bwa mem reference.fasta reads_1.fq.gz reads_2.fq.gz > aligned.sam` |
| `snippy-family` | snippy + snippy-core | `for dir in samples/*/; do snippy --ref reference.fasta --R1 $dir/reads_1.fq.gz --R2 $dir/reads_2.fq.gz --outdir $(basename $dir)_snps; done && snippy-core --ref reference.fasta *_snps/` |
| `cfsan-snp-pipeline` | CFSAN-SNP-Pipeline | `cfsan_snp_pipeline run reference.fasta samples/` |
| `spades-family` | SPAdes, Unicycler | `spades.py -1 reads_1.fq.gz -2 reads_2.fq.gz -o spades_output/` |
| `seqsero2` | SeqSero2 (assembly mode) | `seqsero2 -m k -t 4 -i assembly.fasta` |
| `sistr` | SISTR | `sistr -i assembly.fasta -f tab -o sistr_results` |
| `mlst` | mlst (tseemann) | `mlst *.fasta` |
| `resfinder-family` | ResFinder, AMRFinderPlus, abricate | `abricate --db resfinder assembly.fasta` |
| `prokka-family` | Prokka, Bakta | `prokka --outdir prokka_output/ --prefix sample assembly.fasta` |

Run `python3 layout.py --list-tools` for the live list with current descriptions.

---

## Challenge Index

22 challenges across 10 phenomenon categories.

### amr_detection (5)

| Instance | Tool categories | Data source |
|---|---|---|
| `novel_gene_below_threshold` | in_silico_typing | recipe (python3) |
| `truncated_gene_at_contig_boundary` | in_silico_typing, assembly | recipe (python3) |
| `fluoroquinolone_point_mutation_missed` | in_silico_typing | SRR8301919 (C. jejuni, PRJNA509514) |
| `mcr1_colistin_plasmid_context` | in_silico_typing | SRR38363847 (E. coli, PRJNA1461862) |
| `disrupted_resistance_gene` | in_silico_typing | recipe (python3) |

### contamination (3)

| Instance | Tool categories | Data source |
|---|---|---|
| `sample_swap_ecoli_in_typhimurium` | population_variant_analysis | GCF_000006945.2 + SRR accessions |
| `mixed_lineages_st19_st34` | population_variant_analysis | GCF_000006945.2 + SRR/ERR accessions |
| `contaminated_reads_chimeric_assembly` | assembly | recipe (seqtk mix of SRR accessions) |

### degenerate_input (3)

| Instance | Tool categories | Data source |
|---|---|---|
| `empty_fastq` | alignment, assembly, in_silico_typing, qc | recipe (gzip) |
| `all_n_reads` | alignment, assembly, in_silico_typing | recipe (python3) |
| `mismatched_read_pairs` | alignment | recipe (python3) |

### extreme_gc (1)

| Instance | Tool categories | Data source |
|---|---|---|
| `streptomyces_coverage_dropout` | assembly, alignment | ERR16938122 + GCF_000203835.1 |

### file_format (1)

| Instance | Tool categories | Data source |
|---|---|---|
| `iupac_bases_in_reference` | alignment | recipe (python3) + GCF_000006945.2 |

### high_recombination (1)

| Instance | Tool categories | Data source |
|---|---|---|
| `helicobacter_pylori_cohort` | population_variant_analysis | GCF_000008525.1 + DRR accessions |

### low_coverage (2)

| Instance | Tool categories | Data source |
|---|---|---|
| `outlier_in_typhimurium_cohort` | population_variant_analysis | SRR accessions + recipe (seqtk) |
| `sparse_assembly` | assembly | recipe (seqtk) |

### platform_mismatch (1)

| Instance | Tool categories | Data source |
|---|---|---|
| `ont_reads_short_read_aligner` | alignment | SRR37380174 (ONT) + GCF_000006945.2 |

### repetitive_genome (3)

| Instance | Tool categories | Data source |
|---|---|---|
| `rrna_operon_collapse` | assembly | SRR38945246 |
| `is_element_collapse_ecoli` | assembly | SRR1770413 |
| `circular_reference_linearization` | alignment | SRR38945246 + GCF_000006945.2 |

### wrong_organism (1)

| Instance | Tool categories | Data source |
|---|---|---|
| `ecoli_to_seqsero2` | in_silico_typing | GCF_000005845.2 |

### wrong_reference (1)

| Instance | Tool categories | Data source |
|---|---|---|
| `typhimurium_cohort_enteritidis_ref` | population_variant_analysis | GCF_000009505.1 + SRR accessions |

---

## Typical Workflow

```bash
# 1. Pick a challenge
ls amr_detection/

# 2. Read the manifest to understand what the challenge tests
cat amr_detection/novel_gene_below_threshold/manifest.json | python3 -m json.tool | less

# 3. Download the data
python3 acquire.py --challenge amr_detection/novel_gene_below_threshold

# 4. Lay it out for your tool
python3 layout.py --challenge amr_detection/novel_gene_below_threshold --tool resfinder-family --out /tmp/amr_test

# 5. Run the tool
ls /tmp/amr_test/                    # see what files the layout created
abricate --db resfinder /tmp/amr_test/assembly.fasta

# 6. Interpret: compare what the tool reports against the manifest's mechanism and ground_truth
```

---

## File Layout After Download

```
test/challenges/
├── acquire.py               # download script
├── layout.py                # symlink layout renderer
├── tool_layouts/            # per-tool-family layout templates (JSON)
│   ├── bwa-family.json
│   └── ...
├── PHENOMENON/
│   └── INSTANCE/
│       ├── manifest.json    # committed — defines the challenge
│       ├── data/            # gitignored — downloaded/generated by acquire.py
│       │   └── SAMPLE_ID/
│       │       ├── assembly.fasta
│       │       └── reads_*.fq.gz
│       └── layouts/         # gitignored — rendered by layout.py (if --out points here)
```

---

## Adding a New Challenge

1. Create `PHENOMENON/INSTANCE/manifest.json` following [`MANIFEST_SCHEMA.md`](MANIFEST_SCHEMA.md)
2. Verify all NCBI accessions live with `efetch runinfo` before committing
3. Test the download: `python3 acquire.py --challenge PHENOMENON/INSTANCE`
4. Test a layout: `python3 layout.py --challenge PHENOMENON/INSTANCE --tool FAMILY --out /tmp/test`
5. Commit only the manifest — never commit data files
