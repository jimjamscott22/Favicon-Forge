import json
import shutil
import zipfile
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from PIL import Image

from app.favicon_generator import (
    FAVICON_FILES,
    build_html_snippet,
    generate_favicon_pack,
)


@pytest.fixture
def output_dir():
    path = Path("generated") / f"test-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def make_source_image(width=120, height=80):
    image = Image.new("RGB", (width, height), "#0ea5e9")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def test_generate_favicon_pack_creates_expected_files(output_dir):
    result = generate_favicon_pack(
        source=make_source_image(),
        output_dir=output_dir,
        app_name="Favicon Forge",
        short_name="Forge",
        theme_color="#38bdf8",
        background_color="#020617",
    )

    generated_names = {path.name for path in result.files}
    assert generated_names == set(FAVICON_FILES) | {"site.webmanifest"}
    assert result.zip_path.exists()

    for filename, expected_size in {
        "favicon-16x16.png": (16, 16),
        "favicon-32x32.png": (32, 32),
        "favicon-192x192.png": (192, 192),
        "favicon-512x512.png": (512, 512),
        "apple-touch-icon.png": (180, 180),
        "android-chrome-192x192.png": (192, 192),
        "android-chrome-512x512.png": (512, 512),
    }.items():
        with Image.open(output_dir / filename) as generated:
            assert generated.size == expected_size
            assert generated.mode == "RGBA"

    with zipfile.ZipFile(result.zip_path) as archive:
        assert set(archive.namelist()) == generated_names


def test_generate_favicon_pack_writes_manifest(output_dir):
    generate_favicon_pack(
        source=make_source_image(),
        output_dir=output_dir,
        app_name="My App",
        short_name="App",
        theme_color="#111827",
        background_color="#f8fafc",
    )

    manifest = json.loads((output_dir / "site.webmanifest").read_text())

    assert manifest["name"] == "My App"
    assert manifest["short_name"] == "App"
    assert manifest["theme_color"] == "#111827"
    assert manifest["background_color"] == "#f8fafc"
    assert manifest["icons"] == [
        {
            "src": "/android-chrome-192x192.png",
            "sizes": "192x192",
            "type": "image/png",
        },
        {
            "src": "/android-chrome-512x512.png",
            "sizes": "512x512",
            "type": "image/png",
        },
    ]


def test_build_html_snippet_contains_required_tags():
    snippet = build_html_snippet(theme_color="#38bdf8")

    assert '<link rel="icon" href="/favicon.ico">' in snippet
    assert '<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">' in snippet
    assert '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">' in snippet
    assert '<link rel="apple-touch-icon" href="/apple-touch-icon.png">' in snippet
    assert '<link rel="manifest" href="/site.webmanifest">' in snippet
    assert '<meta name="theme-color" content="#38bdf8">' in snippet
