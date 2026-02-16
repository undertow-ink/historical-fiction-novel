#!/usr/bin/env python3
"""
manuscript_stats.py - Manuscript statistics tool for historical fiction manuscripts.

Calculates comprehensive statistics across all manuscript .md files:
  - Word, sentence, and paragraph counts
  - Page estimates (trade paperback @ 250 wpp, mass market @ 300 wpp)
  - Reading time (fiction @ 250 WPM, audiobook @ 150 WPM)
  - Average sentence length and sentence length distribution
  - Dialogue ratio (percentage of text in quotation marks)
  - Length categorization (short story, novelette, novella, novel, epic)
  - Breakdown by scene, chapter, and part

Usage:
    python3 manuscript_stats.py series/{series_name}/{book_name}/manuscript/

Outputs:
    Human-readable table to stdout (with rich formatting if available)
    JSON to stdout with --json flag, or to a file with --json-output <path>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WORDS_PER_PAGE_TRADE = 250
WORDS_PER_PAGE_MASS = 300
READING_WPM_FICTION = 250
READING_WPM_AUDIOBOOK = 150

# Length categories per SFWA / industry standard thresholds
LENGTH_CATEGORIES = [
    (0, "Empty"),
    (1, "Flash fiction"),
    (1_000, "Flash fiction"),
    (7_500, "Short story"),
    (17_500, "Novelette"),
    (40_000, "Novella"),
    (100_000, "Novel"),
    (120_000, "Long novel"),
    (200_000, "Epic"),
]

# Pattern to identify scene-file naming convention
SCENE_FILE_PATTERN = re.compile(
    r"part-(\d+)/chapter-(\d+)/scene-(\d+)\.md$"
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TextStats:
    """Statistics for a block of text."""
    words: int = 0
    sentences: int = 0
    paragraphs: int = 0
    dialogue_words: int = 0
    characters_no_spaces: int = 0

    @property
    def pages_trade(self) -> float:
        return self.words / WORDS_PER_PAGE_TRADE if self.words else 0.0

    @property
    def pages_mass(self) -> float:
        return self.words / WORDS_PER_PAGE_MASS if self.words else 0.0

    @property
    def reading_time_minutes(self) -> float:
        return self.words / READING_WPM_FICTION if self.words else 0.0

    @property
    def audiobook_time_minutes(self) -> float:
        return self.words / READING_WPM_AUDIOBOOK if self.words else 0.0

    @property
    def avg_sentence_length(self) -> float:
        return self.words / self.sentences if self.sentences else 0.0

    @property
    def dialogue_ratio(self) -> float:
        return self.dialogue_words / self.words if self.words else 0.0

    @property
    def length_category(self) -> str:
        category = "Empty"
        for threshold, cat in LENGTH_CATEGORIES:
            if self.words >= threshold:
                category = cat
        return category

    def to_dict(self) -> dict:
        """Serialize to a dictionary including computed properties."""
        return {
            "words": self.words,
            "sentences": self.sentences,
            "paragraphs": self.paragraphs,
            "dialogue_words": self.dialogue_words,
            "characters_no_spaces": self.characters_no_spaces,
            "pages_trade_paperback": round(self.pages_trade, 1),
            "pages_mass_market": round(self.pages_mass, 1),
            "reading_time_minutes": round(self.reading_time_minutes, 1),
            "audiobook_time_minutes": round(self.audiobook_time_minutes, 1),
            "avg_sentence_length": round(self.avg_sentence_length, 1),
            "dialogue_ratio": round(self.dialogue_ratio, 3),
            "length_category": self.length_category,
        }


@dataclass
class SceneStats:
    """Statistics for a single scene file."""
    part: int
    chapter: int
    scene: int
    file_path: str
    stats: TextStats = field(default_factory=TextStats)


@dataclass
class ChapterStats:
    """Aggregated statistics for a chapter."""
    part: int
    chapter: int
    scenes: list[SceneStats] = field(default_factory=list)
    stats: TextStats = field(default_factory=TextStats)


@dataclass
class PartStats:
    """Aggregated statistics for a part."""
    part: int
    chapters: list[ChapterStats] = field(default_factory=list)
    stats: TextStats = field(default_factory=TextStats)


@dataclass
class ManuscriptStats:
    """Top-level manuscript statistics."""
    manuscript_dir: str
    parts: list[PartStats] = field(default_factory=list)
    total: TextStats = field(default_factory=TextStats)


# ---------------------------------------------------------------------------
# Text analysis
# ---------------------------------------------------------------------------

def strip_front_matter(text: str) -> str:
    """Remove YAML front matter from markdown text."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:].strip()
    return text


