# Multi-Locus Sequence Typing (MLST)

## Overview

MLST characterizes bacterial isolates by sequencing internal fragments of 7-8 housekeeping genes. Each unique combination of alleles defines a **Sequence Type (ST)**. MLST is:
- Species/genus-specific (different schemes for different organisms)
- Used for outbreak investigation and phylogenetic analysis
- More discriminatory than serotyping for some organisms
- Stable marker (housekeeping genes under purifying selection)

Tools like `mlst` (Torsten Seemann) and `stringMLST` predict ST from assemblies.

## Selection Strategy

We target **40 test cases** across multiple organisms for **broad scheme coverage**:

### Distribution
- **Salmonella enterica** (10 cases) - Diverse STs, some linked to serotypes
- **Escherichia coli** (8 cases) - Mix of commensal and pathogenic STs
- **Campylobacter jejuni** (5 cases) - Common food-borne pathogen
- **Listeria monocytogenes** (5 cases) - Different lineages
- **Shigella** (4 cases) - If using separate scheme vs E. coli
- **Other foodborne** (8 cases) - Vibrio, Yersinia, Cronobacter, etc.

Priority: Test both common STs (positive controls) and rare STs (scheme coverage).

## Target Organisms and STs

### Salmonella enterica (senterica scheme) - 10 cases

- **ST19** (priority: critical) - Typhimurium dominant. Most common globally.
- **ST11** (priority: critical) - Enteritidis dominant. Second most common.
- **ST45** (priority: high) - Newport associated.
- **ST27** (priority: high) - Heidelberg associated.
- **ST32** (priority: high) - Infantis dominant in Europe.
- **ST34** (priority: high) - Monophasic Typhimurium, single-locus variant of ST19.
- **ST2** (priority: medium) - Paratyphi A.
- **ST1** (priority: medium) - Typhi. Regulated pathogen.
- **ST198** (priority: medium) - Kentucky.
- **Novel/rare ST** (priority: low) - Any ST > 1000 for scheme breadth.

### Escherichia coli (ecoli scheme) - 8 cases

- **ST131** (priority: critical) - Pandemic ExPEC (extraintestinal), fluoroquinolone-resistant.
- **ST11** (priority: high) - O157:H7 associated. STEC outbreaks.
- **ST95** (priority: high) - ExPEC, neonatal meningitis.
- **ST73** (priority: high) - ExPEC, UTIs.
- **ST10** (priority: medium) - Commensal, diverse.
- **ST69** (priority: medium) - ExPEC.
- **ST58** (priority: medium) - Shiga toxin-producing.
- **Rare/novel ST** (priority: low) - For scheme coverage.

### Campylobacter jejuni (cjejuni scheme) - 5 cases

- **ST21** (priority: critical) - Most common globally, poultry reservoir.
- **ST45** (priority: high) - Common, clinical isolates.
- **ST50** (priority: high) - Frequent in outbreaks.
- **ST257** (priority: medium) - Emerging clone.
- **Rare ST** (priority: low) - Uncommon lineage.

### Listeria monocytogenes (lmonocytogenes scheme) - 5 cases

- **ST1** (priority: critical) - Lineage I, serotype 1/2b. Outbreak-associated.
- **ST2** (priority: critical) - Lineage I, serotype 4b. Major epidemic clone.
- **ST5** (priority: high) - Lineage II, serotype 1/2a. Common.
- **ST6** (priority: high) - Lineage II, serotype 1/2a.
- **ST121** (priority: medium) - Serotype 1/2a, hypervirulent.

### Shigella (if using separate scheme) - 4 cases

- **ST152** (priority: high) - S. flexneri.
- **ST245** (priority: high) - S. sonnei dominant globally.
- **ST147** (priority: medium) - S. flexneri.
- **Rare ST** (priority: low)

**Note:** Many labs use E. coli MLST scheme for Shigella (same species). Adjust based on target scheme.

### Other Foodborne Pathogens - 8 cases

