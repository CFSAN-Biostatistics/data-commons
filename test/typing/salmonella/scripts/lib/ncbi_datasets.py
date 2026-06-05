"""
NCBI Datasets CLI wrapper for searching assemblies and genomes.
"""

import json
import subprocess
from typing import Dict, List, Optional
from pathlib import Path


class DatasetsClient:
    """Wrapper for NCBI datasets CLI tool."""

    def __init__(self):
        """Initialize datasets client."""
        self._check_datasets_installed()

    def _check_datasets_installed(self):
        """Verify datasets CLI is installed."""
        try:
            subprocess.run(
                ["datasets", "--version"],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "NCBI datasets CLI not found. "
                "Install from: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/download-and-install/"
            )

    def search_genomes(
        self,
        taxon: str,
        search_term: Optional[str] = None,
        assembly_level: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search for genomes using datasets CLI.

        Args:
            taxon: Organism name (e.g., "Salmonella enterica")
            search_term: Additional search term (e.g., serotype name)
            assembly_level: Filter by assembly level (complete, chromosome, scaffold, contig)
            limit: Maximum number of results

        Returns:
            List of assembly metadata dictionaries
        """
        cmd = [
            "datasets", "summary", "genome", "taxon", taxon,
            "--limit", str(limit),
            "--as-json-lines"
        ]

        if assembly_level:
            cmd.extend(["--assembly-level", assembly_level])

        if search_term:
            cmd.extend(["--search", search_term])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Parse JSON Lines format
            assemblies = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    assemblies.append(json.loads(line))

            return assemblies

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Datasets search failed: {e.stderr}")

    def get_assembly_metadata(self, accession: str) -> Dict:
        """
        Get detailed metadata for a specific assembly.

        Args:
            accession: Assembly accession (GCA/GCF)

        Returns:
            Assembly metadata dictionary
        """
        cmd = [
            "datasets", "summary", "genome", "accession", accession,
            "--as-json-lines"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Parse first (and only) line
            if result.stdout.strip():
                return json.loads(result.stdout.strip().split('\n')[0])
            else:
                raise ValueError(f"No metadata found for {accession}")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get metadata for {accession}: {e.stderr}")

    def generate_download_command(
        self,
        accession: str,
        output_dir: str = "data"
    ) -> str:
        """
        Generate command to download assembly.

        Args:
            accession: Assembly accession
            output_dir: Target directory

        Returns:
            Shell command string
        """
        return (
            f"datasets download genome accession {accession} "
            f"--include genome --filename {output_dir}/assembly.zip && "
            f"unzip -j {output_dir}/assembly.zip '*/genomic.fna' -d {output_dir}/ && "
            f"mv {output_dir}/genomic.fna {output_dir}/contigs.fa && "
            f"rm {output_dir}/assembly.zip"
        )
