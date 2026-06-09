# Agent Guide — Short-Read Aligner Benchmark

This document is written for AI agents executing the benchmark end-to-end. It
describes each phase, the expected inputs and outputs, and how to format results
for `score.py`. Human users may also follow this as a protocol reference.

The normalization framework (BNT, CAS, CBS) is fully described in the companion
spec document. This guide focuses on the mechanical workflow.

---

## Overview

The benchmark has five phases:

1. **Acquire** — download reference genomes and simulate reads (`acquire.py`)
2. **Index** — build aligner indices from reference FASTAs
3. **Align** — run each aligner, capturing wall time and peak RSS
4. **Evaluate** — compute placement accuracy (PA) and MAPQ calibration (MCS)
5. **Score** — compute BNT, CAS, CBS, MEI from results table (`score.py`)

Additionally, for T1 with `--giab`: call variants with GATK, evaluate with
`hap.py` to get variant accuracy (VA).

---

## Phase 1 — Acquire data

```bash
# Download all targets (references + simulate reads where tools are present)
python acquire.py --all

# Download a single target
python acquire.py --target T1

# Download T1 with GIAB real reads (~300x, large download, opt-in)
python acquire.py --target T1 --giab

# Download all synthetic targets
python acquire.py --synthetic

# Force re-download even if files exist
python acquire.py --all --force
```

`acquire.py` checks for simulation and construction tools at startup and reports
any that are missing. Public reference downloads proceed regardless. Simulation
and construction are skipped only if the required tool is absent.

### Required tools by phase

| Phase | Tools |
|---|---|
| Reference download | `entrez-direct` (efetch), `ncbi-datasets-cli` (datasets), `wget` |
| Read simulation | `dwgsim` (most targets), `art_illumina` (T8, large genomes), `gargammel` (S2 only) |
| Synthetic construction | `simuG` (S1, S3), `VISOR` (S5), `python3` + `biopython` (S1, S3, S4) |
| GIAB download | `fasterq-dump` (sra-tools) |
| GIAB variant eval | `gatk` (HaplotypeCaller), `hap.py` |

### Output layout per target

```
{organism}/{name}/data/
  reference/
    reference.fasta       # downloaded or constructed reference
    reference.fasta.fai   # build with: samtools faidx reference.fasta
    truth.bed             # synthetic targets only
    copy_identity_map.tsv # S1 only
    mito.fasta            # S4 only
  reads/
    reads_1.fastq.gz      # simulated R1
    reads_2.fastq.gz      # simulated R2
  giab/                   # T1 --giab only
    *.fastq.gz
```

---

## Phase 2 — Build aligner indices

Build indices for each aligner before the timed query phase. Index build time
is reported separately and NOT included in the query timing used for BNT.

```bash
# BWA-MEM2 example
bwa-mem2 index {target}/data/reference/reference.fasta

# Bowtie2 example
bowtie2-build {target}/data/reference/reference.fasta {target}/data/reference/bt2_index

# minimap2 does not require a pre-built index step; include -d flag for index caching
minimap2 -d {target}/data/reference/reference.mmi {target}/data/reference/reference.fasta
```

---

## Phase 3 — Align and time

Time the **query phase only** (not index build). Use `/usr/bin/time -v` to
capture peak RSS and wall time together.

```bash
/usr/bin/time -v bwa-mem2 mem \
    -t 8 \
    {target}/data/reference/reference.fasta \
    {target}/data/reads/reads_1.fastq.gz \
    {target}/data/reads/reads_2.fastq.gz \
    > {aligner}_{target}.sam \
    2> {aligner}_{target}.time.txt
```

### Required measurements per run

| Field | Source |
|---|---|
| `reads` | read count from simulation manifest |
| `wall_time_s` | "Elapsed (wall clock) time" from `/usr/bin/time -v` |
| `threads` | thread count used (keep constant across all aligners) |
| `peak_rss_gb` | "Maximum resident set size" ÷ 1,048,576 from `/usr/bin/time -v` |

Run at least 3 replicates per aligner per target (warm cache). Record mean
wall time; investigate if CV > 5%.

### Parsing `/usr/bin/time -v` output

```python
import re, subprocess

def parse_time_output(text):
    wall = re.search(r'Elapsed \(wall clock\) time.*?(\d+):(\d+\.\d+)', text)
    rss  = re.search(r'Maximum resident set size \(kbytes\): (\d+)', text)
    wall_s = int(wall.group(1)) * 60 + float(wall.group(2)) if wall else None
    rss_gb = int(rss.group(1)) / 1_048_576 if rss else None
    return wall_s, rss_gb
```

