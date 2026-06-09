#!/usr/bin/env python3
"""
Search Assembly database for E. coli with serotype metadata.
Assemblies often have better metadata annotation than SRA.
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

def esummary_assembly(assembly_id):
    """Get assembly summary including BioSample"""
    params = {
        'db': 'assembly',
        'id': assembly_id,
        'retmode': 'json'
    }
    if API_KEY:
        params['api_key'] = API_KEY

    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"

    rate_limit()
    try:
        with urllib.request.urlopen(full_url) as response:
            data = json.loads(response.read().decode())

        result = data.get('result', {}).get(assembly_id, {})
        return {
            'assembly_accession': result.get('assemblyaccession'),
            'organism': result.get('organism'),
            'biosample': result.get('biosample'),
            'strain': result.get('infraspecieslist', [{}])[0].get('sub_value') if result.get('infraspecieslist') else None
        }
    except Exception as e:
        print(f"Error in esummary: {e}", file=sys.stderr)
        return {}

def elink_assembly_to_sra(biosample_acc):
    """Find SRA runs linked to BioSample"""
    # Search SRA by BioSample
    sra_ids = esearch('sra', f'{biosample_acc}[BioSample]', retmax=5)
    return sra_ids

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

    return sra_acc

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

    return metadata

# Search Assembly database for E. coli with serotype info
TARGETS = [
    ('O26', ['Escherichia coli[Organism] AND O26', 'Escherichia coli O26[All Fields]']),
    ('O45', ['Escherichia coli[Organism] AND O45', 'Escherichia coli O45[All Fields]']),
    ('O103', ['Escherichia coli[Organism] AND O103', 'Escherichia coli O103[All Fields]']),
    ('O111', ['Escherichia coli[Organism] AND O111', 'Escherichia coli O111[All Fields]']),
    ('O121', ['Escherichia coli[Organism] AND O121', 'Escherichia coli O121[All Fields]']),
    ('O145', ['Escherichia coli[Organism] AND O145', 'Escherichia coli O145[All Fields]']),
    ('ST95', ['Escherichia coli[Organism] AND (ST95 OR "sequence type 95")']),
    ('ST73', ['Escherichia coli[Organism] AND (ST73 OR "sequence type 73")']),
    ('ST69', ['Escherichia coli[Organism] AND (ST69 OR "sequence type 69")']),
    ('K-12', ['Escherichia coli K-12[Organism]', 'Escherichia coli[Organism] AND MG1655']),
]

if __name__ == '__main__':
    all_results = {}

    for target_name, queries in TARGETS:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Searching: {target_name}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        found = False
        for query in queries:
            if found:
                break

            print(f"\nQuery: {query}", file=sys.stderr)
            assembly_ids = esearch('assembly', query, retmax=5)

            if not assembly_ids:
                print("  No assemblies found", file=sys.stderr)
                continue

            candidates = []
            for asm_id in assembly_ids[:3]:
                try:
                    asm_summary = esummary_assembly(asm_id)

                    if not asm_summary.get('biosample'):
                        print(f"  Skipping {asm_summary.get('assembly_accession')}: no BioSample", file=sys.stderr)
                        continue

                    # Get detailed metadata from BioSample
                    biosample_data = efetch_biosample(asm_summary['biosample'])

                    # Try to find linked SRA
                    sra_ids = elink_assembly_to_sra(asm_summary['biosample'])
                    sra_acc = None
                    if sra_ids:
                        sra_acc = efetch_sra(sra_ids[0])

                    result = {
                        'assembly': asm_summary.get('assembly_accession'),
                        'biosample': asm_summary['biosample'],
                        'sra': sra_acc,
                        'organism': biosample_data.get('organism', asm_summary.get('organism')),
                        'strain': biosample_data.get('strain') or asm_summary.get('strain') or 'Unknown',
                        'serotype': biosample_data.get('serotype'),
                        'isolation_source': biosample_data.get('isolation_source'),
                        'collection_date': biosample_data.get('collection_date'),
                        'query': query
                    }

                    print(f"  ✓ Found: {result['assembly']}", file=sys.stderr)
                    print(f"    BioSample: {result['biosample']}", file=sys.stderr)
                    print(f"    SRA: {result['sra'] or 'None'}", file=sys.stderr)
                    print(f"    Organism: {result['organism']}", file=sys.stderr)
                    print(f"    Strain: {result['strain']}", file=sys.stderr)
                    if result['serotype']:
                        print(f"    Serotype: {result['serotype']}", file=sys.stderr)

                    candidates.append(result)

                except Exception as e:
                    print(f"  Error processing assembly {asm_id}: {e}", file=sys.stderr)
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                    continue

            if candidates:
                safe_key = target_name.replace(':', '').replace('-', '')
                all_results[safe_key] = {
                    'target': target_name,
                    'candidates': candidates
                }
                found = True

    print(json.dumps(all_results, indent=2))
