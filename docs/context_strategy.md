# Context Window Strategy

This document describes how the Historical Fiction Novel Factory manages Claude's context window to produce consistent, high-quality prose across a full-length novel. Context management is arguably the most important technical challenge in LLM-assisted long-form writing: the entire manuscript will never fit in the context window, so what you include -- and what you leave out -- determines the quality of every page.

---

## Table of Contents

1. [Model Specifications](#model-specifications)
2. [The 7-Layer Writing Prompt Architecture](#the-7-layer-writing-prompt-architecture)
3. [The Editing Prompt Architecture](#the-editing-prompt-architecture)
4. [Why ~25K Tokens Is the Sweet Spot](#why-25k-tokens-is-the-sweet-spot)
5. [The 3-5 Page Rule for Surrounding Context](#the-3-5-page-rule-for-surrounding-context)
6. [Why Smaller Curated Context Outperforms Larger Unfocused Context](#why-smaller-curated-context-outperforms-larger-unfocused-context)
7. [Rolling Continuity Notes Strategy](#rolling-continuity-notes-strategy)
8. [Token Cost Estimates for a Full Novel](#token-cost-estimates-for-a-full-novel)
9. [Prompt Caching for Static Components](#prompt-caching-for-static-components)

---

## Model Specifications

The system uses **Claude Opus 4.6**, Anthropic's most capable model for creative writing tasks.

| Specification | Value |
|--------------|-------|
| Standard context window | 200,000 tokens |
| Extended context (beta) | 1,000,000 tokens |
| Maximum output tokens | 128,000 tokens |
| Input token cost | $15 per million tokens |
| Output token cost | $75 per million tokens |
| Prompt caching (write) | $18.75 per million tokens |
| Prompt caching (read) | $1.50 per million tokens |

**Why Opus 4.6 for fiction writing?** Opus is Anthropic's strongest model for tasks requiring nuanced language, deep contextual understanding, and creative expression. Compared to Sonnet or Haiku, Opus produces prose with greater sentence variety, more sophisticated metaphor, better character voice differentiation, and fewer AI-tell patterns. For a task where prose quality is paramount, the cost difference is justified.

**Why not use the full 200K window?** While the model can process 200K tokens, filling the context window does not improve output quality for creative writing. See [Why Smaller Curated Context Outperforms Larger Unfocused Context](#why-smaller-curated-context-outperforms-larger-unfocused-context).

---

## The 7-Layer Writing Prompt Architecture

Every page of the novel is generated using a structured prompt composed of seven distinct layers. Each layer serves a specific purpose and has a defined token budget.

### Layer 1: System Prompt and Voice Rules (~2,500 tokens, 10%)

**Purpose**: Establish the writer agent's identity, constraints, and stylistic rules.

**Contents**:
- Role definition: "You are a literary fiction writer specializing in historical fiction."
- Voice rules from `style/voice_guide.md` (condensed)
- Anti-pattern rules from `style/style_rules.md` (banned words, structural requirements)
- Output format instructions (prose only, no commentary)
- Sentence variety requirements
- Show-don't-tell mandate

**Why it matters**: This layer sets the ceiling for prose quality. Without explicit anti-pattern rules, the model falls into AI-tell habits (starting paragraphs with "The," using "delve" and "tapestry," telling emotions instead of showing them). These rules are the most important 2,500 tokens in the entire prompt.

### Layer 2: Story Bible Excerpt (~4,000 tokens, 16%)

**Purpose**: Provide the factual foundation for this specific scene.

**Contents**:
- Character sheets for characters who appear in this scene (and only those characters)
- Location details for the scene's setting
- Relevant relationship dynamics
- Any world rules that apply (social customs, power structures, etc.)
- Historical context specific to the scene's time period and events

**Critical rule**: Only include story bible entries relevant to the current scene. The full story bible for a novel may be 20,000+ tokens. Dumping it all in wastes context budget on irrelevant information and dilutes the model's attention on what actually matters.

**Example**: If the scene takes place in a harbor between Elena and Aldo, include Elena's character sheet, Aldo's character sheet, the harbor location sheet, and the relevant section of the historical timeline. Do not include character sheets for characters who are elsewhere in the story.

### Layer 3: Scene Outline (~750 tokens, 3%)

**Purpose**: Give the writer agent the structural plan for the current scene.

**Contents**:
- The scene's beats (what needs to happen)
- Emotional arc for the scene (where characters start and end emotionally)
- Key information to be revealed or withheld
- Sensory atmosphere notes
- Connection to surrounding scenes (what leads into this scene, what this scene sets up)

**Why it is compact**: The scene outline is a guide, not a script. Providing too much detail makes the prose feel mechanical. The outline should tell the writer what needs to happen and how the characters should feel, then let the writer find the words.

### Layer 4: Previous 3-5 Pages (~5,000 tokens, 20%)

**Purpose**: Provide immediate narrative continuity.

**Contents**:
- The raw text of the 3-5 pages immediately preceding the page being written
- Scene break markers if the preceding pages include a scene transition

**Why raw text (not summaries)**: The writer agent needs to match the exact tone, rhythm, and voice of what came immediately before. A summary loses the specific word choices, sentence patterns, and atmospheric details that make the prose feel continuous. The transition from page N to page N+1 must be seamless, and that requires the model to "hear" the actual prose, not a description of it.

**Why 3-5 pages (not more)**: See [The 3-5 Page Rule](#the-3-5-page-rule-for-surrounding-context).

### Layer 5: Chapter Summary (~1,500 tokens, 6%)

**Purpose**: Provide chapter-level context without consuming excessive tokens.

**Contents**:
- A compressed summary of everything that has happened in the current chapter so far
- Key emotional beats
- Unresolved tensions or open questions from earlier in the chapter
- Character positions (who is where, what do they know)

**Why compressed**: The chapter may be 15-25 pages. Including all of it as raw text would consume 15,000-25,000 tokens, which is the entire budget. A 1,500-token summary captures the essential information at roughly 10:1 compression.

### Layer 6: Narrative Summary (~1,250 tokens, 5%)

**Purpose**: Provide the "story so far" -- everything that has happened in the novel before this chapter.

**Contents**:
- Compressed summaries of all preceding chapters
- Major plot developments
- Character arc progression
- Unresolved foreshadowing
- Relevant entries from `continuity/rolling_notes.md`

**Why this is small**: By the time the novel is 200 pages in, the "story so far" could be an enormous document. But the writer agent does not need to know everything -- it needs to know what is relevant to the current scene. The orchestrator curates this summary to include only information that the current page might reference or build upon.

### Layer 7: Writing Instruction (~500 tokens, 2%)

**Purpose**: Specific direction for this individual page.

**Contents**:
- What should happen on this page (derived from the scene outline)
- Any specific beats to hit
- Tone guidance (if this page is a shift from the preceding tone)
- Word count target (typically ~250 words, or ~300-325 for overwrite target)
- Any special requirements (introduce a new character, reveal specific information, end on a cliffhanger)

**Why it is last**: The writing instruction is placed at the end of the prompt, closest to where the model begins generating. This ensures the specific instructions for this page are freshest in the model's attention.

### Total Budget

```
Layer 1: System + Voice Rules        ~2,500 tokens   10%
Layer 2: Story Bible Excerpt          ~4,000 tokens   16%
Layer 3: Scene Outline                  ~750 tokens    3%
Layer 4: Previous 3-5 Pages           ~5,000 tokens   20%
Layer 5: Chapter Summary              ~1,500 tokens    6%
Layer 6: Narrative Summary            ~1,250 tokens    5%
Layer 7: Writing Instruction            ~500 tokens    2%
────────────────────────────────────────────────────────
Total Input                          ~15,500 tokens   62%
Reserved for Output                  ~5,000-10,000   38%
────────────────────────────────────────────────────────
Grand Total                            ~25,000 tokens
```

The remaining 175K tokens of the 200K context window are intentionally unused. This is by design.

---

## The Editing Prompt Architecture

The editing prompt follows a different structure than the writing prompt, because the task is different: evaluation and revision rather than generation.

### Layer 1: Style Rules and Review Checklist (~3,000 tokens)

**Contents**:
- The full `style/style_rules.md` (banned words, structural requirements, dialogue tag ratios)
- The relevant section of `templates/review_checklist.md`
- Specific instructions for this editing pass (developmental, line, copy, or final)

### Layer 2: Story Bible Excerpt (~3,000 tokens)

**Contents**:
- Character sheets for characters in the scene under review
- Location details
- Relevant timeline entries
- Historical facts that should be verified

### Layer 3: The Page Under Review (~500 tokens)

**Contents**:
- The exact text of the page being edited

### Layer 4: Surrounding Context (~2,000 tokens)

**Contents**:
- 2 pages before the page under review
- 2 pages after the page under review (if they exist)

**Why surrounding context**: The editor needs to evaluate transitions, consistency, and flow. A page cannot be evaluated in isolation -- it must make sense in the context of what comes before and after.

### Layer 5: Scene Outline and Chapter Context (~1,000 tokens)

**Contents**:
- The scene outline (what was supposed to happen)
- Chapter-level context (where this page fits in the chapter's arc)

### Layer 6: Editing Instructions (~500 tokens)

**Contents**:
- Specific focus areas for this page
- Known issues to look for
- Permission to suggest significant changes (for developmental edit) or only surface changes (for copy edit)

### Total Editing Budget

```
Layer 1: Style Rules + Checklist     ~3,000 tokens
Layer 2: Story Bible Excerpt          ~3,000 tokens
Layer 3: Page Under Review              ~500 tokens
Layer 4: Surrounding Context          ~2,000 tokens
Layer 5: Outline + Chapter Context    ~1,000 tokens
Layer 6: Editing Instructions           ~500 tokens
────────────────────────────────────────────────────
Total Input                          ~10,000 tokens
Reserved for Output                  ~5,000-10,000
────────────────────────────────────────────────────
Grand Total                          ~15,000-20,000 tokens
```

Editing prompts are smaller than writing prompts because the task is more focused: evaluate one page against known criteria, rather than generate new prose that must cohere with the entire narrative.

---

## Why ~25K Tokens Is the Sweet Spot

The 25,000-token total budget (15,500 input + ~10,000 output) is not arbitrary. It emerges from several converging factors:

### 1. Attention Quality Degrades with Context Length

Language models process context through attention mechanisms. While Claude can handle 200K tokens, the model's attention is not uniformly distributed across all tokens. Information in the middle of a very long context receives less attention than information at the beginning or end (the "lost in the middle" phenomenon). By keeping the total context compact, every token in the prompt receives strong attention.

### 2. More Context Means More Noise

A 200K-token prompt for a single page of prose would include enormous amounts of information irrelevant to that specific page. The model must then distinguish signal from noise, and inevitably some noise leaks into the output. A character detail from chapter 2 that is irrelevant to the current scene in chapter 15 might nevertheless influence word choices or thematic elements if it is present in the context.

### 3. Output Quality Is Best in the 1,000-5,000 Token Range

For creative writing, the model produces its best work when generating 1,000-5,000 tokens at a time. Longer generations tend to lose coherence, repeat patterns, or drift from the initial tone. A single page (~250 words, ~350 tokens of prose) is comfortably within this range.

### 4. Cost Efficiency

At $15/million input tokens and $75/million output tokens:
- A 25K-token call costs approximately $0.23 for input + $0.75 for output = ~$0.98
- A 200K-token call would cost approximately $3.00 for input + $0.75 for output = ~$3.75

The 25K approach is 4x cheaper per page with equal or better output quality.

### 5. Speed

Smaller prompts process faster. Time-to-first-token and total generation time both increase with context length. For a 320-page novel, the cumulative time savings of compact prompts is substantial.

---

## The 3-5 Page Rule for Surrounding Context

### The Rule

When writing page N, include the raw text of pages N-3 through N-1 (minimum) to N-5 through N-1 (maximum) as context.

### Why 3 Pages Minimum

Three pages (~750 words) is the minimum needed for the model to:
- Match the current sentence rhythm and paragraph structure
- Continue any in-progress dialogue naturally
- Maintain the atmospheric tone established in the preceding pages
- Avoid repeating a phrase or image that was used 2 pages ago

With fewer than 3 pages, the model lacks enough "voice memory" and may produce prose that feels discontinuous with what came before.

### Why 5 Pages Maximum

Beyond 5 pages (~1,250 words), the additional context provides diminishing returns:
- Pages 6+ ago are far enough back that the chapter summary covers them adequately
- The token cost of raw text is high (~1,000 tokens per page)
- Older pages may contain scene transitions or tonal shifts that no longer apply

### Adjusting the Window

The 3-5 range is a guideline, not a rule. The orchestrator adjusts based on:

- **Scene openings**: At the start of a new scene, include only 1-2 pages (or none if it is the chapter's first scene), plus the scene outline. The model needs a fresh start, not carryover from the previous scene's tone.
- **Long dialogue sequences**: Expand to 5 pages to maintain the full conversational thread.
- **Action sequences**: 3 pages is usually sufficient; action scenes have shorter paragraphs and faster pacing.
- **Emotional climaxes**: Expand to 5 pages to preserve the emotional buildup.

---

## Why Smaller Curated Context Outperforms Larger Unfocused Context

This is the central insight of the context strategy: **what you leave out matters as much as what you include.**

### The Information Overload Problem

Imagine asking a novelist to write the next page of their novel. In scenario A, you hand them the last 3 pages and a brief reminder of the scene plan. In scenario B, you hand them the entire manuscript, all their research notes, every character biography, and every version of the outline. In scenario B, the novelist spends most of their cognitive effort figuring out what is relevant rather than writing. The quality of the next page does not improve -- it may actually decrease because of decision fatigue.

LLMs behave similarly. Given an enormous context, the model must attend to all of it when generating each token. Irrelevant information creates noise in the attention patterns, which can manifest as:

- **Thematic drift**: The model picks up on themes or details from irrelevant context and weaves them into the current scene.
- **Character bleed**: Details from one character's bio influence how a different character is written.
- **Tonal inconsistency**: The model averages across multiple tones present in the context rather than maintaining the current scene's specific tone.
- **Reduced creativity**: With more "known" information in context, the model tends to be more conservative and derivative rather than inventive.

### The Curation Advantage

By carefully selecting only the information relevant to the current page, the orchestrator ensures that:

1. **Every token earns its place.** Nothing in the prompt is there "just in case." If it is in the prompt, it is there because the current page needs it.
2. **The model's attention is focused.** With 15,500 tokens of curated input, every piece of information is within strong attention range.
3. **Voice consistency is maintained.** The raw text of the preceding pages (Layer 4) is the strongest voice signal. By not diluting it with other raw text from elsewhere in the novel, the model's voice matching is precise.
4. **Creativity is preserved.** The model has room to be inventive within the constraints because the constraints are clear and specific, not buried in a sea of tangentially related information.

### The Compression Hierarchy

The context strategy uses a deliberate compression hierarchy:

| Distance from Current Page | Format | Compression |
|---------------------------|--------|-------------|
| Pages N-1 to N-5 | Raw text | None (full fidelity) |
| Current chapter (beyond 5 pages) | Summary | ~10:1 |
| Previous chapters | Compressed summary | ~50:1 |
| Full novel arc | Narrative summary | ~100:1 |
| Character/location facts | Structured YAML | Lossless (but filtered) |

This hierarchy mirrors how a human novelist thinks: vivid, word-for-word recall of what they just wrote; clear memory of what happened earlier in the chapter; general awareness of the story arc; and on-demand access to reference facts.

---

## Rolling Continuity Notes Strategy

### The Problem

By chapter 15, the novel contains thousands of specific details: character descriptions, revealed secrets, objects introduced, promises made, relationships shifted. The writer agent needs awareness of these details but cannot load the full manuscript.

### The Solution

`continuity/rolling_notes.md` is a living document updated after every page. It records every narratively significant detail in a structured, searchable format.

### Update Process

After each page is finalized:

1. The orchestrator scans the new page for narratively significant details.
2. New details are appended to `rolling_notes.md` under the current chapter and page heading.
3. If a detail contradicts or updates an earlier note, the earlier note is marked as superseded.

### Feeding Notes into Context

When assembling Layer 6 (Narrative Summary), the orchestrator:

1. Identifies which characters, locations, and plot threads are active in the current scene.
2. Extracts relevant entries from `rolling_notes.md` for those characters, locations, and threads.
3. Compresses the extracted entries into a narrative summary paragraph.

This means the writer agent receives only the continuity information it needs, not the full rolling notes document (which may be 10,000+ tokens by mid-novel).

### Chapter Summaries

In addition to per-page rolling notes, `continuity/chapter_summaries.md` contains a 200-300 word summary of each completed chapter. These summaries are:

- Written by the orchestrator (not the writer agent) to ensure objectivity
- Focused on plot events, character development, and unresolved questions
- Used as the primary source for Layer 6 when the current scene does not require page-level detail from earlier chapters

---

## Token Cost Estimates for a Full Novel

### Assumptions

- Novel length: 80,000 words (~300 pages at 267 words/page, or ~320 pages at 250 words/page)
- Using 300 pages for round-number estimation
- Model: Claude Opus 4.6
- Input cost: $15 per million tokens
- Output cost: $75 per million tokens
- Prompt caching: Active for static components

### Per-Page Cost

| Component | Tokens | Cost |
|-----------|--------|------|
| Input (cached static layers) | ~6,250 | $0.009 (at cached read rate of $1.50/M) |
| Input (dynamic layers) | ~9,250 | $0.139 (at standard $15/M) |
| Output (prose + thinking) | ~7,500 | $0.563 (at $75/M) |
| **Total per page** | **~23,000** | **~$0.71** |

### First Draft (Writing Phase)

| Item | Quantity | Cost |
|------|----------|------|
| Page generation | 300 pages | $213.00 |
| Prompt caching savings | ~40% of input | -$72.00 |
| Consistency checks | ~60 scene completions | $12.00 |
| Progress updates | ~60 updates | $3.00 |
| **Subtotal: Writing** | | **~$156.00** |

Note: The overwrite approach means the first draft is 120-130% of target, so actual page count is closer to 360-390 pages. However, the additional pages are trimmed during editing, not generated as separate calls.

### Editing Phase

| Pass | Pages Reviewed | Cost per Page | Total |
|------|---------------|---------------|-------|
| Developmental edit | 300 | $0.35 | $105.00 |
| Line edit | 300 | $0.30 | $90.00 |
| Copy edit | 300 | $0.25 | $75.00 |
| Final polish | 300 | $0.20 | $60.00 |
| **Subtotal: Editing** | | | **~$330.00** |

Note: Editing prompts are smaller (~15K-20K tokens), so per-page cost is lower. But editing requires reviewing every page in each pass.

### Total Estimated Cost

| Phase | Cost |
|-------|------|
| Conception + Research | ~$15 |
| Design (outlines, character sheets) | ~$25 |
| Writing (first draft) | ~$156 |
| Editing (four passes) | ~$330 |
| **Total** | **~$526** |

### Optimized Estimate with Aggressive Caching

With prompt caching fully utilized (static layers cached across all pages in a session):

| Phase | Standard | Cached | Savings |
|-------|----------|--------|---------|
| Writing | $156 | $112 | 28% |
| Editing | $330 | $245 | 26% |
| **Total** | **$526** | **$397** | **25%** |

**The ~$112 figure for writing represents the best-case scenario** where prompt caching is maximally effective: writing sessions are organized to process multiple pages sequentially (keeping the system prompt, style rules, and story bible cached), and the orchestrator batches pages within the same scene to maximize cache hits on Layers 1-3.

---

## Prompt Caching for Static Components

### What Is Prompt Caching?

Anthropic's prompt caching allows you to mark portions of the prompt as cacheable. The first request pays the cache write cost ($18.75/M tokens, 25% premium over standard input). Subsequent requests that reuse the same cached prefix pay only the cache read cost ($1.50/M tokens, 90% discount from standard input).

### Which Layers to Cache

| Layer | Cacheable? | Rationale |
|-------|-----------|-----------|
| Layer 1: System + Voice Rules | Yes (always) | Identical across every page in the novel |
| Layer 2: Story Bible Excerpt | Partially | Cache the full bible, but only include relevant sections |
| Layer 3: Scene Outline | Per-scene | Same for all pages within a scene (~4-6 pages) |
| Layer 4: Previous Pages | No | Changes every page |
| Layer 5: Chapter Summary | Per-chapter | Same for all pages within a chapter |
| Layer 6: Narrative Summary | Partially | Changes slowly, but updated per page |
| Layer 7: Writing Instruction | No | Unique per page |

### Optimal Caching Strategy

**Session-based caching**: Organize writing into sessions where the orchestrator processes an entire scene (4-6 pages) before moving to the next scene. Within a scene:

- Layers 1, 2, and 3 are identical and fully cached after the first page.
- Layer 5 is identical and cached.
- Only Layers 4, 6, and 7 change per page.

**Cost per page within a cached session:**

| Component | Tokens | Rate | Cost |
|-----------|--------|------|------|
| Cached input (Layers 1, 2, 3, 5) | ~8,750 | $1.50/M | $0.013 |
| Dynamic input (Layers 4, 6, 7) | ~6,750 | $15/M | $0.101 |
| Output | ~7,500 | $75/M | $0.563 |
| **Total** | **~23,000** | | **$0.677** |

Compared to the non-cached cost of ~$0.71, caching saves approximately $0.03 per page, or ~$10 over a 300-page novel's writing phase. The savings are modest per page but compound over the full production cycle (including editing passes where the style rules and checklist are cached across hundreds of calls).

### Cache Lifetime Considerations

Anthropic's prompt cache has a TTL (time to live) of 5 minutes by default, refreshed on each use. To maximize cache hits:

- Process pages in rapid succession within a scene (do not pause for long reviews between pages).
- Complete an entire scene before taking a break.
- When resuming after a break, accept the cache write cost on the first page of the new session.

### Editing Phase Caching

Editing benefits even more from caching because:

- Layer 1 (style rules + checklist) is identical across every page in every editing pass.
- The editing prompt is smaller, so the cached portion represents a larger percentage of the total.
- An entire chapter can be edited in one session, keeping the cache warm for 15-25 pages.

Estimated caching savings during editing: 25-30% reduction in input costs per pass.
