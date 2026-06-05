#!/usr/bin/env python3
"""
Discover Campylobacter AMR test cases from NCBI with resistance metadata.

Queries NCBI BioSample/SRA for isolates with AMR phenotype annotations
(antibiogram, resistance_phenotype attributes) and generates manifest.json
stubs for manual review.

Usage:
    ./scripts/discover_cases.py --config config/amr_systems/resfinder.md
    ./scripts/discover_cases.py --organism "Campylobacter jejuni" --profile amp_tet --limit 10
"""
# TODO: implement NCBI Datasets + Entrez queries
# Mirror structure from test/typing/salmonella/scripts/discover_cases.py
# Key metadata fields to extract from BioSample:
#   antibiogram, resistance_phenotype, isolation_source, host
# Filter: SRA availability + assembly availability + AMR annotation confidence
