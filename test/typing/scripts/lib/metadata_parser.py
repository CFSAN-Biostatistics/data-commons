"""
Parse and extract typing information from NCBI metadata.
"""

import re
from typing import Dict, List, Optional, Tuple


class MetadataParser:
    """Extract typing information from various metadata sources."""

    @staticmethod
    def extract_serotype(metadata: Dict) -> Tuple[Optional[str], List[Dict], str]:
        """
        Extract Salmonella serotype from metadata.

        Args:
            metadata: Metadata dictionary from NCBI

        Returns:
            Tuple of (serotype, evidence_list, confidence)
        """
        evidence = []
        serotype = None

        # Check BioSample attributes
        if "attributes" in metadata:
            attrs = metadata["attributes"]

            # Check standard serotype fields
            for field in ["serotype", "serovar", "serogroup"]:
                if field in attrs:
                    value = attrs[field]
                    evidence.append({
                        "source": f"BioSample.Attributes.{field}",
                        "value": value
                    })
                    if not serotype:
                        serotype = value

        # Check organism name
        if "organism" in metadata:
            organism_name = metadata["organism"]
            # Look for "serovar X" or "serotype X" in organism name
            serovar_match = re.search(
                r'sero(?:var|type)\s+([A-Za-z0-9\[\],:\-\.\s]+?)(?:\s+str\.|$)',
                organism_name,
                re.IGNORECASE
            )
            if serovar_match:
                value = serovar_match.group(1).strip()
                evidence.append({
                    "source": "BioSample.Organism.name",
                    "value": value
                })
                if not serotype:
                    serotype = value

        # Determine confidence
        if len(evidence) == 0:
            confidence = "low"
        elif len(evidence) == 1:
            if evidence[0]["source"].startswith("BioSample.Attributes"):
                confidence = "high"
            else:
                confidence = "medium"
        else:
            # Check for conflicts
            unique_values = set(e["value"] for e in evidence)
            if len(unique_values) > 1:
                confidence = "conflict"
            else:
                confidence = "high"

        return serotype, evidence, confidence

    @staticmethod
    def extract_mlst_st(metadata: Dict) -> Tuple[Optional[str], List[Dict]]:
        """
        Extract MLST sequence type from metadata.

        Args:
            metadata: Metadata dictionary from NCBI

        Returns:
            Tuple of (sequence_type, evidence_list)
        """
        evidence = []
        st = None

        if "attributes" in metadata:
            attrs = metadata["attributes"]

            # Check for MLST-related fields
            for field in ["MLST", "mlst", "sequence_type", "ST"]:
                if field in attrs:
                    value = attrs[field]
                    evidence.append({
                        "source": f"BioSample.Attributes.{field}",
                        "value": value
                    })
                    if not st:
                        st = value

        return st, evidence

    @staticmethod
    def assess_data_quality(metadata: Dict) -> Dict:
        """
        Assess quality metrics from metadata.

        Args:
            metadata: Metadata dictionary

        Returns:
            Quality metrics dictionary
        """
        quality = {
            "has_reads": False,
            "has_assembly": False,
            "reported_coverage": None,
            "submitter": None
        }

        # Check for coverage information
        if "attributes" in metadata:
            attrs = metadata["attributes"]
            for field in ["coverage", "sequencing_coverage", "depth_of_coverage"]:
                if field in attrs:
                    quality["reported_coverage"] = attrs[field]
                    break

        # Check for submitter
        if "owner" in metadata or "submission" in metadata:
            quality["submitter"] = metadata.get("owner", {}).get("Name") or \
                                 metadata.get("submission", {}).get("organization")

        return quality

    @staticmethod
    def parse_antigenic_formula(formula: str) -> Dict:
        """
        Parse Salmonella antigenic formula into components.

        Args:
            formula: Antigenic formula string (e.g., "1,4,[5],12:i:1,2")

        Returns:
            Dictionary with o_antigen, h1_antigen, h2_antigen lists
        """
        result = {
            "o_antigen": [],
            "h1_antigen": [],
            "h2_antigen": []
        }

        # Split by colons
        parts = formula.split(":")
        if len(parts) < 2:
            return result

        # O antigens (before first colon)
        o_part = parts[0]
        # Split by comma, preserving brackets
        o_antigens = re.findall(r'\[?\d+\]?', o_part)
        result["o_antigen"] = [a.strip() for a in o_antigens if a.strip()]

        # H1 antigens (between first and second colon)
        if len(parts) >= 2:
            h1_part = parts[1]
            if h1_part and h1_part != "-":
                result["h1_antigen"] = [a.strip() for a in h1_part.split(",")]

        # H2 antigens (after second colon)
        if len(parts) >= 3:
            h2_part = parts[2]
            if h2_part and h2_part != "-":
                result["h2_antigen"] = [a.strip() for a in h2_part.split(",")]

        return result

    @staticmethod
    def normalize_serotype_name(serotype: str) -> str:
        """
        Normalize serotype name for consistency.

        Args:
            serotype: Raw serotype string

        Returns:
            Normalized serotype name
        """
        # Remove common prefixes
        serotype = re.sub(r'^Salmonella\s+enterica\s+(?:subsp\.\s+enterica\s+)?sero(?:var|type)\s+', '', serotype, flags=re.IGNORECASE)

        # Remove strain designations
        serotype = re.sub(r'\s+str\.\s+.*$', '', serotype)

        # Capitalize first letter of each word
        serotype = ' '.join(word.capitalize() for word in serotype.split())

        return serotype.strip()
