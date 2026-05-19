# Salmonella Serological Typing

## Overview

The Kauffmann-White scheme classifies Salmonella into over 2,600 serovars based on antigenic differences in:
- **O antigens** (somatic/cell wall lipopolysaccharides)
- **H antigens** (flagellar proteins - Phase 1 and Phase 2)

Serotyping is critical for outbreak investigation, source attribution, and public health surveillance. Tools like SeqSero2 and SISTR predict serotype from whole genome sequence data (in-silico serotyping).

## Selection Strategy

We target **100 test cases** distributed across:

### 1. High-Frequency Serotypes (30 cases)
Most common in clinical surveillance - positive controls for routine detection.

### 2. Antigenic Diversity Representatives (50 cases)
Systematic sampling across O-groups and H-antigen combinations to test comprehensive scheme coverage.

### 3. Edge Cases (20 cases)
Known difficult variants: monophasic, rough, non-motile, rare but regulated.

## Target Serotypes

### High Frequency (30 cases)

- **Enteritidis** (priority: critical) - Most common in poultry/eggs. Antigenic formula 1,9,12:g,m:-. Tests Phase 2-negative detection.
- **Typhimurium** (priority: critical) - Most common in US clinical isolates. Formula 1,4,[5],12:i:1,2. Dominant ST19.
- **Newport** (priority: critical) - Third most common, multiresistant strains. Formula 6,8:e,h:1,2.
- **Javiana** (priority: high) - Common in produce outbreaks. Formula 1,9,12:l,z28:1,5.
- **Heidelberg** (priority: high) - Poultry-associated, resistance concerns. Formula 1,4,[5],12:r:1,2.
- **Infantis** (priority: high) - Emerging globally, broiler chicken reservoir. Formula 6,7,14:r:1,5.
- **Saintpaul** (priority: high) - Produce outbreaks. Formula 1,4,[5],12:e,h:1,2.
- **Muenchen** (priority: high) - Cattle-associated. Formula 6,8:d:1,2.
- **Braenderup** (priority: high) - Formula 6,7,14:e,h:e,n,z15.
- **Thompson** (priority: high) - Formula 6,7,14:k:1,5.
- **Hadar** (priority: medium) - Formula 6,8:z10:e,n,x.
- **Montevideo** (priority: medium) - Formula 6,7,14:g,m,s:-.
- **Agona** (priority: medium) - Formula 1,4,12:f,g,s:-.
- **Oranienburg** (priority: medium) - Formula 6,7,14:m,t:-.
- **Bareilly** (priority: medium) - Formula 6,7,14:y:1,5.
- **Mississippi** (priority: medium) - Formula 6,7,14:b:1,5.
- **Uganda** (priority: medium) - Formula 1,4,12,27:f,g:-.
- **Kentucky** (priority: medium) - Formula 8,20:i:z6.
- **Anatum** (priority: medium) - Formula 3,10:e,h:1,6.
- **Derby** (priority: medium) - Formula 1,4,[5],12:f,g:-.
- **Schwarzengrund** (priority: medium) - Formula 1,4,12,27:d:1,7.
- **Panama** (priority: medium) - Formula 1,9,12:l,v:1,5.
- **Poona** (priority: medium) - Formula 1,13,22:z:1,6.
- **Mbandaka** (priority: medium) - Formula 6,7,14:z10:e,n,z15.
- **Worthington** (priority: medium) - Formula 6,7,14:z10:e,n,x.
- **Sandiego** (priority: medium) - Formula 4,5,12:e,h:e,n,x.
- **Bovismorbificans** (priority: medium) - Formula 6,7,14:r:1,5. (Formerly Paratyphi B var. L(+) tartrate+)
- **Stanley** (priority: medium) - Formula 1,4,[5],12:d:1,2.
- **Hartford** (priority: medium) - Formula 6,8:e,h:1,5.
- **Give** (priority: medium) - Formula 3,10:l,v:1,7.

### Antigenic Diversity (50 cases)

Systematic coverage across O-groups:

#### O:2 Group (3 cases)
- **Paratyphi A** (priority: high) - Regulated, invasive. Formula 1,2,12:a:-.
- **Kisangani** (priority: low) - Formula 1,2,12:e,h:1,5.
- **Schwarzenbek** (priority: low) - Formula 1,2,12:l,v:1,7.

#### O:3,10 Group (5 cases)
- **Anatum** (listed above)
- **Senftenberg** (priority: medium) - Heat-resistant. Formula 1,3,19:g,s,t:-.
- **Rissen** (priority: low) - Formula 6,7:f,g:-.
- **Meleagridis** (priority: low) - Turkey-associated. Formula 3,10:e,h:1,w.
- **Tennessee** (priority: low) - Formula 3,10:z29:-.

#### O:4 Group (8 cases)
- **Typhimurium**, **Heidelberg**, **Saintpaul**, **Derby**, **Agona** (listed above)
- **Blockley** (priority: low) - Formula 1,4,[5],12:i:e,n,x.
- **Bredeney** (priority: low) - Formula 1,4,12,27:l,v:1,7.
- **London** (priority: low) - Formula 3,10:l,v:1,6.

#### O:6,7 Group (10 cases)
- **Braenderup**, **Thompson**, **Infantis**, **Montevideo**, **Oranienburg**, **Bareilly**, **Mississippi**, **Mbandaka**, **Bovismorbificans** (listed above)
- **Ohio** (priority: low) - Formula 6,7:b:1,5.

#### O:6,8 Group (5 cases)
- **Newport**, **Muenchen**, **Hadar**, **Hartford** (listed above)
- **Blockley** (priority: low) - Formula 6,8:l,v:1,7.

