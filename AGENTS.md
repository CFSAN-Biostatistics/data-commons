# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Test data library for bioinformatics tool validation. Provides known input/output pairs for various analysis tools used by the HFP Division of Surveillance & Data Integration.

**Design principles:**
- Small & portable - download via GitHub raw links during testing
- No large source data committed (use references to public databases)
- Known ground truth for typing/validation test cases (`test/typing/`)
- No expected outcome for adversarial challenge cases (`test/challenges/`) — they encode the pathological condition, not the expected tool behavior

## Repository Structure

```
test/
├── challenges/      # Adversarial stimulus library (see below)
├── compression/     # File compression format examples (gz, zst, tar.gz)
├── csp2/            # Submodule from CFSAN-Biostatistics/CSP2_TestData
├── identify/        # Sample accession ID parsing tests
├── reference_selection/  # Assembly collections for reference chooser tools
├── resistance/      # AMR prediction tool test data
├── taxonomy/        # Legacy in-silico serotyping & MLST test data
└── typing/          # Automated typing tool test suite (primary)
```

### Test Data Organization Pattern

Each test category follows:
```
test/<category>/<organism_or_tool>/
├── contigs.fa                    # Assembly input
├── reads.fq.gz                   # Raw read input
├── <tool_name>_report.tsv        # Tool output for validation
└── <ToolName>_result/            # Full tool output directory
    ├── <tool>_result.tsv
    └── <tool>_log.txt
```

Examples:
- `test/taxonomy/salmonella/` - Salmonella Edinburg (7:b:1,5) with SeqSero2 outputs
- `test/resistance/NCTC11351_resfinder/` - Campylobacter jejuni ResFinder outputs (JSON + tables)

## Typing Tool Test Suite (test/typing/)

The `test/typing/` directory contains an automated test case discovery and validation system for in-silico microbial typing tools (MLST, SeqSero2, ShigaTyper, etc.).

### Architecture

**Key principle:** Metadata-driven testing. Large sequence data is NOT committed - only manifests with ground truth and download instructions.

Each test case directory contains:
```
test/typing/sal_typhimurium_SRR14029682/
├── manifest.json          # Ground truth, data sources, tool configs, validation instructions
├── expected/              # Reference tool outputs (committed)
│   ├── seqsero2/
│   └── mlst/
├── data/                  # Downloaded sequence data (gitignored)
│   ├── reads_1.fq.gz
│   ├── reads_2.fq.gz
│   └── contigs.fa
└── actual/                # Fresh tool runs (gitignored)
```

### Manifest Schema

Manifests (`manifest.json`) define:
- **Ground truth** per typing system (serological, MLST, etc.)
- **Curation metadata** (NCBI accessions, confidence scores, evidence sources)
- **Data sources** (SRA/assembly accessions + download commands)
- **Tool configurations** (run commands, expected outputs)
- **Validation instructions** (custom per-case LLM prompts for semantic validation)

See `test/typing/MANIFEST_SCHEMA.md` for complete schema documentation.

### Scripts

Located in `test/typing/`:

- **download.sh** - Downloads sequence data based on manifests. Supports `--all`, `--case`, `--organism` flags.
- **run.sh** - Executes typing tools on test cases. Captures outputs to `actual/` directories.
- **scripts/discover_cases.py** - Discovers new test cases from NCBI using typing system configs. THE CORE VALUE OF THE PROJECT.
- **scripts/validate.py** - LLM-based validation of tool outputs vs ground truth (semantic, not diff-based).
- **scripts/generate_index.py** - Generates `INDEX.md` summary of all test cases.

### Discovery Workflow

Discovery is the "real juice" - automated mining of public data for test case curation:

1. **Define targets** in `config/typing_systems/{system}.md`:
   - 100 Salmonella serotypes (30 common, 50 antigenic diversity, 20 edge cases)
   - 40 MLST cases across multiple organisms
   - Structured markdown with priority annotations

2. **Run discovery**:
   ```bash
   ./scripts/discover_cases.py --config config/typing_systems/salmonella_serological.md
   ```

3. **Discovery script**:
   - Searches NCBI Datasets for assemblies matching serotype metadata
   - Uses Entrez E-utilities to link assemblies to SRA reads
   - Extracts serotype/ST from multiple metadata fields (permissive, handles messy data)
   - Scores candidates by confidence (metadata quality, evidence sources, data availability)
   - Generates draft `manifest.json` files with curation provenance

