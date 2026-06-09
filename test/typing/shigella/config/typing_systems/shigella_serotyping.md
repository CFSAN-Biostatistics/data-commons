# Shigella Serotyping and Species Identification

## Overview

Shigella is a genetically diverse genus causing bacillary dysentery (shigellosis). It comprises four species based on serological and biochemical properties:
- **S. dysenteriae** (serogroup A) - 15 serotypes, includes Sd1 (epidemic dysentery)
- **S. flexneri** (serogroup B) - 19 serotypes/subserotypes, most common globally
- **S. boydii** (serogroup C) - 20 serotypes
- **S. sonnei** (serogroup D) - Single serotype, most common in developed countries

**Note:** Shigella is genetically E. coli (same species), distinguished by:
- **ipaH gene** - Invasion plasmid antigen H (species marker, multiple copies)
- Loss of motility (fliC deletion/disruption)
- Lactose non-fermenting (lacZ mutation)
- Chromosomal virulence genes (ipa, ics)

In-silico tools use:
- **ipaH presence** for Shigella vs E. coli distinction
- **O antigen typing** for serogroup/serotype
- **Phylogenetic placement** for species-level ID

## Selection Strategy

Target **15 test cases** covering:
- **S. sonnei** (4 cases) - Dominant in developed countries, clonal
- **S. flexneri** (6 cases) - Most diverse, multiple serotypes
- **S. dysenteriae** (2 cases) - Includes Sd1 (epidemic)
- **S. boydii** (2 cases) - Rare, declining prevalence
- **Edge cases** (1 case) - E. coli/Shigella boundary, atypical

## Target Serotypes

### S. sonnei (4 cases)

- **S. sonnei** (priority: critical) - Single serotype, most common in US/Europe, highly clonal
- **S. sonnei (MDR)** (priority: high) - Multidrug-resistant clone
- **S. sonnei (MSM-associated)** (priority: high) - Men-who-have-sex-with-men outbreak lineage
- **S. sonnei (travel-associated)** (priority: medium) - Imported cases

### S. flexneri (6 cases)

- **S. flexneri 2a** (priority: critical) - Most common S. flexneri serotype globally
- **S. flexneri 3a** (priority: high) - Second most common
- **S. flexneri 6** (priority: high) - Emerging serotype
- **S. flexneri 1b** (priority: medium) - Common in endemic regions
- **S. flexneri 2b** (priority: medium) - Less common subserotype
- **S. flexneri X variant** (priority: low) - Untypeable variant for edge case

### S. dysenteriae (2 cases)

- **S. dysenteriae type 1 (Sd1)** (priority: critical) - Epidemic dysentery, produces Shiga toxin (stx)
- **S. dysenteriae type 2** (priority: medium) - Less virulent, non-stx

### S. boydii (2 cases)

- **S. boydii serotype 1** (priority: medium) - Rare, declining
- **S. boydii serotype 14** (priority: low) - Very rare

### Edge Cases (1 case)

- **EIEC (Enteroinvasive E. coli)** (priority: low) - ipaH+, but retains E. coli characteristics (motile, lactose+)

## Discovery Parameters

### NCBI Search Strategy

**Primary queries:**
```
Shigella sonnei[Organism]
Shigella flexneri[Organism] AND <serotype>[All Fields]
Shigella dysenteriae[Organism]
Shigella boydii[Organism]
```

**Metadata extraction:**
- Organism name: `Shigella sonnei`, `Shigella flexneri serotype 2a`
- BioSample attributes: `serotype`, `serovar`, `serogroup`
- Strain names often encode serotype: `Sf2a`, `Sd1`

**Fallback:**
- Search Shigella genus, run ShigaTyper/ipaH detection
- Use phylogenetic tools (Mash, ANI) to confirm species

### Quality Filters

**Require:**
- Assembly available (serotyping tools need O antigen gene clusters)
- Reads available (ShigaTyper works on reads)

**Prefer:**
- Complete genomes (ipaH is plasmid-borne; complete assemblies capture plasmid)
- Metadata with confirmed serotype
- Curated RefSeq assemblies

**Accept:**
- Draft assemblies if high quality
- Species inferred from phylogeny if serotype unknown

**Exclude:**
- E. coli misannotated as Shigella (check metadata carefully)
- Poor quality assemblies
- Contaminated samples

## Ground Truth Schema

