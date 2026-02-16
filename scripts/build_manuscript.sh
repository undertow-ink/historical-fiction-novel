#!/usr/bin/env bash
#
# build_manuscript.sh - Build EPUB, PDF, and manuscript-format outputs from markdown scenes.
#
# Collects all scene .md files in order (by part/chapter/scene numbering),
# assembles them into a single manuscript, and uses pandoc to generate:
#   - EPUB with table of contents, cover image, and custom CSS
#   - Print-ready PDF (6x9 trim size, via pdflatex)
#   - Manuscript format PDF (12pt Courier, double-spaced)
#
# Usage:
#   ./scripts/build_manuscript.sh <command> <book_path>
#
#   Commands:
#     epub        - Generate EPUB file
#     pdf         - Generate print-ready PDF (6x9 trim)
#     manuscript  - Generate manuscript-format PDF (Courier, double-spaced)
#     all         - Generate all formats
#
# Examples:
#   ./scripts/build_manuscript.sh epub series/tides-of-war/book-1/
#   ./scripts/build_manuscript.sh all series/tides-of-war/book-1/
#
# Requirements:
#   - pandoc (>= 2.0)
#   - pdflatex (for PDF output; usually from TeX Live or MacTeX)
#
# Scene files are expected at:
#   <book_path>/manuscript/part-N/chapter-NN/scene-NN.md
#
# Optional files:
#   <book_path>/cover.jpg or cover.png   - Cover image for EPUB
#   <repo_root>/style/epub.css           - Custom CSS for EPUB
#
# Output goes to:
#   <book_path>/build/
#

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Defaults
EPUB_CSS="${REPO_ROOT}/style/epub.css"
PRINT_TRIM_WIDTH="6in"
PRINT_TRIM_HEIGHT="9in"
PRINT_MARGIN_TOP="0.8in"
PRINT_MARGIN_BOTTOM="0.8in"
PRINT_MARGIN_LEFT="0.75in"
PRINT_MARGIN_RIGHT="0.75in"

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

usage() {
    cat <<'USAGE'
Usage: build_manuscript.sh <command> <book_path>

Commands:
  epub        Generate EPUB with TOC and cover image
  pdf         Generate print-ready PDF (6x9 trim, pdflatex)
  manuscript  Generate manuscript-format PDF (12pt Courier, double-spaced)
  all         Generate all formats

Arguments:
  book_path   Path to the book directory (e.g. series/tides-of-war/book-1/)

Examples:
  ./scripts/build_manuscript.sh epub series/tides-of-war/book-1/
  ./scripts/build_manuscript.sh all series/tides-of-war/book-1/
USAGE
    exit 1
}

log_info() {
    echo "[INFO] $*"
}

log_error() {
    echo "[ERROR] $*" >&2
}

log_success() {
    echo "[OK]   $*"
}

check_dependency() {
    local cmd="$1"
    if ! command -v "$cmd" &>/dev/null; then
        log_error "$cmd is required but not found. Please install it."
        return 1
    fi
}

# ---------------------------------------------------------------------------
# Collect and assemble scene files
# ---------------------------------------------------------------------------

collect_scenes() {
    # Collect all scene .md files in numerical order.
    # Outputs file paths, one per line, sorted by part/chapter/scene number.
    local manuscript_dir="$1"

    if [[ ! -d "$manuscript_dir" ]]; then
        log_error "Manuscript directory not found: $manuscript_dir"
        exit 1
    fi

    # Find all scene files and sort them numerically by part, chapter, scene
    find "$manuscript_dir" -name "scene-*.md" -type f | \
        sed 's|.*/part-\([0-9]*\)/chapter-\([0-9]*\)/scene-\([0-9]*\)\.md|\1 \2 \3 &|' | \
        sort -n -k1 -k2 -k3 | \
        awk '{print $4}'
}

