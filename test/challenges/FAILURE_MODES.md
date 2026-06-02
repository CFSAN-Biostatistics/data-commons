# Bioinformatics Tool Failure Mode Catalog

This document catalogs known failure modes, edge cases, and pathological inputs for major categories of bioinformatics tools. It is the research basis for the challenge dataset library in this directory.

Each entry describes a **phenomenon** — a dataset characteristic that challenges tool assumptions — not a specific tool bug. The same phenomenon often affects multiple tool families. The most dangerous failures are marked **SILENT**: they produce exit 0, a valid-format output file, and plausible-looking statistics, with the error only detectable by domain expertise or downstream analysis.

---

## Organization

Challenges are prioritized for data collection in this order:
1. **In-silico typing & population variant analysis** (SNP pipelines) — highest clinical impact
2. **Assembly** — foundational for all downstream analysis
3. **Alignment** — upstream dependency

---

## 1. In-Silico Typing Tools

*Affected tools: SeqSero2, SISTR, mlst, ShigaTyper, ECTyper, Kaptive, emmTyper, chewBBACA*

### 1.1 Trivial / Degenerate Inputs

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Empty or zero-length assembly | No sequences to query | Crash or **SILENT** empty output (exit 0) |
| All-N assembly | No usable k-mers or BLAST hits | **SILENT** "no hits" / "untypeable" with no error |
| Wrong organism submitted | Tool has no organism guard | Confident wrong call using conserved housekeeping k-mers |
| Wrong subspecies (Salmonella subsp. II–VI) | Tools trained on subsp. I only | Suppresses subspecies discriminator, calls wrong serovar |

### 1.2 Novel / Rare Types

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Novel MLST allele (not in PubMLST) | Allele absent from database | Reports `?` for locus, `-` for ST — no closest-match warning |
| Novel ST (alleles known, combination unregistered) | Combination not assigned | Reports "novel" / `0`; downstream integer-ST tools crash |
| Rare unnamed serovar (antigenic formula not in Kauffmann-White) | Formula exists, no name assigned | SISTR reports formula, empty name field; SeqSero2 calls nearest named serovar (wrong) |
| High-numbered / rare ST (>1000) | Underrepresented in training data | ML-assisted tools assign wrong ST by nearest-neighbor error |

### 1.3 Biological Phenomena

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Monophasic flagellar variant (H2 deleted/silenced) | H2 locus absent | Tools predict biphasic (H2=1,2) when strain is truly monophasic — critical for *S.* Typhimurium 1,4,[5],12:i:- surveillance |
| Rough strain (O-antigen biosynthesis defect) | Truncated or absent LPS O-chain | Reports "O:-" or "Rough"; typing only by H antigen; ambiguous call |
| Non-motile / aflagellate variant | fliC/fljB deletion | Both H antigens reported as "-"; misidentified as Gallinarum/Pullorum |
| Plasmid-borne O-antigen gene cluster | rfb operon acquired horizontally | Conflicting or chimeric O-antigen calls; both chromosomal and plasmid loci detected |
| Prophage insertion disrupting typing locus | Prophage in fliC, fljB, or rfb | Partial alignment; locus called as missing; k-mer tools miss junction |
| Recombination scrambling a typing locus | Mosaic allele from intragenic recombination | Top BLAST hit is donor type, not true mosaic; wrong call at ~95% identity threshold |
| Vi capsule loss (Typhi Vi-negative) | viaB locus deleted | Fails to flag regulated pathogen; SeqSero2 reports formula without [Vi] |
| Simultaneous H1 and H2 expression (phase variation failure) | hin inversion stuck or absent | Both H antigens reported; doesn't match any named serovar |

### 1.4 Assembly Quality Artifacts

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Truncated allele at contig boundary | Typing locus spans contig break | mlst: `~N` (partial) or `-` (missing); chewBBACA: NIPH/LOTSC |
| Fragmented assembly obscuring multi-gene typing loci | O-antigen cluster (~20 kb) fragmented | SISTR: "O antigen prediction: -"; SeqSero2: serogroup only, no full formula |
| Highly repetitive sequences near typing genes | IS elements flanking typing loci | Misassembled loci; chimeric contigs; wrong allele called |

### 1.5 Mixed / Contaminated Samples

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Two serotypes in one sample (mixed infection) | Reads/contigs from two strains | Chimeric formula call; minor serotype reported as "novel allele" |
| Cross-species contamination | Assembly has contigs from different organism | mlst autodetect picks wrong scheme; SISTR low confidence |

