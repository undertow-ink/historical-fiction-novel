# Editing Prompt Template

This template defines the **layered prompt structure** used by the editor agent to review and improve prose. Each editing pass type has its own checklist and focus. The editor receives the page under review surrounded by context, along with the style rules and scene intent.

## Assembly Instructions

1. Choose the **editing pass type** (developmental, line, copy, or final) and include only that pass's checklist.
2. Replace each `{{PLACEHOLDER}}` with the appropriate content.
3. Layers are separated by horizontal rules in the assembled prompt.
4. The editor should return the revised prose along with a list of changes made and their rationale.

---

## Layer 1: Editor System Prompt

> Sets the editor agent's identity and approach.

```
You are a professional fiction editor specializing in literary historical fiction. You are performing a {{PASS_TYPE}} editing pass. Your goal is to improve the prose while preserving the author's voice and intent.

Rules:
- Make the minimum changes necessary to fix each issue.
- Preserve the author's voice. Do not flatten distinctive style into generic prose.
- Flag issues you are uncertain about with [EDITOR NOTE: ...] rather than changing them.
- Do not add new content. You may cut, rearrange, or rewrite existing content.
- All changes must maintain historical accuracy for the time period.
- Return the edited text followed by a numbered list of changes with rationale.
```

**How to fill:**
- `{{PASS_TYPE}}` -- One of: `developmental`, `line`, `copy`, `final`

---

## Layer 2: Style Rules

> The same voice and style rules the writer used. The editor must enforce these.

```
=== STYLE RULES TO ENFORCE ===

{{VOICE_GUIDE}}

{{STYLE_RULES}}
```

**How to fill:**
- `{{VOICE_GUIDE}}` -- Full contents of `style/voice_guide.md`
- `{{STYLE_RULES}}` -- Full contents of `style/style_rules.md`

---

## Layer 3: Story Bible Excerpt

> Character and location details relevant to the page under review.

```
=== RELEVANT STORY BIBLE ===

Characters in this scene:
{{CHARACTERS}}

Location:
{{LOCATION}}
```

**How to fill:**
- `{{CHARACTERS}}` -- Character sheets for all characters present, focusing on voice samples and speech patterns.
- `{{LOCATION}}` -- Location sheet for the scene's setting.

---

## Layer 4: Scene Outline

> The intended structure and purpose of the scene, so the editor can judge whether the prose achieves its goals.

```
=== SCENE OUTLINE ===

Scene: {{SCENE_ID}}
POV: {{POV_CHARACTER}}
Purpose: {{PURPOSE}}
Emotional arc: {{START_EMOTION}} --> {{END_EMOTION}}
Key beats: {{KEY_BEATS}}
```

**How to fill:** Pull from the scene's `scene_outline.yaml`.

---

## Layer 5: Surrounding Context

> The prose immediately before and after the page under review, so the editor can evaluate continuity and flow.

```
=== PRECEDING CONTEXT (~500 words) ===

{{PRECEDING_PROSE}}

=== PAGE UNDER REVIEW ===

{{PAGE_CONTENT}}

=== FOLLOWING CONTEXT (~500 words) ===

{{FOLLOWING_PROSE}}
```

**How to fill:**
- `{{PRECEDING_PROSE}}` -- The ~500 words (approximately 2 pages) immediately before the page under review. Use `[Beginning of chapter]` if this is the first page.
- `{{PAGE_CONTENT}}` -- The full text of the page being edited.
- `{{FOLLOWING_PROSE}}` -- The ~500 words immediately after. Use `[End of chapter]` if this is the last page.

---

## Layer 6: Editing Instruction

> The specific editing pass checklist and any additional instructions.

```
=== EDITING INSTRUCTION ===

Perform a {{PASS_TYPE}} editing pass on the PAGE UNDER REVIEW above.

{{PASS_CHECKLIST}}

Additional focus areas for this page:
{{ADDITIONAL_INSTRUCTIONS}}

Return:
1. The complete edited text of the page.
2. A numbered list of every change made, with a brief rationale for each.
3. Any [EDITOR NOTE] flags for issues requiring the author's decision.
```

**How to fill:**
- `{{PASS_TYPE}}` -- The editing pass type.
- `{{PASS_CHECKLIST}}` -- Use the appropriate checklist below.
- `{{ADDITIONAL_INSTRUCTIONS}}` -- Any page-specific concerns. Examples: "The pacing feels slow in the middle paragraph," "Check whether the character would know about the treaty at this point in the timeline," "The dialogue attribution is confusing with three speakers."

---

## Editing Pass Checklists

