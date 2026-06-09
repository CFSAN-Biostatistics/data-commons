#!/usr/bin/env python3
"""
Search NCBI SRA for E. coli isolates matching typing targets.
Extracts SRA, BioSample, and metadata for manifest generation.
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import time
import os
import sys

API_KEY = os.environ.get('NCBI_API_KEY', '')
BASE_DELAY = 0.12  # Stay under 10 req/sec with API key

def rate_limit():
    """Sleep to respect rate limits"""
    time.sleep(BASE_DELAY)

def esearch(db, term, retmax=5):
    """Search NCBI database"""
    params = {
        'db': db,
        'term': term,
        'retmax': retmax,
        'retmode': 'json',
        'usehistory': 'y'
    }
    if API_KEY:
        params['api_key'] = API_KEY

    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"

    rate_limit()
    with urllib.request.urlopen(full_url) as response:
        data = json.loads(response.read().decode())

    return data.get('esearchresult', {}).get('idlist', [])

def efetch_sra(sra_id):
    """Fetch SRA metadata including BioSample link"""
    params = {
        'db': 'sra',
        'id': sra_id,
        'retmode': 'xml'
    }
    if API_KEY:
        params['api_key'] = API_KEY

    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"

    rate_limit()
    with urllib.request.urlopen(full_url) as response:
        xml_data = response.read().decode()

    root = ET.fromstring(xml_data)

    # Extract SRA run accession
    sra_acc = None
    for run in root.findall('.//RUN'):
        sra_acc = run.get('accession')
        break

    # Extract BioSample accession
    biosample_acc = None
    for sample in root.findall('.//SAMPLE'):
        biosample_acc = sample.get('accession')
        break

    # Extract experiment title
    title = None
    for exp_title in root.findall('.//TITLE'):
        title = exp_title.text
        break

    return {
        'sra': sra_acc,
        'biosample': biosample_acc,
        'title': title
    }

def efetch_biosample(biosample_id):
    """Fetch BioSample metadata"""
    params = {
        'db': 'biosample',
        'id': biosample_id,
        'retmode': 'xml'
    }
    if API_KEY:
        params['api_key'] = API_KEY

    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"

    rate_limit()
    with urllib.request.urlopen(full_url) as response:
        xml_data = response.read().decode()

    root = ET.fromstring(xml_data)

    metadata = {}

    # Organism name
    for org in root.findall('.//OrganismName'):
        metadata['organism'] = org.text
        break

    # Attributes
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

    return metadata

def search_target(organism, characteristics, retmax=5):
    """Search for isolates matching target characteristics"""
    term = f'"{organism}"[Organism] AND {characteristics}'

    print(f"\nSearching: {term}", file=sys.stderr)
    sra_ids = esearch('sra', term, retmax=retmax)

    if not sra_ids:
        print(f"  No results found", file=sys.stderr)
        return []

    results = []
    for sra_id in sra_ids[:3]:  # Limit to 3 per search
        try:
            sra_data = efetch_sra(sra_id)
            if not sra_data['biosample']:
                continue

            biosample_data = efetch_biosample(sra_data['biosample'])

            result = {
                'sra': sra_data['sra'],
                'biosample': sra_data['biosample'],
                'organism': biosample_data.get('organism', 'Unknown'),
                'strain': biosample_data.get('strain', 'Unknown'),
                'serotype': biosample_data.get('serotype'),
                'isolation_source': biosample_data.get('isolation_source'),
                'collection_date': biosample_data.get('collection_date'),
                'search_term': characteristics
            }

            print(f"  Found: {result['sra']} / {result['biosample']}", file=sys.stderr)
            print(f"    Organism: {result['organism']}", file=sys.stderr)
            print(f"    Strain: {result['strain']}", file=sys.stderr)
            if result['serotype']:
                print(f"    Serotype: {result['serotype']}", file=sys.stderr)

            results.append(result)

        except Exception as e:
            print(f"  Error processing {sra_id}: {e}", file=sys.stderr)
            continue

    return results

# Define search targets based on E. coli typing documentation
TARGETS = [
    # Big Six STEC serotypes
    {
        'category': 'stec_big_six',
        'serotype': 'O26:H11',
        'organism': 'Escherichia coli',
        'search': 'O26:H11',
        'expected_st': None
    },
    {
        'category': 'stec_big_six',
        'serotype': 'O45:H2',
        'organism': 'Escherichia coli',
        'search': 'O45',
        'expected_st': None
    },
    {
        'category': 'stec_big_six',
        'serotype': 'O103:H2',
        'organism': 'Escherichia coli',
        'search': 'O103',
        'expected_st': None
    },
    {
        'category': 'stec_big_six',
        'serotype': 'O111:H8',
        'organism': 'Escherichia coli',
        'search': 'O111',
        'expected_st': None
    },
    {
        'category': 'stec_big_six',
        'serotype': 'O121:H19',
        'organism': 'Escherichia coli',
        'search': 'O121',
        'expected_st': None
    },
    {
        'category': 'stec_big_six',
        'serotype': 'O145:H28',
        'organism': 'Escherichia coli',
        'search': 'O145',
        'expected_st': None
    },
    # ExPEC additional STs
    {
        'category': 'expec',
        'serotype': None,
        'organism': 'Escherichia coli',
        'search': 'ST95',
        'expected_st': '95'
    },
    {
        'category': 'expec',
        'serotype': None,
        'organism': 'Escherichia coli',
        'search': 'ST73',
        'expected_st': '73'
    },
    # Other important STs
    {
        'category': 'mlst',
        'serotype': None,
        'organism': 'Escherichia coli',
        'search': 'ST10',
        'expected_st': '10'
    },
    {
        'category': 'mlst',
        'serotype': None,
        'organism': 'Escherichia coli',
        'search': 'ST69',
        'expected_st': '69'
    },
    # Commensal
    {
        'category': 'commensal',
        'serotype': 'K-12',
        'organism': 'Escherichia coli K-12',
        'search': 'K-12',
        'expected_st': '10'
    },
]

if __name__ == '__main__':
    all_results = {}

    for target in TARGETS:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Target: {target['category']} - {target.get('serotype') or target['expected_st']}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        results = search_target(target['organism'], target['search'])

        if results:
            key = f"{target['category']}_{target.get('serotype') or target['expected_st']}".replace(':', '').replace('/', '')
            all_results[key] = {
                'target': target,
                'candidates': results
            }

    # Output JSON for processing
    print(json.dumps(all_results, indent=2))