### 1.6 Database & Ambiguity Issues

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Paratyphi B vs. Java (d-Tartrate phenotype) | Distinguished only by STM3356 SNP, not antigen formula | SeqSero2/SISTR cannot distinguish; reports formula identically for both |
| ST34 vs. ST19 (single-locus variant) | aroC allele difference only | mlst correctly calls ST34; surveillance pipelines expect ST19 — semantic mismatch |
| Serovar renamed between database versions | Kauffmann-White scheme updated | Tool reports old name; validation expects new name; biological call is correct |

---

## 2. Population Variant Analysis (SNP Pipelines)

*Affected tools: snippy, snippy-core, Gubbins, ClonalFrameML, CFSAN-SNP-Pipeline, lyve-SET, kSNP3, Parsnp*

### 2.1 Trivial / Degenerate Inputs

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Zero-SNP alignment (all samples identical to reference) | No variable sites | Gubbins/ClonalFrameML crash; CFSAN-SNP-Pipeline downstream RAxML call fails with "no variable sites" |
| Single sample | No pairwise comparison; 2-leaf tree undefined | Gubbins requires ≥3 taxa, crashes; others produce trivial output |
| All samples filtered out by QC | Empty sample list | Cryptic glob-expansion errors; pipelines die at pileup step with no BAM files |

### 2.2 Population Structure Issues

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| **Sample swap — wrong organism in cohort** | One sample from distant species in clonal set | **SILENT**: snippy-core core genome collapses to near-zero; 0 core SNPs reported; no error. Gubbins flags outlier as "massively recombinant." ClonalFrameML inflates r/m for entire dataset |
| Mixed lineages in supposedly clonal set | Inter-lineage SNP density >> intra-lineage | Gubbins misidentifies divergence as recombination; r/m wildly inflated; tree topology wrong |
| Multiple independent outbreak clusters submitted as one cohort | Dataset is not clonal | Gubbins/ClonalFrameML results biologically meaningless; no tool warns about population structure violation |

### 2.3 Recombination Artifacts

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| High recombination organism (H. pylori, N. gonorrhoeae) | >50% of SNP variation is imported via recombination | SNP-based phylogeny reconstructs recombination history, not clonal frame; Gubbins may fail to converge |
| Recombinant region appearing as dense SNP cluster | HGT import looks like many simultaneous mutations | RAxML long-branch attraction; CFSAN density filter removes real signal; Gubbins over-masks flanking region |

### 2.4 Reference Selection Failures

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Wrong reference genome (different serovar/lineage) | Fixed between-lineage differences inflate SNP count | **SILENT**: core genome shrinks; SNP counts inflated; phylogeny distorted; Gubbins r/m estimates wrong |
| Reference too distant (>50% mapping rate) | Reads cannot uniquely map | Crash or near-empty SNP matrix; cryptic downstream RAxML failure |
| Plasmid reference vs. chromosome reads | Coverage heterogeneity + AMR gene multi-mapping | **SILENT**: phylogeny mixes chromosomal and plasmid evolutionary histories |
| Multi-chromosome reference | Some tools assume single linear chromosome | Version-dependent crash or correct handling |

### 2.5 Technical Artifacts

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Low-coverage sample mixed into cohort | High genotyping error; many N calls | **SILENT**: snippy-core `--mincov` shrinks core genome for entire dataset; distances to low-coverage sample underestimated |
| Mixed sequencing platforms (Illumina + ONT) | Platform-specific error signatures | **SILENT**: tree splits by sequencing technology, not biology; systematic false SNPs at homopolymers |
| Duplicate samples (same isolate twice) | Zero-length branches in tree | Gubbins/ClonalFrameML numerical instability; possible SIGFPE crash |

### 2.6 Core Genome Collapse

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Samples with large chromosomal deletions | Deleted positions → non-core for entire dataset | **SILENT**: core genome shrinks by deletion size; if multiple samples have different deletions, core collapses to <10% of chromosome |
| Samples with large insertions not in reference | Reads from inserted region multi-map to off-target loci | **SILENT**: insertion invisible in VCF; false SNPs at multi-mapping loci |
| Diverse sample set (core genome collapse) | Each added divergent sample shrinks the intersection | Gubbins crashes on alignment too short; or tree reflects only 3-4 housekeeping genes |

