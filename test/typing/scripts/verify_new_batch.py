#!/usr/bin/env python3
"""
Verify new batch of GenomeTrakr E. coli accessions.
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import time
import os
import sys

API_KEY = os.environ.get('NCBI_API_KEY', '')
BASE_DELAY = 0.12

def rate_limit():
    time.sleep(BASE_DELAY)

def efetch_biosample(biosample_acc):
    """Fetch BioSample metadata"""
    params = {
        'db': 'biosample',
        'id': biosample_acc,
        'retmode': 'xml'
    }
    if API_KEY:
        params['api_key'] = API_KEY

    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"

    rate_limit()
    try:
        with urllib.request.urlopen(full_url) as response:
            xml_data = response.read().decode()
    except Exception as e:
        print(f"Error fetching BioSample {biosample_acc}: {e}", file=sys.stderr)
        return None

    root = ET.fromstring(xml_data)
    metadata = {}

    for org in root.findall('.//OrganismName'):
        metadata['organism'] = org.text
        break

    for attr in root.findall('.//Attribute'):
        attr_name = attr.get('attribute_name', '').lower()
        attr_value = attr.text

        if attr_name in ['strain', 'isolate']:
            metadata['strain'] = attr_value
        elif attr_name == 'serotype':
            metadata['serotype'] = attr_value
        elif attr_name in ['isolation_source', 'isolation source']:
            metadata['isolation_source'] = attr_value
        elif attr_name in ['collection_date', 'collection date']:
            metadata['collection_date'] = attr_value
        elif attr_name == 'collected_by':
            metadata['collected_by'] = attr_value
        elif attr_name in ['geographic location', 'geo_loc_name']:
            metadata['geo_loc'] = attr_value
        elif attr_name == 'host':
            metadata['host'] = attr_value

    return metadata

# New cases from combined manifest
NEW_CASES = [
    {
        "target": "O104:H4",
        "sra": "SRR14771989",
        "biosample": "SAMN19645968",
        "organism": "Escherichia coli O104:H4",
        "serotype": "O104:H4",
        "coverage": "81.6x",
        "file_size_mb": "308.4",
        "gims_isolate": "ISO000117256",
        "gims_sequence": "SEQ000113215",
        "qaqc_status": "CFSAN112382"
    },
    {
        "target": "O6:H1",
        "sra": "SRR7042029",
        "biosample": "SAMN08943194",
        "organism": "Escherichia coli O6:H1",
        "serotype": "O6:H1",
        "coverage": "72.0x",
        "file_size_mb": "296.9",
        "gims_isolate": "ISO000083983",
        "gims_sequence": "SEQ000072745",
        "qaqc_status": "CFSAN079781"
    },
    {
        "target": "O1:H7",
        "sra": "SRR10257703",
        "biosample": "SAMN13012205",
        "organism": "Escherichia coli O1:H7",
        "serotype": "O1:H7",
        "coverage": "82.0x",
        "file_size_mb": "315.1",
        "gims_isolate": "ISO000104797",
        "gims_sequence": "SEQ000098727",
        "qaqc_status": "ECOL-19-VL-SD-OK-0007"
    },
    {
        "target": "O15:H18",
        "sra": "SRR6875395",
        "biosample": "SAMN08596249",
        "organism": "Escherichia coli O15:H18",
        "serotype": "O15:H18",
        "coverage": "81.0x",
        "file_size_mb": "302.1",
        "gims_isolate": "ISO000080430",
        "gims_sequence": "SEQ000070406",
        "qaqc_status": "CFSAN076230"
    }
]

if __name__ == '__main__':
    results = []

    for item in NEW_CASES:
        biosample_acc = item['biosample']
        target = item['target']

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Verifying: {target}", file=sys.stderr)
        print(f"  BioSample: {biosample_acc}", file=sys.stderr)
        print(f"  SRA: {item['sra']}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        biosample_data = efetch_biosample(biosample_acc)
        if not biosample_data:
            print(f"  ✗ BioSample not found", file=sys.stderr)
            results.append({
                'target': target,
                'status': 'BIOSAMPLE_NOT_FOUND',
                'genomtrakr': item
            })
            continue

        organism = biosample_data.get('organism', '')
        print(f"  Organism: {organism}", file=sys.stderr)

        if 'Escherichia coli' not in organism:
            print(f"  ✗ Wrong organism: {organism}", file=sys.stderr)
            results.append({
                'target': target,
                'status': 'WRONG_ORGANISM',
                'metadata': biosample_data,
                'genomtrakr': item
            })
            continue

        print(f"  ✓ Organism confirmed: E. coli", file=sys.stderr)
        print(f"    Strain: {biosample_data.get('strain', 'Unknown')}", file=sys.stderr)
        if biosample_data.get('serotype'):
            print(f"    Serotype: {biosample_data['serotype']}", file=sys.stderr)
        if biosample_data.get('isolation_source'):
            print(f"    Source: {biosample_data['isolation_source']}", file=sys.stderr)
        if biosample_data.get('collection_date'):
            print(f"    Date: {biosample_data['collection_date']}", file=sys.stderr)
        if biosample_data.get('host'):
            print(f"    Host: {biosample_data['host']}", file=sys.stderr)

        results.append({
            'target': target,
            'sra': item['sra'],
            'biosample': biosample_acc,
            'metadata': biosample_data,
            'genomtrakr': item,
            'status': 'VERIFIED'
        })

    print(json.dumps(results, indent=2))
