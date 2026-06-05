"""
NCBI Entrez E-utilities REST API client for linking assemblies to SRA data.
"""

import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional


class EntrezClient:
    """Client for NCBI Entrez E-utilities."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, email: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize Entrez client.

        Args:
            email: Email for NCBI (recommended)
            api_key: NCBI API key for higher rate limits
        """
        self.email = email or "user@example.com"
        self.api_key = api_key
        self._last_request = 0
        self._rate_limit = 0.34 if not api_key else 0.1  # seconds between requests

    def _rate_limit_wait(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self._last_request
        if elapsed < self._rate_limit:
            time.sleep(self._rate_limit - elapsed)
        self._last_request = time.time()

    def _make_request(self, endpoint: str, params: Dict) -> ET.Element:
        """
        Make a request to Entrez E-utilities.

        Args:
            endpoint: API endpoint (e.g., "esearch.fcgi")
            params: Query parameters

        Returns:
            Parsed XML ElementTree root
        """
        self._rate_limit_wait()

        params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key

        url = f"{self.BASE_URL}/{endpoint}?{urllib.parse.urlencode(params)}"

        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return ET.fromstring(response.read())
        except Exception as e:
            raise RuntimeError(f"Entrez request failed: {e}")

    def search_biosample(self, term: str, retmax: int = 100) -> List[str]:
        """
        Search BioSample database.

        Args:
            term: Search term (e.g., "Salmonella Typhimurium[Organism]")
            retmax: Maximum results

        Returns:
            List of BioSample IDs
        """
        root = self._make_request("esearch.fcgi", {
            "db": "biosample",
            "term": term,
            "retmax": str(retmax),
            "retmode": "xml"
        })

        id_list = root.find(".//IdList")
        if id_list is not None:
            return [id_elem.text for id_elem in id_list.findall("Id")]
        return []

    def get_biosample_metadata(self, biosample_id: str) -> Dict:
        """
        Get BioSample metadata.

        Args:
            biosample_id: BioSample numeric ID

        Returns:
            Parsed metadata dictionary
        """
        root = self._make_request("efetch.fcgi", {
            "db": "biosample",
            "id": biosample_id,
            "retmode": "xml"
        })

        metadata = {
            "id": biosample_id,
            "accession": None,
            "organism": None,
            "attributes": {}
        }

        biosample = root.find(".//BioSample")
        if biosample is None:
            return metadata

        # Extract accession
        metadata["accession"] = biosample.get("accession")

        # Extract organism name
        organism_elem = biosample.find(".//Organism/OrganismName")
        if organism_elem is not None:
            metadata["organism"] = organism_elem.text

        # Extract attributes
        for attr in biosample.findall(".//Attribute"):
            attr_name = attr.get("attribute_name")
            attr_value = attr.text
            if attr_name and attr_value:
                metadata["attributes"][attr_name] = attr_value

        return metadata

    def link_biosample_to_sra(self, biosample_id: str) -> List[str]:
        """
        Find SRA runs linked to a BioSample.

        Args:
            biosample_id: BioSample numeric ID

        Returns:
            List of SRA run accessions (SRR...)
        """
        # Link BioSample to SRA
        root = self._make_request("elink.fcgi", {
            "dbfrom": "biosample",
            "db": "sra",
            "id": biosample_id,
            "retmode": "xml"
        })

        sra_ids = []
        for link in root.findall(".//Link/Id"):
            if link.text:
                sra_ids.append(link.text)

        if not sra_ids:
            return []

        # Fetch SRA metadata to get run accessions
        sra_root = self._make_request("efetch.fcgi", {
            "db": "sra",
            "id": ",".join(sra_ids[:10]),  # Limit to first 10
            "retmode": "xml"
        })

        run_accessions = []
        for run in sra_root.findall(".//RUN"):
            accession = run.get("accession")
            if accession and accession.startswith("SRR"):
                run_accessions.append(accession)

        return run_accessions

    def get_assembly_biosample(self, assembly_accession: str) -> Optional[str]:
        """
        Get BioSample accession from assembly accession.

        Args:
            assembly_accession: Assembly accession (GCA/GCF)

        Returns:
            BioSample accession (SAMN...) or None
        """
        root = self._make_request("esearch.fcgi", {
            "db": "assembly",
            "term": assembly_accession,
            "retmode": "xml"
        })

        id_list = root.find(".//IdList")
        if id_list is None or len(id_list) == 0:
            return None

        assembly_id = id_list.find("Id").text

        # Get assembly metadata
        assembly_root = self._make_request("esummary.fcgi", {
            "db": "assembly",
            "id": assembly_id,
            "retmode": "xml"
        })

        # Look for BioSample link in metadata
        for item in assembly_root.findall(".//DocumentSummary/BioSampleAccn"):
            if item.text:
                return item.text

        return None

    def generate_sra_download_command(
        self,
        sra_accession: str,
        output_dir: str = "data"
    ) -> str:
        """
        Generate command to download SRA reads using fasterq-dump.

        Args:
            sra_accession: SRA run accession (SRR...)
            output_dir: Target directory

        Returns:
            Shell command string
        """
        return (
            f"fasterq-dump --gzip --outdir {output_dir}/ {sra_accession} && "
            f"mv {output_dir}/{sra_accession}_1.fastq.gz {output_dir}/reads_1.fq.gz && "
            f"mv {output_dir}/{sra_accession}_2.fastq.gz {output_dir}/reads_2.fq.gz"
        )
