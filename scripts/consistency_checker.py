#!/usr/bin/env python3
"""
consistency_checker.py - Comprehensive consistency checking tool for historical fiction manuscripts.

Validates a manuscript against its book_bible.yaml to catch:
  - Character age inconsistencies at any point in the timeline
  - Relationship math errors (marriage duration, children's ages, etc.)
  - Implausible travel times between locations
  - Character presence violations (dead characters appearing, wrong locations)
  - Physical description inconsistencies across manuscript files
  - Timeline ordering violations (accidental time travel)

Usage:
    python3 consistency_checker.py series/{series_name}/{book_name}/

Expects the book directory to contain:
    book_bible.yaml   - Story bible with characters, locations, timeline, world_rules
    manuscript/       - Directory tree of .md scene files (part-N/chapter-NN/scene-NN.md)
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Character:
    """Represents a character from the story bible."""
    name: str
    aliases: list[str] = field(default_factory=list)
    birth_date: Optional[date] = None
    death_date: Optional[date] = None
    physical: dict[str, str] = field(default_factory=dict)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    locations_timeline: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Location:
    """Represents a location from the story bible."""
    name: str
    aliases: list[str] = field(default_factory=list)
    region: str = ""
    coordinates: Optional[tuple[float, float]] = None


@dataclass
class TravelRule:
    """Defines plausible travel time between two locations."""
    origin: str
    destination: str
    min_days: float = 0.0
    max_days: float = 0.0
    method: str = ""


@dataclass
class TimelineEvent:
    """An event on the story timeline."""
    date: date
    description: str
    characters: list[str] = field(default_factory=list)
    location: str = ""


@dataclass
class SceneInfo:
    """Parsed metadata and content from a single manuscript scene file."""
    file_path: Path
    part: int = 0
    chapter: int = 0
    scene: int = 0
    scene_date: Optional[date] = None
    location: str = ""
    characters_mentioned: list[str] = field(default_factory=list)
    text: str = ""
    physical_descriptions: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class Issue:
    """A single consistency issue found during checking."""
    severity: str  # "error", "warning", "info"
    category: str
    message: str
    reference: str  # e.g. "Part 1 / Chapter 3 / Scene 2"

    def __str__(self) -> str:
        icon = {"error": "[ERR]", "warning": "[WRN]", "info": "[INF]"}.get(
            self.severity, "[???]"
        )
        return f"{icon} [{self.category}] {self.reference}: {self.message}"


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_date_flexible(value: Any) -> Optional[date]:
    """Parse a date from various YAML representations.

    Supports:
        - datetime.date objects (YAML auto-parses YYYY-MM-DD)
        - Strings in YYYY-MM-DD, YYYY-MM, or YYYY formats
        - Integer years (e.g. 1920)
    """
    if value is None:
        return None
    if isinstance(value, date):
        return value
    s = str(value).strip()
    # YYYY-MM-DD
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    # YYYY-MM (assume first of month)
    m = re.match(r"^(\d{4})-(\d{1,2})$", s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), 1)
    # YYYY (assume January 1)
    m = re.match(r"^(\d{4})$", s)
    if m:
        return date(int(m.group(1)), 1, 1)
    return None


def age_at_date(birth: date, ref: date) -> int:
    """Calculate age in whole years at a given reference date."""
    age = ref.year - birth.year
    if (ref.month, ref.day) < (birth.month, birth.day):
        age -= 1
    return age


def scene_ref(scene: SceneInfo) -> str:
    """Human-readable reference string for a scene."""
    return f"Part {scene.part} / Chapter {scene.chapter} / Scene {scene.scene}"


# ---------------------------------------------------------------------------
# Bible loading
# ---------------------------------------------------------------------------

class StoryBible:
    """Loads and holds all data from book_bible.yaml."""

    def __init__(self, bible_path: Path) -> None:
        self.path = bible_path
        self.raw: dict[str, Any] = {}
        self.characters: dict[str, Character] = {}
        self.locations: dict[str, Location] = {}
        self.travel_rules: list[TravelRule] = []
        self.timeline: list[TimelineEvent] = []
        self.world_rules: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Parse the YAML bible file into structured data."""
        with open(self.path, "r", encoding="utf-8") as f:
            self.raw = yaml.safe_load(f) or {}

        self._load_characters()
        self._load_locations()
        self._load_travel_rules()
        self._load_timeline()
        self.world_rules = self.raw.get("world_rules", {})

    def _load_characters(self) -> None:
        chars_data = self.raw.get("characters", {})
        if isinstance(chars_data, list):
            items = [(c.get("name", f"unnamed_{i}"), c) for i, c in enumerate(chars_data)]
        else:
            items = chars_data.items()

        for name, data in items:
            if not isinstance(data, dict):
                data = {}
            char = Character(
                name=name,
                aliases=data.get("aliases", []) or [],
                birth_date=parse_date_flexible(data.get("birth_date") or data.get("born")),
                death_date=parse_date_flexible(data.get("death_date") or data.get("died")),
                physical=data.get("physical", {}) or {},
                relationships=data.get("relationships", []) or [],
                locations_timeline=data.get("locations_timeline", []) or [],
            )
            self.characters[name.lower()] = char
            for alias in char.aliases:
                self.characters[alias.lower()] = char

    def _load_locations(self) -> None:
        locs_data = self.raw.get("locations", {})
        if isinstance(locs_data, list):
            items = [(loc.get("name", f"unnamed_{i}"), loc) for i, loc in enumerate(locs_data)]
        else:
            items = locs_data.items()

        for name, data in items:
            if not isinstance(data, dict):
                data = {}
            loc = Location(
                name=name,
                aliases=data.get("aliases", []) or [],
                region=data.get("region", "") or "",
            )
            coords = data.get("coordinates")
            if coords and isinstance(coords, (list, tuple)) and len(coords) == 2:
                loc.coordinates = (float(coords[0]), float(coords[1]))
            self.locations[name.lower()] = loc
            for alias in loc.aliases:
                self.locations[alias.lower()] = loc

    def _load_travel_rules(self) -> None:
        rules = self.raw.get("travel_rules", []) or []
        for r in rules:
            if not isinstance(r, dict):
                continue
            self.travel_rules.append(TravelRule(
                origin=r.get("origin", ""),
                destination=r.get("destination", ""),
                min_days=float(r.get("min_days", 0)),
                max_days=float(r.get("max_days", 0)),
                method=r.get("method", ""),
            ))

    def _load_timeline(self) -> None:
        events = self.raw.get("timeline", []) or []
        for ev in events:
            if not isinstance(ev, dict):
                continue
            d = parse_date_flexible(ev.get("date"))
            if d is None:
                continue
            self.timeline.append(TimelineEvent(
                date=d,
                description=ev.get("description", ""),
                characters=ev.get("characters", []) or [],
                location=ev.get("location", ""),
            ))
        self.timeline.sort(key=lambda e: e.date)

    def get_character(self, name: str) -> Optional[Character]:
        """Look up a character by name or alias (case-insensitive)."""
        return self.characters.get(name.lower())

    def all_character_names(self) -> set[str]:
        """Return the set of all unique character canonical names."""
        return {c.name for c in self.characters.values()}


