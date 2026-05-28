.PHONY: dev build video youtube

dev:
	@python3 -m venv .venv
	@.venv/bin/pip install -qr requirements-dev.txt
	@.venv/bin/python scripts/dev.py

build:
	@python3 -m venv .venv
	@.venv/bin/pip install -qr requirements.txt
	@.venv/bin/python scripts/build_site.py

# Render sing-along videos. `make video` renders every song with cues;
# `make video SONG=004` renders one. Requires ffmpeg.
video:
	@python3 -m venv .venv
	@.venv/bin/pip install -qr requirements.txt
	@.venv/bin/python scripts/build_video.py $(SONG) $(if $(FORCE),--force,)

# Upload rendered videos to YouTube + add to playlist + write URLs back into
# song frontmatter. Requires a one-time Google Cloud OAuth client.
# See scripts/upload_youtube.py --help for setup.
#   make youtube                                  # upload everything pending
#   make youtube SONG=004                          # one song
#   make youtube ARGS="--list-playlists"           # discover playlist IDs
#   make youtube ARGS="--dry-run"                  # preview titles/descriptions
#   make youtube ARGS="--privacy public"           # upload as public
youtube:
	@python3 -m venv .venv
	@.venv/bin/pip install -qr requirements.txt
	@.venv/bin/python scripts/upload_youtube.py $(SONG) $(ARGS)
