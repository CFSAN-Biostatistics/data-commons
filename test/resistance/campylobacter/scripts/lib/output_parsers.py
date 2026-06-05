"""
Parsers for AMR tool output formats.
Each parser returns a normalized structure for use by validate.py.
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional


def parse_resfinder_json(path: Path) -> Dict:
    """
    Parse ResFinder JSON output.

    Returns:
        {
            "genes": [{"gene": str, "identity": float, "coverage": float, "drug_class": str}],
            "resistant_phenotypes": [str],
            "susceptible_phenotypes": [str],
            "phenotype_summary": str
        }
    """
    with open(path) as f:
        data = json.load(f)

    genes = []
    for key, region in data.get("seq_regions", {}).items():
        genes.append({
            "gene": region.get("name", key.split(";;")[0]),
            "identity": region.get("identity", None),
            "coverage": region.get("ref_coverage", None),
            "drug_class": region.get("amr_classes", [None])[0] if region.get("amr_classes") else None,
        })

    resistant = [
        k for k, v in data.get("phenotypes", {}).items()
        if v.get("amr_resistant")
    ]
    susceptible = [
        k for k, v in data.get("phenotypes", {}).items()
        if not v.get("amr_resistant") and v.get("amr_species_relevant")
    ]

    return {
        "genes": genes,
        "resistant_phenotypes": resistant,
        "susceptible_phenotypes": susceptible,
        "phenotype_summary": data.get("result_summary", ""),
        "software_version": data.get("software_version", ""),
        "database_version": list(data.get("databases", {}).keys()),
    }


def parse_amrfinderplus_tsv(path: Path) -> Dict:
    """
    Parse AMRFinderPlus TSV output.

    Returns:
        {
            "genes": [{"gene": str, "drug_class": str, "identity": float, "coverage": float, "element_type": str}],
            "drug_classes": [str]
        }
    """
    genes = []
    drug_classes = set()

    with open(path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            genes.append({
                "gene": row.get("Gene symbol", row.get("Name", "")),
                "drug_class": row.get("Drug class", ""),
                "subclass": row.get("Drug subclass", ""),
                "identity": float(row["% Identity to reference sequence"]) if row.get("% Identity to reference sequence") else None,
                "coverage": float(row["% Coverage of reference sequence"]) if row.get("% Coverage of reference sequence") else None,
                "element_type": row.get("Element type", ""),
                "method": row.get("Method", ""),
            })
            if row.get("Drug class"):
                drug_classes.add(row["Drug class"])

    return {
        "genes": genes,
        "drug_classes": list(drug_classes),
        "hit_count": len(genes),
    }


def parse_card_rgi_json(path: Path) -> Dict:
    """
    Parse CARD RGI JSON output (rgi.json).

    Returns:
        {
            "genes": [{"gene": str, "drug_class": str, "identity": float, "model_type": str, "hit_type": str}],
            "drug_classes": [str]
        }
    """
    with open(path) as f:
        data = json.load(f)

    genes = []
    drug_classes = set()

    for contig_id, hits in data.items():
        if not isinstance(hits, dict):
            continue
        for hit_id, hit in hits.items():
            if not isinstance(hit, dict):
                continue
            aro_term = hit.get("ARO_term", "")
            drug_class = hit.get("drug_class", {})
            if isinstance(drug_class, dict):
                dc_name = drug_class.get("category_aro_name", "")
            else:
                dc_name = str(drug_class)

            genes.append({
                "gene": aro_term,
                "drug_class": dc_name,
                "identity": hit.get("perc_identity", None),
                "coverage": hit.get("perc_coverage", None),
                "model_type": hit.get("model_type", ""),
                "hit_type": hit.get("type_match", ""),
                "aro_accession": hit.get("ARO_accession", ""),
            })
            if dc_name:
                drug_classes.add(dc_name)

    return {
        "genes": genes,
        "drug_classes": list(drug_classes),
        "hit_count": len(genes),
    }


def parse_abricate_tsv(path: Path) -> Dict:
    """
    Parse abricate TSV output.

    Returns:
        {
            "genes": [{"gene": str, "database": str, "identity": float, "coverage": float, "resistance": str}],
            "resistances": [str]
        }
    """
    genes = []
    resistances = set()

    with open(path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            genes.append({
                "gene": row.get("GENE", row.get("gene", "")),
                "database": row.get("DATABASE", row.get("database", "")),
                "identity": float(row["%IDENTITY"]) if row.get("%IDENTITY") else None,
                "coverage": float(row["%COVERAGE"]) if row.get("%COVERAGE") else None,
                "resistance": row.get("RESISTANCE", row.get("resistance", "")),
                "sequence": row.get("SEQUENCE", ""),
            })
            if row.get("RESISTANCE"):
                resistances.add(row["RESISTANCE"])

    return {
        "genes": genes,
        "resistances": list(resistances),
        "hit_count": len(genes),
    }
