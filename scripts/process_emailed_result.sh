#!/bin/bash
set -e

# Process Emailed Result Script
# Helper script for maintainers to quickly process result files received via email

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SUBMITTED_DIR="$REPO_ROOT/results/submitted"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Function to show usage
show_usage() {
    echo "Process Emailed Result - Helper for maintainers"
    echo ""
    echo "Usage: $0 <result-file.json> [options]"
    echo ""
    echo "Options:"
    echo "  --copy-only       Copy file to submitted/ without validation or aggregation"
    echo "  --validate        Copy and validate only (no aggregation)"
    echo "  --aggregate       Copy, validate, and run aggregation"
    echo ""
    echo "Examples:"
    echo "  $0 ~/Downloads/cursor_modelA_REST_run1_20241218T1430.json"
    echo "  $0 result.json --validate"
    echo "  $0 result.json --aggregate"
    echo ""
}

# Parse arguments
if [[ $# -eq 0 ]]; then
    show_usage
    exit 1
fi

RESULT_FILE="$1"
MODE="validate"  # default mode

# Parse optional flags
shift
while [[ $# -gt 0 ]]; do
    case "$1" in
        --copy-only)
            MODE="copy"
            shift
            ;;
        --validate)
            MODE="validate"
            shift
            ;;
        --aggregate)
            MODE="aggregate"
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main processing
main() {
    echo "============================================================"
    echo "  Process Emailed Result File"
    echo "============================================================"
    echo ""
    
    # Check if file exists
    if [[ ! -f "$RESULT_FILE" ]]; then
        print_error "File not found: $RESULT_FILE"
        exit 1
    fi
    
    # Get filename
    local filename=$(basename "$RESULT_FILE")
    local dest_path="$SUBMITTED_DIR/$filename"
    
    print_info "Source: $RESULT_FILE"
    print_info "Destination: $dest_path"
    print_info "Mode: $MODE"
    echo ""
    
    # Check if destination already exists
    if [[ -f "$dest_path" ]]; then
        print_warning "File already exists in submitted/: $filename"
        read -p "Overwrite? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Cancelled by user"
            exit 0
        fi
    fi
    
    # Ensure submitted directory exists
    mkdir -p "$SUBMITTED_DIR"
    
    # Copy file
    print_info "Copying file to results/submitted/..."
    cp "$RESULT_FILE" "$dest_path"
    print_success "File copied successfully"
    echo ""
    
    # Validate if requested
    if [[ "$MODE" == "validate" ]] || [[ "$MODE" == "aggregate" ]]; then
        print_info "Validating result file..."
        if [[ -x "$SCRIPT_DIR/validate_result.sh" ]]; then
            if "$SCRIPT_DIR/validate_result.sh" "$dest_path"; then
                print_success "Validation passed"
                echo ""
            else
                print_error "Validation failed"
                echo ""
                print_warning "File has been copied but validation found issues"
                print_info "Fix issues and re-run validation: ./scripts/validate_result.sh $dest_path"
                exit 1
            fi
        else
            print_warning "validate_result.sh not found or not executable"
            print_info "Skipping validation"
            echo ""
        fi
    fi
    
    # Aggregate if requested
    if [[ "$MODE" == "aggregate" ]]; then
        print_info "Running aggregation..."
        if [[ -f "$SCRIPT_DIR/aggregate_results.py" ]]; then
            if python3 "$SCRIPT_DIR/aggregate_results.py" --input-dir "$SUBMITTED_DIR" --output-dir "$REPO_ROOT/results/compiled"; then
                print_success "Aggregation completed"
                echo ""
                print_info "Compiled reports are in: results/compiled/"
            else
                print_error "Aggregation failed"
                exit 1
            fi
        else
            print_warning "aggregate_results.py not found"
            print_info "Skipping aggregation"
            echo ""
        fi
    fi
    
    print_success "Processing complete!"
    echo ""
    print_info "Next steps:"
    
    if [[ "$MODE" == "copy" ]]; then
        echo "  1. Validate: ./scripts/validate_result.sh $dest_path"
        echo "  2. Aggregate: python3 scripts/aggregate_results.py --input-dir results/submitted --output-dir results/compiled"
    elif [[ "$MODE" == "validate" ]]; then
        echo "  1. Run aggregation: python3 scripts/aggregate_results.py --input-dir results/submitted --output-dir results/compiled"
        echo "  2. Review compiled reports in: results/compiled/"
    else
        echo "  1. Review compiled reports in: results/compiled/"
        echo "  2. Commit changes to git (if desired)"
    fi
    
    echo ""
}

# Run main
main

