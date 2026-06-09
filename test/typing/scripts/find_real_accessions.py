#!/usr/bin/env python3
"""
Find real NCBI accessions for typing manifest examples.
Uses urllib to avoid permission issues with external scripts.
"""

import json
import time
import urllib.request
import urllib.parse
from xml.etree import ElementTree as ET

ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
EMAIL = "typing-manifest@example.com"

def esearch(db, term, retmax=10):
    """Search NCBI database."""
    params = {
        'db': db,
        'term': term,
        'retmax': retmax,
        'email': EMAIL,
        'tool': 'typing-manifest-finder'
    }
    url = ENTREZ_BASE + 'esearch.fcgi?' + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
            root = ET.fromstring(data)

            ids = [id_elem.text for id_elem in root.findall('.//Id')]
            return ids
    except Exception as e:
        print(f"Error in esearch: {e}")
        return []

def efetch_biosample(biosample_id):
    """Fetch BioSample details."""
    params = {
        'db': 'biosample',
        'id': biosample_id,
        'retmode': 'xml',
        'email': EMAIL
    }
    url = ENTREZ_BASE + 'efetch.fcgi?' + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
            root = ET.fromstring(data)

            # Extract info
            biosample = {}

            # Accession
            acc_elem = root.find('.//BioSample')
            if acc_elem is not None:
                biosample['accession'] = acc_elem.get('accession', '')

            # Organism
            org_elem = root.find('.//OrganismName')
            if org_elem is not None:
                biosample['organism'] = org_elem.text

            # Attributes
            attrs = {}
            for attr_elem in root.findall('.//Attribute'):
                name = attr_elem.get('attribute_name', '')
                value = attr_elem.text or ''
                attrs[name] = value

            biosample['attributes'] = attrs
            biosample['serotype'] = attrs.get('serotype', attrs.get('serovar', ''))
            biosample['mlst'] = attrs.get('mlst', attrs.get('sequence_type', ''))
            biosample['strain'] = attrs.get('strain', '')

            # Links
            biosample['sra_ids'] = []
            biosample['assembly_ids'] = []

            for link_elem in root.findall('.//Link'):
                target = link_elem.get('target', '')
                label = link_elem.get('label', '')

                if target == 'sra':
                    biosample['sra_ids'].append(link_elem.text)
                elif 'GCA_' in label or 'GCF_' in label:
                    biosample['assembly_ids'].append(label)

            return biosample

    except Exception as e:
        print(f"Error fetching BioSample: {e}")
        return None

def search_target(organism, characteristics, limit=3):
    """Search for BioSamples matching criteria."""
    # Build query
    query_parts = [f'"{organism}"[Organism]']

    if characteristics.get('serotype'):
        query_parts.append(f'"{characteristics["serotype"]}"[All Fields]')

    if characteristics.get('st'):
        query_parts.append(f'"ST{characteristics["st"]}"[All Fields]')

    # Add filters
    query_parts.append('has_sra[filter]')

    query = ' AND '.join(query_parts)

    print(f"\nSearching: {query}")

    # Search BioSample
    biosample_ids = esearch('biosample', query, retmax=limit)
    print(f"Found {len(biosample_ids)} BioSamples")

    if not biosample_ids:
        return []

    # Fetch details
    results = []
    for bs_id in biosample_ids[:limit]:
        time.sleep(0.4)  # Rate limit
        biosample = efetch_biosample(bs_id)
        if biosample:
            results.append(biosample)
            print(f"  {biosample['accession']}: {biosample.get('organism', 'N/A')} | "
                  f"Serotype: {biosample.get('serotype', 'N/A')} | "
                  f"ST: {biosample.get('mlst', 'N/A')}")

    return results

