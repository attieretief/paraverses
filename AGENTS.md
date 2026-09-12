# Paraverses

Paraverses is a bounded body of ~72 **newly composed** Reformed worship songs — original
words and original music — in the lineage of the GKSA *Skrifberymings* and the Scottish
*Paraphrases* of 1781. It is not a translation: it is an original canon, worked out in full
up front so the finished body can be read back as one architecture in which the Gospel is
visible. It is a **working hymnal** — every movement built liturgically complete for
ordinary weekly use, weighted toward Grace, in a congregation-led idiom singable without a
band. Attribution for all creative content: **"Words and music by Attie Retief."**

This repo *is* the canon. The songs are the real work; the Python plumbing exists only to
publish progress. Default to songwriting craft — lyrics, metre, theology, singability —
and do engineering only when asked.

## How to collaborate here

- **Attie is the composer and author**, not a researcher or critic. He is the maker. Engage
  as a creative peer with real craft engagement, not process commentary or hedged
  generalities. He is technically fluent (Python, git, GitHub Pages, CI), so keep the
  engineering talk economical.
- **Tone: terse, direct, unsentimental** — in replies and in creative output. Confirm work
  in a sentence or two; don't narrate what you're about to do; don't pad with caveats or
  summaries readable from the diff. Give creative proposals directly with rationale
  compressed. The Reformed-hymnal idiom values restrained prose; match it.
- Reformed worship aesthetics matter: the Heidelberg guilt–grace–gratitude frame, the
  Skrifberyming / Scottish Paraphrase lineage, congregation-led simple melodies
  (Getty/Townend register, not band-led contemporary), theological precision.

## Structure of the canon

`framework.yaml` is the **master working document** — the source of truth for scope,
purpose, design principles, three arcs, nine movements, three threads, and decisions. Read
it first when framing or scope comes up; don't recapitulate from memory. (The original Word
doc has been retired; `framework.yaml` supersedes it.)

- **Three arcs** (Heidelberg): Ellende / Our Need (18), Verlossing / Grace (36),
  Dankbaarheid / Gratitude (18).
- **Nine movements**, 1–9, each with anchor passages and a mode. Movement 6 (cross &
  resurrection) is the hinge and densest cluster; Movement 1 opens on the being of God
  (Sanctus), which is load-bearing.
- **Three threads** resurfacing across movements: **Light · The Name · Water & Thirst.**
  Hold them lightly for resonance, never as a repeated lyric or musical leitmotif.
- **Tunes:** a bounded tune-set, not 72 bespoke melodies. Most texts are written to a
  portable metre (CM/LM/SM) so one tune can carry several texts (contrafactum); a few
  bespoke tunes are reserved for hinge songs. Writing to a metre is a lyric decision and
  does not commit the melody.

## Song files — locked structure

Each song is `songs/NNN-slug.md` with YAML front-matter (`number`, `movement`, `title`,
`scripture`, `status`, `threads`, `metre`, `key_suggestion`, `written`; optional per-variant
`cues:` and `youtube:`). `songs/_TEMPLATE.md` holds the structural template. Every song
follows this fixed order, locked across all 72:

1. Front-matter
2. Title + movement line
3. `[Jump to the song →](#lyric)` anchor
4. **Theological foundation** — the seven-section spine (below)
5. **Lyric** under `## <a id="lyric"></a>Lyric`
6. **Annotated lyric** — a two-column table: stanza text | regulative-principle warrant
   (scripture refs + confessional anchors)
7. **Notes** — threads, metre, melody intent, title status

The **seven-section defense spine** (same headings, same order, every song):

1. **Locus** — where in systematic theology the song sits
2. **Scripture grounding** — anchor passages per stanza, one-line glosses, grouped by stanza
3. **Confessional anchoring** — Belgic / WCF / Heidelberg / Athanasian, with article/question
   numbers; brief quotation of the load-bearing article welcome
4. **Why this content, this shape** — the argument for the design
5. **Lineage continuity** — how it honors the tradition's *form and intent*, never its text
6. **Objections answered** — the likely concerns of a traditional Afrikaans Reformed audience,
   each named and answered
7. **Lyric brief** — numbered criteria the lyric must satisfy; the approval gate for any later
   lyric revision

**Do the theology first.** Produce the seven-section defense before drafting or revising a
lyric; a song without a locked defense is not ready for lyric review. Write the §7 brief,
then the lyric, then test the lyric against the brief. When the lyric changes, regenerate the
annotated two-column table so the warrant stays accurate. Prose register inside the defense
is terse and declarative — no padding, no devotional softening.

## Production workflow — theology durable, music discovered

**Theology is the durable layer; the music is discovered and reconciled after.** Lock the
defense and lyric first (status `draft-lyric`); hold melody, exact metre, key, and any refrain
decision loosely, and reconcile the song `.md` to what actually gets recorded. Mark
`metre`/`key_suggestion` as provisional until confirmed. Do not commit a lead sheet until the
melody is settled (`_TEMPLATE.md` says delete the lead-sheet section if the melody isn't
sketched).

The `prompts/` folder is **gitignored, local-only** — it holds the music-generation cues.
Those cues capture what was sent into generation, not what shipped (Attie post-edits in the
studio, which no text file describes). Treat cues as one input for aesthetic *direction*, not
as a description of the final sound. Claude cannot hear audio; when a question depends on the
actual shipped mix, ask Attie to describe it.

**Song pages (`songs/NNN-*.md`) must never name any production tool.** Describe music as
composed / recorded / discovered / sketched. Tool-talk belongs in `prompts/`, not in the
public canon.

## Build & run

- `make dev` — build + serve at http://localhost:5500, watches `framework.yaml`, `songs/`,
  `scripts/build_site.py`, auto-reloads.
- `make build` — one-shot build into `site/` (generated; gitignored; not edited by hand).
- `make video` (or `make video SONG=004`) — renders sing-along MP4s per audio variant, timed
  to the per-variant `cues:` in front-matter. Videos are gitignored.
- `make youtube` — uploads rendered videos, adds to a playlist, writes URLs back into song
  front-matter (needs one-time Google Cloud OAuth). See `scripts/upload_youtube.py --help`.
- `scripts/build_site.py` reads framework + songs → `site/index.html` and per-song
  `site/songs/<slug>.html`. Songs may include an `abc` lead sheet (piped through `abcm2ps`)
  and a demo at `audio/<slug>.mp3` (rendered as an `<audio>` player).

## Status lifecycle & deploy

`idea` (0) → `draft-lyric` (0.4) → `draft-melody` (0.7) → `complete` (1.0). Progress on the
site is computed from committed `status` values — never updated by hand.

- **Repo:** https://github.com/attieretief/paraverses (public)
- **Live site:** https://paraverses.attieretief.com — deployed by GitHub Actions from `main`
  via `actions/deploy-pages` on every push (custom domain via `site/CNAME`).

## Licensing

Dual: creative content (lyrics, music, lead sheets, demos, framework prose) under **CC BY-SA
4.0** (`LICENSE-CONTENT`); build scripts and site code under **MIT** (`LICENSE`). Required
attribution for reuse: *"Words and music by Attie Retief, from Paraverses, licensed under
CC BY-SA 4.0."*
