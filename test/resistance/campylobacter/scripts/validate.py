#!/usr/bin/env python3
"""
LLM-based validation of AMR tool outputs against ground truth.

Reads manifest.json ground truth and validation instructions, parses tool
outputs using format-specific parsers, and uses an LLM to determine if the
tool correctly detected the expected resistance profile.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))
from lib.output_parsers import (
    parse_resfinder_json,
    parse_amrfinderplus_tsv,
    parse_card_rgi_json,
    parse_abricate_tsv,
)


TOOL_PARSERS = {
    "resfinder": (parse_resfinder_json, "resfinder.json"),
    "amrfinderplus": (parse_amrfinderplus_tsv, "amrfinder.tsv"),
    "card_rgi": (parse_card_rgi_json, "rgi.json"),
    "abricate": (parse_abricate_tsv, "abricate_resfinder.tsv"),
}


def load_manifest(case_dir: Path) -> Dict:
    manifest_path = case_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No manifest.json found in {case_dir}")
    with open(manifest_path) as f:
        return json.load(f)


def resolve_output_path(case_dir: Path, reference_output: str) -> Optional[Path]:
    """Try actual/ first, then expected/."""
    for subdir in ["actual", "expected"]:
        candidate = case_dir / reference_output.replace("expected/", f"{subdir}/").replace("actual/", f"{subdir}/")
        if candidate.exists():
            return candidate
    return None


def parse_tool_output(case_dir: Path, tool_name: str, reference_output: str) -> Optional[Dict]:
    """Parse tool output using the appropriate format parser."""
    tool_key = tool_name.lower().replace(" ", "_").replace("-", "_")

    path = resolve_output_path(case_dir, reference_output)
    if path is None:
        return None

    # Match by tool key
    for key, (parser_fn, _) in TOOL_PARSERS.items():
        if key in tool_key:
            try:
                return parser_fn(path)
            except Exception as e:
                print(f"Warning: Failed to parse {path}: {e}", file=sys.stderr)
                return None

    # Fallback: return raw text
    try:
        return {"raw": path.read_text()}
    except Exception:
        return None


def build_validation_prompt(
    ground_truth: Dict,
    validation_instructions: str,
    tool_name: str,
    parsed_output: Optional[Dict],
    raw_output: Optional[str],
) -> str:
    output_section = ""
    if parsed_output:
        output_section = f"## Parsed Tool Output\n```json\n{json.dumps(parsed_output, indent=2)}\n```\n"
    if raw_output:
        output_section += f"\n## Raw Tool Output\n```\n{raw_output[:4000]}\n```\n"

    return f"""# AMR Tool Validation Task

You are validating the output of an antimicrobial resistance (AMR) detection tool against known ground truth.

## Ground Truth
```json
{json.dumps(ground_truth, indent=2)}
```

## Tool: {tool_name}

{output_section}

## Validation Instructions
{validation_instructions}

## Task
Determine if the tool correctly detected the AMR profile described in the ground truth.

Return a JSON object with:
- "result": "PASS" | "FAIL" | "PARTIAL"
- "reasoning": Detailed explanation
- "confidence": Number between 0.0 and 1.0
- "details": Object with specific findings (genes matched, missed, extra)

PASS: Tool correctly detected all expected resistance genes/phenotypes.
PARTIAL: Tool detected some but not all; or detected correct drug classes but missed individual genes.
FAIL: Tool missed major resistance determinants or called resistance when none expected.

