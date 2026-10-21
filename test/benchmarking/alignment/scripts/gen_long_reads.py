#!/usr/bin/env python3
"""
Simulate ONT/PacBio-style long reads from a real reference FASTA with exact truth.

Single-end reads, one molecule per read, ~50% reverse-complemented. Errors follow a
long-read profile: each base errs with probability --read-error; --indel-frac of
errors are indels (insertion/deletion 50/50, geometric length p=0.5 capped at
--max-indel-len), the rest substitutions. Quality is a constant '?' string.

Output (the harness layout for ALPHABET=long-read):
    <reads-out>                 FASTQ, uncompressed
    <reads-out>.truth.tsv       read_id chrom true_start strand true_end n_subs n_ins n_del indel_events

`true_start` is the 0-based leftmost reference coordinate of the source fragment and
`true_end = true_start + fragment length` (half-open). `indel_events` is a ';'-separated
list of `offset:op:len` (1-based offset into the fragment in reference orientation).
The truth TSV matches the format written by phraya's gen_synthetic_long.py.

Determinism: the output is a pure function of (reference, arguments, --seed). Reads are
generated sequentially, so the first N reads of a run with --num-reads M > N are
identical to a run with --num-reads N (used for read-count sweeps).

Fragments containing any non-ACGT base (e.g. N gaps in human assemblies) are rejected
and redrawn. --region-bed restricts fragments to those overlapping the BED intervals
(chosen uniformly per read), for targeted tests such as segmental duplications.

Usage:
    gen_long_reads.py --reference ref.fasta --reads-out reads_1.fq --seed 9101 \
        --num-reads 2000 --min-len 10000 --max-len 30000 --read-error 0.12
"""

from __future__ import annotations

import argparse
import math
import random
import re
import sys

BASES = "ACGT"
COMP = str.maketrans("ACGT", "TGCA")
NON_ACGT = re.compile(r"[^ACGT]")
MAX_REDRAWS = 1000


def read_single_fasta(path: str) -> tuple[str, str]:
    """Return (record id, uppercase sequence). Exactly one record is required."""
    name = None
    parts: list[str] = []
    with open(path) as fh:
        for line in fh:
            line = line.rstrip("\r\n")
            if line.startswith(">"):
                if name is not None:
                    sys.exit(f"ERROR: {path} has more than one record; expected a single sequence")
                name = line[1:].split()[0]
            elif line:
                parts.append(line)
    if name is None:
        sys.exit(f"ERROR: no FASTA record in {path}")
    return name, "".join(parts).upper()


def read_bed(path: str, chrom: str, genome: int) -> list[tuple[int, int]]:
    regions = []
    with open(path) as fh:
        for line in fh:
            f = line.split("\t")
            if len(f) < 3 or line.startswith(("#", "track", "browser")):
                continue
            if f[0] != chrom:
                continue
            s, e = int(f[1]), int(f[2])
            if not 0 <= s < e <= genome:
                sys.exit(f"ERROR: BED interval {f[0]}:{s}-{e} outside reference (length {genome})")
            regions.append((s, e))
    if not regions:
        sys.exit(f"ERROR: no intervals for {chrom} in {path}")
    return regions


def mutate(frag: str, p: float, indel_frac: float, max_indel_len: int,
           rng: random.Random) -> tuple[str, int, int, int, str]:
    """Apply the long-read error model. Returns (seq, n_subs, n_ins, n_del, events)."""
    if p <= 0.0:
        return frag, 0, 0, 0, ""
    n = len(frag)
    log_clean = math.log1p(-p) if p < 1.0 else None
    out: list[str] = []
    events: list[str] = []
    n_subs = n_ins = n_del = 0
    i = 0
    while i < n:
        # Clean bases before the next error ~ Geometric(p).
        run = 0 if log_clean is None else int(math.log(1.0 - rng.random()) / log_clean)
        if i + run >= n:
            out.append(frag[i:])
            break
        out.append(frag[i:i + run])
        i += run
        if rng.random() < indel_frac:
            length = 1
            while length < max_indel_len and rng.random() < 0.5:
                length += 1
            if rng.random() < 0.5:  # insertion before base i
                out.append("".join(rng.choices(BASES, k=length)))
                n_ins += length
                events.append(f"{i + 1}:I:{length}")
            else:  # deletion of bases i..i+length
                length = min(length, n - i)
                n_del += length
                events.append(f"{i + 1}:D:{length}")
                i += length
        else:  # substitution
            alt = rng.choice(BASES)
            while alt == frag[i]:
                alt = rng.choice(BASES)
            out.append(alt)
            n_subs += 1
            i += 1
    return "".join(out), n_subs, n_ins, n_del, ";".join(events)


