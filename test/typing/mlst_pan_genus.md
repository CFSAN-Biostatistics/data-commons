# Pan-Genus MLST Test Manifest

## Overview

This is a **pan-genus MLST typing manifest** for validating MLST tools across multiple bacterial genera. Unlike organism-specific manifests, this focuses exclusively on MLST (Multi-Locus Sequence Typing) tool validation across diverse organisms and schemes.

**Purpose:** Test MLST tool robustness across:
- Multiple organism schemes (different gene sets)
- Diverse assembly qualities
- Common vs novel STs
- Multi-scheme disambiguation

**Target tools:**
- `mlst` (Torsten Seemann) - Auto-detects schemes
- `stringMLST` - Requires scheme specification
- PubMLST database integrity

## Selection Strategy

Target **50 test cases** across organisms for **maximum scheme coverage**:

### Distribution by Organism
- **Salmonella enterica** (10 cases) - `senterica` scheme, 7 loci
- **Escherichia coli / Shigella** (10 cases) - `ecoli` scheme, 7 loci
- **Listeria monocytogenes** (8 cases) - `lmonocytogenes` scheme, 7 loci
- **Campylobacter jejuni** (5 cases) - `cjejuni` scheme, 7 loci
- **Klebsiella pneumoniae** (4 cases) - `kpneumoniae` scheme, 7 loci
- **Cronobacter sakazakii** (3 cases) - `cronobacter` scheme, 7 loci
- **Staphylococcus aureus** (3 cases) - `saureus` scheme, 7 loci
- **Enterococcus faecium** (2 cases) - `efaecium` scheme, 7 loci
- **Vibrio parahaemolyticus** (2 cases) - `vparahaemolyticus` scheme, 8 loci
- **Bacillus cereus** (2 cases) - `bcereus` scheme, 7 loci
- **Yersinia enterocolitica** (1 case) - `yenterocolitica` scheme, 7 loci

### Target Coverage
- **Common STs** (70% of cases) - Dominant clones, positive controls
- **Rare/novel STs** (20% of cases) - Scheme breadth, novel allele detection
- **Edge cases** (10% of cases) - Poor assemblies, incomplete loci, scheme ambiguity

## Validation Focus

### Core MLST Functionality
1. **Scheme detection** - Auto-detect correct scheme from species
2. **Allele calling** - Match alleles against PubMLST database
3. **ST assignment** - Assign correct ST from allele profile
4. **Novel allele handling** - Report novel alleles appropriately
5. **Missing loci handling** - Report incomplete typing when loci missing

### Quality Metrics
- **Complete typing** - All 7 loci successfully typed (preferred outcome)
- **Partial typing** - Some loci typed, some missing (acceptable for poor assemblies)
- **Failed typing** - No loci typed or wrong scheme detected (FAIL)

## Ground Truth Schema

```json
{
  "organism": "string - Full organism name",
  "ground_truth": {
    "mlst": {
      "scheme": "string - MLST scheme name (e.g., 'ecoli', 'senterica', 'lmonocytogenes')",
      "sequence_type": "string or null - Expected ST (e.g., '131', 'novel')",
      "expected_alleles": {
        "locus1": "string or null - Expected allele number (optional for validation)",
        "locus2": "string or null"
      },
      "notes": "string or null - Context (e.g., 'novel allele at aroC', 'single-locus variant of ST19')"
    }
  },
  "data_sources": {
    "assembly": {
      "accession": "string - GenBank/RefSeq assembly accession",
      "download_cmd": "string - Command to download assembly"
    }
  },
  "tools": {
    "mlst": {
      "input_type": "assembly",
      "run_cmd": "mlst --scheme <scheme> data/contigs.fa > actual/mlst/mlst_report.tsv",
      "reference_output": "expected/mlst/mlst_report.tsv"
    },
    "stringMLST": {
      "input_type": "assembly",
      "run_cmd": "stringMLST.py -p -P <profile> -k <alleles> -o actual/stringmlst/ data/contigs.fa",
      "reference_output": "expected/stringmlst/output.txt"
    }
  },
  "validation_instructions": {
    "mlst": "string - Detailed acceptance criteria for this test case"
  },
  "difficulty": "string - common|challenging|edge_case",
  "assembly_quality": {
    "n50": "integer - N50 in bp",
    "num_contigs": "integer - Number of contigs",
    "completeness": "string - complete|scaffold|draft"
  }
}
```

## Validation Logic

### PASS Criteria
- Correct scheme detected (if auto-detection used)
- ST matches ground truth exactly
- All 7 loci successfully typed (no `-` in output)

### PARTIAL Criteria
- Correct scheme but ST is single-locus variant (SLV) of expected ST
- Novel alleles detected but ST assigned (e.g., `ST19(novel aroC allele)`)
- Missing 1-2 loci due to assembly gaps, but remaining loci match expected profile

### FAIL Criteria
- Wrong scheme detected
- Wrong ST (>1 allele difference from expected)
- Failed to detect ≥3 loci (indicates poor assembly or wrong scheme)
- Reported "contamination" or "mixed ST profiles"