---

## Phase 4 — Evaluate placement accuracy

For simulated reads, extract true origin coordinates from read names and
compare to reported alignment positions.

### Using paftools.js mapeval (recommended)

Convert SAM to PAF first, then evaluate:

```bash
# SAM → PAF
samtools view -F4 {aligner}_{target}.sam | \
    paftools.js sam2paf - > {aligner}_{target}.paf

# Evaluate (dwgsim read name format)
paftools.js mapeval {aligner}_{target}.paf > {aligner}_{target}.mapeval.txt
```

`paftools.js mapeval` reports accuracy stratified by MAPQ. Extract PA and MCS:

- **PA**: fraction correctly placed within tolerance d (report at d=1,5,10,50 bp;
  use d=10 for CAS)
- **MCS**: 1 − ECE, computed from the MAPQ-stratified accuracy table. ECE formula
  is in the normalization spec §4.3.2.

### MAPQ calibration score (MCS) — computation

```python
import math

MAPQ_BINS = [(0,9),(10,19),(20,29),(30,39),(40,49),(50,59),(60,255)]

def compute_mcs(mapq_accuracy_table):
    """
    mapq_accuracy_table: list of (mapq_bin_label, n_reads, n_correct) tuples
    Returns MCS in [0, 1].
    """
    total = sum(n for _, n, _ in mapq_accuracy_table)
    if total == 0:
        return 0.0
    ece = 0.0
    for bin_label, n, n_correct in mapq_accuracy_table:
        if n == 0:
            continue
        acc = n_correct / n
        q_mean = sum(range(bin_label[0], min(bin_label[1]+1, 255))) / (bin_label[1] - bin_label[0] + 1)
        conf = 1.0 - 10 ** (-q_mean / 10)
        ece += (n / total) * abs(acc - conf)
    return 1.0 - ece
```

---

## Phase 4b — Variant accuracy (T1 GIAB only)

Only required for the variant accuracy (VA) component of CAS on target T1.
Skip if GIAB reads were not downloaded with `--giab`.

```bash
# Align GIAB reads to full GRCh38 (not just chr1)
bwa-mem2 mem -t 8 grch38_full.fasta \
    homo_sapiens/chr1/data/giab/reads_1.fastq.gz \
    homo_sapiens/chr1/data/giab/reads_2.fastq.gz \
    | samtools sort -o giab_aligned.bam
samtools index giab_aligned.bam

# Call variants (pinned GATK version — record in results)
gatk HaplotypeCaller -R grch38_full.fasta -I giab_aligned.bam -O calls.vcf.gz

# Evaluate against GIAB truth — restrict to chr1 ∩ high-confidence BED
hap.py \
    /path/to/giab/HG001_GRCh38_GIAB_highconf.vcf.gz \
    calls.vcf.gz \
    -r grch38_full.fasta \
    --target-regions chr1 \
    -f /path/to/giab/HG001_GRCh38_highconf.bed \
    -o haplo_results
```

VA is the geometric mean of SNP F1 and indel F1 from `haplo_results.summary.csv`.

---

## Phase 5 — Platform characterization (STREAM Triad)

Run once per platform and record the result in your results file.

```bash
# Download and build STREAM v5.10+
wget https://www.cs.virginia.edu/stream/FTP/Code/stream.c
gcc -O3 -march=native -fopenmp -DSTREAM_ARRAY_SIZE=400000000 -o stream stream.c
./stream
```

Record the **Triad** result (GB/s). Use the best single-run value as `stream_triad_gbps`.
Array size of 4×10⁸ doubles (~3.2 GB each, ~9.6 GB total) ensures DRAM is measured.

On NUMA systems: `numactl --membind=0 --cpunodebind=0 ./stream`

---

## Phase 6 — Format results for score.py

### JSON format (primary)

```json
{
  "platform": {
    "stream_triad_gbps": 80.0,
    "cpu_model": "Intel Xeon Gold 6248R",
    "threads": 8
  },
  "aligners": [
    {
      "name": "bwa-mem2",
      "version": "2.2.1",
      "targets": [
        {
          "id": "T1",
          "reads": 10000000,
          "wall_time_s": 45.2,
          "threads": 8,
          "pa": 0.941,
          "mcs": 0.881,
          "va": 0.962,
          "peak_rss_gb": 6.1,
          "genome_size_gb": 0.249
        },
        {
          "id": "T3",
          "reads": 500000,
          "wall_time_s": 3.1,
          "threads": 8,
          "pa": 0.973,
          "mcs": 0.904,
          "peak_rss_gb": 0.8,
          "genome_size_gb": 0.0044
        }
      ]
    }
  ]
}
```

