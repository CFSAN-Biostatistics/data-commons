#!/usr/bin/env python3
"""
Create manifest files for new batch of E. coli isolates.
"""

import json
import os
from datetime import datetime

# Load verified data
with open('/tmp/new_batch_verified.json') as f:
    verified = json.load(f)

BASE_DIR = '/home/justin/data-commons/test/typing/ecoli/examples'

# Characteristics for each new case
CASE_INFO = {
    'O104:H4': {
        'category': 'emerging_stec',
        'virulence': ['stx2', 'aggR'],
        'expected_st': '678',
        'phylogroup': 'B1',
        'notes': '2011 German outbreak strain (E. coli O104:H4). Unusual STEC/EAEC hybrid with Shiga toxin (stx2) and enteroaggregative traits (aggR). Associated with contaminated fenugreek sprouts. Ground beef isolate from California 2020.',
        'validation_notes': 'Expected serotype O104:H4. Rare STEC with EAEC virulence profile. Should detect stx2 (Shiga toxin) and aggR (enteroaggregative regulator). ST678 expected but confirm with mlst tool.',
        'difficulty': 'rare'
    },
    'O6:H1': {
        'category': 'expec_serotype',
        'virulence': ['pap', 'hlyA', 'cnf1'],
        'expected_st': '73',
        'phylogroup': 'B2',
        'notes': 'Classic UPEC serotype O6:H1, typically ST73 phylogroup B2. Canine isolate 1999 from E. coli Reference Center. NCBI metadata shows "O119" but GenomeTrakr GIMS database shows "O6:H1" - serotype discrepancy requires verification with typing tools.',
        'validation_notes': 'Expected O6:H1 (per GenomeTrakr) but NCBI BioSample says O119. PARTIAL acceptable if either serotype detected. Verify with both tools. Expected ExPEC virulence: pap, hlyA, cnf1. Likely ST73 or ST127.',
        'difficulty': 'complex',
        'confidence': 'medium'
    },
    'O1:H7': {
        'category': 'expec_serotype',
        'virulence': ['ibeA', 'hlyA', 'cnf1'],
        'expected_st': '95',
        'phylogroup': 'B2',
        'notes': 'ExPEC serotype O1:H7, often associated with ST95 neonatal meningitis strains when K1 capsule present. This isolate from dog wound (Oklahoma 2019) likely lacks K1. O1:H7 without K1 typically ST59 or other B2 lineages. Veterinary ExPEC.',
        'validation_notes': 'Expected serotype O1:H7. Check for K1 capsule genes (if present, likely ST95). ExPEC virulence genes expected: ibeA, hlyA, cnf1. ST may be ST95, ST59, or other B2 lineage depending on K1 status.',
        'difficulty': 'common'
    },
    'O15:H18': {
        'category': 'expec_mlst',
        'virulence': ['hlyA', 'cnf1'],
        'expected_st': '69',
        'phylogroup': 'D',
        'notes': 'Classic ST69 serotype O15:H18. Phylogroup D ExPEC causing UTI and bacteremia. Dog bite wound isolate (Texas 2017). Less virulent than ST95/ST73 but clinically relevant. Veterinary ExPEC from dog infection.',
        'validation_notes': 'Expected serotype O15:H18 and ST69 (phylogroup D). Accept exact match. ExPEC virulence profile: hlyA, cnf1. Less virulent than B2 ExPEC but established pathogenic lineage.',
        'difficulty': 'common'
    }
}

