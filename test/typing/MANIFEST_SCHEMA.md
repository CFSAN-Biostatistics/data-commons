# Manifest Schema Documentation

This document defines the structure of `manifest.json` files used in the typing test suite.

## Schema Structure

```json
{
  "organism": "string - Scientific name (e.g., 'Salmonella enterica')",
  "subspecies": "string - Optional subspecies/strain designation",
  
  "curation": {
    "date": "ISO 8601 date string - When this manifest was created",
    "ncbi_accessions": {
      "biosample": "SAMN... accession",
      "sra": "SRR... accession (may be null for assembly-only cases)",
      "assembly": "GCA/GCF... accession (may be null for reads-only cases)"
    },
    "metadata_confidence": "high|medium|low|conflict",
    "serotype_evidence": [
      {
        "source": "Path to metadata field (e.g., 'BioSample.Attributes.serotype')",
        "value": "Value found in that field"
      }
    ],
    "st_evidence": [
      {
        "source": "Path to metadata field",
        "value": "Value found"
      }
    ],
    "quality_metrics": {
      "has_reads": "boolean",
      "has_assembly": "boolean",
      "reported_coverage": "string - e.g., '50x' (may be null)",
      "submitter": "string - Submitting organization"
    },
    "notes": "string - Free-form notes about data quality, selection rationale, etc."
  },
  
  "ground_truth": {
    "serological": {
      "serotype": "string - Expected serotype name",
      "antigenic_formula": "string - Full antigenic formula (e.g., '1,4,[5],12:i:1,2')",
      "o_antigen": ["array of strings - O antigen components"],
      "h1_antigen": ["array of strings - H1 antigen components"],
      "h2_antigen": ["array of strings - H2 antigen components (may be empty for monophasic)"]
    },
    "mlst": {
      "scheme": "string - MLST scheme name (e.g., 'senterica', 'ecoli')",
      "sequence_type": "string or null - Expected ST (null if unknown/to be determined)"
    }
  },
  
  "data_sources": {
    "reads": {
      "sra_accession": "SRR... accession (null if not available)",
      "download_cmd": "string - Command to download reads (null if not available)"
    },
    "assembly": {
      "accession": "GCA/GCF... accession (null if not available)",
      "download_cmd": "string - Command to download assembly (null if not available)"
    }
  },
  
  "tools": {
    "ToolName": {
      "input_type": "reads|assembly|both",
      "run_cmd": "string - Command to execute tool",
      "reference_output": "string - Path to expected output file relative to case directory"
    }
  },
  
  "validation_instructions": {
    "serological": "string - Instructions for validating serological typing results",
    "mlst": "string - Instructions for validating MLST results"
  },
  
  "difficulty": "common|edge_case|regulated|rare",
  "notes": "string - High-level notes about why this case is included"
}
```

## Field Guidelines

### metadata_confidence

- **high**: Serotype/ST found in standard NCBI metadata fields, no conflicts
- **medium**: Parsed from organism name or inferred from related fields
- **low**: Found only in free-text fields or descriptions
- **conflict**: Disagreement between different metadata sources

### ground_truth typing systems

Each typing system (serological, mlst, etc.) has its own nested object. Fields within can be null if the ground truth is unknown or will be determined by tool execution.

### validation_instructions

Free-form text per typing system providing context for LLM-based validation:
- What constitutes correct identification
- Acceptable synonyms or variants
- Known edge cases or tool quirks
- Specific criteria for PASS/FAIL/PARTIAL

### difficulty

- **common**: Frequently encountered type, positive control
- **edge_case**: Known difficult case (monophasic, rough, etc.)
- **regulated**: Public health significance, special handling
- **rare**: Unusual type important for coverage

## Notes

- All paths in manifest are relative to the test case directory
- Commands assume execution from the test case directory
- Null values indicate data not available or not applicable
- Arrays may be empty (e.g., h2_antigen for monophasic Salmonella)
