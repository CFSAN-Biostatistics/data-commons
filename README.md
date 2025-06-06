# HFP Division of Surveillance & Data Integration Test Data Library

A common resource for testing workflows against inputs and known outputs. Generally not necessary to clone or fork this resource in order to make use of it; download the files during testing using Github raw data links as below.

## Contents

### test/compression

A high-entropy file compressed in several formats:

test/compression/example.raw  # source file for comparison
test/compression/example.gz  
test/compression/example.tar.gz  
test/compression/example.1.zst # ZSTD compression level 1  
test/compression/example.8.zst # compression level 8  
test/compression/example.15.zst # compression level 15  

### test/csp2

As per https://github.com/CFSAN-Biostatistics/CSP2_TestData.git .

### test/identify

Data in this section is intended to test tools that parse sample accessions inside of FASTA and FASTQ files. In-silico serotyping and other taxonomy prediction tools should be tested using data in test/taxonomy.

### test/resistance

Data examples for AMR and other phenotype/functional prediction tools.

### test/taxonomy

Data examples for in-silico serotyping and other taxonomy prediction tools.