#!/usr/bin/env python3
"""
LLM-based validation of typing tool outputs against ground truth.

This script reads manifest.json ground truth and validation instructions,
parses tool outputs, and uses an LLM to determine if the tool correctly
identified the organism type.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def load_manifest(case_dir: Path) -> Dict:
    """Load manifest.json from test case directory."""
    manifest_path = case_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No manifest.json found in {case_dir}")

    with open(manifest_path) as f:
        return json.load(f)


def read_tool_output(case_dir: Path, tool_name: str, output_path: str) -> Optional[str]:
    """
    Read tool output file.

    Args:
        case_dir: Test case directory
        tool_name: Name of tool
        output_path: Relative path to output file from manifest

    Returns:
        File contents or None if not found
    """
    # Try actual/ first (fresh run), then expected/ (reference)
    for subdir in ["actual", "expected"]:
        full_path = case_dir / output_path.replace("expected/", f"{subdir}/").replace("actual/", f"{subdir}/")
        if full_path.exists():
            try:
                with open(full_path) as f:
                    return f.read()
            except Exception as e:
                print(f"Warning: Failed to read {full_path}: {e}", file=sys.stderr)

    return None


def build_validation_prompt(
    typing_system: str,
    ground_truth: Dict,
    validation_instructions: str,
    tool_name: str,
    tool_output: str
) -> str:
    """
    Build LLM prompt for validation.

    Args:
        typing_system: Type of typing system (serological, mlst, etc.)
        ground_truth: Ground truth dictionary for this typing system
        validation_instructions: Custom validation instructions
        tool_name: Name of tool being validated
        tool_output: Tool output text

    Returns:
        Formatted prompt string
    """
    prompt = f"""# Typing Tool Validation Task

You are validating the output of a microbial typing tool against known ground truth.

## Typing System: {typing_system}

## Ground Truth
```json
{json.dumps(ground_truth, indent=2)}
```

## Tool Information
- Tool name: {tool_name}
- Typing system: {typing_system}

## Tool Output
```
{tool_output}
```

## Validation Instructions
{validation_instructions}

## Task
Determine if the tool correctly identified this organism's {typing_system} type.

Return a JSON object with:
- "result": "PASS" | "FAIL" | "PARTIAL"
- "reasoning": Detailed explanation of your determination
- "confidence": Number between 0.0 and 1.0
- "details": Object with specific findings (e.g., which fields matched/mismatched)

PASS means the tool correctly identified the organism type according to ground truth and validation instructions.
FAIL means the tool incorrectly identified the organism or failed to produce valid output.
PARTIAL means the tool got some aspects correct but missed important details (e.g., correct O antigens but wrong H antigens).

