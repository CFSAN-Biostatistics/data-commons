#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Run typing tools on test cases based on manifest.json specifications.

OPTIONS:
    --all                   Run all tools on all test cases
    --case PATH             Run tools on specific test case directory
    --tool TOOL             Run specific tool (can be repeated)
    --all-tools             Run all tools defined in manifest
    --all-cases             Run on all test case directories
    --dry-run               Print commands without executing
    -h, --help              Show this help message

EXAMPLES:
    $0 --case sal_typhimurium_SRR14029682 --all-tools
    $0 --case sal_typhimurium_SRR14029682 --tool SeqSero2
    $0 --all
    $0 --all-cases --tool MLST

EOF
    exit 1
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

error() {
    log "ERROR: $*"
    exit 1
}

# Parse command line arguments
ALL=false
CASE=""
TOOLS=()
ALL_TOOLS=false
ALL_CASES=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            ALL=true
            ALL_CASES=true
            ALL_TOOLS=true
            shift
            ;;
        --case)
            CASE="$2"
            shift 2
            ;;
        --tool)
            TOOLS+=("$2")
            shift 2
            ;;
        --all-tools)
            ALL_TOOLS=true
            shift
            ;;
        --all-cases)
            ALL_CASES=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Validate arguments
if ! $ALL && ! $ALL_CASES && [[ -z "$CASE" ]]; then
    error "Must specify --all, --all-cases, or --case"
fi

if ! $ALL_TOOLS && [[ ${#TOOLS[@]} -eq 0 ]]; then
    error "Must specify --all-tools or --tool"
fi

# Find test case directories
find_test_cases() {
    if $ALL_CASES; then
        find "$SCRIPT_DIR" -mindepth 1 -maxdepth 1 -type d -name "sal_*"
    elif [[ -n "$CASE" ]]; then
        if [[ -d "$SCRIPT_DIR/$CASE" ]]; then
            echo "$SCRIPT_DIR/$CASE"
        elif [[ -d "$CASE" ]]; then
            echo "$CASE"
        else
            error "Case directory not found: $CASE"
        fi
    fi
}

# Get list of tools to run for a manifest
get_tools_to_run() {
    local manifest="$1"

    if $ALL_TOOLS; then
        # Get all tool names from manifest
        jq -r '.tools | keys[]' "$manifest" 2>/dev/null || true
    else
        # Return specified tools
        printf '%s\n' "${TOOLS[@]}"
    fi
}

# Run a single tool on a test case
run_tool() {
    local case_dir="$1"
    local tool_name="$2"
    local manifest="$case_dir/manifest.json"

    if [[ ! -f "$manifest" ]]; then
        log "  Skipping: no manifest.json found"
        return 1
    fi

    # Get tool configuration
    local run_cmd
    run_cmd=$(jq -r ".tools.${tool_name}.run_cmd // empty" "$manifest" 2>/dev/null)

    if [[ -z "$run_cmd" ]]; then
        log "  Tool $tool_name not configured in manifest"
        return 1
    fi

    # Check if required data exists
    local input_type
    input_type=$(jq -r ".tools.${tool_name}.input_type // empty" "$manifest")

    case "$input_type" in
        reads)
            if ! find "$case_dir/data" -name "*.fq.gz" -o -name "*.fastq.gz" 2>/dev/null | grep -q .; then
                log "  ERROR: Reads not found for $tool_name (run download.sh first)"
                return 1
            fi
            ;;
        assembly)
            if ! find "$case_dir/data" -name "*.fa" -o -name "*.fna" -o -name "*.fasta" 2>/dev/null | grep -q .; then
                log "  ERROR: Assembly not found for $tool_name (run download.sh first)"
                return 1
            fi
            ;;
        both)
            if ! find "$case_dir/data" -type f 2>/dev/null | grep -q .; then
                log "  ERROR: No data found for $tool_name (run download.sh first)"
                return 1
            fi
            ;;
    esac

    # Create actual output directory
    local tool_output_dir
    tool_output_dir=$(dirname "$case_dir/actual/${tool_name}/output")
    mkdir -p "$tool_output_dir"

    # Execute tool
    log "  Running $tool_name..."

    if $DRY_RUN; then
        log "  [DRY RUN] Would execute: $run_cmd"
    else
        (
            cd "$case_dir" || exit 1
            eval "$run_cmd" 2>&1 | tee "actual/${tool_name}.log" || {
                log "  ERROR: $tool_name failed (see actual/${tool_name}.log)"
                return 1
            }
        )
        log "  $tool_name completed successfully"
    fi

    return 0
}

# Process a single test case
process_case() {
    local case_dir="$1"
    local manifest="$case_dir/manifest.json"

    log "Processing case: $(basename "$case_dir")"

    if [[ ! -f "$manifest" ]]; then
        log "  Skipping: no manifest.json found"
        return
    fi

    # Get tools to run
    local tool_count=0
    local success_count=0

    while IFS= read -r tool_name; do
        if [[ -n "$tool_name" ]]; then
            ((tool_count++))
            if run_tool "$case_dir" "$tool_name"; then
                ((success_count++))
            fi
        fi
    done < <(get_tools_to_run "$manifest")

    if [[ $tool_count -eq 0 ]]; then
        log "  No tools to run"
    else
        log "  Completed $success_count/$tool_count tools successfully"
    fi
}

# Main execution
main() {
    # Check for required tools
    if ! command -v jq &> /dev/null; then
        error "jq is required but not installed. Please install jq."
    fi

    log "Starting tool execution..."

    if $DRY_RUN; then
        log "DRY RUN MODE - no commands will be executed"
    fi

    local case_count=0
    while IFS= read -r case_dir; do
        process_case "$case_dir"
        ((case_count++))
    done < <(find_test_cases)

    if [[ $case_count -eq 0 ]]; then
        log "No test cases found matching criteria"
    else
        log "Processed $case_count test case(s)"
    fi

    if ! $DRY_RUN; then
        log ""
        log "Tool execution complete. Review outputs in actual/ directories."
        log "To validate results: ./scripts/validate.py --case <case_name>"
        log "To commit expected outputs: cp -r <case>/actual/* <case>/expected/"
    fi
}

main
