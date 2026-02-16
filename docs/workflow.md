# Workflow Documentation

This document describes the complete workflow for the Historical Fiction Novel Factory, an autonomous novel-writing system orchestrated by Claude. It covers every phase from initial story conception through final publication, including the git-based editorial workflow, context assembly strategy, and quality assurance processes.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [The Dynamic Plotter Methodology](#the-dynamic-plotter-methodology)
3. [Phase 1: Conception](#phase-1-conception)
4. [Phase 2: Research](#phase-2-research)
5. [Phase 3: Design](#phase-3-design)
6. [Phase 4: Writing](#phase-4-writing)
7. [Phase 5: Editing](#phase-5-editing)
8. [Phase 6: Publication](#phase-6-publication)
9. [Git Workflow and Worktrees](#git-workflow-and-worktrees)
10. [The Page-by-Page Writing Process](#the-page-by-page-writing-process)
11. [The Multi-Pass Editing Process](#the-multi-pass-editing-process)
12. [Pull Requests as Editorial Checkpoints](#pull-requests-as-editorial-checkpoints)
13. [Claude GitHub App as Editorial Reviewer](#claude-github-app-as-editorial-reviewer)
14. [Progress Tracking](#progress-tracking)
15. [Consistency Checking](#consistency-checking)
16. [The Overwrite-Then-Cut Approach](#the-overwrite-then-cut-approach)
17. [The Continuity Notes System](#the-continuity-notes-system)
18. [Handling Narrative Deviations](#handling-narrative-deviations)

---

## System Overview

The Historical Fiction Novel Factory uses a multi-agent architecture where a single orchestrator delegates all prose production to specialized background worker agents. The orchestrator never writes prose directly. Instead, it manages the pipeline, assembles context, coordinates git operations, and enforces quality standards.

### Agent Roles

| Role | Mode | Responsibility |
|------|------|----------------|
| **Orchestrator** | Interactive | Plans, delegates, reviews, manages git, tracks progress |
| **Writer Agent** | Background Task | Produces prose one page at a time following strict context and style rules |
| **Editor Agent** | Background Task | Reviews prose for quality, consistency, voice, and style compliance |
| **Researcher Agent** | Background Task | Gathers historical facts, verifies period accuracy |
| **Reviewer** | Claude GitHub App | Reviews pull requests with editorial comments |

### The Serial Production Rule

Only one writer agent operates at a time. This is the single most important architectural constraint in the system. Running multiple writers in parallel would cause:

- **Voice drift**: Each agent develops slightly different stylistic tendencies within a session.
- **Continuity gaps**: Agent B cannot know what Agent A just wrote if they work simultaneously.
- **Repetition**: Without awareness of what was just produced, agents fall into repeated imagery, phrasing, and structural patterns.

Serial production means the orchestrator waits for each page to complete before dispatching the next. This is slower but produces a coherent manuscript that reads as though one person wrote it.

### Data Flow

```
Orchestrator
    |
    |-- assembles context (story bible, outline, previous pages, continuity notes)
    |-- dispatches Writer Agent with assembled prompt
    |
    Writer Agent
        |-- produces ~250 words (one page)
        |-- returns output to Orchestrator
    |
    Orchestrator
        |-- reviews output
        |-- dispatches Editor Agent if needed
        |-- updates continuity notes
        |-- commits to git
        |-- repeats for next page
```

---

## The Dynamic Plotter Methodology

The Dynamic Plotter is a hybrid methodology that takes the best elements from two opposing schools of fiction writing:

**From the Plotter school**: Rigorous upfront planning at every level (series, novel, part, chapter, scene). Complete character design documents. The Seven-Layer Narrative Architecture (see `docs/story_structure.md`) — a custom framework synthesized from twelve methodologies. Detailed outlines before a single word of prose is written.

**From the Pantser school**: Serial page-by-page writing where each page is composed with only local context, allowing the prose to develop organically. Freedom to follow unexpected character decisions, plot twists, or thematic directions that emerge during writing.

The reconciliation works as follows:

1. **Plan everything before writing.** The outline goes down to scene-level detail with specific beats, emotional arcs, and page estimates.
2. **Write serially, one page at a time.** The writer agent receives curated context -- not the entire plan. This allows local creative freedom while maintaining global coherence.
3. **When the story deviates from the plan, update the plan.** The outline is a living document. If a character does something unexpected but interesting, the orchestrator adjusts downstream outline entries to accommodate.
4. **Never force the story back to a plan that no longer fits.** Organic evolution is a feature, not a bug. The plan serves the story, not the reverse.

This approach is particularly well-suited to LLM-based writing because it solves two fundamental problems: LLMs without plans produce meandering, structureless prose; and LLMs forced to follow rigid plans produce mechanical, predictable prose. The Dynamic Plotter gives the model a strong skeleton while letting the muscle and skin form naturally.

---

## Phase 1: Conception

The conception phase generates and evaluates story ideas before committing to a full novel.

### Steps

1. **Generate pitches.** The orchestrator dispatches a researcher agent to generate 5-7 story pitches using `templates/pitch_template.md`. Each pitch includes a premise, setting, protagonist, central conflict, thematic question, and series potential.

2. **Evaluate pitches.** Each pitch is scored against criteria:
   - Originality of premise
   - Depth of available historical research
   - Series potential (can this sustain 2-4 books?)
   - Target audience clarity
   - Emotional resonance of the central conflict
   - Feasibility of period research

3. **Select and refine.** The highest-scoring pitch is selected. The orchestrator may combine elements from multiple pitches.

4. **Initialize the project.** Create the series directory structure under `series/`, initialize the series bible, and commit the pitch document.

### Output Artifacts

- `series/{series_name}/series_bible.yaml` (initial)
- Selected pitch document
- Initial commit on `main`

---

## Phase 2: Research

Historical fiction demands accuracy. The research phase builds a comprehensive factual foundation before any design or writing begins.

### Steps

1. **Define the research scope.** Based on the selected pitch, identify the historical period, geographic locations, social classes, and specific events that the novel will engage with.

2. **Conduct web research.** The orchestrator dispatches researcher agents to gather facts on the period. Each research task focuses on a specific domain (daily life, politics, technology, social customs, etc.).

3. **Build the historical timeline.** All key events are placed in chronological order in `research/historical_timeline.yaml`. This includes both real historical events and the fictional events of the novel, interleaved.

4. **Document sources.** Every factual claim is traced to at least one source in `research/sources.md`. No single-source facts in the manuscript.

5. **Capture period-specific details.** The research phase specifically targets:
   - Currency and prices (what things cost, wages, purchasing power)
   - Transportation and travel times (how long to get from A to B by available methods)
   - Food, drink, and dining customs
   - Clothing and fashion (what people actually wore, not costume-drama fantasy)
   - Social hierarchy and forms of address
   - Legal systems and law enforcement
   - Medicine and health (what was known, what was not, common ailments)
   - Communication methods (mail, telegraph, telephone -- what existed when)
   - Architecture and living conditions
   - Occupations and daily routines

6. **Organize research notes.** All findings go into `research/notes/` as structured Markdown or YAML files, organized by topic.

### Git Workflow

Research is conducted on branches prefixed `research/`. For example, `research/1920s-maritime` or `research/prohibition-era-chicago`. These branches are merged to `main` when the research phase completes.

### Output Artifacts

- `research/historical_timeline.yaml`
- `research/sources.md`
- `research/notes/*.md`

---

## Phase 3: Design

The design phase transforms a pitch and research into a complete novel blueprint.

### Steps

1. **One-sentence premise.** Distill the entire novel into a single sentence that captures the protagonist, conflict, and stakes.

2. **One-paragraph synopsis.** Expand the premise into a paragraph that includes the setup, rising action, crisis, climax, and resolution.

3. **Full synopsis.** Write a 2-3 page synopsis covering the complete plot, all major characters, and the thematic arc.

4. **Character design.** Create full character profiles using `templates/character_sheet.yaml` for every named character. Profiles include physical description, backstory, motivation, arc, speech patterns, relationships, and the specific function each character serves in the plot.

5. **Seven-Layer Narrative Architecture.** Apply the custom structural framework (see `docs/story_structure.md`):
   - **Layer 1 — Thematic Engine**: Define the Thematic Question, Controlling Idea, Counter-Idea, and Four Throughlines (Overall Story, Main Character, Influence Character, Relationship)
   - **Layer 2 — Character Architecture**: Ghost, Lie, Need (psychological + moral), Want, Truth, Arc Type for each major character
   - **Layer 3 — Five Movements**: Map the novel's global arc — Establishment (~20%), Deepening (~20%), Complication (~25%), Revelation & Reckoning (~20%), Aftermath (~15%)
   - **Layer 4 — Sequence Architecture**: Divide into 8-12 sequences, each with its own dramatic question and Five Commandments (Inciting Incident → Complication → Crisis → Climax → Resolution)

6. **Multi-level outline.** Build the outline from the top down:
   - **Series arc** (if applicable): How this book fits into the larger series
   - **Novel arc**: Five Movements mapped to parts and chapters, with Four Throughlines tracked
   - **Part arcs**: 3-4 parts, each corresponding to one or more movements
   - **Chapter outlines**: What happens, whose POV, where, when, value shift, which throughlines advance
   - **Scene outlines**: Using `templates/scene_outline.yaml`, detailed Five Commandments with page estimates

7. **Story bible.** Compile all characters, locations, relationships, timeline entries, and world rules into YAML files. The story bible is the single source of truth for facts about the fictional world.

8. **Voice guide.** Write sample paragraphs that demonstrate the target prose style, and document the voice rules in `style/voice_guide.md`.

9. **Word count targets.** Set targets at every level: novel total, per part, per chapter, per scene. Standard target is ~80,000 words for a historical fiction novel (~320 pages at 250 words/page).

### Git Workflow

Design work happens on branches prefixed `outline/`. For example, `outline/part-1` or `outline/character-design`. These merge to `main` when the design phase completes.

### Output Artifacts

- `outline.md` (the multi-level outline)
- `book_bible.yaml` (characters, locations, timeline, world rules)
- `style/voice_guide.md`
- `style/style_rules.md`

---

## Phase 4: Writing

The writing phase produces the first draft, one page at a time, one chapter per git branch.

### Chapter-Level Workflow

1. **Create a writing branch.** Branch naming: `write/part-{N}/chapter-{NN}`. Example: `write/part-1/chapter-03`.

2. **Write each scene in order.** Scenes within the chapter are written sequentially. Each scene comprises multiple pages.

3. **After each scene completes:**
   - Run `scripts/consistency_checker.py` against the story bible
   - Run `scripts/manuscript_stats.py` to verify word count
   - Update `progress.md` via `scripts/progress_tracker.py`

4. **After all scenes in the chapter are complete:**
   - Push the branch to the remote
   - Create a pull request with chapter summary, word count stats, and consistency check results
   - The Claude GitHub App reviews the PR
   - Address review comments on the same branch
   - Merge to `main` when approved

5. **Update the outline if needed.** If the chapter deviated from the plan, update downstream outline entries before starting the next chapter.

### Page-Level Workflow

See [The Page-by-Page Writing Process](#the-page-by-page-writing-process) below for the detailed per-page process.

### The Overwrite Target

First draft pages target 120-130% of the final word count. A page targeting 250 final words should be written at 300-325 words in the first draft. The excess is trimmed during editing. See [The Overwrite-Then-Cut Approach](#the-overwrite-then-cut-approach) for the rationale.

---

## Phase 5: Editing

The editing phase refines the first draft through four distinct passes, each with a different focus.

### Pass 1: Developmental Edit

**Focus**: Story structure, pacing, character arcs, plot logic.

This pass is conducted primarily through the PR review process. The Claude GitHub App reviews each chapter PR with developmental questions:
- Does the chapter advance the plot meaningfully?
- Are character motivations consistent with their established profiles?
- Is the pacing appropriate (no sagging middle, no rushed climax)?
- Do subplots receive adequate attention?
- Are there any plot holes or logic gaps?

Issues identified in this pass may require significant rewrites of entire scenes.

### Pass 2: Line Edit

**Focus**: Prose quality, voice consistency, sentence variety, imagery.

An editor agent reviews the manuscript page by page, checking:
- Sentence length variation (short/medium/long alternation)
- Paragraph opening variety (no consecutive paragraphs starting with the same word)
- Banned word detection (AI-tell words like "delve," "tapestry," "nuanced")
- Show-vs-tell violations (emotions stated directly instead of shown through action)
- Dialogue tag distribution (70% "said," 25% action beats, 5% other)
- Metaphor and imagery freshness (no repeats from earlier chapters)
- Period-appropriate language (no anachronisms)

### Pass 3: Copy Edit

**Focus**: Grammar, spelling, period accuracy, factual consistency.

This pass combines automated and LLM-based checking:
- `scripts/consistency_checker.py` validates all character facts, timeline entries, and travel times against the story bible
- An editor agent reviews for grammatical errors, spelling, and punctuation
- Historical details are cross-referenced against `research/` notes
- Character speech patterns are verified against their character sheets

### Pass 4: Final Polish

**Focus**: Rhythm, flow, word count targets, final cuts.

The final pass is the read-aloud pass. The editor agent reviews each page for:
- Sentence rhythm when read aloud
- Final word count adherence (cutting to target)
- Last opportunities for tightening
- Consistent formatting and scene break markers

All material cut during editing passes is preserved in the `cuts/` directory. See [The Overwrite-Then-Cut Approach](#the-overwrite-then-cut-approach).

### Git Workflow for Editing

Each editing pass operates on its own branch:
- `edit/dev-edit/chapter-01`
- `edit/line-edit/chapter-01`
- `edit/copy-edit/chapter-01`
- `edit/final/chapter-01`

Each branch produces a PR that is reviewed before merging. This creates an auditable trail of every editorial change.

---

## Phase 6: Publication

The publication phase transforms the finished manuscript into distributable formats.

### Steps

1. **Build EPUB and PDF.** Run `scripts/build_manuscript.sh` to generate reader-ready files via pandoc. See `docs/publishing.md` for full details.

2. **Generate cover art.** Use the OpenAI GPT Image 1.5 API or Flux 2 Pro via Replicate to generate cover art. Iterate on prompts until the cover matches the tone and period of the novel.

3. **Create the GitHub Pages site.** Set up a Jekyll or Hugo site for the novel with synopsis, sample chapters, and download links.

4. **Upload to distribution platforms.** Submit the EPUB to Amazon KDP, Draft2Digital, and other platforms. Submit the print-ready PDF to KDP Print and/or IngramSpark.

5. **Generate the audiobook.** Use the ElevenLabs API to produce chapter-by-chapter audio narration. See `docs/publishing.md` for production details.

6. **Distribute the audiobook.** Upload to Voices by INaudio, Kobo, and other platforms that accept AI-narrated audiobooks.

---

## Git Workflow and Worktrees

### Branch Strategy

The repository uses a structured branching scheme where branch prefixes indicate the type of work:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `main` | Published/approved content only | -- |
| `framework/` | Infrastructure improvements | `framework/add-consistency-checker` |
| `research/` | Research branches | `research/1920s-maritime` |
| `outline/` | Outline development | `outline/part-2-chapters` |
| `write/` | Writing branches (one chapter per branch) | `write/part-1/chapter-03` |
| `edit/` | Editing branches (one pass per branch) | `edit/line-edit/chapter-03` |

### Git Worktrees

Git worktrees allow multiple branches to be checked out simultaneously in separate directories. This is particularly useful during the editing phase, when you may need to reference the `main` branch (clean, merged content) while working on an editing branch.

Typical worktree setup:

```bash
# Main checkout (the primary working directory)
/Users/bedwards/writing/historical-fiction-novel/        # main branch

# Worktree for active writing
git worktree add ../novel-writing write/part-1/chapter-05

# Worktree for editing a different chapter
git worktree add ../novel-editing edit/line-edit/chapter-03
```

Worktrees share the same `.git` directory, so all branches, commits, and history are shared. This avoids the need to stash or commit incomplete work when switching contexts.

### Commit Convention

```
type(scope): description

Types: research, outline, write, edit, fix, style, build, docs, framework
Scope: series name, book name, part/chapter, or script name
```

Examples:
```
write(tides/ch03): complete scene 2 - the harbor confrontation
edit(tides/ch01): line editing pass - tighten dialogue
framework(scripts): add consistency checker travel time validation
research(1920s-maritime): add shipping route data
```

Commits happen frequently. Every page of prose is committed individually. Every scene completion, every consistency check result, every progress update is committed. The commit history should tell the full story of how the novel was built.

---

## The Page-by-Page Writing Process

Each page of the novel (~250 words) is produced through a structured assembly and dispatch process.

### Step 1: Context Assembly

The orchestrator builds a 7-layer prompt for the writer agent. Each layer is curated for the specific page being written:

| Layer | Content | Budget |
|-------|---------|--------|
| 1 | System prompt and voice rules | ~2,500 tokens (10%) |
| 2 | Story bible excerpt (characters and locations in this scene only) | ~4,000 tokens (16%) |
| 3 | Scene outline (beats for this scene) | ~750 tokens (3%) |
| 4 | Previous 3-5 pages (raw text) | ~5,000 tokens (20%) |
| 5 | Chapter summary (compressed) | ~1,500 tokens (6%) |
| 6 | Narrative summary (story so far, compressed) | ~1,250 tokens (5%) |
| 7 | Writing instruction (specific direction for this page) | ~500 tokens (2%) |

Total input: ~15,500 tokens (62% of budget). Remaining ~10,000 tokens (38%) are reserved for the model's output (thinking + prose).

**Critical rule**: Only include story bible entries for characters and locations that appear in the current scene. Never dump the entire bible into the context.

### Step 2: Dispatch Writer Agent

The assembled prompt is sent to a background writer agent. The agent produces approximately 250 words of prose plus any internal reasoning.

### Step 3: Review Output

The orchestrator reviews the returned page for:
- Adherence to the scene outline
- Consistency with the previous page (smooth continuation)
- Compliance with style rules (no banned words, proper sentence variety)
- Word count within target range

### Step 4: Editor Dispatch (if needed)

If the page has issues that can be fixed through editing rather than rewriting, an editor agent is dispatched with the page and specific instructions for improvement.

### Step 5: Update Continuity Notes

After each page is finalized, the orchestrator updates `continuity/rolling_notes.md` with any new information introduced on that page. See [The Continuity Notes System](#the-continuity-notes-system).

### Step 6: Commit

The page is appended to the appropriate scene file and committed:
```
write(tides/ch03): page 7 - Elena discovers the letter
```

### Step 7: Scene and Chapter Boundaries

- **After each scene completes**: Run `scripts/consistency_checker.py`, update `progress.md`.
- **After each chapter completes**: Push branch, create PR, trigger Claude GitHub App review.

---

## The Multi-Pass Editing Process

Editing is not a single activity. It is four distinct activities performed in order, each with its own branch and PR.

### Pass 1: Developmental Edit

**What it examines**: The big picture. Does the story work?

- Plot structure: Does the chapter fulfill its role in the novel arc?
- Character arcs: Are characters growing, changing, or revealing new facets?
- Pacing: Is the chapter the right length for its content? Does it drag or rush?
- Stakes: Are the stakes clear and escalating appropriately?
- Subplots: Are they advancing without overshadowing the main plot?

**How it works**: The developmental edit is primarily conducted through the PR review process. The Claude GitHub App reviews the chapter-level PR and leaves comments on structural issues. The orchestrator addresses these comments, potentially rewriting entire scenes.

### Pass 2: Line Edit

**What it examines**: The prose itself. Is the writing good?

- Sentence variety: Mix of short, medium, and long sentences
- Word choice: Precise, period-appropriate, concrete
- Voice consistency: Does it sound like the same narrator throughout?
- Show vs. tell: Emotions shown through action and sensation, not stated
- Dialogue: Natural, distinctive per character, properly tagged
- Imagery: Fresh metaphors drawn from the period and setting
- Banned patterns: No AI-tell words, no cliches, no forbidden constructions

**How it works**: An editor agent reviews the manuscript page by page with `style/style_rules.md` and `style/voice_guide.md` loaded into context. Edits are made on the `edit/line-edit/chapter-{NN}` branch.

### Pass 3: Copy Edit

**What it examines**: Correctness. Are the facts right?

- Grammar and punctuation
- Spelling (including period-appropriate spellings)
- Historical accuracy against research notes
- Character fact consistency (physical descriptions, ages, relationships)
- Timeline consistency (no accidental anachronisms in the plot)
- Geography and travel time consistency

**How it works**: This pass combines Python script validation (`scripts/consistency_checker.py`) with LLM-based review. The scripts catch mathematical and factual errors; the LLM catches semantic and contextual errors.

### Pass 4: Final Polish

**What it examines**: Rhythm and finish. Does it sound right read aloud?

- Sentence rhythm and cadence
- Word count adherence to targets
- Final tightening opportunities
- Consistent formatting (scene breaks, chapter headings, dialogue formatting)
- Any remaining cuts needed to hit the target word count

**How it works**: The editor agent reads each page with attention to how it sounds, not just what it says. Final cuts are made to bring the manuscript within 2% of the target word count.

---

## Pull Requests as Editorial Checkpoints

Every chapter passes through a pull request before it joins the main manuscript. PRs serve as editorial checkpoints with several functions:

### What the PR Contains

- **Title**: Chapter number and title
- **Description**: A summary of what happens in the chapter, written by the orchestrator
- **Statistics**: Word count, page count, reading time (from `scripts/manuscript_stats.py`)
- **Consistency report**: Output of `scripts/consistency_checker.py`
- **Self-assessment**: The orchestrator's evaluation of the chapter's quality and any known issues

### What the PR Review Covers

The Claude GitHub App reviews the PR using the checklist in `templates/review_checklist.md`. Review comments are posted as inline annotations on specific lines of the manuscript, just as a human editor would mark up a document.

### The Review-Revise Cycle

1. PR is created with the chapter draft.
2. Claude GitHub App reviews and posts comments.
3. The orchestrator reads the comments and dispatches editor agents to address them.
4. Changes are committed and pushed to the same branch.
5. A new review cycle is triggered by the push.
6. This continues until the reviewer approves or the orchestrator makes a judgment call to merge.

### Why PRs Work for Fiction

PRs provide:
- **A permanent record** of editorial feedback and how it was addressed
- **Atomic chapter merges** to the main manuscript
- **A gating mechanism** that prevents unreviewed content from reaching `main`
- **Diff-based review** that highlights exactly what changed between revisions
- **Discussion threads** for debating specific editorial choices

---

## Claude GitHub App as Editorial Reviewer

The Claude GitHub App (via `.github/workflows/claude-review.yml`) acts as an automated editorial reviewer on every manuscript PR.

### How It Works

1. A PR is opened or updated with changes to files in the `series/` directory.
2. The GitHub Actions workflow triggers the Claude Code Action.
3. Claude receives a custom editorial review prompt along with the `templates/review_checklist.md` checklist.
4. Claude reviews the changed manuscript files and posts inline comments.

### What Claude Reviews

The editorial review prompt instructs Claude to evaluate:

- **Plot consistency**: Do events align with established facts and previous chapters?
- **Character voice**: Does each character sound distinct and consistent with their profile?
- **Historical accuracy**: Are period details correct for the setting?
- **Pacing**: Does the chapter maintain appropriate momentum?
- **Dialogue quality**: Is dialogue natural, purposeful, and character-specific?
- **Show vs. tell**: Are emotions and states shown through action rather than stated?
- **Cliche detection**: Are there tired phrases, predictable turns, or lazy descriptions?
- **Sentence variety**: Is there appropriate variation in sentence length and structure?
- **Emotional authenticity**: Do character reactions feel genuine and earned?

### Review Configuration

- **Max turns**: 5 (Claude can take up to 5 reasoning steps per review)
- **Trigger**: Only on changes to files in `series/` (manuscript content)
- **Authentication**: Uses `ANTHROPIC_API_KEY` from repository secrets

---

## Progress Tracking

### How progress.md Works

Each book has a `progress.md` file that is auto-generated by `scripts/progress_tracker.py`. This file is never edited manually. It is regenerated after every scene completion.

### What It Tracks

- **Overall status**: Current draft phase, total word count vs. target, page count, reading time estimate, chapter completion count.
- **Per-part status**: Each part's completion percentage and average quality grade.
- **Per-chapter status**: Scene count, word count, draft status, and quality grade.
- **Per-scene detail**: Page count, word count, status, and individual grade.

### Quality Grades

Grades are on a 0-100 scale:

| Range | Meaning |
|-------|---------|
| 0-39 | Needs complete rewrite |
| 40-59 | Major issues (plot holes, flat characters, inconsistencies) |
| 60-74 | Solid draft, needs editing |
| 75-84 | Good quality, minor polish needed |
| 85-94 | Publication ready with minor tweaks |
| 95-100 | Exceptional |

### When It Updates

- After every scene completion (during writing)
- After every editing pass completion
- On demand when requested

---

## Consistency Checking

The system uses two complementary approaches to consistency checking: deterministic Python scripts for quantifiable facts, and LLM-based review for semantic and narrative consistency.

### Python Scripts (Trust These for Math)

`scripts/consistency_checker.py` validates:

- **Character ages**: Given a character's birth date and the current story date, verify that any stated age is correct.
- **Relationship durations**: "Married for twelve years" must match the wedding date in the story bible.
- **Travel times**: A journey from London to Edinburgh by train in 1925 takes approximately 8-10 hours. The script flags impossible travel times.
- **Character presence**: Is the character alive at this point in the story? Are they in the right location to appear in this scene?
- **Physical descriptions**: Eye color, hair color, height, scars, and other physical details must match the story bible across all appearances.
- **Timeline ordering**: Events must occur in chronological order. No accidental time travel.
- **Word count targets**: Verify that scenes, chapters, and parts are within acceptable range of their targets.

These scripts compare the manuscript text against the structured YAML data in the story bible. They produce reports listing every discrepancy found, with file and line references.

**Why scripts, not LLMs?** LLMs are unreliable at arithmetic, date math, and cross-referencing large structured datasets. A Python script that computes "character was born in 1892, story date is 1925, so character is 32 or 33" is correct every time. An LLM might say 31 or 34.

### LLM-Assisted Review (Trust These for Semantics)

The editor agent performs semantic consistency checks that require understanding narrative context:

- **Motivation consistency**: Does this character's action in chapter 12 align with their established motivations and the pressure they are under?
- **Tone and voice consistency**: Has the narrative voice shifted inadvertently between chapters?
- **Foreshadowing and Chekhov's Gun tracking**: Was the gun on the mantelpiece in chapter 3 ever fired? Was the hint in chapter 7 ever paid off?
- **Pacing analysis**: Is the story accelerating toward the climax appropriately, or has it stalled?
- **Dialogue authenticity**: Would this character actually say this, in this way, in this period?

### When Checks Run

- After every scene completion: full consistency check
- Before every PR: full consistency check with report included in the PR description
- On demand: any time the orchestrator suspects an issue

---

## The Overwrite-Then-Cut Approach

### The Principle

Every first draft is written at 120-130% of the target word count. A scene targeting 1,250 words (5 pages) is written at 1,500-1,625 words. The excess is then trimmed during editing.

### Why Overwrite?

1. **It is easier to cut good material than to add it.** When a draft is too short, padding it requires inventing new content that often feels forced and tangential. When a draft is too long, cutting the weakest material raises the average quality of what remains.

2. **It produces tighter prose.** The act of cutting forces the editor to evaluate every sentence: does this earn its place? Sentences that survive the cut are there because they are necessary, not because they filled space.

3. **It builds the cuts directory.** Material removed during editing is not deleted. It is moved to the `cuts/` directory (the "darling graveyard"). This material may be repurposed later -- a cut paragraph from chapter 3 might be exactly what chapter 18 needs.

4. **It reduces anxiety about word count.** The writer agent does not need to worry about hitting an exact target. It writes freely, knowing that the editing phase will sculpt the material to the right length.

### How It Works in Practice

1. **During writing**: The orchestrator tells the writer agent the scene's target word count inflated by 25%. A 5-page scene (1,250 words) is assigned a 1,563-word target.
2. **During Pass 2 (line edit)**: The editor agent identifies the weakest sentences, paragraphs, and passages.
3. **During Pass 4 (final polish)**: The manuscript is trimmed to within 2% of the target word count.
4. **Cut material is preserved**: Every cut paragraph is saved to `cuts/{chapter}/` with a note about why it was cut and where it came from.

---

## The Continuity Notes System

### What Are Continuity Notes?

Continuity notes are a rolling record of every narratively significant detail introduced in the manuscript. They live in `continuity/rolling_notes.md` and are updated after every single page.

### Why Rolling Notes?

The writer agent's context window cannot hold the entire manuscript. When writing page 237, the agent has no direct access to what happened on page 14. Continuity notes serve as compressed memory, allowing the agent to maintain consistency across hundreds of pages without needing to load the full text.

### What Gets Recorded

After each page, the orchestrator scans the new content and records:

- **New character details**: Any physical description, backstory revelation, habit, or personality trait mentioned for the first time.
- **Relationship changes**: New relationships formed, existing relationships altered, betrayals, alliances.
- **Plot developments**: Events that change the state of the story world.
- **Promises and commitments**: Characters promising to do something, making plans, setting up future events.
- **Objects introduced**: Significant objects (letters, weapons, heirlooms) that may reappear.
- **Location details**: New descriptions of places that must remain consistent on future visits.
- **Time markers**: Explicit references to dates, seasons, days of the week, or durations.

### Structure of Rolling Notes

```markdown
## Chapter 3: The Harbor

### Page 1
- Elena arrives at the harbor at dawn. She is wearing her gray wool coat (first mention).
- The harbor smells of tar and salt fish (sensory baseline for this location).
- She is looking for the cargo manifest from the SS Adriatic.

### Page 2
- The harbormaster is Aldo Ferretti, mid-50s, heavy build, tobacco-stained fingers.
- Aldo recognizes Elena's surname and becomes guarded.
- First hint that Elena's father had dealings at this harbor.
```

### How Notes Feed into Writing Context

When assembling the prompt for a new page, the orchestrator includes relevant entries from the rolling notes in Layer 6 (narrative summary). The notes are compressed and filtered to include only information relevant to the current scene and its characters.

### Chapter Summaries

In addition to per-page rolling notes, the system maintains `continuity/chapter_summaries.md`, which contains a 200-300 word summary of each completed chapter. These summaries are more compressed than the rolling notes and are used when the writer agent needs awareness of the full story arc without page-level detail.

---

## Handling Narrative Deviations

### What Is a Narrative Deviation?

A narrative deviation occurs when the writer agent produces prose that diverges from the scene outline in a meaningful way. Examples:

- A character makes a decision the outline did not anticipate.
- A conversation reveals information that was planned for a later scene.
- A new minor character emerges organically from the setting.
- The emotional tone of a scene shifts from what was planned.
- A subplot develops an unexpected connection to the main plot.

### The Decision Framework

When a deviation is detected, the orchestrator evaluates it:

1. **Is it better than the plan?** If the deviation produces more interesting, authentic, or emotionally resonant storytelling, accept it and update the plan.

2. **Is it neutral?** If the deviation is different but not clearly better or worse, accept it if it does not create downstream problems. Update the plan.

3. **Is it worse than the plan?** If the deviation weakens the story (introduces a plot hole, undermines character development, derails pacing), reject the page and re-dispatch the writer agent with clarified instructions.

4. **Does it create downstream conflicts?** Even a good deviation may conflict with planned events in later chapters. The orchestrator must trace the implications forward and update all affected outline entries.

### The Update Process

When a deviation is accepted:

1. **Update the scene outline** for the current scene to reflect what actually happened.
2. **Review downstream scene outlines** in the same chapter. Adjust as needed.
3. **Review downstream chapter outlines** in the same part. Adjust as needed.
4. **Review the novel-level Five Movements and Sequence Architecture** if the deviation affects major structural beats or throughlines.
5. **Update the story bible** if the deviation introduces new facts about characters, locations, or the world.
6. **Update continuity notes** to record the deviation and the new direction.
7. **Commit the outline changes** with a clear commit message:
   ```
   outline(tides/ch07): update scenes 3-5 after Elena's early confession
   ```

### The Living Outline Principle

The outline is always the plan for what comes next, updated to reflect what has actually been written. At no point should the outline describe events that contradict what has already been committed to the manuscript. The outline leads the writing, but the writing can redirect the outline.

This is the core of the Dynamic Plotter: the plan is authoritative until the story tells you otherwise, at which point the plan adapts.
