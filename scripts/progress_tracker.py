#!/usr/bin/env python3
"""
progress_tracker.py - Progress tracking dashboard generator for historical fiction manuscripts.

Reads the outline, manuscript files, and optional grades to generate a comprehensive
progress.md markdown dashboard showing:
  - Overall completion stats (words/target, pages, reading time, chapters complete)
  - Per-part breakdown with status and quality grade
  - Per-chapter table with scene counts, words, status, and grade
  - Per-scene detail rows with individual stats

Usage:
    python3 progress_tracker.py series/{series_name}/{book_name}/

Expects the book directory to contain:
    outline.md       - Expected structure (parts, chapters, scenes)
    manuscript/      - Directory tree of .md scene files
    grades.yaml      - (Optional) Quality grades for chapters/scenes (0-100)

Generates:
    progress.md      - Markdown progress dashboard in the book directory
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich import box

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WORDS_PER_PAGE = 250
READING_WPM = 250
AUDIOBOOK_WPM = 150

STATUS_VALUES = [
    "Not Started",
    "Writing",
    "First Draft",
    "Editing",
    "Revised",
    "Final",
]

GRADE_LABELS = {
    (0, 39): "Needs rewrite",
    (40, 59): "Major issues",
    (60, 74): "Solid draft",
    (75, 84): "Good quality",
    (85, 94): "Publication ready",
    (95, 100): "Exceptional",
}

# Scene file naming pattern
SCENE_FILE_PATTERN = re.compile(
    r"part-(\d+)/chapter-(\d+)/scene-(\d+)\.md$"
)

# Minimum words to consider a scene as "started"
MIN_WORDS_STARTED = 50

# Minimum words to consider a scene as a "first draft"
MIN_WORDS_DRAFT = 200


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SceneOutline:
    """A scene as defined in the outline."""
    part: int
    chapter: int
    scene: int
    title: str = ""
    word_target: int = 0


@dataclass
class SceneProgress:
    """Progress data for a single scene."""
    part: int
    chapter: int
    scene: int
    title: str = ""
    words: int = 0
    word_target: int = 0
    pages: float = 0.0
    status: str = "Not Started"
    grade: Optional[int] = None
    exists: bool = False


@dataclass
class ChapterProgress:
    """Progress data for a chapter."""
    part: int
    chapter: int
    title: str = ""
    scenes: list[SceneProgress] = field(default_factory=list)
    expected_scenes: int = 0
    complete_scenes: int = 0
    total_words: int = 0
    word_target: int = 0
    status: str = "Not Started"
    grade: Optional[int] = None


@dataclass
class PartProgress:
    """Progress data for a part."""
    part: int
    title: str = ""
    chapters: list[ChapterProgress] = field(default_factory=list)
    total_words: int = 0
    word_target: int = 0
    status: str = "Not Started"
    grade: Optional[int] = None


@dataclass
class BookProgress:
    """Top-level progress data for the book."""
    title: str = ""
    parts: list[PartProgress] = field(default_factory=list)
    total_words: int = 0
    word_target: int = 80_000  # default target
    total_chapters: int = 0
    complete_chapters: int = 0
    total_scenes: int = 0
    complete_scenes: int = 0
    overall_status: str = "Not Started"


# ---------------------------------------------------------------------------
# Outline parser
# ---------------------------------------------------------------------------

def parse_outline(outline_path: Path) -> tuple[str, list[SceneOutline], dict[str, str]]:
    """Parse outline.md to extract the expected structure.

    Supports a multi-level markdown outline with headers like:
        # Book Title
        ## Part 1: Title
        ### Chapter 1: Title
        #### Scene 1: Title

    Also looks for YAML front matter with word_target settings.

    Returns:
        (book_title, list_of_scene_outlines, titles_dict)
        titles_dict maps "part-N", "chapter-N-M", etc. to their titles.
    """
    text = outline_path.read_text(encoding="utf-8", errors="replace")
    scenes: list[SceneOutline] = []
    titles: dict[str, str] = {}
    book_title = ""
    word_target = 80_000

    # Check for YAML front matter
    fm_match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if fm_match:
        try:
            meta = yaml.safe_load(fm_match.group(1)) or {}
            word_target = int(meta.get("word_target", word_target))
            book_title = meta.get("title", "")
        except (yaml.YAMLError, ValueError):
            pass

    current_part = 0
    current_chapter = 0
    default_scene_target = 1_200  # ~5 pages per scene default

    for line in text.split("\n"):
        line = line.strip()

        # Book title: # Title
        m = re.match(r"^#\s+(.+)$", line)
        if m and not book_title:
            book_title = m.group(1).strip()
            continue

        # Part: ## Part N: Title
        m = re.match(r"^##\s+(?:Part\s+)?(\d+)[:\s]*(.*)$", line, re.IGNORECASE)
        if m:
            current_part = int(m.group(1))
            part_title = m.group(2).strip().lstrip(":").strip()
            titles[f"part-{current_part}"] = part_title
            continue

        # Chapter: ### Chapter N: Title
        m = re.match(r"^###\s+(?:Chapter\s+)?(\d+)[:\s]*(.*)$", line, re.IGNORECASE)
        if m:
            current_chapter = int(m.group(1))
            ch_title = m.group(2).strip().lstrip(":").strip()
            titles[f"chapter-{current_part}-{current_chapter}"] = ch_title
            continue

        # Scene: #### Scene N: Title  (or - Scene N: Title for list items)
        m = re.match(
            r"^(?:####\s+|[-*]\s+)(?:Scene\s+)?(\d+)[:\s]*(.*)$",
            line, re.IGNORECASE,
        )
        if m and current_part > 0 and current_chapter > 0:
            scene_num = int(m.group(1))
            scene_title = m.group(2).strip().lstrip(":").strip()

            # Check for word target in parentheses like "(~1500 words)"
            wt_match = re.search(r"\(~?(\d+)\s*words?\)", scene_title, re.IGNORECASE)
            scene_target = int(wt_match.group(1)) if wt_match else default_scene_target
            if wt_match:
                scene_title = scene_title[:wt_match.start()].strip().rstrip(",").strip()

            scenes.append(SceneOutline(
                part=current_part,
                chapter=current_chapter,
                scene=scene_num,
                title=scene_title,
                word_target=scene_target,
            ))
            titles[f"scene-{current_part}-{current_chapter}-{scene_num}"] = scene_title

    return book_title, scenes, titles


# ---------------------------------------------------------------------------
# Grades loader
# ---------------------------------------------------------------------------

def load_grades(grades_path: Path) -> dict[str, int]:
    """Load quality grades from grades.yaml.

    Expected format:
        part-1:
          grade: 72
          chapter-1:
            grade: 78
            scene-1: 80
            scene-2: 75
          chapter-2:
            grade: 65

    Returns a flat dictionary mapping keys like:
        "part-1" -> 72
        "chapter-1-1" -> 78
        "scene-1-1-1" -> 80
    """
    grades: dict[str, int] = {}
    if not grades_path.is_file():
        return grades

    try:
        with open(grades_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except yaml.YAMLError:
        return grades

    for part_key, part_data in raw.items():
        # part-N
        m = re.match(r"part-(\d+)", str(part_key))
        if not m:
            continue
        part_num = int(m.group(1))

        if isinstance(part_data, dict):
            if "grade" in part_data:
                grades[f"part-{part_num}"] = int(part_data["grade"])

            for ch_key, ch_data in part_data.items():
                m = re.match(r"chapter-(\d+)", str(ch_key))
                if not m:
                    continue
                ch_num = int(m.group(1))

                if isinstance(ch_data, dict):
                    if "grade" in ch_data:
                        grades[f"chapter-{part_num}-{ch_num}"] = int(ch_data["grade"])

                    for sc_key, sc_val in ch_data.items():
                        m = re.match(r"scene-(\d+)", str(sc_key))
                        if not m:
                            continue
                        sc_num = int(m.group(1))
                        if isinstance(sc_val, int):
                            grades[f"scene-{part_num}-{ch_num}-{sc_num}"] = sc_val
                        elif isinstance(sc_val, dict) and "grade" in sc_val:
                            grades[f"scene-{part_num}-{ch_num}-{sc_num}"] = int(sc_val["grade"])

                elif isinstance(ch_data, int):
                    grades[f"chapter-{part_num}-{ch_num}"] = ch_data

        elif isinstance(part_data, int):
            grades[f"part-{part_num}"] = part_data

    return grades


# ---------------------------------------------------------------------------
# Manuscript scanner
# ---------------------------------------------------------------------------

def count_words(text: str) -> int:
    """Count words in text after stripping front matter and markdown headers."""
    # Strip YAML front matter
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]

    # Remove markdown headers and horizontal rules
    text = re.sub(r"^#+\s+.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[\-\*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    return len(text.split())


def determine_status(words: int, word_target: int, has_grade: bool, grade: Optional[int]) -> str:
    """Determine the status of a scene based on word count and grade."""
    if words == 0:
        return "Not Started"
    if words < MIN_WORDS_STARTED:
        return "Not Started"
    if words < MIN_WORDS_DRAFT:
        return "Writing"

    # If we have a grade, use it to infer editing stage
    if has_grade and grade is not None:
        if grade >= 95:
            return "Final"
        elif grade >= 85:
            return "Revised"
        elif grade >= 60:
            return "Editing"
        else:
            return "First Draft"

    # Without a grade, estimate from word count vs target
    if word_target > 0:
        ratio = words / word_target
        if ratio >= 0.9:
            return "First Draft"
        else:
            return "Writing"

    return "First Draft"


def aggregate_status(statuses: list[str]) -> str:
    """Determine aggregate status from a list of child statuses."""
    if not statuses:
        return "Not Started"

    status_order = {s: i for i, s in enumerate(STATUS_VALUES)}

    if all(s == "Not Started" for s in statuses):
        return "Not Started"
    if all(s == "Final" for s in statuses):
        return "Final"
    if all(s in ("Revised", "Final") for s in statuses):
        return "Revised"
    if all(s in ("Editing", "Revised", "Final") for s in statuses):
        return "Editing"
    if all(status_order.get(s, 0) >= status_order["First Draft"] for s in statuses):
        return "First Draft"

    return "Writing"


def scan_manuscript_for_progress(
    manuscript_dir: Path,
    outline_scenes: list[SceneOutline],
    titles: dict[str, str],
    grades: dict[str, int],
    word_target: int,
) -> BookProgress:
    """Scan manuscript files and build the full progress tree."""
    progress = BookProgress(word_target=word_target)

    # Index outline scenes
    outline_index: dict[tuple[int, int, int], SceneOutline] = {}
    for so in outline_scenes:
        outline_index[(so.part, so.chapter, so.scene)] = so

    # Find all parts/chapters/scenes expected from outline
    expected_parts: dict[int, dict[int, list[int]]] = {}
    for so in outline_scenes:
        expected_parts.setdefault(so.part, {}).setdefault(so.chapter, []).append(so.scene)

    # Also scan the filesystem for scenes that might exist but aren't in outline
    if manuscript_dir.is_dir():
        for fp in sorted(manuscript_dir.rglob("*.md")):
            relative = str(fp.relative_to(manuscript_dir)).replace("\\", "/")
            m = SCENE_FILE_PATTERN.search(relative)
            if m:
                p, c, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
                expected_parts.setdefault(p, {}).setdefault(c, [])
                if s not in expected_parts[p][c]:
                    expected_parts[p][c].append(s)

    # Build progress tree
    for part_num in sorted(expected_parts):
        part_title = titles.get(f"part-{part_num}", "")
        part_prog = PartProgress(
            part=part_num,
            title=part_title,
            grade=grades.get(f"part-{part_num}"),
        )

        for ch_num in sorted(expected_parts[part_num]):
            ch_title = titles.get(f"chapter-{part_num}-{ch_num}", "")
            ch_prog = ChapterProgress(
                part=part_num,
                chapter=ch_num,
                title=ch_title,
                grade=grades.get(f"chapter-{part_num}-{ch_num}"),
            )

            scene_nums = sorted(set(expected_parts[part_num][ch_num]))
            ch_prog.expected_scenes = len(scene_nums)

            for sc_num in scene_nums:
                outline = outline_index.get((part_num, ch_num, sc_num))
                sc_title = (
                    outline.title if outline
                    else titles.get(f"scene-{part_num}-{ch_num}-{sc_num}", "")
                )
                sc_target = outline.word_target if outline else 1_200

                # Check if the file exists and count words
                scene_file = (
                    manuscript_dir
                    / f"part-{part_num}"
                    / f"chapter-{ch_num:02d}"
                    / f"scene-{sc_num:02d}.md"
                )
                # Also try without zero-padding
                if not scene_file.is_file():
                    scene_file = (
                        manuscript_dir
                        / f"part-{part_num}"
                        / f"chapter-{ch_num}"
                        / f"scene-{sc_num}.md"
                    )

                words = 0
                exists = False
                if scene_file.is_file():
                    exists = True
                    text = scene_file.read_text(encoding="utf-8", errors="replace")
                    words = count_words(text)

                sc_grade = grades.get(f"scene-{part_num}-{ch_num}-{sc_num}")
                sc_status = determine_status(
                    words, sc_target, sc_grade is not None, sc_grade
                )

                sc_prog = SceneProgress(
                    part=part_num,
                    chapter=ch_num,
                    scene=sc_num,
                    title=sc_title,
                    words=words,
                    word_target=sc_target,
                    pages=words / WORDS_PER_PAGE if words else 0.0,
                    status=sc_status,
                    grade=sc_grade,
                    exists=exists,
                )
                ch_prog.scenes.append(sc_prog)
                ch_prog.total_words += words
                ch_prog.word_target += sc_target

                if sc_status not in ("Not Started", "Writing"):
                    ch_prog.complete_scenes += 1

            # Chapter aggregate status
            ch_statuses = [s.status for s in ch_prog.scenes]
            ch_prog.status = aggregate_status(ch_statuses)

            # Chapter grade: use explicit grade or average of scene grades
            if ch_prog.grade is None:
                scene_grades = [s.grade for s in ch_prog.scenes if s.grade is not None]
                if scene_grades:
                    ch_prog.grade = round(sum(scene_grades) / len(scene_grades))

            part_prog.chapters.append(ch_prog)
            part_prog.total_words += ch_prog.total_words
            part_prog.word_target += ch_prog.word_target

        # Part aggregate status
        ch_statuses_for_part = [c.status for c in part_prog.chapters]
        part_prog.status = aggregate_status(ch_statuses_for_part)

        # Part grade: use explicit grade or average of chapter grades
        if part_prog.grade is None:
            ch_grades = [c.grade for c in part_prog.chapters if c.grade is not None]
            if ch_grades:
                part_prog.grade = round(sum(ch_grades) / len(ch_grades))

        progress.parts.append(part_prog)

    # Top-level aggregates
    for pt in progress.parts:
        progress.total_words += pt.total_words
        for ch in pt.chapters:
            progress.total_chapters += 1
            progress.total_scenes += ch.expected_scenes
            progress.complete_scenes += ch.complete_scenes
            if ch.status not in ("Not Started", "Writing"):
                progress.complete_chapters += 1

    all_statuses = [pt.status for pt in progress.parts]
    progress.overall_status = aggregate_status(all_statuses) if all_statuses else "Not Started"

    return progress


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def format_time(minutes: float) -> str:
    """Format minutes as 'Xh Ym'."""
    if minutes < 1:
        return "< 1m"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def format_number(n: int) -> str:
    """Format an integer with comma separators."""
    return f"{n:,}"


def grade_str(grade: Optional[int]) -> str:
    """Format a grade value for display."""
    if grade is None:
        return "--"
    return str(grade)


def grade_label(grade: Optional[int]) -> str:
    """Get descriptive label for a grade."""
    if grade is None:
        return ""
    for (lo, hi), label in GRADE_LABELS.items():
        if lo <= grade <= hi:
            return label
    return ""


def generate_progress_md(progress: BookProgress, title: str) -> str:
    """Generate the complete progress.md markdown content."""
    lines: list[str] = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines.append(f"# Progress: {title}")
    lines.append("")
    lines.append(f"Last updated: {now}")
    lines.append("")

    # Overall stats
    lines.append("## Overall")
    lines.append("")
    lines.append(f"- **Status:** {progress.overall_status}")

    pct = (progress.total_words / progress.word_target * 100) if progress.word_target else 0
    lines.append(
        f"- **Words:** {format_number(progress.total_words)} / "
        f"{format_number(progress.word_target)} target ({pct:.1f}%)"
    )

    pages = progress.total_words / WORDS_PER_PAGE
    est_pages = progress.word_target / WORDS_PER_PAGE
    lines.append(f"- **Pages:** {pages:.0f} / {est_pages:.0f} estimated")

    reading = progress.total_words / READING_WPM
    lines.append(f"- **Reading time:** {format_time(reading)} estimated")

    audiobook = progress.total_words / AUDIOBOOK_WPM
    lines.append(f"- **Audiobook time:** {format_time(audiobook)} estimated")

    lines.append(
        f"- **Chapters:** {progress.complete_chapters} / "
        f"{progress.total_chapters} complete"
    )
    lines.append(
        f"- **Scenes:** {progress.complete_scenes} / "
        f"{progress.total_scenes} complete"
    )
    lines.append("")

    # Per-part breakdown
    for pt in progress.parts:
        pt_title = pt.title if pt.title else f"Part {pt.part}"
        lines.append(f"## Part {pt.part}: {pt_title}")
        lines.append("")

        grade_display = grade_str(pt.grade)
        grade_lbl = grade_label(pt.grade)
        grade_suffix = f" ({grade_lbl})" if grade_lbl else ""
        lines.append(f"**Status:** {pt.status} | **Grade:** {grade_display}/100{grade_suffix}")

        pt_pct = (pt.total_words / pt.word_target * 100) if pt.word_target else 0
        lines.append(
            f"**Words:** {format_number(pt.total_words)} / "
            f"{format_number(pt.word_target)} ({pt_pct:.1f}%)"
        )
        lines.append("")

        # Chapter table
        lines.append("| Chapter | Scenes | Words | Status | Grade |")
        lines.append("|---------|--------|-------|--------|-------|")

        for ch in pt.chapters:
            ch_title = ch.title if ch.title else f"Chapter {ch.chapter}"
            ch_label = f"Ch {ch.chapter}: {ch_title}"
            scenes_str = f"{ch.complete_scenes}/{ch.expected_scenes}"
            words_str = format_number(ch.total_words)
            ch_grade = grade_str(ch.grade)

            lines.append(
                f"| {ch_label} | {scenes_str} | {words_str} | {ch.status} | {ch_grade} |"
            )

        lines.append("")

        # Per-chapter scene detail
        for ch in pt.chapters:
            ch_title = ch.title if ch.title else f"Chapter {ch.chapter}"
            lines.append(f"### Chapter {ch.chapter}: {ch_title}")
            lines.append("")
            lines.append("| Scene | Pages | Words | Status | Grade |")
            lines.append("|-------|-------|-------|--------|-------|")

            for i, sc in enumerate(ch.scenes):
                sc_title = sc.title if sc.title else f"Scene {sc.scene}"
                sc_label = f"{sc.scene}: {sc_title}"
                pages_str = f"{sc.pages:.1f}"
                words_str = format_number(sc.words)
                sc_grade = grade_str(sc.grade)

                lines.append(
                    f"| {sc_label} | {pages_str} | {words_str} | {sc.status} | {sc_grade} |"
                )

                # Scene break marker between scenes (not after the last)
                if i < len(ch.scenes) - 1:
                    lines.append("|   ---   |       |       |        |       |")

            lines.append("")

        lines.append("---")
        lines.append("")

    # Grade legend
    lines.append("## Grade Legend")
    lines.append("")
    lines.append("| Range | Description |")
    lines.append("|-------|-------------|")
    for (lo, hi), label in GRADE_LABELS.items():
        lines.append(f"| {lo}-{hi} | {label} |")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point for the progress tracker."""
    parser = argparse.ArgumentParser(
        description="Generate a progress.md dashboard for a book.",
        epilog="Example: python3 progress_tracker.py series/tides-of-war/book-1/",
    )
    parser.add_argument(
        "book_dir",
        type=str,
        help="Path to the book directory containing outline.md and manuscript/.",
    )
    parser.add_argument(
        "--target",
        type=int,
        default=None,
        help="Override word count target (default: from outline.md front matter or 80,000).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Override output path for progress.md (default: <book_dir>/progress.md).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print progress.md to stdout instead of writing to file.",
    )
    args = parser.parse_args()

    book_path = Path(args.book_dir).resolve()

    if not book_path.is_dir():
        print(f"ERROR: Book directory not found: {book_path}", file=sys.stderr)
        sys.exit(1)

    outline_path = book_path / "outline.md"
    manuscript_dir = book_path / "manuscript"
    grades_path = book_path / "grades.yaml"

    # Parse outline
    if outline_path.is_file():
        book_title, outline_scenes, titles = parse_outline(outline_path)
    else:
        print(
            f"WARNING: outline.md not found at {outline_path}. "
            f"Building progress from manuscript files only.",
            file=sys.stderr,
        )
        book_title = book_path.name
        outline_scenes = []
        titles = {}

    # Load grades
    grades = load_grades(grades_path)

    # Determine word target
    word_target = args.target if args.target else 80_000
    # Try to get from outline front matter (already parsed if outline exists)
    if args.target is None and outline_path.is_file():
        text = outline_path.read_text(encoding="utf-8", errors="replace")
        fm_match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        if fm_match:
            try:
                meta = yaml.safe_load(fm_match.group(1)) or {}
                word_target = int(meta.get("word_target", word_target))
            except (yaml.YAMLError, ValueError):
                pass

    if not book_title:
        book_title = book_path.name

    # Scan and build progress
    if manuscript_dir.is_dir():
        progress = scan_manuscript_for_progress(
            manuscript_dir, outline_scenes, titles, grades, word_target
        )
    else:
        print(
            f"WARNING: manuscript/ directory not found at {manuscript_dir}.",
            file=sys.stderr,
        )
        progress = BookProgress(
            title=book_title,
            word_target=word_target,
        )
        # Still build structure from outline
        progress = scan_manuscript_for_progress(
            manuscript_dir, outline_scenes, titles, grades, word_target
        )

    progress.title = book_title

    # Generate markdown
    md_content = generate_progress_md(progress, book_title)

    # Output
    if args.dry_run:
        print(md_content)
    else:
        output_path = Path(args.output) if args.output else book_path / "progress.md"
        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(md_content, encoding="utf-8")

        if RICH_AVAILABLE:
            console = Console()
            console.print(Panel(
                f"Progress dashboard written to:\n[cyan]{output_path}[/cyan]\n\n"
                f"[bold]Words:[/bold] {format_number(progress.total_words)} / "
                f"{format_number(progress.word_target)}\n"
                f"[bold]Chapters:[/bold] {progress.complete_chapters} / "
                f"{progress.total_chapters}\n"
                f"[bold]Status:[/bold] {progress.overall_status}",
                title="Progress Tracker",
                box=box.DOUBLE,
            ))
        else:
            print(f"Progress dashboard written to: {output_path}")
            print(
                f"Words: {format_number(progress.total_words)} / "
                f"{format_number(progress.word_target)}"
            )
            print(
                f"Chapters: {progress.complete_chapters} / "
                f"{progress.total_chapters}"
            )
            print(f"Status: {progress.overall_status}")


if __name__ == "__main__":
    main()