Return ONLY the JSON object, no other text.
"""

    return prompt


def call_llm(prompt: str) -> Dict:
    """
    Call LLM for validation.

    For now, this is a placeholder that would integrate with
    Claude API or other LLM. Users should implement their preferred LLM.

    Args:
        prompt: Validation prompt

    Returns:
        Validation result dictionary
    """
    # TODO: Implement actual LLM call
    # This is a placeholder that returns a template result
    print("\n" + "="*80, file=sys.stderr)
    print("LLM PROMPT:", file=sys.stderr)
    print("="*80, file=sys.stderr)
    print(prompt, file=sys.stderr)
    print("="*80 + "\n", file=sys.stderr)

    print("NOTE: LLM integration not yet implemented. Please implement call_llm() function.", file=sys.stderr)
    print("For now, returning a template result that requires manual review.\n", file=sys.stderr)

    return {
        "result": "MANUAL_REVIEW_REQUIRED",
        "reasoning": "LLM integration not implemented. Manual review required.",
        "confidence": 0.0,
        "details": {
            "note": "Implement call_llm() function to enable automatic validation"
        }
    }


def validate_tool(
    case_dir: Path,
    manifest: Dict,
    tool_name: str
) -> Dict:
    """
    Validate a single tool's output.

    Args:
        case_dir: Test case directory
        manifest: Manifest dictionary
        tool_name: Name of tool to validate

    Returns:
        Validation result for this tool
    """
    tool_config = manifest.get("tools", {}).get(tool_name)
    if not tool_config:
        return {
            "result": "ERROR",
            "reasoning": f"Tool {tool_name} not configured in manifest",
            "confidence": 0.0
        }

    # Determine typing system based on tool name
    # TODO: Make this more robust/configurable
    if "seqsero" in tool_name.lower():
        typing_system = "serological"
    elif "mlst" in tool_name.lower():
        typing_system = "mlst"
    else:
        typing_system = "serological"  # default

    # Get ground truth and validation instructions
    ground_truth = manifest.get("ground_truth", {}).get(typing_system, {})
    validation_instructions = manifest.get("validation_instructions", {}).get(typing_system, "")

    if not ground_truth:
        return {
            "result": "ERROR",
            "reasoning": f"No ground truth defined for {typing_system}",
            "confidence": 0.0
        }

    # Read tool output
    tool_output = read_tool_output(case_dir, tool_name, tool_config["reference_output"])
    if tool_output is None:
        return {
            "result": "ERROR",
            "reasoning": f"Tool output not found (run tool first or check path: {tool_config['reference_output']})",
            "confidence": 0.0
        }

    # Build prompt and call LLM
    prompt = build_validation_prompt(
        typing_system,
        ground_truth,
        validation_instructions,
        tool_name,
        tool_output
    )

    result = call_llm(prompt)

    return result


def validate_case(case_dir: Path, tools: Optional[List[str]] = None) -> Dict:
    """
    Validate all (or specified) tools for a test case.

    Args:
        case_dir: Test case directory
        tools: List of specific tools to validate (None = all)

    Returns:
        Validation report dictionary
    """
    manifest = load_manifest(case_dir)

    # Determine which tools to validate
    available_tools = list(manifest.get("tools", {}).keys())
    if tools:
        tools_to_validate = [t for t in tools if t in available_tools]
    else:
        tools_to_validate = available_tools

    if not tools_to_validate:
        print(f"No tools to validate in {case_dir.name}", file=sys.stderr)
        return {}

    # Validate each tool
    tool_results = {}
    for tool_name in tools_to_validate:
        print(f"Validating {tool_name}...", file=sys.stderr)
        result = validate_tool(case_dir, manifest, tool_name)
        tool_results[tool_name] = result

    # Determine overall result
    results = [r["result"] for r in tool_results.values()]
    if all(r == "PASS" for r in results):
        overall = "PASS"
    elif any(r == "FAIL" for r in results):
        overall = "FAIL"
    elif any(r == "PARTIAL" for r in results):
        overall = "PARTIAL"
    else:
        overall = "ERROR"

    # Build report
    report = {
        "case": case_dir.name,
        "timestamp": datetime.now().isoformat(),
        "tools": tool_results,
        "overall": overall
    }

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Validate typing tool outputs using LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--case",
        type=Path,
        required=True,
        help="Test case directory to validate"
    )
    parser.add_argument(
        "--tool",
        action="append",
        dest="tools",
        help="Specific tool to validate (can be repeated)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path for validation report (default: stdout)"
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "markdown"],
        default="json",
        help="Output format"
    )

    args = parser.parse_args()

    # Resolve case directory
    if not args.case.is_absolute():
        case_dir = Path.cwd() / args.case
    else:
        case_dir = args.case

    if not case_dir.exists():
        print(f"ERROR: Case directory not found: {case_dir}", file=sys.stderr)
        return 1

    # Run validation
    try:
        report = validate_case(case_dir, args.tools)
    except Exception as e:
        print(f"ERROR: Validation failed: {e}", file=sys.stderr)
        return 1

    # Output report
    if args.output_format == "json":
        output_text = json.dumps(report, indent=2)
    else:  # markdown
        output_text = f"# Validation Report: {report['case']}\n\n"
        output_text += f"**Timestamp:** {report['timestamp']}\n\n"
        output_text += f"**Overall Result:** {report['overall']}\n\n"
        output_text += "## Tool Results\n\n"
        for tool_name, result in report["tools"].items():
            output_text += f"### {tool_name}\n\n"
            output_text += f"- **Result:** {result['result']}\n"
            output_text += f"- **Confidence:** {result['confidence']}\n"
            output_text += f"- **Reasoning:** {result['reasoning']}\n\n"

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_text)
        print(f"Validation report written to: {args.output}", file=sys.stderr)
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
