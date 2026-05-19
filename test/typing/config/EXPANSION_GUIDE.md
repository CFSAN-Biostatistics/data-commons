# Typing System Expansion Guide

This guide enables AI agents to add new microbial typing systems to the test suite.

## Overview

The test suite is designed to be extensible. Adding a new typing system requires:
1. Creating a typing system documentation file
2. Updating the manifest schema (ground_truth)
3. Optionally extending discovery/validation scripts

## Adding a New Typing System

### Step 1: Create Typing System Documentation

Create `config/typing_systems/{system_name}.md` with the following structure:

#### Required Sections

**## Overview**
- What does this typing system classify? (serological, genetic, functional)
- What biological markers does it use?
- Why is it important for surveillance/diagnostics?
- What tools perform this typing?

**## Selection Strategy**
- How many test cases total?
- What distribution? (common types, antigenic diversity, edge cases)
- Rationale for case selection

**## Target List**
Structured markdown with targets:
```markdown
### Category Name (N cases)

- **TypeName** (priority: critical|high|medium|low) - Description and rationale
- **TypeName2** (priority: ...) - ...
```

**## Discovery Parameters**
- NCBI search strategies (datasets, entrez queries)
- Metadata field names to extract (BioSample attributes, organism name patterns)
- Quality filters (coverage, assembly quality, submitter reputation)

**## Ground Truth Schema**
JSON schema snippet showing what fields belong in:
```json
"ground_truth": {
  "{system_name}": {
    "field1": "description",
    "field2": "description"
  }
}
```

**## Validation Logic**
- What constitutes PASS, PARTIAL, FAIL?
- Known tool issues or edge cases
- How to handle ambiguous results

**## Tool Configurations**
- Command-line invocations for relevant tools
- Input/output formats
- Version considerations

#### Optional Sections

- **Notes** - Historical context, nomenclature changes, versioning
- **Cross-References** - Links to other typing systems (e.g., cgMLST extends MLST)
- **Quality Thresholds** - Specific criteria for this typing system

### Step 2: Update Manifest Schema

Add new typing system to ground_truth structure in manifests:

```json
{
  "ground_truth": {
    "serological": {...},
    "mlst": {...},
    "new_system": {
      "field1": "value",
      "field2": "value"
    }
  },
  "validation_instructions": {
    "serological": "...",
    "mlst": "...",
    "new_system": "Validation instructions for this typing system..."
  }
}
```

Update `MANIFEST_SCHEMA.md` to document the new fields.

### Step 3: Extend Discovery Script (Optional)

If the new typing system requires specialized metadata extraction:

**Add parser to `lib/metadata_parser.py`:**
```python
@staticmethod
def extract_new_system_type(metadata: Dict) -> Tuple[Optional[str], List[Dict]]:
    """
    Extract typing information for new system.
    
    Returns:
        Tuple of (type_value, evidence_list)
    """
    evidence = []
    type_value = None
    
    # Search metadata fields
    if "attributes" in metadata:
        for field in ["new_type_field", "alternate_field"]:
            if field in metadata["attributes"]:
                value = metadata["attributes"][field]
                evidence.append({
                    "source": f"BioSample.Attributes.{field}",
                    "value": value
                })
                if not type_value:
                    type_value = value
    
    return type_value, evidence
```

**Add to `manifest_builder.py`:**
```python
# In create_manifest(), add ground truth for new system:
if new_system_type:
    manifest["ground_truth"]["new_system"] = {
        "type": new_system_type,
        # Additional fields...
    }
```

**Add to `discover_cases.py`:**
```python
# Add organism-specific discovery function
def discover_organism_new_system(
    target_type: str,
    datasets_client: DatasetsClient,
    entrez_client: EntrezClient,
    limit: int = 5
) -> List[Dict]:
    """Discover candidates for new typing system."""
    # Search strategy specific to this typing system
    pass
```

### Step 4: Update Validation (Optional)

If validation requires specialized logic beyond LLM:

**Update `validate.py`:**
```python
# Add typing system detection
if "new_system" in tool_name.lower():
    typing_system = "new_system"
```

