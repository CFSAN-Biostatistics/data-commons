# Campylobacter AMR Test Case Index

**Generated:** 2026-06-05
**Total Cases:** 2
**Organisms:** 1 (Campylobacter jejuni)
**Tools Configured:** ResFinder, AMRFinderPlus, CARD RGI, abricate

## Statistics

- Cases with assemblies: 2 (100%)
- Cases with reads: 0 (0%)
- Susceptible controls: 1
- Resistance profiles: 1 (AMP_TET)

## Test Cases

### Susceptible Controls (1)

- **campy_jejuni_sus_NCTC11351** — Strain: NCTC11351, AMR: susceptible [confidence: high]

### Multi-Drug Resistance (1)

- **campy_jejuni_amp_tet_UCLA1626** — Strain: UCLA_1626, AMR: AMP_TET (blaOXA×7, tet(O)) [confidence: high]

---

## Legend

- **[confidence: X]** — Ground truth confidence (high/medium/low/bootstrapped)
- AMR profile tokens: `sus`=susceptible, `amp`=beta-lactam, `tet`=tetracycline, `cip`=fluoroquinolone, `mdr`=3+ classes

## Usage

```bash
# Download data (assemblies already present for existing cases)
./download.sh --all

# Run all tools on all cases (dry-run first)
./run.sh --all --dry-run
./run.sh --all

# Validate specific case
./scripts/validate.py --case campy_jejuni_amp_tet_UCLA1626

# Validate with markdown output
./scripts/validate.py --case campy_jejuni_amp_tet_UCLA1626 --output-format markdown
```

See `README.md` for full usage instructions.