def analyze_text(text: str) -> TextStats:
    """Compute word, sentence, paragraph, and dialogue statistics for text."""
    # Strip front matter for word counting
    clean = strip_front_matter(text)

    # Remove markdown headers for cleaner prose analysis
    prose = re.sub(r"^#+\s+.*$", "", clean, flags=re.MULTILINE)
    # Remove horizontal rules
    prose = re.sub(r"^[\-\*_]{3,}\s*$", "", prose, flags=re.MULTILINE)

    stats = TextStats()

    # Paragraphs: non-empty lines separated by blank lines
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", prose) if p.strip()]
    stats.paragraphs = len(paragraphs)

    # Words: split on whitespace
    words = prose.split()
    stats.words = len(words)

    # Characters (no spaces)
    stats.characters_no_spaces = sum(len(w) for w in words)

    # Sentences: split on sentence-ending punctuation followed by space or end
    # This handles abbreviations imperfectly but is a reasonable heuristic
    sentences = re.split(r'[.!?]+(?:\s+|"|\'|\u201D|\u2019|$)', prose)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 1]
    stats.sentences = max(len(sentences), 1) if stats.words > 0 else 0

    # Dialogue: count words inside quotation marks (straight and curly)
    # Matches text between pairs of quotes
    dialogue_matches = re.findall(
        r'[\u201C"](.*?)[\u201D"]',
        prose,
        re.DOTALL,
    )
    dialogue_text = " ".join(dialogue_matches)
    stats.dialogue_words = len(dialogue_text.split()) if dialogue_text.strip() else 0

    return stats


def merge_stats(target: TextStats, source: TextStats) -> None:
    """Add source stats into target (in place)."""
    target.words += source.words
    target.sentences += source.sentences
    target.paragraphs += source.paragraphs
    target.dialogue_words += source.dialogue_words
    target.characters_no_spaces += source.characters_no_spaces


# ---------------------------------------------------------------------------
# Manuscript scanning
# ---------------------------------------------------------------------------

def scan_manuscript(manuscript_dir: Path) -> ManuscriptStats:
    """Scan all .md files in the manuscript directory and compute stats."""
    result = ManuscriptStats(manuscript_dir=str(manuscript_dir))

    md_files = sorted(manuscript_dir.rglob("*.md"))

    # Parse each scene file
    scene_list: list[SceneStats] = []
    for fp in md_files:
        relative = str(fp.relative_to(manuscript_dir)).replace("\\", "/")
        m = SCENE_FILE_PATTERN.search(relative)
        if not m:
            continue

        text = fp.read_text(encoding="utf-8", errors="replace")
        stats = analyze_text(text)

        scene = SceneStats(
            part=int(m.group(1)),
            chapter=int(m.group(2)),
            scene=int(m.group(3)),
            file_path=relative,
            stats=stats,
        )
        scene_list.append(scene)

    scene_list.sort(key=lambda s: (s.part, s.chapter, s.scene))

    # Aggregate by chapter and part
    chapters_map: dict[tuple[int, int], ChapterStats] = {}
    parts_map: dict[int, PartStats] = {}

    for scene in scene_list:
        # Chapter
        ch_key = (scene.part, scene.chapter)
        if ch_key not in chapters_map:
            chapters_map[ch_key] = ChapterStats(
                part=scene.part, chapter=scene.chapter
            )
        ch = chapters_map[ch_key]
        ch.scenes.append(scene)
        merge_stats(ch.stats, scene.stats)

        # Part
        if scene.part not in parts_map:
            parts_map[scene.part] = PartStats(part=scene.part)
        pt = parts_map[scene.part]
        merge_stats(pt.stats, scene.stats)

        # Total
        merge_stats(result.total, scene.stats)

    # Wire chapters into parts
    for ch_key in sorted(chapters_map):
        ch = chapters_map[ch_key]
        pt = parts_map[ch.part]
        pt.chapters.append(ch)

    result.parts = [parts_map[k] for k in sorted(parts_map)]

    return result


# ---------------------------------------------------------------------------
# Formatting helpers
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


def format_pct(ratio: float) -> str:
    """Format a ratio as a percentage string."""
    return f"{ratio * 100:.1f}%"


# ---------------------------------------------------------------------------
# Output: Human-readable
# ---------------------------------------------------------------------------

