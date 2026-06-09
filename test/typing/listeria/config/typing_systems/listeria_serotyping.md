# Listeria monocytogenes Serotyping

## Overview

Listeria monocytogenes is a foodborne pathogen causing listeriosis (particularly severe in pregnant women, neonates, elderly, immunocompromised). Serotyping is based on somatic (O) and flagellar (H) antigens.

There are **13 recognized serotypes**, but three dominate human disease:
- **Serotype 1/2a** - Most common in food, less virulent (Lineage II)
- **Serotype 1/2b** - Common in clinical isolates (Lineage I)
- **Serotype 4b** - Most common in outbreaks, highly virulent (Lineage I)

These three serotypes account for >95% of human listeriosis cases.

**In-silico serotyping** tools:
- **LisSero** - Uses lmo gene markers and flagellar typing
- **SISTR** (originally for Salmonella, adapted for Listeria)

## Selection Strategy

Target **12 test cases** covering:
- **Major serotypes** (9 cases) - 1/2a, 1/2b, 4b dominance
- **Rare serotypes** (2 cases) - 1/2c, 4a, etc.
- **Edge cases** (1 case) - Non-monocytogenes Listeria for specificity

## Target Serotypes

### Serotype 4b (Lineage I) - 4 cases

- **4b (epidemic clone)** (priority: critical) - Most outbreak-associated serotype, ST2 typically
- **4b (ST6)** (priority: high) - Second most common 4b lineage
- **4b (hypervirulent)** (priority: high) - ST1 with enhanced virulence markers
- **4b (rare ST)** (priority: medium) - Uncommon 4b lineage for scheme breadth

### Serotype 1/2a (Lineage II) - 3 cases

- **1/2a (ST5)** (priority: critical) - Most common 1/2a lineage, environmental persistence
- **1/2a (ST121)** (priority: high) - Hypervirulent 1/2a clone
- **1/2a (ST8)** (priority: medium) - Common food isolate

### Serotype 1/2b (Lineage I) - 2 cases

- **1/2b (ST5)** (priority: critical) - Common clinical serotype
- **1/2b (rare ST)** (priority: medium) - Less common lineage

### Serotype 1/2c (Lineage II) - 1 case

- **1/2c** (priority: medium) - Less common serotype, similar to 1/2a

### Rare Serotypes - 1 case

- **4a or 4c** (priority: low) - Rare serotypes for scheme coverage

### Edge Case - 1 case

- **L. ivanovii or L. innocua** (priority: low) - Non-monocytogenes species for specificity test

## Discovery Parameters

### NCBI Search Strategy

**Primary queries:**
```
Listeria monocytogenes[Organism] AND <serotype>[Attribute]
Listeria monocytogenes[Organism] AND serotype 4b[All Fields]
```

**Metadata extraction:**
- Organism name: `Listeria monocytogenes serotype 4b`
- BioSample attributes: `serotype`, `serovar`
- Strain names: often encode serotype (e.g., `FSL_N1-227_4b`)

**Fallback:**
- Search by lineage (Lineage I typically 1/2b or 4b; Lineage II typically 1/2a or 1/2c)
- Run LisSero on assemblies to determine serotype

### Quality Filters

**Require:**
- Assembly available (LisSero uses gene markers)
- High-quality assembly (N50 > 20kb)

**Prefer:**
- Complete genomes (Listeria is ~3 Mb, assembles well)
- Confirmed serotype in metadata
- Isolates from outbreaks (traceback cases)

**Accept:**
- Draft assemblies if well-assembled
- Serotype inferred from lineage + tool prediction

**Exclude:**
- Contaminated assemblies
- Non-monocytogenes Listeria unless used as negative control
- Poor quality (>300 contigs)

## Ground Truth Schema

```json
"ground_truth": {
  "serological": {
    "serotype": "string - Full serotype (e.g., '4b', '1/2a', '1/2b')",
    "lineage": "string - Phylogenetic lineage (I, II, III, IV)",
    "notes": "string or null - Optional context (e.g., 'epidemic clone', 'hypervirulent')"
  },
  "mlst": {
    "scheme": "lmonocytogenes",
    "sequence_type": "string - Expected ST (e.g., '2', '5', '121')"
  }
}
```

## Validation Logic

### PASS Criteria
- Tool reports serotype matching ground truth exactly
- Accept notation variants: `4b`, `serotype 4b`, `1/2a`

### PARTIAL Criteria
- Correct lineage but wrong serotype (e.g., predicted 1/2b when ground truth is 4b - both Lineage I)
- Tool reports "Listeria monocytogenes" without serotype (species correct)

### FAIL Criteria
- Wrong serotype entirely (different lineage)
- Misidentified as different Listeria species
- Tool fails to identify Listeria

### Known Tool Issues
- **LisSero:** Highly accurate for major serotypes (1/2a, 1/2b, 4b); may struggle with rare serotypes
- Some rare serotypes (4d, 4e) are poorly represented in databases
- Serotype prediction relies on specific gene markers (lmo genes, prs); incomplete assemblies may affect accuracy

## Tool Configurations

### LisSero
```bash
lissero -i data/contigs.fa -o actual/lissero/ -t 4
```

Output: TSV with serotype, lineage

### SISTR (if adapted for Listeria)
```bash
sistr -i data/contigs.fa -o actual/sistr/ -f tsv
```

### MLST
```bash
mlst --scheme lmonocytogenes data/contigs.fa > actual/mlst/mlst_report.tsv
```

## Validation Instructions Template

Example for serotype 4b:
```
Expected serotype 4b (Lineage I). This is the most outbreak-associated Listeria serotype, 
highly virulent. Common STs for 4b include ST2, ST6, ST1. Accept exact match '4b', 'serotype 
4b', or '4b/4d/4e' (tools may group these). Do not accept 1/2b as PASS (different serotype, 
though both are Lineage I). Tool should confidently call serotype.
```

Example for serotype 1/2a:
```
Expected serotype 1/2a (Lineage II). Most common in food environments, less virulent than 
4b or 1/2b. Common STs for 1/2a include ST5, ST8, ST121. Accept exact match '1/2a', 
'serotype 1/2a'. Also accept '1/2a/3a' (some tools group these closely related serotypes). 
Do not accept 1/2c as PASS (distinct serotype, though both Lineage II).
```

Example for serotype 1/2b:
```
Expected serotype 1/2b (Lineage I). Common in clinical isolates. Accept exact match '1/2b', 
'serotype 1/2b', or '1/2b/3b/7' (grouped by some tools). Do not accept 4b as PASS (different 
serotype despite same lineage).
```

## Cross-References

- **MLST**: Serotype 4b commonly ST2 or ST6; serotype 1/2a commonly ST5 or ST121
- **Lineage**: Lineage I (1/2b, 4b, 3b) more virulent; Lineage II (1/2a, 1/2c, 3a) more environmental
- **Outbreak Investigation**: cgMLST is primary tool; serotype is supplementary

## Notes

- Only three serotypes (1/2a, 1/2b, 4b) account for >95% of human listeriosis
- Serotype 4b is overrepresented in outbreaks (30% of isolates, >50% of outbreaks)
- Lineage correlates with serotype and virulence potential
- In-silico serotyping for Listeria is highly reliable due to genetic markers
- Traditional serology (antisera-based) is labor-intensive; WGS-based typing is now standard
- cgMLST/wgMLST preferred for outbreak investigation; serotyping used for rapid screening
- Some serotypes are rare (<1% of cases): 3a, 3b, 3c, 4a, 4c, 4d, 4e, 7
