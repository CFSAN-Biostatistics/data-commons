# E. coli Typing Test Cases

Organism-scoped test cases for *Escherichia coli* in-silico typing tools.

## Typing Systems

| System | Tools | Target Cases | Status |
|--------|-------|--------------|--------|
| Serotyping | SerotypeFinder, ECTyper, ShigaTyper | 20 | Planned |
| MLST | mlst, stringMLST | 10 | Planned |

## Target Coverage

### Serotyping
- **Big Six non-O157 STEC** (6 cases): O26:H11, O103:H2, O111:H8, O145:H28, O45:H2, O121:H19
- **O157 STEC** (3 cases): O157:H7, O157:NM, O157:H-
- **Emerging STEC** (3 cases): O26:H-, O111:NM, O104:H4
- **ExPEC serotypes** (3 cases): O25:H4 (ST131), O1:H7, O6:H1
- **Common commensal** (2 cases): O9:H4, ONT:H-
- **Edge cases** (3 cases): Rough strain, novel O:H, multiple H antigens

### MLST
- **Pandemic ExPEC** (3 cases): ST131, ST95, ST73
- **STEC lineages** (3 cases): ST11 (O157:H7), ST21, ST10
- **Commensal** (2 cases): ST10, ST69
- **Rare/novel** (2 cases): ST1193, novel ST

## Example Cases

### Verified (11 cases - 55% complete)

**STEC Serotypes** (Big Six + O157):
- [`examples/ecoli_o157h7_example.json`](examples/ecoli_o157h7_example.json) - O157:H7 (SRR8362622) - FDA-CFSAN strain CFSAN076620
- [`examples/ecoli_o157h7_example.json`](examples/ecoli_o157h7_example.json) - O157:H7 (SRR24226263) - USDA GenomeTrakr RM13485, feral pig isolate
- [`examples/ecoli_o26h11_example.json`](examples/ecoli_o26h11_example.json) - O26:H11 (SRR23097950) - GenomeTrakr RM10843, feral pig
- [`examples/ecoli_o45h2_example.json`](examples/ecoli_o45h2_example.json) - O45:H2 (SRR7608303) - TW18373, human stool
- [`examples/ecoli_o111h8_example.json`](examples/ecoli_o111h8_example.json) - O111:H8 (SRR24226261) - GenomeTrakr RM13483, cattle
- [`examples/ecoli_o121h19_example.json`](examples/ecoli_o121h19_example.json) - O121:H19 (SRR24434721) - GenomeTrakr RM19265, water
- [`examples/ecoli_o145h28_example.json`](examples/ecoli_o145h28_example.json) - O145:H28 (SRR26363320) - GenomeTrakr RM9917, feral pig

**ExPEC (4 cases)**:
- [`examples/ecoli_st131_example.json`](examples/ecoli_st131_example.json) - ST131 O25:H4 (SRR13220449) - Blood isolate 2018
- [`examples/ecoli_o6h1_example.json`](examples/ecoli_o6h1_example.json) - O6:H1 ST73 (SRR7042029) - Canine isolate 1999
- [`examples/ecoli_o1h7_example.json`](examples/ecoli_o1h7_example.json) - O1:H7 ST95 (SRR10257703) - Dog wound 2019
- [`examples/ecoli_o15h18_example.json`](examples/ecoli_o15h18_example.json) - O15:H18 ST69 (SRR6875395) - Dog bite wound 2017

**Emerging STEC**:
- [`examples/ecoli_o104h4_example.json`](examples/ecoli_o104h4_example.json) - O104:H4 ST678 (SRR14771989) - Ground beef 2020 (2011 outbreak type)

## Typing System Documentation

- [`config/typing_systems/ecoli_serotyping.md`](config/typing_systems/ecoli_serotyping.md) - Serotyping strategy and targets
- [`config/typing_systems/mlst.md`](config/typing_systems/mlst.md) - MLST strategy and targets

## Quick Start

```bash
cd ecoli
# Setup (when implemented)
./download.sh --case ecoli_o157h7_SRR1234567
./run.sh --case ecoli_o157h7_SRR1234567 --all-tools
./scripts/validate.py --case ecoli_o157h7_SRR1234567
```

## Dataset Caveats and Limitations

**Current Status:** 11 of 20 target cases (55% complete)

### Known Issues

1. **O103:H2 (SAMN33828130)** - BioSample not accessible in NCBI (HTTP 400). Manifest created but metadata incomplete. May require replacement isolate.

2. **O6:H1 serotype discrepancy** - GenomeTrakr GIMS shows O6:H1, NCBI BioSample shows O119. Manifest flagged with medium confidence. Requires tool verification to resolve.

3. **Expected STs not confirmed** - O1:H7 (expected ST95), O6:H1 (expected ST73), O15:H18 (expected ST69) have predicted sequence types based on serotype associations. Actual STs require mlst tool execution.

### Missing Coverage

- **No commensal strains** - K-12 laboratory reference strains and ST10 commensal not yet included
- **No O157 variants** - O157:NM (non-motile) and O157:H- variants missing
- **No O26/O111 variants** - Non-motile variants (O26:NM, O111:NM) not included
- **Limited human clinical isolates** - Only 1 human isolate (O45:H2 stool); rest are veterinary, food, or animal reservoir

### Data Status

- **Assemblies:** Not yet generated - all cases require local assembly with SPAdes
- **Expected outputs:** `expected/` directories not yet populated - requires running typing tools and validating outputs
- **Tool validation:** Ground truth predictions not yet confirmed by tool execution

### Future Work

Planned additions to reach 20-case minimum:
- K-12 laboratory strains (MG1655, DH5α, BW25113)
- O157 non-motile variants
- ST10 commensal
- Additional MLST diversity (ST21, ST95 confirmed, ST73 confirmed)

## Notes

- E. coli serotyping focuses on clinically/regulatory relevant serotypes (STEC, ExPEC)
- All accessions verified as real *Escherichia coli* from GenomeTrakr GIMS database
- Dataset suitable for serotyping and MLST tool validation despite incomplete coverage
- O157:H7 and "Big Six" non-O157 STEC are FDA/USDA regulated
- ST131 is the pandemic ExPEC clone (fluoroquinolone-resistant UTIs)
- E. coli MLST scheme is also used for Shigella (same species)