**Notes:**
- `va` is only valid for T1 with GIAB reads. Omit the field entirely for all other targets.
- `threads` in each target record overrides `platform.threads` for that run.
- `genome_size_gb` is the reference FASTA size used for MEI computation.
- Include all targets evaluated; missing targets are excluded from CAS aggregation.

### TSV format (alternative, via --from-tsv)

```
aligner	version	target	reads	wall_time_s	threads	pa	mcs	va	peak_rss_gb	genome_size_gb
bwa-mem2	2.2.1	T1	10000000	45.2	8	0.941	0.881	0.962	6.1	0.249
bwa-mem2	2.2.1	T3	500000	3.1	8	0.973	0.904		0.8	0.0044
bowtie2	2.5.3	T1	10000000	120.0	8	0.967	0.954	0.971	4.2	0.249
```

Leave `va` empty (not "NA", just empty) for non-T1 targets.

---

## Phase 7 — Score

```bash
# From JSON
python score.py results.json

# From TSV
python score.py --from-tsv results.tsv --bandwidth 80.0

# Custom alpha
python score.py results.json --alpha 0.8

# Sensitivity analysis (required for publication)
python score.py results.json --sensitivity

# Save intermediate JSON for downstream analysis
python score.py results.json --sensitivity --json results_scored.json

# Pipe to file
python score.py results.json > benchmark_table.txt
```

### Required sensitivity analysis

All publications using CBS must report the α sensitivity table. Run:

```bash
python score.py results.json --sensitivity
```

And verify that rankings are stable across α ∈ {0.5, 0.6, 0.7, 0.8, 0.9}. If
rankings change, report all CBS values in supplementary materials.

---

## Synthetic target evaluation notes

### S1 — Segmental duplication

Score reads by which copy they mapped to using `numt_truth.bed` (copy boundaries)
and `copy_identity_map.tsv`. For each identity bin, report:
- PA overall
- Fraction "confidently wrong" (MAPQ ≥ 20, wrong copy) — headline stat
- MAPQ calibration within the array vs. in flanking spacers

### S2 — Ancient DNA

Run each (fragment length, damage level) combination independently. Report
mapped fraction vs. fragment length as the primary curve. Validate damage
profile with `mapDamage2` before scoring — if the damage profile is wrong,
the simulation is wrong.

### S3 — Divergent haplotype

Map the mixed {H1+H2} read set against H1 only. Stratify results by read
origin (H1 vs. H2) using dwgsim read names. Report H2 sensitivity vs. divergence
percent as the primary curve. Track soft-clip rate for H2 reads.

### S4 — NUMT trap

Compare mito-origin read destinations against `numt_truth.bed`. A mito read
that maps to a nuclear NUMT position is "misrouted". Report misrouting rate per
NUMT identity bin. A perfectly calibrated aligner should route mito reads to the
mito contig at all NUMT identity levels, with MAPQ degrading as NUMT identity
increases.

### S5 — SV breakpoints

For each breakpoint in `svs.bed`, classify reads spanning it as:
- `split_correct`: split-mapped with breakpoint within 5 bp of truth
- `soft_clipped`: one end clipped at breakpoint position
- `mismapped`: mapped linearly across breakpoint with no evidence of SV

Report split-read recall and position accuracy vs. SV density.

---

## Checklist for a complete benchmark run

- [ ] `acquire.py --all` completed without reference download failures
- [ ] Simulation completed for all targets (reads_1.fastq.gz present)
- [ ] Platform STREAM Triad measured and recorded
- [ ] Aligner versions pinned and recorded
- [ ] GATK version pinned (if running GIAB variant eval)
- [ ] All aligners run with identical thread count
- [ ] ≥ 3 replicates per aligner per target; CV < 5%
- [ ] PA computed at d ∈ {1, 5, 10, 50} bp (d=10 used for CAS)
- [ ] MCS computed from MAPQ reliability diagram
- [ ] Results formatted as JSON or TSV per schema above
- [ ] `score.py --sensitivity` run; α sensitivity table included in report
- [ ] Per-target CAS breakdown reported alongside aggregate CAS
