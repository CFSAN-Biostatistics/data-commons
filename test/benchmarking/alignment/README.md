# Short-Read Aligner Benchmark

A tiered benchmark corpus for comparing short-read alignment tools across
genomes of increasing structural complexity, plus synthetic torture tests that
isolate specific aligner failure modes.

Provides: reference accessions, simulation parameters, construction scripts for
synthetic genomes, a data acquisition tool (`acquire.py`), and a scoring tool
(`score.py`) implementing the Bandwidth-Normalized Throughput (BNT) / Composite
Accuracy Score (CAS) / Combined Benchmark Score (CBS) framework.

**This directory contains only manifests and scripts — no sequence data.** Run
`acquire.py` to download references and generate simulated reads locally.

---

## Quick start

```bash
# Download all references and simulate reads (requires dwgsim in PATH)
python acquire.py --all

# Run your aligner, collect timing and accuracy results, write results.json
# (see AGENTS.md for the full protocol)

# Score results
python score.py results.json --sensitivity
```

---

## Directory structure

```
test/benchmarking/alignment/
  global.json                        # RNG seed, scoring defaults, protocol constants
  acquire.py                         # Reference download + read simulation
  score.py                           # BNT / CAS / CBS / MEI scoring tool
  AGENTS.md                          # Step-by-step benchmark protocol (agents + humans)
  MANIFEST_SCHEMA.md                 # Manifest field reference
  README.md                          # This file
  scripts/
    build_segdup.py                  # Construct S1 segmental duplication array
    build_het_hybrid.py              # Construct S3 divergent haplotype pair
    build_numt_trap.py               # Construct S4 NUMT trap reference
  homo_sapiens/chr1/                 # T1: GRCh38 chr1 (human baseline + GIAB truth)
  gallus_gallus/grcg7b/              # T2: Chicken bGalGal1 (ERVs, micro/macrochromosomes)
  mycobacterium_tuberculosis/h37rv/  # T3: MTB H37Rv (high GC, PE/PPE repeats)
  staphylococcus_aureus/mrsa252/     # T4: MRSA252 (low GC, mobile elements)
  plasmodium_falciparum/3d7/         # T5: Pf 3D7 (extreme AT-bias, var repeats)
  clostridioides_difficile/630/      # T6: C. diff 630 (mosaic, mobile elements)
  candida_albicans/sc5314_haploid/   # T7a: SC5314 haploid (paralog families)
  candida_albicans/sc5314_diploid/   # T7b: SC5314 diploid Assembly 22 (LOH, het)
  triticum_aestivum/chr3b/           # T8a: Wheat chr3B (homeolog ambiguity, ~830 Mb)
  triticum_aestivum/hexaploid/       # T8b: Full hexaploid wheat (~17 Gb)
  triticum_aestivum/aegilops_tauschii_aet_v4/  # T8c: Aegilops diploid (~4.3 Gb)
  synthetic/segmental_duplication/   # S1: Identity-gradient paralog array
  synthetic/ancient_dna/             # S2: Short/damaged aDNA read profile
  synthetic/divergent_haplotype/     # S3: High-divergence haplotype read dropout
  synthetic/numt_trap/               # S4: Mito reads misrouted to nuclear NUMTs
  synthetic/sv_breakpoint/           # S5: Dense SV breakpoint gauntlet
```

---

## Target glossary

| ID | Organism | Assembly | Why it's here |
|---|---|---|---|
| T1 | *Homo sapiens* | GRCh38 chr1 | Human baseline; only target with real-read variant truth (GIAB) |
| T2 | *Gallus gallus* | bGalGal1.mat.broiler.GRCg7b | ERV content, macro/microchromosome size range |
| T3 | *Mycobacterium tuberculosis* | H37Rv | High GC (~65.6%), PE/PPE repeat families |
| T4 | *Staphylococcus aureus* | MRSA252 | Low GC (~32.8%), mobile genetic elements |
| T5 | *Plasmodium falciparum* | 3D7 | Extreme AT-bias (~81%), var/rifin/stevor multimapping |
| T6 | *Clostridioides difficile* | 630 | Mosaic genome, mobile elements |
| T7a | *Candida albicans* | SC5314 haploid (ASM18296v3) | Paralog families — simpler haploid control |
| T7b | *Candida albicans* | SC5314 diploid Assembly 22 | Heterozygosity, LOH tracts |
| T8a | *Triticum aestivum* | IWGSC RefSeq v2.1 chr3B | Homeolog ambiguity (~95% A/B/D identity), tractable scale |
| T8b | *Triticum aestivum* | IWGSC RefSeq v2.1 full | Full hexaploid scale for MEI testing (~17 Gb) |
| T8c | *Aegilops tauschii* | Aet v4.0 | Wheat D-genome diploid tractable alternative (~4.3 Gb) |
| S1 | Synthetic | Segmental duplication array | Confident mismap in high-identity paralogs (98–99.9% identity sweep) |
| S2 | Synthetic | Ancient/damaged reads | Short/damaged read sensitivity and MAPQ calibration |
| S3 | Synthetic | Divergent haplotype | Read dropout at 1–8% divergence |
| S4 | Synthetic | NUMT trap | Mitochondrial reads misrouted to nuclear insertions |
| S5 | Synthetic | SV breakpoint gauntlet | Clip vs. split vs. mismap at dense breakpoints |