def print_plain(ms: ManuscriptStats) -> None:
    """Print statistics as plain text tables."""
    t = ms.total
    print(f"\n{'=' * 72}")
    print(f"  MANUSCRIPT STATISTICS")
    print(f"  Source: {ms.manuscript_dir}")
    print(f"{'=' * 72}\n")

    print(f"  Total words:          {format_number(t.words)}")
    print(f"  Total sentences:      {format_number(t.sentences)}")
    print(f"  Total paragraphs:     {format_number(t.paragraphs)}")
    print(f"  Avg sentence length:  {t.avg_sentence_length:.1f} words")
    print(f"  Dialogue ratio:       {format_pct(t.dialogue_ratio)}")
    print(f"  Length category:      {t.length_category}")
    print()
    print(f"  Trade paperback:      {t.pages_trade:.0f} pages (@ {WORDS_PER_PAGE_TRADE} w/p)")
    print(f"  Mass market:          {t.pages_mass:.0f} pages (@ {WORDS_PER_PAGE_MASS} w/p)")
    print(f"  Reading time:         {format_time(t.reading_time_minutes)} (@ {READING_WPM_FICTION} WPM)")
    print(f"  Audiobook time:       {format_time(t.audiobook_time_minutes)} (@ {READING_WPM_AUDIOBOOK} WPM)")
    print()

    # Per-part breakdown
    for pt in ms.parts:
        print(f"\n--- Part {pt.part} ---")
        print(f"  Words: {format_number(pt.stats.words)}  |  "
              f"Pages: {pt.stats.pages_trade:.0f}  |  "
              f"Sentences: {format_number(pt.stats.sentences)}  |  "
              f"Dialogue: {format_pct(pt.stats.dialogue_ratio)}")

        # Chapter table header
        print(f"\n  {'Chapter':<12} {'Scenes':<8} {'Words':<10} {'Pages':<8} "
              f"{'Avg Sent':<10} {'Dialogue':<10}")
        print(f"  {'-' * 12} {'-' * 8} {'-' * 10} {'-' * 8} {'-' * 10} {'-' * 10}")

        for ch in pt.chapters:
            print(
                f"  Ch {ch.chapter:<8} {len(ch.scenes):<8} "
                f"{format_number(ch.stats.words):<10} "
                f"{ch.stats.pages_trade:<8.0f} "
                f"{ch.stats.avg_sentence_length:<10.1f} "
                f"{format_pct(ch.stats.dialogue_ratio):<10}"
            )

            # Scene detail
            for sc in ch.scenes:
                print(
                    f"    Sc {sc.scene:<6} {'':<8} "
                    f"{format_number(sc.stats.words):<10} "
                    f"{sc.stats.pages_trade:<8.1f} "
                    f"{sc.stats.avg_sentence_length:<10.1f} "
                    f"{format_pct(sc.stats.dialogue_ratio):<10}"
                )

    print(f"\n{'=' * 72}")


def print_rich(ms: ManuscriptStats) -> None:
    """Print statistics using rich tables and panels."""
    console = Console()
    t = ms.total

    # Summary panel
    summary = (
        f"[bold]Total words:[/bold]          {format_number(t.words)}\n"
        f"[bold]Total sentences:[/bold]      {format_number(t.sentences)}\n"
        f"[bold]Total paragraphs:[/bold]     {format_number(t.paragraphs)}\n"
        f"[bold]Avg sentence length:[/bold]  {t.avg_sentence_length:.1f} words\n"
        f"[bold]Dialogue ratio:[/bold]       {format_pct(t.dialogue_ratio)}\n"
        f"[bold]Length category:[/bold]      [cyan]{t.length_category}[/cyan]\n"
        f"\n"
        f"[bold]Trade paperback:[/bold]      {t.pages_trade:.0f} pages (@ {WORDS_PER_PAGE_TRADE} w/p)\n"
        f"[bold]Mass market:[/bold]          {t.pages_mass:.0f} pages (@ {WORDS_PER_PAGE_MASS} w/p)\n"
        f"[bold]Reading time:[/bold]         {format_time(t.reading_time_minutes)} (@ {READING_WPM_FICTION} WPM)\n"
        f"[bold]Audiobook time:[/bold]       {format_time(t.audiobook_time_minutes)} (@ {READING_WPM_AUDIOBOOK} WPM)"
    )
    console.print(Panel(
        summary,
        title=f"Manuscript Statistics - {ms.manuscript_dir}",
        box=box.DOUBLE,
    ))

    # Per-part tables
    for pt in ms.parts:
        table = Table(
            title=f"Part {pt.part} - {format_number(pt.stats.words)} words",
            box=box.ROUNDED,
            show_lines=True,
        )
        table.add_column("Chapter", style="bold", width=10)
        table.add_column("Scene", width=8)
        table.add_column("Words", justify="right", width=10)
        table.add_column("Pages", justify="right", width=8)
        table.add_column("Sentences", justify="right", width=10)
        table.add_column("Avg Sent Len", justify="right", width=12)
        table.add_column("Dialogue", justify="right", width=10)

        for ch in pt.chapters:
            # Chapter summary row
            table.add_row(
                f"Ch {ch.chapter}",
                f"{len(ch.scenes)} scenes",
                format_number(ch.stats.words),
                f"{ch.stats.pages_trade:.0f}",
                format_number(ch.stats.sentences),
                f"{ch.stats.avg_sentence_length:.1f}",
                format_pct(ch.stats.dialogue_ratio),
                style="bold",
            )
            # Scene detail rows
            for sc in ch.scenes:
                table.add_row(
                    "",
                    f"Sc {sc.scene}",
                    format_number(sc.stats.words),
                    f"{sc.stats.pages_trade:.1f}",
                    format_number(sc.stats.sentences),
                    f"{sc.stats.avg_sentence_length:.1f}",
                    format_pct(sc.stats.dialogue_ratio),
                    style="dim",
                )

        console.print(table)
        console.print()


