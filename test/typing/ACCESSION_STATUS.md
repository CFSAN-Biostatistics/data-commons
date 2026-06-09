# Accession Status for Typing Manifests

**Created:** 2026-06-08  
**Status:** TEMPLATE MANIFESTS - ACCESSIONS NOT YET VERIFIED

## Issue

The example manifest JSON files created in this session contain **placeholder/template accession numbers** that are **NOT real NCBI accessions**. These were created to demonstrate the manifest structure and schema, but they have not been verified against NCBI databases.

## Affected Files

All example manifest files in:
- `test/typing/ecoli/examples/` (2 files)
- `test/typing/shigella/examples/` (2 files)
- `test/typing/listeria/examples/` (2 files)

**Total:** 6 example manifest files with unverified placeholder accessions

## Placeholder Accessions Used

### E. coli Examples
- **ecoli_o157h7_example.json**
  - BioSample: `SAMN02603001` (placeholder)
  - SRA: `SRR1234567` (placeholder)
  - Assembly: `GCA_000123456.1` (placeholder)
  - Target: O157:H7, ST11

- **ecoli_st131_example.json**
  - BioSample: `SAMN02603002` (placeholder)
  - SRA: `SRR2345678` (placeholder)
  - Assembly: `GCA_000234567.1` (placeholder)
  - Target: O25:H4, ST131

### Shigella Examples
- **shigella_sonnei_example.json**
  - BioSample: `SAMN03601001` (placeholder)
  - SRA: `SRR3456789` (placeholder)
  - Assembly: `GCA_000345678.1` (placeholder)
  - Target: S. sonnei, ST152

- **shigella_flexneri_example.json**
  - BioSample: `SAMN03602001` (placeholder)
  - SRA: `SRR4567890` (placeholder)
  - Assembly: `GCA_000456789.1` (placeholder)
  - Target: S. flexneri 2a, ST245

### Listeria Examples
- **listeria_4b_example.json**
  - BioSample: `SAMN04701001` (placeholder)
  - SRA: `SRR5678901` (placeholder)
  - Assembly: `GCA_000567890.1` (placeholder)
  - Target: Serotype 4b, ST2

- **listeria_1-2a_example.json**
  - BioSample: `SAMN04702001` (placeholder)
  - SRA: `SRR6789012` (placeholder)
  - Assembly: `GCA_000678901.1` (placeholder)
  - Target: Serotype 1/2a, ST5

## Why Placeholders Were Used

1. **Demonstration Purpose**: These examples were created to show the manifest schema and structure
2. **Search Complexity**: Finding real accessions requires:
   - NCBI Entrez queries with specific serotype/MLST filters
   - Verification that accessions have both reads and assemblies
   - Confirmation of metadata quality
   - Manual curation to ensure characteristics match
3. **Time Constraints**: Exhaustive NCBI searches with rate limiting would require significant time

## Solutions

### Option 1: Use Provided Discovery Script (Recommended)

A script has been created to search NCBI for real accessions:

```bash
cd test/typing
python3 scripts/find_real_accessions.py
```

This script will:
- Search NCBI BioSample for organisms matching target characteristics
- Verify linked SRA and Assembly accessions
- Output verified accessions in JSON format
- Respect NCBI API rate limits

**Note:** This script requires network access and ~5-10 minutes to run.

### Option 2: Use Salmonella Manifests as Reference

The Salmonella directory contains **111 real, verified manifests** with actual NCBI accessions:

```bash
ls test/typing/salmonella/sal_*/manifest.json
```

These can serve as:
- Templates for manifest structure
- Examples of real accession formatting
- Validation reference

### Option 3: Manual NCBI Search

For each target (e.g., E. coli O157:H7 ST11):

1. **Search NCBI BioSample:**
   ```
   https://www.ncbi.nlm.nih.gov/biosample/?term="Escherichia+coli"[Organism]+AND+"O157:H7"[All+Fields]+AND+has_sra[filter]
   ```

2. **Verify characteristics:**
   - Check serotype in BioSample attributes
   - Check MLST/ST if annotated
   - Verify SRA and Assembly links exist

3. **Extract accessions:**
   - BioSample: SAMN########
   - SRA: Click through to SRA, get SRR#######
   - Assembly: Click through to Assembly, get GCA_#########

4. **Update manifest JSON** with real accessions

### Option 4: Mark as Template and Defer

Keep example files as **templates** with placeholder accessions clearly marked:

```json
{
  "_template": true,
  "_note": "TEMPLATE ONLY - Replace accessions with real NCBI accessions",
  "organism": "Escherichia coli",
  ...
}
```

Users implementing the manifest should replace placeholders before use.

## Recommendation

**For immediate use:**
- Treat example manifests as **schema templates only**
- Do NOT use placeholder accessions for actual tool validation
- Reference Salmonella manifests for real accession examples

**For production use:**
- Run `scripts/find_real_accessions.py` to populate with real accessions
- OR manually curate accessions from NCBI BioSample
- Verify each accession resolves correctly before use

## Verification Checklist

Before using a manifest for tool validation, verify:

- [ ] BioSample accession exists in NCBI
- [ ] BioSample organism matches expected species
- [ ] Serotype/MLST metadata matches ground truth (if available)
- [ ] SRA accession exists and is linked to BioSample
- [ ] Assembly accession exists and is linked to BioSample
- [ ] Download commands execute successfully
- [ ] Quality metrics are acceptable (coverage, N50, etc.)

## Status by Organism

| Organism | Example Manifests | Accessions Status | Action Needed |
|----------|-------------------|-------------------|---------------|
| Salmonella | 111 real manifests | ✅ VERIFIED | None - use as reference |
| E. coli | 2 templates | ❌ PLACEHOLDER | Search/verify real accessions |
| Shigella | 2 templates | ❌ PLACEHOLDER | Search/verify real accessions |
| Listeria | 2 templates | ❌ PLACEHOLDER | Search/verify real accessions |

## Next Steps

1. **Immediate:** Add prominent warning to example manifest files
2. **Short-term:** Run discovery script to find real accessions for 6 examples
3. **Long-term:** Implement full case discovery as described in typing system documentation (20+ cases per organism)

## Notes

- The **typing system documentation** (`.md files in config/typing_systems/`) is valid and complete
- The **manifest schema** demonstrated in examples is correct
- Only the **specific accession values** are placeholders
- The **discovery strategy** documented in each typing system `.md` file provides the correct approach for finding real accessions
