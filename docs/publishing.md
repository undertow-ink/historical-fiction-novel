# Publishing Guide

This document covers the complete publishing pipeline for the Historical Fiction Novel Factory: building distributable formats from the Markdown manuscript, distributing through eBook, print, and audiobook channels, generating cover art, and pricing strategy.

---

## Table of Contents

1. [Build Pipeline](#build-pipeline)
2. [eBook Distribution](#ebook-distribution)
3. [Print Distribution](#print-distribution)
4. [Audiobook Production and Distribution](#audiobook-production-and-distribution)
5. [Free Distribution](#free-distribution)
6. [Cover Art Generation](#cover-art-generation)
7. [Pricing Strategy](#pricing-strategy)
8. [Pre-Publication Checklist](#pre-publication-checklist)

---

## Build Pipeline

The manuscript is authored in Markdown and converted to distributable formats using pandoc and LaTeX.

### Markdown to EPUB

EPUB is the standard eBook format accepted by virtually all digital bookstores.

```bash
./scripts/build_manuscript.sh epub
```

**What this does:**

1. Collects all scene files from `manuscript/` in order (part-1/chapter-01/scene-01.md through the final scene).
2. Concatenates them with proper chapter headings and scene breaks.
3. Runs pandoc with the following configuration:
   - Input: Markdown (GitHub-flavored)
   - Output: EPUB3
   - Metadata: Title, author, language, publication date, description, ISBN (from `book_bible.yaml`)
   - CSS: `style/epub.css` for typography and layout
   - Cover image: `build/cover.jpg` (if present)
   - Table of contents: Auto-generated from chapter headings
4. Outputs to `build/{book-name}.epub`.

**Pandoc command (underlying):**

```bash
pandoc \
  --from=gfm \
  --to=epub3 \
  --metadata-file=book_bible.yaml \
  --css=style/epub.css \
  --epub-cover-image=build/cover.jpg \
  --toc \
  --toc-depth=1 \
  --output=build/book-name.epub \
  manuscript/combined.md
```

**Validation:** After building, validate the EPUB with epubcheck:

```bash
java -jar epubcheck.jar build/book-name.epub
```

### Markdown to PDF

Two PDF variants are produced: a trade paperback for print distribution and a manuscript format for editorial review.

#### Trade Paperback PDF (for KDP Print / IngramSpark)

```bash
./scripts/build_manuscript.sh pdf
```

**Configuration:**
- Page size: 6" x 9" (standard trade paperback)
- Margins: 0.75" inside (gutter), 0.5" outside, 0.75" top, 0.625" bottom
- Font: EB Garamond 11pt (body), Cormorant Garamond (chapter headings)
- Line spacing: 1.3
- Chapter starts: Recto (right-hand page) with drop caps
- Headers: Book title (verso), chapter title (recto)
- Page numbers: Centered bottom

**Pandoc + LaTeX pipeline:**

```bash
pandoc \
  --from=gfm \
  --to=pdf \
  --pdf-engine=xelatex \
  --template=templates/trade-paperback.tex \
  --metadata-file=book_bible.yaml \
  --toc \
  --output=build/book-name.pdf \
  manuscript/combined.md
```

#### Manuscript Format PDF (for editorial review)

```bash
./scripts/build_manuscript.sh manuscript
```

**Configuration:**
- Page size: 8.5" x 11" (US Letter)
- Font: Courier New 12pt (monospaced, industry standard)
- Margins: 1" all sides
- Line spacing: Double-spaced
- Header: Author surname / title keyword / page number
- Scene breaks: Centered `#`
- Chapter breaks: New page, centered title

### Build Verification

After any build, run the stats script to verify the output:

```bash
python3 scripts/manuscript_stats.py series/{name}/{book}/manuscript/
```

This reports:
- Total word count
- Page count (at 250 words/page)
- Estimated reading time (at 250 words/minute)
- Per-chapter word counts
- Any chapters over or under target

---

## eBook Distribution

### Amazon Kindle Direct Publishing (KDP)

**Platform**: [kdp.amazon.com](https://kdp.amazon.com)

**What it offers:**
- Access to the world's largest eBook marketplace
- 70% royalty rate on eBooks priced $2.99-$9.99
- 35% royalty rate on eBooks priced outside that range
- KDP Select (optional, exclusive): Kindle Unlimited enrollment, promotional tools, 70% royalty in additional territories
- Real-time sales reporting

**Upload requirements:**
- Format: EPUB (preferred) or DOCX
- Cover: JPEG or TIFF, minimum 1000x625 pixels, recommended 2560x1600 pixels (1.6:1 ratio)
- Metadata: Title, subtitle, author, description, keywords (up to 7), categories (up to 3)
- ISBN: Optional for KDP (Amazon assigns an ASIN), required if you want your own

**Royalty structure:**

| Price Range | Royalty Rate | Delivery Fee | Net per $4.99 book |
|-------------|-------------|--------------|---------------------|
| $0.99-$2.98 | 35% | None | -- |
| $2.99-$9.99 | 70% | ~$0.06/MB | ~$3.43 |
| $10.00+ | 35% | None | -- |

**Recommendation:** Price in the $2.99-$9.99 range to qualify for the 70% royalty. The delivery fee is negligible for text-only books (typically under $0.10).

**KDP Select consideration:** KDP Select requires 90-day exclusivity (no selling the eBook anywhere else). In exchange, you get Kindle Unlimited page reads (paid per page, roughly $0.004-$0.005/page) and promotional tools. For a first novel, the wide distribution approach (non-exclusive) is generally recommended to establish presence across platforms.

### Draft2Digital

**Platform**: [draft2digital.com](https://www.draft2digital.com)

**What it offers:**
- Aggregator that distributes to Apple Books, Barnes & Noble, Kobo, OverDrive (libraries), Scribd, Vivlio, and dozens of smaller retailers
- Single upload, distributed everywhere
- 10% fee on net receipts (you keep 90% of what each retailer pays)
- Free ISBN assignment
- Automated formatting tools
- Universal Book Link (one link that routes readers to their preferred store)
- Payment aggregation (one monthly payment regardless of how many stores)

**Upload requirements:**
- Format: EPUB, DOCX, or use their online formatter
- Cover: JPEG or PNG, minimum 1600x2400 pixels (1:1.5 ratio)
- Metadata: Title, author, description, keywords, categories, language, publication date

**Royalty example (Apple Books, $4.99 list price):**

| Component | Amount |
|-----------|--------|
| List price | $4.99 |
| Apple's cut (30%) | -$1.50 |
| Net to Draft2Digital | $3.49 |
| Draft2Digital fee (10%) | -$0.35 |
| **Net to author** | **$3.14** |

**Recommendation:** Use Draft2Digital for all non-Amazon distribution. Upload directly to KDP for the Amazon channel (to avoid the aggregator fee on your highest-volume store) and use Draft2Digital for everything else.

---

## Print Distribution

### Amazon KDP Print

**Platform**: [kdp.amazon.com](https://kdp.amazon.com) (same account as eBook KDP)

**What it offers:**
- Print-on-demand paperback and hardcover
- No upfront costs (no inventory, no minimum order)
- Listed on Amazon alongside the eBook
- Author copies at printing cost
- 60% royalty rate (list price minus printing cost minus Amazon's 40%)

**Specifications:**
- Trim sizes: Multiple options; 6" x 9" is standard for fiction
- Paper: White or cream (cream preferred for fiction)
- Cover: Matte or glossy laminate
- Binding: Perfect bound (paperback) or case laminate (hardcover)
- Interior: Black and white (standard for fiction)
- Bleed: No bleed required for text-only interiors

**Printing cost estimate (6" x 9" cream paperback, ~320 pages):**

| Component | Cost |
|-----------|------|
| Fixed cost | $0.85 |
| Per-page cost (320 pages x $0.012) | $3.84 |
| **Total printing cost** | **$4.69** |

**Royalty example ($14.99 list price, US sales):**

| Component | Amount |
|-----------|--------|
| List price | $14.99 |
| Amazon cut (40%) | -$6.00 |
| Printing cost | -$4.69 |
| **Net royalty** | **$4.30** |

**Expanded distribution:** KDP Print offers expanded distribution to online retailers beyond Amazon. The royalty is lower (list price minus printing cost minus 60% Amazon cut), but it extends reach.

### IngramSpark

**Platform**: [ingramspark.com](https://www.ingramspark.com)

**What it offers:**
- Print-on-demand distribution to 40,000+ retailers, bookstores, and libraries worldwide
- The standard for bookstore and library distribution (many independent bookstores order from Ingram)
- Returns program (bookstores can return unsold copies -- essential for shelf placement)
- Hardcover, paperback, and large print options
- Global printing (books printed near the point of sale, reducing shipping costs)

**Costs:**
- Title setup fee: Currently waived for new titles (previously $49)
- Revision fee: $25 per revision after initial upload
- Printing costs: Comparable to KDP Print, varies by specifications
- Wholesale discount: You set the discount (typically 55% for bookstore distribution)

**Royalty example ($14.99 list price, 55% trade discount, ~320 page paperback):**

| Component | Amount |
|-----------|--------|
| List price | $14.99 |
| Wholesale discount (55%) | -$8.24 |
| Printing cost (~$4.69) | -$4.69 |
| **Net royalty** | **$2.06** |

The royalty is lower than KDP Print because the wholesale discount is higher (bookstores need margin to be profitable). The tradeoff is access to the physical bookstore and library market.

**Recommendation:** Use both KDP Print (for Amazon-direct sales at higher royalty) and IngramSpark (for bookstore and library distribution). Set different ISBNs for each to avoid channel conflict.

---

## Audiobook Production and Distribution

### Production: ElevenLabs API

**Platform**: [elevenlabs.io](https://elevenlabs.io)

The audiobook is generated using ElevenLabs' text-to-speech API via their Python SDK.

**Model**: `eleven_v3` (latest multilingual model with superior prosody, emotion, and pacing)

**Estimated cost for a full novel:**
- ~80,000 words = ~480,000 characters
- ElevenLabs pricing: ~$0.20 per 1,000 characters (Scale tier)
- **Total: ~$96-$99 per novel** (depending on exact character count)

**Production workflow:**

```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key="your-api-key")

# Generate audio for each chapter
for chapter in chapters:
    audio = client.text_to_speech.convert(
        voice_id="selected-voice-id",
        model_id="eleven_v3",
        text=chapter.text,
        voice_settings={
            "stability": 0.65,
            "similarity_boost": 0.75,
            "style": 0.45,
            "use_speaker_boost": True
        }
    )

    # Save chapter audio
    with open(f"build/audio/chapter-{chapter.number:02d}.mp3", "wb") as f:
        for chunk in audio:
            f.write(chunk)
```

**Voice selection considerations:**
- Choose a voice that matches the novel's period and setting
- Test with a sample passage before committing to the full novel
- Use consistent voice settings across all chapters
- The `stability` parameter controls consistency (higher = more consistent, lower = more expressive)
- The `style` parameter controls expressiveness (higher = more dramatic)

**Post-production:**
- Concatenate chapter files with appropriate pauses between chapters
- Add opening and closing credits (title, author, narrator credit)
- Normalize audio levels across all chapters
- Export as M4A (for Apple/Kobo) and MP3 (for other platforms)
- Target specifications: 192 kbps, 44.1 kHz, mono (industry standard for audiobooks)

### Distribution: Voices by INaudio

**Platform**: Voices by INaudio (formerly Findaway Voices)

**What it offers:**
- Distribution to 40+ audiobook retailers and library platforms
- Accepts AI-narrated audiobooks (with disclosure)
- Includes Apple Books, Google Play, Kobo, Scribd, Chirp, libraries (OverDrive/Libby)
- You set the retail price; INaudio takes a percentage per platform

**Requirements:**
- Audio files: MP3 or M4A, per-chapter files
- Cover art: Square, minimum 2400x2400 pixels
- Retail sample: 5-minute audio sample for store listings
- Metadata: Title, author, narrator credit, description, categories

### Distribution: Kobo

**Platform**: [kobo.com/writinglife](https://www.kobo.com/writinglife)

Kobo accepts AI-narrated audiobooks directly (without an aggregator) and has been transparent about supporting AI narration with appropriate disclosure.

### Important: ACX/Audible Restriction

**ACX (Audiobook Creation Exchange) and Audible do NOT accept AI-narrated audiobooks.** As of their current policies, all audiobooks distributed through ACX/Audible must be narrated by a human voice actor. Uploading AI-narrated content violates their terms of service and will result in removal.

If Audible distribution is required, a human narrator must be hired. ACX provides a marketplace for connecting with narrators, typically on a per-finished-hour (PFH) rate or royalty share basis.

---

## Free Distribution

### GitHub Pages Site

Create a public-facing website for the novel using GitHub Pages with a static site generator.

**Options:**

- **Jekyll**: Native GitHub Pages support, no build step required, large theme ecosystem
- **Hugo**: Faster builds, more flexible, requires GitHub Actions for deployment

**Site content:**
- Novel synopsis and cover art
- Sample chapters (first 2-3 chapters as a preview)
- Author page
- PDF download link (full novel or sample)
- Links to purchase (Amazon, other retailers)
- Series page (if applicable)
- Blog for writing process updates

**Setup:**

```bash
# Jekyll (simplest)
# Create a docs/ directory in the repo root or a separate gh-pages branch
# Enable GitHub Pages in repository settings

# Hugo (via GitHub Actions)
# Create a separate workflow that builds Hugo on push to main
# Deploy to gh-pages branch
```

### PDF Download

Offer the trade paperback PDF as a free download from the GitHub Pages site. This serves as a loss leader to build readership for a series. The PDF should include:

- Full novel text
- Cover page with cover art
- Title page and copyright page
- Table of contents
- "Also by" page (if series)
- Link to purchase print/audiobook versions

---

## Cover Art Generation

### OpenAI GPT Image 1.5 API

**Model**: GPT Image 1.5 (gpt-image-1.5)

**Cost**: $0.04-$0.20 per image (depending on resolution and quality settings)

| Quality | Resolution | Cost |
|---------|-----------|------|
| Low | 1024x1024 | $0.04 |
| Medium | 1024x1536 | $0.07 |
| High | 1536x2048 | $0.19 |

**Usage:**

```python
from openai import OpenAI

client = OpenAI()

response = client.images.generate(
    model="gpt-image-1.5",
    prompt="Book cover for a historical fiction novel set in 1920s Mediterranean...",
    size="1024x1536",
    quality="high",
    n=1
)
```

**Tips for cover prompts:**
- Specify the genre conventions (historical fiction covers typically feature period imagery, muted color palettes, or atmospheric landscapes)
- Include composition direction (title placement area at top, author name at bottom)
- Reference the period and setting explicitly
- Request high contrast between the background and where text will be placed
- Generate multiple variants and select the best

### Flux 2 Pro via Replicate

**Model**: Flux 2 Pro (black-forest-labs/flux-2-pro)

**Cost**: $0.055 per image

**Usage:**

```python
import replicate

output = replicate.run(
    "black-forest-labs/flux-2-pro",
    input={
        "prompt": "Book cover for a historical fiction novel set in 1920s Mediterranean...",
        "width": 1024,
        "height": 1536,
        "num_inference_steps": 50,
        "guidance_scale": 7.5
    }
)
```

**Advantages of Flux 2 Pro:**
- Excellent at photorealistic and painterly styles
- Strong text rendering (useful if you want the model to attempt title text, though professional typography overlay is recommended)
- Consistent quality at low cost
- Fast generation (~10-15 seconds)

### Cover Production Workflow

1. **Generate 10-20 candidate images** across both APIs with varied prompts.
2. **Select the top 3-5 candidates** based on composition, mood, and period accuracy.
3. **Add professional typography** using image editing tools (Figma, Photoshop, or GIMP). Never rely on AI-generated text for the final cover -- always overlay the title and author name with professional fonts.
4. **Create format-specific versions:**
   - eBook cover: 2560x1600 pixels (KDP) or 1600x2400 pixels (Draft2Digital)
   - Print cover: Full wrap (front + spine + back) at 300 DPI, dimensions per trim size and page count
   - Audiobook cover: 2400x2400 pixels (square)
   - Social media: Various sizes for promotional use
5. **Total cost**: $1-$5 for the complete cover art generation process.

---

## Pricing Strategy

### eBook Pricing

**Fiction sweet spot: $3.99-$6.99**

| Price Point | Royalty (KDP 70%) | Use Case |
|-------------|-------------------|----------|
| $0.99 | $0.35 | Promotional pricing, first-in-series loss leader |
| $2.99 | $2.09 | Minimum for 70% royalty, short novels |
| $3.99 | $2.79 | Entry-level fiction, series starters |
| $4.99 | $3.49 | Standard fiction pricing, strong value perception |
| $5.99 | $4.19 | Established authors, longer novels |
| $6.99 | $4.89 | Premium fiction, literary/historical fiction |
| $9.99 | $6.99 | Maximum for 70% royalty, premium pricing |

**Recommendation for historical fiction:** $4.99-$6.99. Historical fiction readers tend to be willing to pay slightly more than genre fiction readers, and higher prices signal quality in the literary-adjacent categories.

**Series pricing strategy:**
- Book 1: $3.99 or $4.99 (accessible entry point)
- Books 2-3: $5.99 (reader is now invested)
- Box set (3 books): $9.99 (high value perception, strong royalty)
- Promotional: Drop Book 1 to $0.99 or free temporarily to drive series adoption

### Print Pricing

**Paperback sweet spot: $12.99-$17.99**

| Trim Size | Page Count | Print Cost | Suggested Price | KDP Royalty |
|-----------|-----------|------------|-----------------|-------------|
| 5.5" x 8.5" | 280-320 | ~$4.50 | $14.99 | ~$4.50 |
| 6" x 9" | 280-320 | ~$4.69 | $15.99 | ~$4.91 |
| 6" x 9" | 320-400 | ~$5.60 | $16.99 | ~$4.60 |

**Hardcover pricing:** $24.99-$29.99 (higher perceived value, gift market, library acquisitions).

**Key principle:** Print pricing should feel fair relative to the eBook. A $4.99 eBook paired with a $14.99 paperback is natural. A $4.99 eBook paired with a $24.99 paperback makes the eBook feel like a steal (which is fine -- it drives eBook sales where royalties are higher).

### Audiobook Pricing

Audiobook pricing is largely controlled by the distribution platforms:

- **Kobo**: You set the price. $14.99-$24.99 is typical for fiction audiobooks.
- **INaudio/Findaway**: You set the list price; each retailer may discount. $19.99-$24.99 suggested list price.
- **Apple Books**: You set the price. $14.99-$19.99 is competitive.

**Production cost recovery:** At ~$99 production cost (ElevenLabs) and an average $5-$7 net royalty per audiobook sale, break-even occurs at approximately 15-20 sales.

---

## Pre-Publication Checklist

### Manuscript

- [ ] All four editing passes complete
- [ ] Final consistency check clean (no unresolved issues)
- [ ] Word count within 2% of target
- [ ] All chapters merged to `main`
- [ ] Front matter complete (title page, copyright page, dedication, epigraph)
- [ ] Back matter complete (acknowledgments, author note, "also by" page)

### eBook

- [ ] EPUB builds without errors
- [ ] EPUB passes epubcheck validation
- [ ] Table of contents renders correctly
- [ ] Cover image embedded and displays properly
- [ ] Test on Kindle Previewer (KDP) and Apple Books (EPUB)
- [ ] Metadata complete (title, author, description, keywords, categories)

### Print

- [ ] PDF builds at correct trim size
- [ ] Margins meet printer specifications
- [ ] Page count verified (affects spine width and printing cost)
- [ ] Cover wrap created with correct spine width
- [ ] Proof copy ordered and reviewed
- [ ] ISBN assigned (separate ISBN for each format)

### Audiobook

- [ ] All chapters generated and reviewed
- [ ] Audio levels normalized across chapters
- [ ] Chapter markers embedded
- [ ] Opening/closing credits included
- [ ] Retail sample extracted (5 minutes)
- [ ] Square cover art created (2400x2400)

### Distribution

- [ ] KDP eBook uploaded and in review
- [ ] KDP Print uploaded and proof approved
- [ ] Draft2Digital uploaded and distributed
- [ ] IngramSpark uploaded (if using)
- [ ] Audiobook uploaded to INaudio/Kobo
- [ ] GitHub Pages site live with sample chapters
- [ ] PDF download available

### Marketing

- [ ] Book description written (150-300 words, hook-focused)
- [ ] Keywords researched (7 for KDP, categories for all platforms)
- [ ] Author bio written
- [ ] Launch plan documented
