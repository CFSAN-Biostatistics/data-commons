#!/usr/bin/env python3
"""
Compute bandwidth-normalized aligner benchmark scores (BNT, CAS, CBS, MEI).

Reads per-aligner per-target results and produces a scored comparison table.
See AGENTS.md for the expected input format.

Usage — JSON input (primary):
    score.py results.json

Usage — TSV input:
    score.py --from-tsv results.tsv --bandwidth 80.0

Options:
    --alpha FLOAT       Accuracy weight in CBS (default: 0.7, range 0-1)
    --tolerance INT     Placement tolerance in bp for PA (default: 10)
    --bandwidth FLOAT   STREAM Triad GB/s (required with --from-tsv; overrides JSON if provided)
    --json FILE         Write full intermediate results to FILE as JSON
    --sensitivity       Print CBS sensitivity table across alpha in {0.5,0.6,0.7,0.8,0.9}

JSON input schema:
    {
      "platform": {
        "stream_triad_gbps": 80.0,   // required
        "cpu_model": "...",          // optional, for reporting
        "threads": 8                 // default thread count; may be overridden per target
      },
      "aligners": [
        {
          "name": "bwa-mem2",
          "version": "2.2.1",
          "targets": [
            {
              "id": "T1",
              "reads": 10000000,
              "wall_time_s": 45.0,
              "threads": 8,          // optional, overrides platform.threads
              "pa": 0.941,           // placement accuracy (fraction, 0-1)
              "mcs": 0.881,          // MAPQ calibration score (fraction, 0-1)
              "va": 0.962,           // variant accuracy F1 (T1 GIAB only; omit otherwise)
              "peak_rss_gb": 6.0,
              "genome_size_gb": 0.249
            }
          ]
        }
      ]
    }

TSV columns (tab-separated, header row required):
    aligner  version  target  reads  wall_time_s  threads  pa  mcs  va  peak_rss_gb  genome_size_gb

    - va: leave empty or use "NA" for non-T1 targets
    - threads: per-run thread count
    - bandwidth supplied via --bandwidth flag
"""

import argparse
import json
import math
import sys
from pathlib import Path


def geomean(values: list[float]) -> float:
    if not values or any(v <= 0 for v in values):
        return 0.0
    return math.exp(sum(math.log(v) for v in values) / len(values))


def compute_bnt(reads: int, wall_time_s: float, threads: int, bandwidth_gbps: float) -> float:
    if wall_time_s <= 0 or threads <= 0 or bandwidth_gbps <= 0:
        return 0.0
    T = reads / (wall_time_s * threads)
    return T / bandwidth_gbps


def compute_cas_target(pa: float, mcs: float, va: float | None) -> float:
    if va is not None:
        return geomean([pa, mcs, va])
    return geomean([pa, mcs])


def compute_cbs(cas: float, bnt_norm: float, alpha: float) -> float:
    if cas <= 0 or bnt_norm <= 0:
        return 0.0
    return (cas ** alpha) * (bnt_norm ** (1.0 - alpha))


def parse_tsv(path: str, bandwidth: float) -> dict:
    lines = Path(path).read_text().strip().splitlines()
    if not lines:
        sys.exit("ERROR: TSV file is empty")
    header = lines[0].split("\t")
    required = {"aligner", "version", "target", "reads", "wall_time_s", "threads", "pa", "mcs"}
    missing = required - set(header)
    if missing:
        sys.exit(f"ERROR: TSV missing required columns: {', '.join(sorted(missing))}")

    col = {name: i for i, name in enumerate(header)}
    aligners_map: dict[str, dict] = {}

    for lineno, line in enumerate(lines[1:], 2):
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) < len(header):
            sys.exit(f"ERROR: line {lineno} has fewer fields than header")

        def get(name):
            return fields[col[name]].strip() if name in col else ""

        aligner_name = get("aligner")
        version = get("version")
        key = f"{aligner_name}|{version}"
        if key not in aligners_map:
            aligners_map[key] = {"name": aligner_name, "version": version, "targets": []}

        va_raw = get("va")
        va = None if (not va_raw or va_raw.upper() in ("NA", "")) else float(va_raw)
        aligners_map[key]["targets"].append({
            "id": get("target"),
            "reads": int(get("reads")),
            "wall_time_s": float(get("wall_time_s")),
            "threads": int(get("threads")),
            "pa": float(get("pa")),
            "mcs": float(get("mcs")),
            "va": va,
            "peak_rss_gb": float(get("peak_rss_gb")) if "peak_rss_gb" in col and get("peak_rss_gb") else None,
            "genome_size_gb": float(get("genome_size_gb")) if "genome_size_gb" in col and get("genome_size_gb") else None,
        })

    return {
        "platform": {"stream_triad_gbps": bandwidth, "threads": None},
        "aligners": list(aligners_map.values()),
    }


