#!/usr/bin/env python3
"""
Generate INDEX.md summary of all test cases.
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def load_manifest(case_dir: Path) -> dict:
    """Load manifest.json from case directory."""
    manifest_path = case_dir / "manifest.json"
    if not manifest_path.exists():
        return None

    try:
        with open(manifest_path) as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load {manifest_path}: {e}", file=sys.stderr)
        return None


def extract_case_summary(case_dir: Path, manifest: dict) -> dict:
    """Extract summary information from case."""
    summary = {
        "name": case_dir.name,
        "organism": manifest.get("organism", "Unknown"),
        "difficulty": manifest.get("difficulty", "unknown"),
        "tools": list(manifest.get("tools", {}).keys()),
        "typing_systems": list(manifest.get("ground_truth", {}).keys()),
        "has_reads": bool(manifest.get("data_sources", {}).get("reads", {}).get("sra_accession")),
        "has_assembly": bool(manifest.get("data_sources", {}).get("assembly", {}).get("accession")),
        "confidence": manifest.get("curation", {}).get("metadata_confidence", "unknown"),
    }

    # Extract type information
    for ts in summary["typing_systems"]:
        gt = manifest.get("ground_truth", {}).get(ts, {})
        if ts == "serological":
            summary["serotype"] = gt.get("serotype")
        elif ts == "mlst":
            summary["st"] = gt.get("sequence_type")

    return summary


def generate_index(typing_dir: Path) -> str:
    """
    Generate INDEX.md content.

    Args:
        typing_dir: Path to test/typing directory

    Returns:
        Markdown content
    """
    # Find all test cases
    cases = []
    for item in typing_dir.iterdir():
        if item.is_dir() and (item / "manifest.json").exists():
            # Skip special directories
            if item.name in ["scripts", "config", "examples"]:
                continue

            manifest = load_manifest(item)
            if manifest:
                summary = extract_case_summary(item, manifest)
                cases.append(summary)

    if not cases:
        return "# Test Case Index\n\nNo test cases found.\n"

    # Group by organism
    by_organism = defaultdict(list)
    for case in cases:
        by_organism[case["organism"]].append(case)

    # Sort organisms alphabetically
    sorted_organisms = sorted(by_organism.keys())

    # Count statistics
    total_cases = len(cases)
    total_with_reads = sum(1 for c in cases if c["has_reads"])
    total_with_assembly = sum(1 for c in cases if c["has_assembly"])
    unique_tools = set()
    for case in cases:
        unique_tools.update(case["tools"])

    # Build markdown
    lines = [
        "# Test Case Index",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Total Cases:** {total_cases}",
        f"**Organisms:** {len(sorted_organisms)}",
        f"**Tools Configured:** {', '.join(sorted(unique_tools))}",
        "",
        "## Statistics",
        "",
        f"- Cases with reads: {total_with_reads} ({total_with_reads*100//total_cases if total_cases else 0}%)",
        f"- Cases with assemblies: {total_with_assembly} ({total_with_assembly*100//total_cases if total_cases else 0}%)",
        "",
        "## Test Cases by Organism",
        ""
    ]

    for organism in sorted_organisms:
        organism_cases = by_organism[organism]
        lines.append(f"### {organism} ({len(organism_cases)} cases)")
        lines.append("")

        # Group by difficulty
        by_difficulty = defaultdict(list)
        for case in organism_cases:
            by_difficulty[case["difficulty"]].append(case)

        for difficulty in ["common", "edge_case", "regulated", "rare", "unknown"]:
            if difficulty not in by_difficulty:
                continue

            diff_cases = by_difficulty[difficulty]
            if diff_cases:
                lines.append(f"#### {difficulty.replace('_', ' ').title()} ({len(diff_cases)})")
                lines.append("")

                for case in sorted(diff_cases, key=lambda c: c["name"]):
                    # Build case line
                    case_line = f"- **{case['name']}**"

                    # Add type information
                    type_info = []
                    if "serotype" in case and case["serotype"]:
                        type_info.append(f"Serotype: {case['serotype']}")
                    if "st" in case and case["st"]:
                        type_info.append(f"ST: {case['st']}")

                    if type_info:
                        case_line += f" - {', '.join(type_info)}"

                    # Add data types
                    data_types = []
                    if case["has_reads"]:
                        data_types.append("reads")
                    if case["has_assembly"]:
                        data_types.append("assembly")
                    if data_types:
                        case_line += f" ({'/'.join(data_types)})"

                    # Add confidence
                    if case["confidence"] != "unknown":
                        case_line += f" [confidence: {case['confidence']}]"

                    lines.append(case_line)

                lines.append("")

    # Add footer
    lines.extend([
        "---",
        "",
        "## Legend",
        "",
        "- **(reads/assembly)** - Available data types",
        "- **[confidence: X]** - Metadata confidence level (high/medium/low)",
        "",
        "## Usage",
        "",
        "```bash",
        "# Download data for all cases",
        "./download.sh --all",
        "",
        "# Run tools on all cases",
        "./run.sh --all",
        "",
        "# Validate specific case",
        "./scripts/validate.py --case <case_name>",
        "```",
        "",
        "See `README.md` for detailed usage instructions.",
        ""
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate test case index")
    parser.add_argument(
        "--typing-dir",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Path to test/typing directory"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file (default: <typing-dir>/INDEX.md)"
    )

    args = parser.parse_args()

    typing_dir = args.typing_dir
    if not typing_dir.exists():
        print(f"ERROR: Directory not found: {typing_dir}", file=sys.stderr)
        return 1

    # Generate index
    index_content = generate_index(typing_dir)

    # Write output
    output_path = args.output or (typing_dir / "INDEX.md")
    with open(output_path, 'w') as f:
        f.write(index_content)

    print(f"Index generated: {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
