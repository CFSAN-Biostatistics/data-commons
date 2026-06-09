# Typing Manifest Summary

Created: 2026-06-08

## Overview

This document summarizes the typing manifests developed for E. coli, Shigella, Listeria monocytogenes, and a pan-genus MLST manifest.

## Created Manifests

### 1. E. coli Typing Manifest

**Location:** `test/typing/ecoli/`

**Typing Systems:**
- **Serotyping** (20 target cases)
  - Tools: SerotypeFinder, ECTyper, ShigaTyper
  - Focus: STEC serotypes (O157:H7, Big Six), ExPEC serotypes (O25:H4), commensal types
  - Key targets: O157:H7, O26:H11, O103:H2, O145:H28, O25:H4 (ST131), O121:H19, O45:H2
  
- **MLST** (10 target cases)
  - Tools: mlst, stringMLST
  - Scheme: `ecoli` (7 loci: adk, fumC, gyrB, icd, mdh, purA, recA)
  - Key targets: ST131 (pandemic ExPEC), ST11 (O157:H7), ST95, ST73, ST21

**Documentation:**
- `config/typing_systems/ecoli_serotyping.md` - Comprehensive serotyping strategy
- `config/typing_systems/mlst.md` - MLST targets and validation logic
- `config/EXPANSION_GUIDE.md` - How to add new typing systems
- `README.md` - Quick reference and setup instructions

**Examples:**
- `examples/ecoli_o157h7_example.json` - O157:H7 STEC (ST11)
- `examples/ecoli_st131_example.json` - Pandemic ExPEC O25:H4 (ST131)

---

### 2. Shigella Typing Manifest

**Location:** `test/typing/shigella/`

**Typing Systems:**
- **Species Identification & Serotyping** (15 target cases)
  - Tools: ShigaTyper, ipaH detection (BLAST)
  - Focus: Species confirmation (ipaH gene), serotype assignment
  - Key targets: S. sonnei (clonal), S. flexneri 2a/3a/6, S. dysenteriae type 1 (Sd1), S. boydii
  
- **MLST** (6 target cases)
  - Tools: mlst, stringMLST
  - Scheme: `ecoli` (Shigella uses E. coli MLST scheme)
  - Key targets: ST152 (S. sonnei dominant), ST245 (S. flexneri), ST147, ST148 (Sd1)

**Documentation:**
- `config/typing_systems/shigella_serotyping.md` - Serotyping and ipaH detection strategy
- `config/typing_systems/mlst.md` - MLST strategy using E. coli scheme
- `config/EXPANSION_GUIDE.md` - How to add new typing systems
- `README.md` - Quick reference and setup instructions

**Examples:**
- `examples/shigella_sonnei_example.json` - S. sonnei ST152 (clonal)
- `examples/shigella_flexneri_example.json` - S. flexneri 2a ST245

**Key Notes:**
- Shigella is genetically E. coli; distinguished by **ipaH gene** presence
- S. sonnei is highly clonal (>90% are ST152)
- S. flexneri is phylogenetically diverse

---

### 3. Listeria monocytogenes Typing Manifest

**Location:** `test/typing/listeria/`

**Typing Systems:**
- **Serotyping** (12 target cases)
  - Tools: LisSero, SISTR
  - Focus: Major serotypes (1/2a, 1/2b, 4b) and lineage assignment
  - Key targets: 4b (epidemic clone), 1/2a (persistent), 1/2b (clinical), 1/2c
  
- **MLST** (8 target cases)
  - Tools: mlst, stringMLST
  - Scheme: `lmonocytogenes` (7 loci: abcZ, bglA, cat, dapE, dat, ldh, lhkA)
  - Key targets: ST2 (4b epidemic), ST1 (1/2b hypervirulent), ST5 (1/2a persistent), ST6 (4b), ST121 (1/2a hypervirulent)

**Documentation:**
- `config/typing_systems/listeria_serotyping.md` - Serotyping strategy and lineage correlation
- `config/typing_systems/mlst.md` - MLST targets and clonal complex assignment
- `config/EXPANSION_GUIDE.md` - How to add new typing systems
- `README.md` - Quick reference and setup instructions

**Examples:**
- `examples/listeria_4b_example.json` - Serotype 4b ST2 (epidemic clone)
- `examples/listeria_1-2a_example.json` - Serotype 1/2a ST5 (persistent)

**Key Notes:**
- Three serotypes (1/2a, 1/2b, 4b) account for >95% of human listeriosis
- Serotype 4b is most outbreak-associated (highly virulent, Lineage I)
- ST2 is the major epidemic clone (2011 cantaloupe, 2015 ice cream outbreaks)

---

### 4. Pan-Genus MLST Manifest

**Location:** `test/typing/mlst_pan_genus.md`

**Purpose:** Cross-organism MLST tool validation (tool-focused, not organism-focused)

