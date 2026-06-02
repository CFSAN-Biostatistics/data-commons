# AGENTS.md — AI Agent Guide for the Challenges Library

This document is for AI agents tasked with using this library to validate bioinformatics tools. It covers philosophy, how to select and run challenges, how to form tool command lines, and how to recognize that a failure mode fired.

---

## What This Library Is (and Isn't)

This is a **stimulus library**, not a test suite. The distinction matters:

- A test suite has a pass/fail assertion. You run the tool and compare output to expected output.
- A stimulus library has a *pathological condition* — an input designed to trigger a known failure mode. There is no canonical "correct" output. The purpose is to observe what the tool does when put under stress.

**The most dangerous failures are silent.** They share four characteristics:
1. Exit code 0 — no crash, no non-zero return
2. Valid-format output — the file passes format validators
3. Plausible aggregate statistics — mapping rate, contig count, gene count all look reasonable
4. Localized failure — only specific reads, positions, samples, or genes are affected

When a challenge fires correctly, the tool often looks like it succeeded. Your job is to look past the summary statistics to the specific data the challenge was designed to stress.

---

## Workflow: Validating a Tool Against Relevant Challenges

### Step 1: Identify Relevant Challenges

Read each manifest's `tool_categories` and `tool_families` fields:

```bash
# Find all challenges relevant to alignment tools
python3 -c "
import json, pathlib
for p in sorted(pathlib.Path('.').glob('*/*/manifest.json')):
    d = json.load(open(p))
    cats = d.get('tool_categories', [])
    fams = d.get('tool_families', [])
    if 'alignment' in cats or 'bwa-family' in fams:
        print(p.parent)
"
```

Also check `tool_families` — some challenges are tagged to a specific tool family (e.g., `snippy-family`) even if their `tool_categories` is broader.

Prioritize challenges whose `known_behaviors` field mentions your tool by name. If `known_behaviors` is absent, the challenge is still valid — just less pre-characterized.

### Step 2: Read the Manifest Before Running Anything

The `mechanism` field is the most important field. It explains *why* this input is adversarial. Read it before constructing any commands. It tells you:
- What the input condition is
- Why it stresses the tool
- What signal to look for in the output

The `known_behaviors` field (optional) documents observed tool behavior from prior runs. Use it as a prior, not a ground truth — your tool version may behave differently.

### Step 3: Download the Data

```bash
python3 acquire.py --challenge PHENOMENON/INSTANCE
```

Recipe-based challenges (those with `source_type: recipe` samples) generate synthetic data locally. Check `recipe.tools_required` in the manifest if the download fails — you may be missing `seqtk`, `python3`, or similar.

### Step 4: Render the Layout

```bash
python3 layout.py --challenge PHENOMENON/INSTANCE --tool TOOL_FAMILY --out /tmp/challenge_run
```

Use `python3 layout.py --list-tools` to see all available tool families and their invocation hints. Pick the family that matches your tool. If no family matches exactly, pick the closest one and note the deviation.

The `--out` directory will contain symlinks to the downloaded data, arranged the way the tool expects. Use this directory as your working directory when running the tool.

### Step 5: Form the Tool CLI

**Always run the tool with its default flags first.** These challenges are designed to fire on default configurations — the failure is the tool's out-of-the-box behavior. Running with remediation flags first obscures the failure.

The layout template's `invocation_hint` (visible in `--list-tools` output and in `tool_layouts/*.json`) gives a minimal working invocation. Adapt it to your specific tool and version.

For multi-sample challenges (those with `ingroup`, `outlier`, or `contaminant` roles), the layout arranges samples in the directory structure the tool family expects. For snippy-family, this is one directory per sample under `samples/`; for cfsan-snp-pipeline, similarly. Check the layout output with `ls -R /tmp/challenge_run/` before invoking.

Capture everything:
```bash
tool-invocation ... > /tmp/challenge_run/stdout.txt 2> /tmp/challenge_run/stderr.txt
echo "exit: $?" >> /tmp/challenge_run/stderr.txt
```

### Step 6: Recognize Whether the Failure Mode Fired

See the section below on detection patterns. After running, always:
1. Check exit code
2. Check that output files exist and are non-empty
3. Read the specific fields the `mechanism` says to inspect
4. Compare against `known_behaviors` if present

### Step 7: Re-run With a Remediation Flag (Optional but Valuable)

After observing the default behavior, consider re-running with a flag that should mitigate the failure. For example:
- A coverage-threshold challenge: re-run ResFinder with `--min_cov 0.40` instead of the default `0.60`
- A point-mutation challenge: re-run ResFinder with `--point -s species_name`
- An identity-threshold challenge: re-run with `--threshold 0.80`

This confirms the failure was caused by the condition the challenge encodes, not some other factor.

---

## Forming Tool Command Lines

### From the Layout

After `layout.py --out /tmp/run`, inspect what files were created:
```bash
find /tmp/run -type l | sort   # all symlinks
find /tmp/run -type l | xargs ls -la   # confirm they resolve
```

The file names match the roles from the manifest: `reference.fasta`, `reads_1.fq.gz`, `reads_2.fq.gz`, or `samples/SAMPLE_ID/reads_1.fq.gz` for multi-sample tools.

### Tool-Specific Notes