#### O:7 Group (3 cases)
- **Choleraesuis** (priority: medium) - Swine-adapted, invasive. Formula 6,7:c:1,5.
- **Decatur** (priority: low) - Formula 6,7,14:z4,z23:-.
- **Litchfield** (priority: low) - Formula 6,7:l,v:1,2.

#### O:8 Group (3 cases)
- **Kentucky** (listed above)
- **Kottbus** (priority: low) - Formula 6,8:e,h:1,5.
- **Weltevreden** (priority: medium) - Southeast Asia common. Formula 3,10:r:z6.

#### O:9 Group (5 cases)
- **Enteritidis**, **Javiana**, **Panama** (listed above)
- **Virchow** (priority: medium) - Formula 6,7:r:1,2.
- **Dublin** (priority: medium) - Cattle-adapted, invasive. Formula 1,9,12:g,p:-.

#### O:11 Group (2 cases)
- **Give** (listed above)
- **Gaminara** (priority: low) - Formula 1,9,12:l,z28:z6.

#### O:13 Group (2 cases)
- **Poona** (listed above)
- **Rubislaw** (priority: low) - Formula 1,13,23:d:e,n,x.

#### Rare O-groups (4 cases)
- **Typhi** (priority: critical) - Regulated, human-only pathogen. Formula 9,12,[Vi]:d:-.
- **Paratyphi B** (priority: high) - Formula 1,4,[5],12:b:1,2.
- **Paratyphi C** (priority: medium) - Formula 6,7:[Vi]:c:1,5.
- **Gallinarum** (priority: medium) - Non-motile, poultry. Formula 1,9,12:-:-.

### Edge Cases (20 cases)

- **I 4,[5],12:i:-** (priority: critical) - Monophasic Typhimurium variant. Tests H2-negative detection. Major public health concern.
- **Rough strains** (priority: high) - 3 cases with incomplete O-antigen synthesis. Tests tool robustness.
- **Non-motile variants** (priority: high) - 2 cases lacking flagella. Formula X,Y:-:-.
- **Typhi Vi-negative** (priority: medium) - Lacks capsule antigen. Tests variant detection.
- **Multiple phase expression** (priority: medium) - Strain expressing both H1 and H2 simultaneously.
- **Novel/unnamed serovars** (priority: low) - 3 cases with formula not matching named serovars.
- **Crossreactive O-antigens** (priority: medium) - 2 cases with O-antigens shared across groups (e.g., O:1,4,5,12 vs 1,4,12).
- **Rare H-antigens** (priority: low) - 3 cases with unusual flagellar types (z15, z27, z29, z35, z36, etc.).
- **Subspecies II-VI** (priority: low) - 3 cases from non-enterica subspecies (salamae, arizonae, diarizonae, houtenae, indica).

## Discovery Parameters

### NCBI Search Strategy

**Primary query:**
```
Salmonella enterica[Organism] AND <serotype>[Attribute]
```

**Fallback queries:**
- Parse organism name: `Salmonella enterica subsp. enterica serovar <serotype>`
- Free-text search in strain or isolate fields

### Quality Filters

**Prefer:**
- Coverage ≥ 30x (if reported)
- Assembly + reads available (test both tool modes)
- Complete/chromosome-level assemblies for accuracy
- Reputable submitters (FDA, CDC, USDA, university, RefSeq)

**Accept:**
- Assembly-only if high quality (N50 > 50kb, < 100 contigs)
- Scaffold/contig assemblies if well-assembled
- Diverse geographic/temporal origins

**Exclude:**
- Marked as contaminated
- Poor assembly quality (N50 < 10kb, > 500 contigs)
- No serotype metadata (unless edge case discovery)

## Ground Truth Schema

```json
"ground_truth": {
  "serological": {
    "serotype": "string - Expected serotype name",
    "antigenic_formula": "string - Full formula (e.g., '1,4,[5],12:i:1,2')",
    "o_antigen": ["array", "of", "O antigens"],
    "h1_antigen": ["array", "of", "H1 antigens"],
    "h2_antigen": ["array", "or", "empty", "for", "monophasic"]
  }
}
```

## Validation Logic

### PASS Criteria
- Serotype name matches ground truth (exact or accepted synonym)
- Antigenic formula components correct (O, H1, H2)
- Tool correctly identifies monophasic variants (H2 = "-" or empty)

### PARTIAL Criteria
- Correct O antigens but wrong H antigens
- Correct serotype family but wrong variant (e.g., Typhimurium vs I 4,[5],12:i:-)
- Minor notation differences (brackets, spacing) but semantically correct

### FAIL Criteria
- Wrong serotype prediction
- Failed to run or produce output
- Predicted serotype from different O-group

### Known Tool Issues
- **SeqSero2:** May omit bracket notation around O:5
- **SISTR:** Conservative predictions, may report "unidentified" for rare types
- **Both:** May struggle with rough/non-motile variants

## Tool Configurations

### SeqSero2 (Full Scheme)
```bash
SeqSero2_package.py -m a -t 4 -i <reads> -d <output>  # reads mode
SeqSero2_package.py -m k -t 4 -i <assembly> -d <output>  # assembly mode
```

### SeqSero2S (Abbreviated Scheme)
```bash
SeqSero2S_package.py -m a -t 4 -i <reads> -d <output>
```

### SISTR
```bash
sistr -f tab -o <output> <assembly>
```

## Notes

- Kauffmann-White scheme continuously updated - reference version matters
- Serotype names have historical synonyms (e.g., Bovismorbificans = Paratyphi B var. L(+) tartrate+)
- Vi antigen (capsular) is distinct from O/H but part of formula notation
- Subspecies II-VI use numeric serotype designation (e.g., II 42:z39:-)
