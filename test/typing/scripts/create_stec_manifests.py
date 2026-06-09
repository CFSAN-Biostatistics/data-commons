#!/usr/bin/env python3
"""
Create E. coli STEC manifest files from verified GenomeTrakr data.
"""

import json
import os
from datetime import datetime

# Load verified data
with open('/tmp/genomtrakr_v2_verified.json') as f:
    verified = json.load(f)

BASE_DIR = '/home/justin/data-commons/test/typing/ecoli/examples'

# Serotype to expected characteristics
STEC_INFO = {
    'O26:H11': {
        'virulence': ['stx1', 'stx2', 'eae', 'ehxA'],
        'notes': 'Non-O157 STEC, common in Europe, associated with cattle and leafy greens'
    },
    'O45:H2': {
        'virulence': ['stx1', 'stx2', 'eae'],
        'notes': 'Non-O157 STEC, associated with ground beef outbreaks'
    },
    'O103:H2': {
        'virulence': ['stx1', 'eae'],
        'notes': 'Non-O157 STEC, associated with dairy products'
    },
    'O111:H8': {
        'virulence': ['stx1', 'stx2', 'eae'],
        'notes': 'Non-O157 STEC, clinical and cattle isolates'
    },
    'O121:H19': {
        'virulence': ['stx2', 'eae'],
        'notes': 'Non-O157 STEC, associated with flour and produce'
    },
    'O145:H28': {
        'virulence': ['stx1', 'stx2', 'eae'],
        'notes': 'Non-O157 STEC, associated with lettuce outbreaks'
    },
    'O157:H7': {
        'virulence': ['stx1', 'stx2', 'eae', 'ehxA'],
        'expected_st': '11',
        'notes': 'Classic STEC serotype, major cause of HUS. ST11 is the dominant lineage.'
    }
}

for item in verified:
    if item['status'] == 'BIOSAMPLE_NOT_FOUND':
        print(f"Skipping {item['target']}: BioSample not found")
        continue

    target = item['target']
    sra = item['sra']
    biosample = item['biosample']
    metadata = item.get('metadata', {})
    genomtrakr = item['genomtrakr']

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
            "metadata_confidence": "high" if metadata.get('isolation_source') else "medium",
            "serotype_evidence": [
                {
                    "source": "GenomeTrakr GIMS database",
                    "value": target,
                    "gims_isolate": genomtrakr['gims_isolate']
                }
            ],
            "quality_metrics": {
                "has_reads": True,
                "has_assembly": False,
                "reported_coverage": genomtrakr['coverage'],
                "file_size_mb": genomtrakr['file_size_mb'],
                "strain": metadata.get('strain', 'Unknown'),
                "collection_date": metadata.get('collection_date'),
                "isolation_source": metadata.get('isolation_source', 'Not provided'),
                "host": metadata.get('host'),
                "geo_loc": metadata.get('geo_loc'),
                "collected_by": metadata.get('collected_by', 'USDA ARS' if 'USDA' in metadata.get('collected_by', '') else None)
            },
            "notes": f"GenomeTrakr isolate {genomtrakr['gims_isolate']} (SEQ{genomtrakr['gims_sequence']}). " +
                     f"Strain {metadata.get('strain', 'Unknown')}. " +
                     f"Isolation: {metadata.get('isolation_source', 'not specified')} " +
                     f"from {metadata.get('host', 'unknown host')} ({metadata.get('collection_date', 'unknown date')}). " +
                     "Assembly not available - generate locally."
        },
        "ground_truth": {
            "serological": {
                "serotype": target,
                "o_antigen": target.split(':')[0],
                "h_antigen": target.split(':')[1] if ':' in target else None
            },
            "virulence": {
                "expected_genes": STEC_INFO.get(target, {}).get('virulence', []),
                "stec_confirmation": True
            }
        }
    }

    # Add MLST for O157:H7
    if target == 'O157:H7':
        manifest['ground_truth']['mlst'] = {
            "scheme": "ecoli",
            "sequence_type": "11",
            "notes": "ST11 is the dominant O157:H7 lineage"
        }

    # Add data sources
    manifest['data_sources'] = {
        "reads": {
            "sra_accession": sra,
            "download_cmd": f"fasterq-dump --gzip --outdir data/ {sra} && mv data/{sra}_1.fastq.gz data/reads_1.fq.gz && mv data/{sra}_2.fastq.gz data/reads_2.fq.gz"
        },
        "assembly": {
            "accession": None,
            "download_cmd": None,
            "notes": f"Assembly not available in NCBI. Generate locally: spades.py -1 data/reads_1.fq.gz -2 data/reads_2.fq.gz -o assembly/ --careful && cp assembly/contigs.fasta data/contigs.fa"
        }
    }

    # Add tools
    manifest['tools'] = {
        "ECTyper": {
            "input_type": "assembly",
            "run_cmd": f"ectyper -i data/contigs.fa -o actual/ectyper/",
            "reference_output": "expected/ectyper/output.tsv"
        },
        "SerotypeFinder": {
            "input_type": "assembly",
            "run_cmd": "serotypefinder.py -i data/contigs.fa -o actual/serotypefinder/ -d /path/to/serotypefinder_db",
            "reference_output": "expected/serotypefinder/results_tab.tsv"
        },
        "ShigaToxinFinder": {
            "input_type": "reads",
            "run_cmd": f"shigatoxinfinder.py -1 data/reads_1.fq.gz -2 data/reads_2.fq.gz -o actual/shigatoxin/",
            "reference_output": "expected/shigatoxin/results.txt"
        },
        "MLST": {
            "input_type": "assembly",
            "run_cmd": "mlst --scheme ecoli data/contigs.fa > actual/mlst/mlst_report.tsv",
            "reference_output": "expected/mlst/mlst_report.tsv"
        }
    }

    # Add validation instructions
    virulence_genes = STEC_INFO.get(target, {}).get('virulence', [])
    manifest['validation_instructions'] = {
        "serological": f"Expected serotype {target}. Accept exact match '{target}' or individual O/H antigen calls that match. " +
                      f"Serotype confirmed in GenomeTrakr GIMS database (ISO{genomtrakr['gims_isolate']}). " +
                      "Tool should confidently call this serotype.",
        "virulence": f"Expected STEC virulence genes: {', '.join(virulence_genes)}. " +
                    "At minimum, stx (Shiga toxin) and eae (intimin) should be detected for typical STEC. " +
                    "Accept PASS if all expected genes found. PARTIAL if stx present but other genes missing.",
        "mlst": "Run mlst with 'ecoli' scheme. ST will vary by isolate. Document observed ST for future reference." if target != 'O157:H7' else
                "Expected ST11 (dominant O157:H7 lineage). Accept exact ST11 match. Other STs unusual for O157:H7."
    }

    manifest['difficulty'] = 'common'
    manifest['notes'] = STEC_INFO.get(target, {}).get('notes', 'STEC isolate for serotyping validation')

    # Write manifest
    with open(filepath, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"Created: {filename}")

print(f"\n✓ Created {len([v for v in verified if v['status'] != 'BIOSAMPLE_NOT_FOUND'])} STEC manifest files")
print(f"✗ Skipped 1 file (O103:H2 - BioSample not found)")
