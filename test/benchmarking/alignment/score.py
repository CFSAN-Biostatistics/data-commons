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

Long-read results (every target has "alphabet": "long-read", as written by the phraya SLURM
harness's aggregate_results.py) are scored in a separate mode, auto-detected from the input;
mixing long-read and other alphabets in one file is an error. Differences from short-read:
    - BNT is bases-based: bases_per_s / threads / STREAM GB/s  (20 kb and 150 bp reads are not
      comparable per read). Requires "bases_per_s" on every target; there is no fallback to reads.
    - CAS is the geometric mean of PA over targets (MCS is unimplemented for long reads and a
      non-positive "mcs" is ignored rather than zeroing the score; "va" is used if present).
      A target with "pa": null (e.g. real reads with no truth) is excluded from CAS but still
      counts toward BNT and MEI.
    - "pa" is placement accuracy at the locus tolerance "pa_tolerance_bp" (2000 bp from the harness):
      the best placement's START is within that distance of the true start. CAS uses it. A tight
      start test (100 bp) also penalises soft-clipped read ends, so it is reported separately as
      "pa_start_100bp" and is not part of CAS. --tolerance is not used.
    - Targets with "sweep_of" (read-count sweep points) are excluded from the aggregate
      CAS/BNT/MEI and reported in a separate amortization table.
    - "wall_time_s" is the aligner step only; "plan_time_s" (phraya plan, the index-build
      analogue) is reported but not part of BNT.
    Optional long-read target fields: bases_per_s, plan_time_s, precision, n_truth,
    n_correct_any, wall_cv_pct, unaligned_frac, pa_tolerance_bp, pa_start_100bp, sweep_of;
    planted-repeat targets: n_repeat_inside, n_repeat_both_copies, n_overhang, n_overhang_correct;
    no-truth targets: agree_frac, n_both, n_agree, n_only_this, n_only_ref (agreement of the
    aligner's best placement with minimap2-ont's primary placement).
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


LONG_READ_DETAIL_KEYS = (
    "reads", "wall_time_s", "plan_time_s", "peak_rss_gb", "unaligned_frac", "precision",
    "n_truth", "n_correct_any", "bases_per_s", "wall_cv_pct", "pa_tolerance_bp", "genome_size_gb",
    "pa_start_100bp", "pa_start_tolerance_bp", "agree_frac", "n_both", "n_agree", "n_only_this",
    "n_only_ref", "n_repeat_inside", "n_repeat_both_copies", "n_overhang", "n_overhang_correct",
)


def detect_mode(data: dict) -> str:
    """'long-read' if every target is long-read, 'short-read' otherwise. Mixed is an error:
    bases-based and reads-based BNT cannot be normalized against each other."""
    alphabets = {t.get("alphabet", "dna")
                 for a in data.get("aligners", []) for t in a.get("targets", [])}
    if "long-read" in alphabets and alphabets != {"long-read"}:
        sys.exit("ERROR: results mix long-read and other alphabets "
                 f"({', '.join(sorted(alphabets))}); score them separately")
    return "long-read" if alphabets == {"long-read"} else "short-read"


def compute_bnt_bases(bases_per_s: float, threads: int, bandwidth_gbps: float) -> float:
    if bases_per_s <= 0 or threads <= 0 or bandwidth_gbps <= 0:
        return 0.0
    return bases_per_s / threads / bandwidth_gbps


def compute_cas_long_read(pa: float | None, mcs: float | None, va: float | None) -> float | None:
    """Geometric mean of the accuracy components that exist. PA null -> None (unscored).
    mcs <= 0 is the harness's "not implemented" sentinel, not a measured zero."""
    if pa is None:
        return None
    parts = [pa]
    if mcs is not None and mcs > 0:
        parts.append(mcs)
    if va is not None:
        parts.append(va)
    return geomean(parts)


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
    mode = detect_mode(data)
    long_read = mode == "long-read"

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
            va = t.get("va")
            if long_read:
                bases_per_s = t.get("bases_per_s")
                if not bases_per_s:
                    sys.exit(f"ERROR: long-read target {t.get('id')} for {name} has no bases_per_s "
                             "(wrapper timing.txt needs total_bases)")
                bnt = compute_bnt_bases(bases_per_s, threads, bandwidth)
                cas_t = compute_cas_long_read(t.get("pa"), t.get("mcs"), va)
            else:
                bnt = compute_bnt(t["reads"], t["wall_time_s"], threads, bandwidth)
                cas_t = compute_cas_target(t["pa"], t["mcs"], va)

            peak_rss = t.get("peak_rss_gb")
            genome_size = t.get("genome_size_gb")
            mei = (peak_rss / genome_size) if (peak_rss and genome_size) else None

            if not (long_read and t.get("sweep_of")):
                if cas_t is not None:
                    target_scores.append(cas_t)
                bnt_values.append(bnt)
                if mei is not None:
                    mei_values.append(mei)

            detail = {
                "id": t.get("id"),
                "pa": t.get("pa") if long_read else t["pa"],
                "mcs": t.get("mcs") if long_read else t["mcs"],
                "va": va,
                "cas": cas_t,
                "bnt": bnt,
                "mei": mei,
            }
            if long_read:
                detail["sweep_of"] = t.get("sweep_of")
                detail.update({k: t.get(k) for k in LONG_READ_DETAIL_KEYS})
            target_details.append(detail)

        cas = geomean(target_scores) if target_scores else 0.0
        bnt_agg = geomean(bnt_values) if bnt_values else 0.0
        mei_agg = (sum(mei_values) / len(mei_values)) if mei_values else None

        results.append({
            "name": name,
            "version": version,
            "mode": mode,
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


def print_sensitivity(results: list[dict], alpha: float, sens: dict, col_w: int):
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
        print_sensitivity(results, alpha, sens, col_w)


def print_long_read_results(results: list[dict], platform: dict, alpha: float,
                            show_sensitivity: bool, sens: dict | None = None):
    cpu = platform.get("cpu_model", "")
    bw = platform.get("stream_triad_gbps", "?")
    threads = platform.get("threads", "?")
    all_td = [td for r in results for td in r["target_details"]]
    tols = sorted({td["pa_tolerance_bp"] for td in all_td if td.get("pa_tolerance_bp")})
    tol_str = " / ".join(f"±{t} bp" for t in tols) if tols else "unknown (no pa_tolerance_bp in results)"

    print("\nLong-Read Aligner Benchmark Results")
    print("====================================")
    if cpu:
        print(f"Platform:      {cpu}")
    print(f"STREAM Triad:  {bw} GB/s  |  Threads: {threads}")
    print(f"α = {alpha:.2f}  |  PA tolerance: {tol_str} (set upstream; --tolerance is not used)")
    print("CAS = geometric mean of PA (locus tolerance above) over scored primary targets (MCS/VA not implemented for long reads)")
    print("BNT = bases / (wall × threads) / STREAM GB/s  [b/t·GB]. wall = aligner step only;")
    print("      phraya plan_time_s (read + reference sketching) is shown below, not included in BNT.\n")

    col_w = max(len(r["name"]) for r in results) + 2
    ver_w = max(len(r["version"]) for r in results) + 2
    ranked = sorted(results, key=lambda x: -x["cbs"])

    header = (f"{'Aligner':<{col_w}} {'Version':<{ver_w}}"
              f"{'CAS':>8} {'BNT(b/t·GB)':>13} {'BNT_norm':>10} {'CBS':>8} {'MEI':>6}")
    print(header)
    print("-" * len(header))
    for r in ranked:
        mei_str = f"{r['mei']:.1f}" if r["mei"] is not None else "-"
        print(f"{r['name']:<{col_w}} {r['version']:<{ver_w}}"
              f"{r['cas']:>8.3f} {r['bnt']:>13.1f} {r['bnt_norm']:>10.3f}"
              f" {r['cbs']:>8.3f} {mei_str:>6}")

    primary_ids = []
    for td in all_td:
        if not td.get("sweep_of") and td["id"] not in primary_ids:
            primary_ids.append(td["id"])

    def detail(r, tid):
        return next((td for td in r["target_details"] if td["id"] == tid), None)

    w = max([len(t) for t in primary_ids] + [7]) + 2
    print("\nPer-target PA (primary targets; '-' = no truth / not run):")
    row_header = f"{'Aligner':<{col_w}}" + "".join(f"{t:>{w}}" for t in primary_ids)
    print(row_header)
    print("-" * len(row_header))
    for r in ranked:
        row = f"{r['name']:<{col_w}}"
        for tid in primary_ids:
            td = detail(r, tid)
            row += fmt(td["pa"] if td else None, width=w).rjust(w)
        print(row)

    print("\nPer-target detail (wall = aligner step; plan = phraya plan; Mb/s = input bases per wall second):")
    dh = (f"{'Target':<10}{'Aligner':<{col_w}}{'reads':>8}{'wall_s':>9}{'cv%':>7}{'plan_s':>9}"
          f"{'RSS_GB':>9}{'unal':>8}{'Mb/s':>8}{'PA':>8}{'PA@100':>8}{'prec':>8}")
    print(dh)
    print("-" * len(dh))
    for tid in primary_ids:
        for r in ranked:
            td = detail(r, tid)
            if td is None:
                continue
            mbs = td["bases_per_s"] / 1e6 if td.get("bases_per_s") else None
            print(f"{tid:<10}{r['name']:<{col_w}}"
                  f"{(td.get('reads') or 0):>8d}{fmt(td.get('wall_time_s'), 9, 2)}{fmt(td.get('wall_cv_pct'), 7, 1)}"
                  f"{fmt(td.get('plan_time_s'), 9, 2)}{fmt(td.get('peak_rss_gb'), 9, 3)}"
                  f"{fmt(td.get('unaligned_frac'), 8, 4)}{fmt(mbs, 8, 2)}"
                  f"{fmt(td['pa'], 8, 4)}{fmt(td.get('pa_start_100bp'), 8, 4)}{fmt(td.get('precision'), 8, 4)}")

    rep = [(r, td) for r in ranked for td in r["target_details"] if td.get("n_repeat_inside") is not None]
    if rep:
        print("\nPlanted-repeat targets (PA is ambiguous by design; correct_any = either copy counts):")
        rh = (f"{'Target':<10}{'Aligner':<{col_w}}{'PA':>8}{'any/truth':>12}{'both/inside':>13}{'overhang ok':>13}")
        print(rh)
        print("-" * len(rh))
        for r, td in rep:
            n = td.get("n_truth") or 0
            anyf = f"{td['n_correct_any']}/{n}" if td.get("n_correct_any") is not None else "-"
            print(f"{td['id']:<10}{r['name']:<{col_w}}{fmt(td['pa'], 8, 4)}{anyf:>12}"
                  f"{str(td['n_repeat_both_copies']) + '/' + str(td['n_repeat_inside']):>13}"
                  f"{str(td['n_overhang_correct']) + '/' + str(td['n_overhang']):>13}")

    agr = [(r, td) for r in ranked for td in r["target_details"] if td.get("agree_frac") is not None]
    if agr:
        print("\nNo-truth targets: agreement of best placement with minimap2-ont's primary (never PA):")
        ah = f"{'Target':<10}{'Aligner':<{col_w}}{'both':>8}{'agree':>8}{'frac':>8}{'only_this':>11}{'only_ont':>10}"
        print(ah)
        print("-" * len(ah))
        for r, td in agr:
            print(f"{td['id']:<10}{r['name']:<{col_w}}{td['n_both']:>8d}{td['n_agree']:>8d}"
                  f"{fmt(td['agree_frac'], 8, 4)}{td['n_only_this']:>11d}{td['n_only_ref']:>10d}")

    sweeps = [td for td in all_td if td.get("sweep_of")]
    if sweeps:
        print("\nRead-count sweep (amortization of fixed plan/index cost; excluded from CAS/BNT/MEI):")
        sh = (f"{'Sweep':<8}{'Aligner':<{col_w}}{'reads':>8}{'wall_s':>9}{'plan_s':>9}"
              f"{'ms/read':>10}{'ms/read+plan':>14}")
        print(sh)
        print("-" * len(sh))
        for parent in sorted({td["sweep_of"] for td in sweeps}):
            for r in ranked:
                pts = sorted((td for td in r["target_details"]
                              if td.get("sweep_of") == parent or td["id"] == parent),
                             key=lambda td: td.get("reads") or 0)
                for td in pts:
                    n, wall, plan = td.get("reads") or 0, td.get("wall_time_s"), td.get("plan_time_s")
                    per = wall / n * 1000 if n and wall is not None else None
                    per_plan = (wall + plan) / n * 1000 if n and wall is not None and plan is not None else None
                    print(f"{parent:<8}{r['name']:<{col_w}}{n:>8d}{fmt(wall, 9, 2)}{fmt(plan, 9, 2)}"
                          f"{fmt(per, 10, 2)}{fmt(per_plan, 14, 2)}")

    if show_sensitivity and sens:
        print_sensitivity(results, alpha, sens, col_w)


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
                        help="Placement tolerance in bp for PA (default: 10 per spec). Short-read only; "
                             "long-read PA tolerance is taken from the results (pa_tolerance_bp)")
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
            "mode": detect_mode(data),
            "platform": data.get("platform", {}),
            "alpha": args.alpha,
            "tolerance_bp": args.tolerance,
            "results": results,
            "sensitivity": {str(a): r for a, r in sens.items()} if sens else None,
        }
        Path(args.json).write_text(json.dumps(output, indent=2))
        print(f"[score] Intermediate results written to {args.json}", file=sys.stderr)

    if detect_mode(data) == "long-read":
        print_long_read_results(results, data.get("platform", {}), args.alpha, args.sensitivity, sens)
    else:
        print_results(results, data.get("platform", {}), args.alpha, args.tolerance,
                      args.sensitivity, sens)


if __name__ == "__main__":
    main()
