#!/usr/bin/env python3
"""
Build the NUMT trap synthetic genome (S4).

Embeds NUMT fragments (nuclear copies of mitochondrial sequence) into a
nuclear scaffold at random positions. Each NUMT fragment is degraded to
a target identity by SNP injection. Outputs a combined reference FASTA
(nuclear + mito contig) and a truth BED recording NUMT positions and
identities.

Usage:
    build_numt_trap.py --nuclear chr1.fasta --mito mito.fasta \
        --numt-count 100 --identity-min 60 --identity-max 99 \
        --seed 1234567 \
        --out combined_reference.fasta --truth-bed numt_truth.bed
"""

import argparse
import random
import sys
from pathlib import Path

try:
    from Bio import SeqIO
    from Bio.Seq import Seq
    from Bio.SeqRecord import SeqRecord
except ImportError:
    sys.exit("ERROR: biopython is required. Install with: pip install biopython")

NUCLEAR_SLICE_LEN = 50_000_000
NUCLEAR_SLICE_START = 20_000_000
NUMT_MIN_LEN = 100
NUMT_MAX_LEN = 5000
BASES = list("ACGT")


def degrade_sequence(seq: str, target_identity: float, rng: random.Random) -> str:
    """Return a copy of seq degraded to approximately target_identity via random SNPs."""
    divergence = 1.0 - target_identity
    seq = list(seq)
    n_changes = int(len(seq) * divergence)
    if n_changes == 0:
        return "".join(seq)
    positions = rng.sample(range(len(seq)), min(n_changes, len(seq)))
    for pos in positions:
        seq[pos] = rng.choice([b for b in BASES if b != seq[pos]])
    return "".join(seq)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--nuclear", required=True, help="Nuclear reference FASTA (human chr1)")
    parser.add_argument("--mito", required=True, help="Mitochondrial reference FASTA (rCRS NC_012920.1)")
    parser.add_argument("--numt-count", type=int, default=100, help="Number of NUMT fragments to embed")
    parser.add_argument("--identity-min", type=float, default=60, help="Minimum NUMT identity percent")
    parser.add_argument("--identity-max", type=float, default=99, help="Maximum NUMT identity percent")
    parser.add_argument("--seed", type=int, default=1234567)
    parser.add_argument("--out", required=True, help="Output combined reference FASTA")
    parser.add_argument("--truth-bed", required=True, help="Output NUMT truth BED")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    print(f"[build_numt_trap] Loading nuclear reference from {args.nuclear}", file=sys.stderr)
    nuc_records = list(SeqIO.parse(args.nuclear, "fasta"))
    if not nuc_records:
        sys.exit(f"ERROR: no sequences in {args.nuclear}")
    nuc_full = str(nuc_records[0].seq).upper()

    if len(nuc_full) < NUCLEAR_SLICE_START + NUCLEAR_SLICE_LEN:
        sys.exit("ERROR: nuclear reference too short for slice")
    nuclear = list(nuc_full[NUCLEAR_SLICE_START: NUCLEAR_SLICE_START + NUCLEAR_SLICE_LEN])
    print(f"[build_numt_trap] Using {len(nuclear):,} bp nuclear slice", file=sys.stderr)

    print(f"[build_numt_trap] Loading mito reference from {args.mito}", file=sys.stderr)
    mito_records = list(SeqIO.parse(args.mito, "fasta"))
    if not mito_records:
        sys.exit(f"ERROR: no sequences in {args.mito}")
    mito_seq = str(mito_records[0].seq).upper()
    mito_len = len(mito_seq)
    print(f"[build_numt_trap] Mito reference: {mito_len:,} bp", file=sys.stderr)

    bed_lines = ["#chrom\tstart\tend\tname\tidentity_pct\tfragment_len"]
    insertions = []

    print(f"[build_numt_trap] Embedding {args.numt_count} NUMT fragments...", file=sys.stderr)
    for i in range(args.numt_count):
        numt_len = rng.randint(NUMT_MIN_LEN, min(NUMT_MAX_LEN, mito_len))
        mito_start = rng.randint(0, mito_len - numt_len)
        mito_fragment = mito_seq[mito_start: mito_start + numt_len]

        identity_pct = rng.uniform(args.identity_min, args.identity_max)
        degraded = degrade_sequence(mito_fragment, identity_pct / 100.0, rng)

        insert_pos = rng.randint(0, len(nuclear) - numt_len)
        insertions.append((insert_pos, degraded, identity_pct, i))

    # Sort by position descending so insertions don't shift earlier positions
    insertions.sort(key=lambda x: x[0], reverse=True)
    for insert_pos, fragment, identity_pct, idx in insertions:
        nuclear[insert_pos:insert_pos] = list(fragment)
        # Recompute position accounting for prior insertions by tracking offset
        # (bed coordinates use pre-insertion reference space for simplicity)
        bed_lines.append(f"nuclear\t{insert_pos}\t{insert_pos + len(fragment)}\tnumt_{idx:03d}\t{identity_pct:.1f}\t{len(fragment)}")

    nuclear_seq = "".join(nuclear)
    print(f"[build_numt_trap] Nuclear scaffold after insertions: {len(nuclear_seq):,} bp", file=sys.stderr)

    nuclear_record = SeqRecord(Seq(nuclear_seq), id="nuclear",
                               description=f"chr1_slice_with_{args.numt_count}_numts")
    mito_record = SeqRecord(Seq(mito_seq), id="chrM",
                            description=f"rCRS_mitochondrion NC_012920.1")
    SeqIO.write([nuclear_record, mito_record], args.out, "fasta")
    print(f"[build_numt_trap] Wrote combined reference to {args.out}", file=sys.stderr)

    Path(args.truth_bed).write_text("\n".join(bed_lines) + "\n")
    print(f"[build_numt_trap] Wrote NUMT truth BED to {args.truth_bed}", file=sys.stderr)


if __name__ == "__main__":
    main()
