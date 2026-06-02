# HFP Data Commons — Test Data Library

Shared test data for the HFP Division of Surveillance & Data Integration. Provides known inputs and outputs for validating bioinformatics workflows used in microbial surveillance.

No need to clone the whole repository — individual files can be fetched directly during CI using GitHub raw links:

```
https://raw.githubusercontent.com/CFSAN-Biostatistics/data-commons/main/test/PATH/TO/FILE
```

Large sequence data is not committed. Each test section provides manifests and scripts to download data from public sources (NCBI SRA, NCBI Assembly) on demand.

---

## Contents

### test/typing/ — Automated Typing Tool Test Suite

Metadata-driven test cases for in-silico microbial typing tools (SeqSero2, SISTR, MLST, ShigaTyper, etc.). Each case provides a `manifest.json` with ground truth, NCBI accessions, download instructions, and per-case LLM validation prompts. Sequence data is gitignored and downloaded locally.

- `download.sh` — fetch sequence data from SRA/Assembly
- `run.sh` — execute typing tools and capture outputs
- `scripts/discover_cases.py` — automated NCBI mining for new test cases (the core of the project)
- `scripts/validate.py` — semantic LLM-based validation (not diff-based)

Currently: 100 Salmonella serotype targets, 40 MLST targets across multiple organisms.

### test/challenges/ — Adversarial Stimulus Library

Datasets engineered to trigger known failure modes in major bioinformatics tool categories. A stimulus library, not a test suite — challenges encode the pathological condition, not the expected tool behavior. No pass/fail assertion.

22 challenges across 10 phenomenon categories: `amr_detection`, `contamination`, `degenerate_input`, `extreme_gc`, `file_format`, `high_recombination`, `low_coverage`, `platform_mismatch`, `repetitive_genome`, `wrong_organism`, `wrong_reference`.

- `acquire.py` — download or generate challenge data
- `layout.py` — render symlink trees for 9 supported tool families
- `USAGE.md` — toolchain reference
- `AGENTS.md` — guide for AI agents running challenges against tools
- `FAILURE_MODES.md` — catalog of ~150 known tool failure modes

### test/resistance/ — Legacy AMR Test Data

Committed assemblies and ResFinder outputs for two *Campylobacter jejuni* strains (NCTC11351, UCLA_1626). Kept for compatibility; new AMR test cases belong in `test/challenges/amr_detection/`.

### test/taxonomy/ — Legacy Typing Test Data

Committed assemblies with SeqSero2 outputs for a small set of *Salmonella* serotypes. Kept for compatibility; new typing test cases belong in `test/typing/`.

### test/compression/ — Compression Format Examples

A high-entropy file compressed in several formats, for testing decompression handling:

```
test/compression/example.raw        # source
test/compression/example.gz
test/compression/example.tar.gz
test/compression/example.1.zst      # ZSTD level 1
test/compression/example.8.zst      # ZSTD level 8
test/compression/example.15.zst     # ZSTD level 15
```

### test/csp2/ — CSP2 Test Data (submodule)

Submodule from [CFSAN-Biostatistics/CSP2_TestData](https://github.com/CFSAN-Biostatistics/CSP2_TestData). Populate with:

```bash
git submodule update --init
```

### test/identify/ — Accession ID Parsing

Test data for tools that parse sample accessions from FASTA/FASTQ headers.

### test/reference_selection/ — Assembly Collections

Assembly collections for testing reference selection tools (e.g., refchooser).
