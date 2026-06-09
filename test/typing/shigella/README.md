# Shigella Typing Test Cases

Organism-scoped test cases for *Shigella* spp. in-silico typing tools.

## Typing Systems

| System | Tools | Target Cases | Status |
|--------|-------|--------------|--------|
| Species/Serotyping | ShigaTyper, ipaH detection | 15 | Planned |
| MLST | mlst (ecoli scheme) | 6 | Planned |

## Target Coverage

### Species and Serotyping
- **S. sonnei** (4 cases): Standard, MDR, MSM-associated, travel-associated
- **S. flexneri** (6 cases): 2a, 3a, 6, 1b, 2b, X variant
- **S. dysenteriae** (2 cases): Type 1 (Sd1), Type 2
- **S. boydii** (2 cases): Serotype 1, Serotype 14
- **Edge cases** (1 case): EIEC (E. coli/Shigella boundary)

### MLST
- **S. sonnei** (2 cases): ST152 (dominant), rare ST
- **S. flexneri** (3 cases): ST245, ST147, novel/rare ST
- **S. dysenteriae** (1 case): ST148

## Example Cases

- [`examples/shigella_sonnei_example.json`](examples/shigella_sonnei_example.json) - S. sonnei ST152 (clonal)
- [`examples/shigella_flexneri_example.json`](examples/shigella_flexneri_example.json) - S. flexneri 2a ST245

## Typing System Documentation

- [`config/typing_systems/shigella_serotyping.md`](config/typing_systems/shigella_serotyping.md) - Serotyping and species ID strategy
- [`config/typing_systems/mlst.md`](config/typing_systems/mlst.md) - MLST strategy (uses E. coli scheme)

## Quick Start

```bash
cd shigella
# Setup (when implemented)
./download.sh --case shi_sonnei_SRR3456789
./run.sh --case shi_sonnei_SRR3456789 --all-tools
./scripts/validate.py --case shi_sonnei_SRR3456789
```

## Notes

- Shigella is genetically E. coli; distinguished by **ipaH gene** presence
- S. sonnei is highly clonal (>90% are ST152)
- S. flexneri is phylogenetically diverse (many serotypes and STs)
- S. dysenteriae type 1 (Sd1) produces Shiga toxin (stx gene)
- MLST uses E. coli scheme (Shigella = E. coli at species level)
- ipaH detection is critical for Shigella vs EIEC distinction
