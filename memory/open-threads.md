# Open threads — unresolved work, TODOs, things to revisit

## Canon scope still open (from `framework.yaml` decisions.open)

- **Exact song counts per movement** within the 18 / 36 / 18 arc targets — and whether any hinge
  (e.g. a closing Amen or doxology) is deliberately a single song.
- **Whether to publish with a companion keyboard/accompaniment edition** from the outset, given
  the single-instrument, congregation-led intent.

## Songwriting backlog

- Only songs **001–007** exist so far against a target of ~72; movements 4–9 are largely unwritten.
  Each new song needs the full seven-section defense before its lyric.

## Known inconsistency to clean up

- **Stale claims left in `prompts/003-*.md`** (Song 3): after reconciling the song `.md` to the
  recording, the prompt file was left carrying both new and stale claims side by side (the cue
  says "REFRAIN after every verse" while bullets below still say "NO REFRAIN... five stanzas only"
  and "the B-line breathes; it does not climax"). When a `prompts/NNN-*.md` is revised, rewrite it
  to be internally consistent rather than layering new claims on old. (`prompts/` is gitignored,
  local-only.)

## Production traps to keep in mind

- Music generation defaults toward a threefold "Holy, Holy, Holy" wherever it detects Isaiah 6 —
  watch for it on the relevant movements.
- Set Mixed/Choir gender in generation; a Male picker locked Songs 1–2 into solo baritone.
- Vary one axis at a time when riffing generations.

## Scores workflow — not yet settled

- The **piano-score pipeline** (ByteDance/Klangio transcription → MusicXML → flat.io, vs step-time
  entry from the Roland FP-E50) was explored but not confirmed as the adopted process. Revisit and
  lock a repeatable path before generating scores at scale.
