# E. coli MLST

## Overview

Multi-Locus Sequence Typing (MLST) for E. coli uses 7 housekeeping genes to characterize isolates. The **E. coli MLST scheme** (Achtman scheme) analyzes:
- **adk** - adenylate kinase
- **fumC** - fumarate hydratase
- **gyrB** - DNA gyrase subunit B
- **icd** - isocitrate dehydrogenase
- **mdh** - malate dehydrogenase
- **purA** - adenylosuccinate synthetase
- **recA** - recombinase A

Each unique allele combination defines a **Sequence Type (ST)**. MLST is used for:
- Phylogenetic analysis and clonal complex (CC) assignment
- Tracking pandemic clones (e.g., ST131, ST11)
- Outbreak investigation (supplementary to SNP/cgMLST)

**Note:** The same E. coli MLST scheme is often used for **Shigella** (same species).

## Selection Strategy

Target **10 test cases** covering:
- **Pandemic ExPEC clones** (3 cases) - ST131, ST95, ST73
- **STEC lineages** (3 cases) - ST11 (O157:H7), ST10, ST58
- **Commensal** (2 cases) - Common environmental/fecal STs
- **Rare/novel STs** (2 cases) - Scheme breadth

## Target STs

### Pandemic ExPEC (Extraintestinal Pathogenic E. coli) - 3 cases

- **ST131** (priority: critical) - Dominant global ExPEC clone, fluoroquinolone-resistant, O25:H4 serotype. Responsible for majority of UTIs, bacteremia.
- **ST95** (priority: high) - Neonatal meningitis, serotype O18:K1:H7. Second most common ExPEC lineage.
- **ST73** (priority: high) - UTI-associated, diverse serotypes. Common in hospital and community infections.

### STEC (Shiga Toxin-Producing E. coli) - 3 cases

- **ST11** (priority: critical) - O157:H7 dominant lineage. Classic STEC outbreak strain.
- **ST21** (priority: high) - O26:H11 associated. Leading non-O157 STEC.
- **ST10** (priority: medium) - Commensal but also found in STEC strains. Very diverse.

### Commensal E. coli - 2 cases

- **ST10** (priority: medium) - Most common commensal ST globally, diverse environments
- **ST69** (priority: medium) - Common in human gut, occasionally ExPEC

### Rare/Novel STs - 2 cases

- **ST1193** (priority: medium) - Emerging ExPEC, single-locus variant (SLV) of ST131 at fumC
- **Novel ST** (priority: low) - ST >1000 or novel alleles for scheme breadth

## Discovery Parameters

### NCBI Search Strategy

**Primary query:**
```
Escherichia coli[Organism] AND <ST>[Attribute]
Escherichia coli[Organism] AND ST131[All Fields]
```

**Metadata extraction:**
- BioSample attributes: `mlst`, `sequence_type`, `ST`
- Publications: "ST131", "MLST sequence type"

**Fallback:**
- Download high-quality E. coli assemblies, run mlst tool to determine ST
- Cross-reference with EnteroBase or other E. coli databases

### Quality Filters

**Require:**
- Assembly available (MLST requires assembly)
- High-quality assembly (N50 > 20kb)

**Prefer:**
- Complete genomes
- ST annotated in metadata (for validation)
- Isolates from clinical or outbreak sources

**Accept:**
- Draft assemblies if good quality
- Unknown ST (will be determined by tool)

**Exclude:**
- Contaminated assemblies
- Poor quality (N50 < 10kb, >500 contigs)
- Shigella (unless explicitly testing E. coli/Shigella MLST shared scheme)

## Ground Truth Schema

```json
"ground_truth": {
  "mlst": {
    "scheme": "ecoli",
    "sequence_type": "string or null - Expected ST (e.g., '131', '11', 'novel')",
    "clonal_complex": "string or null - Optional CC assignment (e.g., 'CC131')",
    "notes": "string or null - Context (e.g., 'SLV of ST131 at fumC')"
  }
}
```

## Validation Logic

### PASS Criteria
- Tool reports ST matching ground truth
- All 7 loci successfully typed
- Scheme correctly identified as `ecoli`

### PARTIAL Criteria
- Single-locus variant (SLV) of expected ST (e.g., ST1193 when expecting ST131)
- Novel alleles detected but ST assigned
- Missing 1 locus due to assembly gap, remaining loci match expected profile

### FAIL Criteria
- Wrong ST (>1 allele difference)
- Failed to type ≥3 loci
- Wrong scheme detected (e.g., `ecoli_2` instead of `ecoli`)

### Known Tool Issues
- **mlst:** Reports `-` if any locus missing; conservative approach
- ST131 has many single-locus variants (ST1193, ST2003) - document relationships
- E. coli MLST scheme is well-established; database completeness is good

## Tool Configurations

### mlst (Torsten Seemann)
```bash
mlst --scheme ecoli data/contigs.fa > actual/mlst/mlst_report.tsv
```

Output format:
```
contigs.fa	ecoli	131	adk(6)	fumC(4)	gyrB(14)	icd(1)	mdh(20)	purA(7)	recA(7)
```

### stringMLST
```bash
stringMLST.py -p -P /path/to/pubmlst/ecoli/profile.txt \
  -k /path/to/pubmlst/ecoli/alleles/ \
  -o actual/stringmlst/ data/contigs.fa
```

## Validation Instructions Template

Example for ST131:
```
Expected ST131, the pandemic ExPEC clone responsible for majority of fluoroquinolone-resistant 
UTIs globally. Tool must use 'ecoli' scheme. All 7 loci must be typed: adk(6), fumC(4), gyrB(14), 
icd(1), mdh(20), purA(7), recA(7). Accept exact ST131 match as PASS. Also accept ST1193 as 
PARTIAL - it is a single-locus variant at fumC, closely related and often grouped with ST131. 
Any other ST is FAIL unless novel alleles are flagged.
```

Example for ST11:
```
Expected ST11, the dominant O157:H7 STEC lineage. Tool must use 'ecoli' scheme. Accept exact 
ST11 match. This ST is associated with O157:H7 serotype - cross-check serotyping results if 
available. Do not accept other STs unless they are documented single-locus variants of ST11 
(rare for this lineage).
```

## Cross-References

- **Serotype**: ST131 typically O25:H4; ST11 typically O157:H7; ST21 typically O26:H11
- **Pathotype**: ST131, ST95, ST73 are ExPEC; ST11, ST21 are STEC
- **Clonal Complex**: ST131 is CC131; ST95 is CC95

## Notes

- E. coli MLST is one of the most extensively curated schemes in PubMLST
- ST131 is a global pandemic clone; its prevalence makes it essential for test suite
- The same scheme is used for Shigella (E. coli and Shigella are the same species)
- Clonal complexes (CC) group related STs; useful for phylogenetic analysis
- Some STs are generalist (ST10) found in diverse environments; others are specialized (ST131 in human UTIs)
- cgMLST and SNP-based methods have higher resolution than MLST for outbreak investigation
