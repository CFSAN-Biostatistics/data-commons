# AMR Detection Tool Test Suite

Organism-scoped test cases for verification and benchmarking of antimicrobial resistance (AMR) detection tools. Each organism directory is self-contained with its own cases, scripts, and configuration.

## Organisms

| Directory | Species | Cases | AMR Tools | Status |
|-----------|---------|-------|-----------|--------|
| [campylobacter/](campylobacter/) | *Campylobacter jejuni* | 2 | ResFinder, AMRFinderPlus, CARD RGI, abricate | active |
| [salmonella/](salmonella/) | *Salmonella enterica* | — | planned | stub |
| [ecoli/](ecoli/) | *Escherichia coli* | — | planned | stub |
| [listeria/](listeria/) | *Listeria monocytogenes* | — | planned | stub |

## Structure

Each organism directory follows the same layout:

```
<organism>/
├── <prefix>_<species>_<amrprofile>_<strain_or_SRR>/   # test cases
│   ├── manifest.json          # ground truth, tool commands, validation instructions
│   ├── expected/              # reference outputs (committed)
│   │   ├── resfinder/
│   │   ├── amrfinderplus/
│   │   ├── card_rgi/
│   │   └── abricate/
│   ├── data/                  # sequence data (gitignored or pre-loaded)
│   │   └── contigs.fa
│   └── actual/                # fresh tool outputs (gitignored)
├── config/
│   ├── amr_systems/           # tool docs and target lists
│   └── EXPANSION_GUIDE.md
├── scripts/
│   ├── validate.py
│   ├── discover_cases.py
│   ├── generate_index.py
│   └── lib/
│       ├── output_parsers.py  # ResFinder JSON, AMRFinder TSV, CARD JSON, abricate TSV
│       └── __init__.py
├── examples/
├── download.sh
├── run.sh
├── INDEX.md
├── README.md
└── MANIFEST_SCHEMA.md
```

## Case Naming Convention

`<orgcode>_<species>_<amrprofile>_<strain_or_SRR>/`

AMR profile tokens: `sus` (susceptible), `amp` (beta-lactam), `tet` (tetracycline), `cip` (fluoroquinolone), `gen` (aminoglycoside), `col` (colistin), `mdr` (3+ classes), `novel_var`, `truncated`

## Quick Start

```bash
# Campylobacter — run existing cases
cd campylobacter
./run.sh --all --dry-run          # preview commands
./run.sh --all --tool ResFinder   # run ResFinder on all cases
./scripts/validate.py --case campy_jejuni_amp_tet_UCLA1626
```

## Adding a New Organism

1. `mkdir -p <organism>/{config/amr_systems,scripts/lib,examples}`
2. Copy `campylobacter/download.sh` and `campylobacter/run.sh`; update the `campy_*` glob to the new prefix
3. Create `config/amr_systems/<tool>.md` following `campylobacter/config/EXPANSION_GUIDE.md`
4. Run discovery: `scripts/discover_cases.py --config config/amr_systems/<tool>.md`
5. Add row to the table above
