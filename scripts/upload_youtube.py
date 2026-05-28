#!/usr/bin/env python3
"""Upload rendered sing-along MP4s to YouTube, add them to a playlist, and
write the resulting URLs back into each song's frontmatter `youtube:` map.

One-time setup:
  1. Google Cloud Console (https://console.cloud.google.com):
       - create/select a project
       - APIs & Services > Library > enable "YouTube Data API v3"
       - APIs & Services > OAuth consent screen > External, add your account
         as a Test user (no app review needed while in Testing mode)
       - APIs & Services > Credentials > Create credentials >
         OAuth client ID > Application type: Desktop > download the JSON
  2. Save the downloaded file as ~/.config/paraverses/client_secret.json
     (or pass --client-secret PATH).
  3. Find your target playlist ID: YouTube Studio > Playlists > open the
     playlist; the URL contains list=PLxxxxx. The value after `list=` is the
     ID. Pass it via --playlist-id or YOUTUBE_PLAYLIST_ID env var. Or run
     `make youtube ARGS="--list-playlists"` after the first auth to print them.

Usage:
  python scripts/upload_youtube.py --playlist-id PLxxx       # upload all pending
  python scripts/upload_youtube.py --playlist-id PLxxx 004   # one song
  python scripts/upload_youtube.py --list-playlists          # show your playlists
  python scripts/upload_youtube.py --dry-run --playlist-id PLxxx
  python scripts/upload_youtube.py --privacy public --playlist-id PLxxx
  python scripts/upload_youtube.py --force --playlist-id PLxxx   # re-upload everything

Quota: each `videos.insert` costs 1600 of the 10000/day default quota
(~6 uploads/day). The script stops cleanly when YouTube returns
quotaExceeded — re-run tomorrow, or request a quota increase.
"""
import os, re, sys, json, argparse

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
except ImportError:
    sys.exit("Google API client + oauthlib required: "
             "pip install google-api-python-client google-auth-oauthlib")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONGS = os.path.join(ROOT, "songs")
AUDIO = os.path.join(ROOT, "audio")
SITE = os.path.join(ROOT, "site")
VIDEO_OUT = os.path.join(SITE, "video")

CONFIG_DIR = os.path.expanduser("~/.config/paraverses")
DEFAULT_CLIENT_SECRET = os.path.join(CONFIG_DIR, "client_secret.json")
TOKEN_PATH = os.path.join(CONFIG_DIR, "youtube_token.json")
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]
SITE_HOST = "paraverses.attieretief.com"
LICENSE = "CC BY-SA 4.0 — https://creativecommons.org/licenses/by-sa/4.0/"

FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.S)
LYRIC_SECTION_RE = re.compile(
    r"^##\s+(?:<a[^>]*></a>\s*)?Lyric\s*$(.*?)^##\s",
    re.S | re.M,
)
SLIDE_RE = re.compile(
    r"^###\s+(?P<title>.+?)\s*$\n(?P<body>(?:(?:^>.*\n?)|(?:^\s*\n))+)",
    re.M,
)
YOUTUBE_BLOCK_RE = re.compile(
    r"^youtube:[^\n]*\n(?:[ \t]+[^\n]*\n)*",
    re.M,
)


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
    meta["_path"] = path
    meta["_raw"] = text
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
    slides = []
    for sm in SLIDE_RE.finditer(m.group(1)):
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


def variant_label(slug, audio_fn):
    if audio_fn == f"{slug}.mp3":
        return "Demo"
    suffix = audio_fn[len(slug) + 1:-4]
    # strip leading numeric index (e.g. "1-female-solo" -> "female-solo")
    suffix = re.sub(r"^\d+-", "", suffix)
    label = suffix.replace("-", " ").strip()
    return label[:1].upper() + label[1:] if label else "Demo"


def build_title(song, audio_fn):
    slug = song["_slug"]
    number = song.get("number", "")
    title = str(song.get("title", "")).strip()
    label = variant_label(slug, audio_fn)
    parts = [f"Paraverse {number}", title]
    if label:
        parts.append(label)
    full = " · ".join(p for p in parts if p)
    return full[:100]


