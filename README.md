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
pip install pyyaml
python scripts/build_site.py
# open site/index.html
```

## Status lifecycle

| status | meaning | progress weight |
|---|---|---|
| `idea` | passage chosen, nothing written | 0 |
| `draft-lyric` | lyric drafted | 0.4 |
| `draft-melody` | melody sketched | 0.7 |
| `complete` | lyric + melody done | 1.0 |

---

*"Once it is finished, one should be able to look back at the body of work and see
the arc, see the intent — see the Gospel."*