### 2.7 Tool-Specific Failures

| Phenomenon | Tool | Failure Behavior |
|---|---|---|
| Iterative algorithm non-convergence | Gubbins | **SILENT**: hits max iterations (default 5), outputs last unstable result without warning |
| Phylogeny tip label mismatch | ClonalFrameML | Crash; very sensitive to whitespace, trailing characters |
| Wrong k-mer size selection | kSNP3 | **SILENT**: wrong k produces inflated/deflated SNP counts; plausible-looking topology |
| No repeat masking | lyve-SET | **SILENT**: IS element SNPs inflate distances; samples with more IS elements appear more diverged |
| Multi-allelic site handling at VCF merge | CFSAN-SNP-Pipeline | **SILENT** data loss: multi-allelic sites (can be real) silently excluded |
| Fragmented assembly input | Parsnp | OOM crash or silent data loss from short-contig exclusion |
| Mixed infection / heterozygosity | snippy | **SILENT**: heterozygous positions become N; core genome shrinks; contaminated sample produces no phylogenetic signal |

---

## 3. Assembly Tools

*Affected tools: SPAdes, Velvet, Flye, Unicycler, SKESA, ABySS*

### 3.1 Trivial / Degenerate Inputs

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Empty input file | No reads to build k-mer graph | Crash (most) or **SILENT** empty FASTA with exit 0 (SKESA, ABySS) |
| All-N reads | N bases contribute no valid k-mers | **SILENT**: 0 contigs, exit 0; or single N-filled contig; Unicycler may hang in polishing |
| Too few reads (<1x coverage) | K-mer graph entirely disconnected | **SILENT** (SPAdes/ABySS: fragmented output, exit 0); Flye: explicit "No disjointigs" error |
| Single-ended reads given as paired input | Missing mate; insert size estimation fails | SPAdes: wrong assembly, scaffolding disabled silently; Velvet: crash |
| Read file truncated mid-record | Incomplete FASTQ record | Crash (SPAdes, Flye) or WRONG output (Velvet reads partial k-mers) |

### 3.2 Biological Phenomena

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Mixed organism contamination | Two subgraphs share conserved k-mers (16S, housekeeping) | **SILENT** chimeric scaffolds; inflated genome size; no contamination warning |
| Plasmid with high-copy IS elements | IS elements create graph bubbles; copy number unresolvable | **SILENT**: wrong plasmid size; IS element count wrong; plasmid may fuse to chromosome |
| Prophage insertion (long terminal repeats) | LTRs collapse; phage-host junctions misassembled | **SILENT**: phage region missing or duplicated; integration site incorrect |
| Highly repetitive genome (Mycobacterium IS6110, Streptomyces) | Repeat copy number exceeds read length | **SILENT**: large repeat regions collapsed; genome appears 20–30% smaller than actual |
| Very high GC content (>70%, e.g., Streptomyces) | Library GC bias causes coverage dropouts in k-mer graph | **SILENT**: genes in high-GC regions missing from assembly; normal-looking N50 reported |
| Sample dominated by phage (>50% reads) | Phage at 200x; host at 20x; coverage-based filters remove host | **SILENT**: only phage assembled; host chromosome absent |

### 3.3 Technical Artifacts

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Very low coverage (<5x) | Most k-mers appear once; indistinguishable from errors | **SILENT** (SPAdes BayesHammer removes real reads as "errors"); Flye/SKESA crash |
| Adapter contamination | Adapter k-mers form hub node connecting unrelated sequences | **SILENT** chimeric contigs joined through adapter; no assembler catches this |
| Optical/PCR duplicates not removed | Duplicate-inflated coverage; k-mer spectrum loses bimodal structure | **SILENT**: repeat copy numbers miscalled |

### 3.4 K-mer Failures

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Suboptimal k-mer selection for short reads (<80bp) | Default k (55 or 77) too large for 75bp reads | **SILENT**: Velvet/ABySS assemblies 4–5x fewer contigs but miss many sequences |
| Tandem repeats shorter than read length | Bubbles; assembler cannot determine copy number without spanning reads | **SILENT**: VNTR loci systematically wrong; wzy, rfb clusters |

