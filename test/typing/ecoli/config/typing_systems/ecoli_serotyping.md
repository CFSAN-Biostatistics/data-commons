# E. coli Serotyping

## Overview

E. coli serotyping classifies strains based on three surface antigens:
- **O antigen** - Lipopolysaccharide (LPS) somatic antigen (~180 types)
- **H antigen** - Flagellar antigen (~53 types)
- **K antigen** - Capsular antigen (less commonly typed)

Serotyping is critical for identifying pathogenic E. coli:
- **STEC/EHEC** - Shiga toxin-producing (e.g., O157:H7, O26:H11, O103:H2, O111:H8, O145:H28, O45:H2)
- **ETEC** - Enterotoxigenic E. coli
- **EPEC** - Enteropathogenic E. coli
- **ExPEC** - Extraintestinal pathogenic E. coli

In-silico tools like **SerotypeFinder** and **ECTyper** predict serotype from WGS data.

## Selection Strategy

Target **20 test cases** covering:
- **"Big Six" non-O157 STEC** (6 cases) - FDA/USDA regulated serotypes
- **O157:H7** (3 cases) - Classic STEC, most common outbreak strain
- **Emerging STEC** (3 cases) - O26, O111 variants
- **ExPEC serotypes** (3 cases) - UTI-associated
- **Common commensal** (2 cases) - Non-pathogenic baseline
- **Edge cases** (3 cases) - Non-motile (H-), rough strains (O-), novel combinations

## Target Serotypes

### Big Six Non-O157 STEC (6 cases)

- **O26:H11** (priority: critical) - Leading non-O157 STEC globally, common in outbreaks
- **O103:H2** (priority: critical) - Second most common non-O157 STEC
- **O111:H8** (priority: critical) - Historic outbreak strain, less common now
- **O145:H28** (priority: critical) - Common in US beef-associated outbreaks
- **O45:H2** (priority: high) - Emerging outbreak strain
- **O121:H19** (priority: high) - Common in produce outbreaks

### O157 STEC (3 cases)

- **O157:H7** (priority: critical) - Classic STEC, most studied serotype
- **O157:NM** (priority: high) - Non-motile variant, less common
- **O157:H-** (priority: medium) - Flagellar deletion variant

### Emerging/Other STEC (3 cases)

- **O26:H-** (priority: high) - Non-motile O26, increasing prevalence
- **O111:NM** (priority: medium) - Non-motile O111
- **O104:H4** (priority: high) - European outbreak strain (2011 Germany), unusual STEC/EAEC hybrid

### ExPEC Serotypes (3 cases)

- **O25:H4** (priority: high) - ST131-associated, pandemic ExPEC clone
- **O1:H7** (priority: medium) - Neonatal meningitis (NMEC)
- **O6:H1** (priority: medium) - UTI-associated ExPEC

### Common Commensal (2 cases)

- **O9:H4** (priority: medium) - Common commensal, non-pathogenic
- **ONT:H-** (priority: low) - Non-typeable O, non-motile (baseline negative control)

### Edge Cases (3 cases)

- **Rough strain (O-)** (priority: low) - Loss of O antigen, rare
- **Novel O:H combination** (priority: low) - Uncommon serotype for scheme breadth
- **Multiple H antigens** (priority: low) - Phase variation testing

## Discovery Parameters

### NCBI Search Strategy

**Primary queries:**
```
Escherichia coli[Organism] AND <serotype>[Attribute]
Escherichia coli[Organism] AND O157:H7[All Fields]
```

**Metadata extraction:**
- BioSample attributes: `serotype`, `serovar`, `serogroup`
- Organism name: `Escherichia coli O157:H7` patterns
- Publication titles: "O26:H11", "STEC O103"

**Fallback:**
- Search by pathotype (STEC, EHEC, ExPEC) and run SerotypeFinder to determine serotype
- Cross-reference with EcOH database (E. coli O and H antigen database)

### Quality Filters

**Require:**
- Assembly available (SerotypeFinder works best on assemblies)
- Reads available (for read-based typing validation)

**Prefer:**
- Complete genomes for O/H gene cluster analysis
- RefSeq or GenBank curated assemblies
- Serotype confirmed by traditional serology or WGS tools
- Reputable submitters (CDC, FDA, university labs)