**Alignment (bwa-family):** Index the reference before aligning. The layout gives you `reference.fasta` and paired reads. Run `bwa index reference.fasta` first.

**SNP pipelines (snippy-family, cfsan-snp-pipeline):** Multi-sample challenges have a `samples/` directory with one subdirectory per ingroup/outlier sample. The `reference.fasta` is a separate file at the layout root.

**AMR detection (resfinder-family):** ResFinder and AMRFinderPlus both work on assemblies. The layout gives `assembly.fasta`. For point mutation challenges, run ResFinder twice: once without `--point`, once with `--point -s <species>`. AMRFinderPlus requires `-O <organism>` for chromosomal point mutation detection.

**Assembly (spades-family):** Reads only. The layout gives `reads_1.fq.gz` and `reads_2.fq.gz`. No reference.

**In-silico typing (seqsero2, sistr, mlst):** Single-sample assembly input. The layout gives `assembly.fasta`.

---

## Recognizing That a Failure Mode Fired

The challenge fired if the tool produced output consistent with the failure described in the `mechanism` field. The table below maps common failure behaviors to what to check.

| Failure behavior (from `challenge_tags`) | What to check |
|---|---|
| `silent_wrong_output` | Exit 0. Inspect output *values*, not just presence. Compare to what you'd expect for a normal input. |
| `silent_empty_output` | Exit 0. Output file exists but has zero data rows, zero mapped reads, zero contigs, zero resistance genes. |
| `crash` | Non-zero exit code. Check stderr for the error message. Note whether it's informative or cryptic. |
| `tool_misconfiguration` | Exit 0 with wrong or incomplete results. The failure requires running the tool *with* and *without* the correct flag to see the difference. |

### Key checks by tool category

**Alignment:**
- `samtools flagstat` — look for mapped read percentage. 0% = likely fired.
- `samtools depth -a` — check per-position coverage at the locations named in `ground_truth` (e.g., position 1 and contig end for the circular linearization challenge).
- Empty BAM (header only): `samtools view -c output.bam` returns 0.

**Assembly:**
- Contig count and total assembly size: `grep -c '>' assembly.fasta` and `grep -v '>' assembly.fasta | tr -d '\n' | wc -c`
- Zero contigs = fired for degenerate input challenges.
- Assembly size significantly below expected genome size = fired for coverage/GC challenges.

**SNP pipelines:**
- snippy-core `core.aln`: check alignment length and number of variant sites. 0 core SNPs with a diverse cohort = likely fired.
- CFSAN output: check `snpma.fasta` and the distance matrix for all-zero distances or missing samples.

**In-silico typing:**
- SeqSero2/SISTR: empty or "Undetermined" serotype result.
- MLST: all loci showing `-` (not found) or `?` (novel allele not in scheme).

**AMR detection:**
- ResFinder: check `ResFinder_results_tab.txt`. Empty = no resistance genes found.
- AMRFinderPlus: check the output TSV. Count rows with `RESISTANCE` in the Element Type column.
- ABRicate: check the tabular output. Zero rows = nothing found.
- For truncated/low-identity gene challenges: run BLAST directly against the assembly to confirm the gene IS there at the nucleotide level, even though the AMR tool missed it.

---

## Philosophy: What You're Looking For

You are not grading the tool. You are characterizing its behavior under a specific adversarial condition.

A tool that **crashes loudly** on a degenerate input is often better than one that **silently produces wrong output**. The crash is diagnosable. The silent wrong output propagates downstream and may never be caught.

When reporting what you found, structure it as:
1. **What the challenge encodes** — quote the `mechanism` field or summarize it
2. **What the tool did** — exact exit code, relevant output lines, specific values
3. **Whether the failure mode fired** — did the tool behave as the `known_behaviors` field predicts, or differently?
4. **What a downstream consumer would see** — a user looking at the final report, not the internals

The last point is critical. The question is not "did the tool error?" but "would a biologist interpreting this output be misled?" A tool that outputs `Serotype: Undetermined` is less dangerous than one that outputs `Serotype: Typhimurium` when the input was E. coli. Both are wrong; only the second is silently wrong.

---

## Quick Reference

```bash
# List all challenges with their categories
python3 -c "
import json, pathlib
for p in sorted(pathlib.Path('.').glob('*/*/manifest.json')):
    d = json.load(open(p))
    print(f\"{p.parent}  [{', '.join(d.get('tool_categories', []))}]\")
"

# Show tool families and invocation hints
python3 layout.py --list-tools

# Download a challenge
python3 acquire.py --challenge PHENOMENON/INSTANCE

# Render a tool layout
python3 layout.py --challenge PHENOMENON/INSTANCE --tool TOOL_FAMILY --out /tmp/run

# Check what the layout created
find /tmp/run -type l -exec ls -la {} \;

# Run any tool and capture everything
my-tool [flags] > /tmp/run/stdout.txt 2> /tmp/run/stderr.txt; echo "exit:$?" >> /tmp/run/stderr.txt
```

For full flag documentation see [`USAGE.md`](USAGE.md). For the manifest field reference see [`MANIFEST_SCHEMA.md`](MANIFEST_SCHEMA.md). For the catalog of failure modes see [`FAILURE_MODES.md`](FAILURE_MODES.md).