# ---------------------------------------------------------------------------
# Manuscript scanner
# ---------------------------------------------------------------------------

class ManuscriptScanner:
    """Scans manuscript .md files and extracts scene metadata and content."""

    # Regex patterns for extracting scene metadata from YAML front matter or comments
    _FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
    _PART_CHAPTER_SCENE = re.compile(
        r"part-(\d+)/chapter-(\d+)/scene-(\d+)\.md$"
    )
    # Patterns for finding physical descriptions in prose
    _PHYSICAL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
        ("eye", re.compile(
            r"\b(\w+(?:\s+\w+)?)\b['\u2019]?s?\s+(?:\w+\s+)*?"
            r"(blue|green|brown|hazel|gray|grey|black|dark|light|pale|bright|amber|violet)\s+"
            r"eyes?\b",
            re.IGNORECASE,
        )),
        ("hair", re.compile(
            r"\b(\w+(?:\s+\w+)?)\b['\u2019]?s?\s+(?:\w+\s+)*?"
            r"(blonde?|brunette|black|dark|red|auburn|grey|gray|white|silver|brown|sandy|golden|chestnut)\s+"
            r"hair\b",
            re.IGNORECASE,
        )),
        ("height", re.compile(
            r"\b(\w+(?:\s+\w+)?)\b\s+(?:was|stood|standing)\s+(?:\w+\s+)*?"
            r"(tall|short|towering|petite|diminutive|average[\s-]height)\b",
            re.IGNORECASE,
        )),
    ]

    def __init__(self, manuscript_dir: Path, bible: StoryBible) -> None:
        self.manuscript_dir = manuscript_dir
        self.bible = bible
        self.scenes: list[SceneInfo] = []

    def scan(self) -> list[SceneInfo]:
        """Walk the manuscript directory and parse every .md file."""
        md_files = sorted(self.manuscript_dir.rglob("*.md"))
        for fp in md_files:
            scene = self._parse_scene(fp)
            if scene is not None:
                self.scenes.append(scene)
        self.scenes.sort(key=lambda s: (s.part, s.chapter, s.scene))
        return self.scenes

    def _parse_scene(self, fp: Path) -> Optional[SceneInfo]:
        """Parse a single .md scene file."""
        relative = str(fp.relative_to(self.manuscript_dir))
        m = self._PART_CHAPTER_SCENE.search(relative.replace("\\", "/"))
        if not m:
            return None

        text = fp.read_text(encoding="utf-8", errors="replace")

        scene = SceneInfo(
            file_path=fp,
            part=int(m.group(1)),
            chapter=int(m.group(2)),
            scene=int(m.group(3)),
            text=text,
        )

        # Try to extract front matter metadata
        fm = self._FRONT_MATTER.match(text)
        if fm:
            try:
                meta = yaml.safe_load(fm.group(1)) or {}
                scene.scene_date = parse_date_flexible(meta.get("date"))
                scene.location = meta.get("location", "")
                chars = meta.get("characters", [])
                if isinstance(chars, list):
                    scene.characters_mentioned = chars
                elif isinstance(chars, str):
                    scene.characters_mentioned = [c.strip() for c in chars.split(",")]
            except yaml.YAMLError:
                pass

        # If no characters listed in front matter, scan text for known names
        if not scene.characters_mentioned:
            scene.characters_mentioned = self._find_characters_in_text(text)

        # Extract physical descriptions from prose
        scene.physical_descriptions = self._extract_physical_descriptions(text)

        return scene

    def _find_characters_in_text(self, text: str) -> list[str]:
        """Find known character names mentioned in the text."""
        found: list[str] = []
        seen: set[str] = set()
        for char in self.bible.all_character_names():
            # Use word-boundary matching for names
            pattern = re.compile(r"\b" + re.escape(char) + r"\b", re.IGNORECASE)
            if pattern.search(text) and char.lower() not in seen:
                found.append(char)
                seen.add(char.lower())
        return found

    def _extract_physical_descriptions(self, text: str) -> dict[str, list[str]]:
        """Extract physical description snippets tied to character names."""
        descriptions: dict[str, list[str]] = {}
        for _attr_name, pattern in self._PHYSICAL_PATTERNS:
            for match in pattern.finditer(text):
                # The first capture group is the name-like token preceding the description
                possible_name = match.group(1).strip()
                snippet = match.group(0).strip()
                # Only record if the name token matches a known character
                char = self.bible.get_character(possible_name)
                if char:
                    descriptions.setdefault(char.name, []).append(snippet)
        return descriptions