**Accept:**
- Draft assemblies if high quality (N50 > 50kb)
- Serotype inferred from pathotype + metadata

**Exclude:**
- Poor assemblies (N50 < 10kb, >500 contigs)
- Contaminated samples
- Shigella misannotated as E. coli (check for ipaH)

## Ground Truth Schema

```json
"ground_truth": {
  "serological": {
    "serotype": "string - Full serotype (e.g., 'O157:H7', 'O26:H11', 'ONT:H-')",
    "o_antigen": "string or null - O antigen (e.g., 'O157', 'O26', 'ONT', 'O-')",
    "h_antigen": "string or null - H antigen (e.g., 'H7', 'H11', 'H-', 'NM')",
    "k_antigen": "string or null - K antigen if known (rarely typed)"
  }
}
```

**Notation:**
- `ONT` = O non-typeable (antigen present but not in typing scheme)
- `O-` = Rough strain, no O antigen
- `H-` = Non-motile, no flagella
- `NM` = Non-motile (synonym for H-)

## Validation Logic

### PASS Criteria
- Tool reports O and H antigens matching ground truth
- Exact match on serotype notation (case-insensitive)
- Accept `H-` and `NM` as equivalent (both mean non-motile)

### PARTIAL Criteria
- Correct O antigen but wrong/missing H antigen (common in draft assemblies with fragmented flagellar operons)
- Correct H antigen but O is `ONT` vs specific type (acceptable if O gene cluster incomplete)
- Tool reports "multiple H antigens" when ground truth is one specific H (phase variation)

### FAIL Criteria
- Wrong O antigen (different serogroup entirely)
- Both O and H incorrect
- Tool reports "contamination" or "mixed serotypes"

### Known Tool Issues
- **SerotypeFinder:** Requires good assembly of O/H gene clusters; fragmented assemblies may result in partial calls
- **ECTyper:** Uses both reads and assemblies; may call multiple antigens if reads contaminated
- Non-motile strains (H-) often have deleted or disrupted flagellar genes - tools must distinguish deletion from assembly gaps

## Tool Configurations

### SerotypeFinder (CGE)
```bash
serotypefinder.pl -i data/contigs.fa -o actual/serotypefinder/ -d /path/to/serotypefinder_db
```

Output: `results_tab.tsv` with columns: O_type, H_type

### ECTyper
```bash
ectyper -i data/contigs.fa -o actual/ectyper/
```

Output: `output.tsv` with serotype, O-type, H-type columns

### ShigaTyper (includes E. coli O antigen detection)
```bash
shigatyper --R1 data/reads_1.fq.gz --R2 data/reads_2.fq.gz --name ecoli > actual/shigatyper/result.tsv
```

## Validation Instructions Template

Example for O157:H7:
```
Expected serotype O157:H7. O antigen must be O157 (wzx/wzy O157 cluster). H antigen must be 
H7 (fliC H7 allele). This is the classic STEC serotype responsible for major outbreaks. 
Accept case-insensitive match. Do not accept O157:NM or O157:H- (those are non-motile variants 
and would be separate test cases). Tool should detect both O and H successfully.
```

Example for O26:H-:
```
Expected serotype O26:H- (non-motile). O antigen must be O26. H antigen should be reported as 
H-, NM, or 'non-motile' (accept any of these notations as PASS). This strain lacks functional 
flagella. Do not accept O26:H11 (that is the motile variant).
```

## Cross-References

- **MLST**: O157:H7 typically ST11; O26:H11 typically ST21
- **Virulence**: STEC serotypes should carry stx1/stx2 genes
- **Pathotype**: Use serotype to infer pathotype (O157 → STEC; O25:H4 → ExPEC)

## Notes

- E. coli has >180 O antigens and >53 H antigens - true serotyping coverage would require thousands of test cases
- Focus on clinically/regulatory relevant serotypes
- Traditional serology requires antisera and cultured isolates; WGS-based in-silico typing is now standard
- Some H antigens are phase-variable (alternate between two flagellar types) - WGS typically detects both
- O antigen gene clusters (rfb/wzy/wzx) are large (~10-20kb); assembly quality critical for accurate O typing