Return ONLY the JSON object, no other text.
"""


def call_llm(prompt: str) -> Dict:
    """
    Call LLM for validation. Implement with your preferred API.
    Currently a placeholder — prints prompt to stderr and returns MANUAL_REVIEW_REQUIRED.
    """
    print("\n" + "=" * 80, file=sys.stderr)
    print("LLM PROMPT:", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    print(prompt, file=sys.stderr)
    print("=" * 80 + "\n", file=sys.stderr)
    print("NOTE: LLM integration not implemented. Implement call_llm() to enable automatic validation.", file=sys.stderr)

    return {
        "result": "MANUAL_REVIEW_REQUIRED",
        "reasoning": "LLM integration not implemented. Manual review required.",
        "confidence": 0.0,
        "details": {"note": "Implement call_llm() to enable automatic validation"}
    }


def validate_tool(case_dir: Path, manifest: Dict, tool_name: str) -> Dict:
    tool_config = manifest.get("tools", {}).get(tool_name)
    if not tool_config:
        return {"result": "ERROR", "reasoning": f"Tool {tool_name} not configured in manifest", "confidence": 0.0}

    ground_truth = manifest.get("ground_truth", {}).get("amr", {})
    if not ground_truth:
        return {"result": "ERROR", "reasoning": "No ground_truth.amr defined in manifest", "confidence": 0.0}

    tool_key = tool_name.lower().replace(" ", "_").replace("-", "_")
    validation_instructions = manifest.get("validation_instructions", {}).get(tool_key, "")
    if not validation_instructions:
        # Try matching by prefix
        for key, instr in manifest.get("validation_instructions", {}).items():
            if key in tool_key or tool_key in key:
                validation_instructions = instr
                break

    reference_output = tool_config.get("reference_output", "")
    parsed_output = parse_tool_output(case_dir, tool_name, reference_output)

    raw_path = resolve_output_path(case_dir, reference_output)
    raw_output = raw_path.read_text() if raw_path and raw_path.stat().st_size < 50_000 else None

    if parsed_output is None and raw_output is None:
        return {
            "result": "ERROR",
            "reasoning": f"Tool output not found. Run tool first or check path: {reference_output}",
            "confidence": 0.0
        }

    prompt = build_validation_prompt(
        ground_truth, validation_instructions, tool_name, parsed_output, raw_output
    )

    return call_llm(prompt)


def validate_case(case_dir: Path, tools: Optional[List[str]] = None) -> Dict:
    manifest = load_manifest(case_dir)
    available_tools = list(manifest.get("tools", {}).keys())
    tools_to_validate = [t for t in tools if t in available_tools] if tools else available_tools

    if not tools_to_validate:
        print(f"No tools to validate in {case_dir.name}", file=sys.stderr)
        return {}

    tool_results = {}
    for tool_name in tools_to_validate:
        print(f"Validating {tool_name}...", file=sys.stderr)
        tool_results[tool_name] = validate_tool(case_dir, manifest, tool_name)

    results = [r["result"] for r in tool_results.values()]
    if all(r == "PASS" for r in results):
        overall = "PASS"
    elif any(r == "FAIL" for r in results):
        overall = "FAIL"
    elif any(r == "PARTIAL" for r in results):
        overall = "PARTIAL"
    else:
        overall = "ERROR"

    return {
        "case": case_dir.name,
        "organism": manifest.get("organism", ""),
        "amr_profile": manifest.get("ground_truth", {}).get("amr", {}).get("phenotype_summary", ""),
        "timestamp": datetime.now().isoformat(),
        "tools": tool_results,
        "overall": overall,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate AMR tool outputs using LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--case", type=Path, required=True, help="Test case directory to validate")
    parser.add_argument("--tool", action="append", dest="tools", help="Specific tool to validate (repeatable)")
    parser.add_argument("--output", type=Path, help="Output path for validation report (default: stdout)")
    parser.add_argument("--output-format", choices=["json", "markdown"], default="json")

    args = parser.parse_args()
    case_dir = args.case if args.case.is_absolute() else Path.cwd() / args.case

    if not case_dir.exists():
        print(f"ERROR: Case directory not found: {case_dir}", file=sys.stderr)
        return 1

    try:
        report = validate_case(case_dir, args.tools)
    except Exception as e:
        print(f"ERROR: Validation failed: {e}", file=sys.stderr)
        return 1

    if args.output_format == "json":
        output_text = json.dumps(report, indent=2)
    else:
        output_text = f"# AMR Validation Report: {report['case']}\n\n"
        output_text += f"**Organism:** {report.get('organism', '')}\n"
        output_text += f"**AMR Profile:** {report.get('amr_profile', '')}\n"
        output_text += f"**Timestamp:** {report['timestamp']}\n"
        output_text += f"**Overall Result:** {report['overall']}\n\n"
        output_text += "## Tool Results\n\n"
        for tool_name, result in report.get("tools", {}).items():
            output_text += f"### {tool_name}\n\n"
            output_text += f"- **Result:** {result['result']}\n"
            output_text += f"- **Confidence:** {result['confidence']}\n"
            output_text += f"- **Reasoning:** {result['reasoning']}\n\n"

    if args.output:
        args.output.write_text(output_text)
        print(f"Validation report written to: {args.output}", file=sys.stderr)
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