**Coverage:** 50 target cases across 11 organisms
- Salmonella enterica (10 cases) - `senterica` scheme
- Escherichia coli / Shigella (10 cases) - `ecoli` scheme
- Listeria monocytogenes (8 cases) - `lmonocytogenes` scheme
- Campylobacter jejuni (5 cases) - `cjejuni` scheme
- Klebsiella pneumoniae (4 cases) - `kpneumoniae` scheme
- Cronobacter sakazakii (3 cases) - `cronobacter` scheme
- Staphylococcus aureus (3 cases) - `saureus` scheme
- Enterococcus faecium (2 cases) - `efaecium` scheme
- Vibrio parahaemolyticus (2 cases) - `vparahaemolyticus` scheme
- Bacillus cereus (2 cases) - `bcereus` scheme
- Yersinia enterocolitica (1 case) - `yenterocolitica` scheme

**Target Focus:**
- **Common STs** (70% of cases) - Dominant clones, positive controls
- **Rare/novel STs** (20% of cases) - Scheme breadth, novel allele detection
- **Edge cases** (10% of cases) - Poor assemblies, incomplete loci, scheme ambiguity

**Use Cases:**
1. Tool installation validation (mlst, stringMLST)
2. Scheme coverage testing
3. Benchmark across tools
4. Assembly quality impact assessment

**Key Notes:**
- Organism-agnostic: focuses on MLST tool validation, not organism-specific biology
- Cross-references organism-specific manifests for biological context
- Tests multiple MLST schemes (7-8 loci each)
- Validates scheme auto-detection and manual specification

---

## Manifest Structure

All organism-specific manifests follow this structure:

```
<organism>/
├── config/
│   ├── typing_systems/
│   │   ├── <organism>_serotyping.md    # Serotyping strategy
│   │   └── mlst.md                      # MLST strategy
│   └── EXPANSION_GUIDE.md               # How to add typing systems
├── examples/
│   └── <organism>_<type>_example.json   # Example manifest files
└── README.md                             # Organism overview
```

## Manifest Schema

Each manifest JSON includes:

```json
{
  "organism": "string - Full organism name",
  "curation": {
    "date": "YYYY-MM-DD",
    "ncbi_accessions": {...},
    "metadata_confidence": "high|medium|low",
    "serotype_evidence": [...],
    "st_evidence": [...],
    "quality_metrics": {...}
  },
  "ground_truth": {
    "serological": {...},        // For serotyping
    "mlst": {...},                // For MLST
    "species_confirmation": {...} // For Shigella (ipaH)
  },
  "data_sources": {
    "reads": {...},
    "assembly": {...}
  },
  "tools": {
    "ToolName": {
      "input_type": "reads|assembly",
      "run_cmd": "string - Command to run tool",
      "reference_output": "string - Path to expected output"
    }
  },
  "validation_instructions": {
    "serological": "string - Validation criteria",
    "mlst": "string - Validation criteria"
  },
  "difficulty": "common|challenging|edge_case"
}
```

## Total Target Case Counts

| Organism | Serotyping | MLST | Total |
|----------|------------|------|-------|
| E. coli | 20 | 10 | 30 |
| Shigella | 15 | 6 | 21 |
| Listeria | 12 | 8 | 20 |
| **Pan-genus MLST** | — | **50** | **50** |
| **Total** | **47** | **74** | **121** |

Note: Pan-genus MLST cases overlap with organism-specific MLST cases (same isolates, tool-focused vs organism-focused validation).

## Key Features

### 1. Comprehensive Target Selection
- Clinically/regulatory relevant serotypes (FDA/USDA regulated STEC, outbreak-associated Listeria)
- Pandemic clones (E. coli ST131, Listeria ST2)
- High-diversity organisms (S. flexneri) and clonal organisms (S. sonnei, Listeria 4b)

### 2. Tool Coverage
- **Serotyping:** SerotypeFinder, ECTyper, ShigaTyper, LisSero, SISTR
- **MLST:** mlst (Torsten Seemann), stringMLST
- **Species confirmation:** ipaH detection (BLAST)

### 3. Validation Logic
- PASS/PARTIAL/FAIL criteria for each typing system
- Known tool issues documented
- Cross-references between serotype and ST (e.g., O157:H7 = ST11, O25:H4 = ST131, 4b = ST2)

### 4. Discovery Parameters
- NCBI search strategies (BioSample queries, metadata extraction)
- Quality filters (assembly quality, metadata confidence)
- Fallback strategies for rare types

### 5. Edge Cases
- Non-motile variants (H-, NM)
- Species boundaries (Shigella vs EIEC, Listeria monocytogenes vs other Listeria spp.)
- Novel alleles and rare STs
- Poor assembly quality impact

## Next Steps

To implement these manifests:

1. **Discover cases:** Use NCBI queries and discovery scripts to find target isolates
2. **Download data:** Use provided download commands for reads and assemblies
3. **Run tools:** Execute typing tools with provided commands
4. **Validate:** Compare tool outputs against ground truth using validation instructions
5. **Iterate:** Add cases as needed, update manifests based on tool performance

## Cross-References

- Parent directory: `test/typing/README.md` - Overall typing test suite structure
- Salmonella manifest: `test/typing/salmonella/` - Reference implementation (111 cases)
- EXPANSION_GUIDE.md in each organism directory - How to add new typing systems

## Contact

For questions or contributions, see the main repository README.