Validation instructions in manifests should guide the LLM appropriately.

### Step 5: Document Tool Configurations

Add tool configs to manifests for new typing system:

```json
"tools": {
  "NewTypingTool": {
    "input_type": "reads|assembly|both",
    "run_cmd": "new_typing_tool --input data/contigs.fa --output actual/newtool/",
    "reference_output": "expected/newtool/result.tsv"
  }
}
```

## Examples

### Example 1: Adding cgMLST

Create `config/typing_systems/cgmlst.md`:
```markdown
# Core Genome MLST (cgMLST)

## Overview
Extension of MLST using hundreds to thousands of core genes...

## Selection Strategy
20 test cases across Listeria (10), Salmonella (5), E. coli (5)...

## Target List
### Listeria monocytogenes (10 cases)
- **CT1** (priority: critical) - Epidemic clone I...
```

Add to manifest:
```json
"ground_truth": {
  "cgmlst": {
    "scheme": "lmonocytogenes_cgmlst_v2",
    "cgmlst_type": "CT1",
    "allelic_distance_to_outbreak": 5
  }
}
```

### Example 2: Adding Virulence Profiling

Create `config/typing_systems/virulence.md`:
```markdown
# Virulence Factor Profiling

## Overview
Detects presence/absence of virulence genes...

## Target List
### Shiga toxin-producing E. coli (10 cases)
- **stx1+stx2+eae+** (priority: critical) - O157:H7 profile...
```

Add to manifest:
```json
"ground_truth": {
  "virulence": {
    "expected_genes": ["stx1", "stx2", "eae", "ehxA"],
    "expected_absent": ["inv", "ipa"],
    "pathotype": "STEC"
  }
}
```

## Best Practices

### Typing System Selection
- Choose systems used by your lab/organization
- Prioritize systems with clear ground truth
- Start with tools that have stable output formats

### Target Case Selection
- Balance common types (positive controls) vs rare types (coverage)
- Include known difficult cases
- Document WHY each case is included

### Validation Instructions
- Be specific about acceptance criteria
- Document known tool quirks
- Provide context for edge cases
- Include relevant synonyms or alternate notations

### Discovery Strategy
- Start with high-confidence metadata (RefSeq, curated databases)
- Accept diverse metadata sources for breadth
- Use confidence scoring to prioritize manual review

## Validation Across Typing Systems

Some test cases can validate multiple typing systems simultaneously:

```json
{
  "ground_truth": {
    "serological": {
      "serotype": "Typhimurium"
    },
    "mlst": {
      "sequence_type": "19"
    },
    "cgmlst": {
      "cgmlst_type": "CT1234"
    },
    "amr": {
      "expected_genes": ["aph(3')-Ia", "sul1"]
    }
  }
}
```

Cross-system validation can identify inconsistencies (e.g., serotype doesn't match expected ST).

## Common Typing Systems to Consider

- **cgMLST / wgMLST** - Core/whole genome MLST
- **Virulence profiling** - Pathogenicity genes (stx, eae, inv, ipa)
- **AMR profiling** - Resistance gene detection
- **Plasmid typing** - Replicon identification
- **Phylogenetic typing** - SNP-based lineages, clades
- **Capsule typing** - K-antigen (E. coli), capsular serotypes (Strep)
- **Toxin typing** - Botulinum toxin types, C. difficile ribotypes
- **Species confirmation** - In-silico 16S/rpoB/ANI

## Troubleshooting

**Q: Discovery script not finding targets**
- Check if metadata fields exist in NCBI for this organism
- Try alternate field names
- Consider manual curation for rare types

**Q: Validation inconsistent**
- Refine validation_instructions with more examples
- Add known edge cases to instructions
- Consider rule-based validation for deterministic cases

**Q: Too few high-confidence candidates**
- Lower min_score threshold in discovery
- Accept broader submitter base
- Use tool-determined ground truth instead of metadata

## Updating This Guide

As new typing systems are added, update this guide with:
- Lessons learned
- New metadata field patterns discovered
- Tool-specific integration notes
- Common pitfalls and solutions
