#!/usr/bin/env python3
"""Build the Paraverses progress site from framework.yaml + songs/*.md.

Usage: python scripts/build_site.py
Outputs:
  site/index.html        — landing page
  site/songs/*.html      — one page per song (drill-in)
  site/data.json         — small summary blob
"""
import os, re, json, html, datetime, sys

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
SITE = os.path.join(ROOT, "site")
SITE_SONGS = os.path.join(SITE, "songs")

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

/* Song-page specifics */
.song-page {{ max-width:720px; margin:0 auto; padding:48px 24px 96px; }}
.song-page .back {{ color:var(--slate); font-size:13px; text-decoration:none;
                     letter-spacing:1px; text-transform:uppercase; }}
.song-page .back:hover {{ color:var(--green); }}
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
"""

def pill(fw, sid):
    colors = {"idea":"#aaa","draft-lyric":"#b08900","draft-melody":"#7a8b6e","complete":GREEN}
    return f'<span class="pill" style="background:{colors.get(sid,"#aaa")}">{html.escape(status_label(fw, sid))}</span>'

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

    out = []
    out.append("<!doctype html><html lang='en'><head><meta charset='utf-8'>")
    out.append("<meta name='viewport' content='width=device-width,initial-scale=1'>")
    out.append("<meta name='author' content='Attie Retief'>")
    out.append(f"<title>{html.escape(title)} — Paraverses</title>")
    out.append(f"<style>{CSS}</style></head><body><div class='song-page'>")
    out.append("<a class='back' href='../index.html'>&larr; Paraverses</a>")
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

    out.append(f"<div class='body'>{body_html}</div>")
    out.append("<footer><div>Words and music by Attie Retief.</div></footer>")
    out.append("</div></body></html>")
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
    out.append("<footer>"
               "<div>Words and music by Attie Retief.</div>"
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

    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(fw, songs, by_movement))

    for s in songs:
        page = render_song_page(fw, s)
        with open(os.path.join(SITE_SONGS, f"{s['_slug']}.html"), "w", encoding="utf-8") as f:
            f.write(page)

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
