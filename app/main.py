from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import UnidentifiedImageError

from app.favicon_generator import generate_favicon_pack


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
GENERATED_DIR = BASE_DIR / "generated"
MAX_UPLOAD_SIZE = 8 * 1024 * 1024
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg"}

UPLOAD_DIR.mkdir(exist_ok=True)
GENERATED_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Favicon Forge")
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")
app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")


def render_index(request: Request, *, error: str | None = None):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "error": error,
            "max_upload_mb": MAX_UPLOAD_SIZE // (1024 * 1024),
        },
    )


def validate_upload(file: UploadFile) -> str | None:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return "Please upload a PNG, JPG, or JPEG image."
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        return "That file does not look like a supported image type."
    return None


@app.get("/")
async def index(request: Request):
    return render_index(request)


@app.post("/generate")
async def generate(
    request: Request,
    file: UploadFile = File(...),
    app_name: str = Form("Favicon Forge"),
    short_name: str = Form("Forge"),
    theme_color: str = Form("#38bdf8"),
    background_color: str = Form("#020617"),
):
    validation_error = validate_upload(file)
    if validation_error:
        return render_index(request, error=validation_error)

    content = await file.read(MAX_UPLOAD_SIZE + 1)
    if len(content) > MAX_UPLOAD_SIZE:
        return render_index(
            request,
            error=f"Please upload an image smaller than {MAX_UPLOAD_SIZE // (1024 * 1024)} MB.",
        )

    job_id = uuid4().hex
    uploaded_path = UPLOAD_DIR / f"{job_id}{Path(file.filename or '').suffix.lower()}"
    uploaded_path.write_bytes(content)
    output_dir = GENERATED_DIR / job_id

    try:
        result = generate_favicon_pack(
            source=BytesIO(content),
            output_dir=output_dir,
            app_name=app_name.strip() or "Favicon Forge",
            short_name=short_name.strip() or "Forge",
            theme_color=theme_color.strip() or "#38bdf8",
            background_color=background_color.strip() or "#020617",
        )
    except UnidentifiedImageError:
        return render_index(request, error="Pillow could not read that image. Try a different PNG or JPG.")

    return templates.TemplateResponse(
        request,
        "result.html",
        {
            "job_id": job_id,
            "files": [path.name for path in result.files],
            "html_snippet": result.html_snippet,
            "preview_url": f"/generated/{job_id}/favicon-192x192.png",
            "zip_url": f"/download/{job_id}",
        },
    )


@app.get("/download/{job_id}")
async def download(job_id: str):
    zip_path = GENERATED_DIR / job_id / "favicon-pack.zip"
    if not zip_path.exists():
        return RedirectResponse(url="/")
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename="favicon-pack.zip",
    )
