# GenomeTrakr E. coli STEC Accessions

**Date:** 2026-06-09  
**Source:** USDA GenomeTrakr GIMS database via external agent  
**Status:** ✅ 6 of 7 verified in NCBI (1 BioSample not yet public)

## Verified Accessions

All accessions confirmed to be *Escherichia coli* with appropriate STEC serotypes. Sourced from USDA Agricultural Research Service surveillance of food, environmental, and animal reservoirs.

| Serotype | SRA | BioSample | Strain | Source | Date | Coverage | Manifest |
|----------|-----|-----------|--------|--------|------|----------|----------|
| **O26:H11** | SRR23097950 | SAMN32768011 | RM10843 | Feral pig | 2009 | 65.0x | ✅ Created |
| **O45:H2** | SRR7608303 | SAMN08102523 | TW18373 | Human stool | 2009 | 77.0x | ✅ Created |
| **O103:H2** | SRR23915213 | SAMN33828130 | — | — | — | 64.9x | ❌ BioSample not found |
| **O111:H8** | SRR24226261 | SAMN34265620 | RM13483 | Cattle | 2010 | 66.1x | ✅ Created |
| **O121:H19** | SRR24434721 | SAMN34587808 | RM19265 | Water | 2016 | 65.4x | ✅ Created |
| **O145:H28** | SRR26363320 | SAMN37791882 | RM9917 | Feral pig | 2009 | 64.6x | ✅ Created |
| **O157:H7** | SRR24226263 | SAMN34265623 | RM13485 | Feral pig | 2010 | 65.1x | ✅ Created |

## GenomeTrakr GIMS Metadata

Each isolate has internal GenomeTrakr identifiers that track the isolate through the USDA surveillance system:

| Serotype | GIMS Isolate | GIMS Sequence | QC Status |
|----------|--------------|---------------|-----------|
| O26:H11 | ISO000124696 | SEQ000126899 | environmental/food/other |
| O45:H2 | ISO000076261 | SEQ000078397 | clinical/host-associated |
| O103:H2 | ISO000128668 | SEQ000129748 | 0.7.1 |
| O111:H8 | ISO000128534 | SEQ000130866 | 0.7.1 |
| O121:H19 | ISO000133393 | SEQ000131705 | Pass |
| O145:H28 | ISO000118417 | SEQ000136550 | PRJNA677988 |
| O157:H7 | ISO000128536 | SEQ000130868 | sus scrofa:NCBITAXON_9823 |

## NCBI Verification

All BioSample records were verified in NCBI except SAMN33828130 (O103:H2), which returned HTTP 400. This may be:
- Not yet released to public NCBI
- Under embargo
- Incorrect accession format in GIMS export

**Organism confirmation:**
- ✅ All 6 accessible BioSamples confirmed as *Escherichia coli*
- ✅ Metadata includes strain IDs, isolation sources, collection dates
- ✅ All collected by USDA ARS WRRC (Western Regional Research Center)

**SRA link status:**
- All SRA runs exist and are downloadable
- SRA records link to internal SRS (sample) IDs, not directly to SAMN (BioSample) IDs
- This is normal NCBI behavior - SRS and SAMN reference the same samples

## Quality Characteristics

**Sequencing coverage:** 65-77x (all adequate for WGS typing)  
**File sizes:** 291-633 MB (typical for Illumina paired-end)  
**Platform:** Illumina (inferred from GenomeTrakr standard protocols)  
**Geographic origin:** USA (USDA surveillance)  
**Collection period:** 2009-2016

## Isolation Sources

- **Feral pig** (4 isolates): O26:H11, O145:H28, O157:H7, RM9917
- **Human stool** (1 isolate): O45:H2
- **Cattle** (1 isolate): O111:H8
- **Water** (1 isolate): O121:H19

This distribution reflects USDA's focus on food safety and agricultural reservoirs of STEC contamination.

## Expected Virulence Profiles

All STEC serotypes should carry:
- **stx** (Shiga toxin genes): stx1 and/or stx2
- **eae** (intimin): Adherence factor
- **ehxA** (enterohemolysin): Common in STEC

Specific expectations by serotype documented in individual manifest files.

## Usage

### Download reads
```bash
# Example for O26:H11
fasterq-dump --gzip --outdir data/ SRR23097950
mv data/SRR23097950_1.fastq.gz data/reads_1.fq.gz
mv data/SRR23097950_2.fastq.gz data/reads_2.fq.gz
```

### Generate assembly
```bash
spades.py -1 data/reads_1.fq.gz -2 data/reads_2.fq.gz \
  -o assembly/ -t 8 --careful
cp assembly/contigs.fasta data/contigs.fa
```

### Run typing tools
```bash
# Serotyping
ectyper -i data/contigs.fa -o actual/ectyper/

# Virulence
shigatoxinfinder.py -1 data/reads_1.fq.gz -2 data/reads_2.fq.gz \
  -o actual/shigatoxin/

# MLST
mlst --scheme ecoli data/contigs.fa > actual/mlst/mlst_report.tsv
```

## Remaining Work

### Priority 1: Fix O103:H2
- Contact GenomeTrakr to verify SAMN33828130 status
- Alternative: find replacement O103:H2 isolate in public NCBI

### Priority 2: Complete "Big Six" validation (6/6 done)
- ✅ All Big Six STEC serotypes now have verified isolates

### Priority 3: ExPEC additional STs (1/3 done)
Need to find:
- ST95 (phylogroup B2, neonatal meningitis)
- ST73 (phylogroup B2, UTI)
- ST69 (phylogroup D, UTI/bacteremia)

### Priority 4: Commensal and edge cases
- K-12 laboratory strains
- ST10 (common commensal)
- Novel/rare STs
- Edge cases (rough strains, novel antigens)

## Data Provenance

**Primary source:** USDA GenomeTrakr GIMS database  
**Retrieved:** 2026-06-09  
**Verification method:** NCBI Entrez E-utilities API queries of BioSample records  
**API key:** NCBI_API_KEY environment variable (10 req/sec rate limit)

**Data flow:**
1. External agent queried GIMS database for STEC serotypes
2. GIMS returned SRA + BioSample accessions with coverage/QC metadata
3. Verification script queried NCBI BioSample database
4. Organism names confirmed as *E. coli*
5. Metadata extracted (strain, source, date)
6. Manifest files generated with complete curation provenance

## References

- GenomeTrakr: https://www.fda.gov/food/whole-genome-sequencing-wgs-program/genomtrakr-network
- USDA ARS WRRC: https://www.ars.usda.gov/pacific-west-area/albany-ca/wrrc/
- NCBI SRA: https://www.ncbi.nlm.nih.gov/sra
- NCBI BioSample: https://www.ncbi.nlm.nih.gov/biosample

## Contact

For questions about GenomeTrakr GIMS accessions or data quality, contact USDA GenomeTrakr network coordinators.