def score(data: dict, alpha: float, tolerance_bp: int) -> list[dict]:
    platform = data.get("platform", {})
    bandwidth = platform.get("stream_triad_gbps")
    default_threads = platform.get("threads")
    if not bandwidth:
        sys.exit("ERROR: platform.stream_triad_gbps is required (or use --bandwidth with --from-tsv)")

    results = []
    for aligner in data.get("aligners", []):
        name = aligner.get("name", "?")
        version = aligner.get("version", "?")
        target_scores = []
        bnt_values = []
        mei_values = []
        target_details = []

        for t in aligner.get("targets", []):
            threads = t.get("threads") or default_threads
            if not threads:
                sys.exit(f"ERROR: thread count not specified for {name} target {t.get('id')}")
            bnt = compute_bnt(t["reads"], t["wall_time_s"], threads, bandwidth)
            va = t.get("va")
            cas_t = compute_cas_target(t["pa"], t["mcs"], va)
            target_scores.append(cas_t)
            bnt_values.append(bnt)

            peak_rss = t.get("peak_rss_gb")
            genome_size = t.get("genome_size_gb")
            mei = (peak_rss / genome_size) if (peak_rss and genome_size) else None
            if mei is not None:
                mei_values.append(mei)

            target_details.append({
                "id": t.get("id"),
                "pa": t["pa"],
                "mcs": t["mcs"],
                "va": va,
                "cas": cas_t,
                "bnt": bnt,
                "mei": mei,
            })

        cas = geomean(target_scores) if target_scores else 0.0
        bnt_agg = geomean(bnt_values) if bnt_values else 0.0
        mei_agg = (sum(mei_values) / len(mei_values)) if mei_values else None

        results.append({
            "name": name,
            "version": version,
            "cas": cas,
            "bnt": bnt_agg,
            "mei": mei_agg,
            "target_details": target_details,
        })

    # Normalize BNT against best in comparison set
    max_bnt = max((r["bnt"] for r in results), default=1.0) or 1.0
    for r in results:
        r["bnt_norm"] = r["bnt"] / max_bnt
        r["cbs"] = compute_cbs(r["cas"], r["bnt_norm"], alpha)

    return results


def sensitivity_table(data: dict, tolerance_bp: int) -> dict[float, list[dict]]:
    alphas = [0.5, 0.6, 0.7, 0.8, 0.9]
    return {a: score(data, a, tolerance_bp) for a in alphas}


def fmt(val, width=7, decimals=3):
    if val is None:
        return "-".rjust(width)
    return f"{val:.{decimals}f}".rjust(width)