# ---------------------------------------------------------------------------
# Output: JSON
# ---------------------------------------------------------------------------

def build_json(ms: ManuscriptStats) -> dict:
    """Build a JSON-serializable dictionary of all statistics."""
    result: dict = {
        "manuscript_dir": ms.manuscript_dir,
        "total": ms.total.to_dict(),
        "total_reading_time": format_time(ms.total.reading_time_minutes),
        "total_audiobook_time": format_time(ms.total.audiobook_time_minutes),
        "parts": [],
    }

    for pt in ms.parts:
        part_data: dict = {
            "part": pt.part,
            "stats": pt.stats.to_dict(),
            "chapters": [],
        }

        for ch in pt.chapters:
            ch_data: dict = {
                "part": ch.part,
                "chapter": ch.chapter,
                "scene_count": len(ch.scenes),
                "stats": ch.stats.to_dict(),
                "scenes": [],
            }

            for sc in ch.scenes:
                sc_data = {
                    "part": sc.part,
                    "chapter": sc.chapter,
                    "scene": sc.scene,
                    "file": sc.file_path,
                    "stats": sc.stats.to_dict(),
                }
                ch_data["scenes"].append(sc_data)

            part_data["chapters"].append(ch_data)

        result["parts"].append(part_data)

    return result


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point for manuscript statistics."""
    parser = argparse.ArgumentParser(
        description="Calculate manuscript statistics from markdown scene files.",
        epilog="Example: python3 manuscript_stats.py series/tides-of-war/book-1/manuscript/",
    )
    parser.add_argument(
        "manuscript_dir",
        type=str,
        help="Path to the manuscript directory containing part-N/chapter-NN/scene-NN.md files.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output JSON to stdout instead of human-readable tables.",
    )
    parser.add_argument(
        "--json-file",
        type=str,
        default=None,
        help="Write JSON output to the specified file path.",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Force plain-text output (no rich formatting).",
    )
    args = parser.parse_args()

    manuscript_path = Path(args.manuscript_dir).resolve()

    if not manuscript_path.is_dir():
        print(f"ERROR: Manuscript directory not found: {manuscript_path}", file=sys.stderr)
        sys.exit(1)

    # Scan
    ms = scan_manuscript(manuscript_path)

    if ms.total.words == 0:
        print(
            f"WARNING: No words found in manuscript files at {manuscript_path}",
            file=sys.stderr,
        )
        print("Expected file pattern: part-N/chapter-NN/scene-NN.md")

    # JSON output
    if args.json_output or args.json_file:
        json_data = build_json(ms)
        json_str = json.dumps(json_data, indent=2)

        if args.json_file:
            out_path = Path(args.json_file).resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json_str, encoding="utf-8")
            print(f"JSON written to: {out_path}")
        else:
            print(json_str)
        return

    # Human-readable output
    use_rich = RICH_AVAILABLE and not args.plain
    if use_rich:
        print_rich(ms)
    else:
        print_plain(ms)


if __name__ == "__main__":
    main()