def draw_start(read_len: int, genome: int, regions: list[tuple[int, int]] | None,
               rng: random.Random) -> int:
    max_start = genome - read_len
    if regions is None:
        return rng.randint(0, max_start)
    s, e = regions[rng.randrange(len(regions))]
    lo = max(0, s - read_len + 1)  # fragment overlaps [s, e) by at least 1 bp
    hi = min(e - 1, max_start)
    if lo > hi:
        return rng.randint(0, max_start)
    return rng.randint(lo, hi)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reference", required=True, help="single-record reference FASTA")
    ap.add_argument("--reads-out", required=True, help="output FASTQ; truth goes to <reads-out>.truth.tsv")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--num-reads", type=int, required=True)
    ap.add_argument("--min-len", type=int, required=True)
    ap.add_argument("--max-len", type=int, required=True)
    ap.add_argument("--read-error", type=float, required=True, help="per-base error rate in [0,1]")
    ap.add_argument("--indel-frac", type=float, default=0.70, help="fraction of errors that are indels")
    ap.add_argument("--max-indel-len", type=int, default=50)
    ap.add_argument("--region-bed", help="BED; only draw fragments overlapping these intervals")
    args = ap.parse_args()

    if not 0.0 <= args.read_error <= 1.0:
        sys.exit(f"ERROR: --read-error must be in [0,1], got {args.read_error}")
    if not 0.0 <= args.indel_frac <= 1.0:
        sys.exit(f"ERROR: --indel-frac must be in [0,1], got {args.indel_frac}")
    if not 0 < args.min_len <= args.max_len:
        sys.exit("ERROR: need 0 < --min-len <= --max-len")

    chrom, ref = read_single_fasta(args.reference)
    genome = len(ref)
    if genome < args.max_len:
        sys.exit(f"ERROR: reference ({genome} bp) shorter than --max-len ({args.max_len})")
    regions = read_bed(args.region_bed, chrom, genome) if args.region_bed else None

    rng = random.Random(args.seed)
    truth_path = f"{args.reads_out}.truth.tsv"
    qual_char = "?"
    with open(args.reads_out, "w") as fq, open(truth_path, "w") as tr:
        tr.write("read_id\tchrom\ttrue_start\tstrand\ttrue_end\tn_subs\tn_ins\tn_del\tindel_events\n")
        for i in range(args.num_reads):
            for _ in range(MAX_REDRAWS):
                read_len = rng.randint(args.min_len, args.max_len)
                start = draw_start(read_len, genome, regions, rng)
                frag = ref[start:start + read_len]
                if not NON_ACGT.search(frag):
                    break
            else:
                sys.exit(f"ERROR: could not draw an ACGT-only fragment after {MAX_REDRAWS} attempts")
            strand = "+"
            if rng.random() < 0.5:
                strand = "-"
            seq, n_subs, n_ins, n_del, events = mutate(
                frag, args.read_error, args.indel_frac, args.max_indel_len, rng)
            if strand == "-":
                seq = seq.translate(COMP)[::-1]
            rid = f"longread_{i}"
            fq.write(f"@{rid} pos={start} strand={strand}\n{seq}\n+\n{qual_char * len(seq)}\n")
            tr.write(f"{rid}\t{chrom}\t{start}\t{strand}\t{start + read_len}\t"
                     f"{n_subs}\t{n_ins}\t{n_del}\t{events}\n")

    print(f"[gen_long_reads] {args.num_reads} reads from {chrom} ({genome:,} bp), "
          f"len {args.min_len}-{args.max_len}, err={args.read_error}, "
          f"indel_frac={args.indel_frac}, seed={args.seed} -> {args.reads_out}", file=sys.stderr)


if __name__ == "__main__":
    main()