### 3.5 Silent Output Quality Failures

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| rRNA operon collapse | 99%+ identical copies collapsed to single node | **SILENT** universal: genome appears to have 1 rrn operon instead of 6–10 |
| IS element misassembly | IS elements present at single copy in assembly even if 6 copies in genome | **SILENT**: flanking gene order wrong; IS-mediated deletions invisible |
| Plasmid integrated into chromosome scaffold | Plasmid/chromosome share IS elements; scaffolding joins them | **SILENT**: AMR genes appear chromosomally encoded when plasmid-borne |
| Chimeric contigs at repetitive regions | Two loci connected by repeat shorter than read length | **SILENT**: BLAST shows one contig end matching two different chromosomal locations |

### 3.6 Scale Failures

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Plasmid-only sample (no chromosome) | Assembler assumes chromosomal structure; plasmid flagged as contamination | **SILENT**: Unicycler labels plasmid "unresolved"; SKESA drops small plasmids (500bp minimum) |
| Sample with >10 plasmids | Topology assumptions fail; shared backbone merges plasmids | **SILENT**: wrong plasmid count; AMR genes on wrong replicon |
| Very small genome (<1 Mb, Mycoplasma) | SPAdes --cov-cutoff auto discards genome as "low coverage" | **SILENT**: empty assembly or only partial genome |

---

## 4. Alignment Tools

*Affected tools: BWA-MEM, BWA-MEM2, Bowtie2, Minimap2, STAR*

### 4.1 Trivial / Degenerate Inputs

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Empty FASTQ file | 0 reads | **SILENT**: exit 0, empty BAM; GATK/variant callers may crash downstream |
| All-N reads | No valid seeds | **SILENT**: unmapped; paired-mate rescue may misplace mate |
| Zero-length reads | Empty sequence field in FASTQ | Crash (BWA segfault, Bowtie2 error) or silent skip |
| Reads shorter than k-mer/seed size | Below 19bp (BWA) or 21bp (Minimap2 sr) | **SILENT**: unmapped with no warning |
| Mismatched R1/R2 read counts | Unequal records after asymmetric trimming | BWA hangs or wrong pairing; Bowtie2/STAR catch and error |
| Duplicate read names | Same QNAME multiple times | **SILENT**: downstream deduplication tools break silently |

### 4.2 Biological Phenomena

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Extreme GC content (>80% or <20%) | Repetitive GC seeds; AT-rich random-match probability | **SILENT** coverage dropout; detectable only by per-position depth analysis |
| Highly repetitive regions (satellite, centromeres, transposons) | Seeds match thousands of locations; MAPQ=0 | **SILENT**: reads unmapped or randomly placed; Minimap2 most honest (unmapped rather than placed) |
| Large structural variants (inversions, translocations) | Split reads required | **SILENT** (Bowtie2: no split-read support; SV signal entirely lost); STAR: SV looks like splice junction |
| Plasmid/chromosome shared sequences | Reads multi-map to shared loci; MAPQ=0 | **SILENT**: resistance gene variants on plasmid become invisible to variant callers |
| Contamination at conserved loci | rRNA/housekeeping genes align from wrong organism at high MAPQ | **SILENT** false positives; NM tag elevated but not automatically filtered |
| Circular reference linearized | Reads spanning artificial boundary are split/soft-clipped | **SILENT** coverage gap at position 1 and end of every contig |

### 4.3 Technical Artifacts

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Untrimmed adapters | Adapter forces soft-clipping; >50% adapter = unmapped | STAR: **SILENT** false novel splice junctions at adapter boundary |
| Very short reads (<30bp) | MAPQ reliability collapses; random matches inflate confidence | **SILENT** MAPQ overconfidence; BWA: inflated MAPQ by scoring heuristic |
| Low-quality reads (all Q2) | Quality ignored during alignment; Q2 reads get same MAPQ as Q40 reads | **SILENT**: variant callers must filter independently; aligner is unaware |
| IUPAC bases in reference | Indexed as N; read bases at IUPAC positions scored as mismatches | **SILENT** elevated NM, reduced MAPQ near IUPAC-rich regions |
| Duplicate contig names in reference | First contig wins; second silently ignored | **SILENT** data loss |
| Minimap2 preset mismatch (sr preset on ONT data) | Wrong chaining parameters | **SILENT** high-MAPQ wrong alignments; output looks valid |
| STAR genome parameters not matched to assembly | --genomeSAindexNbases wrong for small genome or many contigs | Segfault at genome generation, or 0% mapping with no useful error |

