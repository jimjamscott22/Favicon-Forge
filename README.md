# Favicon Forge

Upload once. Generate everywhere.

Favicon Forge is a polished FastAPI utility that takes one PNG or JPG/JPEG image and generates a complete favicon pack for modern web apps.

## Features

- Validates image type and upload size.
- Center-crops uploads to a square with Pillow.
- Exports ICO, browser PNG favicons, Apple touch icon, Android Chrome icons, and `site.webmanifest`.
- Shows a generated preview, copyable HTML snippet, and ZIP download.
- Uses Jinja2 templates and plain CSS.

## Run locally

Install `uv` first if you do not already have it.

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Test

```bash
uv run pytest
```
