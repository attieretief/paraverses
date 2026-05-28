#!/usr/bin/env python3
"""Build the Paraverses progress site from framework.yaml + songs/*.md.

Usage: python scripts/build_site.py
Outputs:
  site/index.html        — landing page
  site/songs/*.html      — one page per song (drill-in)
  site/data.json         — small summary blob
"""
import os, re, json, html, datetime, sys, shutil, subprocess, tempfile

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

try:
    import markdown as md
except ImportError:
    sys.exit("markdown required: pip install markdown")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONGS = os.path.join(ROOT, "songs")
AUDIO = os.path.join(ROOT, "audio")
SITE = os.path.join(ROOT, "site")
SITE_SONGS = os.path.join(SITE, "songs")
SITE_AUDIO = os.path.join(SITE, "audio")

GREEN, GOLD, CREAM, SLATE = "#1A2E1E", "#C9A84C", "#F7F4EF", "#5A6B5E"

FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.S)

def load_framework():
    with open(os.path.join(ROOT, "framework.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_songs():
    songs = []
    if not os.path.isdir(SONGS):
        return songs
    for fn in sorted(os.listdir(SONGS)):
        if not fn.endswith(".md") or fn.startswith("_"):
            continue
        with open(os.path.join(SONGS, fn), encoding="utf-8") as f:
            text = f.read()
        m = FM.match(text)
        if m:
            meta = yaml.safe_load(m.group(1)) or {}
            body = m.group(2)
        else:
            meta, body = {}, text
        meta["_file"] = fn
        meta["_slug"] = fn[:-3]
        meta["_body"] = body
        songs.append(meta)
    return songs

def status_weight(fw, sid):
    for s in fw["statuses"]:
        if s["id"] == sid:
            return s["weight"]
    return 0.0

def status_label(fw, sid):
    return {s["id"]: s["label"] for s in fw["statuses"]}.get(sid, sid)

def arc_label(fw, arc_id):
    for a in fw["arcs"]:
        if a["id"] == arc_id:
            return a
    return {"label": arc_id, "gloss": ""}

CSS = f"""
:root {{ --green:{GREEN}; --gold:{GOLD}; --cream:{CREAM}; --slate:{SLATE}; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:Georgia,'Times New Roman',serif; color:#222;
        background:var(--cream); line-height:1.6; }}
.wrap {{ max-width:880px; margin:0 auto; padding:48px 24px 96px; }}
header.hero {{ text-align:center; padding:40px 0 24px; }}
.hero h1 {{ font-size:54px; letter-spacing:2px; color:var(--green); margin:0; }}
.hero .tag {{ font-style:italic; color:var(--slate); font-size:22px; margin-top:4px; }}
.hero .sub {{ color:var(--slate); font-size:15px; margin-top:10px; }}
.hero .doc {{ color:var(--slate); font-size:12px; letter-spacing:1px;
              text-transform:uppercase; margin-top:14px; }}
.hero p.desc {{ color:#444; max-width:620px; margin:18px auto 0; }}
.aim {{ max-width:680px; margin:24px auto 0; padding:18px 22px;
        border-left:3px solid var(--gold); background:white; color:#333;
        font-style:italic; }}
.meter {{ margin:32px auto; max-width:620px; }}
.meter .bar {{ height:14px; background:#e3ddd0; border-radius:8px; overflow:hidden; }}
.meter .fill {{ height:100%; background:linear-gradient(90deg,var(--green),var(--gold)); }}
.meter .label {{ display:flex; justify-content:space-between; font-size:14px; color:var(--slate); margin-top:6px; }}
h2.section {{ color:var(--green); border-bottom:2px solid var(--gold); padding-bottom:6px;
              margin-top:56px; font-size:26px; }}
h2.arc {{ color:var(--green); border-bottom:2px solid var(--gold); padding-bottom:6px;
          margin-top:48px; font-size:26px; }}
h2.arc .gloss {{ color:var(--slate); font-weight:normal; font-size:18px; }}
h2.arc .ct {{ float:right; color:var(--gold); font-size:16px; }}
.lede {{ color:#444; margin:14px 0 8px; }}
.arc-blurb {{ color:#555; font-style:italic; margin:8px 0 16px; }}
.principles {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; margin:18px 0; }}
@media (max-width:640px) {{ .principles {{ grid-template-columns:1fr; }} }}
.principle {{ background:white; border:1px solid #e3ddd0; border-radius:10px; padding:14px 16px; }}
.principle h4 {{ margin:0 0 4px; color:var(--green); font-size:16px; }}
.principle p {{ margin:0; font-size:14px; color:#444; }}
.mv {{ background:white; border:1px solid #e3ddd0; border-radius:10px; padding:18px 20px; margin:14px 0; }}
.mv h3 {{ margin:0 0 2px; color:var(--green); font-size:19px; }}
.mv .sub {{ color:var(--slate); font-style:italic; font-size:15px; }}
.mv .pass {{ font-size:14px; color:#555; margin-top:8px; }}
.mv .mvbar {{ height:8px; background:#eee; border-radius:5px; overflow:hidden; margin-top:12px; }}
.mv .mvfill {{ height:100%; background:var(--gold); }}
.mv .mvmeta {{ font-size:13px; color:var(--slate); margin-top:5px; }}
.songs {{ list-style:none; padding:0; margin:10px 0 0; }}
.songs li {{ font-size:14px; padding:6px 0; border-top:1px dotted #e3ddd0;
              display:flex; justify-content:space-between; align-items:center; gap:10px; }}
.songs a {{ color:var(--green); text-decoration:none; border-bottom:1px solid transparent; }}
.songs a:hover {{ border-bottom-color:var(--gold); }}
.pill {{ font-size:11px; padding:2px 8px; border-radius:10px; color:white;
         white-space:nowrap; }}
.threads {{ margin-top:20px; }}
.thread {{ background:white; border:1px solid #e3ddd0; border-radius:10px;
            padding:18px 22px; margin:14px 0; }}
.thread h3 {{ color:var(--gold); margin:0 0 4px; font-size:20px; }}
.thread .tline {{ font-style:italic; color:var(--slate); margin-bottom:10px; }}
.thread .inarc {{ margin:8px 0; font-size:14px; color:#444; }}
.thread .inarc b {{ color:var(--green); }}
.decisions .resolved, .decisions .open {{
    background:white; border:1px solid #e3ddd0; border-radius:10px;
    padding:14px 18px; margin:12px 0; }}
.decisions h4 {{ margin:0 0 6px; color:var(--green); font-size:16px; }}
.decisions ol {{ margin:6px 0 0 18px; padding:0; color:#444; }}
.decisions p {{ margin:0; color:#444; }}
.lineage {{ background:white; border:1px solid #e3ddd0; border-radius:10px;
            padding:18px 22px; margin:14px 0; color:#444; }}
footer {{ text-align:center; color:var(--slate); font-size:13px; margin-top:48px; }}
footer div {{ margin:2px 0; }}
footer a, .song-page .body a, .song-page .ascription a {{
    color:inherit; border-bottom:1px solid var(--gold); text-decoration:none; }}
footer a:hover, .song-page .body a:hover, .song-page .ascription a:hover {{
    color:var(--green); }}

/* Song-page specifics */
.song-page {{ max-width:1080px; margin:0 auto; padding:48px 24px 96px; }}
.song-page .back {{ color:var(--slate); font-size:13px; text-decoration:none;
                     letter-spacing:1px; text-transform:uppercase; }}
.song-page .back:hover {{ color:var(--green); }}
.song-page .present-link {{ float:right; color:var(--green); font-size:13px;
                              text-decoration:none; letter-spacing:1px;
                              text-transform:uppercase; border:1px solid var(--gold);
                              border-radius:6px; padding:6px 12px; }}
.song-page .present-link:hover {{ background:var(--green); color:var(--cream); }}
.song-page h1 {{ color:var(--green); font-size:38px; margin:18px 0 4px; }}
.song-page .ascription {{ color:var(--slate); font-style:italic; margin-bottom:18px; }}
.song-page .meta {{ background:white; border:1px solid #e3ddd0; border-radius:10px;
                     padding:14px 18px; margin:10px 0 24px; font-size:14px; }}
.song-page .meta dt {{ color:var(--slate); float:left; width:140px; clear:left; }}
.song-page .meta dd {{ margin:0 0 4px 150px; color:#333; }}
.song-page .meta dd:after {{ content:""; display:block; clear:both; }}
.song-page .body h2 {{ color:var(--green); font-size:20px; margin-top:24px;
                       border-bottom:1px solid #e3ddd0; padding-bottom:4px; }}
.song-page .body h3 {{ color:var(--green); font-size:17px; }}
.song-page .body p {{ white-space:pre-line; }}
.song-page .body hr {{ border:0; border-top:1px solid #e3ddd0; margin:24px 0; }}
.song-page .body em {{ color:var(--slate); }}
.song-page .demo {{ background:white; border:1px solid #e3ddd0; border-radius:10px;
                     padding:14px 18px; margin:10px 0 24px; }}
.song-page .demo-label {{ font-size:12px; color:var(--slate); letter-spacing:1px;
                           text-transform:uppercase; margin-bottom:6px; }}
.song-page .demo audio {{ width:100%; display:block; }}
.song-page .demo-empty {{ color:var(--slate); font-style:italic; font-size:14px;
                           padding:4px 0; }}
.song-page .demo .yt {{ display:inline-block; margin-top:8px; font-size:12px;
                          letter-spacing:1px; text-transform:uppercase;
                          color:var(--green); text-decoration:none;
                          border-bottom:1px solid var(--gold); }}
.song-page .demo .yt:hover {{ color:var(--gold); }}
.song-page .lead-sheet {{ background:white; border:1px solid #e3ddd0; border-radius:10px;
                           padding:14px 18px; margin:18px 0; overflow-x:auto; }}
.song-page .lead-sheet svg {{ max-width:100%; height:auto; display:block;
                               margin:0 auto; }}
.song-page .lead-sheet-error {{ color:#a00; font-family:Menlo,monospace; font-size:13px; }}
.song-page .lead-sheet-error pre {{ background:#fafafa; border:1px solid #eee;
                                      padding:8px 10px; margin-top:8px;
                                      white-space:pre-wrap; }}
"""

LICENSE_LINK = "https://creativecommons.org/licenses/by-sa/4.0/"
LICENSE_LABEL = "CC BY-SA 4.0"

def pill(fw, sid):
    colors = {"idea":"#aaa","draft-lyric":"#b08900","draft-melody":"#7a8b6e","complete":GREEN}
    return f'<span class="pill" style="background:{colors.get(sid,"#aaa")}">{html.escape(status_label(fw, sid))}</span>'

ABC_FORMAT_PRELUDE = (
    "%%staffsep 80\n"
    "%%sysstaffsep 24\n"
)

def render_abc_to_svg(abc_text):
    """Render ABC notation text to inline SVG via abcm2ps. Returns SVG or None."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".abc", delete=False,
                                         encoding="utf-8") as f:
            f.write(ABC_FORMAT_PRELUDE)
            f.write(abc_text)
            tmp_path = f.name
        result = subprocess.run(
            ["abcm2ps", "-v", "-O", "-", tmp_path],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        return result.stdout
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

ABC_BLOCK_RE = re.compile(r'<pre><code class="language-abc">(.*?)</code></pre>', re.S)

def expand_abc_in_html(body_html):
    """Replace ```abc fenced blocks (already rendered as <pre><code>) with SVG lead sheets."""
    def replace(m):
        abc_text = html.unescape(m.group(1))
        svg = render_abc_to_svg(abc_text)
        if svg is None:
            return ('<div class="lead-sheet lead-sheet-error">'
                    'ABC source could not be rendered (abcm2ps unavailable or invalid syntax). '
                    'Source:<pre>' + html.escape(abc_text) + '</pre></div>')
        return f'<div class="lead-sheet">{svg}</div>'
    return ABC_BLOCK_RE.sub(replace, body_html)

LEAD_SHEET_SECTION_RE = re.compile(
    r'<h2>Lead sheet</h2>\s*(<div class="lead-sheet[^"]*">.*?</div>)',
    re.S,
)

def extract_lead_sheet(body_html):
    """Pull the Lead sheet heading + rendered notation out of the body so it can be
    placed beside the demo audio. Returns (body_without_lead_sheet, lead_sheet_html or None)."""
    m = LEAD_SHEET_SECTION_RE.search(body_html)
    if not m:
        return body_html, None
    return LEAD_SHEET_SECTION_RE.sub("", body_html, count=1), m.group(1)

LYRIC_SECTION_RE = re.compile(
    r"^##\s+(?:<a[^>]*></a>\s*)?Lyric\s*$(.*?)^##\s",
    re.S | re.M,
)
SLIDE_RE = re.compile(
    r"^###\s+(?P<title>.+?)\s*$\n(?P<body>(?:(?:^>.*\n?)|(?:^\s*\n))+)",
    re.M,
)

def get_audio_variants(slug):
    """Return [(filename, label)] for every audio file matching this song's slug."""
    variants = []
    if not os.path.isdir(AUDIO):
        return variants
    for fn in sorted(os.listdir(AUDIO)):
        if not fn.endswith(".mp3"):
            continue
        if fn == f"{slug}.mp3":
            variants.append((fn, "Demo recording"))
        elif fn.startswith(f"{slug}-"):
            suffix = fn[len(slug) + 1:-4]
            variants.append((fn, suffix.replace("-", " ").capitalize()))
    return variants

def get_cues(song):
    """Normalise the song's `cues:` frontmatter to {filename: [float, ...]}.

    Accepted forms:
      cues: [0, 18.5, 28.2]           -> applies to {slug}.mp3
      cues: {filename.mp3: [0, ...]}  -> per-file mapping
    """
    raw = song.get("cues")
    if not raw:
        return {}
    slug = song["_slug"]
    if isinstance(raw, list):
        return {f"{slug}.mp3": [float(t) for t in raw]}
    if isinstance(raw, dict):
        return {str(k): [float(t) for t in v] for k, v in raw.items()}
    return {}

def parse_lyric_slides(body_md):
    """Extract presentation slides from a song's Lyric section.

    Each `### Heading` followed by a blockquote becomes one slide:
    {title, lines: [str, ...]}. Returns [] when no Lyric section is found.
    """
    m = LYRIC_SECTION_RE.search(body_md + "\n## __end__\n")
    if not m:
        return []
    section = m.group(1)
    slides = []
    for sm in SLIDE_RE.finditer(section):
        title = sm.group("title").strip()
        raw = sm.group("body")
        lines = []
        for ln in raw.splitlines():
            ln = ln.strip()
            if not ln.startswith(">"):
                continue
            text = ln.lstrip(">").strip()
            if text:
                lines.append(text)
        if lines:
            slides.append({"title": title, "lines": lines})
    return slides

def render_song_page(fw, song):
    title = str(song.get("title", "(untitled)"))
    num = song.get("number", "—")
    mv_id = song.get("movement")
    mv_title = ""
    arc_label_text = ""
    for arc in fw["arcs"]:
        for mv in arc["movements"]:
            if mv["id"] == mv_id:
                mv_title = mv["title"]
                arc_label_text = f"{arc['gloss']} ({arc['label']})"
                break
    body_md = song.get("_body", "").strip()
    body_md = re.sub(r"^#\s+.*\n+", "", body_md, count=1)
    body_html = md.markdown(body_md, extensions=["extra"])
    body_html = expand_abc_in_html(body_html)
    body_html, lead_sheet_html = extract_lead_sheet(body_html)

    out = []
    out.append("<!doctype html><html lang='en'><head><meta charset='utf-8'>")
    out.append("<meta name='viewport' content='width=device-width,initial-scale=1'>")
    out.append("<meta name='author' content='Attie Retief'>")
    out.append(f"<title>{html.escape(title)} — Paraverses</title>")
    out.append(f"<style>{CSS}</style></head><body><div class='song-page'>")
    out.append("<a class='back' href='../index.html'>&larr; Paraverses</a>")
    has_slides = bool(parse_lyric_slides(song.get("_body", "")))
    slug_esc = html.escape(song["_slug"])
    if has_slides and get_audio_variants(song["_slug"]):
        out.append(f"<a class='present-link' href='{slug_esc}-preview.html'>"
                   "Sing along &rarr;</a>")
    if has_slides:
        out.append(f"<a class='present-link' href='{slug_esc}-present.html'>"
                   "Present &rarr;</a>")
    out.append(f"<h1>{html.escape(title)}</h1>")
    out.append(f"<div class='ascription'>Paraverse {html.escape(str(num))} · "
               f"Movement {html.escape(str(mv_id))} — {html.escape(mv_title)} · "
               f"<span>{html.escape(arc_label_text)}</span></div>")

    out.append("<dl class='meta'>")
    def row(label, val):
        if val:
            out.append(f"<dt>{html.escape(label)}</dt><dd>{html.escape(str(val))}</dd>")
    row("Status", status_label(fw, song.get("status", "idea")))
    row("Scripture", song.get("scripture"))
    threads = song.get("threads") or []
    if threads:
        row("Threads", ", ".join(threads))
    row("Metre", song.get("metre"))
    row("Key", song.get("key_suggestion"))
    row("Written", song.get("written"))
    out.append("</dl>")

    audio_variants = get_audio_variants(song["_slug"])
    yt_map = song.get("youtube") or {}
    if not isinstance(yt_map, dict):
        yt_map = {}
    if audio_variants:
        for fn, label in audio_variants:
            out.append("<div class='demo'>")
            out.append(f"<div class='demo-label'>{html.escape(label)}</div>")
            out.append(f"<audio controls preload='metadata' "
                       f"src='../audio/{html.escape(fn)}'></audio>")
            yt = yt_map.get(fn)
            if yt:
                out.append(f"<a class='yt' href='{html.escape(str(yt))}' "
                           f"target='_blank' rel='noopener'>Watch on YouTube &rarr;</a>")
            out.append("</div>")
    else:
        out.append("<div class='demo'>"
                   "<div class='demo-label'>Demo recording</div>"
                   "<div class='demo-empty'>Coming soon.</div>"
                   "</div>")

    if lead_sheet_html:
        out.append(lead_sheet_html)

    out.append(f"<div class='body'>{body_html}</div>")
    year = datetime.date.today().year
    out.append("<footer>"
               f"<div>Words and music &copy; {year} "
               "<a href='https://attieretief.com'>Attie Retief</a>. "
               f"Licensed under <a href='{LICENSE_LINK}'>{LICENSE_LABEL}</a>.</div>"
               "<div>Free to sing, print, project, record, translate, and arrange "
               "with attribution and same-license sharing.</div>"
               "</footer>")
    out.append("</div></body></html>")
    return "\n".join(out)

PRESENT_CSS = """
* { box-sizing:border-box; }
html, body { margin:0; padding:0; height:100%; overflow:hidden;
              background:#070b08; color:#f5efe1;
              font-family:Georgia,'Times New Roman',serif; }
body.idle { cursor:none; }
.bg { position:fixed; inset:0; z-index:0;
       background:
         radial-gradient(circle at 20% 30%, rgba(201,168,76,0.18), transparent 55%),
         radial-gradient(circle at 80% 70%, rgba(26,46,30,0.85), transparent 60%),
         linear-gradient(160deg, #0d1810 0%, #050807 60%, #0a1410 100%);
       background-size: 140% 140%;
       animation: drift 60s ease-in-out infinite alternate; }
@keyframes drift {
  0%   { background-position: 0% 0%, 100% 100%, 0% 0%; }
  100% { background-position: 30% 20%, 70% 80%, 50% 50%; }
}
.stage { position:relative; z-index:1; height:100%;
          display:flex; flex-direction:column; }
.topbar { display:flex; justify-content:space-between; align-items:center;
           padding:18px 28px; font-size:13px; letter-spacing:1.5px;
           text-transform:uppercase; color:rgba(245,239,225,0.55); }
.topbar a { color:inherit; text-decoration:none; border-bottom:1px solid transparent; }
.topbar a:hover { border-bottom-color:#c9a84c; color:#f5efe1; }
.title { color:rgba(245,239,225,0.7); }
.indicator { font-variant-numeric: tabular-nums; }
.slide-wrap { flex:1; position:relative; padding:24px 6vw; }
.slide { position:absolute; inset:0; display:flex; flex-direction:column;
          align-items:center; justify-content:center; text-align:center;
          padding:24px 6vw; opacity:0; pointer-events:none;
          transition:opacity 360ms ease; }
.slide.show { opacity:1; pointer-events:auto; }
.slide > * { max-width:1100px; }
.label { font-style:italic; font-size:clamp(16px,2vw,22px);
          color:#c9a84c; letter-spacing:2px; text-transform:uppercase;
          margin-bottom:28px; }
.lyric { font-size:clamp(28px,5.2vw,68px); line-height:1.35;
          font-weight:400; text-shadow:0 2px 24px rgba(0,0,0,0.6); }
.lyric .line { display:block; margin:0.1em 0; }
.dots { display:flex; justify-content:center; gap:8px;
         padding:14px 0 22px; }
.dot { width:8px; height:8px; border-radius:50%;
        background:rgba(245,239,225,0.18); transition:background 200ms; }
.dot.active { background:#c9a84c; }
.hint { position:fixed; bottom:14px; right:18px; z-index:2;
         font-size:11px; letter-spacing:1.5px; text-transform:uppercase;
         color:rgba(245,239,225,0.35); transition:opacity 600ms; }
body.idle .hint { opacity:0; }
@media (max-width:640px) {
  .topbar { padding:12px 16px; font-size:11px; }
  .lyric { font-size:clamp(22px,7vw,40px); }
}
"""

PRESENT_JS = """
(function(){
  var slides = document.querySelectorAll('.slide');
  var dots = document.querySelectorAll('.dot');
  var indicator = document.getElementById('indicator');
  var total = slides.length;
  var i = 0;
  function show(n){
    if (n < 0) n = 0;
    if (n >= total) n = total - 1;
    slides[i].classList.remove('show');
    if (dots[i]) dots[i].classList.remove('active');
    i = n;
    slides[i].classList.add('show');
    if (dots[i]) dots[i].classList.add('active');
    if (indicator) indicator.textContent = (i + 1) + ' / ' + total;
  }
  function next(){ if (i < total - 1) show(i + 1); }
  function prev(){ if (i > 0) show(i - 1); }
  document.addEventListener('keydown', function(e){
    var k = e.key;
    if (k === ' ' || k === 'ArrowRight' || k === 'PageDown' || k === 'Enter') {
      e.preventDefault(); next();
    } else if (k === 'ArrowLeft' || k === 'PageUp' || k === 'Backspace') {
      e.preventDefault(); prev();
    } else if (k === 'Home') {
      e.preventDefault(); show(0);
    } else if (k === 'End') {
      e.preventDefault(); show(total - 1);
    } else if (k === 'f' || k === 'F') {
      e.preventDefault();
      if (!document.fullscreenElement) document.documentElement.requestFullscreen();
      else document.exitFullscreen();
    } else if (k === 'Escape') {
      if (document.fullscreenElement) document.exitFullscreen();
    }
  });
  document.addEventListener('click', function(e){
    if (e.target.closest('a')) return;
    var w = window.innerWidth;
    if (e.clientX < w * 0.25) prev(); else next();
  });
  var idleTimer;
  function wake(){
    document.body.classList.remove('idle');
    clearTimeout(idleTimer);
    idleTimer = setTimeout(function(){ document.body.classList.add('idle'); }, 2500);
  }
  document.addEventListener('mousemove', wake);
  document.addEventListener('touchstart', wake);
  wake();
  show(0);
})();
"""

def render_presentation_page(fw, song, slides):
    title = str(song.get("title", "(untitled)"))
    num = song.get("number", "—")
    slug = song["_slug"]
    out = []
    out.append("<!doctype html><html lang='en'><head><meta charset='utf-8'>")
    out.append("<meta name='viewport' content='width=device-width,initial-scale=1'>")
    out.append("<meta name='author' content='Attie Retief'>")
    out.append(f"<title>{html.escape(title)} — Present</title>")
    out.append(f"<style>{PRESENT_CSS}</style></head>")
    out.append("<body><div class='bg'></div><div class='stage'>")
    out.append("<div class='topbar'>"
               f"<a href='{html.escape(slug)}.html'>&larr; Back</a>"
               f"<div class='title'>Paraverse {html.escape(str(num))} · {html.escape(title)}</div>"
               "<div class='indicator' id='indicator'></div>"
               "</div>")
    out.append("<div class='slide-wrap'>")
    for sl in slides:
        out.append("<div class='slide'>")
        out.append(f"<div class='label'>{html.escape(sl['title'])}</div>")
        out.append("<div class='lyric'>")
        for line in sl["lines"]:
            out.append(f"<span class='line'>{html.escape(line)}</span>")
        out.append("</div></div>")
    out.append("</div>")
    out.append("<div class='dots'>")
    for _ in slides:
        out.append("<span class='dot'></span>")
    out.append("</div></div>")
    out.append("<div class='hint'>Space / Click · F = Fullscreen · Esc</div>")
    out.append(f"<script>{PRESENT_JS}</script>")
    out.append("</body></html>")
    return "\n".join(out)

PREVIEW_CSS_EXTRA = """
.audio-bar { position:relative; z-index:2;
             display:flex; gap:14px; align-items:center;
             padding:14px 28px 18px;
             background:linear-gradient(180deg, transparent, rgba(0,0,0,0.55));
             flex-wrap:wrap; }
.audio-bar audio { flex:1; min-width:260px; height:38px;
                    filter:invert(0.92) hue-rotate(180deg); }
.audio-bar select { background:rgba(245,239,225,0.06); color:#f5efe1;
                     border:1px solid rgba(245,239,225,0.25); border-radius:6px;
                     padding:6px 10px; font:inherit; font-size:13px; }
.audio-bar select:focus { outline:1px solid #c9a84c; }
.audio-bar .btn { background:transparent; color:#f5efe1;
                   border:1px solid rgba(245,239,225,0.3); border-radius:6px;
                   padding:8px 14px; font:inherit; font-size:12px;
                   letter-spacing:1.5px; text-transform:uppercase; cursor:pointer;
                   transition:background 200ms, border-color 200ms; }
.audio-bar .btn:hover { border-color:#c9a84c; color:#c9a84c; }
.audio-bar .btn.recording { background:#7a1d1d; border-color:#c94c4c; color:#fff;
                              animation:pulse 1.4s ease-in-out infinite; }
@keyframes pulse {
  0%,100% { box-shadow:0 0 0 0 rgba(201,76,76,0.6); }
  50%     { box-shadow:0 0 0 8px rgba(201,76,76,0); }
}
.audio-bar .mode { font-size:11px; letter-spacing:1.5px; text-transform:uppercase;
                    color:rgba(245,239,225,0.45); }
.audio-bar .mode b { color:#c9a84c; font-weight:normal; }
.modal { position:fixed; inset:0; z-index:10;
          background:rgba(5,8,7,0.92); display:none;
          align-items:center; justify-content:center; padding:24px; }
.modal.open { display:flex; }
.modal .box { background:#0f1a13; border:1px solid rgba(201,168,76,0.4);
               border-radius:10px; padding:22px 26px; max-width:640px; width:100%;
               color:#f5efe1; }
.modal h3 { margin:0 0 6px; color:#c9a84c; font-size:18px; letter-spacing:1px; }
.modal p { margin:0 0 14px; color:rgba(245,239,225,0.7); font-size:14px; }
.modal textarea { width:100%; min-height:160px;
                   background:#050807; color:#f5efe1;
                   border:1px solid rgba(245,239,225,0.2); border-radius:6px;
                   padding:12px; font:13px/1.5 Menlo,Consolas,monospace;
                   resize:vertical; }
.modal .row { display:flex; gap:10px; margin-top:12px; justify-content:flex-end; }
"""

PREVIEW_JS = """
(function(){
  var slides = document.querySelectorAll('.slide');
  var dots = document.querySelectorAll('.dot');
  var indicator = document.getElementById('indicator');
  var audio = document.getElementById('audio');
  var variantSel = document.getElementById('variant');
  var recordBtn = document.getElementById('record');
  var modeLabel = document.getElementById('mode');
  var modal = document.getElementById('modal');
  var output = document.getElementById('output');
  var copyBtn = document.getElementById('copy');
  var closeBtn = document.getElementById('close');
  var cuesByFile = window.__CUES__ || {};
  var total = slides.length;
  var i = 0;
  var recording = false;
  var recordedTimes = [];

  function show(n){
    if (n < 0) n = 0;
    if (n >= total) n = total - 1;
    slides[i].classList.remove('show');
    if (dots[i]) dots[i].classList.remove('active');
    i = n;
    slides[i].classList.add('show');
    if (dots[i]) dots[i].classList.add('active');
    if (indicator) indicator.textContent = (i + 1) + ' / ' + total;
  }
  function currentCues(){
    var src = audio.currentSrc.split('/').pop().split('?')[0];
    return cuesByFile[decodeURIComponent(src)] || null;
  }
  function setMode(){
    if (recording) { modeLabel.innerHTML = 'Mode <b>recording</b>'; return; }
    var c = currentCues();
    modeLabel.innerHTML = c ? 'Mode <b>auto</b>' : 'Mode <b>manual</b>';
  }
  function next(){
    if (recording) {
      recordedTimes.push(audio.currentTime);
      if (i < total - 1) show(i + 1);
      return;
    }
    var c = currentCues();
    if (c && i + 1 < total && c[i + 1] != null) {
      audio.currentTime = c[i + 1];
      if (audio.paused) audio.play();
    }
    if (i < total - 1) show(i + 1);
  }
  function prev(){
    if (recording) {
      if (recordedTimes.length) recordedTimes.pop();
      if (i > 0) show(i - 1);
      return;
    }
    var c = currentCues();
    if (c && i > 0 && c[i - 1] != null) {
      audio.currentTime = c[i - 1];
    }
    if (i > 0) show(i - 1);
  }
  audio.addEventListener('timeupdate', function(){
    if (recording) return;
    var c = currentCues();
    if (!c) return;
    var target = 0;
    for (var k = 0; k < c.length && k < total; k++) {
      if (audio.currentTime + 0.05 >= c[k]) target = k;
    }
    if (target !== i) show(target);
  });
  function switchVariant(){
    if (!variantSel) return;
    var v = variantSel.value;
    audio.src = v;
    audio.load();
    show(0);
    setMode();
  }
  if (variantSel) variantSel.addEventListener('change', switchVariant);

  function startRecording(){
    recording = true;
    recordedTimes = [0];
    recordBtn.textContent = 'Stop & show cues';
    recordBtn.classList.add('recording');
    audio.currentTime = 0;
    show(0);
    setMode();
    var p = audio.play();
    if (p && p.catch) p.catch(function(){});
  }
  function stopRecording(){
    recording = false;
    recordBtn.textContent = 'Record cues';
    recordBtn.classList.remove('recording');
    audio.pause();
    setMode();
    var src = audio.currentSrc.split('/').pop().split('?')[0];
    var fname = decodeURIComponent(src);
    var fmt = recordedTimes.map(function(t){ return (Math.round(t * 10) / 10).toFixed(1); });
    var yaml = 'cues:\\n  ' + fname + ': [' + fmt.join(', ') + ']';
    output.value = yaml;
    modal.classList.add('open');
    output.select();
  }
  recordBtn.addEventListener('click', function(){
    if (recording) stopRecording(); else startRecording();
  });
  copyBtn.addEventListener('click', function(){
    output.select();
    document.execCommand('copy');
    copyBtn.textContent = 'Copied';
    setTimeout(function(){ copyBtn.textContent = 'Copy'; }, 1200);
  });
  closeBtn.addEventListener('click', function(){ modal.classList.remove('open'); });

  document.addEventListener('keydown', function(e){
    if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
    var k = e.key;
    var modalOpen = modal.classList.contains('open');
    if (k === 'Escape') {
      if (modalOpen) modal.classList.remove('open');
      else if (document.fullscreenElement) document.exitFullscreen();
      return;
    }
    if (modalOpen) return;
    if (k === ' ' || k === 'ArrowRight' || k === 'PageDown' || k === 'Enter') {
      e.preventDefault(); next();
    } else if (k === 'ArrowLeft' || k === 'PageUp' || k === 'Backspace') {
      e.preventDefault(); prev();
    } else if (k === 'Home') { e.preventDefault(); show(0); }
    else if (k === 'End') { e.preventDefault(); show(total - 1); }
    else if (k === 'f' || k === 'F') {
      e.preventDefault();
      if (!document.fullscreenElement) document.documentElement.requestFullscreen();
      else document.exitFullscreen();
    } else if (k === 'r' || k === 'R') {
      e.preventDefault();
      recordBtn.click();
    }
  });
  document.addEventListener('click', function(e){
    if (e.target.closest('a, button, audio, select, .audio-bar, .modal')) return;
    var w = window.innerWidth;
    if (e.clientX < w * 0.25) prev(); else next();
  });
  var idleTimer;
  function wake(){
    document.body.classList.remove('idle');
    clearTimeout(idleTimer);
    idleTimer = setTimeout(function(){ document.body.classList.add('idle'); }, 2500);
  }
  document.addEventListener('mousemove', wake);
  document.addEventListener('touchstart', wake);
  wake();
  show(0);
  setMode();
})();
"""

def render_preview_page(fw, song, slides, audio_variants, cues_by_file):
    title = str(song.get("title", "(untitled)"))
    num = song.get("number", "—")
    slug = song["_slug"]
    out = []
    out.append("<!doctype html><html lang='en'><head><meta charset='utf-8'>")
    out.append("<meta name='viewport' content='width=device-width,initial-scale=1'>")
    out.append("<meta name='author' content='Attie Retief'>")
    out.append(f"<title>{html.escape(title)} — Sing along</title>")
    out.append(f"<style>{PRESENT_CSS}{PREVIEW_CSS_EXTRA}</style></head>")
    out.append("<body><div class='bg'></div><div class='stage'>")
    out.append("<div class='topbar'>"
               f"<a href='{html.escape(slug)}.html'>&larr; Back</a>"
               f"<div class='title'>Paraverse {html.escape(str(num))} · {html.escape(title)}</div>"
               "<div class='indicator' id='indicator'></div>"
               "</div>")
    out.append("<div class='slide-wrap'>")
    for sl in slides:
        out.append("<div class='slide'>")
        out.append(f"<div class='label'>{html.escape(sl['title'])}</div>")
        out.append("<div class='lyric'>")
        for line in sl["lines"]:
            out.append(f"<span class='line'>{html.escape(line)}</span>")
        out.append("</div></div>")
    out.append("</div>")
    out.append("<div class='dots'>")
    for _ in slides:
        out.append("<span class='dot'></span>")
    out.append("</div>")

    out.append("<div class='audio-bar'>")
    if len(audio_variants) > 1:
        out.append("<select id='variant'>")
        for fn, label in audio_variants:
            out.append(f"<option value='../audio/{html.escape(fn)}'>"
                       f"{html.escape(label)}</option>")
        out.append("</select>")
    first_src = f"../audio/{html.escape(audio_variants[0][0])}"
    out.append(f"<audio id='audio' controls preload='metadata' src='{first_src}'></audio>")
    out.append("<button class='btn' id='record'>Record cues</button>")
    out.append("<span class='mode' id='mode'></span>")
    out.append("</div>")

    out.append("</div>")
    out.append("<div class='hint'>Space / Click · F = Fullscreen · R = Record · Esc</div>")
    out.append("<div class='modal' id='modal'><div class='box'>"
               "<h3>Recorded cues</h3>"
               "<p>Paste into the song&rsquo;s frontmatter to enable auto-advance.</p>"
               "<textarea id='output' readonly></textarea>"
               "<div class='row'>"
               "<button class='btn' id='copy'>Copy</button>"
               "<button class='btn' id='close'>Close</button>"
               "</div></div></div>")
    cues_json = json.dumps(cues_by_file)
    out.append(f"<script>window.__CUES__ = {cues_json};</script>")
    out.append(f"<script>{PREVIEW_JS}</script>")
    out.append("</body></html>")
    return "\n".join(out)

def render_index(fw, songs, by_movement):
    total_target = fw["project"]["target_total"]
    total_weight = sum(status_weight(fw, s.get("status", "idea")) for s in songs)
    overall_pct = round(100 * total_weight / total_target) if total_target else 0
    complete_count = sum(1 for s in songs if s.get("status") == "complete")
    pj = fw["project"]

    out = []
    out.append("<!doctype html><html lang='en'><head><meta charset='utf-8'>")
    out.append("<meta name='viewport' content='width=device-width,initial-scale=1'>")
    out.append("<meta name='author' content='Attie Retief'>")
    out.append(f"<title>{html.escape(pj['name'])} — {html.escape(pj['tagline'])}</title>")
    out.append(f"<style>{CSS}</style></head><body><div class='wrap'>")

    # Hero
    out.append("<header class='hero'>")
    out.append(f"<h1>{html.escape(pj['name'].upper())}</h1>")
    out.append(f"<div class='tag'>{html.escape(pj['tagline'])}</div>")
    if pj.get("subtitle"):
        out.append(f"<div class='sub'>{html.escape(pj['subtitle'].strip())}</div>")
    if pj.get("document_label"):
        out.append(f"<div class='doc'>{html.escape(pj['document_label'])}</div>")
    out.append("</header>")

    # Progress meter
    out.append("<div class='meter'><div class='bar'>"
               f"<div class='fill' style='width:{overall_pct}%'></div></div>")
    out.append(f"<div class='label'><span>{complete_count} complete · {len(songs)} in progress</span>"
               f"<span>{overall_pct}% toward {total_target}</span></div></div>")

    # Purpose and Posture
    if pj.get("purpose_and_posture"):
        out.append("<h2 class='section'>Purpose and Posture</h2>")
        out.append(f"<p class='lede'>{html.escape(pj['purpose_and_posture'].strip())}</p>")
    if pj.get("governing_aim"):
        out.append(f"<div class='aim'>{html.escape(pj['governing_aim'].strip())}</div>")

    # Design Principles
    if fw.get("design_principles"):
        out.append("<h2 class='section'>Design Principles</h2>")
        out.append("<div class='principles'>")
        for p in fw["design_principles"]:
            out.append("<div class='principle'>"
                       f"<h4>{html.escape(p['title'])}</h4>"
                       f"<p>{html.escape(p['body'].strip())}</p>"
                       "</div>")
        out.append("</div>")

    # Architecture (arcs + movements)
    out.append("<h2 class='section'>The Architecture</h2>")
    out.append("<p class='lede'>Three arcs, nine movements. Song counts are indicative targets, weighted toward Grace.</p>")
    for arc in fw["arcs"]:
        out.append(f"<h2 class='arc'>{html.escape(arc['gloss'])} "
                   f"<span class='gloss'>({html.escape(arc['label'])})</span>"
                   f"<span class='ct'>target {arc['target']}</span></h2>")
        out.append(f"<div class='arc-blurb'>{html.escape(arc['blurb'].strip())}</div>")
        for mv in arc["movements"]:
            mvsongs = by_movement.get(mv["id"], [])
            w = sum(status_weight(fw, s.get("status","idea")) for s in mvsongs)
            tgt = mv.get("target", 8)
            pct = min(100, round(100 * w / tgt)) if tgt else 0
            out.append("<div class='mv'>")
            out.append(f"<h3>Movement {mv['id']} — {html.escape(mv['title'])}</h3>")
            out.append(f"<div class='sub'>{html.escape(mv['subtitle'])}</div>")
            out.append(f"<div class='pass'>{html.escape(mv['body'].strip())}</div>")
            out.append(f"<div class='pass'><b>Anchor passages:</b> {html.escape(mv['passages'])}</div>")
            out.append(f"<div class='mvbar'><div class='mvfill' style='width:{pct}%'></div></div>")
            out.append(f"<div class='mvmeta'>{len(mvsongs)} of ~{tgt} · {pct}% · "
                       f"<i>{html.escape(mv['mode'])}</i></div>")
            if mvsongs:
                out.append("<ul class='songs'>")
                for s in mvsongs:
                    t = html.escape(str(s.get("title", "(untitled)")))
                    href = f"songs/{s['_slug']}.html"
                    out.append(f"<li><a href='{href}'><span>{s.get('number','—')}. {t}</span></a>"
                               f"{pill(fw, s.get('status','idea'))}</li>")
                out.append("</ul>")
            out.append("</div>")

    # Three Threads (expanded per-arc)
    out.append("<h2 class='section'>The Three Threads</h2>")
    out.append("<p class='lede'>Three theological motifs run the length of Paraverses, "
               "surfacing in each arc in new form. They are never repeated as a fixed lyric "
               "or tune; they recur as images that a careful listener feels returning and "
               "deepening — the quiet evidence that the songs are one body.</p>")
    out.append("<div class='threads'>")
    for t in fw["threads"]:
        out.append("<div class='thread'>")
        out.append(f"<h3>{html.escape(t['name'])}</h3>")
        out.append(f"<div class='tline'>{html.escape(t['line'])}</div>")
        for ia in t.get("in_arcs", []):
            a = arc_label(fw, ia["arc"])
            label = f"{a['gloss']} ({a['label']})"
            out.append(f"<div class='inarc'><b>In {html.escape(label)}.</b> "
                       f"{html.escape(ia['text'].strip())}</div>")
        out.append("</div>")
    out.append("</div>")

    # Decisions
    if fw.get("decisions"):
        out.append("<h2 class='section'>Decisions</h2>")
        out.append("<div class='decisions'>")
        if fw["decisions"].get("resolved"):
            out.append("<div class='resolved'>"
                       "<h4>Resolved</h4>"
                       f"<p>{html.escape(fw['decisions']['resolved'].strip())}</p>"
                       "</div>")
        opens = fw["decisions"].get("open") or []
        if opens:
            out.append("<div class='open'><h4>Still open</h4><ol>")
            for item in opens:
                out.append(f"<li>{html.escape(item.strip())}</li>")
            out.append("</ol></div>")
        out.append("</div>")

    # Lineage
    if fw.get("lineage"):
        out.append("<h2 class='section'>Lineage</h2>")
        out.append(f"<div class='lineage'>{html.escape(fw['lineage'].strip())}</div>")

    # Footer
    stamp = datetime.date.today().isoformat()
    year = datetime.date.today().year
    out.append("<footer>"
               f"<div>Words and music &copy; {year} "
               "<a href='https://attieretief.com'>Attie Retief</a>. "
               f"Licensed under <a href='{LICENSE_LINK}'>{LICENSE_LABEL}</a>. "
               "Site code: <a href='https://opensource.org/licenses/MIT'>MIT</a>.</div>"
               "<div>Free for congregational worship, printing, projection, recording, "
               "translation, and arrangement with attribution and same-license sharing.</div>"
               f"<div>Generated {stamp} from the repository. "
               "Progress reflects committed songs. — Paraverses</div>"
               "</footer>")
    out.append("</div></body></html>")
    return "\n".join(out)

def build():
    fw = load_framework()
    songs = load_songs()
    by_movement = {}
    for s in songs:
        by_movement.setdefault(s.get("movement"), []).append(s)

    os.makedirs(SITE_SONGS, exist_ok=True)
    os.makedirs(SITE_AUDIO, exist_ok=True)

    with open(os.path.join(SITE, "CNAME"), "w", encoding="utf-8") as f:
        f.write("paraverses.attieretief.com\n")

    if os.path.isdir(AUDIO):
        for fn in os.listdir(AUDIO):
            if fn.endswith(".mp3"):
                shutil.copy2(os.path.join(AUDIO, fn), os.path.join(SITE_AUDIO, fn))

    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(fw, songs, by_movement))

    for s in songs:
        page = render_song_page(fw, s)
        with open(os.path.join(SITE_SONGS, f"{s['_slug']}.html"), "w", encoding="utf-8") as f:
            f.write(page)
        slides = parse_lyric_slides(s.get("_body", ""))
        if slides:
            present = render_presentation_page(fw, s, slides)
            with open(os.path.join(SITE_SONGS, f"{s['_slug']}-present.html"),
                      "w", encoding="utf-8") as f:
                f.write(present)
            variants = get_audio_variants(s["_slug"])
            if variants:
                preview = render_preview_page(fw, s, slides, variants, get_cues(s))
                with open(os.path.join(SITE_SONGS, f"{s['_slug']}-preview.html"),
                          "w", encoding="utf-8") as f:
                    f.write(preview)

    total_target = fw["project"]["target_total"]
    total_weight = sum(status_weight(fw, s.get("status", "idea")) for s in songs)
    overall_pct = round(100 * total_weight / total_target) if total_target else 0
    complete_count = sum(1 for s in songs if s.get("status") == "complete")

    with open(os.path.join(SITE, "data.json"), "w", encoding="utf-8") as f:
        json.dump({"overall_pct": overall_pct, "complete": complete_count,
                   "in_progress": len(songs), "target": total_target}, f, indent=2)
    print(f"Built site: {overall_pct}% toward {total_target} "
          f"({len(songs)} songs, {complete_count} complete)")

if __name__ == "__main__":
    build()
