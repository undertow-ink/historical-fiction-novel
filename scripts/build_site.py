#!/usr/bin/env python3
"""Build a static reading site from the manuscript files."""

import os
import re
from pathlib import Path
from html import escape

REPO_ROOT = Path(__file__).resolve().parent.parent
MANUSCRIPT = REPO_ROOT / "series" / "the-burning-glass" / "the-feast-of-ashes" / "manuscript"
PROGRESS = REPO_ROOT / "series" / "the-burning-glass" / "the-feast-of-ashes" / "progress.md"
OUTPUT = REPO_ROOT / "_site"

BOOK_TITLE = "The Feast of Ashes"
SERIES_TITLE = "The Burning Glass"
AUTHOR = "Luka Vane"

PARTS = {
    "part-1": {"title": "Part One: Establishment", "roman": "I"},
    "part-2": {"title": "Part Two: Deepening", "roman": "II"},
    "part-3": {"title": "Part Three: Complication", "roman": "III"},
    "part-4": {"title": "Part Four: Revelation and Reckoning", "roman": "IV"},
    "part-5": {"title": "Part Five: Aftermath", "roman": "V"},
}

CHAPTER_TITLES = {
    1: "The Furnace at Dawn",
    2: "The Ghetto at Evening",
    3: "The Contarini Furnace",
    4: "The Storeroom",
    5: "The Weight of Glass",
    6: "Light Through a Stolen Lens",
    7: "The Guild and the Ghetto",
    8: "The Rialto",
    9: "The Craft and the Girl",
    10: "The Silent Room",
    11: "The Celebration",
    12: "The Alhazen Letters",
    13: "The Assembly",
    14: "Questions in the Dark",
    15: "The Friar's Shadow",
    16: "The Silk",
    17: "The Confrontation",
    18: "Fornovo",
    19: "The Handler",
    20: "The Father's Secret",
    21: "Mirela's Truth",
    22: "The Closing Trap",
    23: "The Crisis",
    24: "The Plan",
    25: "The Sabotage",
    26: "The Test",
    27: "The Unraveling",
    28: "The Exposure",
    29: "Bardolino's Choice",
    30: "The Self-Revelation",
    31: "Exile",
    32: "Final Suspense",
    33: "The Last Lesson",
    34: "The Grinding Wheel",
}

CHAPTER_TO_PART = {}
for ch in range(1, 7):
    CHAPTER_TO_PART[ch] = "part-1"
for ch in range(7, 14):
    CHAPTER_TO_PART[ch] = "part-2"
for ch in range(14, 24):
    CHAPTER_TO_PART[ch] = "part-3"
for ch in range(24, 31):
    CHAPTER_TO_PART[ch] = "part-4"
for ch in range(31, 35):
    CHAPTER_TO_PART[ch] = "part-5"



def md_to_html_safe(text: str) -> str:
    """Convert markdown prose to safe HTML."""
    paragraphs = text.strip().split("\n\n")
    html_parts = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if re.match(r"^\*{3,}$", para.strip()):
            html_parts.append('<div class="scene-break" aria-hidden="true"></div>')
            continue
        # Escape HTML entities but preserve typographic quotes and dashes
        para = escape(para, quote=False)
        # Convert *text* to <em>text</em> (but not ** which would be bold)
        para = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", para)
        # Handle line breaks within a paragraph (single newlines)
        para = para.replace("\n", " ")
        html_parts.append(f"<p>{para}</p>")
    return "\n".join(html_parts)


def read_css() -> str:
    css_path = REPO_ROOT / "site" / "style.css"
    if css_path.exists():
        return css_path.read_text()
    return ""


def get_progress_info() -> dict:
    """Parse progress.md for stats."""
    info = {}
    if PROGRESS.exists():
        text = PROGRESS.read_text()
        m = re.search(r"\*\*Words:\*\*\s*([\d,]+)\s*/\s*([\d,]+)", text)
        if m:
            info["words"] = m.group(1)
            info["target"] = m.group(2)
        m = re.search(r"\*\*Chapters:\*\*\s*(\d+)\s*/\s*(\d+)", text)
        if m:
            info["chapters_done"] = int(m.group(1))
            info["chapters_total"] = int(m.group(2))
        m = re.search(r"\*\*Reading time:\*\*\s*(.+?)estimated", text)
        if m:
            info["reading_time"] = m.group(1).strip()
        m = re.search(r"\((\d+\.\d+)%\)", text)
        if m:
            info["percent"] = m.group(1)
    return info


def collect_chapters() -> list:
    """Collect all written chapters with their scenes."""
    chapters = []
    for part_dir in sorted(MANUSCRIPT.glob("part-*")):
        part_key = part_dir.name
        for ch_dir in sorted(part_dir.glob("chapter-*")):
            ch_num = int(ch_dir.name.replace("chapter-", ""))
            scenes = []
            for scene_file in sorted(ch_dir.glob("scene-*.md")):
                scenes.append(scene_file.read_text().strip())
            if scenes:
                chapters.append({
                    "num": ch_num,
                    "title": CHAPTER_TITLES.get(ch_num, f"Chapter {ch_num}"),
                    "part_key": part_key,
                    "part_title": PARTS.get(part_key, {}).get("title", part_key),
                    "part_roman": PARTS.get(part_key, {}).get("roman", ""),
                    "scenes": scenes,
                })
    return chapters


def page_header(title: str, description: str = "") -> str:
    meta_desc = f'<meta name="description" content="{escape(description)}">' if description else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{meta_desc}
<title>{escape(title)} &mdash; {BOOK_TITLE}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
{read_css()}
</style>
</head>
<body>
"""


def page_footer() -> str:
    return """</body>
