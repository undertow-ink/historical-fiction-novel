# Writing Prompt Template

This template defines the **7-layer prompt structure** used to generate prose from the writer agent. Each layer provides a different type of context, ordered from most persistent (system-level rules) to most specific (the current instruction).

## Assembly Instructions

1. Replace each `{{PLACEHOLDER}}` with the appropriate content.
2. Layers are separated by horizontal rules (`---`) in the assembled prompt.
3. All layers are required. If a layer has no content yet (e.g., Layer 4 for the first page), replace the placeholder with the noted fallback text.
4. Keep the total prompt under the context window limit. If content must be trimmed, compress Layers 5 and 6 first, then reduce Layer 2 to only the characters and locations present in the current scene.
5. The assembled prompt is sent as a single message to the writer agent.

---

## Layer 1: System Prompt -- Voice and Style Rules

> This layer sets the writer agent's identity and immutable stylistic constraints. It does not change between scenes. Load it from `style/voice_guide.md` and `style/style_rules.md`.

```
You are a literary fiction writer. You write prose for a historical novel. Follow these voice and style rules exactly. Never break character. Never insert commentary or meta-text. Output only prose.

=== VOICE GUIDE ===

{{VOICE_GUIDE}}

=== STYLE RULES ===

{{STYLE_RULES}}
```

**Source files:**
- `{{VOICE_GUIDE}}` -- paste the full contents of `style/voice_guide.md`
- `{{STYLE_RULES}}` -- paste the full contents of `style/style_rules.md`

---

## Layer 2: Story Bible Excerpt

> This layer provides the writer with all the character and location details relevant to the current scene. Pull from the story bible YAML files and format as readable text.

```
=== STORY BIBLE: CHARACTERS IN THIS SCENE ===

{{CHARACTERS}}

=== STORY BIBLE: LOCATION ===

{{LOCATION}}
```

**How to fill:**
- `{{CHARACTERS}}` -- For each character listed in the scene outline's `characters_present`, extract their character sheet and format it as structured text. Include: name, physical description, personality traits, speech patterns, mannerisms, current relationship statuses (as of this chapter), and voice sample.
- `{{LOCATION}}` -- Extract the location sheet for the scene's location. Include: physical description, atmosphere, and all sensory details.

---

## Layer 3: Scene Outline

> This layer gives the writer the structural blueprint for the current scene. Pull directly from the scene outline YAML.

```
=== SCENE OUTLINE ===

Scene ID: {{SCENE_ID}}
Chapter: {{CHAPTER}}, Scene: {{SCENE_NUMBER}}
POV Character: {{POV_CHARACTER}}
Location: {{LOCATION_NAME}}
Date: {{DATE_IN_STORY}}
Time: {{TIME_OF_DAY}}

Characters present: {{CHARACTERS_PRESENT}}

Summary:
{{SUMMARY}}

Purpose: {{PURPOSE}}

Emotional arc: {{START_EMOTION}} --> {{END_EMOTION}}
Pivot: {{PIVOT}}

Key beats:
{{KEY_BEATS}}

Target length: ~{{TARGET_WORDS}} words
```

**How to fill:** Pull all values from the scene's `scene_outline.yaml` file. Format `KEY_BEATS` as a numbered list.

---

## Layer 4: Previous Pages

> This layer provides immediate prose continuity. The writer needs to match the rhythm, tone, and details of the most recently written pages so the new output reads as a seamless continuation.

```
=== PREVIOUS PAGES (last ~1,250 words) ===

{{PREVIOUS_PAGES}}
```

**How to fill:**
- `{{PREVIOUS_PAGES}}` -- Paste the last 3-5 pages of written prose (approximately 750-1,250 words). This should be the prose immediately preceding what the writer will generate.
- **Fallback:** If this is the first page of the first scene, replace with: `[This is the opening of the novel. There are no previous pages.]`
- **Fallback:** If this is the first page of a new chapter, include the last 2-3 pages of the previous chapter and add a note: `[New chapter begins here. Scene break above.]`

---

## Layer 5: Chapter Summary

> This layer provides compressed context for everything that has happened earlier in the current chapter. It prevents the writer from contradicting recent events without consuming too many tokens on full prose.

```
=== CHAPTER {{CHAPTER_NUMBER}} SUMMARY (scenes so far) ===

{{CHAPTER_SUMMARY}}
```

**How to fill:**
- `{{CHAPTER_SUMMARY}}` -- Write a compressed summary (200-400 words) of all scenes in this chapter that precede the current scene. Focus on: what happened, what was revealed, what emotional state the POV character is in, and any objects or details that were established and must be maintained.
- **Fallback:** If this is the first scene of the chapter, replace with: `[This is the first scene of Chapter {{CHAPTER_NUMBER}}. No prior scenes in this chapter.]`

---

## Layer 6: Narrative Summary

> This layer provides the broadest context -- a compressed version of everything that has happened in the story up to this point. It prevents plot holes and dropped threads without requiring the full manuscript in context.

```
=== STORY SO FAR (through Chapter {{PREVIOUS_CHAPTER}}) ===

{{NARRATIVE_SUMMARY}}
```

**How to fill:**
- `{{NARRATIVE_SUMMARY}}` -- A 300-800 word summary of the entire story from the beginning through the end of the previous chapter. Organize by chapter or by major plot thread. Emphasize: key plot events, character development, unresolved tensions, planted seeds not yet paid off, and the current state of all major relationships.
- **Fallback:** If this is Chapter 1, replace with: `[This is the beginning of the story. No prior narrative.]`

---

## Layer 7: Writing Instruction

> This is the specific, actionable instruction for what the writer should produce right now. It should be precise about scope (how many words, which beat to cover) and any special requirements.

```
=== INSTRUCTION ===

Write the next ~{{WORD_COUNT}} words of the scene.

{{SPECIFIC_INSTRUCTION}}

Requirements:
- Stay in {{POV_CHARACTER}}'s point of view. Do not reveal information they would not know.
- Maintain the established voice, tone, and period accuracy.
- Cover the following beat(s): {{CURRENT_BEATS}}
- End at a point that creates forward momentum.
- Do not summarize or skip ahead. Write the moment fully.
{{ADDITIONAL_REQUIREMENTS}}
```

**How to fill:**
- `{{WORD_COUNT}}` -- Typically 250-500 words per generation (one to two pages).
- `{{SPECIFIC_INSTRUCTION}}` -- Any scene-specific instruction. Examples: "Open with a description of the harbor at dawn," "This is a dialogue-heavy passage between X and Y," "Build tension slowly -- the character does not yet know what the reader suspects."
- `{{CURRENT_BEATS}}` -- The specific key beat(s) from the scene outline that this generation should cover. Usually 1-2 beats per generation.
- `{{ADDITIONAL_REQUIREMENTS}}` -- Any extra constraints. Examples: "Include the detail about the broken lock established in p1-c02-s01," "This passage must reference the smell of lavender from the location sheet," "No dialogue in this passage."

---

## Quick Reference: Layer Summary

| Layer | Content | Changes per... | Token Budget |
|-------|---------|----------------|--------------|
| 1 | Voice and style rules | Novel | ~1,500 |
| 2 | Story bible excerpt | Scene | ~2,000 |
| 3 | Scene outline | Scene | ~500 |
| 4 | Previous pages | Page | ~1,500 |
| 5 | Chapter summary | Scene | ~500 |
| 6 | Narrative summary | Chapter | ~1,000 |
| 7 | Writing instruction | Page | ~200 |

**Total estimated budget:** ~7,200 tokens of prompt per generation, leaving ample room for output within a standard context window.