### 4.4 Scale Issues

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Very high depth (>1000x) | Insert size estimation dominated by PCR duplicates | **SILENT**: proper-pair flagging wrong for all reads |
| Uneven coverage (amplicons, capture) | Extreme depth at amplicons; Minimap2 chaining is O(n²) in anchors | Minimap2 OOM at targeted long-read loci |

---

## 5. Gene Prediction and Annotation

*Affected tools: Prokka, PGAP, Prodigal, Augustus, Glimmer, RAST, Bakta*

### 5.1 Trivial / Degenerate Inputs

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Empty FASTA | No sequences | Crash (Prokka, Prodigal, PGAP, Augustus) or **SILENT** empty output (RAST) |
| All-N assembly | No resolvable ATG or stop codons | **SILENT**: 0 CDS, exit 0 (Prodigal, Prokka); Glimmer training fails silently |
| Assembly < 20 kb total | Below Prodigal's minimum for codon model training | Prodigal: explicit error in single-genome mode; must use `-p meta`; Prokka inherits crash |
| Highly fragmented assembly (10,000+ contigs) | Genes at contig boundaries are simply absent | **SILENT** gene loss at every boundary; PGAP hard-fails; RAST times out |

### 5.2 Biological Phenomena

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Non-standard genetic code (Mycoplasma UGA=Trp, table 4) | Wrong translation table truncates proteins at UGA | Prodigal/Prokka/Glimmer default to table 11; every UGA-Trp codon terminates an ORF; systematic truncation; Glimmer hardcoded, cannot handle |
| Very high/low GC content | Codon bias models trained on ~50% GC organisms | **SILENT**: Glimmer up to 30% false-negative rate; Prodigal degrades on short inputs |
| Overlapping genes (phage, plasmids) | Post-processing prunes overlaps; biological overlaps removed | **SILENT**: lower-scoring gene of each overlapping pair lost; Glimmer systematic miss |
| Very short genes (<90bp / <30aa) | Below minimum ORF length cutoffs | **SILENT** universal miss in all tools |
| Programmed frameshifts (prfB, dnaX) | Cannot be modeled by 6-frame scan | **SILENT**: gene split into two adjacent truncated ORFs |
| Pseudogenes | Require protein homology + disruptive mutation modeling | **SILENT** (Prodigal/Glimmer: miss entirely); Prokka: wrong functional annotation on fragments |
| Prophage insertion | Phage codon usage skews assembly-wide model | **SILENT**: host genes near insertion missed; phage ORFs predicted at lower confidence |

### 5.3 Annotation-Level Failures

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Wrong taxonomy → wrong reference protein database | PGAP/RAST select proteins by taxon | **SILENT**: systematic wrong functional annotation; wrong EC numbers, substrate specificities |
| Alternative start codons (GTG, TTG, CTG) | ATG preferred; alternative starts scored lower | **SILENT** ~10–20% wrong start sites; lower-scoring ATG nearby selected instead |
| Genes split across contigs | Each contig treated independently | **SILENT** universal: gene exists in genome but no full-length annotation produced |
| Augustus applied to bacteria | Eukaryote splice-site model applied to intronless genome | Systematic wrong output; spurious multi-exon models; no warning about wrong organism model |
| Prodigal on plasmid-only assembly (<100 kb) | Insufficient sequence for codon model | Hard error in default mode; must use `-p meta`; degraded accuracy in meta mode |

---

## 6. AMR / Resistance Gene Detection

*Affected tools: ResFinder, AMRFinderPlus, RGI/CARD, ARIBA, abricate*

### 6.1 Core Failure Modes

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Novel resistance gene (database lag) | Gene <80% identity to any known entry | **SILENT** false negative: tool reports susceptible; isolate is resistant |
| Truncated resistance gene (contig break) | Each fragment below coverage threshold | **SILENT** false negative: blaKPC split across two contigs; neither fragment reaches 60% coverage |
| Plasmid vs. chromosome conflation | Tools report gene presence only; no replicon context | **SILENT**: intrinsic chromosomal genes flagged as acquired AMR threats |
| Point mutation resistance, acquired-gene-only tool | gyrA S83L missed if `-point` flag absent | **SILENT** false negative: fluoroquinolone/isoniazid resistance missed by ResFinder without PointFinder |
| Multiple copies at different identity levels | Single identity threshold; divergent copy miscalled | **SILENT** allele-level misidentification: blaOXA-181 called as blaOXA-48 |
| Resistance gene in wrong organism context | No gene-organism plausibility check | False positive: erm(B) in Salmonella reported as resistance regardless of biological plausibility |
| Synonymous variant near resistance site | Flanking SNP breaks k-mer matching | **SILENT** false negative: ARIBA fails to recruit reads carrying resistance allele |