### Metric glossary

| Term | Definition |
|---|---|
| **BNT** | Bandwidth-Normalized Throughput: reads / (wall_time × threads × STREAM_Triad_GB/s). Platform-independent speed measure in reads·thread⁻¹·GB⁻¹. |
| **PA** | Placement Accuracy: fraction of simulated reads mapped within d bp of true origin (default d = 10 bp). |
| **MCS** | MAPQ Calibration Score: 1 − ECE (Expected Calibration Error), measuring how well MAPQ values predict actual error rates. |
| **VA** | Variant Accuracy: F1 for SNP and indel calls against GIAB truth VCF (T1 only). |
| **CAS** | Composite Accuracy Score: geometric mean of PA, MCS, and (for T1) VA across all targets. |
| **CBS** | Combined Benchmark Score: CAS^α × BNT_norm^(1−α), default α = 0.7. Single-number leaderboard summary. |
| **MEI** | Memory Efficiency Index: peak RSS / reference genome size. Index "bloat factor". |
| **ECE** | Expected Calibration Error: MAPQ-bin-weighted mean absolute difference between observed accuracy and predicted confidence. |
| **STREAM Triad** | Sustained main-memory bandwidth (GB/s) measured by the STREAM benchmark Triad kernel. Platform characterization constant for BNT normalization. |
| **GIAB** | Genome in a Bottle: NIST truth variant set for HG001/NA12878 used for VA evaluation on T1. |
| **NUMT** | Nuclear Mitochondrial DNA insert: fragment of mitochondrial sequence embedded in the nuclear genome. |
| **LOH** | Loss of Heterozygosity: genomic region where a diploid organism has become effectively haploid. |

---

## Scoring

`score.py` computes BNT, CAS, CBS, and MEI from a results table you provide.
It does not run aligners — you time your own runs and supply the measurements.

```bash
python score.py results.json
python score.py --from-tsv results.tsv --bandwidth 80.0
python score.py results.json --alpha 0.8 --sensitivity --json full_results.json
```

The normalization framework is described in the companion specification document.
Parameters α = 0.7 and d = 10 bp are the spec defaults; both are adjustable CLI
flags. Any publication using CBS must report the α sensitivity table
(`--sensitivity` flag) and disclose the α value used.

---

## Open items (VERIFY before full run)

- **GRCh38 patch level** — confirm current patch at NCBI; chr1 sequence
  NC_000001.11 is stable but parent assembly accession increments.
- **Wheat v2.1 URLs** — URGI file listing changes; verify download URL in
  T8a and T8b manifests before acquisition.
- **Aegilops Aet version** — T8c uses Aet v4.0 (GCA_002575655.1); Aet v5.0
  and v6.0 exist. Confirm desired version before download.
- **Aligner roster** — pin aligner versions in your results JSON before
  publishing; suggested baseline: BWA-MEM2, Bowtie2, minimap2 (sr preset).

---

## References

- Normalization framework: companion spec `aligner_benchmark_normalization_spec.md`
- Roofline Model: Williams, Waterman & Patterson, *CACM* 52(4), 2009
- STREAM benchmark: McCalpin, https://www.cs.virginia.edu/stream/
- GIAB: Zook et al., *Nature Biotechnology* 32, 246–251, 2014
- dwgsim: https://github.com/nh13/DWGSIM
- art_illumina: Huang et al., *Bioinformatics* 28(4), 2012
- gargammel: Renaud et al., *Bioinformatics* 33(4), 2017
- simuG: Yue & Liti, *Bioinformatics* 35(21), 2019
- VISOR: Bolognini et al., *Bioinformatics* 36(5), 2020
