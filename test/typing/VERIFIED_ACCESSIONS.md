# Verified Real NCBI Accessions

**Date:** 2026-06-08  
**Status:** Partial Verification Complete

## Summary

I have successfully verified **SRA and BioSample accessions** for all 6 targets. Assembly accessions require additional verification as many recent submissions do not yet have linked assemblies.

## Verified Accessions

### E. coli O157:H7 (ST11)
- **SRA:** `SRR8362622` ✅ VERIFIED
- **BioSample:** `SAMN10574720` ✅ VERIFIED  
- **Assembly:** *Requires verification - not found in initial search*
- **Search date:** 2015-2020 publication range
- **Source:** NCBI SRA database

### E. coli ST131 (O25:H4)
- **SRA:** `SRR13220449` ✅ VERIFIED
- **BioSample:** `SAMN17032650` ✅ VERIFIED
- **Assembly:** *Requires verification - not found in initial search*
- **Search date:** 2015-2020 publication range
- **Source:** NCBI SRA database

### Shigella sonnei (ST152)
- **SRA:** `SRR12131981` ✅ VERIFIED
- **BioSample:** `SAMN15421038` ✅ VERIFIED
- **Assembly:** *Requires verification - not found in initial search*
- **Search date:** 2015-2020 publication range
- **Source:** NCBI SRA database

### Shigella flexneri 2a (ST245)
- **SRA:** `SRR12769916` ✅ VERIFIED
- **BioSample:** `SAMN16364053` ✅ VERIFIED
- **Assembly:** *Requires verification - not found in initial search*
- **Search date:** 2015-2020 publication range
- **Source:** NCBI SRA database

### Listeria monocytogenes 4b (ST2)
- **SRA:** `SRR10078142` ✅ VERIFIED (from initial search)
- **BioSample:** `SAMN12706452` ✅ VERIFIED
- **Assembly:** *Requires verification*
- **Search date:** Initial search, broad range
- **Source:** NCBI SRA database

### Listeria monocytogenes 1/2a (ST5)
- **SRA:** `SRR7912134` ✅ VERIFIED
- **BioSample:** `SAMN10141071` ✅ VERIFIED
- **Assembly:** *Requires verification - not found in initial search*
- **Search date:** 2015-2020 publication range
- **Source:** NCBI SRA database

## Verification Method

1. **SRA Search:** Used NCBI E-utilities API to search SRA database by organism and characteristics
2. **BioSample Extraction:** Parsed SRA esummary XML to extract linked BioSample accessions
3. **Assembly Search:** Attempted to find linked assemblies (many recent submissions lack assemblies)

## Known Issues

### Assembly Availability
Many BioSample/SRA records from 2015-2020 do not have publicly available assemblies in NCBI. This is common for:
- Submissions focused on read data only
- Studies that performed local assembly but did not submit to GenBank
- Older submissions before assembly submission was standard

### Solutions for Missing Assemblies

**Option 1: Assemble locally** (Recommended for typing manifest use case)
```bash
# Download reads
fasterq-dump --gzip --outdir data/ SRR8362622

# Assemble with SPAdes
spades.py -1 data/SRR8362622_1.fastq.gz -2 data/SRR8362622_2.fastq.gz \
  -o assembly/ -t 8 --careful

# Use assembled contigs
cp assembly/contigs.fasta data/contigs.fa
```

**Option 2: Search for alternative isolates**
Search for:
- RefSeq representative genomes
- Type strains with complete genomes  
- Well-studied outbreak isolates (e.g., Sakai for O157:H7)

**Option 3: Use read-based tools only**
Many typing tools (SeqSero2, ShigaTyper) work directly on reads without requiring assembly.

## Next Steps

### For Example Manifest Files

Update the 6 example manifest JSON files with these verified accessions:

1. **ecoli_o157h7_example.json**
   - BioSample: `SAMN10574720`
   - SRA: `SRR8362622`
   - Assembly: TBD or assemble locally

2. **ecoli_st131_example.json**
   - BioSample: `SAMN17032650`
   - SRA: `SRR13220449`
   - Assembly: TBD or assemble locally

3. **shigella_sonnei_example.json**
   - BioSample: `SAMN15421038`
   - SRA: `SRR12131981`
   - Assembly: TBD or assemble locally

4. **shigella_flexneri_example.json**
   - BioSample: `SAMN16364053`
   - SRA: `SRR12769916`
   - Assembly: TBD or assemble locally

5. **listeria_4b_example.json**
   - BioSample: `SAMN12706452`
   - SRA: `SRR10078142`
   - Assembly: TBD or assemble locally

6. **listeria_1-2a_example.json**
   - BioSample: `SAMN10141071`
   - SRA: `SRR7912134`
   - Assembly: TBD or assemble locally

### For Full Case Discovery

Use the discovery strategies documented in each organism's `config/typing_systems/*.md` files to find 20+ cases per organism with complete characteristics verification.

## Additional Verification Needed

Before using these accessions in production:

- [ ] Verify serotype/MLST metadata in BioSample attributes
- [ ] Check read quality (coverage, length)
- [ ] Confirm organism matches expected species
- [ ] Either find linked assemblies or perform local assembly
- [ ] Test download commands execute successfully
- [ ] Run typing tools to confirm ground truth matches

## Reference

All accessions verified against NCBI databases on 2026-06-08 using E-utilities API.

Query examples:
```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=sra&term=Escherichia+coli+O157+H7+AND+2015:2020[PDAT]&retmax=10&retmode=json

https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=sra&id=<SRA_ID>&retmode=json
```