# ---------------------------------------------------------------------------
# Consistency checks
# ---------------------------------------------------------------------------

class ConsistencyChecker:
    """Runs all consistency checks and collects issues."""

    def __init__(self, bible: StoryBible, scenes: list[SceneInfo]) -> None:
        self.bible = bible
        self.scenes = scenes
        self.issues: list[Issue] = []

    def run_all(self) -> list[Issue]:
        """Execute every consistency check and return the combined issue list."""
        self.check_character_ages()
        self.check_character_alive()
        self.check_relationship_math()
        self.check_travel_times()
        self.check_physical_descriptions()
        self.check_timeline_ordering()
        return self.issues

    # -- Character age checks -----------------------------------------------

    def check_character_ages(self) -> None:
        """Validate that character ages referenced in scenes are plausible."""
        age_pattern = re.compile(
            r"\b(\w+(?:\s+\w+)?)\b[,\s]+(?:age[d]?\s+|(\d{1,3})\s*(?:years?\s+old|year[\s-]old))",
            re.IGNORECASE,
        )
        explicit_age = re.compile(
            r"\b(\d{1,3})\s*[-\s]?year[\s-]?old\s+(\w+(?:\s+\w+)?)\b",
            re.IGNORECASE,
        )

        for scene in self.scenes:
            if scene.scene_date is None:
                continue
            # Pattern: "Name, aged 42" or "Name, 42 years old"
            for match in age_pattern.finditer(scene.text):
                name_token = match.group(1).strip()
                stated_age_str = match.group(2)
                if stated_age_str is None:
                    continue
                stated_age = int(stated_age_str)
                char = self.bible.get_character(name_token)
                if char and char.birth_date:
                    expected = age_at_date(char.birth_date, scene.scene_date)
                    if stated_age != expected:
                        self.issues.append(Issue(
                            severity="error",
                            category="Character Age",
                            message=(
                                f"{char.name} is stated as age {stated_age} but should be "
                                f"{expected} on {scene.scene_date} "
                                f"(born {char.birth_date})."
                            ),
                            reference=scene_ref(scene),
                        ))

            # Pattern: "42-year-old Margaret"
            for match in explicit_age.finditer(scene.text):
                stated_age = int(match.group(1))
                name_token = match.group(2).strip()
                char = self.bible.get_character(name_token)
                if char and char.birth_date:
                    expected = age_at_date(char.birth_date, scene.scene_date)
                    if stated_age != expected:
                        self.issues.append(Issue(
                            severity="error",
                            category="Character Age",
                            message=(
                                f"{char.name} is stated as {stated_age}-year-old but should be "
                                f"{expected} on {scene.scene_date} "
                                f"(born {char.birth_date})."
                            ),
                            reference=scene_ref(scene),
                        ))

    # -- Character alive / presence checks ----------------------------------

    def check_character_alive(self) -> None:
        """Check that dead characters don't appear in scenes after their death date."""
        for scene in self.scenes:
            if scene.scene_date is None:
                continue
            for name in scene.characters_mentioned:
                char = self.bible.get_character(name)
                if char is None:
                    continue
                if char.death_date and scene.scene_date > char.death_date:
                    # Allow if the character appears only in dialogue or memory
                    # (heuristic: name in quotes or preceded by "remember")
                    memory_pattern = re.compile(
                        r"(?:remember(?:ed|ing)?|recalled?|thought\s+(?:of|about)|"
                        r"memor(?:y|ies)|ghost|spirit|dream(?:ed|t)?)\s+.*?"
                        + re.escape(name),
                        re.IGNORECASE,
                    )
                    if memory_pattern.search(scene.text):
                        self.issues.append(Issue(
                            severity="info",
                            category="Character Presence",
                            message=(
                                f"{char.name} (died {char.death_date}) is mentioned on "
                                f"{scene.scene_date} -- appears to be in memory/dialogue."
                            ),
                            reference=scene_ref(scene),
                        ))
                    else:
                        self.issues.append(Issue(
                            severity="error",
                            category="Character Presence",
                            message=(
                                f"{char.name} appears in scene dated {scene.scene_date} "
                                f"but died on {char.death_date}."
                            ),
                            reference=scene_ref(scene),
                        ))

                # Check birth: character shouldn't act before being born
                if char.birth_date and scene.scene_date < char.birth_date:
                    self.issues.append(Issue(
                        severity="error",
                        category="Character Presence",
                        message=(
                            f"{char.name} appears in scene dated {scene.scene_date} "
                            f"but was not born until {char.birth_date}."
                        ),
                        reference=scene_ref(scene),
                    ))

    # -- Relationship math --------------------------------------------------

    def check_relationship_math(self) -> None:
        """Validate relationship durations mentioned in prose against the bible."""
        # Pattern: "married (for) N years"
        married_pattern = re.compile(
            r"\b(\w+(?:\s+\w+)?)\b.*?married\s+(?:for\s+)?(\d+)\s+years?",
            re.IGNORECASE,
        )
        # Pattern: "divorced N years ago"
        divorced_pattern = re.compile(
            r"\b(\w+(?:\s+\w+)?)\b.*?divorced?\s+(\d+)\s+years?\s+ago",
            re.IGNORECASE,
        )

        for scene in self.scenes:
            if scene.scene_date is None:
                continue

            for match in married_pattern.finditer(scene.text):
                name_token = match.group(1).strip()
                stated_years = int(match.group(2))
                char = self.bible.get_character(name_token)
                if char is None:
                    continue
                for rel in char.relationships:
                    if not isinstance(rel, dict):
                        continue
                    rel_type = rel.get("type", "").lower()
                    if rel_type not in ("spouse", "married", "marriage", "husband", "wife"):
                        continue
                    marriage_date = parse_date_flexible(rel.get("start") or rel.get("date"))
                    if marriage_date is None:
                        continue
                    expected_years = scene.scene_date.year - marriage_date.year
                    if (scene.scene_date.month, scene.scene_date.day) < (
                        marriage_date.month, marriage_date.day
                    ):
                        expected_years -= 1
                    if abs(stated_years - expected_years) > 1:
                        self.issues.append(Issue(
                            severity="error",
                            category="Relationship Math",
                            message=(
                                f"{char.name} stated married {stated_years} years, "
                                f"but marriage date {marriage_date} gives ~{expected_years} years "
                                f"as of {scene.scene_date}."
                            ),
                            reference=scene_ref(scene),
                        ))

            for match in divorced_pattern.finditer(scene.text):
                name_token = match.group(1).strip()
                stated_years = int(match.group(2))
                char = self.bible.get_character(name_token)
                if char is None:
                    continue
                for rel in char.relationships:
                    if not isinstance(rel, dict):
                        continue
                    divorce_date = parse_date_flexible(rel.get("end") or rel.get("divorced"))
                    if divorce_date is None:
                        continue
                    expected_years = scene.scene_date.year - divorce_date.year
                    if (scene.scene_date.month, scene.scene_date.day) < (
                        divorce_date.month, divorce_date.day
                    ):
                        expected_years -= 1
                    if abs(stated_years - expected_years) > 1:
                        self.issues.append(Issue(
                            severity="error",
                            category="Relationship Math",
                            message=(
                                f"{char.name} stated divorced {stated_years} years ago, "
                                f"but divorce date {divorce_date} gives ~{expected_years} years "
                                f"as of {scene.scene_date}."
                            ),
                            reference=scene_ref(scene),
                        ))

    # -- Travel times -------------------------------------------------------

    def check_travel_times(self) -> None:
        """Check if characters move between locations faster than defined limits."""
        # Build a per-character timeline of (date, location) from scenes
        char_locations: dict[str, list[tuple[date, str, SceneInfo]]] = {}
        for scene in self.scenes:
            if scene.scene_date is None or not scene.location:
                continue
            for name in scene.characters_mentioned:
                char = self.bible.get_character(name)
                if char:
                    char_locations.setdefault(char.name, []).append(
                        (scene.scene_date, scene.location, scene)
                    )

        # Sort each character's location visits by date
        for char_name, visits in char_locations.items():
            visits.sort(key=lambda v: v[0])
            for i in range(1, len(visits)):
                prev_date, prev_loc, prev_scene = visits[i - 1]
                curr_date, curr_loc, curr_scene = visits[i]
                if prev_loc.lower() == curr_loc.lower():
                    continue
                days_elapsed = (curr_date - prev_date).days
                # Check against travel rules
                for rule in self.bible.travel_rules:
                    origins = {rule.origin.lower()}
                    dests = {rule.destination.lower()}
                    pair_match = (
                        (prev_loc.lower() in origins and curr_loc.lower() in dests)
                        or (prev_loc.lower() in dests and curr_loc.lower() in origins)
                    )
                    if pair_match:
                        if days_elapsed < rule.min_days:
                            self.issues.append(Issue(
                                severity="error",
                                category="Travel Time",
                                message=(
                                    f"{char_name} travels from {prev_loc} to {curr_loc} in "
                                    f"{days_elapsed} days, but minimum is {rule.min_days} days"
                                    f" ({rule.method})."
                                ),
                                reference=(
                                    f"{scene_ref(prev_scene)} -> {scene_ref(curr_scene)}"
                                ),
                            ))
                        elif rule.max_days > 0 and days_elapsed > rule.max_days * 3:
                            # Only warn if the gap is suspiciously long (3x max)
                            self.issues.append(Issue(
                                severity="warning",
                                category="Travel Time",
                                message=(
                                    f"{char_name} takes {days_elapsed} days between "
                                    f"{prev_loc} and {curr_loc} (expected max {rule.max_days} "
                                    f"days by {rule.method}). "
                                    f"Possible missing scenes or timeline gap."
                                ),
                                reference=(
                                    f"{scene_ref(prev_scene)} -> {scene_ref(curr_scene)}"
                                ),
                            ))

    # -- Physical description consistency -----------------------------------

    def check_physical_descriptions(self) -> None:
        """Cross-reference physical descriptions in prose against the bible."""
        # Collect all descriptions per character across all scenes
        all_descriptions: dict[str, list[tuple[str, str]]] = {}
        for scene in self.scenes:
            for char_name, snippets in scene.physical_descriptions.items():
                for snippet in snippets:
                    all_descriptions.setdefault(char_name, []).append(
                        (snippet, scene_ref(scene))
                    )

        # Check against bible definitions
        for char_name, desc_list in all_descriptions.items():
            char = self.bible.get_character(char_name)
            if char is None:
                continue
            bible_phys = char.physical
            if not bible_phys:
                continue

            for snippet, ref in desc_list:
                snippet_lower = snippet.lower()

                # Check eye color
                bible_eyes = bible_phys.get("eyes", "").lower()
                if bible_eyes:
                    eye_colors = [
                        "blue", "green", "brown", "hazel", "gray", "grey",
                        "black", "dark", "light", "pale", "bright", "amber", "violet",
                    ]
                    for color in eye_colors:
                        if color in snippet_lower and "eye" in snippet_lower:
                            if color not in bible_eyes:
                                self.issues.append(Issue(
                                    severity="error",
                                    category="Physical Description",
                                    message=(
                                        f"{char_name}'s eyes described as containing "
                                        f"'{color}' but bible says '{bible_eyes}'. "
                                        f"Snippet: \"{snippet}\""
                                    ),
                                    reference=ref,
                                ))

                # Check hair color
                bible_hair = bible_phys.get("hair", "").lower()
                if bible_hair:
                    hair_colors = [
                        "blonde", "blond", "brunette", "black", "dark", "red",
                        "auburn", "grey", "gray", "white", "silver", "brown",
                        "sandy", "golden", "chestnut",
                    ]
                    for color in hair_colors:
                        if color in snippet_lower and "hair" in snippet_lower:
                            if color not in bible_hair:
                                self.issues.append(Issue(
                                    severity="error",
                                    category="Physical Description",
                                    message=(
                                        f"{char_name}'s hair described as '{color}' "
                                        f"but bible says '{bible_hair}'. "
                                        f"Snippet: \"{snippet}\""
                                    ),
                                    reference=ref,
                                ))

        # Check for internal inconsistency across scenes (same character,
        # contradictory descriptions even if no bible entry)
        for char_name, desc_list in all_descriptions.items():
            eye_colors_found: dict[str, str] = {}
            hair_colors_found: dict[str, str] = {}
            for snippet, ref in desc_list:
                snippet_lower = snippet.lower()
                if "eye" in snippet_lower:
                    for color in [
                        "blue", "green", "brown", "hazel", "gray", "grey",
                        "black", "amber", "violet",
                    ]:
                        if color in snippet_lower:
                            if eye_colors_found and color not in eye_colors_found:
                                first_color = next(iter(eye_colors_found))
                                first_ref = eye_colors_found[first_color]
                                self.issues.append(Issue(
                                    severity="warning",
                                    category="Physical Description",
                                    message=(
                                        f"{char_name}'s eyes are '{color}' here but "
                                        f"'{first_color}' in {first_ref}."
                                    ),
                                    reference=ref,
                                ))
                            eye_colors_found[color] = ref
                if "hair" in snippet_lower:
                    for color in [
                        "blonde", "blond", "brunette", "black", "red", "auburn",
                        "grey", "gray", "white", "silver", "brown", "sandy",
                        "golden", "chestnut",
                    ]:
                        if color in snippet_lower:
                            if hair_colors_found and color not in hair_colors_found:
                                first_color = next(iter(hair_colors_found))
                                first_ref = hair_colors_found[first_color]
                                self.issues.append(Issue(
                                    severity="warning",
                                    category="Physical Description",
                                    message=(
                                        f"{char_name}'s hair is '{color}' here but "
                                        f"'{first_color}' in {first_ref}."
                                    ),
                                    reference=ref,
                                ))
                            hair_colors_found[color] = ref

    # -- Timeline ordering --------------------------------------------------

    def check_timeline_ordering(self) -> None:
        """Verify that scene dates are in chronological order (no time travel)."""
        dated_scenes = [s for s in self.scenes if s.scene_date is not None]
        dated_scenes.sort(key=lambda s: (s.part, s.chapter, s.scene))

        for i in range(1, len(dated_scenes)):
            prev = dated_scenes[i - 1]
            curr = dated_scenes[i]
            assert prev.scene_date is not None
            assert curr.scene_date is not None

            # Within the same part, chapters should generally advance or stay same
            if prev.part == curr.part:
                if curr.scene_date < prev.scene_date:
                    # Allow small flashbacks within a chapter (same chapter)
                    if prev.chapter == curr.chapter:
                        self.issues.append(Issue(
                            severity="warning",
                            category="Timeline Order",
                            message=(
                                f"Scene date goes backward: {prev.scene_date} -> "
                                f"{curr.scene_date}. If this is an intentional flashback, "
                                f"consider adding a front matter tag: flashback: true"
                            ),
                            reference=scene_ref(curr),
                        ))
                    else:
                        self.issues.append(Issue(
                            severity="error",
                            category="Timeline Order",
                            message=(
                                f"Chapter {curr.chapter} scene date ({curr.scene_date}) "
                                f"is earlier than Chapter {prev.chapter} scene date "
                                f"({prev.scene_date}) within Part {curr.part}."
                            ),
                            reference=scene_ref(curr),
                        ))

        # Also validate bible timeline events are ordered
        for i in range(1, len(self.bible.timeline)):
            prev_ev = self.bible.timeline[i - 1]
            curr_ev = self.bible.timeline[i]
            if curr_ev.date < prev_ev.date:
                self.issues.append(Issue(
                    severity="error",
                    category="Timeline Order",
                    message=(
                        f"Bible timeline events out of order: "
                        f"'{prev_ev.description}' ({prev_ev.date}) comes before "
                        f"'{curr_ev.description}' ({curr_ev.date})."
                    ),
                    reference="book_bible.yaml / timeline",
                ))


