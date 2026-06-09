# Listeria monocytogenes MLST

## Overview

MLST for Listeria monocytogenes uses 7 housekeeping genes:
- **abcZ** - ABC transporter
- **bglA** - beta-glucosidase
- **cat** - catalase
- **dapE** - succinyl-diaminopimelate desuccinylase
- **dat** - D-amino acid aminotransferase
- **ldh** - L-lactate dehydrogenase
- **lhkA** - histidine kinase

Each unique allele combination defines a **Sequence Type (ST)**. MLST is used for:
- Clonal complex (CC) assignment - groups related outbreak strains
- Lineage identification (complements serotyping)
- Phylogenetic analysis
- Tracking persistent strains in food facilities

**Note:** cgMLST (Core Genome MLST) has largely replaced traditional MLST for outbreak investigation in Listeria, but MLST remains useful for clonal complex assignment.

## Selection Strategy

Target **8 test cases** covering:
- **Lineage I** (4 cases) - Serotypes 1/2b, 4b (outbreak-associated, hypervirulent)
- **Lineage II** (3 cases) - Serotypes 1/2a, 1/2c (food-associated, persistent)
- **Rare lineages** (1 case) - Lineage III or IV for scheme breadth

## Target STs

### Lineage I (Hypervirulent, Outbreak-Associated) - 4 cases

- **ST2** (priority: critical) - Serotype 4b, major epidemic clone. Responsible for large outbreaks (cantaloupe 2011, ice cream 2015).
- **ST1** (priority: critical) - Serotype 1/2b, hypervirulent. Common in clinical isolates.
- **ST6** (priority: high) - Serotype 4b, second most common 4b ST. Frequently isolated from food.
- **ST4** (priority: medium) - Serotype 4b variant, less common but outbreak-associated.

### Lineage II (Environmental Persistence, Food-Associated) - 3 cases

- **ST5** (priority: critical) - Serotype 1/2a, most common Lineage II ST. Food facility persistence.
- **ST121** (priority: high) - Serotype 1/2a, hypervirulent variant with LIPI-3 and LIPI-4 pathogenicity islands.
- **ST8** (priority: medium) - Serotype 1/2a, common in food environments.

### Rare Lineages - 1 case

- **Lineage III/IV ST** (priority: low) - Rare lineages (e.g., ST398, ST199), mostly from animals. Scheme coverage.

## Discovery Parameters

### NCBI Search Strategy

**Primary queries:**
```
Listeria monocytogenes[Organism] AND <ST>[Attribute]
Listeria monocytogenes[Organism] AND ST2[All Fields]
Listeria monocytogenes[Organism] AND serotype 4b[All Fields] AND outbreak
```

**Metadata extraction:**
- BioSample attributes: `mlst`, `sequence_type`, `ST`
- Cross-reference with serotype (4b typically ST2 or ST6; 1/2a typically ST5 or ST121)

**Fallback:**
- Download Listeria assemblies, run mlst tool to determine ST
- Use Institut Pasteur MLST database for L. monocytogenes

### Quality Filters

**Require:**
- Assembly available (MLST requires assembly)
- High-quality assembly (N50 > 20kb)

**Prefer:**
- Complete genomes (Listeria assembles well, ~3 Mb)
- ST and serotype annotated in metadata (for cross-validation)
- Isolates from outbreaks or food facilities

**Accept:**
- Draft assemblies if good quality
- Unknown ST (will be determined by tool)

**Exclude:**
- Non-monocytogenes Listeria (L. ivanovii, L. innocua) unless used as negative control
- Contaminated assemblies
- Poor quality (>300 contigs)

## Ground Truth Schema

```json
"ground_truth": {
  "serological": {
    "serotype": "string - Expected serotype (e.g., '4b', '1/2a')",
    "lineage": "string - Phylogenetic lineage (I, II, III, IV)"
  },
  "mlst": {
    "scheme": "lmonocytogenes",
    "sequence_type": "string or null - Expected ST (e.g., '2', '5', '121')",
    "clonal_complex": "string or null - Optional CC (e.g., 'CC2', 'CC5')",
    "notes": "string or null - Context (e.g., 'epidemic clone', 'persistent food isolate')"
  }
}
```

