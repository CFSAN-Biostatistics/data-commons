# AMR Test Suite Expansion Guide

This guide enables AI agents and developers to add new AMR detection systems and test cases to the suite.

## Overview

The test suite validates AMR detection tools by comparing their output against curated ground truth. Adding a new tool or organism requires:
1. Creating an AMR system documentation file
2. Adding tool configuration to manifest.json for relevant cases
3. Optionally extending discovery and validation scripts

## Adding a New AMR Detection Tool

### Step 1: Create Tool Documentation

Create `config/amr_systems/{tool_name}.md` with:

**## Overview**
- What databases does this tool use?
- What resistance mechanisms does it detect? (acquired genes, point mutations, both)
- What input types does it accept? (reads, assembly, protein)
- What output format does it produce?

**## Selection Strategy**
- How many test cases needed for full coverage?
- What AMR profiles to prioritize?
- Known tool limitations or edge cases to test

**## Target List**
```markdown
### Susceptible Controls (3-5 cases)
- **fully_susceptible** (priority: critical) - True negative; any hit = false positive

### Single Resistance (2-3 per drug class)
- **beta_lactam_only** (priority: high) - blaOXA or similar, no other resistance

### Multi-Drug Resistance (5+ cases)
- **amp_tet** (priority: high) - Beta-lactam + tetracycline combination
- **mdr** (priority: high) - 3+ drug classes

### Edge Cases (3-5 cases)
- **truncated_gene** (priority: medium) - Gene at contig boundary
- **novel_variant** (priority: medium) - Gene below default identity threshold
- **borderline_identity** (priority: medium) - Gene at 80-85% identity
```

**## Ground Truth Schema**
```json
"ground_truth": {
  "amr": {
    "phenotype_summary": "AMP_TET",
    "resistant_phenotypes": {
      "ampicillin": {"amr_resistant": true, "genes": ["blaOXA-61"], "amr_class": "beta-lactam"}
    },
    "detected_genes": ["blaOXA-61", "tet(O)"],
    "amr_database_evidence": {"source": "ResFinder v4.6.0"}
  }
}
```

**## Validation Logic**
- PASS: All expected genes/phenotypes detected within identity/coverage thresholds
- PARTIAL: Expected drug classes detected but not all individual gene variants
- FAIL: Major resistance determinants missed, or false positives in susceptible control

**## Tool Configuration**
```json
"ToolName": {
  "input_type": "assembly",
  "version_min": "X.Y.Z",
  "run_cmd": "tool_command --input data/contigs.fa --output actual/toolname/",
  "reference_output": "expected/toolname/output.json"
}
```

### Step 2: Add lib/output_parsers.py Parser

Add a `parse_toolname_<format>(path)` function to `scripts/lib/output_parsers.py`:

```python
def parse_toolname_tsv(path: Path) -> Dict:
    """Parse ToolName TSV output. Returns normalized gene/phenotype structure."""
    # ...
```

Register it in `TOOL_PARSERS` in `scripts/validate.py`.

### Step 3: Add to Existing Manifests

For each existing test case, add the new tool's configuration:
```json
"tools": {
  "ExistingTool": {...},
  "NewTool": {
    "input_type": "assembly",
    "version_min": "X.Y.Z",
    "run_cmd": "...",
    "reference_output": "expected/newtool/output.tsv"
  }
}
```

And add validation instructions:
```json
"validation_instructions": {
  "newtool": "Expect hits for blaOXA-61 and tet(O). PASS if both drug classes detected..."
}
```

## Adding a New Organism

1. Create `../<organism>/` directory (e.g., `../salmonella/`)
2. Copy this `campylobacter/` structure
3. Update `find_test_cases()` in `download.sh` and `run.sh` to glob the new organism prefix
4. Create organism-specific typing system config in `config/amr_systems/`
5. Add organism to top-level `../README.md` registry table

## Case Naming Convention

`<orgcode>_<species>_<amrprofile>_<strain_or_SRR>/`

AMR profile tokens:
- `sus` — fully susceptible
- `amp` — ampicillin/beta-lactam
- `tet` — tetracycline
- `cip` — ciprofloxacin/fluoroquinolone
- `gen` — gentamicin/aminoglycoside
- `col` — colistin
- `mdr` — 3+ drug classes
- `novel_var` — novel gene variant edge case
- `truncated` — truncated gene edge case

Examples:
- `campy_jejuni_sus_NCTC11351`
- `campy_jejuni_amp_tet_UCLA1626`
- `sal_typhimurium_amp_tet_cip_SRR3372431`

## Ground Truth Sources

Priority order:
1. **NCBI BioSample antibiogram attributes** — MIC-based phenotypic data linked to WGS
2. **NARMS (National Antimicrobial Resistance Monitoring System)** — FDA-curated surveillance data
3. **Published literature** — peer-reviewed AMR profiles with accession links
4. **Tool-bootstrapped** — run reference tools, treat output as ground truth (flag confidence as "bootstrapped")

Always record the source and version in `curation.amr_evidence`.

## Validation Best Practices

- Be specific about identity/coverage thresholds in `validation_instructions`
- Document known tool quirks (e.g., "AMRFinderPlus uses NCBI gene names, not ResFinder names")
- Include context for edge cases ("OXA-61 and OXA-193 differ by 2 aa — some tools collapse to OXA-61")
- Test susceptible controls first to establish specificity baseline