# ---------------------------------------------------------------------------
# Output / reporting
# ---------------------------------------------------------------------------

def report_plain(issues: list[Issue], scenes_count: int, bible_path: Path) -> None:
    """Print a plain-text report to stdout."""
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]

    print(f"\n{'=' * 72}")
    print(f"  CONSISTENCY CHECK REPORT")
    print(f"  Bible: {bible_path}")
    print(f"  Scenes scanned: {scenes_count}")
    print(f"{'=' * 72}")
    print(f"  Errors:   {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"  Info:     {len(infos)}")
    print(f"{'=' * 72}\n")

    if errors:
        print("--- ERRORS ---\n")
        for issue in errors:
            print(f"  {issue}\n")

    if warnings:
        print("--- WARNINGS ---\n")
        for issue in warnings:
            print(f"  {issue}\n")

    if infos:
        print("--- INFO ---\n")
        for issue in infos:
            print(f"  {issue}\n")

    if not issues:
        print("  No issues found. Manuscript is consistent with the story bible.\n")

    print(f"{'=' * 72}")


def report_rich(issues: list[Issue], scenes_count: int, bible_path: Path) -> None:
    """Print a rich-formatted report using the rich library."""
    console = Console()

    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]

    # Summary panel
    summary_lines = [
        f"Bible: [cyan]{bible_path}[/cyan]",
        f"Scenes scanned: [cyan]{scenes_count}[/cyan]",
        "",
        f"[red]Errors:   {len(errors)}[/red]",
        f"[yellow]Warnings: {len(warnings)}[/yellow]",
        f"[blue]Info:     {len(infos)}[/blue]",
    ]
    console.print(Panel(
        "\n".join(summary_lines),
        title="Consistency Check Report",
        box=box.DOUBLE,
    ))

    if not issues:
        console.print(
            "\n[green bold]No issues found.[/green bold] "
            "Manuscript is consistent with the story bible.\n"
        )
        return

    # Issues table
    if errors or warnings:
        table = Table(
            title="Issues",
            box=box.ROUNDED,
            show_lines=True,
            expand=True,
        )
        table.add_column("Severity", style="bold", width=8, no_wrap=True)
        table.add_column("Category", width=20)
        table.add_column("Reference", width=30)
        table.add_column("Message")

        severity_style = {
            "error": "red",
            "warning": "yellow",
            "info": "blue",
        }

        for issue in errors + warnings + infos:
            table.add_row(
                f"[{severity_style[issue.severity]}]{issue.severity.upper()}[/]",
                issue.category,
                issue.reference,
                issue.message,
            )

        console.print(table)
        console.print()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point for the consistency checker."""
    parser = argparse.ArgumentParser(
        description="Validate manuscript consistency against the story bible.",
        epilog="Example: python3 consistency_checker.py series/tides-of-war/book-1/",
    )
    parser.add_argument(
        "book_dir",
        type=str,
        help="Path to the book directory containing book_bible.yaml and manuscript/.",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Force plain-text output (no rich formatting).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any errors are found.",
    )
    args = parser.parse_args()

    book_path = Path(args.book_dir).resolve()

    # Validate directory structure
    if not book_path.is_dir():
        print(f"ERROR: Book directory not found: {book_path}", file=sys.stderr)
        sys.exit(1)

    bible_path = book_path / "book_bible.yaml"
    if not bible_path.is_file():
        print(f"ERROR: Story bible not found: {bible_path}", file=sys.stderr)
        sys.exit(1)

    manuscript_dir = book_path / "manuscript"
    if not manuscript_dir.is_dir():
        print(f"ERROR: Manuscript directory not found: {manuscript_dir}", file=sys.stderr)
        sys.exit(1)

    # Load and check
    try:
        bible = StoryBible(bible_path)
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse story bible: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to load story bible: {e}", file=sys.stderr)
        sys.exit(1)

    scanner = ManuscriptScanner(manuscript_dir, bible)
    scenes = scanner.scan()

    if not scenes:
        print(f"WARNING: No manuscript scene files found in {manuscript_dir}", file=sys.stderr)
        print("Expected file pattern: manuscript/part-N/chapter-NN/scene-NN.md")
        sys.exit(0)

    checker = ConsistencyChecker(bible, scenes)
    issues = checker.run_all()

    # Report
    use_rich = RICH_AVAILABLE and not args.plain
    if use_rich:
        report_rich(issues, len(scenes), bible_path)
    else:
        report_plain(issues, len(scenes), bible_path)

    # Exit code
    if args.strict:
        error_count = sum(1 for i in issues if i.severity == "error")
        if error_count > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
