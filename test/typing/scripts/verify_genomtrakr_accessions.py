#!/usr/bin/env python3
"""
Verify GenomeTrakr SRA accessions and extract BioSample + metadata.
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

def efetch_sra(sra_acc):
    """Fetch SRA record and extract BioSample"""
    params = {
        'db': 'sra',
        'id': sra_acc,
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
        print(f"Error fetching {sra_acc}: {e}", file=sys.stderr)
        return None

    root = ET.fromstring(xml_data)

    biosample_acc = None
    for sample in root.findall('.//SAMPLE'):
        biosample_acc = sample.get('accession')
        break

    # Get experiment info
    exp_title = None
    for title_elem in root.findall('.//TITLE'):
        exp_title = title_elem.text
        break

    return {
        'sra': sra_acc,
        'biosample': biosample_acc,
        'title': exp_title
    }

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
        return {}

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
        elif attr_name == 'geographic location':
            metadata['geo_loc'] = attr_value

    return metadata

if __name__ == '__main__':
    # Read GenomeTrakr manifest
    input_file = '/home/justin/projects/gims-agent/data/ecoli_typing_manifest.json'

    with open(input_file) as f:
        genomtrakr_data = json.load(f)

    results = []

    for item in genomtrakr_data:
        sra_acc = item['sra']
        target = item['target']

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Verifying: {target} - {sra_acc}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        # Fetch SRA record
        sra_data = efetch_sra(sra_acc)
        if not sra_data:
            print(f"  ✗ Failed to fetch SRA", file=sys.stderr)
            results.append({
                'target': target,
                'sra': sra_acc,
                'status': 'SRA_NOT_FOUND',
                'genomtrakr': item
            })
            continue

        if not sra_data['biosample']:
            print(f"  ✗ No BioSample linked", file=sys.stderr)
            results.append({
                'target': target,
                'sra': sra_acc,
                'biosample': None,
                'status': 'NO_BIOSAMPLE',
                'genomtrakr': item
            })
            continue

        print(f"  ✓ SRA verified: {sra_acc}", file=sys.stderr)
        print(f"  ✓ BioSample: {sra_data['biosample']}", file=sys.stderr)

        # Fetch BioSample metadata
        biosample_data = efetch_biosample(sra_data['biosample'])

        print(f"    Organism: {biosample_data.get('organism', 'Unknown')}", file=sys.stderr)
        print(f"    Strain: {biosample_data.get('strain', 'Unknown')}", file=sys.stderr)
        if biosample_data.get('serotype'):
            print(f"    Serotype: {biosample_data['serotype']}", file=sys.stderr)
        if biosample_data.get('isolation_source'):
            print(f"    Source: {biosample_data['isolation_source']}", file=sys.stderr)

        results.append({
            'target': target,
            'sra': sra_acc,
            'biosample': sra_data['biosample'],
            'metadata': biosample_data,
            'genomtrakr': item,
            'status': 'VERIFIED'
        })

    print(json.dumps(results, indent=2))