</html>"""


def build_home(chapters: list, progress: dict) -> str:
    pct = progress.get("percent", "0")
    words = progress.get("words", "0")
    target = progress.get("target", "110,000")
    reading_time = progress.get("reading_time", "")
    chapters_done = progress.get("chapters_done", 0)
    chapters_total = progress.get("chapters_total", 34)

    # Group chapters by part
    parts_grouped = {}
    for ch in chapters:
        pk = ch["part_key"]
        if pk not in parts_grouped:
            parts_grouped[pk] = {"title": ch["part_title"], "roman": ch["part_roman"], "chapters": []}
        parts_grouped[pk]["chapters"].append(ch)

    toc_html = ""
    for pk in sorted(parts_grouped.keys()):
        part = parts_grouped[pk]
        toc_html += f'<div class="toc-part">\n'
        toc_html += f'<h3>{escape(part["title"])}</h3>\n'
        toc_html += '<ol class="toc-chapters">\n'
        for ch in part["chapters"]:
            word_count = sum(len(s.split()) for s in ch["scenes"])
            toc_html += f'<li value="{ch["num"]}"><a href="chapters/{ch["num"]:02d}.html">{escape(ch["title"])}</a><span class="toc-meta">{word_count:,} words</span></li>\n'
        toc_html += '</ol>\n</div>\n'

    # Add unwritten parts
    for pk in sorted(PARTS.keys()):
        if pk not in parts_grouped:
            toc_html += f'<div class="toc-part toc-upcoming">\n'
            toc_html += f'<h3>{escape(PARTS[pk]["title"])}</h3>\n'
            toc_html += '<p class="toc-upcoming-note">Forthcoming</p>\n'
            toc_html += '</div>\n'

    html = page_header("Home", f"Literary historical fiction set in 1490s Venice. {chapters_done} of {chapters_total} chapters.")
    html += f"""
<main class="home">
  <header class="book-header">
    <p class="series-label">{escape(SERIES_TITLE)} &middot; Book One</p>
    <h1>{BOOK_TITLE}</h1>
    <p class="author">{escape(AUTHOR)}</p>
  </header>

  <div class="epigraph">
    <p>Venice, 1494. A seventeen-year-old Jewish lens grinder discovers that his master is manufacturing components for a weapon that uses light itself to burn.</p>
  </div>

  <div class="progress-bar-container">
    <div class="progress-label">
      <span>{words} of {target} words</span>
      <span>{pct}% complete</span>
    </div>
    <div class="progress-track">
      <div class="progress-fill" style="width: {pct}%"></div>
    </div>
    <div class="progress-stats">
      <span>{chapters_done} of {chapters_total} chapters</span>
      <span>~{reading_time} reading time</span>
    </div>
  </div>

  <nav class="toc" aria-label="Table of Contents">
    <h2>Chapters</h2>
    {toc_html}
  </nav>

  <footer class="site-footer">
    <p>First draft in progress. This is a working manuscript.</p>
  </footer>
</main>
"""
    html += page_footer()
    return html


def build_chapter(ch: dict, prev_ch: dict | None, next_ch: dict | None) -> str:
    ch_num = ch["num"]
    title = ch["title"]

    # Build navigation
    nav_prev = ""
    nav_next = ""
    if prev_ch:
        nav_prev = f'<a href="{prev_ch["num"]:02d}.html" class="nav-prev">&larr; Chapter {prev_ch["num"]}: {escape(prev_ch["title"])}</a>'
    if next_ch:
        nav_next = f'<a href="{next_ch["num"]:02d}.html" class="nav-next">Chapter {next_ch["num"]}: {escape(next_ch["title"])} &rarr;</a>'

    # Build prose
    prose_parts = []
    for i, scene in enumerate(ch["scenes"]):
        prose_parts.append(md_to_html_safe(scene))
        if i < len(ch["scenes"]) - 1:
            prose_parts.append('<div class="scene-break" aria-hidden="true"></div>')
    prose_html = "\n".join(prose_parts)

    word_count = sum(len(s.split()) for s in ch["scenes"])

    html = page_header(f"Chapter {ch_num}: {title}", f"Chapter {ch_num} of The Feast of Ashes")
    html += f"""
<main class="chapter">
  <nav class="chapter-nav top" aria-label="Chapter navigation">
    <a href="../index.html" class="nav-home">{escape(BOOK_TITLE)}</a>
  </nav>

  <header class="chapter-header">
    <p class="part-label">{escape(ch["part_title"])}</p>
    <h1><span class="chapter-number">Chapter {ch_num}</span>{escape(title)}</h1>
    <p class="chapter-meta">{word_count:,} words</p>
  </header>

  <article class="prose">
    {prose_html}
  </article>

  <nav class="chapter-nav bottom" aria-label="Chapter navigation">
    {nav_prev}
    {nav_next}
  </nav>
</main>
"""
    html += page_footer()
    return html


def main():
    chapters = collect_chapters()
    progress = get_progress_info()

    # Create output directories
    os.makedirs(OUTPUT / "chapters", exist_ok=True)

    # Build home page
    (OUTPUT / "index.html").write_text(build_home(chapters, progress))
    print(f"Built index.html")

    # Build chapter pages
    for i, ch in enumerate(chapters):
        prev_ch = chapters[i - 1] if i > 0 else None
        next_ch = chapters[i + 1] if i < len(chapters) - 1 else None
        path = OUTPUT / "chapters" / f"{ch['num']:02d}.html"
        path.write_text(build_chapter(ch, prev_ch, next_ch))
        print(f"Built chapter {ch['num']:02d}: {ch['title']}")

    # Copy CNAME or create .nojekyll
    (OUTPUT / ".nojekyll").write_text("")

    print(f"\nSite built: {len(chapters)} chapters, {OUTPUT}")


if __name__ == "__main__":
    main()
