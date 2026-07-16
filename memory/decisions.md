# Decisions — durable choices and their rationale

One decision per bullet: **Decision — why.**

## Scope & canon

- **An original canon, not a translation — ~72 songs across 3 arcs / 9 movements —** so the
  finished body reads back as one architecture in which the Gospel is visible, not a collection
  that merely accumulated. ~72 sits between the Scots' 67 and the GKSA's 79 (locating the work
  in the lineage), is richly divisible (6×12, 3×24), and echoes the seventy-two of Luke 10.
- **`framework.yaml` is the single master working document — because** the whole framework
  (purpose, principles, arcs, movements, threads, decisions, lineage) lives there and is
  rendered on the site. The original framework Word doc was retired (commit 4f24cae). Read
  `framework.yaml` before framing scope; do not recapitulate from memory.
- **Working hymnal, weighted toward Grace but liturgically complete — because** songs are pulled
  individually into ordinary weekly worship, so high-traffic movements (opening adoration,
  grateful-life closers) must be full even though Grace is the largest arc.
- **Movement 1 adores the divine nature; the explicit Father/Son/Spirit confession is not a
  separate movement — because** the work opens on the being of God (the Sanctus register); this
  opening placement is load-bearing.
- **Unity by three threads (Light · the Name · Water & Thirst), not by a repeated lyric or
  musical leitmotif — because** the threads resurface in new dress across movements; a shared
  signature would flatten the architecture. This does not forbid tune reuse (contrafactum).

## Musical form

- **A bounded tune-set, not 72 bespoke melodies — because** most texts are written to a portable
  metre (CM/LM/SM) so one tune can carry several unrelated texts (contrafactum, the native
  economy of the metrical Psalter/Paraphrase tradition); a small number of bespoke tunes are
  reserved for hinge songs (cross movement, doxologies, distinctive forms).
- **Writing to a metre is a lyric decision and does not commit the melody — because** the melody
  is discovered and reconciled after drafting (see production workflow below).
- **Congregation-led simple melodies (Getty/Townend register), singable without a band —**
  modest ~octave range, stepwise motion, strong regular metre, phrases that resolve. Closer to
  the paraphrase DNA than band-led contemporary worship.

## Song-file discipline (locked 2026-05-22)

- **Every song `.md` follows a fixed order: seven-section defense → lyric → two-column annotated
  lyric → notes — because** the traditional Afrikaans Reformed audience must be convinced the
  canon honors Scripture-bound worship (regulative principle, confessional discipline, lineage)
  before engaging the lyric. Using identical headings in identical order across all 72 makes the
  canon read as one disciplined architecture. `songs/_TEMPLATE.md` holds the template.
- **Theology first: the defense is written before the lyric, and the §7 lyric brief is the
  approval gate — because** a song without a locked defense is not ready for lyric review; the
  brief is the standard every lyric (and later revision) is tested against.
- **The annotated two-column table is regenerated whenever the lyric changes — because** every
  line's scriptural/confessional warrant must stay visible and accurate to anyone scrutinising
  the song line by line.
- **Defense prose is terse, declarative, no devotional softening — because** it matches the
  Reformed idiom and Attie's tone preference.

## Production workflow

- **Theology is durable and locked first; melody, exact metre, key, and refrain are held loosely
  and reconciled to the recording — because** generation overrides modal/key intent (Song 3:
  D Dorian → B♭ major, no-refrain → refrain-after-every-stanza). Mark `metre`/`key_suggestion`
  provisional; don't commit a lead sheet until the melody is settled.
- **Lead the music generation with a positive 2026 aesthetic vision, not a wall of negatives —
  because** stacked refusals leave generation nowhere to land but the dullest traditional hymn;
  open with a vivid contemporary-sacred vision (2–3 current reference artists + genre fusion +
  distinctive textures) and keep only the 2–3 load-bearing negatives. The demo is an artistic
  2026 rendering; singability lives in the lead sheet.
- **Song pages (`songs/NNN-*.md`) never name any production tool — because** the pages are the
  public canon documenting the theological-musical artifact, not the tooling; naming a transient
  AI tool dates the work and clashes with the lineage frame. Use composed/recorded/discovered/
  sketched. Tool-talk belongs in `prompts/` (gitignored, local-only). Audited 2026-06-01.

## Aesthetic calibration

- **The warm aesthetic is the landing zone: warm, intimate, melody-first, atmospheric, spacious,
  hook-led, rich warm harmony, ~76 BPM (locked by Song 4) — because** "modern/2026" for Attie
  means warmth on a real tune with room to breathe, never cold/experimental abstraction nor
  busy/dense arrangement. "Let it rest, let it air, let it build." Chase the pattern, not a
  single genre tag.
- **Named-artist references carry their full performance aesthetic, so anchor sacred close-harmony
  on sacred-classical names only (Voces8, Chanticleer, The Sixteen, Tenebrae, Whitacre,
  Lauridsen, Pärt, Bach) and exclude commercial vocal-group names (Gaither, Voctave, Take 6,
  Pentatonix) — because** generation pulls toward a reference's overall register, not its
  structure; commercial names produced a "shoop-shoop choir" on Song 6. For descending
  walking-bass reverence, anchor on Bach's Air on a G String, not Pachelbel's Canon.

## Scores & tooling

- **suggested:** Produce piano scores by **step-time entry via the Roland FP-E50** into flat.io
  or MuseScore (or transcribe with the ByteDance model / Klangio and interchange as **MusicXML**,
  not MIDI) — because the old stem-to-MIDI-then-Logic-cleanup path was too slow; step entry
  yields zero cleanup. (From a Claude recommendation Attie explored, not confirmed as adopted.)

## Licensing

- **Dual license: creative content under CC BY-SA 4.0, code under MIT — so** congregations may
  freely sing, print, project, record, translate, and arrange the works with attribution and
  share-alike, while the build tooling stays permissively reusable. Attribution: "Words and music
  by Attie Retief, from Paraverses, licensed under CC BY-SA 4.0."