def build_description(song, audio_fn):
    slug = song["_slug"]
    number = song.get("number", "")
    title = str(song.get("title", "")).strip()
    scripture = str(song.get("scripture", "")).strip()
    threads = song.get("threads") or []
    slides = parse_slides(song.get("_body", ""))

    lines = []
    lines.append(f"A sing-along video for Paraverse {number}: “{title}”")
    if threads:
        lines.append("Thread: " + ", ".join(threads))
    if scripture:
        lines.append("Scripture: " + scripture)
    lines.append("")
    lines.append("—— Lyric ——")
    lines.append("")
    for sl in slides:
        lines.append(sl["title"])
        lines.extend(sl["lines"])
        lines.append("")
    lines.append("——")
    lines.append("")
    lines.append("Words and music by Attie Retief.")
    lines.append("Licensed under " + LICENSE)
    lines.append("Free to sing, print, project, record, translate, and arrange "
                 "with attribution and same-license sharing.")
    lines.append("")
    lines.append(f"Song page (full theological defense + lead sheet): "
                 f"https://{SITE_HOST}/songs/{slug}")
    lines.append(f"Project: https://{SITE_HOST}")
    lines.append("Composer: https://attieretief.com")
    desc = "\n".join(lines)
    return desc[:4900]


def build_tags(song):
    tags = ["paraverses", "hymn", "reformed", "sing-along"]
    for t in (song.get("threads") or []):
        tags.append(str(t).lower())
    return tags


def get_existing_youtube(song):
    raw = song.get("youtube")
    if not raw or not isinstance(raw, dict):
        return {}
    return {str(k): str(v) for k, v in raw.items()}


def get_audio_variants(slug):
    if not os.path.isdir(AUDIO):
        return []
    out = []
    for fn in sorted(os.listdir(AUDIO)):
        if not fn.endswith(".mp3"):
            continue
        if fn == f"{slug}.mp3" or fn.startswith(f"{slug}-"):
            out.append(fn)
    return out


def video_path_for(audio_fn):
    return os.path.join(VIDEO_OUT, audio_fn[:-4] + ".mp4")


def write_youtube_block(song_path, raw_text, urls):
    """Surgically insert/replace the `youtube:` block in the song's frontmatter.

    Preserves all other hand-formatted lines, comments, and field order.
    """
    m = FM.match(raw_text)
    if not m:
        raise RuntimeError(f"no frontmatter in {song_path}")
    # FM regex strips the trailing newline off the last frontmatter line; add
    # it back so YOUTUBE_BLOCK_RE can match a youtube block sitting at the end.
    fm_text = m.group(1) + "\n"
    body = m.group(2)
    fm_text = YOUTUBE_BLOCK_RE.sub("", fm_text)
    fm_text = fm_text.rstrip() + "\n"
    block = ["youtube:"]
    for k in sorted(urls.keys()):
        block.append(f"  {k}: {urls[k]}")
    fm_text += "\n".join(block) + "\n"
    new_text = "---\n" + fm_text + "---\n" + body
    with open(song_path, "w", encoding="utf-8") as f:
        f.write(new_text)


def get_youtube_service(client_secret_path):
    if not os.path.exists(client_secret_path):
        sys.exit(
            f"OAuth client secret not found at {client_secret_path}.\n"
            f"See `python scripts/upload_youtube.py --help` for one-time setup."
        )
    os.makedirs(CONFIG_DIR, exist_ok=True)
    creds = None
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except ValueError:
            creds = None
    if creds and not creds.valid and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            creds = None
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def list_playlists(youtube):
    print("Your playlists:")
    page = None
    while True:
        req = youtube.playlists().list(
            part="snippet,contentDetails", mine=True, maxResults=50, pageToken=page,
        )
        res = req.execute()
        for it in res.get("items", []):
            count = it.get("contentDetails", {}).get("itemCount", "?")
            print(f"  {it['id']}  ({count:>4} videos)  {it['snippet']['title']}")
        page = res.get("nextPageToken")
        if not page:
            break


