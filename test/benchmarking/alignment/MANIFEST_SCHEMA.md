# Benchmark Manifest Schema

Each target directory contains a `manifest.json` defining the reference genome,
acquisition method, simulation parameters, and benchmark metadata. This schema
is distinct from `test/challenges/MANIFEST_SCHEMA.md`.

---

## Complete Example (real genome target)

```json
{
  "id": "T3",
  "name": "h37rv",
  "organism": "Mycobacterium tuberculosis",
  "strain_assembly": "H37Rv",
  "target_type": "real_genome",
  "tier": 1,
  "key_challenge": "Very high GC (~65.6%), PE/PPE and PE_PGRS repeat gene families",
  "size_approx": "4.41 Mb",
  "length_bp": 4411532,
  "gc_percent": 65.6,
  "ploidy": "haploid",
  "reference": {
    "refseq": "NC_000962.3",
    "genbank": "AL123456.3",
    "assembly": "GCA_000195955.2",
    "download": {
      "tool": "entrez-direct",
      "command": "efetch -db nucleotide -id NC_000962.3 -format fasta > reference.fasta"
    }
  },
  "simulation": {
    "tool": "dwgsim",
    "command": "dwgsim -1 150 -2 150 -C 100 -z {rng_seed} ../reference/reference.fasta reads && mv reads.bwa.read1.fastq.gz reads_1.fastq.gz && mv reads.bwa.read2.fastq.gz reads_2.fastq.gz",
    "read_length_bp": 150,
    "coverage_x": 100
  },
  "truth": {
    "simulated": "dwgsim read name encodes true origin coordinates; evaluate with paftools.js mapeval"
  },
  "benchmark_notes": "Partition accuracy by PE/PPE vs. non-PE/PPE regions.",
  "curation": {
    "curator": "Justin Payne",
    "date": "2026-06-03"
  }
}
```

---

## Top-Level Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Target identifier: `T1`–`T8c` for real genomes, `S1`–`S5` for synthetic |
| `name` | string | yes | Short slug matching the directory name |
| `organism` | string | yes | Full organism name |
| `strain_assembly` | string | yes | Strain and/or assembly version |
| `target_type` | string | yes | `real_genome` or `synthetic` |
| `tier` | int | yes | `1` for real genome targets, `2` for synthetic torture tests |
| `key_challenge` | string | yes | One-line description of the primary alignment stress |
| `size_approx` | string | no | Human-readable genome size |
| `length_bp` | int | no | Exact reference length in base pairs |
| `gc_percent` | float | no | GC content (%). For AT-rich genomes record AT percent instead |
| `at_percent` | float | no | AT content (%) — use for AT-biased genomes (T5, etc.) |
| `ploidy` | string | no | `haploid`, `diploid`, `hexaploid`, `haploid_representation`, etc. |
| `chromosomes` | int | no | Chromosome count |
| `reference` | object | yes* | Reference acquisition config. Required for real genome targets. |
| `construction` | object | yes* | Synthetic genome construction config. Required for synthetic targets. |
| `simulation` | object | no | Read simulation config. Omit if simulation is not applicable. |
| `real_reads` | object | no | Real read acquisition config (T1 GIAB only) |
| `sweep` | object | no | Parameter sweep config for synthetic targets |
| `truth` | object | yes | Truth encoding description |
| `benchmark_notes` | string | no | Evaluation guidance: partitioning, known behaviors, etc. |
| `curation` | object | yes | Provenance metadata |

---

## `reference` Object (real genome targets)

| Field | Type | Required | Description |
|---|---|---|---|
| `refseq` | string | no | NCBI RefSeq accession |
| `genbank` | string | no | GenBank accession |
| `assembly` | string | no | Assembly accession (GCA_ or GCF_) |
| `assembly_refseq` | string | no | RefSeq assembly accession (GCF_) |
| `assembly_genbank` | string | no | GenBank assembly accession (GCA_) |
| `assembly_name` | string | no | Human-readable assembly name |
| `url` | string | no | Direct download URL (for non-NCBI sources) |
| `notes` | string | no | Download caveats; VERIFY flags for accessions that may change |
| `download` | object | yes | Download instructions (see below) |

### `reference.download`

| Field | Type | Required | Description |
|---|---|---|---|
| `tool` | string | yes | Primary tool: `entrez-direct`, `ncbi-datasets-cli`, `wget`, `curl` |
| `command` | string | yes | Shell command run from `data/reference/` directory. Outputs `reference.fasta`. |