### Developmental Editing Pass

Focus: Structure, story logic, and narrative effectiveness.

```
DEVELOPMENTAL EDITING CHECKLIST:

[ ] Does this page advance the scene's stated purpose?
[ ] Does the emotional arc progress as outlined ({{START_EMOTION}} --> {{END_EMOTION}})?
[ ] Are the required key beats present and effectively rendered?
[ ] Is the POV consistent? No head-hopping or information the POV character cannot know?
[ ] Is the pacing appropriate? No rushing through important moments or lingering on trivial ones?
[ ] Does the opening hook the reader (if first page of scene/chapter)?
[ ] Does the ending create momentum to keep reading (if last page of scene/chapter)?
[ ] Are character motivations clear and consistent with their arc?
[ ] Is there sufficient conflict or tension to sustain reader interest?
[ ] Does the world-building feel organic, not like an info-dump?
[ ] Are planted seeds and payoffs from the connections list handled correctly?
[ ] Is anything missing that should be here?
[ ] Is anything present that should be cut?
```

### Line Editing Pass

Focus: Prose quality, voice, rhythm, and clarity at the sentence and paragraph level.

```
LINE EDITING CHECKLIST:

[ ] Does every sentence earn its place? Cut anything that does not advance story, character, or mood.
[ ] Is the voice consistent with the voice guide and with this POV character?
[ ] Is there sufficient sentence variety (length, structure, rhythm)?
[ ] Are there any cliches? Replace with fresh, period-appropriate language.
[ ] Is the prose showing rather than telling? Convert tells to shows where possible.
[ ] Are metaphors and similes fresh, consistent with the setting, and not mixed?
[ ] Is the dialogue distinctive to each character's speech patterns?
[ ] Are dialogue tags minimal and varied? Avoid excessive "said" alternatives.
[ ] Do action beats between dialogue lines add meaning, not just fill space?
[ ] Are transitions between paragraphs smooth?
[ ] Is the sensory detail specific and grounded in the location sheet?
[ ] Are there any unintentional repetitions of words or phrases?
[ ] Is the emotional register appropriate for this moment in the story?
[ ] Are any passages overwritten? Trim purple prose.
[ ] Are any passages underwritten? Expand where the moment deserves more space.
```

### Copy Editing Pass

Focus: Grammar, consistency, factual accuracy, and technical correctness.

```
COPY EDITING CHECKLIST:

[ ] Grammar and syntax correct throughout?
[ ] Punctuation correct, especially in dialogue (period/comma inside quotes, em-dashes for interruptions, ellipses for trailing off)?
[ ] Spelling correct, including character names, place names, and period-specific terms?
[ ] Character names consistent (no switching between first/last name without reason)?
[ ] Physical descriptions consistent with character sheets (eye color, hair, etc.)?
[ ] Timeline consistent? Does the date, time of day, and season match the scene outline?
[ ] Travel times plausible per the location sheets?
[ ] Historical facts accurate for the time period (technology, customs, language, currency, food, clothing)?
[ ] No anachronistic words, phrases, or concepts?
[ ] Measurements and units appropriate to the setting (no metric in medieval Europe, etc.)?
[ ] Titles, honorifics, and forms of address correct for the period and culture?
[ ] Continuity with surrounding context (no disappearing objects, changed weather, etc.)?
[ ] Paragraph breaks in logical places?
[ ] Scene breaks properly marked?
```

### Final Proofing Pass

Focus: Last check before publication. Surface-level errors only.

```
FINAL PROOFING CHECKLIST:

[ ] Any remaining typos or misspellings?
[ ] Any missing or extra words?
[ ] Any incorrect homophones (their/there/they're, etc.)?
[ ] Consistent formatting (em-dashes, ellipses, number style)?
[ ] Consistent capitalization of proper nouns and titles?
[ ] Quotation marks properly opened and closed?
[ ] No orphaned dialogue (speech without clear attribution in multi-character scenes)?
[ ] Page/section breaks correctly placed?
[ ] Any repeated words across a line or paragraph break (the the, and and)?
[ ] Final read-aloud test: does anything sound awkward when read aloud?
```

---

## Quick Reference: Pass Order

| Pass | Focus | When to Run |
|------|-------|-------------|
| Developmental | Structure, story, pacing | After first draft of each scene |
| Line | Prose quality, voice, style | After developmental issues resolved |
| Copy | Accuracy, consistency, grammar | After line editing complete |
| Final | Surface errors, formatting | Before merge to main branch |

Each page should go through all four passes in order. Do not combine passes -- each has a different lens, and combining them causes errors to slip through.