def print_results(results: list[dict], platform: dict, alpha: float, tolerance_bp: int,
                  show_sensitivity: bool, sens: dict | None = None):
    cpu = platform.get("cpu_model", "")
    bw = platform.get("stream_triad_gbps", "?")
    threads = platform.get("threads", "?")

    print("\nShort-Read Aligner Benchmark Results")
    print("=====================================")
    if cpu:
        print(f"Platform:      {cpu}")
    print(f"STREAM Triad:  {bw} GB/s  |  Threads: {threads}")
    print(f"α = {alpha:.2f}  |  placement tolerance d = {tolerance_bp} bp\n")

    col_w = max(len(r["name"]) for r in results) + 2
    ver_w = max(len(r["version"]) for r in results) + 2

    header = (f"{'Aligner':<{col_w}} {'Version':<{ver_w}}"
              f"{'CAS':>8} {'BNT(r/t·GB)':>13} {'BNT_norm':>10} {'CBS':>8} {'MEI':>6}")
    print(header)
    print("-" * len(header))

    for r in sorted(results, key=lambda x: -x["cbs"]):
        mei_str = f"{r['mei']:.1f}" if r["mei"] is not None else "-"
        print(f"{r['name']:<{col_w}} {r['version']:<{ver_w}}"
              f"{r['cas']:>8.3f} {r['bnt']:>13.1f} {r['bnt_norm']:>10.3f}"
              f" {r['cbs']:>8.3f} {mei_str:>6}")

    print("\nPer-target CAS breakdown:")
    all_target_ids = []
    for r in results:
        for td in r["target_details"]:
            if td["id"] not in all_target_ids:
                all_target_ids.append(td["id"])

    tid_w = max(len(t) for t in all_target_ids) + 2 if all_target_ids else 6
    row_header = f"{'Aligner':<{col_w}}" + "".join(f"{t:>{max(tid_w, 7)}}" for t in all_target_ids)
    print(row_header)
    print("-" * len(row_header))
    for r in sorted(results, key=lambda x: -x["cbs"]):
        td_map = {td["id"]: td["cas"] for td in r["target_details"]}
        row = f"{r['name']:<{col_w}}"
        for tid in all_target_ids:
            val = td_map.get(tid)
            row += fmt(val, width=max(tid_w, 7)).rjust(max(tid_w, 7))
        print(row)

    if show_sensitivity and sens:
        print(f"\nCBS sensitivity (α sweep):")
        alpha_vals = sorted(sens.keys())
        sens_header = f"{'Aligner':<{col_w}}" + "".join(
            f"{'α='+str(a):>9}{'*' if abs(a - alpha) < 0.001 else ' '}" for a in alpha_vals
        )
        print(sens_header)
        print("-" * len(sens_header))
        for r in sorted(results, key=lambda x: -x["cbs"]):
            row = f"{r['name']:<{col_w}}"
            for a in alpha_vals:
                a_results = {rr["name"]: rr["cbs"] for rr in sens[a]}
                row += f"{a_results.get(r['name'], 0.0):>10.3f}"
            print(row)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input", nargs="?", help="JSON results file (primary input format)")
    parser.add_argument("--from-tsv", metavar="FILE", help="Read results from TSV instead of JSON")
    parser.add_argument("--bandwidth", type=float, metavar="GB/S",
                        help="STREAM Triad result in GB/s (required with --from-tsv)")
    parser.add_argument("--alpha", type=float, default=0.7,
                        help="Accuracy weight in CBS, 0-1 (default: 0.7 per spec)")
    parser.add_argument("--tolerance", type=int, default=10,
                        help="Placement tolerance in bp for PA (default: 10 per spec)")
    parser.add_argument("--json", metavar="FILE",
                        help="Write full intermediate results to FILE as JSON")
    parser.add_argument("--sensitivity", action="store_true",
                        help="Print CBS sensitivity across α ∈ {0.5,0.6,0.7,0.8,0.9}")
    args = parser.parse_args()

    if not args.input and not args.from_tsv:
        parser.print_help()
        sys.exit(1)

    if args.from_tsv:
        if not args.bandwidth:
            sys.exit("ERROR: --bandwidth is required when using --from-tsv")
        data = parse_tsv(args.from_tsv, args.bandwidth)
    else:
        with open(args.input) as f:
            data = json.load(f)
        if args.bandwidth:
            data.setdefault("platform", {})["stream_triad_gbps"] = args.bandwidth

    results = score(data, args.alpha, args.tolerance)

    sens = sensitivity_table(data, args.tolerance) if args.sensitivity else None

    if args.json:
        output = {
            "platform": data.get("platform", {}),
            "alpha": args.alpha,
            "tolerance_bp": args.tolerance,
            "results": results,
            "sensitivity": {str(a): r for a, r in sens.items()} if sens else None,
        }
        Path(args.json).write_text(json.dumps(output, indent=2))
        print(f"[score] Intermediate results written to {args.json}", file=sys.stderr)

    print_results(results, data.get("platform", {}), args.alpha, args.tolerance,
                  args.sensitivity, sens)


if __name__ == "__main__":
    main()