def upload_one(youtube, song, audio_fn, video_path, privacy, dry_run):
    title = build_title(song, audio_fn)
    description = build_description(song, audio_fn)
    tags = build_tags(song)
    body = {
        "snippet": {
            "title": title, "description": description, "tags": tags,
            "categoryId": "10", "defaultLanguage": "en", "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy, "selfDeclaredMadeForKids": False,
            "license": "creativeCommon",
            "embeddable": True,
        },
    }
    if dry_run:
        print(f"    [dry-run] would upload as: {title}")
        print(f"    [dry-run] privacy: {privacy}, tags: {tags}")
        return None
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True,
                            mimetype="video/mp4")
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            sys.stdout.write(f"\r    uploading… {int(status.progress() * 100)}%")
            sys.stdout.flush()
    sys.stdout.write("\r" + " " * 30 + "\r")
    return response["id"]


def add_to_playlist(youtube, video_id, playlist_id):
    body = {"snippet": {
        "playlistId": playlist_id,
        "resourceId": {"kind": "youtube#video", "videoId": video_id},
    }}
    youtube.playlistItems().insert(part="snippet", body=body).execute()


def handle_http_error(e):
    try:
        err = json.loads(e.content.decode("utf-8"))
        reason = err.get("error", {}).get("errors", [{}])[0].get("reason", "")
        message = err.get("error", {}).get("message", str(e))
    except Exception:
        reason = ""
        message = str(e)
    return reason, message


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("song", nargs="?",
                    help="Song number (e.g. 004) or slug; default: all songs")
    ap.add_argument("--playlist-id",
                    default=os.environ.get("YOUTUBE_PLAYLIST_ID"),
                    help="Target playlist ID (or set YOUTUBE_PLAYLIST_ID)")
    ap.add_argument("--privacy", default="unlisted",
                    choices=["unlisted", "public", "private"])
    ap.add_argument("--client-secret", default=DEFAULT_CLIENT_SECRET)
    ap.add_argument("--list-playlists", action="store_true",
                    help="Print your playlists with IDs and exit")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show what would be uploaded; no API calls beyond auth")
    ap.add_argument("--force", action="store_true",
                    help="Re-upload variants that already have a URL in frontmatter")
    args = ap.parse_args()

    youtube = get_youtube_service(args.client_secret)

    if args.list_playlists:
        list_playlists(youtube)
        return

    if not args.playlist_id and not args.dry_run:
        sys.exit("--playlist-id required (or set YOUTUBE_PLAYLIST_ID). "
                 "Run with --list-playlists to find it.")

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
        if not variants:
            continue
        existing = get_existing_youtube(s)
        pending = []
        for v in variants:
            vp = video_path_for(v)
            if not os.path.exists(vp):
                continue
            if v in existing and not args.force:
                continue
            pending.append((v, vp))
        if not pending:
            continue
        print(f"{slug}")
        urls = dict(existing)
        changed = False
        quota_hit = False
        for audio_fn, vp in pending:
            print(f"  {audio_fn}")
            try:
                vid = upload_one(youtube, s, audio_fn, vp, args.privacy,
                                 args.dry_run)
            except HttpError as e:
                reason, message = handle_http_error(e)
                if reason in ("quotaExceeded", "uploadLimitExceeded"):
                    print(f"    quota exhausted: {message}")
                    quota_hit = True
                    break
                print(f"    upload failed ({reason}): {message}")
                continue
            if args.dry_run:
                continue
            url = f"https://youtu.be/{vid}"
            print(f"    uploaded → {url}")
            try:
                add_to_playlist(youtube, vid, args.playlist_id)
                print(f"    added to playlist")
            except HttpError as e:
                reason, message = handle_http_error(e)
                print(f"    playlist add failed ({reason}): {message}")
            urls[audio_fn] = url
            changed = True
        if changed:
            write_youtube_block(s["_path"], s["_raw"], urls)
            print(f"  wrote youtube: block into {os.path.basename(s['_path'])}")
        if quota_hit:
            break


if __name__ == "__main__":
    main()
