#!/usr/bin/env python3
"""
Plant a segmental duplication pair into a real single-record reference (T9f).

Copies the block [--src-start, --src-start + --length) to a second locus
(--insert-at, in ORIGINAL reference coordinates), mutating the copy to --identity
(SNPs plus --indel-fraction of single-base indels). All other sequence is unchanged,
so the output stays a natural genome with exactly one engineered repeat pair.

Outputs the new FASTA (same record id) and a 0-based BED of both copies in the NEW
coordinate system. Copy A is the original block; copy B is the inserted mutated copy.

Usage:
    build_embedded_segdup.py --ref base.fasta --src-start 1500000 --length 20000 \
        --insert-at 3200000 --identity 99.0 --seed 9106 \
        --out reference.fasta --truth-bed segdup_truth.bed
"""

from __future__ import annotations

import argparse
import random
import sys

BASES = "ACGT"


def read_single_fasta(path: str) -> tuple[str, str, str]:
    """Return (record id, header description, uppercase sequence)."""
    header = None
    parts: list[str] = []
    with open(path) as fh:
        for line in fh:
            line = line.rstrip("\r\n")
            if line.startswith(">"):
                if header is not None:
                    sys.exit(f"ERROR: {path} has more than one record")
                header = line[1:]
            elif line:
                parts.append(line)
    if header is None:
        sys.exit(f"ERROR: no FASTA record in {path}")
    rid = header.split()[0]
    return rid, header[len(rid):].strip(), "".join(parts).upper()


def mutate_block(seq: str, identity: float, indel_fraction: float, rng: random.Random) -> str:
    div = 1.0 - identity
    out: list[str] = []
    for b in seq:
        if rng.random() >= div:
            out.append(b)
        elif rng.random() < indel_fraction:
            if rng.random() < 0.5:
                continue  # deletion
            out.append(b)
            out.append(rng.choice(BASES))  # insertion after b
        else:
            out.append(rng.choice([x for x in BASES if x != b]))
    return "".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--src-start", type=int, required=True)
    ap.add_argument("--length", type=int, required=True)
    ap.add_argument("--insert-at", type=int, required=True)
    ap.add_argument("--identity", type=float, required=True, help="percent, e.g. 99.0")
    ap.add_argument("--indel-fraction", type=float, default=0.1)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--truth-bed", required=True)
    args = ap.parse_args()

    rid, desc, ref = read_single_fasta(args.ref)
    src_end = args.src_start + args.length
    if not 0 <= args.src_start < src_end <= len(ref):
        sys.exit("ERROR: source block outside reference")
    if not 0 <= args.insert_at <= len(ref):
        sys.exit("ERROR: --insert-at outside reference")
    if args.src_start < args.insert_at < src_end:
        sys.exit("ERROR: --insert-at falls inside the source block")
    if not 0.0 < args.identity < 100.0:
        sys.exit("ERROR: --identity must be in (0, 100)")

    rng = random.Random(args.seed)
    copy = mutate_block(ref[args.src_start:src_end], args.identity / 100.0, args.indel_fraction, rng)
    new = ref[:args.insert_at] + copy + ref[args.insert_at:]

    a_start = args.src_start if args.insert_at > args.src_start else args.src_start + len(copy)
    b_start = args.insert_at if args.insert_at > args.src_start else args.insert_at
    intervals = [("copy_A", a_start, a_start + args.length),
                 ("copy_B", b_start, b_start + len(copy))]
    with open(args.out, "w") as fh:
        fh.write(f">{rid} {desc} with planted segdup\n".replace("  ", " "))
        for i in range(0, len(new), 80):
            fh.write(new[i:i + 80] + "\n")
    with open(args.truth_bed, "w") as fh:
        for name, s, e in sorted(intervals, key=lambda t: t[1]):
            fh.write(f"{rid}\t{s}\t{e}\t{name}\t{args.identity:.1f}\n")
    print(f"[build_embedded_segdup] {len(ref):,} -> {len(new):,} bp; "
          f"A={a_start}-{a_start + args.length} B={b_start}-{b_start + len(copy)}", file=sys.stderr)


if __name__ == "__main__":
    main()