## Validation Logic

### PASS Criteria
- Tool reports ST matching ground truth
- Scheme correctly identified as `lmonocytogenes`
- All 7 loci successfully typed

### PARTIAL Criteria
- Single-locus variant of expected ST
- Novel alleles detected but ST assigned
- Serotype-ST correlation confirmed even if ST differs slightly (e.g., ST6 vs ST2, both serotype 4b)

### FAIL Criteria
- Wrong ST with different serotype/lineage
- Failed to type ≥3 loci
- Wrong scheme detected

### Known Tool Issues
- **mlst:** L. monocytogenes scheme is well-curated; few issues
- ST2 and ST6 are both serotype 4b - distinguish based on allele profiles
- ST121 is hypervirulent 1/2a - should be flagged as notable (carries LIPI-3, LIPI-4)

## Tool Configurations

### mlst (Torsten Seemann)
```bash
mlst --scheme lmonocytogenes data/contigs.fa > actual/mlst/mlst_report.tsv
```

Output format:
```
contigs.fa	lmonocytogenes	2	abcZ(1)	bglA(1)	cat(1)	dapE(1)	dat(1)	ldh(1)	lhkA(1)
```

### stringMLST
```bash
stringMLST.py -p -P /path/to/pubmlst/lmonocytogenes/profile.txt \
  -k /path/to/pubmlst/lmonocytogenes/alleles/ \
  -o actual/stringmlst/ data/contigs.fa
```

## Validation Instructions Template

Example for ST2:
```
Expected ST2 (lmonocytogenes scheme), serotype 4b, Lineage I. This is the major epidemic 
clone responsible for large Listeria outbreaks (2011 cantaloupe, 2015 ice cream). All 7 loci 
must be typed successfully: abcZ(1), bglA(1), cat(1), dapE(1), dat(1), ldh(1), lhkA(1). 
Accept exact ST2 match. Do not accept ST6 as PASS (also serotype 4b but distinct clone). 
ST2 is highly virulent and outbreak-associated - flag for epidemiological significance.
```

Example for ST5:
```
Expected ST5 (lmonocytogenes scheme), serotype 1/2a, Lineage II. This is the most common 
Lineage II ST, frequently isolated from food processing environments due to persistence. 
Accept exact ST5 match. All 7 loci should type successfully. ST5 is less virulent than 
Lineage I STs (ST1, ST2) but important for food safety. Do not accept ST121 as PASS 
(also 1/2a but hypervirulent variant with additional pathogenicity islands).
```

Example for ST121:
```
Expected ST121 (lmonocytogenes scheme), serotype 1/2a, Lineage II. This is a hypervirulent 
1/2a clone carrying LIPI-3 and LIPI-4 pathogenicity islands - unusual for Lineage II, which 
is typically less virulent. Accept exact ST121 match. All 7 loci must type successfully. 
Flag ST121 isolates for virulence gene profiling (LIPI-3, LIPI-4) to confirm hypervirulent 
status. Do not accept ST5 as PASS (common 1/2a but non-hypervirulent).
```

## Cross-References

- **Serotype**: ST2/ST6 typically 4b; ST1 typically 1/2b; ST5/ST121 typically 1/2a
- **Lineage**: ST2/ST1/ST6 are Lineage I (hypervirulent); ST5/ST121 are Lineage II (persistent)
- **Clonal Complex**: CC2, CC5, CC121 are epidemiologically significant

## Notes

- Listeria MLST is less discriminatory than cgMLST for outbreak investigation
- ST-serotype correlation is strong but not absolute (e.g., ST5 is mostly 1/2a, but variants exist)
- ST121 is epidemiologically significant - Lineage II but hypervirulent (rare trait for this lineage)
- Institut Pasteur hosts the Listeria MLST database (alternate to PubMLST)
- Persistent food facility strains often have same ST over years - ST5 common in this context
- cgMLST has become standard for Listeria outbreak investigation; MLST used for initial clonal complex assignment
