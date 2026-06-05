# Campylobacter AMR Tool Test Suite

Test cases for verification and benchmarking of antimicrobial resistance (AMR) detection tools on *Campylobacter jejuni* assemblies.

## Quick Start

```bash
# Run ResFinder on both cases (assemblies already present)
./run.sh --all --tool ResFinder

# Validate results
./scripts/validate.py --case campy_jejuni_amp_tet_UCLA1626

# Dry-run all tools on all cases
./run.sh --all --dry-run
```

## Structure

Each test case directory contains:

```
campy_jejuni_amp_tet_UCLA1626/
├── manifest.json          # Ground truth, data sources, tool commands, validation instructions
├── expected/              # Reference tool outputs (committed to repo)
│   └── resfinder/
├── data/                  # Sequence data (pre-loaded for existing cases)
│   └── contigs.fa
└── actual/                # Fresh tool execution outputs (gitignored)
    ├── resfinder/
    ├── amrfinderplus/
    ├── card_rgi/
    └── abricate/
```

## Case Categories

| Category | Description | Expected Tool Behavior |
|----------|-------------|----------------------|
| `susceptible_control` | No resistance genes | All tools: no hits. Any hit = false positive |
| `single_resistance` | One drug class | Tools detect that class; others negative |
| `multi_resistance` | 2 drug classes | Tools detect both classes |
| `mdr` | 3+ drug classes | Tools detect all classes |
| `edge_case` | Truncated gene, novel variant, borderline threshold | Tests tool robustness |

## Supported Tools

| Tool | Input | Output | Config |
|------|-------|--------|--------|
| ResFinder | assembly | JSON | `config/amr_systems/resfinder.md` |
| AMRFinderPlus | assembly | TSV | `config/amr_systems/amrfinderplus.md` |
| CARD RGI | assembly | JSON+TSV | `config/amr_systems/card_rgi.md` |
| abricate | assembly | TSV | `config/amr_systems/abricate.md` |

## Scripts

- `download.sh` — Fetches sequence data from NCBI based on manifest
- `run.sh` — Executes AMR tools on test cases
- `scripts/validate.py` — LLM-based validation of tool outputs against ground truth
- `scripts/discover_cases.py` — Discovers and generates new cases from NCBI
- `scripts/generate_index.py` — Regenerates INDEX.md

## Adding Test Cases

See `config/amr_systems/resfinder.md` for target lists and rationale.

Run discovery:
```bash
./scripts/discover_cases.py --config config/amr_systems/resfinder.md
```

This generates manifest.json stubs for manual review. Review and populate ground truth, then run tools to generate expected outputs:
```bash
./run.sh --case <new_case> --all-tools
cp -r <new_case>/actual/<tool>/ <new_case>/expected/<tool>/
```

## Extending to New AMR Tools

See `config/EXPANSION_GUIDE.md` for instructions on adding new AMR detection tools.
