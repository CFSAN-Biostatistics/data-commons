# Listeria monocytogenes Typing Test Cases

Organism-scoped test cases for *Listeria monocytogenes* in-silico typing tools.

## Typing Systems

| System | Tools | Target Cases | Status |
|--------|-------|--------------|--------|
| Serotyping | LisSero, SISTR | 12 | Planned |
| MLST | mlst, stringMLST | 8 | Planned |

## Target Coverage

### Serotyping
- **Serotype 4b (Lineage I)** (4 cases): Epidemic clone (ST2), ST6, hypervirulent (ST1), rare ST
- **Serotype 1/2a (Lineage II)** (3 cases): ST5, ST121 (hypervirulent), ST8
- **Serotype 1/2b (Lineage I)** (2 cases): ST5, rare ST
- **Serotype 1/2c (Lineage II)** (1 case): Standard
- **Rare serotypes** (1 case): 4a or 4c
- **Edge case** (1 case): L. ivanovii or L. innocua (non-monocytogenes)

### MLST
- **Lineage I** (4 cases): ST2 (4b), ST1 (1/2b), ST6 (4b), ST4 (4b)
- **Lineage II** (3 cases): ST5 (1/2a), ST121 (1/2a hypervirulent), ST8 (1/2a)
- **Rare lineages** (1 case): Lineage III/IV

## Example Cases

- [`examples/listeria_4b_example.json`](examples/listeria_4b_example.json) - Serotype 4b ST2 (epidemic clone)
- [`examples/listeria_1-2a_example.json`](examples/listeria_1-2a_example.json) - Serotype 1/2a ST5 (persistent)

## Typing System Documentation

- [`config/typing_systems/listeria_serotyping.md`](config/typing_systems/listeria_serotyping.md) - Serotyping strategy and targets
- [`config/typing_systems/mlst.md`](config/typing_systems/mlst.md) - MLST strategy and targets

## Quick Start

```bash
cd listeria
# Setup (when implemented)
./download.sh --case lis_4b_SRR5678901
./run.sh --case lis_4b_SRR5678901 --all-tools
./scripts/validate.py --case lis_4b_SRR5678901
```

## Notes

- Three serotypes (1/2a, 1/2b, 4b) account for >95% of human listeriosis
- Serotype 4b is overrepresented in outbreaks (most virulent)
- ST2 (4b) is the major epidemic clone (2011 cantaloupe, 2015 ice cream outbreaks)
- ST5 (1/2a) is common in food processing environments (persistence)
- ST121 (1/2a) is a hypervirulent Lineage II strain (carries LIPI-3, LIPI-4)
- Lineage I (1/2b, 4b) is more virulent; Lineage II (1/2a, 1/2c) is more environmental
- cgMLST preferred for outbreak investigation; MLST for clonal complex assignment
