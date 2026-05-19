#!/usr/bin/env python3
"""
Discover and generate test case manifests from NCBI data.

This script searches NCBI for assemblies/reads matching typing system targets,
extracts metadata, scores candidates, and generates manifest.json files.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from ncbi_datasets import DatasetsClient
from ncbi_entrez import EntrezClient
from metadata_parser import MetadataParser
from confidence_scorer import ConfidenceScorer
from manifest_builder import ManifestBuilder


def parse_config_markdown(config_path: Path) -> Dict:
    """
    Parse typing system markdown config to extract targets.

    Args:
        config_path: Path to config markdown file

    Returns:
        Dictionary with typing_system, organism, targets list
    """
    with open(config_path) as f:
        content = f.read()

    config = {
        "typing_system": None,
        "organism": None,
        "targets": []
    }

    # Extract typing system from filename
    config["typing_system"] = config_path.stem

    # Extract organism from first heading or content
    organism_match = re.search(r'#\s+([A-Z][a-z]+(?:\s+[a-z]+)*)', content)
    if organism_match:
        config["organism"] = organism_match.group(1)

    # Extract target serotypes/types from markdown lists
    # Look for patterns like:
    # - **TypeName** (priority: high) - Description
    target_pattern = r'-\s+\*\*([^*]+)\*\*\s+\(priority:\s+(critical|high|medium|low)\)\s*-\s*(.+)'

    for match in re.finditer(target_pattern, content, re.MULTILINE):
        target_name = match.group(1).strip()
        priority = match.group(2).strip()
        description = match.group(3).strip()

        config["targets"].append({
            "name": target_name,
            "priority": priority,
            "description": description
        })

    return config


def discover_salmonella_serotype(
    serotype: str,
    datasets_client: DatasetsClient,
    entrez_client: EntrezClient,
    limit: int = 5
) -> List[Dict]:
    """
    Discover candidates for a Salmonella serotype.

    Args:
        serotype: Target serotype name
        datasets_client: NCBI datasets client
        entrez_client: Entrez client
        limit: Max candidates to return

    Returns:
        List of candidate dictionaries with metadata and scores
    """
    candidates = []
    parser = MetadataParser()
    scorer = ConfidenceScorer()

    print(f"  Searching for {serotype}...")

    # Search using datasets
    try:
        assemblies = datasets_client.search_genomes(
            taxon="Salmonella enterica",
            search_term=serotype,
            limit=limit * 2  # Get more to filter
        )
    except Exception as e:
        print(f"  Warning: Datasets search failed: {e}")
        assemblies = []

    for assembly_data in assemblies[:limit]:
        try:
            # Extract basic info
            assembly_acc = assembly_data.get("accession")
            if not assembly_acc:
                continue

            # Get BioSample from assembly
            biosample_acc = entrez_client.get_assembly_biosample(assembly_acc)
            if not biosample_acc:
                continue

            # Search for BioSample ID
            biosample_ids = entrez_client.search_biosample(f"{biosample_acc}[Accession]")
            if not biosample_ids:
                continue

            # Get BioSample metadata
            biosample_metadata = entrez_client.get_biosample_metadata(biosample_ids[0])

            # Extract typing information
            extracted_serotype, serotype_evidence, confidence = parser.extract_serotype(biosample_metadata)
            st, st_evidence = parser.extract_mlst_st(biosample_metadata)
            quality = parser.assess_data_quality(biosample_metadata)

            # Update quality with assembly info
            quality["has_assembly"] = True

            # Try to find linked SRA
            sra_accessions = entrez_client.link_biosample_to_sra(biosample_ids[0])
            sra_acc = sra_accessions[0] if sra_accessions else None
            if sra_acc:
                quality["has_reads"] = True

            # Score candidate
            score = scorer.score_metadata_confidence(
                confidence,
                serotype_evidence,
                st_evidence,
                quality
            )

            # Build candidate
            candidate = {
                "target_serotype": serotype,
                "biosample_accession": biosample_acc,
                "assembly_accession": assembly_acc,
                "sra_accession": sra_acc,
                "extracted_serotype": extracted_serotype,
                "sequence_type": st,
                "confidence": confidence,
                "score": score,
                "serotype_evidence": serotype_evidence,
                "st_evidence": st_evidence,
                "quality_metrics": quality,
                "organism_name": biosample_metadata.get("organism")
            }

            candidates.append(candidate)

        except Exception as e:
            print(f"  Warning: Failed to process assembly {assembly_data.get('accession')}: {e}")
            continue

    return candidates


def generate_manifest_from_candidate(
    candidate: Dict,
    typing_system: str,
    output_dir: Path
) -> Path:
    """
    Generate manifest.json from a candidate.

    Args:
        candidate: Candidate dictionary
        typing_system: Typing system name
        output_dir: Base output directory

    Returns:
        Path to generated manifest
    """
    builder = ManifestBuilder()

    # Determine organism prefix and identifier
    organism_prefix = "sal"  # TODO: Make configurable
    identifier = candidate["target_serotype"].lower().replace(" ", "_").replace(",", "").replace(":", "")

    # Generate directory name
    case_dir_name = builder.generate_case_directory_name(
        organism_prefix,
        identifier,
        candidate.get("sra_accession")
    )

    case_dir = output_dir / case_dir_name

    # Create manifest
    manifest = builder.create_manifest(
        organism="Salmonella enterica",
        subspecies="enterica",
        biosample_accession=candidate["biosample_accession"],
        sra_accession=candidate.get("sra_accession"),
        assembly_accession=candidate.get("assembly_accession"),
        serotype=candidate.get("extracted_serotype"),
        serotype_evidence=candidate["serotype_evidence"],
        st=candidate.get("sequence_type"),
        st_evidence=candidate["st_evidence"],
        quality_metrics=candidate["quality_metrics"],
        metadata_confidence=candidate["confidence"],
        mlst_scheme="senterica",
        difficulty="common",  # TODO: Determine from config
        notes=f"Target serotype: {candidate['target_serotype']}. Generated by discovery script.",
        curation_notes=f"Discovered from NCBI. Confidence score: {candidate['score']['overall']:.1f}/100. Original organism name: {candidate.get('organism_name', 'N/A')}"
    )

    # Add default tool configurations
    if candidate.get("sra_accession"):
        builder.add_tool_config(
            manifest,
            "SeqSero2",
            "reads",
            "SeqSero2_package.py -m a -t 4 -i data/reads_1.fq.gz data/reads_2.fq.gz -d actual/seqsero2/ -n seqsero2",
            "expected/seqsero2/SeqSero_result.tsv"
        )

    if candidate.get("assembly_accession"):
        builder.add_tool_config(
            manifest,
            "MLST",
            "assembly",
            "mlst --scheme senterica data/contigs.fa > actual/mlst/mlst_report.tsv",
            "expected/mlst/mlst_report.tsv"
        )

    # Write manifest
    manifest_path = case_dir / "manifest.json"
    builder.write_manifest(manifest, manifest_path)

    return manifest_path


def main():
    parser = argparse.ArgumentParser(
        description="Discover typing test cases from NCBI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to typing system config markdown"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("test/typing"),
        help="Output directory for test cases"
    )
    parser.add_argument(
        "--candidates-per-target",
        type=int,
        default=3,
        help="Number of candidates to generate per target"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=50.0,
        help="Minimum confidence score (0-100)"
    )
    parser.add_argument(
        "--email",
        help="Email for NCBI Entrez (recommended)"
    )

    args = parser.parse_args()

    # Parse config
    print(f"Parsing config: {args.config}")
    config = parse_config_markdown(args.config)

    if not config["targets"]:
        print("ERROR: No targets found in config file")
        return 1

    print(f"Found {len(config['targets'])} targets in config")

    # Initialize clients
    datasets_client = DatasetsClient()
    entrez_client = EntrezClient(email=args.email)
    scorer = ConfidenceScorer()

    # Discover candidates for each target
    all_candidates = []

    for target in config["targets"]:
        print(f"\nProcessing target: {target['name']} (priority: {target['priority']})")

        candidates = discover_salmonella_serotype(
            target["name"],
            datasets_client,
            entrez_client,
            limit=args.candidates_per_target
        )

        # Filter and rank
        candidates = scorer.filter_candidates(candidates, min_score=args.min_score)
        candidates = scorer.rank_candidates(candidates)

        print(f"  Found {len(candidates)} candidates meeting criteria")

        all_candidates.extend(candidates[:args.candidates_per_target])

    # Generate manifests
    print(f"\nGenerating manifests for {len(all_candidates)} candidates...")

    generated = []
    for candidate in all_candidates:
        try:
            manifest_path = generate_manifest_from_candidate(
                candidate,
                config["typing_system"],
                args.output
            )
            generated.append(manifest_path)
            print(f"  Generated: {manifest_path}")
        except Exception as e:
            print(f"  ERROR: Failed to generate manifest for {candidate.get('biosample_accession')}: {e}")

    print(f"\nSuccessfully generated {len(generated)} manifests")
    print("\nNext steps:")
    print("1. Review and edit generated manifests (especially validation_instructions)")
    print("2. Download data: ./download.sh --all")
    print("3. Run tools: ./run.sh --all")
    print("4. Commit expected outputs to repo")

    return 0


if __name__ == "__main__":
    sys.exit(main())
