#!/usr/bin/env python3
"""
Verify updated GenomeTrakr accessions with SAMN BioSample IDs.
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
        elif attr_name in ['isolation_source', 'isolation source', 'isolation source']:
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

def verify_sra_biosample_link(sra_acc, expected_biosample):
    """Verify SRA links to expected BioSample"""
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

        root = ET.fromstring(xml_data)

        biosample_acc = None
        for sample in root.findall('.//SAMPLE'):
            biosample_acc = sample.get('accession')
            break

        return biosample_acc == expected_biosample, biosample_acc

    except Exception as e:
        print(f"Error verifying SRA {sra_acc}: {e}", file=sys.stderr)
        return False, None

if __name__ == '__main__':
    input_file = '/home/justin/projects/gims-agent/data/ecoli_typing_manifest.json'

    with open(input_file) as f:
        genomtrakr_data = json.load(f)

    results = []

    for item in genomtrakr_data:
        sra_acc = item['sra']
        biosample_acc = item['biosample']
        target = item['target']

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Verifying: {target}", file=sys.stderr)
        print(f"  SRA: {sra_acc}", file=sys.stderr)
        print(f"  BioSample: {biosample_acc}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        # Verify BioSample exists and is E. coli
        biosample_data = efetch_biosample(biosample_acc)
        if not biosample_data:
            print(f"  ✗ BioSample not found", file=sys.stderr)
            results.append({
                'target': target,
                'sra': sra_acc,
                'biosample': biosample_acc,
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
                'sra': sra_acc,
                'biosample': biosample_acc,
                'metadata': biosample_data,
                'status': 'WRONG_ORGANISM',
                'genomtrakr': item
            })
            continue

        print(f"  ✓ Organism confirmed: E. coli", file=sys.stderr)

        # Check if SRA links to this BioSample
        link_match, actual_biosample = verify_sra_biosample_link(sra_acc, biosample_acc)

        if not link_match:
            print(f"  ⚠ SRA links to {actual_biosample}, not {biosample_acc}", file=sys.stderr)
            status = 'SRA_BIOSAMPLE_MISMATCH'
        else:
            print(f"  ✓ SRA correctly links to BioSample", file=sys.stderr)
            status = 'VERIFIED'

        # Print metadata
        print(f"    Strain: {biosample_data.get('strain', 'Unknown')}", file=sys.stderr)
        if biosample_data.get('serotype'):
            print(f"    Serotype: {biosample_data['serotype']}", file=sys.stderr)
        if biosample_data.get('isolation_source'):
            print(f"    Source: {biosample_data['isolation_source']}", file=sys.stderr)
        if biosample_data.get('collection_date'):
            print(f"    Date: {biosample_data['collection_date']}", file=sys.stderr)

        results.append({
            'target': target,
            'sra': sra_acc,
            'biosample': biosample_acc,
            'metadata': biosample_data,
            'genomtrakr': item,
            'status': status
        })

    print(json.dumps(results, indent=2))
