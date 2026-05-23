# Paraverses — A Sung Gospel

A bounded body of **newly composed worship songs** — original lyrics and original
music — in the lineage of the Reformed *Skrifberymings* (GKSA) and the Scottish
*Paraphrases* (1781). Not a translation: an original canon, worked out up front so
the finished body can be read back as one architecture in which the Gospel is visible.

- **Target:** ~72 songs across 3 arcs / 9 movements
- **Use:** working hymnal — simple, congregation-led melodies, singable without a band
- **Threads:** Light · The Name · Water & Thirst
- **Macro-frame:** Heidelberg's *guilt – grace – gratitude* (ellende – verlossing – dankbaarheid)

See [`docs/Paraverses_Framework.docx`](docs/) for the full framework, and the live
progress dashboard (built from this repo) on the project site.

## How it works

The **repository is the canon.** Each song is a Markdown file in [`songs/`](songs/)
with YAML front-matter. The framework lives in [`framework.yaml`](framework.yaml).
The public progress site is **generated** from these — you never update progress by
hand; it reflects what is committed.

```
paraverses/
├── framework.yaml          # the canon's structure (arcs, movements, threads, targets)
├── songs/                  # one Markdown file per Paraverse (NNN-slug.md)
├── scripts/build_site.py   # reads framework + songs → site/index.html
├── site/                   # generated static site (published)
├── docs/                   # the framework Word document + reference material
└── .github/workflows/      # CI: rebuild + publish the site on every push
```

## Adding a song

1. Copy `songs/_TEMPLATE.md` to `songs/NNN-your-slug.md`.
2. Fill the front-matter (`number`, `movement`, `title`, `scripture`, `status`,
   `threads`) and write the lyric.
3. Set `status` to one of: `idea`, `draft-lyric`, `draft-melody`, `complete`.
4. Commit. The site rebuilds and progress updates automatically.

## Build locally

```bash
# Python dependencies
pip install -r requirements.txt

# Lead-sheet renderer (ABC → SVG)
brew install abcm2ps       # macOS
sudo apt-get install -y abcm2ps   # Ubuntu/Debian

python scripts/build_site.py
# open site/index.html
```

Songs may include a `Lead sheet` section with an `abc` fenced code block; the
build script pipes it through `abcm2ps -v` and embeds the resulting SVG inline.
Songs may also have a demo MP3 at `audio/<slug>.mp3` — when present, the build
copies it to `site/audio/` and renders an `<audio>` player on the song page.

## Status lifecycle

| status | meaning | progress weight |
|---|---|---|
| `idea` | passage chosen, nothing written | 0 |
| `draft-lyric` | lyric drafted | 0.4 |
| `draft-melody` | melody sketched | 0.7 |
| `complete` | lyric + melody done | 1.0 |

## Licensing

Two licenses cover this repository:

- **Lyrics, music, lead sheets, demo recordings, framework prose** —
  [Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/).
  Congregations are free to sing, print, project, record, translate, and arrange
  these works without further permission, provided attribution is given and any
  derivative works are released under the same license. See [`LICENSE-CONTENT`](LICENSE-CONTENT).
- **Build scripts and site code** — [MIT](LICENSE).

Required attribution for any reuse of the creative content:

> Words and music by Attie Retief, from Paraverses, licensed under CC BY-SA 4.0.

---

*"Once it is finished, one should be able to look back at the body of work and see
the arc, see the intent — see the Gospel."*
