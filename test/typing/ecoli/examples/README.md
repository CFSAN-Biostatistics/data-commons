# E. coli Example Manifests

## ⚠️ IMPORTANT WARNING ⚠️

**These example manifests contain PLACEHOLDER accessions that are NOT real NCBI records.**

Do NOT use these files for actual tool validation without first replacing all accession numbers with verified real accessions from NCBI.

## Files

- `ecoli_o157h7_example.json` - Template for O157:H7 (ST11) manifests
- `ecoli_st131_example.json` - Template for ST131 (O25:H4) manifests

## Purpose

These files demonstrate:
- ✅ Correct manifest JSON schema
- ✅ Required fields and structure
- ✅ Ground truth format
- ✅ Tool configuration format
- ✅ Validation instruction format

These files do NOT provide:
- ❌ Real NCBI accessions
- ❌ Verified organism data
- ❌ Downloadable read/assembly files

## How to Find Real Accessions

### Method 1: Use NCBI BioSample Web Search

**For E. coli O157:H7:**
1. Go to: https://www.ncbi.nlm.nih.gov/biosample/
2. Search: `"Escherichia coli"[Organism] AND "O157:H7"[All Fields]`
3. Filter: Click "With SRA links" and "With Assembly links"
4. Select a high-quality isolate
5. Extract accessions:
   - BioSample: SAMN######## (on BioSample page)
   - SRA: Click "SRA" link → SRR#######
   - Assembly: Click "Assembly" link → GCA_#########.#

**For E. coli ST131:**
1. Search: `"Escherichia coli"[Organism] AND ("ST131"[All Fields] OR "O25:H4"[All Fields])`
2. Follow same steps as above

### Method 2: Use Discovery Script

```bash
cd ../../  # Go to test/typing/
python3 scripts/find_real_accessions.py
```

This will search NCBI and output verified accessions.

### Method 3: Copy from Literature

Many E. coli studies publish BioSample/SRA accessions. Search:
- PubMed for "Escherichia coli O157:H7 whole genome sequencing"
- Look for Data Availability sections
- Extract BioProject/BioSample accessions

## Replacement Checklist

Before using an example manifest:

- [ ] Replace `PLACEHOLDER_SAMN_*` with real BioSample accession
- [ ] Replace `PLACEHOLDER_SRR_*` with real SRA run accession
- [ ] Replace `PLACEHOLDER_GCA_*` with real Assembly accession
- [ ] Update `curation.date` to current date
- [ ] Verify organism name matches BioSample
- [ ] Verify serotype/MLST match expected ground truth
- [ ] Update `curation.notes` with any relevant information
- [ ] Test download commands actually work

## Reference

See `test/typing/salmonella/` for 111 examples of real, verified manifests with actual NCBI accessions.
