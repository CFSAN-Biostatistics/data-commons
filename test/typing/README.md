# Microbial Typing Tool Test Suite

Organism-scoped test cases for in-silico typing tools. Each organism directory is self-contained with its own cases, scripts, and configuration.

## Organisms

| Directory | Species | Cases | Typing Systems |
|-----------|---------|-------|----------------|
| [salmonella/](salmonella/) | *Salmonella enterica* | 111 | SeqSero2, MLST |
| [ecoli/](ecoli/) | *Escherichia coli* | — | planned |
| [shigella/](shigella/) | *Shigella* spp. | — | planned |
| [listeria/](listeria/) | *Listeria monocytogenes* | — | planned |
| [bcereus/](bcereus/) | *Bacillus cereus* group | — | planned |
| [streptococcus/](streptococcus/) | *Streptococcus* spp. | — | planned |
| [klebsiella/](klebsiella/) | *Klebsiella pneumoniae* | — | planned |
| [cronobacter/](cronobacter/) | *Cronobacter* spp. | — | planned |

## Structure

Each organism directory follows the same layout:

```
<organism>/
├── <prefix>_<type>_<SRR>/    # test cases (gitignored data/, actual/)
│   ├── manifest.json
│   ├── expected/
│   ├── data/                 # gitignored
│   └── actual/               # gitignored
├── config/
│   ├── typing_systems/       # system docs and target lists
│   └── EXPANSION_GUIDE.md
├── scripts/
│   ├── discover_cases.py
│   ├── generate_index.py
│   ├── validate.py
│   └── lib/
├── examples/
├── download.sh
├── run.sh
├── INDEX.md
└── README.md
```

## Quick Start

```bash
# Salmonella
cd salmonella
./download.sh --case sal_typhimurium_SRR2124515
./run.sh --case sal_typhimurium_SRR2124515 --all-tools
./scripts/validate.py --case sal_typhimurium_SRR2124515
```

## Adding a New Organism

1. `mkdir -p <organism>/{config/typing_systems,scripts/lib,examples}`
2. Copy `salmonella/download.sh` and `salmonella/run.sh`; update the `sal_*` glob to the new prefix
3. Create `config/typing_systems/<system>.md` following `salmonella/config/EXPANSION_GUIDE.md`
4. Run discovery: `scripts/discover_cases.py --config config/typing_systems/<system>.md`
5. Add row to the table above
