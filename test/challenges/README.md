# Challenge Dataset Library

A **stimulus library** for bioinformatics tool validation. Each challenge is a curated public dataset with characteristics that target known failure modes in major tool categories.

## Concept

Standard bioinformatics tools are developed and validated against datasets the authors already have — which means they are implicitly optimized for success on well-behaved data. Real surveillance and diagnostic workflows encounter data that is messy, contaminated, degenerate, or structurally unusual in ways that trigger silent wrong outputs, cryptic crashes, or misleading statistics.

This library captures those conditions. The goal is not to assert that a tool *will* fail — some tools handle these conditions gracefully — but to provide the stimulus that *would* trigger a failure if the tool's assumptions are violated.

**This is a stimulus library, not a test suite.** Challenges encode the pathological condition, not expected tool behavior.

## Difference from `test/typing/`

| | `test/typing/` | `test/challenges/` |
|---|---|---|
| Purpose | Validate tool correctness on known-good inputs | Stress-test tool assumptions with adversarial inputs |
| Ground truth | Committed (known serotype, known ST) | None — no expected output |
| Data | Downloaded on demand | Downloaded on demand |
| Manifests | Encode ground truth + validation instructions | Encode challenge description + sample roles |
| Use case | Regression testing, CI validation | Tool development, robustness auditing |

## Directory Structure

```
test/challenges/
├── README.md                    # This file
├── MANIFEST_SCHEMA.md           # Manifest field reference
├── FAILURE_MODES.md             # Research catalog of known failure modes
├── INDEX.md                     # Auto-generated challenge catalog
├── acquire.py                   # Download sequence data from manifests
├── layout.py                    # Render tool-family symlink layouts
├── tool_layouts/                # Tool-family layout templates
│   ├── snippy-family.json
│   ├── cfsan-snp-pipeline.json
│   └── ...
└── {phenomenon}/
    └── {challenge_instance}/
        ├── manifest.json        # Challenge definition (committed)
        └── data/                # Downloaded sequence data (gitignored)
            └── {sample_id}/
                ├── reads_1.fq.gz
                ├── reads_2.fq.gz
                └── assembly.fasta
```

## Phenomenon Categories

Challenges are organized by biological or technical phenomenon (not by tool). The same dataset may challenge multiple tool families simultaneously.

Current categories (expand as needed):
- `wrong_organism/` — samples submitted to tools expecting a different organism
- `contamination/` — mixed-organism samples, sample swaps
- `degenerate_input/` — empty files, all-N sequences, zero reads
- `low_coverage/` — insufficient depth to support tool assumptions
- `extreme_gc/` — GC content outside tool training distribution
- `repetitive_genome/` — IS elements, tandem repeats, rRNA operons
- `mixed_population/` — multiple strains, lineages, or STs in one sample
- `wrong_reference/` — reference genome from wrong lineage or organism
- `fragmented_assembly/` — high contig count, low N50
- `platform_mismatch/` — data from wrong sequencing platform for tool
- `file_format/` — edge cases in FASTQ/FASTA format

## Supported Tool Families

Challenges tag which tool families they target. Layout templates exist for:

- `snippy-family` — snippy, snippy-core, lyve-SET
- `cfsan-snp-pipeline` — CFSAN-SNP-Pipeline
- `seqsero2` — SeqSero2
- `sistr` — SISTR
- `mlst` — mlst (tseemann)
- `spades-family` — SPAdes, Unicycler
- `bwa-family` — BWA-MEM, BWA-MEM2
- `prokka-family` — Prokka, Bakta
- `resfinder-family` — ResFinder, AMRFinderPlus, abricate

## Workflow

### Downloading challenge data

```bash
# Download all challenges
python acquire.py --all

# Download one challenge
python acquire.py --challenge wrong_organism/ecoli_to_seqsero2

# Download all challenges in a phenomenon category
python acquire.py --phenomenon contamination
```

### Running a tool against a challenge

```bash
# Render a tool-family layout into a working directory
python layout.py \
  --challenge wrong_organism/ecoli_to_seqsero2 \
  --tool seqsero2 \
  --out /tmp/my_run

# Then invoke the tool against the layout
seqsero2 -m k -i /tmp/my_run/assembly.fasta
```

### Adding a new challenge

1. Identify the phenomenon and find a public SRA or assembly accession that exhibits it
2. Create the directory: `{phenomenon}/{descriptive_instance_name}/`
3. Write `manifest.json` following `MANIFEST_SCHEMA.md`
4. Verify download works: `python acquire.py --challenge {phenomenon}/{instance}`
5. Update `INDEX.md`: `python scripts/generate_index.py`
6. Commit only the manifest: `git add {phenomenon}/{instance}/manifest.json`

## Priority Order for Challenge Curation

1. **In-silico typing & SNP pipelines** — highest clinical impact; silent wrong outputs in surveillance context
2. **Assembly** — foundational; assembly errors propagate to all downstream tools
3. **Alignment** — upstream dependency; failures are often diagnosable but worth documenting

See `FAILURE_MODES.md` for the full research catalog of known failure modes by tool category.