#### Vibrio parahaemolyticus (2 cases)
- **ST3** (priority: high) - Pandemic clone, tdh+.
- **ST36** (priority: medium)

#### Yersinia enterocolitica (2 cases)
- **ST9** (priority: high) - Biotype 4, serotype O:3.
- **ST29** (priority: medium) - Biotype 2.

#### Cronobacter sakazakii (2 cases)
- **ST4** (priority: high) - Infant formula outbreaks.
- **ST1** (priority: medium)

#### Bacillus cereus (1 case)
- **ST26** (priority: medium) - Emetic toxin producer.

#### Staphylococcus aureus (1 case)
- **ST5** (priority: high) - Healthcare-associated MRSA.

## Discovery Parameters

### NCBI Search Strategy

**Primary query:**
```
<organism>[Organism] AND <ST>[Attribute]
```

**Fallback:**
- Search by organism, extract ST from BioSample attributes or publications
- Use assemblies with good metadata, run MLST tool to determine ST

**For organisms with targeted STs:**
- Query BioSample for `MLST` or `sequence_type` or `ST` attribute fields
- Cross-reference with PubMLST database downloads

### Quality Filters

**Require:**
- Assembly available (MLST requires assembly, not reads)
- High-quality assembly (N50 > 20kb, <500 contigs preferred)

**Prefer:**
- Complete/chromosome assemblies
- ST annotated in metadata (for validation)
- Reputable submitters

**Accept:**
- Scaffold assemblies if good quality
- Unknown ST (will be determined by tool)

**Exclude:**
- Contaminated assemblies
- Poor quality (N50 < 5kb, >1000 contigs)
- Wrong species

## Ground Truth Schema

```json
"ground_truth": {
  "mlst": {
    "scheme": "string - MLST scheme name (e.g., 'senterica', 'ecoli', 'cjejuni')",
    "sequence_type": "string or null - Expected ST (e.g., '19', 'novel')"
  }
}
```

**Note:** `sequence_type` can be `null` if ST is unknown and will be determined by tool execution. In these cases, validation checks that tool produces a valid ST, not a specific value.

## Validation Logic

### PASS Criteria
- Tool reports ST matching ground truth
- OR if ground truth ST is null: tool reports a valid ST (not "Unknown" or "Novel")

### PARTIAL Criteria
- Tool reports close match (single-locus variant of expected ST)
- Tool identifies novel alleles but assigns ST

### FAIL Criteria
- Tool reports wrong ST (>1 allele difference)
- Tool fails to determine ST when expected
- Tool reports "contamination" or "multiple STs"

### Known Tool Issues
- **mlst:** Conservative, reports "-" if any locus missing
- **stringMLST:** May report novel alleles not in PubMLST database
- Incomplete assemblies can cause locus dropout

## Tool Configurations

### mlst (Torsten Seemann)
```bash
mlst --scheme <scheme> <assembly.fasta> > mlst_report.tsv
```

Output: TSV with columns: filename, scheme, ST, allele1, allele2, ..., allele7

### stringMLST
```bash
stringMLST.py -p -P <pubmlst_profile> -k <alleles_dir> -o <output> <assembly.fasta>
```

## Validation Instructions Template

Example for Salmonella ST19:
```
Expected ST19, the dominant sequence type for Salmonella Typhimurium globally. 
Also accept ST34 as PARTIAL - it is a single-locus variant (aroC allele difference) 
commonly found in clinical isolates. Any other ST is FAIL unless novel alleles are 
reported, which should be flagged for manual review. Tool must report all 7 loci 
successfully typed.
```

## Notes

- MLST schemes are organism-specific - ensure correct scheme used
- PubMLST database is canonical source for ST definitions
- Novel STs require submission to PubMLST for official designation
- Some organisms have multiple schemes (e.g., cgMLST vs traditional MLST)
- ST assignments can change if allele definitions are updated
- Cross-reference ST with serotype for Salmonella validation
