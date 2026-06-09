#!/usr/bin/env python3
"""
Build a divergent haplotype pair for the het-hybrid benchmark (S3).

Slices a region from the input reference as haplotype H1, then derives H2
by injecting SNPs and short indels at the specified divergence rate using
simuG. Outputs H1 FASTA, H2 FASTA, and a truth VCF of injected variants.

Requires simuG in PATH.

Usage:
    build_het_hybrid.py --ref reference.fasta --slice-mb 50 \
        --divergence 1,3,5,8 --indel-fraction 0.15 \
        --seed 1234567 \
        --out-h1 h1.fasta --out-h2 h2.fasta --truth-vcf truth.vcf
"""

import argparse
import random
import subprocess
import sys
from pathlib import Path

try:
    from Bio import SeqIO
    from Bio.Seq import Seq
    from Bio.SeqRecord import SeqRecord
except ImportError:
    sys.exit("ERROR: biopython is required. Install with: pip install biopython")

SLICE_START = 5_000_000


def check_simug():
    result = subprocess.run(["which", "simuG"], capture_output=True)
    if result.returncode != 0:
        sys.exit("ERROR: simuG not found in PATH. Install from https://github.com/yjx1217/simuG")


def write_fasta(seq: str, seq_id: str, path: str):
    record = SeqRecord(Seq(seq), id=seq_id, description="")
    SeqIO.write([record], path, "fasta")


def run_simug(h1_fasta: str, divergence_rate: float, indel_fraction: float, seed: int, out_prefix: str) -> str:
    """Run simuG to inject variants into h1 and return the mutated FASTA path."""
    n_snps_per_kb = int(divergence_rate * (1 - indel_fraction) * 1000)
    n_indels_per_kb = int(divergence_rate * indel_fraction * 1000)

    cmd = [
        "simuG",
        "-refseq", h1_fasta,
        "-snp_count", str(max(1, n_snps_per_kb)),
        "-indel_count", str(max(0, n_indels_per_kb)),
        "-random_seed", str(seed),
        "-prefix", out_prefix,
    ]
    print(f"[build_het_hybrid] Running: {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"ERROR: simuG failed:\n{result.stderr}")

    simug_fasta = f"{out_prefix}.simseq.genome.fa"
    if not Path(simug_fasta).exists():
        sys.exit(f"ERROR: simuG did not produce expected output {simug_fasta}")
    return simug_fasta


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ref", required=True, help="Input reference FASTA")
    parser.add_argument("--slice-mb", type=float, default=50, help="Size of slice to use as H1 (Mb)")
    parser.add_argument("--divergence", default="1,3,5,8",
                        help="Comma-separated divergence values (percent). One H2 per value.")
    parser.add_argument("--indel-fraction", type=float, default=0.15,
                        help="Fraction of divergence that is indels")
    parser.add_argument("--seed", type=int, default=1234567)
    parser.add_argument("--out-h1", required=True, help="Output H1 FASTA")
    parser.add_argument("--out-h2", required=True,
                        help="Output H2 FASTA base path. Divergence value appended: h2_div1.fasta, h2_div3.fasta ...")
    parser.add_argument("--truth-vcf", required=True,
                        help="Output VCF base path. Divergence value appended.")
    args = parser.parse_args()

    check_simug()
    rng = random.Random(args.seed)
    divergence_values = [float(x) for x in args.divergence.split(",")]
    slice_bp = int(args.slice_mb * 1_000_000)

    print(f"[build_het_hybrid] Loading reference from {args.ref}", file=sys.stderr)
    records = list(SeqIO.parse(args.ref, "fasta"))
    if not records:
        sys.exit(f"ERROR: no sequences in {args.ref}")
    ref_seq = str(records[0].seq).upper()

    if len(ref_seq) < SLICE_START + slice_bp:
        sys.exit(f"ERROR: reference too short for {args.slice_mb} Mb slice at offset {SLICE_START}")

    h1_seq = ref_seq[SLICE_START: SLICE_START + slice_bp]
    write_fasta(h1_seq, "H1", args.out_h1)
    print(f"[build_het_hybrid] Wrote H1 ({len(h1_seq):,} bp) to {args.out_h1}", file=sys.stderr)

    out_h2_base = Path(args.out_h2)
    out_vcf_base = Path(args.truth_vcf)

    for div in divergence_values:
        div_tag = f"div{int(div)}" if div == int(div) else f"div{div}".replace(".", "_")
        h2_path = str(out_h2_base.parent / f"{out_h2_base.stem}_{div_tag}{out_h2_base.suffix}")
        vcf_path = str(out_vcf_base.parent / f"{out_vcf_base.stem}_{div_tag}{out_vcf_base.suffix}")
        prefix = str(out_h2_base.parent / f"simug_{div_tag}")

        print(f"[build_het_hybrid] Building H2 at {div}% divergence -> {h2_path}", file=sys.stderr)
        simug_fasta = run_simug(args.out_h1, div / 100.0, args.indel_fraction,
                                rng.randint(1, 2**31 - 1), prefix)

        Path(simug_fasta).rename(h2_path)
        simug_vcf = f"{prefix}.refseq2simseq.SNP.vcf"
        if Path(simug_vcf).exists():
            Path(simug_vcf).rename(vcf_path)
        print(f"[build_het_hybrid]   done: {h2_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
