from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from PIL import Image, ImageOps


FAVICON_SIZES = {
    "favicon-16x16.png": (16, 16),
    "favicon-32x32.png": (32, 32),
    "favicon-192x192.png": (192, 192),
    "favicon-512x512.png": (512, 512),
    "apple-touch-icon.png": (180, 180),
    "android-chrome-192x192.png": (192, 192),
    "android-chrome-512x512.png": (512, 512),
}
FAVICON_FILES = ("favicon.ico", *FAVICON_SIZES.keys())


@dataclass(frozen=True)
class FaviconPackResult:
    files: list[Path]
    zip_path: Path
    html_snippet: str


def center_crop_square(image: Image.Image) -> Image.Image:
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    return image.crop((left, top, left + side, top + side))


def build_manifest(
    *,
    app_name: str,
    short_name: str,
    theme_color: str,
    background_color: str,
) -> dict:
    return {
        "name": app_name,
        "short_name": short_name,
        "icons": [
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
        ],
        "theme_color": theme_color,
        "background_color": background_color,
        "display": "standalone",
    }


def build_html_snippet(*, theme_color: str) -> str:
    return "\n".join(
        [
            '<link rel="icon" href="/favicon.ico">',
            '<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">',
            '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">',
            '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
            '<link rel="manifest" href="/site.webmanifest">',
            f'<meta name="theme-color" content="{theme_color}">',
        ]
    )


def generate_favicon_pack(
    *,
    source: BinaryIO | BytesIO,
    output_dir: Path,
    app_name: str,
    short_name: str,
    theme_color: str,
    background_color: str,
) -> FaviconPackResult:
    output_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as uploaded:
        image = ImageOps.exif_transpose(uploaded).convert("RGBA")
        square = center_crop_square(image)

        ico_path = output_dir / "favicon.ico"
        square.save(
            ico_path,
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48)],
        )

        generated_files = [ico_path]
        for filename, size in FAVICON_SIZES.items():
            target = output_dir / filename
            resized = square.resize(size, Image.Resampling.LANCZOS)
            resized.save(target, format="PNG")
            generated_files.append(target)

    manifest_path = output_dir / "site.webmanifest"
    manifest_path.write_text(
        json.dumps(
            build_manifest(
                app_name=app_name,
                short_name=short_name,
                theme_color=theme_color,
                background_color=background_color,
            ),
            indent=2,
        ),
        encoding="utf-8",
    )
    generated_files.append(manifest_path)

    zip_path = output_dir / "favicon-pack.zip"
    with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in generated_files:
            archive.write(file_path, arcname=file_path.name)

    return FaviconPackResult(
        files=generated_files,
        zip_path=zip_path,
        html_snippet=build_html_snippet(theme_color=theme_color),
    )