assemble_manuscript() {
    # Assemble all scene files into a single markdown file.
    # Adds Part and Chapter headers, converts scene breaks (---) to ***.
    local manuscript_dir="$1"
    local output_file="$2"
    local current_part=""
    local current_chapter=""

    : > "$output_file"

    # Extract book title from outline if available
    local book_dir
    book_dir="$(dirname "$manuscript_dir")"
    local outline="${book_dir}/outline.md"
    local book_title=""

    if [[ -f "$outline" ]]; then
        # Try to get title from YAML front matter
        book_title=$(sed -n '/^---$/,/^---$/{ /^title:/{ s/^title:\s*//; s/^["'\'']\(.*\)["'\'']\s*$/\1/; p; } }' "$outline" | head -1)
        # Fall back to first H1 header
        if [[ -z "$book_title" ]]; then
            book_title=$(grep -m1 '^# ' "$outline" | sed 's/^# //' || true)
        fi
    fi

    if [[ -n "$book_title" ]]; then
        echo "---" >> "$output_file"
        echo "title: \"${book_title}\"" >> "$output_file"
        echo "---" >> "$output_file"
        echo "" >> "$output_file"
    fi

    collect_scenes "$manuscript_dir" | while IFS= read -r scene_file; do
        # Extract part/chapter/scene numbers from path
        local part chapter scene
        part=$(echo "$scene_file" | grep -o 'part-[0-9]*' | grep -o '[0-9]*')
        chapter=$(echo "$scene_file" | grep -o 'chapter-[0-9]*' | grep -o '[0-9]*')
        scene=$(echo "$scene_file" | grep -o 'scene-[0-9]*' | grep -o '[0-9]*')

        # Remove leading zeros for display
        part=$((10#$part))
        chapter=$((10#$chapter))
        scene=$((10#$scene))

        # Add Part header if new part
        if [[ "$part" != "$current_part" ]]; then
            current_part="$part"
            current_chapter=""
            echo "" >> "$output_file"
            echo "# Part ${part}" >> "$output_file"
            echo "" >> "$output_file"
        fi

        # Add Chapter header if new chapter
        if [[ "$chapter" != "$current_chapter" ]]; then
            current_chapter="$chapter"
            echo "" >> "$output_file"
            echo "## Chapter ${chapter}" >> "$output_file"
            echo "" >> "$output_file"
        fi

        # Read scene content, strip YAML front matter
        local content
        content=$(cat "$scene_file")

        # Strip YAML front matter (--- ... ---)
        if echo "$content" | head -1 | grep -q '^---$'; then
            content=$(echo "$content" | sed '1,/^---$/{ /^---$/!d; }' | sed '1d')
        fi

        # Strip any markdown headers from scene files (they're structural, not content)
        content=$(echo "$content" | sed '/^#\{1,4\} /d')

        # Add scene break before non-first scenes in a chapter
        if [[ "$scene" -gt 1 ]]; then
            echo "" >> "$output_file"
            echo "<center>* * *</center>" >> "$output_file"
            echo "" >> "$output_file"
        fi

        # Convert horizontal rules (---) within scene content to centered asterisks
        content=$(echo "$content" | sed 's/^---$/<center>* * *<\/center>/')
        content=$(echo "$content" | sed 's/^\*\*\*$/<center>* * *<\/center>/')

        echo "$content" >> "$output_file"
        echo "" >> "$output_file"

    done

    log_info "Assembled manuscript: $(wc -w < "$output_file" | tr -d ' ') words"
}

# ---------------------------------------------------------------------------
# Build targets
# ---------------------------------------------------------------------------

build_epub() {
    local book_dir="$1"
    local build_dir="$2"
    local assembled="$3"

    check_dependency pandoc || return 1

    local epub_file="${build_dir}/manuscript.epub"
    local pandoc_args=(
        "$assembled"
        -o "$epub_file"
        --toc
        --toc-depth=2
        -f markdown
        -t epub3
        --metadata-file="$assembled"  # for title from front matter
    )

    # Add cover image if available
    local cover=""
    for ext in jpg jpeg png; do
        if [[ -f "${book_dir}/cover.${ext}" ]]; then
            cover="${book_dir}/cover.${ext}"
            break
        fi
    done
    if [[ -n "$cover" ]]; then
        pandoc_args+=(--epub-cover-image="$cover")
        log_info "Using cover image: $cover"
    fi

    # Add custom CSS if available
    if [[ -f "$EPUB_CSS" ]]; then
        pandoc_args+=(--css="$EPUB_CSS")
        log_info "Using custom CSS: $EPUB_CSS"
    fi

    log_info "Building EPUB..."
    pandoc "${pandoc_args[@]}" 2>/dev/null || {
        # Retry without metadata-file flag (in case front matter causes issues)
        pandoc "$assembled" -o "$epub_file" --toc --toc-depth=2 -f markdown -t epub3 \
            ${cover:+--epub-cover-image="$cover"} \
            ${EPUB_CSS:+--css="$EPUB_CSS"} 2>/dev/null || {
            log_error "EPUB build failed. Check pandoc output for details."
            return 1
        }
    }

    log_success "EPUB: $epub_file ($(du -h "$epub_file" | cut -f1 | tr -d ' '))"
}

build_pdf() {
    local book_dir="$1"
    local build_dir="$2"
    local assembled="$3"

    check_dependency pandoc || return 1
    check_dependency pdflatex || {
        log_error "pdflatex is required for PDF output. Install TeX Live or MacTeX."
        return 1
    }

    local pdf_file="${build_dir}/print.pdf"

    log_info "Building print-ready PDF (${PRINT_TRIM_WIDTH} x ${PRINT_TRIM_HEIGHT})..."

    pandoc "$assembled" \
        -o "$pdf_file" \
        -f markdown \
        --pdf-engine=pdflatex \
        --toc \
        --toc-depth=2 \
        -V papersize=custom \
        -V geometry:"paperwidth=${PRINT_TRIM_WIDTH},paperheight=${PRINT_TRIM_HEIGHT},margin-top=${PRINT_MARGIN_TOP},margin-bottom=${PRINT_MARGIN_BOTTOM},margin-left=${PRINT_MARGIN_LEFT},margin-right=${PRINT_MARGIN_RIGHT}" \
        -V fontsize=11pt \
        -V mainfont="Palatino" \
        -V linestretch=1.3 \
        -V indent=true \
        -V documentclass=book \
        -V classoption=openany \
        -V header-includes='\usepackage{fancyhdr}\pagestyle{fancy}\fancyhead[LE,RO]{\thepage}\fancyhead[RE,LO]{}' \
        2>/dev/null || {
        # Fallback: try without font specification
        pandoc "$assembled" \
            -o "$pdf_file" \
            -f markdown \
            --pdf-engine=pdflatex \
            --toc \
            --toc-depth=2 \
            -V papersize=custom \
            -V geometry:"paperwidth=${PRINT_TRIM_WIDTH},paperheight=${PRINT_TRIM_HEIGHT},margin-top=${PRINT_MARGIN_TOP},margin-bottom=${PRINT_MARGIN_BOTTOM},margin-left=${PRINT_MARGIN_LEFT},margin-right=${PRINT_MARGIN_RIGHT}" \
            -V fontsize=11pt \
            -V linestretch=1.3 \
            -V indent=true \
            -V documentclass=book \
            -V classoption=openany \
            2>/dev/null || {
            log_error "Print PDF build failed. Check pandoc/pdflatex output for details."
            return 1
        }
    }

    log_success "Print PDF: $pdf_file ($(du -h "$pdf_file" | cut -f1 | tr -d ' '))"
}

build_manuscript_format() {
    local book_dir="$1"
    local build_dir="$2"
    local assembled="$3"

    check_dependency pandoc || return 1
    check_dependency pdflatex || {
        log_error "pdflatex is required for manuscript PDF. Install TeX Live or MacTeX."
        return 1
    }

    local pdf_file="${build_dir}/manuscript.pdf"

    log_info "Building manuscript-format PDF (Courier 12pt, double-spaced)..."

    # Standard manuscript format: 8.5x11, 1-inch margins, Courier 12pt, double-spaced
    pandoc "$assembled" \
        -o "$pdf_file" \
        -f markdown \
        --pdf-engine=pdflatex \
        -V fontsize=12pt \
        -V fontfamily=courier \
        -V linestretch=2.0 \
        -V geometry:"letterpaper,margin=1in" \
        -V indent=true \
        -V documentclass=article \
        -V pagestyle=plain \
        -V header-includes='\usepackage{setspace}\doublespacing\usepackage{courier}' \
        2>/dev/null || {
        # Fallback without specific font package
        pandoc "$assembled" \
            -o "$pdf_file" \
            -f markdown \
            --pdf-engine=pdflatex \
            -V fontsize=12pt \
            -V linestretch=2.0 \
            -V geometry:"letterpaper,margin=1in" \
            -V indent=true \
            -V documentclass=article \
            -V pagestyle=plain \
            2>/dev/null || {
            log_error "Manuscript PDF build failed. Check pandoc/pdflatex output for details."
            return 1
        }
    }

    log_success "Manuscript PDF: $pdf_file ($(du -h "$pdf_file" | cut -f1 | tr -d ' '))"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

main() {
    # Parse arguments
    if [[ $# -lt 2 ]]; then
        usage
    fi

    local command="$1"
    local book_dir="$2"

    # Normalize book_dir to absolute path
    if [[ "$book_dir" != /* ]]; then
        book_dir="$(pwd)/$book_dir"
    fi
    book_dir="$(cd "$book_dir" 2>/dev/null && pwd)" || {
        log_error "Book directory not found: $2"
        exit 1
    }

    local manuscript_dir="${book_dir}/manuscript"
    local build_dir="${book_dir}/build"

    # Validate
    if [[ ! -d "$manuscript_dir" ]]; then
        log_error "Manuscript directory not found: $manuscript_dir"
        exit 1
    fi

    # Check for scene files
    local scene_count
    scene_count=$(find "$manuscript_dir" -name "scene-*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$scene_count" -eq 0 ]]; then
        log_error "No scene files found in $manuscript_dir"
        log_error "Expected pattern: part-N/chapter-NN/scene-NN.md"
        exit 1
    fi
    log_info "Found $scene_count scene files"

    # Create build directory
    mkdir -p "$build_dir"

    # Create temporary assembled manuscript
    local assembled="${build_dir}/_assembled.md"
    assemble_manuscript "$manuscript_dir" "$assembled"

    # Build requested format(s)
    local exit_code=0

    case "$command" in
        epub)
            build_epub "$book_dir" "$build_dir" "$assembled" || exit_code=1
            ;;
        pdf)
            build_pdf "$book_dir" "$build_dir" "$assembled" || exit_code=1
            ;;
        manuscript)
            build_manuscript_format "$book_dir" "$build_dir" "$assembled" || exit_code=1
            ;;
        all)
            build_epub "$book_dir" "$build_dir" "$assembled" || exit_code=1
            build_pdf "$book_dir" "$build_dir" "$assembled" || exit_code=1
            build_manuscript_format "$book_dir" "$build_dir" "$assembled" || exit_code=1
            ;;
        *)
            log_error "Unknown command: $command"
            usage
            ;;
    esac

    # Clean up assembled file unless debugging
    if [[ "${BUILD_DEBUG:-}" != "1" ]]; then
        rm -f "$assembled"
    else
        log_info "Debug mode: assembled manuscript kept at $assembled"
    fi

    if [[ $exit_code -eq 0 ]]; then
        echo ""
        log_success "Build complete. Output in: $build_dir"
    else
        echo ""
        log_error "Build completed with errors."
    fi

    return $exit_code
}

main "$@"
