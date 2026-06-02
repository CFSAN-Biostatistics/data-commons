#!/usr/bin/env python3
"""
Render a tool-family symlink layout for a challenge dataset.

Reads the challenge manifest and a tool-family template, then creates a
directory of symlinks arranged the way the target tool expects its inputs.
Data stays in the canonical location (data/{sample_id}/); only symlinks
are written to the output directory.

Usage:
    layout.py --challenge wrong_organism/ecoli_to_seqsero2 --tool seqsero2 --out /tmp/run
    layout.py --challenge contamination/sample_swap --tool snippy-family --out /tmp/run
    layout.py --list-tools
"""

import argparse
import json
import os
import sys
from pathlib import Path

CHALLENGES_DIR = Path(__file__).parent
TOOL_LAYOUTS_DIR = CHALLENGES_DIR / "tool_layouts"


def log(msg):
    print(f"[layout] {msg}", file=sys.stderr)


def error(msg):
    print(f"[layout] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def list_tools():
    templates = sorted(TOOL_LAYOUTS_DIR.glob("*.json"))
    if not templates:
        print("No tool layout templates found.")
        return
    print("Available tool families:\n")
    for t in templates:
        data = json.loads(t.read_text())
        print(f"  {data['tool_family']:<25} {data['description']}")
        print(f"  {'':25} hint: {data.get('invocation_hint', '')}")
        print()


def load_manifest(challenge_path: Path) -> dict:
    manifest_path = challenge_path / "manifest.json"
    if not manifest_path.exists():
        error(f"No manifest.json found at {manifest_path}")
    with open(manifest_path) as f:
        return json.load(f)


def load_template(tool_family: str) -> dict:
    template_path = TOOL_LAYOUTS_DIR / f"{tool_family}.json"
    if not template_path.exists():
        available = [p.stem for p in TOOL_LAYOUTS_DIR.glob("*.json")]
        error(
            f"No layout template for '{tool_family}'. "
            f"Available: {', '.join(sorted(available))}"
        )
    with open(template_path) as f:
        return json.load(f)


def samples_matching_roles(samples: list[dict], roles) -> list[dict]:
    if isinstance(roles, str):
        roles = [roles]
    return [s for s in samples if s.get("role") in roles]


def render_layout(manifest: dict, template: dict, challenge_dir: Path, out_dir: Path):
    data_dir = challenge_dir / "data"
    samples = manifest.get("samples", [])
    samples_by_id = {s["id"]: s for s in samples}

    links_created = 0
    links_skipped = 0

    for entry in template.get("layout", []):
        # Resolve which roles this entry applies to
        if "source_role" in entry:
            matched = samples_matching_roles(samples, entry["source_role"])
        elif "source_roles" in entry:
            matched = samples_matching_roles(samples, entry["source_roles"])
        else:
            error(f"Template entry missing 'source_role' or 'source_roles': {entry}")

        source_file_key = entry["source_file"]
        target_template = entry["target"]

        for sample in matched:
            sample_id = sample["id"]
            files = sample.get("files", {})

            if source_file_key not in files:
                log(f"  skipping {sample_id}: no '{source_file_key}' file in manifest")
                links_skipped += 1
                continue

            filename = files[source_file_key]
            source_path = (data_dir / sample_id / filename).resolve()

            if not source_path.exists():
                error(
                    f"Source file not found: {source_path}\n"
                    f"  Run: python acquire.py --challenge {challenge_dir.parent.name}/{challenge_dir.name}"
                )

            target_rel = target_template.replace("{sample_id}", sample_id)
            target_path = out_dir / target_rel
            target_path.parent.mkdir(parents=True, exist_ok=True)

            if target_path.exists() or target_path.is_symlink():
                target_path.unlink()

            target_path.symlink_to(source_path)
            log(f"  {target_rel} -> {source_path}")
            links_created += 1

    return links_created, links_skipped


def main():
    parser = argparse.ArgumentParser(
        description="Render a tool-family symlink layout for a challenge dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--challenge",
        metavar="PHENOMENON/INSTANCE",
        help="Challenge to lay out (e.g. wrong_organism/ecoli_to_seqsero2)",
    )
    parser.add_argument(
        "--tool",
        metavar="TOOL_FAMILY",
        help="Tool family layout to render (e.g. seqsero2, snippy-family)",
    )
    parser.add_argument(
        "--out",
        metavar="DIR",
        help="Output directory for symlink layout (created if absent)",
    )
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="List available tool family layouts and exit",
    )

    args = parser.parse_args()

    if args.list_tools:
        list_tools()
        return

    if not args.challenge or not args.tool or not args.out:
        parser.print_help()
        sys.exit(1)

    challenge_dir = CHALLENGES_DIR / args.challenge
    if not challenge_dir.is_dir():
        error(f"Challenge directory not found: {challenge_dir}")

    manifest = load_manifest(challenge_dir)
    template = load_template(args.tool)

    # Validate this tool family is declared in the manifest
    declared = manifest.get("tool_families", [])
    if declared and args.tool not in declared:
        log(
            f"Warning: '{args.tool}' not listed in manifest tool_families {declared}. "
            f"Proceeding anyway — the layout may be incomplete."
        )

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    name = manifest.get("name", challenge_dir.name)
    log(f"Challenge: {manifest.get('phenomenon', '')}/{name}")
    log(f"Tool family: {args.tool}")
    log(f"Output: {out_dir}")
    log(f"Invocation hint: {template.get('invocation_hint', '(none)')}")

    created, skipped = render_layout(manifest, template, challenge_dir, out_dir)
    log(f"Done: {created} symlink(s) created, {skipped} skipped")


if __name__ == "__main__":
    main()
