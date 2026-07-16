# History — how we got here

A chronological narrative of what has been worked on in this repo and its domain.

## Origins — from translation to an original canon

- The project began as a plan to **translate Afrikaans Skrifberymings into English worship
  songs**, then evolved through research into a fully original project: **Paraverses** — a
  bounded body of newly composed English worship songs (original lyrics and music) in the
  lineage of the Reformed Skrifberymings and the Scottish Paraphrases of 1781. Attie coined
  the name "Paraverses."
- The source research untangled three overlapping Skrifberyming numbering systems (old Totius
  1–50, the 2017 GKSA single 1–79, and a grouped "group-item" format in Attie's Psalmboek
  edition), verified against official GKSA sources (cjbf.co.za, holder of the authoritative
  2017 bundle of 79 Skrifberymings). A master index (`Skrifberyming_Meester_Indeks.xlsx`) was
  built with all 79 texts, Scripture references, cross-referenced numbering, and honest
  source-attribution. Key confirmed finding: grouped SB 12-3 maps to 2017 SB 72 ("Enigste
  Here, enkele Wese," a Trinitarian/Athanasian confession). The Scottish Paraphrases (1781,
  ~67 items) were researched as the closest English-Reformed cognate tradition.

## Framework and repo scaffold

- The canon's structure was worked out up front and captured in `framework.yaml` — the master
  working document (three arcs on the Heidelberg guilt–grace–gratitude frame, nine movements,
  three threads: Light / the Name / Water & Thirst, ~72 songs). The original framework Word
  doc was retired (commit 4f24cae); `framework.yaml` supersedes it.
- The repo was scaffolded as a generate-from-source static site: `songs/NNN-slug.md` +
  `framework.yaml` → `scripts/build_site.py` → `site/`, published by GitHub Actions to
  paraverses.attieretief.com. Tone and collaboration preferences were confirmed during this
  scaffold session (terse, unsentimental).

## Song-file architecture locked

- **2026-05-22:** The song `.md` structure was locked — the seven-section theological defense
  spine, then lyric, then the two-column annotated lyric (regulative-principle warrant). The
  discipline: theology first, defense before lyric, §7 lyric brief as the approval gate.
  Captured in `songs/_TEMPLATE.md`.

## Song production — lessons through Songs 1–7

- **Songs 1–2** got locked into solo baritone by a Male gender picker in generation; the fix
  is to set Mixed/Choir.
- **Song 3 (*My Eyes Have Seen the Lord*):** the defense was written for one melodic shape
  (AAAB, B-line drops, no refrain, D Dorian) but the recording came back inverted (B-line
  climbs, a half-speed refrain after every stanza, B♭ major 4/4). The song `.md` was reconciled
  to the recording. This crystallized the rule: **theology is durable; melody/metre/key are
  discovered in generation and reconciled after, not committed up front.** Also: lead the music
  generation with a positive 2026 aesthetic vision, not a wall of negatives (learned on Songs
  3–4, 2026-05-27).
- **Song 4 (*Father of Lights*, shipped 2026-05-28):** locked the warm aesthetic — warm,
  intimate, melody-first, atmospheric, spacious, hook-led, rich warm harmony, ~76 BPM. Reached
  by rejecting cold-ambient (too cold) and irregular-metre (too experimental), steering via an
  "ethereal Blessing Offor / *Tin Roof*" compass, then dropping the soul-genre tag entirely and
  adding the spaciousness rule: "let it rest, let it air, let it build."
- **Song 5 (2026-05-28):** Attie noted he does post-editing in the studio that the `prompts/`
  cues never capture — so cues are a partial proxy for the shipped sound, not the whole picture.
- **Song 6 (*Holy Is Your Name*, 2026-06-01):** a generation came back as a "ghastly 4-part
  shoop-shoop choir." Diagnosis: named-artist references carry their full performance aesthetic;
  commercial close-harmony names (Gaither, Pentatonix, Take 6, Voctave) pull toward showbiz.
  Anchor sacred close-harmony on sacred-classical names only (Voces8, Chanticleer, Whitacre,
  Bach). Same day: audited songs 3 and 6 to strip any production-tool references from the public
  song pages.

## Tooling / scores workflow

- Explored producing **playable piano scores** from the compositions. Prior workflow used
  generated stem-to-MIDI cleaned in Logic then beautified in flat.io — the Logic step was too
  slow. Recommendation: replace stem-to-MIDI with the **ByteDance piano transcription** model
  (`piano_transcription_inference`) or Klangio, and shift the interchange format from MIDI to
  **MusicXML** for cleaner flat.io import. A ByteDance transcription was run successfully on one
  file (1,044 notes, ~72 BPM, few artifacts). Cleanest score path going forward: **step-time
  entry** directly into flat.io or MuseScore using Attie's **Roland FP-E50** as a MIDI input
  device (USB Computer port, plain piano mode, accompaniment off) — zero cleanup.
- Video pipeline (`scripts/build_video.py`, `scripts/upload_youtube.py`) added for sing-along
  MP4s and YouTube upload with URLs written back into song front-matter.

_As of mid-2026, songs 001–007 exist in the repo._
