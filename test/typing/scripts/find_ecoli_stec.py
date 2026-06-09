#!/usr/bin/env python3
"""
Search for STEC E. coli strains using more specific queries.
Focus on strain names, CDC collections, and outbreak investigations.
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

def esearch(db, term, retmax=10):
    params = {
        'db': db,
        'term': term,
        'retmax': retmax,
        'retmode': 'json'
    }
    if API_KEY:
        params['api_key'] = API_KEY

    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"

    rate_limit()
    try:
        with urllib.request.urlopen(full_url) as response:
            data = json.loads(response.read().decode())
        return data.get('esearchresult', {}).get('idlist', [])
    except Exception as e:
        print(f"Error in esearch: {e}", file=sys.stderr)
        return []

def efetch_sra(sra_id):
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

    sra_acc = None
    for run in root.findall('.//RUN'):
        sra_acc = run.get('accession')
        break

    biosample_acc = None
    for sample in root.findall('.//SAMPLE'):
        biosample_acc = sample.get('accession')
        break

    return {'sra': sra_acc, 'biosample': biosample_acc}

def efetch_biosample(biosample_id):
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
        elif attr_name in ['serovar', 'serogroup']:
            metadata['serovar'] = attr_value

    return metadata

# More specific search strategies for STEC
STEC_TARGETS = [
    {
        'serotype': 'O26:H11',
        'queries': [
            '"Escherichia coli O26"[Organism]',
            'Escherichia coli[Organism] AND ("O26:H11" OR "O26 H11" OR "serogroup O26")',
            'Escherichia coli[Organism] AND STEC AND O26',
        ]
    },
    {
        'serotype': 'O45:H2',
        'queries': [
            '"Escherichia coli O45"[Organism]',
            'Escherichia coli[Organism] AND ("O45:H2" OR "O45 H2" OR "serogroup O45")',
        ]
    },
    {
        'serotype': 'O103:H2',
        'queries': [
            '"Escherichia coli O103"[Organism]',
            'Escherichia coli[Organism] AND ("O103:H2" OR "O103 H2" OR "serogroup O103")',
        ]
    },
    {
        'serotype': 'O111:H8',
        'queries': [
            '"Escherichia coli O111"[Organism]',
            'Escherichia coli[Organism] AND ("O111:H8" OR "O111 H8" OR "serogroup O111")',
        ]
    },
    {
        'serotype': 'O121:H19',
        'queries': [
            '"Escherichia coli O121"[Organism]',
            'Escherichia coli[Organism] AND ("O121:H19" OR "O121 H19")',
        ]
    },
    {
        'serotype': 'O145:H28',
        'queries': [
            '"Escherichia coli O145"[Organism]',
            'Escherichia coli[Organism] AND ("O145:H28" OR "O145 H28" OR "serogroup O145")',
        ]
    },
]

EXPEC_TARGETS = [
    {
        'st': 'ST95',
        'queries': [
            'Escherichia coli[Organism] AND ("sequence type 95" OR "ST95" OR "ST-95") AND (urine OR blood OR UTI)',
        ]
    },
    {
        'st': 'ST73',
        'queries': [
            'Escherichia coli[Organism] AND ("sequence type 73" OR "ST73" OR "ST-73") AND (urine OR blood)',
        ]
    },
    {
        'st': 'ST69',
        'queries': [
            'Escherichia coli[Organism] AND ("sequence type 69" OR "ST69") AND clinical',
        ]
    },
]

COMMENSAL_TARGETS = [
    {
        'strain': 'K-12',
        'queries': [
            '"Escherichia coli str. K-12"[Organism]',
            'Escherichia coli[Organism] AND ("K-12" OR "K12") AND (MG1655 OR DH5alpha OR BW25113)',
        ]
    },
]

def search_with_fallback(target_list, category):
    results = {}

    for target in target_list:
        target_key = target.get('serotype') or target.get('st') or target.get('strain')
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Searching {category}: {target_key}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        found = False
        for query in target['queries']:
            if found:
                break

            print(f"\nTrying: {query}", file=sys.stderr)
            sra_ids = esearch('sra', query, retmax=5)

            if not sra_ids:
                print("  No results", file=sys.stderr)
                continue

            candidates = []
            for sra_id in sra_ids[:3]:
                try:
                    sra_data = efetch_sra(sra_id)
                    if not sra_data.get('biosample'):
                        continue

                    biosample_data = efetch_biosample(sra_data['biosample'])

                    # Filter: must be E. coli
                    organism = biosample_data.get('organism', '')
                    if 'Escherichia coli' not in organism:
                        print(f"  Skipping {sra_data['sra']}: wrong organism ({organism})", file=sys.stderr)
                        continue

                    result = {
                        'sra': sra_data['sra'],
                        'biosample': sra_data['biosample'],
                        'organism': organism,
                        'strain': biosample_data.get('strain', 'Unknown'),
                        'serotype': biosample_data.get('serotype') or biosample_data.get('serovar'),
                        'isolation_source': biosample_data.get('isolation_source'),
                        'collection_date': biosample_data.get('collection_date'),
                        'query': query
                    }

                    print(f"  ✓ Found: {result['sra']} / {result['biosample']}", file=sys.stderr)
                    print(f"    Organism: {result['organism']}", file=sys.stderr)
                    print(f"    Strain: {result['strain']}", file=sys.stderr)
                    if result['serotype']:
                        print(f"    Serotype: {result['serotype']}", file=sys.stderr)

                    candidates.append(result)
                    found = True

                except Exception as e:
                    print(f"  Error processing {sra_id}: {e}", file=sys.stderr)
                    continue

            if candidates:
                safe_key = target_key.replace(':', '').replace('/', '').replace('-', '')
                results[f"{category}_{safe_key}"] = {
                    'target': target_key,
                    'candidates': candidates
                }
                break

    return results

if __name__ == '__main__':
    all_results = {}

    print("="*60, file=sys.stderr)
    print("STEC SEARCH", file=sys.stderr)
    print("="*60, file=sys.stderr)
    stec_results = search_with_fallback(STEC_TARGETS, 'stec')
    all_results.update(stec_results)

    print("\n" + "="*60, file=sys.stderr)
    print("ExPEC SEARCH", file=sys.stderr)
    print("="*60, file=sys.stderr)
    expec_results = search_with_fallback(EXPEC_TARGETS, 'expec')
    all_results.update(expec_results)

    print("\n" + "="*60, file=sys.stderr)
    print("COMMENSAL SEARCH", file=sys.stderr)
    print("="*60, file=sys.stderr)
    commensal_results = search_with_fallback(COMMENSAL_TARGETS, 'commensal')
    all_results.update(commensal_results)

    print(json.dumps(all_results, indent=2))
