# Microbial Typing Tool Test Suite

Automated test case discovery and validation for in-silico typing tools.

## Quick Start

```bash
# Download test data for a specific case
./download.sh --case sal_typhimurium_SRR14029682

# Run typing tools on the case
./run.sh --case sal_typhimurium_SRR14029682 --all-tools

# Validate results
./scripts/validate.py --case sal_typhimurium_SRR14029682
```

## Structure

Each test case directory contains:

```
sal_typhimurium_SRR14029682/
├── manifest.json          # Ground truth, data sources, tool commands, validation instructions
├── expected/              # Reference tool outputs (committed to repo)
│   ├── seqsero2/
│   └── mlst/
├── data/                  # Downloaded sequence data (gitignored, fetch on-demand)
│   ├── reads_1.fq.gz
│   ├── reads_2.fq.gz
│   └── contigs.fa
└── actual/                # Fresh tool execution outputs (gitignored)
    ├── seqsero2/
    └── mlst/
```

## Scripts

- `download.sh` - Fetches sequence data from NCBI based on manifest
- `run.sh` - Executes typing tools on test cases
- `scripts/validate.py` - LLM-based validation of tool outputs
- `scripts/discover_cases.py` - Discovers and generates new test cases from NCBI
- `scripts/generate_index.py` - Generates INDEX.md summary

## Adding Test Cases

See `config/typing_systems/*.md` for target lists and rationale.

Run discovery:
```bash
./scripts/discover_cases.py --config config/typing_systems/salmonella_serological.md
```

This generates manifest.json files in test case directories. Review and edit manifests (especially `validation_instructions`), then download data and run tools to generate expected outputs.

## Extending to New Typing Systems

See `config/EXPANSION_GUIDE.md` for instructions on adding new typing systems beyond serological and MLST.

## Examples

See `examples/` directory for complete example manifests with detailed annotations.