---

## 7. QC Tools and File Format Edge Cases

*Affected tools: FastQC, MultiQC, fastp, Trimmomatic, NanoStat*

### 7.1 Misleading QC Pass/Fail

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Amplicon library (legitimate high duplication) | FastQC duplication detection assumes shotgun WGS | False FAIL: automated pipelines reject valid amplicon data |
| High-GC organism (Streptomyces 72% GC) | FastQC compares to theoretical 45% GC normal | False FAIL on "Per Sequence GC Content" for any organism outside 40–55% GC |
| Contaminated library passes QC | QC tools evaluate read-level properties, not biological identity | **SILENT**: 20% human + 80% bacterial both look normal; FastQC/fastp cannot detect |
| All reads same length (simulated data) | Not typical of real Illumina data | FastQC WARN: automated pipelines may reject valid synthetic data |

### 7.2 Tool Misconfiguration

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Nanopore reads through Illumina QC (Trimmomatic) | Q12–15 ONT reads fail SLIDINGWINDOW:4:20 | Trimmomatic discards 95–100% of reads silently; output file exists but is near-empty |
| Single-read FASTQ to paired-end tool | Trimmomatic PE mode expects two files | Trimmomatic throws `PairedEndIterator received an odd number of reads`; fastp silently runs SE mode without pair-aware adapter trimming |
| All reads identical (PCR jackpot) | fastp dedup reduces 50M reads to 1 | Downstream crash; FastQC detects via Overrepresented Sequences but doesn't block pipeline |

### 7.3 File Format Edge Cases

| Phenomenon | Mechanism | Failure Behavior |
|---|---|---|
| Phred+64 quality scores fed to Phred+33 tool | `@` character (Q0 in Phred+64) is FASTQ record header prefix | GATK: `SAMFormatException`; fastp: crash or skip; FastQC: may misclassify encoding |
| FASTA headers with spaces | Most tools truncate at first whitespace; some don't | **SILENT** ID mismatch across tools; AMRFinderPlus/ResFinder hits don't match assembly FASTA |
| Windows line endings (CRLF) in FASTA/FASTQ | `\r` character appears in sequence data | BLAST/Kraken2 crash; SeqSero2/MLST compute wrong sequence lengths silently |
| Truncated gzipped file (partial download) | Missing end-of-stream marker | fastp: **SILENT** partial output (processes all complete reads, then reports truncation — output appears complete); BWA-MEM: crash mid-run |
| Empty gzipped file | Valid gzip format, 0 bytes decompressed content | SPAdes: crash; ResFinder/abricate: **SILENT** empty output, no error |
| File named `.fastq.gz` that is plain text | Magic byte mismatch | samtools/fastp: immediate error; FastQC: handles gracefully (the exception) |

---

## Cross-Cutting Patterns

The most dangerous failure modes share all of these characteristics:
1. **Exit 0** — no crash, no non-zero return code
2. **Valid-format output** — passes format validators (samtools view, gzip -t)
3. **Plausible summary statistics** — mapping rate, contig count, typing result look reasonable
4. **Localized failure** — only specific reads, positions, or samples are affected

The phenomena most likely to silently corrupt clinical or surveillance outputs:
- **Sample swap in SNP cohort** — 0 core SNPs reported, no error
- **Wrong organism to in-silico typer** — confident wrong serotype/ST
- **rRNA operon collapse in assembly** — universal in short-read assemblies, never warned
- **Novel resistance gene** — susceptible reported for resistant isolate
- **Plasmid/chromosome fusion in assembly** — AMR genes misattributed to chromosome
- **Gubbins non-convergence** — unstable phylogeny output as if converged

---

## Data Sources

Public datasets for challenges are sourced primarily from NCBI SRA and NCBI Assembly. Each challenge directory contains a `manifest.json` with accessions, sample roles, and download instructions. See `MANIFEST_SCHEMA.md` for schema documentation.

Synthetic/recipe-based challenges (where no public dataset captures the exact pathological condition) are documented with generation recipes in the manifest `source_type: recipe` field.
