#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Download sequence data for AMR resistance test cases based on manifest.json specifications.

OPTIONS:
    --all               Download data for all test cases
    --case PATH         Download data for specific test case directory
    --tools TOOLS       Only download data needed for specific tools (comma-separated)
    --force             Re-download even if data exists
    -h, --help          Show this help message

EXAMPLES:
    $0 --all
    $0 --case campy_jejuni_amp_tet_UCLA1626
    $0 --case campy_jejuni_amp_tet_UCLA1626 --tools ResFinder
    $0 --all --force

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

ALL_CASES=false
CASE=""
TOOLS=""
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            ALL_CASES=true
            shift
            ;;
        --case)
            CASE="$2"
            shift 2
            ;;
        --tools)
            TOOLS="$2"
            shift 2
            ;;
        --force)
            FORCE=true
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

if ! $ALL_CASES && [[ -z "$CASE" ]]; then
    error "Must specify --all or --case"
fi

find_test_cases() {
    if $ALL_CASES; then
        find "$SCRIPT_DIR" -mindepth 1 -maxdepth 1 -type d -name "campy_*"
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

needs_data_type() {
    local manifest="$1"
    local data_type="$2"

    if [[ -z "$TOOLS" ]]; then
        if ! jq -e ".data_sources.${data_type}.download_cmd != null" "$manifest" > /dev/null 2>&1; then
            return 1
        fi
        return 0
    fi

    IFS=',' read -ra TOOL_ARRAY <<< "$TOOLS"
    for tool in "${TOOL_ARRAY[@]}"; do
        local input_type
        input_type=$(jq -r ".tools[\"${tool}\"].input_type // empty" "$manifest" 2>/dev/null)
        if [[ "$input_type" == "$data_type" ]] || [[ "$input_type" == "both" ]]; then
            return 0
        fi
    done
    return 1
}

download_case() {
    local case_dir="$1"
    local manifest="$case_dir/manifest.json"

    if [[ ! -f "$manifest" ]]; then
        log "Skipping $case_dir: no manifest.json found"
        return
    fi

    log "Processing case: $(basename "$case_dir")"
    mkdir -p "$case_dir/data"

    if needs_data_type "$manifest" "reads"; then
        local reads_cmd
        reads_cmd=$(jq -r '.data_sources.reads.download_cmd // empty' "$manifest")

        if [[ -n "$reads_cmd" ]]; then
            if ! $FORCE && find "$case_dir/data" -name "*.fq.gz" -o -name "*.fastq.gz" | grep -q .; then
                log "  Reads already exist, skipping (use --force to re-download)"
            else
                log "  Downloading reads..."
                (cd "$case_dir" && eval "$reads_cmd") || error "Failed to download reads for $(basename "$case_dir")"
                log "  Reads downloaded successfully"
            fi
        fi
    fi

    if needs_data_type "$manifest" "assembly"; then
        local assembly_cmd
        assembly_cmd=$(jq -r '.data_sources.assembly.download_cmd // empty' "$manifest")

        if [[ -n "$assembly_cmd" ]]; then
            if ! $FORCE && find "$case_dir/data" -name "*.fa" -o -name "*.fna" -o -name "*.fasta" | grep -q .; then
                log "  Assembly already exists, skipping (use --force to re-download)"
            else
                log "  Downloading assembly..."
                (cd "$case_dir" && eval "$assembly_cmd") || error "Failed to download assembly for $(basename "$case_dir")"
                log "  Assembly downloaded successfully"
            fi
        fi
    fi
}

main() {
    if ! command -v jq &> /dev/null; then
        error "jq is required but not installed. Please install jq."
    fi

    log "Starting download..."

    local case_count=0
    while IFS= read -r case_dir; do
        download_case "$case_dir"
        ((case_count++))
    done < <(find_test_cases)

    if [[ $case_count -eq 0 ]]; then
        log "No test cases found matching criteria"
    else
        log "Downloaded data for $case_count test case(s)"
    fi
}

main