4. **Manual review**:
   - Edit generated manifests, especially `validation_instructions` field
   - Verify ground truth makes sense
   - Adjust tool configurations as needed

5. **Generate test data**:
   ```bash
   ./download.sh --all          # Download sequence data
   ./run.sh --all               # Run typing tools
   cp actual/* expected/        # Commit expected outputs
   git add */manifest.json */expected/
   ```

### Validation

Validation is **semantic, not diff-based**. An LLM reads:
- Ground truth from manifest
- Tool output (TSV/JSON)
- Custom validation instructions (per test case)

Returns `PASS`, `FAIL`, or `PARTIAL` with reasoning. Example validation instruction:
```
"Typhimurium is the most common serotype. Accept 'Typhimurium' or 
'S. Typhimurium'. Antigenic formula must match 1,4,[5],12:i:1,2. 
Monophasic variant 1,4,[5],12:i:- is PARTIAL (missing H2 phase). 
SeqSero2 may omit brackets around 5 - accept either notation."
```

### Typing Systems

Currently supported:
- **Serological** (Salmonella Kauffmann-White scheme) - 100 targets
- **MLST** (multiple organism schemes) - 40 targets

See `config/typing_systems/*.md` for target lists and rationale.

### Extending with New Typing Systems

See `config/EXPANSION_GUIDE.md` for detailed instructions on adding new typing systems (cgMLST, virulence profiling, AMR, etc.).

### Library Architecture

Discovery script uses modular Python libraries in `scripts/lib/`:
- `ncbi_datasets.py` - Wrapper for NCBI Datasets CLI
- `ncbi_entrez.py` - REST API client for Entrez E-utilities (BioSample/SRA linkage)
- `metadata_parser.py` - Extract serotype/ST from messy NCBI metadata
- `confidence_scorer.py` - Score candidate quality
- `manifest_builder.py` - Generate manifest.json files

## Challenge Dataset Library (test/challenges/)

A **stimulus library** — datasets with characteristics that target known failure modes in major bioinformatics tool categories. Distinct from `test/typing/` in a fundamental way: challenges encode the *pathological condition*, not expected tool behavior. There is no ground truth and no pass/fail assertion. The purpose is to provide adversarial inputs that expose tool assumptions.

**Key design decisions:**
- Phenomenon-first organization: challenges are grouped by biological/technical phenomenon (`contamination/`, `wrong_organism/`, `amr_detection/`, etc.), not by tool
- Each challenge has a `manifest.json` with sample roles, mechanism description, and download instructions — no bulk data committed
- Multi-sample challenges use explicit roles: `reference`, `ingroup`, `outlier`, `contaminant`, `subject`
- Optional `known_behaviors` field documents observed tool behavior — not a pass/fail assertion, just reference information
- Layout templates (`tool_layouts/`) render symlink trees so downloaded data appears in the directory structure each tool family expects
- `acquire.py` handles download and recipe-based synthetic data generation; `layout.py --challenge X --tool Y --out /path` renders a working layout

**Current coverage:** 22 challenges across 10 phenomenon categories:
`amr_detection` (5) · `contamination` (3) · `degenerate_input` (3) · `extreme_gc` (1) · `file_format` (1) · `high_recombination` (1) · `low_coverage` (2) · `platform_mismatch` (1) · `repetitive_genome` (3) · `wrong_organism` (1) · `wrong_reference` (1)

**Tool families supported** (9 layout templates in `tool_layouts/`): `bwa-family`, `snippy-family`, `cfsan-snp-pipeline`, `spades-family`, `seqsero2`, `sistr`, `mlst`, `resfinder-family`, `prokka-family`

**Priority for new challenges:** gene prediction → QC edge cases → population variant analysis (SNP pipeline, assembly, alignment, and AMR detection are well-covered)

See `test/challenges/USAGE.md` for the toolchain reference (acquire/layout commands, tool families, challenge index). See `README.md` for design rationale, `MANIFEST_SCHEMA.md` for the manifest field reference, and `FAILURE_MODES.md` for the research catalog of known failure modes across all tool categories.

## Legacy Test Data (test/taxonomy/, test/resistance/)

Pre-existing test data with committed sequence files. Kept for compatibility but NOT the pattern for new typing tool tests - use `test/typing/` instead.

## Notes

- `test/csp2` is a git submodule - use `git submodule update --init` to populate
- README.md contains GitHub raw link patterns for downloading during CI
- Tool versions matter - include version info in output directories when possible