```json
"ground_truth": {
  "species_confirmation": {
    "species": "string - Species (e.g., 'Shigella sonnei', 'Shigella flexneri')",
    "ipaH_present": "boolean - Expected ipaH gene presence (true for Shigella)",
    "notes": "string - Optional context (e.g., 'EIEC, not true Shigella')"
  },
  "serological": {
    "serotype": "string or null - Full serotype (e.g., 'S. sonnei', 'S. flexneri 2a', 'Sd1')",
    "serogroup": "string - Serogroup (A, B, C, D)",
    "o_antigen": "string or null - Underlying O antigen equivalent"
  }
}
```

## Validation Logic

### PASS Criteria
- Tool correctly identifies Shigella species
- Serotype matches ground truth (exact match for S. flexneri subserotypes)
- ipaH detected (if tool checks for it)

### PARTIAL Criteria
- Correct species but serotype not resolved (e.g., "S. flexneri" without subserotype)
- Serogroup correct but subserotype wrong (e.g., S. flexneri 2a vs 2b)

### FAIL Criteria
- Wrong species (S. flexneri called as S. sonnei)
- ipaH not detected (critical species marker)
- Misidentified as E. coli when it is Shigella

### Known Tool Issues
- **ShigaTyper:** Reliable for ipaH detection; serotype prediction depends on read quality
- **SerotypeFinder:** Designed for E. coli; may detect underlying O antigen but not Shigella-specific serotypes
- **ipaH gene:** Present in multiple copies (chromosomal and plasmid); even draft assemblies should detect it
- S. flexneri serotypes are complex (numbered + lettered subtypes); some tools only report base serotype

## Tool Configurations

### ShigaTyper
```bash
shigatyper --R1 data/reads_1.fq.gz --R2 data/reads_2.fq.gz --name shigella > actual/shigatyper/result.tsv
```

Output: Species, serotype, ipaH prediction, stx prediction

### ipaH detection (custom)
```bash
blastn -query ipaH.fasta -subject data/contigs.fa -outfmt 6 > actual/ipah_blast.tsv
```

### MLST (E. coli scheme)
```bash
mlst --scheme ecoli data/contigs.fa > actual/mlst/mlst_report.tsv
```
Note: Many labs use E. coli MLST for Shigella (same species).

### Mash/ANI (species confirmation)
```bash
mash dist -s 1000 shigella_reference.fna data/contigs.fa > actual/mash_dist.tsv
```

## Validation Instructions Template

Example for S. sonnei:
```
Expected species: Shigella sonnei (serogroup D). Tool must detect ipaH gene (invasion plasmid 
marker). S. sonnei is monomorphic (single serotype), so any S. sonnei identification is PASS. 
Accept 'Shigella sonnei', 'S. sonnei', or 'serogroup D'. Do not accept E. coli unless tool 
notes 'Shigella-like' or 'EIEC'.
```

Example for S. flexneri 2a:
```
Expected species: Shigella flexneri serotype 2a (serogroup B). Tool must detect ipaH gene. 
Accept exact match 'S. flexneri 2a', 'Shigella flexneri 2a', or 'serotype 2a'. Accept 'S. 
flexneri' without subserotype as PARTIAL (species correct but incomplete typing). Do not 
accept other subserotypes (2b, 3a, etc.) as PASS - those are distinct serotypes.
```

Example for S. dysenteriae type 1:
```
Expected species: Shigella dysenteriae type 1 (Sd1, serogroup A). This is the epidemic 
dysentery strain and produces Shiga toxin (stx gene expected). Tool must detect ipaH and 
should note stx presence. Accept 'S. dysenteriae type 1', 'Sd1', 'S. dysenteriae 1'. 
This is distinct from other S. dysenteriae types.
```

## Cross-References

- **MLST**: S. sonnei is clonal (mostly ST152); S. flexneri is diverse (multiple STs)
- **Virulence**: ipaH is species marker; S. dysenteriae type 1 has stx
- **E. coli boundary**: EIEC (enteroinvasive E. coli) is ipaH+ but retains motility and lactose fermentation

## Notes

- Shigella is paraphyletic E. coli - genetically indistinguishable at species level
- ipaH gene is THE molecular marker for Shigella; without it, it's just E. coli
- Serotyping is historically based on O antigen; modern WGS tools may use O antigen + genetic context
- S. sonnei is highly clonal (single lineage worldwide); S. flexneri is highly diverse
- S. dysenteriae type 1 (Sd1) is the only Shigella producing Shiga toxin (stx gene)
- Some tools report underlying E. coli O antigen equivalents (S. sonnei = O-antigen equivalent, but specific typing differs)
- Traditional serology vs in-silico serotyping may differ due to genetic vs phenotypic basis
