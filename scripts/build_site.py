#!/usr/bin/env python3
"""Build the Paraverses progress site from framework.yaml + songs/*.md.

Usage: python scripts/build_site.py
Outputs: site/index.html  (and site/data.json for any future use)
"""
import os, re, json, html, datetime, sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONGS = os.path.join(ROOT, "songs")
SITE = os.path.join(ROOT, "site")

GREEN, GOLD, CREAM, SLATE = "#1A2E1E", "#C9A84C", "#F7F4EF", "#5A6B5E"

FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)

def load_framework():
    with open(os.path.join(ROOT, "framework.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_songs():
    songs = []
    if not os.path.isdir(SONGS):
        return songs
    for fn in sorted(os.listdir(SONGS)):
        if not fn.endswith(".md"):
            continue
        with open(os.path.join(SONGS, fn), encoding="utf-8") as f:
            text = f.read()
        m = FM.match(text)
        meta = yaml.safe_load(m.group(1)) if m else {}
        meta["_file"] = fn
        songs.append(meta)
    return songs

def status_weight(fw, sid):
    for s in fw["statuses"]:
        if s["id"] == sid:
            return s["weight"]
    return 0.0

def build():
    fw = load_framework()
    songs = load_songs()
    by_movement = {}
    for s in songs:
        by_movement.setdefault(s.get("movement"), []).append(s)

    # progress per movement (weighted by status toward target)
    total_target = fw["project"]["target_total"]
    total_weight = sum(status_weight(fw, s.get("status", "idea")) for s in songs)
    overall_pct = round(100 * total_weight / total_target) if total_target else 0
    complete_count = sum(1 for s in songs if s.get("status") == "complete")

    css = f"""
    :root {{ --green:{GREEN}; --gold:{GOLD}; --cream:{CREAM}; --slate:{SLATE}; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Georgia,'Times New Roman',serif; color:#222;
            background:var(--cream); line-height:1.6; }}
    .wrap {{ max-width:880px; margin:0 auto; padding:48px 24px 96px; }}
    header.hero {{ text-align:center; padding:40px 0 24px; }}
    .hero h1 {{ font-size:54px; letter-spacing:2px; color:var(--green); margin:0; }}
    .hero .tag {{ font-style:italic; color:var(--slate); font-size:22px; margin-top:4px; }}
    .hero p.desc {{ color:#444; max-width:620px; margin:18px auto 0; }}
    .meter {{ margin:32px auto; max-width:620px; }}
    .meter .bar {{ height:14px; background:#e3ddd0; border-radius:8px; overflow:hidden; }}
    .meter .fill {{ height:100%; background:linear-gradient(90deg,var(--green),var(--gold)); width:{overall_pct}%; }}
    .meter .label {{ display:flex; justify-content:space-between; font-size:14px; color:var(--slate); margin-top:6px; }}
    h2.arc {{ color:var(--green); border-bottom:2px solid var(--gold); padding-bottom:6px;
              margin-top:48px; font-size:26px; }}
    h2.arc .gloss {{ color:var(--slate); font-weight:normal; font-size:18px; }}
    h2.arc .ct {{ float:right; color:var(--gold); font-size:16px; }}
    .arc-blurb {{ color:#555; font-style:italic; margin:8px 0 16px; }}
    .mv {{ background:white; border:1px solid #e3ddd0; border-radius:10px; padding:18px 20px; margin:14px 0; }}
    .mv h3 {{ margin:0 0 2px; color:var(--green); font-size:19px; }}
    .mv .sub {{ color:var(--slate); font-style:italic; font-size:15px; }}
    .mv .pass {{ font-size:14px; color:#555; margin-top:8px; }}
    .mv .mvbar {{ height:8px; background:#eee; border-radius:5px; overflow:hidden; margin-top:12px; }}
    .mv .mvfill {{ height:100%; background:var(--gold); }}
    .mv .mvmeta {{ font-size:13px; color:var(--slate); margin-top:5px; }}
    .songs {{ list-style:none; padding:0; margin:10px 0 0; }}
    .songs li {{ font-size:14px; padding:4px 0; border-top:1px dotted #e3ddd0; display:flex; justify-content:space-between; }}
    .pill {{ font-size:11px; padding:2px 8px; border-radius:10px; color:white; }}
    .threads {{ background:white; border:1px solid #e3ddd0; border-radius:10px; padding:18px 20px; margin:20px 0; }}
    .threads h3 {{ color:var(--gold); margin:14px 0 2px; }}
    .threads .tline {{ font-style:italic; color:var(--slate); }}
    footer {{ text-align:center; color:var(--slate); font-size:13px; margin-top:48px; }}
    """

    def pill(sid):
        colors = {"idea":"#aaa","draft-lyric":"#b08900","draft-melody":"#7a8b6e","complete":GREEN}
        label = {s["id"]:s["label"] for s in fw["statuses"]}.get(sid, sid)
        return f'<span class="pill" style="background:{colors.get(sid,"#aaa")}">{html.escape(label)}</span>'

    out = []
    out.append(f"<!doctype html><html lang='en'><head><meta charset='utf-8'>")
    out.append(f"<meta name='viewport' content='width=device-width,initial-scale=1'>")
    out.append(f"<title>{html.escape(fw['project']['name'])} — {html.escape(fw['project']['tagline'])}</title>")
    out.append(f"<style>{css}</style></head><body><div class='wrap'>")
    out.append("<header class='hero'>")
    out.append(f"<h1>{html.escape(fw['project']['name'].upper())}</h1>")
    out.append(f"<div class='tag'>{html.escape(fw['project']['tagline'])}</div>")
    out.append(f"<p class='desc'>{html.escape(fw['project']['description'])}</p>")
    out.append("</header>")

    out.append("<div class='meter'><div class='bar'><div class='fill'></div></div>")
    out.append(f"<div class='label'><span>{complete_count} complete · {len(songs)} in progress</span>"
               f"<span>{overall_pct}% toward {total_target}</span></div></div>")

    for arc in fw["arcs"]:
        out.append(f"<h2 class='arc'>{html.escape(arc['label'])} "
                   f"<span class='gloss'>· {html.escape(arc['gloss'])}</span>"
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
                    t = html.escape(str(s.get("title","(untitled)")))
                    out.append(f"<li><span>{s.get('number','—')}. {t}</span>{pill(s.get('status','idea'))}</li>")
                out.append("</ul>")
            out.append("</div>")

    out.append("<div class='threads'><h2 class='arc'>The Three Threads</h2>")
    for t in fw["threads"]:
        out.append(f"<h3>{html.escape(t['name'])}</h3>"
                   f"<div class='tline'>{html.escape(t['line'])}</div>")
    out.append("</div>")

    stamp = datetime.date.today().isoformat()
    out.append(f"<footer>Generated {stamp} from the repository. "
               f"Progress reflects committed songs. — Paraverses</footer>")
    out.append("</div></body></html>")

    os.makedirs(SITE, exist_ok=True)
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    with open(os.path.join(SITE, "data.json"), "w", encoding="utf-8") as f:
        json.dump({"overall_pct": overall_pct, "complete": complete_count,
                   "in_progress": len(songs), "target": total_target}, f, indent=2)
    print(f"Built site: {overall_pct}% toward {total_target} ({len(songs)} songs, {complete_count} complete)")

if __name__ == "__main__":
    build()
