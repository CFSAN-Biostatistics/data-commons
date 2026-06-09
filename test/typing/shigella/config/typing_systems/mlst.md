# Shigella MLST

## Overview

Shigella is genetically E. coli (same species). MLST for Shigella can use:
1. **E. coli MLST scheme (Achtman)** - Most common, same 7 loci as E. coli (adk, fumC, gyrB, icd, mdh, purA, recA)
2. **Shigella-specific scheme** - Rare, some labs use modified scheme

Most laboratories and databases (EnteroBase, PubMLST) use the **E. coli scheme** for Shigella.

MLST is used for:
- Phylogenetic analysis (S. sonnei is clonal; S. flexneri is diverse)
- Clonal complex assignment
- Tracking international spread (especially MDR S. sonnei)

## Selection Strategy

Target **6 test cases** covering:
- **S. sonnei** (2 cases) - Clonal, mostly ST152
- **S. flexneri** (3 cases) - Diverse STs across serotypes
- **S. dysenteriae** (1 case) - Rare, distinct lineage

## Target STs

### S. sonnei - 2 cases

- **ST152** (priority: critical) - Dominant S. sonnei ST globally, highly clonal. >90% of S. sonnei isolates are ST152.
- **Rare S. sonnei ST** (priority: low) - Occasional variants (ST146, ST147) for scheme breadth

### S. flexneri - 3 cases

- **ST245** (priority: high) - Common S. flexneri ST, serotype 2a often associated
- **ST147** (priority: high) - S. flexneri lineage, diverse serotypes
- **Novel/rare ST** (priority: medium) - S. flexneri has many STs; select uncommon for coverage

### S. dysenteriae - 1 case

- **ST148** (priority: medium) - S. dysenteriae type 1 (Sd1) often associated with ST148 or related STs

## Discovery Parameters

### NCBI Search Strategy

**Primary queries:**
```
Shigella sonnei[Organism] AND ST152[All Fields]
Shigella flexneri[Organism] AND <ST>[Attribute]
Shigella dysenteriae[Organism]
```

**Metadata extraction:**
- BioSample attributes: `mlst`, `sequence_type`, `ST`
- Cross-reference with EnteroBase (E. coli/Shigella database)

**Fallback:**
- Download Shigella assemblies, run mlst tool with `ecoli` scheme
- Most Shigella STs are in the E. coli MLST database

### Quality Filters

**Require:**
- Assembly available (MLST requires assembly)
- High-quality assembly (N50 > 20kb)

**Prefer:**
- Complete genomes
- ST annotated in metadata
- Confirmed ipaH presence (Shigella species marker)

**Accept:**
- Draft assemblies if good quality
- Unknown ST (will be determined by tool)

**Exclude:**
- E. coli misannotated as Shigella (check for ipaH gene)
- Contaminated assemblies

## Ground Truth Schema

```json
"ground_truth": {
  "species_confirmation": {
    "species": "string - Shigella species (e.g., 'Shigella sonnei')",
    "ipaH_present": true
  },
  "mlst": {
    "scheme": "ecoli",
    "sequence_type": "string or null - Expected ST (e.g., '152', '245')",
    "notes": "string or null - Context (e.g., 'clonal S. sonnei', 'diverse S. flexneri')"
  }
}
```

## Validation Logic

### PASS Criteria
- Tool reports ST matching ground truth
- Scheme correctly identified as `ecoli` (standard for Shigella)
- All 7 loci successfully typed

### PARTIAL Criteria
- Single-locus variant of expected ST
- Novel alleles detected but ST assigned
- Missing 1 locus due to assembly gap, remaining match profile

### FAIL Criteria
- Wrong ST (>1 allele difference)
- Failed to type ≥3 loci
- Wrong scheme detected

### Known Tool Issues
- **mlst:** Must use `ecoli` scheme for Shigella (auto-detection may fail if organism name is "Shigella" not "Escherichia coli")
- S. sonnei is highly clonal - nearly all isolates are ST152
- S. flexneri is diverse - many STs across different serotypes

## Tool Configurations

### mlst (Torsten Seemann) - specify ecoli scheme
```bash
mlst --scheme ecoli data/contigs.fa > actual/mlst/mlst_report.tsv
```

**Important:** May need to specify `--scheme ecoli` if organism name is "Shigella" (tool auto-detection might miss it).

Output format:
```
contigs.fa	ecoli	152	adk(3)	fumC(1)	gyrB(1)	icd(1)	mdh(1)	purA(7)	recA(1)
```

### stringMLST
```bash
stringMLST.py -p -P /path/to/pubmlst/ecoli/profile.txt \
  -k /path/to/pubmlst/ecoli/alleles/ \
  -o actual/stringmlst/ data/contigs.fa
```

## Validation Instructions Template

Example for S. sonnei ST152:
```
Expected ST152 (E. coli scheme). This is the dominant S. sonnei ST globally - over 90% of 
S. sonnei isolates are ST152 due to recent clonal expansion. Tool must use 'ecoli' scheme 
(Shigella uses E. coli MLST). Accept exact ST152 match. All 7 loci should type successfully. 
Any other ST for S. sonnei is rare and should be flagged for manual review - either a true 
variant or possible contamination.
```

Example for S. flexneri ST245:
```
Expected ST245 (E. coli scheme). S. flexneri is phylogenetically diverse with many STs. 
ST245 is common in S. flexneri 2a isolates. Tool must use 'ecoli' scheme. Accept exact 
ST245 match. Accept other STs as PARTIAL if the organism is confirmed S. flexneri 
(serotype correct) - S. flexneri has high ST diversity, so ST alone is not definitive.
```

Example for S. dysenteriae ST148:
```
Expected ST148 or related ST (E. coli scheme). S. dysenteriae type 1 (Sd1) is phylogenetically 
distinct from other Shigella. ST148 is common in Sd1 isolates. Tool must use 'ecoli' scheme. 
Accept exact ST148 match or related STs in the same clonal complex as PARTIAL. Sd1 is less 
common than S. sonnei/flexneri, so STs may be less well-documented.
```

## Cross-References

- **Species**: S. sonnei is clonal (ST152); S. flexneri is diverse (many STs)
- **Serotype**: S. sonnei has single serotype; S. flexneri serotype-ST correlation is weak
- **ipaH gene**: Must be present for Shigella confirmation

## Notes

- Shigella and E. coli are the same species - MLST treats them identically
- S. sonnei's clonality (ST152 dominance) is due to recent global expansion of a single lineage
- S. flexneri has much higher ST diversity - reflects longer evolutionary history and multiple lineages
- EnteroBase is the primary E. coli/Shigella MLST database
- Some labs report "Shigella MLST" but are using the E. coli scheme - always verify scheme name
- EIEC (Enteroinvasive E. coli) is ipaH+ but uses E. coli MLST and has different STs from Shigella
