import shutil
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import main
from app.main import app


client = TestClient(app)


@pytest.fixture
def isolated_runtime_dirs(monkeypatch):
    root = Path("generated") / f"test-app-{uuid4().hex}"
    uploads = root / "uploads"
    generated = root / "generated"
    uploads.mkdir(parents=True, exist_ok=True)
    generated.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(main, "UPLOAD_DIR", uploads)
    monkeypatch.setattr(main, "GENERATED_DIR", generated)
    try:
        yield
    finally:
        shutil.rmtree(root, ignore_errors=True)


def make_png_bytes():
    buffer = BytesIO()
    Image.new("RGB", (96, 64), "#38bdf8").save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def test_homepage_renders_upload_form():
    response = client.get("/")

    assert response.status_code == 200
    assert "Favicon Forge" in response.text
    assert "Upload once. Generate everywhere." in response.text
    assert "Generate favicons" in response.text


def test_generate_rejects_unsupported_file_type():
    response = client.post(
        "/generate",
        files={"file": ("notes.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 200
    assert "Please upload a PNG, JPG, or JPEG image." in response.text


def test_generate_creates_result_page_and_downloadable_zip(isolated_runtime_dirs):
    response = client.post(
        "/generate",
        files={"file": ("logo.png", make_png_bytes(), "image/png")},
        data={
            "app_name": "Demo App",
            "short_name": "Demo",
            "theme_color": "#38bdf8",
            "background_color": "#020617",
        },
    )

    assert response.status_code == 200
    assert "Ready to ship" in response.text
    assert 'href="/download/' in response.text
    assert "Download ZIP" in response.text
    assert "theme-color" in response.text
    assert "#38bdf8" in response.text