### Known Tool Issues
- **mlst (Seemann):** Conservative; reports `-` for ST if any locus missing. Auto-detection relies on species name in assembly.
- **stringMLST:** Requires manual scheme specification. Better at detecting novel alleles from reads.
- Poor assembly quality (#contigs >500, N50 <10kb) often causes locus dropout.
- Incomplete schemes in database may cause issues with rare organisms.

## Target Organisms and Priority STs

### Salmonella enterica (`senterica` scheme) - 10 cases
See `salmonella/config/typing_systems/mlst.md` for full list.
- **ST19** (critical) - Typhimurium
- **ST11** (critical) - Enteritidis
- **ST34** (high) - Monophasic Typhimurium (SLV of ST19)
- **ST45** (high) - Newport
- **Novel/rare ST** (low)

### Escherichia coli (`ecoli` scheme) - 10 cases
See `ecoli/config/typing_systems/mlst.md` for details (to be created).
- **ST131** (critical) - Pandemic ExPEC, fluoroquinolone-resistant
- **ST11** (critical) - O157:H7 STEC
- **ST95** (high) - ExPEC, neonatal meningitis
- **ST73** (high) - ExPEC, UTIs
- **ST10** (medium) - Commensal

### Listeria monocytogenes (`lmonocytogenes` scheme) - 8 cases
See `listeria/config/typing_systems/mlst.md` for details (to be created).
- **ST1** (critical) - Serotype 1/2b, hypervirulent
- **ST2** (critical) - Serotype 4b, epidemic clone
- **ST5** (critical) - Serotype 1/2a, environmental
- **ST6** (high) - Serotype 4b
- **ST121** (high) - Serotype 1/2a, hypervirulent

### Campylobacter jejuni (`cjejuni` scheme) - 5 cases
- **ST21** (critical) - Most common globally
- **ST45** (high) - Clinical isolates
- **ST50** (high) - Outbreak-associated
- **ST257** (medium) - Emerging

### Klebsiella pneumoniae (`kpneumoniae` scheme) - 4 cases
- **ST258** (critical) - KPC-producing, pandemic clone
- **ST11** (critical) - Carbapenem-resistant
- **ST147** (high) - MDR clone
- **ST15** (medium) - Common clinical

### Other Organisms - 13 cases distributed
(Cronobacter, Staph, Enterococcus, Vibrio, Bacillus, Yersinia - see MLST.md target list)

## Discovery Parameters

### NCBI Search Strategy
**Primary:** Query by organism + ST in BioSample attributes
```
<organism>[Organism] AND <ST>[Attribute]
```

**Fallback:** Download high-quality assemblies, run mlst tool to determine ST

### Quality Filters
**Require:**
- Assembly available (MLST requires assembly, not reads)
- Species clearly identified

**Prefer:**
- Complete or chromosome-level assemblies
- N50 > 20kb, <300 contigs
- ST annotated in metadata

**Accept:**
- Draft assemblies (N50 > 10kb)
- Unknown ST (will be determined by tool)

**Exclude:**
- Contaminated assemblies
- N50 < 5kb or >1000 contigs
- Wrong species

## Tool Command Examples

### mlst (auto-detect scheme)
```bash
mlst data/contigs.fa > actual/mlst/mlst_report.tsv
```

Output format:
```
contigs.fa	senterica	19	aroC(10)	dnaN(5)	hemD(12)	hisD(9)	purE(5)	sucA(9)	thrA(2)
```

### mlst (specify scheme)
```bash
mlst --scheme ecoli data/contigs.fa > actual/mlst/mlst_report.tsv
```

### stringMLST
```bash
stringMLST.py -p -P /path/to/pubmlst/ecoli/profile.txt \
  -k /path/to/pubmlst/ecoli/alleles/ \
  -o actual/stringmlst/ data/contigs.fa
```

## Validation Instructions Template

Example for E. coli ST131:
```
Expected ST131 (E. coli scheme). This is the pandemic ExPEC clone associated with 
fluoroquinolone resistance. Tool must use 'ecoli' scheme and report ST131 with all 
7 loci typed: adk, fumC, gyrB, icd, mdh, purA, recA. Accept exact ST131 match. 
Also accept as PARTIAL any single-locus variant (e.g., ST1193 which differs at fumC). 
Novel alleles at any locus should be flagged for review.
```

Example for novel ST:
```
Expected novel ST or rare ST (Salmonella senterica scheme). Tool must use 'senterica' 
scheme and report a valid ST assignment. Accept any valid ST as PASS. If tool reports 
novel alleles not in PubMLST database, this is acceptable - flag for manual ST submission. 
Do NOT accept '-' (missing ST) unless ≥2 loci are missing from assembly (indicates poor quality).
```

## Use Cases

### Use Case 1: Tool Installation Validation
Run all 50 cases to confirm mlst tool correctly installed with PubMLST schemes.

### Use Case 2: Scheme Coverage Testing
Ensure tool supports all relevant schemes for your lab's organisms.

### Use Case 3: Benchmark Across Tools
Compare mlst vs stringMLST performance on same isolates.

### Use Case 4: Assembly Quality Impact
Use cases with varied assembly quality (complete vs draft) to assess tool robustness.

## Notes

- This manifest is organism-agnostic - focuses on MLST tool validation, not organism-specific biology
- Cross-references organism-specific manifests for biological context (serotype-ST correlations)
- PubMLST database is canonical source; schemes and alleles periodically updated
- Some STs are single-locus variants (SLV) of others; these relationships are important for validation
- MLST is less discriminatory than cgMLST/SNP analysis for outbreak investigation but useful for clonal complex assignment
- Tools must handle novel alleles gracefully (report them, don't fail)
