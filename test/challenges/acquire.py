#!/usr/bin/env python3
"""
Download sequence data for challenge datasets based on manifest.json specifications.

Usage:
    acquire.py --all
    acquire.py --challenge wrong_organism/ecoli_to_seqsero2
    acquire.py --phenomenon wrong_organism
    acquire.py --challenge wrong_organism/ecoli_to_seqsero2 --force
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

CHALLENGES_DIR = Path(__file__).parent


def log(msg):
    print(f"[acquire] {msg}", file=sys.stderr)


def error(msg):
    print(f"[acquire] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def find_manifests(root: Path) -> list[Path]:
    return sorted(root.glob("*/*/manifest.json"))


def load_manifest(manifest_path: Path) -> dict:
    with open(manifest_path) as f:
        return json.load(f)


def check_tool(tool: str) -> bool:
    """Return True if a required download tool is available."""
    return subprocess.run(
        ["which", tool], capture_output=True
    ).returncode == 0


def run_recipe(sample: dict, data_dir: Path, force: bool) -> bool:
    """Execute a recipe to construct a synthetic sample. Returns True on success."""
    sample_id = sample["id"]
    sample_dir = data_dir / sample_id
    sample_dir.mkdir(parents=True, exist_ok=True)

    if not force:
        expected_files = list(sample.get("files", {}).values())
        if expected_files and all((sample_dir / f).exists() for f in expected_files):
            log(f"  {sample_id}: recipe output already present, skipping")
            return True

    recipe = sample.get("recipe", {})
    inputs = recipe.get("inputs", [])
    tools_required = recipe.get("tools_required", [])

    # Verify input samples were already downloaded
    for input_id in inputs:
        input_dir = data_dir / input_id
        if not input_dir.exists():
            error(
                f"Recipe input '{input_id}' not yet downloaded. "
                f"Samples are downloaded in manifest order — check that '{input_id}' "
                f"appears before '{sample_id}' in the manifest."
            )

    # Verify required tools
    for tool in tools_required:
        if not check_tool(tool):
            error(f"Recipe requires '{tool}' which was not found in PATH.")

    cmd = recipe.get("command", "")
    log(f"  {sample_id}: running recipe ({recipe.get('description', '')})")
    log(f"  command: {cmd}")

    result = subprocess.run(cmd, shell=True, cwd=sample_dir)
    if result.returncode != 0:
        error(f"Recipe failed for sample '{sample_id}' (exit {result.returncode})")
        return False

    for role, filename in sample.get("files", {}).items():
        if not (sample_dir / filename).exists():
            error(f"Recipe did not produce expected file '{filename}' (role: {role})")
            return False

    log(f"  {sample_id}: recipe done")
    return True


def download_sample(sample: dict, data_dir: Path, force: bool) -> bool:
    """Download a single sample's data. Returns True on success."""
    sample_dir = data_dir / sample["id"]
    sample_dir.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded
    if not force:
        expected_files = list(sample.get("files", {}).values())
        if expected_files and all((sample_dir / f).exists() for f in expected_files):
            log(f"  {sample['id']}: already present, skipping (use --force to re-download)")
            return True

    source_type = sample.get("source_type", "")

    if source_type == "recipe":
        return run_recipe(sample, data_dir, force)

    tool = sample["download"]["tool"]
    tool_binary = tool.split("-")[0] if tool == "ncbi-datasets-cli" else tool
    tool_binary = "datasets" if tool == "ncbi-datasets-cli" else tool_binary

    if not check_tool(tool_binary):
        error(
            f"Required tool '{tool_binary}' not found. "
            f"Install '{tool}' before running this challenge."
        )

    cmd = sample["download"]["command"]
    log(f"  {sample['id']}: downloading ({source_type} / {sample.get('accession', 'no accession')})")
    log(f"  command: {cmd}")

    result = subprocess.run(
        cmd,
        shell=True,
        cwd=sample_dir,
    )

    if result.returncode != 0:
        error(f"Download failed for sample '{sample['id']}' (exit {result.returncode})")
        return False

    # Verify expected files exist
    for role, filename in sample.get("files", {}).items():
        fpath = sample_dir / filename
        if not fpath.exists():
            error(
                f"Expected file '{filename}' (role: {role}) not found after download "
                f"in {sample_dir}. Check the download command in manifest.json."
            )
            return False

    log(f"  {sample['id']}: done")
    return True


def acquire_challenge(manifest_path: Path, force: bool) -> bool:
    """Download all samples for one challenge. Returns True on success."""
    manifest = load_manifest(manifest_path)
    challenge_dir = manifest_path.parent
    data_dir = challenge_dir / "data"

    name = manifest.get("name", challenge_dir.name)
    phenomenon = manifest.get("phenomenon", challenge_dir.parent.name)
    log(f"Challenge: {phenomenon}/{name}")
    log(f"  mechanism: {manifest.get('mechanism', '')[:120]}...")

    for sample in manifest.get("samples", []):
        if not download_sample(sample, data_dir, force):
            return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Download sequence data for challenge datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Download all challenges")
    group.add_argument(
        "--challenge",
        metavar="PHENOMENON/INSTANCE",
        help="Download one challenge (e.g. wrong_organism/ecoli_to_seqsero2)",
    )
    group.add_argument(
        "--phenomenon",
        metavar="SLUG",
        help="Download all challenges under a phenomenon (e.g. wrong_organism)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Re-download even if data already exists"
    )

    args = parser.parse_args()

    if args.all:
        manifests = find_manifests(CHALLENGES_DIR)
        if not manifests:
            error("No manifest.json files found under test/challenges/")
    elif args.challenge:
        manifest_path = CHALLENGES_DIR / args.challenge / "manifest.json"
        if not manifest_path.exists():
            error(f"No manifest found at {manifest_path}")
        manifests = [manifest_path]
    elif args.phenomenon:
        phenomenon_dir = CHALLENGES_DIR / args.phenomenon
        if not phenomenon_dir.is_dir():
            error(f"No phenomenon directory found: {phenomenon_dir}")
        manifests = sorted(phenomenon_dir.glob("*/manifest.json"))
        if not manifests:
            error(f"No challenges found under phenomenon '{args.phenomenon}'")

    log(f"Found {len(manifests)} challenge(s)")
    failed = []
    for manifest_path in manifests:
        if not acquire_challenge(manifest_path, args.force):
            failed.append(manifest_path)

    if failed:
        error(f"{len(failed)} challenge(s) failed to download")

    log("All downloads complete.")


if __name__ == "__main__":
    main()
