#!/usr/bin/env python3
"""Render a sing-along video per audio variant per song.

For each song with `cues:` in its frontmatter, this builds one MP4 per audio
variant under `site/video/<slug>-<variant>.mp4`. Each MP4 is a slideshow timed
to the cues on the shared Paraverses background (assets/video-background.jpg),
with the song's deep-link URL in the bottom-right corner of every slide.

Usage:
  python scripts/build_video.py                  # all songs, all variants
  python scripts/build_video.py 004              # one song by number prefix
  python scripts/build_video.py 004-father-of-lights
  python scripts/build_video.py --background path/to/bg.jpg   # override
  python scripts/build_video.py --force          # re-render existing MP4s

Requires ffmpeg + ffprobe on PATH, Pillow + PyYAML installed.
"""
import os, re, sys, subprocess, tempfile, argparse

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    sys.exit("Pillow required: pip install pillow")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONGS = os.path.join(ROOT, "songs")
AUDIO = os.path.join(ROOT, "audio")
SITE = os.path.join(ROOT, "site")
VIDEO_OUT = os.path.join(SITE, "video")
DEFAULT_BG = os.path.join(ROOT, "assets", "video-background.jpg")

SITE_HOST = "paraverses.attieretief.com"
CREDIT_TEXT = "Words and music by Attie Retief (attieretief.com)"

FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.S)
LYRIC_SECTION_RE = re.compile(
    r"^##\s+(?:<a[^>]*></a>\s*)?Lyric\s*$(.*?)^##\s",
    re.S | re.M,
)
SLIDE_RE = re.compile(
    r"^###\s+(?P<title>.+?)\s*$\n(?P<body>(?:(?:^>.*\n?)|(?:^\s*\n))+)",
    re.M,
)

W, H = 1920, 1080
GOLD = (201, 168, 76)
CREAM = (245, 239, 225)
URL_FILL = (245, 239, 225, 150)
FONT_GEORGIA = "/System/Library/Fonts/Supplemental/Georgia.ttf"
FONT_GEORGIA_IT = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"


def load_song(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = FM.match(text)
    if not m:
        return None
    meta = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    slug = os.path.basename(path)[:-3]
    meta["_slug"] = slug
    meta["_body"] = body
    return meta


def all_songs():
    out = []
    for fn in sorted(os.listdir(SONGS)):
        if not fn.endswith(".md") or fn.startswith("_"):
            continue
        s = load_song(os.path.join(SONGS, fn))
        if s:
            out.append(s)
    return out


def parse_slides(body_md):
    m = LYRIC_SECTION_RE.search(body_md + "\n## __end__\n")
    if not m:
        return []
    section = m.group(1)
    slides = []
    for sm in SLIDE_RE.finditer(section):
        title = sm.group("title").strip()
        lines = []
        for ln in sm.group("body").splitlines():
            ln = ln.strip()
            if not ln.startswith(">"):
                continue
            text = ln.lstrip(">").strip()
            if text:
                lines.append(text)
        if lines:
            slides.append({"title": title, "lines": lines})
    return slides


def get_audio_variants(slug):
    variants = []
    if not os.path.isdir(AUDIO):
        return variants
    for fn in sorted(os.listdir(AUDIO)):
        if not fn.endswith(".mp3"):
            continue
        if fn == f"{slug}.mp3" or fn.startswith(f"{slug}-"):
            variants.append(fn)
    return variants


def get_cues_for(song, audio_fn):
    raw = song.get("cues")
    if not raw:
        return None
    slug = song["_slug"]
    if isinstance(raw, list):
        if audio_fn == f"{slug}.mp3":
            return [float(t) for t in raw]
        return None
    if isinstance(raw, dict):
        v = raw.get(audio_fn)
        return [float(t) for t in v] if v else None
    return None


def ffprobe_duration(audio_path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nokey=1:noprint_wrappers=1", audio_path,
    ], text=True).strip()
    return float(out)


def cover_resize(img, w, h):
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = int(iw * scale + 1), int(ih * scale + 1)
    img = img.resize((nw, nh), Image.LANCZOS)
    x = (nw - w) // 2
    y = (nh - h) // 2
    return img.crop((x, y, x + w, y + h))


