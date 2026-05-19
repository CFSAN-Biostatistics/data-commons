"""
Build manifest.json files from discovered metadata.
"""

import json
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path


class ManifestBuilder:
    """Build manifest.json from NCBI metadata and typing system config."""

    @staticmethod
    def create_manifest(
        organism: str,
        subspecies: Optional[str],
        biosample_accession: str,
        sra_accession: Optional[str],
        assembly_accession: Optional[str],
        serotype: Optional[str],
        serotype_evidence: list,
        st: Optional[str],
        st_evidence: list,
        quality_metrics: Dict,
        metadata_confidence: str,
        antigenic_components: Optional[Dict] = None,
        mlst_scheme: Optional[str] = None,
        difficulty: str = "common",
        notes: str = "",
        curation_notes: str = ""
    ) -> Dict:
        """
        Create a complete manifest dictionary.

        Args:
            organism: Organism name
            subspecies: Subspecies/strain
            biosample_accession: BioSample accession
            sra_accession: SRA run accession (or None)
            assembly_accession: Assembly accession (or None)
            serotype: Extracted serotype
            serotype_evidence: List of serotype evidence dicts
            st: Extracted sequence type
            st_evidence: List of ST evidence dicts
            quality_metrics: Quality assessment dict
            metadata_confidence: Overall confidence level
            antigenic_components: Parsed antigenic formula components
            mlst_scheme: MLST scheme name
            difficulty: Test case difficulty category
            notes: High-level notes
            curation_notes: Detailed curation notes

        Returns:
            Manifest dictionary
        """
        manifest = {
            "organism": organism,
            "curation": {
                "date": datetime.now().isoformat()[:10],
                "ncbi_accessions": {
                    "biosample": biosample_accession,
                    "sra": sra_accession,
                    "assembly": assembly_accession
                },
                "metadata_confidence": metadata_confidence,
                "serotype_evidence": serotype_evidence,
                "st_evidence": st_evidence,
                "quality_metrics": quality_metrics,
                "notes": curation_notes
            },
            "ground_truth": {
                "serological": {},
                "mlst": {}
            },
            "data_sources": {
                "reads": {
                    "sra_accession": sra_accession,
                    "download_cmd": None
                },
                "assembly": {
                    "accession": assembly_accession,
                    "download_cmd": None
                }
            },
            "tools": {},
            "validation_instructions": {
                "serological": "",
                "mlst": ""
            },
            "difficulty": difficulty,
            "notes": notes
        }

        # Add subspecies if provided
        if subspecies:
            manifest["subspecies"] = subspecies

        # Build serological ground truth
        if serotype:
            manifest["ground_truth"]["serological"]["serotype"] = serotype

        if antigenic_components:
            manifest["ground_truth"]["serological"].update({
                "antigenic_formula": None,  # To be filled manually
                "o_antigen": antigenic_components.get("o_antigen", []),
                "h1_antigen": antigenic_components.get("h1_antigen", []),
                "h2_antigen": antigenic_components.get("h2_antigen", [])
            })

        # Build MLST ground truth
        if mlst_scheme:
            manifest["ground_truth"]["mlst"]["scheme"] = mlst_scheme
        manifest["ground_truth"]["mlst"]["sequence_type"] = st

        # Generate download commands
        if sra_accession:
            manifest["data_sources"]["reads"]["download_cmd"] = (
                f"fasterq-dump --gzip --outdir data/ {sra_accession} && "
                f"mv data/{sra_accession}_1.fastq.gz data/reads_1.fq.gz && "
                f"mv data/{sra_accession}_2.fastq.gz data/reads_2.fq.gz"
            )

        if assembly_accession:
            manifest["data_sources"]["assembly"]["download_cmd"] = (
                f"datasets download genome accession {assembly_accession} "
                f"--include genome --filename data/assembly.zip && "
                f"unzip -j data/assembly.zip '*/genomic.fna' -d data/ && "
                f"mv data/genomic.fna data/contigs.fa && "
                f"rm data/assembly.zip"
            )

        return manifest

    @staticmethod
    def add_tool_config(
        manifest: Dict,
        tool_name: str,
        input_type: str,
        run_cmd: str,
        reference_output: str
    ) -> Dict:
        """
        Add tool configuration to manifest.

        Args:
            manifest: Manifest dictionary
            tool_name: Name of typing tool
            input_type: "reads", "assembly", or "both"
            run_cmd: Command to run tool
            reference_output: Path to expected output

        Returns:
            Updated manifest
        """
        manifest["tools"][tool_name] = {
            "input_type": input_type,
            "run_cmd": run_cmd,
            "reference_output": reference_output
        }
        return manifest

    @staticmethod
    def write_manifest(manifest: Dict, output_path: Path):
        """
        Write manifest to JSON file.

        Args:
            manifest: Manifest dictionary
            output_path: Path to write manifest.json
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)

    @staticmethod
    def generate_case_directory_name(
        organism_prefix: str,
        identifier: str,
        sra_accession: Optional[str]
    ) -> str:
        """
        Generate test case directory name.

        Args:
            organism_prefix: Short organism prefix (e.g., "sal", "ecoli")
            identifier: Type identifier (e.g., "typhimurium", "o157h7")
            sra_accession: SRA accession (or None)

        Returns:
            Directory name string
        """
        name_parts = [organism_prefix, identifier]

        if sra_accession:
            name_parts.append(sra_accession)
        else:
            # Use timestamp as fallback
            name_parts.append(datetime.now().strftime("%Y%m%d"))

        return "_".join(name_parts).lower().replace(" ", "_")