for item in verified:
    target = item['target']
    sra = item['sra']
    biosample = item['biosample']
    metadata = item.get('metadata', {})
    genomtrakr = item['genomtrakr']

    info = CASE_INFO[target]

    # Create safe filename
    safe_name = target.lower().replace(':', '').replace('/', '_')
    filename = f'ecoli_{safe_name}_example.json'
    filepath = os.path.join(BASE_DIR, filename)

    # Build manifest
    manifest = {
        "organism": f"Escherichia coli {target}",
        "curation": {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "ncbi_accessions": {
                "biosample": biosample,
                "sra": sra,
                "assembly": None
            },
            "metadata_confidence": info.get('confidence', 'high'),
            "serotype_evidence": [
                {
                    "source": "GenomeTrakr GIMS database",
                    "value": target,
                    "gims_isolate": genomtrakr['gims_isolate']
                }
            ]
        }
    }

    # Add NCBI serotype note if mismatch
    if target == 'O6:H1':
        manifest['curation']['serotype_evidence'].append({
            "source": "NCBI BioSample organism name",
            "value": "O119",
            "notes": "Discrepancy with GenomeTrakr - requires tool verification"
        })

    manifest['curation']['quality_metrics'] = {
        "has_reads": True,
        "has_assembly": False,
        "reported_coverage": genomtrakr['coverage'],
        "file_size_mb": genomtrakr['file_size_mb'],
        "strain": metadata.get('strain', 'Unknown'),
        "collection_date": metadata.get('collection_date'),
        "isolation_source": metadata.get('isolation_source', 'Not provided'),
        "host": metadata.get('host'),
        "geo_loc": metadata.get('geo_loc'),
        "collected_by": metadata.get('collected_by')
    }

    manifest['curation']['notes'] = (
        f"GenomeTrakr isolate {genomtrakr['gims_isolate']} (SEQ{genomtrakr['gims_sequence']}). "
        f"Strain {metadata.get('strain', 'Unknown')}. "
        f"Isolation: {metadata.get('isolation_source', 'not specified')} "
        f"from {metadata.get('host', 'unknown host')} ({metadata.get('collection_date', 'unknown date')}). "
        "Assembly not available - generate locally."
    )

    # Ground truth
    manifest['ground_truth'] = {
        "serological": {
            "serotype": target,
            "o_antigen": target.split(':')[0],
            "h_antigen": target.split(':')[1] if ':' in target else None
        }
    }

    # Add virulence or MLST depending on type
    if info['category'] in ['emerging_stec']:
        manifest['ground_truth']['virulence'] = {
            "expected_genes": info['virulence'],
            "stec_confirmation": True if 'stx' in str(info['virulence']) else False
        }
    elif info['category'] in ['expec_serotype', 'expec_mlst']:
        manifest['ground_truth']['virulence'] = {
            "expected_genes": info['virulence'],
            "expec_confirmation": True
        }

    manifest['ground_truth']['mlst'] = {
        "scheme": "ecoli",
        "sequence_type": info['expected_st'],
        "phylogroup": info['phylogroup'],
        "notes": f"Expected ST{info['expected_st']} phylogroup {info['phylogroup']}"
    }

    # Data sources
    manifest['data_sources'] = {
        "reads": {
            "sra_accession": sra,
            "download_cmd": f"fasterq-dump --gzip --outdir data/ {sra} && mv data/{sra}_1.fastq.gz data/reads_1.fq.gz && mv data/{sra}_2.fastq.gz data/reads_2.fq.gz"
        },
        "assembly": {
            "accession": None,
            "download_cmd": None,
            "notes": "Assembly not available in NCBI. Generate locally: spades.py -1 data/reads_1.fq.gz -2 data/reads_2.fq.gz -o assembly/ --careful && cp assembly/contigs.fasta data/contigs.fa"
        }
    }

    # Tools
    manifest['tools'] = {
        "ECTyper": {
            "input_type": "assembly",
            "run_cmd": "ectyper -i data/contigs.fa -o actual/ectyper/",
            "reference_output": "expected/ectyper/output.tsv"
        },
        "SerotypeFinder": {
            "input_type": "assembly",
            "run_cmd": "serotypefinder.py -i data/contigs.fa -o actual/serotypefinder/ -d /path/to/serotypefinder_db",
            "reference_output": "expected/serotypefinder/results_tab.tsv"
        },
        "MLST": {
            "input_type": "assembly",
            "run_cmd": "mlst --scheme ecoli data/contigs.fa > actual/mlst/mlst_report.tsv",
            "reference_output": "expected/mlst/mlst_report.tsv"
        }
    }

    # Add STEC tool for O104:H4
    if target == 'O104:H4':
        manifest['tools']['ShigaToxinFinder'] = {
            "input_type": "reads",
            "run_cmd": "shigatoxinfinder.py -1 data/reads_1.fq.gz -2 data/reads_2.fq.gz -o actual/shigatoxin/",
            "reference_output": "expected/shigatoxin/results.txt"
        }

    # Validation instructions
    manifest['validation_instructions'] = {
        "serological": info['validation_notes'],
        "mlst": f"Run mlst with 'ecoli' scheme. Expected ST{info['expected_st']} (phylogroup {info['phylogroup']}). Accept exact match."
    }

    manifest['difficulty'] = info['difficulty']
    manifest['notes'] = info['notes']

    # Write manifest
    with open(filepath, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"Created: {filename}")

print(f"\n✓ Created {len(verified)} new manifest files")
