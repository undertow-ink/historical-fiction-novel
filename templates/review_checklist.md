# Chapter PR Review Checklist

Use this checklist when reviewing pull requests that add or modify chapter content. The Claude GitHub App should evaluate each category and provide specific, actionable feedback with line references.

---

## 1. Plot Consistency

- [ ] Events in this chapter are consistent with all previous chapters.
- [ ] No contradictions with established facts (dates, locations, outcomes).
- [ ] Character knowledge is consistent -- no one acts on information they have not received.
- [ ] Cause and effect are logical. Actions have plausible consequences.
- [ ] Subplots are advanced or acknowledged if they were active in previous chapters.
- [ ] No plot threads from earlier chapters are silently dropped.
- [ ] Any new plot elements are properly seeded, not introduced out of nowhere.
- [ ] The chapter's events align with the scene outlines in the story bible.

**Review note:** Cross-reference the chapter against the narrative summary and relevant scene outlines. Flag any discrepancy, no matter how small.

---

## 2. Character Voice

- [ ] Each character's dialogue is distinctive and matches their voice sample.
- [ ] Speech patterns from the character sheet are consistently applied.
- [ ] Characters use vocabulary appropriate to their education and social class.
- [ ] No character sounds like the narrator or like other characters.
- [ ] Internal monologue (for POV characters) matches their personality and worldview.
- [ ] Characters do not speak in ways that are anachronistic for the period.
- [ ] Emotional reactions match the character's established personality and arc stage.

**Review note:** Read each character's dialogue in isolation. If you cannot tell who is speaking without the dialogue tags, the voice needs work.

---

## 3. Historical Accuracy

- [ ] Technology mentioned exists in the stated time period.
- [ ] Social customs, manners, and etiquette are period-appropriate.
- [ ] Clothing, food, and drink are accurate for the time and place.
- [ ] Political structures and titles are correct.
- [ ] Religious practices match the setting.
- [ ] Currency, measurements, and trade goods are period-accurate.
- [ ] Language avoids modern idioms and concepts (see style_rules.md banned list).
- [ ] Military tactics, weapons, and armor are accurate if depicted.
- [ ] Medical knowledge and practices reflect the period, not modern understanding.
- [ ] Travel times between locations are plausible per the location sheets.
- [ ] Seasonal details (weather, daylight, agriculture) are correct for the date and region.

**Review note:** Flag anything questionable with a specific concern and suggested correction. When uncertain, note it as needing research verification.

---

## 4. Pacing

- [ ] The chapter opens with a hook that creates immediate interest.
- [ ] Important scenes receive proportional page space (not rushed).
- [ ] Transitional passages are brief and purposeful, not padded.
- [ ] Action sequences are tight with short sentences and paragraphs.
- [ ] Reflective passages slow the rhythm appropriately without stalling momentum.
- [ ] The chapter ends on a moment that compels the reader to continue.
- [ ] Scene breaks occur at natural transition points.
- [ ] No section overstays its welcome -- every paragraph earns its place.
- [ ] The overall chapter length is appropriate for its content (not padded, not skeletal).

**Review note:** Note any passages where you feel your attention wandering. That is a pacing problem.

---

## 5. Dialogue Quality

- [ ] Dialogue sounds like speech, not written prose.
- [ ] Subtext is present -- characters do not always say exactly what they mean.
- [ ] Dialogue serves at least one purpose: reveals character, advances plot, builds tension, or conveys information the reader needs.
- [ ] No "as you know, Bob" exposition (characters telling each other things they both already know).
- [ ] Dialogue tags are minimal. "Said" is the default; alternatives are used sparingly and only when "said" genuinely does not fit.
- [ ] Action beats are used instead of tags where possible.
- [ ] Group conversations are clear about who is speaking at all times.
- [ ] Interruptions, pauses, and silence are used effectively.
- [ ] No long monologues unless dramatically justified.

**Review note:** Read dialogue aloud. If it sounds stilted or unnatural, flag it.

---

## 6. Show vs. Tell

- [ ] Emotions are demonstrated through action, dialogue, and physical sensation rather than named ("she felt angry" -> show the anger).
- [ ] Character traits are revealed through behavior, not stated by the narrator.
- [ ] Backstory is woven into action and dialogue, not delivered in exposition blocks.
- [ ] Setting details are experienced through character interaction, not listed.
- [ ] Relationships are demonstrated through how characters treat each other, not summarized.
- [ ] Internal states manifest as physical sensation and impulse, not abstract labels.

