#!/usr/bin/env python3
"""
Download reference genomes, construct synthetic references, and simulate reads
for the short-read aligner benchmark.

Usage:
    acquire.py --all
    acquire.py --target T1
    acquire.py --target T1 --giab
    acquire.py --organism homo_sapiens
    acquire.py --synthetic
    acquire.py --target T1 --force

Workflow per target:
  1. Check for required tools (reference download, construction, simulation).
     Report missing tools and skip those phases — public reference download
     always proceeds.
  2. Download the public reference genome.
  3. Construct synthetic reference if needed and construction tools are present.
  4. Simulate reads if simulation tools are present.
  5. If --giab and target is T1: download GIAB real reads.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

BENCHMARK_DIR = Path(__file__).parent
GLOBAL_CONFIG = BENCHMARK_DIR / "global.json"

REFERENCE_TOOLS = ["ncbi-datasets-cli", "entrez-direct", "wget", "curl"]
SIMULATION_TOOLS = ["dwgsim", "art_illumina", "mason2", "gargammel"]
CONSTRUCTION_TOOLS = ["simuG", "VISOR", "python3"]
GIAB_TOOLS = ["fasterq-dump"]


def log(msg: str):
    print(f"[acquire] {msg}", file=sys.stderr)


def die(msg: str):
    print(f"[acquire] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def check_tool(name: str) -> bool:
    return subprocess.run(["which", name], capture_output=True).returncode == 0


def check_tool_set(tools: list[str]) -> tuple[list[str], list[str]]:
    present = [t for t in tools if check_tool(t)]
    missing = [t for t in tools if not check_tool(t)]
    return present, missing


def load_global() -> dict:
    if not GLOBAL_CONFIG.exists():
        die(f"global.json not found at {GLOBAL_CONFIG}")
    with open(GLOBAL_CONFIG) as f:
        return json.load(f)


def load_manifest(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def find_manifests(target_ids: list[str] | None, organism: str | None,
                   synthetic_only: bool, all_targets: bool) -> list[Path]:
    manifests = []

    if not synthetic_only:
        for path in sorted(BENCHMARK_DIR.glob("*/*/manifest.json")):
            if "synthetic" not in path.parts:
                manifests.append(path)

    for path in sorted(BENCHMARK_DIR.glob("synthetic/*/manifest.json")):
        manifests.append(path)

    if not all_targets:
        if target_ids:
            filtered = []
            for m in manifests:
                data = load_manifest(m)
                if data.get("id") in target_ids:
                    filtered.append(m)
            manifests = filtered

        if organism:
            manifests = [m for m in manifests if organism.lower() in str(m).lower()]

        if synthetic_only:
            manifests = [m for m in manifests if "synthetic" in str(m)]

    return manifests


def run_command(cmd: str, cwd: Path, label: str) -> bool:
    log(f"  {label}: running command")
    log(f"    cwd: {cwd}")
    log(f"    cmd: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=str(cwd))
    if result.returncode != 0:
        log(f"  {label}: FAILED (exit {result.returncode})")
        return False
    return True


def substitute_globals(cmd: str, global_cfg: dict) -> str:
    return cmd.replace("{rng_seed}", str(global_cfg["rng_seed"]))


def acquire_reference(manifest: dict, target_dir: Path, force: bool, global_cfg: dict) -> bool:
    ref_cfg = manifest.get("reference", {})
    download_cfg = ref_cfg.get("download", {})
    if not download_cfg:
        log("  reference: no download config — skipping")
        return True

    tool = download_cfg.get("tool", "")
    cmd = download_cfg.get("command", "")
    if not cmd:
        log("  reference: empty command — skipping")
        return True

    ref_dir = target_dir / "data" / "reference"
    ref_fasta = ref_dir / "reference.fasta"

    if ref_fasta.exists() and not force:
        log(f"  reference: {ref_fasta} already present, skipping (use --force to re-download)")
        return True

    # Check download tool availability
    primary_tool = cmd.split()[0]
    if not check_tool(primary_tool):
        log(f"  reference: tool '{primary_tool}' not in PATH — cannot download reference")
        return False

    ref_dir.mkdir(parents=True, exist_ok=True)
    cmd = substitute_globals(cmd, global_cfg)
    return run_command(cmd, ref_dir, "reference download")


def acquire_construction(manifest: dict, target_dir: Path, force: bool,
                         global_cfg: dict, missing_construction: list[str]) -> bool:
    construction = manifest.get("construction", {})
    if not construction:
        return True

    tools_required = construction.get("tools_required", [])
    blocked = [t for t in tools_required if t in missing_construction]
    if blocked:
        log(f"  construction: SKIPPED — missing tools: {', '.join(blocked)}")
        return False

    ref_dir = target_dir / "data" / "reference"
    ref_fasta = ref_dir / "reference.fasta"
    if ref_fasta.exists() and not force:
        log(f"  construction: {ref_fasta} already present, skipping")
        return True

    ref_dir.mkdir(parents=True, exist_ok=True)
    commands = construction.get("commands", [])
    if not commands:
        cmd = construction.get("command", "")
        commands = [cmd] if cmd else []

    for cmd in commands:
        if not cmd:
            continue
        cmd = substitute_globals(cmd, global_cfg)
        if not run_command(cmd, ref_dir, "construction"):
            return False
    return True


def acquire_simulation(manifest: dict, target_dir: Path, force: bool,
                       global_cfg: dict, missing_simulation: list[str]) -> bool:
    sim_cfg = manifest.get("simulation", {})
    if not sim_cfg:
        return True

    tool = sim_cfg.get("tool", "")
    if tool and tool in missing_simulation:
        log(f"  simulation: SKIPPED — tool '{tool}' not in PATH")
        return False

    reads_dir = target_dir / "data" / "reads"
    r1 = reads_dir / "reads_1.fastq.gz"
    if r1.exists() and not force:
        log(f"  simulation: reads already present, skipping")
        return True

    ref_fasta = target_dir / "data" / "reference" / "reference.fasta"
    if not ref_fasta.exists():
        log("  simulation: SKIPPED — reference.fasta not present (run reference acquisition first)")
        return False

    reads_dir.mkdir(parents=True, exist_ok=True)
    cmd = sim_cfg.get("command", "")
    if not cmd:
        log("  simulation: no command specified — skipping")
        return True

    cmd = substitute_globals(cmd, global_cfg)
    return run_command(cmd, reads_dir, "simulation")


def acquire_giab(manifest: dict, target_dir: Path, force: bool) -> bool:
    real_reads = manifest.get("real_reads", {})
    if not real_reads:
        log("  giab: target has no real_reads config")
        return False

    giab_dir = target_dir / "data" / "giab"
    if giab_dir.exists() and any(giab_dir.iterdir()) and not force:
        log("  giab: reads already present, skipping")
        return True

    _, missing = check_tool_set(GIAB_TOOLS)
    if missing:
        log(f"  giab: SKIPPED — missing tools: {', '.join(missing)}")
        return False

    giab_dir.mkdir(parents=True, exist_ok=True)
    ftp = real_reads.get("ftp", "")
    if ftp:
        log(f"  giab: FTP source: {ftp}")
        log("  giab: Downloading from NCBI FTP (this is ~300x coverage, expect large download)")
        cmd = f"wget -q -r -nd -np -A '*.fastq.gz,*.fq.gz' '{ftp}'"
        return run_command(cmd, giab_dir, "giab download")

    sra_start = real_reads.get("sra_range_start", "")
    sra_end = real_reads.get("sra_range_end", "")
    if sra_start and sra_end:
        log(f"  giab: SRA range {sra_start}..{sra_end} — use fasterq-dump per accession")
        log("  giab: Automated SRA range download not implemented — see AGENTS.md for manual procedure")
        return False

    log("  giab: no download method configured")
    return False


def process_target(manifest_path: Path, args, global_cfg: dict,
                   missing_simulation: list[str], missing_construction: list[str]):
    manifest = load_manifest(manifest_path)
    target_id = manifest.get("id", "?")
    name = manifest.get("name", "?")
    organism = manifest.get("organism", "")
    target_dir = manifest_path.parent

    log(f"--- {target_id}: {organism} / {name} ---")

    is_synthetic = manifest.get("target_type") == "synthetic"

    if is_synthetic:
        ok = acquire_construction(manifest, target_dir, args.force, global_cfg, missing_construction)
        if not ok:
            log(f"  {target_id}: construction phase incomplete")
    else:
        ok = acquire_reference(manifest, target_dir, args.force, global_cfg)
        if not ok:
            log(f"  {target_id}: reference download failed or skipped")

    acquire_simulation(manifest, target_dir, args.force, global_cfg, missing_simulation)

    if args.giab and target_id == "T1":
        acquire_giab(manifest, target_dir, args.force)
    elif args.giab and target_id != "T1":
        log(f"  {target_id}: --giab only applies to T1, skipping for this target")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Acquire all targets")
    group.add_argument("--target", metavar="ID", action="append",
                       help="Acquire specific target by ID (e.g. T1, S3). Repeatable.")
    group.add_argument("--organism", metavar="NAME",
                       help="Acquire all targets matching organism directory name (e.g. homo_sapiens)")
    group.add_argument("--synthetic", action="store_true", help="Acquire all synthetic targets (S1-S5)")
    parser.add_argument("--giab", action="store_true",
                        help="Also download GIAB HG001/NA12878 real reads for T1 (large download)")
    parser.add_argument("--force", action="store_true",
                        help="Re-download and re-generate even if output files exist")
    args = parser.parse_args()

    if not any([args.all, args.target, args.organism, args.synthetic]):
        parser.print_help()
        sys.exit(1)

    global_cfg = load_global()
    log(f"RNG seed: {global_cfg['rng_seed']}")

    # Inventory tools upfront
    _, missing_sim = check_tool_set(SIMULATION_TOOLS)
    _, missing_con = check_tool_set(CONSTRUCTION_TOOLS)

    if missing_sim:
        log(f"Simulation tools not found (simulation phases will be skipped): {', '.join(missing_sim)}")
        log(f"  Install: dwgsim, art_illumina, mason2, gargammel")
    if missing_con:
        log(f"Construction tools not found (synthetic construction phases will be skipped): {', '.join(missing_con)}")
        log(f"  Install: simuG, VISOR")
    if not missing_sim and not missing_con:
        log("All simulation and construction tools found.")

    manifests = find_manifests(
        target_ids=args.target,
        organism=args.organism,
        synthetic_only=args.synthetic,
        all_targets=args.all,
    )

    if not manifests:
        die("No matching manifests found. Check --target / --organism values against available manifests.")

    log(f"Processing {len(manifests)} target(s)")
    for mpath in manifests:
        process_target(mpath, args, global_cfg, missing_sim, missing_con)

    log("Done.")


if __name__ == "__main__":
    main()
