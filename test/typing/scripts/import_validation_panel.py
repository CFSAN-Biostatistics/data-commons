#!/usr/bin/env python3
"""
Import validation panel CSV to generate manifest.json files.

Reads a curated validation panel with SeqSero2/SeqSero2S results and MLST data,
generates manifest.json files with ground truth and validation instructions.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from manifest_builder import ManifestBuilder


def normalize_serotype_for_filename(serotype: str) -> str:
    """
    Normalize serotype name for use in directory name.

    Args:
        serotype: Raw serotype string

    Returns:
        Normalized string safe for directory names
    """
    # Remove subspecies prefix
    serotype = re.sub(r'^(?:I|II|III|IV|V|VI)\s+', '', serotype)

    # Handle "or" cases - take first option
    if ' or ' in serotype:
        serotype = serotype.split(' or ')[0]

    # Remove parenthetical notes
    serotype = re.sub(r'\s*\([^)]+\)', '', serotype)

    # Replace special chars with underscores
    serotype = re.sub(r'[^a-zA-Z0-9]+', '_', serotype)

    # Clean up
    serotype = serotype.strip('_').lower()

    return serotype


def parse_antigenic_components(o_antigen: str, h1_antigen: str, h2_antigen: str) -> dict:
    """
    Parse antigenic formula components.

    Args:
        o_antigen: O antigen string (e.g., "4", "1,3,19")
        h1_antigen: H1 antigen string (e.g., "i", "e,h")
        h2_antigen: H2 antigen string (e.g., "1,2", "-")

    Returns:
        Dictionary with parsed components
    """
    components = {
        "o_antigen": [],
        "h1_antigen": [],
        "h2_antigen": []
    }

    # Parse O antigens
    if o_antigen and o_antigen != '-':
        # Split by comma, handle potential brackets
        o_parts = [p.strip() for p in o_antigen.split(',')]
        components["o_antigen"] = o_parts

    # Parse H1 antigens
    if h1_antigen and h1_antigen != '-':
        h1_parts = [p.strip() for p in h1_antigen.split(',')]
        components["h1_antigen"] = h1_parts

    # Parse H2 antigens
    if h2_antigen and h2_antigen != '-':
        h2_parts = [p.strip() for p in h2_antigen.split(',')]
        components["h2_antigen"] = h2_parts

    return components


def build_antigenic_formula(o_antigen: str, h1_antigen: str, h2_antigen: str) -> str:
    """
    Build standard antigenic formula notation.

    Args:
        o_antigen: O antigen string
        h1_antigen: H1 antigen string
        h2_antigen: H2 antigen string

    Returns:
        Standard formula (e.g., "4:i:1,2")
    """
    o = o_antigen if o_antigen and o_antigen != '-' else '-'
    h1 = h1_antigen if h1_antigen and h1_antigen != '-' else '-'
    h2 = h2_antigen if h2_antigen and h2_antigen != '-' else '-'

    return f"{o}:{h1}:{h2}"


def determine_difficulty(serotype: str, note: str, predicted_serotype: str) -> str:
    """
    Determine difficulty category based on serotype and notes.

    Args:
        serotype: Serotype name
        note: Notes from validation panel
        predicted_serotype: Predicted serotype

    Returns:
        Difficulty category
    """
    note_lower = note.lower()

    # Edge cases
    if 'contamination' in note_lower or 'co-existence' in note_lower:
        return "edge_case"
    if 'atypical' in note_lower or 'no serotype antigens' in note_lower:
        return "edge_case"
    if serotype.startswith('I 4') and 'i:-' in serotype:  # Monophasic
        return "edge_case"
    if 'II ' in serotype or 'III ' in serotype or 'IV ' in serotype:
        return "edge_case"
    if predicted_serotype.startswith('I -'):  # Rough/non-motile
        return "edge_case"

    # Common serotypes (based on frequency in US surveillance)
    common = [
        'Enteritidis', 'Typhimurium', 'Newport', 'Javiana', 'Heidelberg',
        'Infantis', 'Saintpaul', 'Muenchen', 'Braenderup', 'Thompson'
    ]

    if any(c.lower() in serotype.lower() for c in common):
        return "common"

    # Default to medium priority
    return "common"


def build_validation_instructions(
    serotype: str,
    antigenic_formula: str,
    note: str,
    st: str,
    predicted_serotype: str,
    h2_antigen: str
) -> dict:
    """
    Build validation instructions based on serotype characteristics and notes.

    Args:
        serotype: Expected serotype
        antigenic_formula: Expected antigenic formula
        note: Notes from panel
        st: MLST sequence type
        predicted_serotype: Predicted serotype from SeqSero2
        h2_antigen: H2 antigen component

    Returns:
        Dictionary with validation instructions per typing system
    """
    instructions = {
        "serological": "",
        "mlst": ""
    }

    # Base serological instructions
    serotype_clean = serotype.replace('"', '').strip()

    instr = f"Expected serotype: {serotype_clean}. "
    instr += f"Antigenic formula should match {antigenic_formula}. "

    # Handle "or" cases
    if ' or ' in predicted_serotype:
        options = [opt.strip() for opt in predicted_serotype.split(' or ')]
        instr += f"Accept any of: {', '.join(options)}. "
        instr += "Note: These serotypes share the same antigenic formula and require additional differentiation. "

    # Monophasic variants
    if h2_antigen == '-' and 'i' in antigenic_formula:
        instr += "This is a monophasic variant (H2-negative). "
        instr += "Tool must correctly identify absence of H2 phase (reported as '-' or empty). "
        instr += "Do NOT accept biphasic predictions with H2 antigens - this is a FAIL. "

    # Subspecies variants
    if 'subspecies' in note:
        if 'salamae' in note or 'II ' in serotype:
            instr += "Subspecies II (salamae). "
        elif 'houtenae' in note or 'IV ' in serotype:
            instr += "Subspecies IV (houtenae). "
        instr += "Tool must correctly identify subspecies designation. "

    # Rough/non-motile
    if 'no serotype antigens' in note.lower():
        instr += "EDGE CASE: Rough strain with no detectable antigens. "
        instr += "Tool may fail or report atypical result - document behavior. "

    # Contamination
    if 'contamination' in note.lower():
        instr += "WARNING: Inter-serotype contamination detected in this sample. "
        instr += "Tool may report multiple serotypes or ambiguous results. "

    # Special markers
    if 'Sdf' in note:
        instr += "Note: Sdf marker characteristic of Enteritidis may be referenced by tool. "
    if 'oafA' in note:
        instr += "Note: O5- variant (oafA deletion) may be noted by tool. "
    if 'tartrate' in note.lower():
        instr += "Note: d-Tartrate fermentation status differentiates typhoidal pathotype. "
    if 'ancillary' in note.lower():
        if 'O22' in note:
            instr += "Note: Ancillary O22 antigen marker (galE allele) may be detected. "
        if 'O23' in note:
            instr += "Note: Ancillary O23 antigen marker (galE allele) may be detected. "

    # Bracket notation
    if '[' in antigenic_formula or '5' in antigenic_formula:
        instr += "Accept antigenic formula with or without bracket notation around O:5. "

    instructions["serological"] = instr.strip()

    # MLST instructions
    if st and st != '-':
        instructions["mlst"] = f"Expected ST{st}. Accept exact match. "

        # Known single-locus variants
        if st == "19":
            instructions["mlst"] += "Also accept ST34 as PARTIAL (single-locus variant of ST19, common in monophasic strains). "
        elif st == "11":
            instructions["mlst"] += "ST11 is dominant for Enteritidis. "

        instructions["mlst"] += "Flag novel alleles for manual review."
    else:
        instructions["mlst"] = "MLST sequence type not provided in validation panel. Accept any valid ST result from tool. Flag novel alleles for review."

    return instructions


def import_row(row: dict, output_dir: Path, builder: ManifestBuilder) -> Path:
    """
    Import a single validation panel row as a manifest.

    Args:
        row: CSV row as dictionary
        output_dir: Base output directory
        builder: ManifestBuilder instance

    Returns:
        Path to generated manifest
    """
    # Extract fields - handle BOM in first column
    serotype_col = next((k for k in row.keys() if 'Serotype' in k), None)
    if not serotype_col:
        raise ValueError("Could not find Serotype column")

    serotype = row[serotype_col].strip()
    sra_acc = row['Representative SRR'].strip()
    st = row['ST'].strip() if row.get('ST', '').strip() else None

    # Get all column names to find duplicates
    cols = list(row.keys())

    # Find O antigen columns (there are 2)
    o_cols = [c for c in cols if 'O antigen prediction' in c]
    h1_cols = [c for c in cols if 'H1 antigen prediction' in c]
    h2_cols = [c for c in cols if 'H2 antigen prediction' in c]
    serotype_cols = [c for c in cols if 'Predicted serotype' in c and 'v1.3.1' not in c]
    note_cols = [c for c in cols if c == 'Note']

    # Use second occurrence (SeqSero2 results, not SeqSero2S)
    o_antigen = row[o_cols[1]].strip() if len(o_cols) > 1 else row[o_cols[0]].strip()
    h1_antigen = row[h1_cols[1]].strip() if len(h1_cols) > 1 else row[h1_cols[0]].strip()
    h2_antigen = row[h2_cols[1]].strip() if len(h2_cols) > 1 else row[h2_cols[0]].strip()
    predicted_serotype = row[serotype_cols[1]].strip() if len(serotype_cols) > 1 else row[serotype_cols[0]].strip()
    note = row[note_cols[1]].strip() if len(note_cols) > 1 else row[note_cols[0]].strip()

    # Parse components
    components = parse_antigenic_components(o_antigen, h1_antigen, h2_antigen)
    formula = build_antigenic_formula(o_antigen, h1_antigen, h2_antigen)
    difficulty = determine_difficulty(serotype, note, predicted_serotype)
    validation_instr = build_validation_instructions(
        serotype, formula, note, st, predicted_serotype, h2_antigen
    )

    # Generate directory name
    serotype_norm = normalize_serotype_for_filename(serotype)
    case_dir_name = f"sal_{serotype_norm}_{sra_acc}"
    case_dir = output_dir / case_dir_name

    # Determine subspecies
    subspecies = "enterica"
    if 'salamae' in note.lower() or 'II ' in serotype:
        subspecies = "salamae"
    elif 'houtenae' in note.lower() or 'IV ' in serotype:
        subspecies = "houtenae"

    # Build curation notes
    curation_notes = f"Imported from validation panel. Original serotype: {serotype}. "
    if note:
        curation_notes += f"Panel notes: {note}"

    # Create manifest
    manifest = builder.create_manifest(
        organism="Salmonella enterica",
        subspecies=subspecies,
        biosample_accession=None,  # Not in CSV
        sra_accession=sra_acc,
        assembly_accession=None,  # Not in CSV
        serotype=serotype,
        serotype_evidence=[
            {
                "source": "ValidationPanel.Serotype",
                "value": serotype
            }
        ],
        st=st,
        st_evidence=[
            {
                "source": "ValidationPanel.ST",
                "value": st or "not provided"
            }
        ],
        quality_metrics={
            "has_reads": True,
            "has_assembly": False,
            "reported_coverage": None,
            "submitter": "FDA-CFSAN Validation Panel"
        },
        metadata_confidence="high",
        antigenic_components=components,
        mlst_scheme="senterica" if subspecies == "enterica" else None,
        difficulty=difficulty,
        notes=f"Part of FDA-CFSAN validation panel. {note}".strip(),
        curation_notes=curation_notes
    )

    # Override ground truth with parsed formula
    manifest["ground_truth"]["serological"]["antigenic_formula"] = formula

    # Add validation instructions
    manifest["validation_instructions"] = validation_instr

    # Add tool configurations
    builder.add_tool_config(
        manifest,
        "SeqSero2",
        "reads",
        "SeqSero2_package.py -m a -t 4 -i data/reads_1.fq.gz data/reads_2.fq.gz -d actual/seqsero2/ -n seqsero2",
        "expected/seqsero2/SeqSero_result.tsv"
    )

    builder.add_tool_config(
        manifest,
        "SeqSero2S",
        "reads",
        "SeqSero2S_package.py -m a -t 4 -i data/reads_1.fq.gz data/reads_2.fq.gz -d actual/seqsero2s/ -n seqsero2s",
        "expected/seqsero2s/SeqSero_result.tsv"
    )

    if st and st != '-':
        builder.add_tool_config(
            manifest,
            "MLST",
            "assembly",
            "mlst --scheme senterica data/contigs.fa > actual/mlst/mlst_report.tsv",
            "expected/mlst/mlst_report.tsv"
        )

    # Write manifest
    manifest_path = case_dir / "manifest.json"
    builder.write_manifest(manifest, manifest_path)

    return manifest_path


def main():
    parser = argparse.ArgumentParser(
        description="Import validation panel CSV to generate manifests",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "csv_file",
        type=Path,
        help="Path to validation panel CSV"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Output directory (default: test/typing/)"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip if manifest already exists"
    )

    args = parser.parse_args()

    if not args.csv_file.exists():
        print(f"ERROR: CSV file not found: {args.csv_file}", file=sys.stderr)
        return 1

    builder = ManifestBuilder()

    # Read CSV
    print(f"Reading validation panel: {args.csv_file}")

    with open(args.csv_file, newline='', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Found {len(rows)} entries in validation panel")

    # Import each row
    generated = []
    skipped = []
    failed = []

    for i, row in enumerate(rows, 1):
        serotype = row.get('Serotype (SS2S merged)', '').strip()
        sra = row.get('Representative SRR', '').strip()

        if not serotype or not sra:
            print(f"Skipping row {i}: missing serotype or SRR")
            skipped.append(f"Row {i}: incomplete data")
            continue

        try:
            manifest_path = import_row(row, args.output, builder)
            generated.append(manifest_path)
            print(f"  [{i}/{len(rows)}] Generated: {manifest_path.parent.name}")
        except Exception as e:
            print(f"  [{i}/{len(rows)}] ERROR: {serotype} ({sra}): {e}", file=sys.stderr)
            failed.append(f"{serotype} ({sra}): {e}")

    # Summary
    print(f"\n{'='*60}")
    print(f"Successfully generated {len(generated)} manifests")

    if skipped:
        print(f"Skipped {len(skipped)} entries:")
        for s in skipped[:5]:
            print(f"  - {s}")
        if len(skipped) > 5:
            print(f"  ... and {len(skipped)-5} more")

    if failed:
        print(f"\nFailed {len(failed)} entries:")
        for f in failed[:5]:
            print(f"  - {f}")
        if len(failed) > 5:
            print(f"  ... and {len(failed)-5} more")

    print(f"\nNext steps:")
    print(f"1. Review generated manifests (especially validation_instructions)")
    print(f"2. Download data: ./download.sh --all")
    print(f"3. Run tools: ./run.sh --all")
    print(f"4. Commit expected outputs")

    return 0


if __name__ == "__main__":
    sys.exit(main())