The `{rng_seed}` placeholder is substituted with the value from `global.json` at acquisition time.

---

## `construction` Object (synthetic targets)

| Field | Type | Required | Description |
|---|---|---|---|
| `tool` | string | yes | Primary construction tool |
| `description` | string | yes | What the construction step produces |
| `parameters` | object | yes | Key construction parameters (for documentation and reproducibility) |
| `requires_base_reference` | string | no | Relative path to the base reference that must exist before construction |
| `requires_references` | string[] | no | List of required reference paths (for targets needing multiple references, e.g. S4) |
| `tools_required` | string[] | yes | All tools needed for construction |
| `command` | string | no | Single construction command (use `commands` for multi-step) |
| `commands` | string[] | no | Ordered list of construction commands |
| `truth_outputs` | string[] | yes | Files produced that encode ground truth (BED, VCF, TSV) |
| `notes` | string | no | Construction caveats |

---

## `simulation` Object

| Field | Type | Required | Description |
|---|---|---|---|
| `tool` | string | yes | Simulator: `dwgsim`, `art_illumina`, `mason2`, `gargammel` |
| `command` | string | yes | Shell command run from `data/reads/` directory |
| `read_length_bp` | int | yes | Simulated read length |
| `coverage_x` | int/float | no | Target coverage depth |
| `parameters` | object | no | Sweep parameters (S2: fragment lengths, damage levels) |
| `notes` | string | no | Simulation caveats, error model notes |

The `{rng_seed}` placeholder is substituted from `global.json`.

Output convention: `reads_1.fastq.gz` and `reads_2.fastq.gz` (paired-end).
Single-end simulators produce `reads_1.fastq.gz` only.

---

## `real_reads` Object (T1 only)

| Field | Type | Description |
|---|---|---|
| `flag` | string | CLI flag that enables this download (`--giab`) |
| `description` | string | What these reads are and why they're needed |
| `source` | string | Data source name |
| `sra_range_start` | string | First SRA experiment accession |
| `sra_range_end` | string | Last SRA experiment accession |
| `coverage_x` | int | Approximate coverage |
| `read_length_bp` | int | Read length |
| `layout` | string | `paired` or `single` |
| `ftp` | string | FTP URL for direct download |
| `truth_vcf` | string | URL to GIAB truth VCF |
| `eval_tool` | string | Variant evaluation tool (`hap.py`) |
| `eval_notes` | string | Evaluation protocol notes |

---

## `sweep` Object (synthetic targets)

| Field | Type | Description |
|---|---|---|
| `parameter` | string | Name of the swept parameter |
| `values` | array | Parameter values to sweep over |
| `notes` | string | How to interpret the sweep in evaluation |

---

## `truth` Object

| Field | Type | Description |
|---|---|---|
| `type` | string | Truth encoding: `simulated_coordinates`, `per_copy_placement`, `haplotype_of_origin`, `sv_breakpoints`, `origin_chromosome` |
| `format` | string | Format of truth data: `dwgsim_read_names`, `art_read_names`, `bed`, `vcf`, etc. |
| `file` | string | Relative path to truth file (for file-based truth) |
| `eval_tool` | string | Recommended evaluation tool |
| `eval_notes` | string | Evaluation protocol notes |

---

## `curation` Object

| Field | Type | Required | Description |
|---|---|---|---|
| `curator` | string | yes | Name of curator |
| `date` | string | yes | ISO 8601 curation date |
| `notes` | string | no | Known limitations, VERIFY items, suggested improvements |

---

## VERIFY convention

Fields or notes containing `VERIFY` indicate accessions or URLs that should be
confirmed against the live source before acquisition. Assembly versions increment
over time and the live record takes precedence over this manifest.

---

## global.json reference

`global.json` in the benchmark root contains shared constants read by `acquire.py`
and `score.py`:

| Field | Description |
|---|---|
| `rng_seed` | Integer RNG seed used in all simulation and construction commands via `{rng_seed}` placeholder |
| `simulation.default_simulator` | Fallback simulator if manifest does not specify one |
| `simulation.read_length_bp` | Default read length |
| `simulation.default_coverage_x` | Default coverage depth |
| `measurement.threads` | Recommended thread count for timed aligner runs |
| `measurement.replicates` | Minimum replicate runs per target |
| `scoring.alpha` | Default α for CBS (0.7 per spec) |
| `scoring.placement_tolerance_bp` | Default d for PA (10 bp per spec) |