**Review note:** Search for emotion words (angry, sad, happy, afraid, nervous, excited) used in narration. Each one is a candidate for conversion to showing.

---

## 7. Cliche Detection

- [ ] No cliched phrases or idioms (unless deliberately used in character dialogue where it fits their speech pattern).
- [ ] No cliched plot devices without a fresh twist (the chosen one, love at first sight, the noble savage, the manic pixie, etc.).
- [ ] No stock descriptions (azure orbs for eyes, raven tresses for hair, aquiline nose, etc.).
- [ ] No predictable emotional reactions -- find the specific, surprising response.
- [ ] Metaphors and similes are original and grounded in the story's world.
- [ ] Avoid AI-tell phrases listed in style_rules.md.

**Review note:** Any phrase that could appear in a hundred other novels should be replaced with something specific to this story, this character, this moment.

---

## 8. Sentence Variety

- [ ] Sentences vary in length (mix of short, medium, and long).
- [ ] Sentences vary in structure (simple, compound, complex; different openings).
- [ ] No more than two sentences in a row begin with the same word.
- [ ] No more than three sentences in a row follow the same Subject-Verb-Object pattern.
- [ ] Paragraph length varies (single-line paragraphs for impact, longer paragraphs for immersion).
- [ ] Rhythm matches content (staccato for action, flowing for reflection).
- [ ] No accidental rhymes or unintentional alliteration that distracts.

**Review note:** Read a full page aloud. Monotonous rhythm is immediately apparent when spoken.

---

## 9. Chekhov's Gun Compliance

- [ ] Every significant object, detail, or piece of information introduced in this chapter is either used in this chapter or noted in the scene outline as a seed for later payoff.
- [ ] No prominent details that are introduced and then forgotten.
- [ ] Payoffs from earlier chapters (listed in the scene outline's `connections.setup_from`) are delivered effectively.
- [ ] Seeds planted in this chapter (listed in `connections.payoff_for`) are subtle enough not to telegraph the payoff but clear enough to be recognized in retrospect.
- [ ] No deus ex machina solutions -- every resolution uses elements previously established.

**Review note:** Cross-reference the scene outline's connections lists. Every `setup_from` should have a visible payoff. Every `payoff_for` should have a visible seed.

---

## 10. Emotional Authenticity

- [ ] Emotional reactions are proportional to the events (not over- or under-reacting).
- [ ] The emotional arc specified in the scene outline is achieved.
- [ ] Complex emotions are present -- characters can feel contradictory things simultaneously.
- [ ] Emotional beats are earned, not forced (setup justifies the payoff).
- [ ] Grief, love, fear, and joy are depicted with specificity, not in generic terms.
- [ ] The reader is invited to feel, not told what to feel.
- [ ] Emotional transitions are gradual, not abrupt (unless the abruptness is the point).
- [ ] Vulnerability is present in appropriate moments -- characters are not emotionally armored at all times.

**Review note:** After reading the chapter, note what you felt. If the answer is "nothing," the emotional work needs revision.

---

## Review Summary Template

When completing a review, structure your feedback as follows:

```
## Review Summary

**Chapter:** [number]
**Branch:** [branch name]
**Overall Assessment:** [1-2 sentence summary]

### Critical Issues (must fix before merge)
1. [Issue with file:line reference]

### Significant Issues (should fix before merge)
1. [Issue with file:line reference]

### Minor Issues (fix if time permits)
1. [Issue with file:line reference]

### Strengths
- [What works well -- always include positive feedback]

### Checklist Scores
| Category | Score | Notes |
|----------|-------|-------|
| Plot Consistency | Pass/Fail | |
| Character Voice | Pass/Fail | |
| Historical Accuracy | Pass/Fail | |
| Pacing | Pass/Fail | |
| Dialogue Quality | Pass/Fail | |
| Show vs. Tell | Pass/Fail | |
| Cliche Detection | Pass/Fail | |
| Sentence Variety | Pass/Fail | |
| Chekhov's Gun | Pass/Fail | |
| Emotional Authenticity | Pass/Fail | |
```
