#!/usr/bin/env python3
"""
Build a segmental duplication array synthetic genome (S1).

Selects a 1 Mb core block from the input reference, creates N copies each
mutated to a target pairwise identity via random SNP/indel injection, and
separates copies with unique spacer sequences. Outputs a synthetic FASTA,
a truth BED of copy coordinates, and a TSV mapping copy index to identity.

Usage:
    build_segdup.py --ref reference.fasta --copies 20 \
        --identities 98.0,99.0,99.5,99.9 --spacer-kb 75 \
        --seed 1234567 --out synthetic.fasta \
        --truth-bed truth.bed --identity-map copy_identity_map.tsv
"""

import argparse
import random
import sys
from pathlib import Path

try:
    from Bio import SeqIO
    from Bio.Seq import Seq, MutableSeq
    from Bio.SeqRecord import SeqRecord
except ImportError:
    sys.exit("ERROR: biopython is required. Install with: pip install biopython")


CORE_BLOCK_START = 10_000_000
CORE_BLOCK_LEN = 1_000_000
BASES = list("ACGT")


def random_spacer(length: int, rng: random.Random) -> str:
    """Generate a unique random spacer sequence."""
    return "".join(rng.choice(BASES) for _ in range(length))


def mutate_sequence(seq: str, target_identity: float, indel_fraction: float, rng: random.Random) -> str:
    """Return a mutated copy of seq at approximately target_identity (0-1)."""
    divergence = 1.0 - target_identity
    seq = list(seq)
    n = len(seq)
    n_changes = int(n * divergence)
    n_indels = int(n_changes * indel_fraction)
    n_snps = n_changes - n_indels

    positions = rng.sample(range(n), min(n_changes, n))
    snp_positions = set(positions[:n_snps])
    indel_positions = set(positions[n_snps:n_snps + n_indels])

    result = []
    i = 0
    while i < len(seq):
        if i in snp_positions:
            alt = rng.choice([b for b in BASES if b != seq[i]])
            result.append(alt)
            i += 1
        elif i in indel_positions:
            if rng.random() < 0.5:
                # deletion — skip this base
                i += 1
            else:
                # insertion — add extra base
                result.append(seq[i])
                result.append(rng.choice(BASES))
                i += 1
        else:
            result.append(seq[i])
            i += 1
    return "".join(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ref", required=True, help="Input reference FASTA (human chr1)")
    parser.add_argument("--copies", type=int, default=20, help="Number of copies to generate")
    parser.add_argument("--identities", default="98.0,99.0,99.5,99.9",
                        help="Comma-separated identity values (percent). Assigned round-robin to copies.")
    parser.add_argument("--spacer-kb", type=int, default=75, help="Spacer length in kb between copies")
    parser.add_argument("--indel-fraction", type=float, default=0.1,
                        help="Fraction of divergence events that are indels (default 0.1)")
    parser.add_argument("--seed", type=int, default=1234567, help="RNG seed")
    parser.add_argument("--out", required=True, help="Output synthetic FASTA")
    parser.add_argument("--truth-bed", required=True, help="Output truth BED (copy coordinates)")
    parser.add_argument("--identity-map", required=True, help="Output TSV (copy_index, identity, start, end)")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    identities = [float(x) / 100.0 for x in args.identities.split(",")]
    spacer_len = args.spacer_kb * 1000

    print(f"[build_segdup] Loading reference from {args.ref}", file=sys.stderr)
    records = list(SeqIO.parse(args.ref, "fasta"))
    if not records:
        sys.exit(f"ERROR: no sequences found in {args.ref}")
    ref_seq = str(records[0].seq).upper()

    if len(ref_seq) < CORE_BLOCK_START + CORE_BLOCK_LEN:
        sys.exit(f"ERROR: reference too short for core block extraction (need {CORE_BLOCK_START + CORE_BLOCK_LEN} bp)")

    core = ref_seq[CORE_BLOCK_START: CORE_BLOCK_START + CORE_BLOCK_LEN]
    print(f"[build_segdup] Extracted {len(core):,} bp core block at offset {CORE_BLOCK_START:,}", file=sys.stderr)

    synthetic_seq = ""
    bed_lines = []
    map_lines = ["copy_index\tidentity_percent\tstart\tend\tlength"]
    pos = 0

    for i in range(args.copies):
        identity = identities[i % len(identities)]
        identity_pct = identity * 100.0

        # Add spacer (first spacer is an anchor before copy 0)
        spacer = random_spacer(spacer_len, rng)
        synthetic_seq += spacer
        pos += spacer_len

        # Mutate core to target identity
        copy_seq = mutate_sequence(core, identity, args.indel_fraction, rng)
        copy_start = pos
        copy_end = pos + len(copy_seq)
        synthetic_seq += copy_seq
        pos += len(copy_seq)

        bed_lines.append(f"synthetic\t{copy_start}\t{copy_end}\tcopy_{i:03d}\t{identity_pct:.1f}")
        map_lines.append(f"{i:03d}\t{identity_pct:.1f}\t{copy_start}\t{copy_end}\t{len(copy_seq)}")

        print(f"[build_segdup]   copy {i:03d}: identity={identity_pct:.1f}% len={len(copy_seq):,} pos={copy_start:,}-{copy_end:,}",
              file=sys.stderr)

    # Final trailing spacer
    synthetic_seq += random_spacer(spacer_len, rng)

    out_record = SeqRecord(Seq(synthetic_seq), id="synthetic", description=f"segdup_array_{args.copies}copies")
    SeqIO.write([out_record], args.out, "fasta")
    print(f"[build_segdup] Wrote {len(synthetic_seq):,} bp to {args.out}", file=sys.stderr)

    Path(args.truth_bed).write_text("\n".join(bed_lines) + "\n")
    print(f"[build_segdup] Wrote truth BED to {args.truth_bed}", file=sys.stderr)

    Path(args.identity_map).write_text("\n".join(map_lines) + "\n")
    print(f"[build_segdup] Wrote identity map to {args.identity_map}", file=sys.stderr)


if __name__ == "__main__":
    main()