def make_background(photo_path):
    """Shared photo, cover-resized, gently blurred, darkened, vignetted."""
    if photo_path and os.path.exists(photo_path):
        img = Image.open(photo_path).convert("RGB")
        img = cover_resize(img, W, H)
        img = img.filter(ImageFilter.GaussianBlur(radius=4))
    else:
        img = Image.new("RGB", (W, H), (8, 14, 11))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([0, 0, W, H], fill=(5, 10, 8, 110))
    grad_h = 240
    for y in range(grad_h):
        alpha = int(140 * (1 - y / grad_h))
        draw.rectangle([0, y, W, y + 1], fill=(0, 0, 0, alpha))
        draw.rectangle([0, H - 1 - y, W, H - y], fill=(0, 0, 0, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def load_font(path, size):
    return ImageFont.truetype(path, size)


def text_w(draw, text, font, tracking=0):
    if tracking == 0:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]
    total = 0
    for ch in text:
        b = draw.textbbox((0, 0), ch, font=font)
        total += (b[2] - b[0]) + tracking
    return total - tracking if text else 0


def draw_tracked(draw, xy, text, font, fill, tracking):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        b = draw.textbbox((0, 0), ch, font=font)
        x += (b[2] - b[0]) + tracking


def render_slide(bg, title, label, lines, url_text, out_path):
    img_rgba = bg.copy().convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    o = ImageDraw.Draw(overlay)

    title_font = load_font(FONT_GEORGIA, 56)
    tw = text_w(o, title, title_font)
    tx = (W - tw) // 2
    ty = 70
    o.text((tx + 2, ty + 3), title, font=title_font, fill=(0, 0, 0, 200))
    o.text((tx, ty), title, font=title_font, fill=CREAM)

    label_text = label.upper()
    label_size = 36
    label_font = load_font(FONT_GEORGIA_IT, label_size)
    label_tracking = 6
    lw = text_w(o, label_text, label_font, label_tracking)

    max_w = int(W * 0.82)
    lyric_size = 92
    while lyric_size >= 36:
        lyric_font = load_font(FONT_GEORGIA, lyric_size)
        widest = max(text_w(o, ln, lyric_font) for ln in lines)
        if widest <= max_w:
            break
        lyric_size -= 4
    line_h = int(lyric_size * 1.35)
    lyric_block_h = line_h * len(lines)
    label_gap = 56
    total_h = label_size + label_gap + lyric_block_h
    y0 = (H - total_h) // 2

    draw_tracked(o, ((W - lw) // 2, y0), label_text, label_font,
                 GOLD, label_tracking)

    ly = y0 + label_size + label_gap
    for ln in lines:
        lw_line = text_w(o, ln, lyric_font)
        x = (W - lw_line) // 2
        o.text((x + 2, ly + 3), ln, font=lyric_font, fill=(0, 0, 0, 200))
        o.text((x, ly), ln, font=lyric_font, fill=CREAM)
        ly += line_h

    foot_font = load_font(FONT_GEORGIA_IT, 24)
    margin = 36
    foot_y = H - margin - 30

    cw = text_w(o, CREDIT_TEXT, foot_font)
    cx = margin
    o.text((cx + 1, foot_y + 1), CREDIT_TEXT, font=foot_font, fill=(0, 0, 0, 180))
    o.text((cx, foot_y), CREDIT_TEXT, font=foot_font, fill=URL_FILL)

    uw = text_w(o, url_text, foot_font)
    ux = W - margin - uw
    o.text((ux + 1, foot_y + 1), url_text, font=foot_font, fill=(0, 0, 0, 180))
    o.text((ux, foot_y), url_text, font=foot_font, fill=URL_FILL)

    out = Image.alpha_composite(img_rgba, overlay).convert("RGB")
    out.save(out_path, "PNG")


def build_video(song, audio_fn, bg, force=False):
    slug = song["_slug"]
    cues = get_cues_for(song, audio_fn)
    slides = parse_slides(song.get("_body", ""))
    if not cues:
        return f"  skip {audio_fn}: no cues"
    if not slides:
        return f"  skip {audio_fn}: no slides"
    if len(cues) != len(slides):
        return (f"  skip {audio_fn}: cues ({len(cues)}) != slides "
                f"({len(slides)})")

    audio_path = os.path.join(AUDIO, audio_fn)
    if not os.path.exists(audio_path):
        return f"  skip {audio_fn}: audio missing"

    out_name = audio_fn[:-4] + ".mp4"
    out_path = os.path.join(VIDEO_OUT, out_name)
    if os.path.exists(out_path) and not force:
        return f"  keep {out_name}"

    duration = ffprobe_duration(audio_path)
    durations = []
    for i in range(len(cues) - 1):
        d = cues[i + 1] - cues[i]
        if d <= 0:
            return f"  skip {audio_fn}: non-monotonic cues at index {i}"
        durations.append(d)
    durations.append(max(0.1, duration - cues[-1]))

    url_text = f"{SITE_HOST}/songs/{slug}"
    title_text = str(song.get("title", "")).strip()
    os.makedirs(VIDEO_OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        slide_paths = []
        for i, sl in enumerate(slides):
            p = os.path.join(td, f"slide_{i:02d}.png")
            render_slide(bg, title_text, sl["title"], sl["lines"], url_text, p)
            slide_paths.append(p)
        list_path = os.path.join(td, "concat.txt")
        with open(list_path, "w", encoding="utf-8") as f:
            for p, d in zip(slide_paths, durations):
                f.write(f"file '{p}'\n")
                f.write(f"duration {d:.3f}\n")
            f.write(f"file '{slide_paths[-1]}'\n")

        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", list_path,
            "-i", audio_path,
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-r", "30", "-c:a", "aac", "-b:a", "192k",
            "-t", f"{duration:.3f}", "-movflags", "+faststart",
            out_path,
        ]
        subprocess.run(cmd, check=True)

    return f"  wrote {out_name}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("song", nargs="?",
                    help="Song number (e.g. 004) or slug; default: all songs")
    ap.add_argument("--variant", help="Single audio filename to render")
    ap.add_argument("--background", default=DEFAULT_BG,
                    help=f"Background image (default: {DEFAULT_BG})")
    ap.add_argument("--force", action="store_true",
                    help="Re-render existing MP4s")
    args = ap.parse_args()

    if not os.path.exists(args.background):
        sys.exit(f"background image not found: {args.background}")
    bg = make_background(args.background)

    songs = all_songs()
    if args.song:
        prefix = args.song
        songs = [s for s in songs if s["_slug"].startswith(prefix) or
                 s["_slug"].split("-", 1)[0] == prefix.zfill(3)]
        if not songs:
            sys.exit(f"no song matches {args.song!r}")

    for s in songs:
        slug = s["_slug"]
        variants = get_audio_variants(slug)
        if args.variant:
            variants = [v for v in variants if v == args.variant]
        if not variants:
            print(f"{slug}: no audio variants")
            continue
        print(f"{slug}")
        for v in variants:
            try:
                print(build_video(s, v, bg, force=args.force))
            except subprocess.CalledProcessError as e:
                print(f"  ffmpeg failed for {v}: {e}")


if __name__ == "__main__":
    main()