def get_sra_runs(biosample_acc):
    """Get SRR accessions for a BioSample."""
    query = f'{biosample_acc}[BioSample]'
    sra_ids = esearch('sra', query, retmax=5)

    if not sra_ids:
        return []

    # Fetch SRA XML to get SRR accessions
    params = {
        'db': 'sra',
        'id': ','.join(sra_ids),
        'retmode': 'xml',
        'email': EMAIL
    }
    url = ENTREZ_BASE + 'efetch.fcgi?' + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')

            # Extract SRR accessions
            import re
            srr_pattern = r'<PRIMARY_ID>(SRR\d+)</PRIMARY_ID>'
            srr_accessions = re.findall(srr_pattern, data)

            return list(set(srr_accessions))[:5]

    except Exception as e:
        print(f"Error fetching SRA: {e}")
        return []

def get_assemblies(biosample_acc):
    """Get Assembly accessions for a BioSample."""
    # Use elink to find assemblies
    params = {
        'dbfrom': 'biosample',
        'db': 'assembly',
        'id': biosample_acc,
        'email': EMAIL
    }
    url = ENTREZ_BASE + 'elink.fcgi?' + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
            root = ET.fromstring(data)

            # Extract assembly IDs
            assembly_ids = [id_elem.text for id_elem in root.findall('.//Link/Id')]

            if not assembly_ids:
                return []

            # Fetch assembly summaries
            time.sleep(0.4)
            params2 = {
                'db': 'assembly',
                'id': ','.join(assembly_ids[:5]),
                'retmode': 'xml',
                'email': EMAIL
            }
            url2 = ENTREZ_BASE + 'esummary.fcgi?' + urllib.parse.urlencode(params2)

            with urllib.request.urlopen(url2) as response2:
                data2 = response2.read()
                root2 = ET.fromstring(data2)

                accessions = []
                for doc_sum in root2.findall('.//DocumentSummary'):
                    acc = doc_sum.findtext('AssemblyAccession', '')
                    if acc:
                        accessions.append(acc)

                return accessions[:5]

    except Exception as e:
        print(f"Error fetching assemblies: {e}")
        return []

def main():
    """Main search logic."""
    targets = [
        {
            "name": "ecoli_o157h7",
            "organism": "Escherichia coli",
            "characteristics": {"serotype": "O157:H7", "st": "11"}
        },
        {
            "name": "ecoli_st131",
            "organism": "Escherichia coli",
            "characteristics": {"serotype": "O25:H4", "st": "131"}
        },
        {
            "name": "shigella_sonnei",
            "organism": "Shigella sonnei",
            "characteristics": {"st": "152"}
        },
        {
            "name": "shigella_flexneri",
            "organism": "Shigella flexneri",
            "characteristics": {"serotype": "2a"}
        },
        {
            "name": "listeria_4b",
            "organism": "Listeria monocytogenes",
            "characteristics": {"serotype": "4b", "st": "2"}
        },
        {
            "name": "listeria_1-2a",
            "organism": "Listeria monocytogenes",
            "characteristics": {"serotype": "1/2a", "st": "5"}
        },
    ]

    all_results = {}

    for target in targets:
        print(f"\n{'='*70}")
        print(f"TARGET: {target['name']}")
        print(f"{'='*70}")

        results = search_target(
            target['organism'],
            target['characteristics'],
            limit=2
        )

        if results:
            # Get SRA and Assembly for first result
            first = results[0]
            biosample_acc = first['accession']

            print(f"\nSelected: {biosample_acc}")

            # Get SRA runs
            time.sleep(0.5)
            sra_runs = get_sra_runs(biosample_acc)
            first['sra_runs'] = sra_runs
            print(f"  SRA runs: {', '.join(sra_runs[:3])}")

            # Get assemblies
            time.sleep(0.5)
            assemblies = get_assemblies(biosample_acc)
            first['assemblies'] = assemblies
            print(f"  Assemblies: {', '.join(assemblies[:3])}")

            all_results[target['name']] = first

        time.sleep(1)

    # Output JSON
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(json.dumps(all_results, indent=2))

    return all_results

if __name__ == '__main__':
    main()
