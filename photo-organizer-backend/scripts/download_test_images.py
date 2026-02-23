#!/usr/bin/env python3
"""
Download and synthesize test images for SmartPhoto integration tests.

Downloads real photos from picsum.photos and synthesizes special cases
(blur, overexposed, underexposed, screenshots, similar pairs).

Output: photo-organizer-backend/test_images/ (~20 JPG files)
"""

import io
import os
import sys
import time
import urllib.request

from PIL import Image, ImageEnhance, ImageFilter

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "test_images")


def download_image(image_id: int, width: int = 800, height: int = 600) -> bytes | None:
    """Download image from picsum.photos, return None on failure."""
    url = f"https://picsum.photos/id/{image_id}/{width}/{height}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SmartPhoto-Test/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read()
    except Exception as e:
        print(f"  [WARN] Failed to download picsum id={image_id}: {e}")
        return None


def make_synthetic_image(
    width: int = 800, height: int = 600, color: tuple = (128, 128, 128)
) -> bytes:
    """Create a synthetic PIL image as JPEG bytes."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def make_gradient_image(width: int = 800, height: int = 600) -> bytes:
    """Create a gradient image as JPEG bytes (richer than flat color)."""
    import random

    img = Image.new("RGB", (width, height))
    pixels = img.load()
    r_start, g_start, b_start = (
        random.randint(50, 200),
        random.randint(50, 200),
        random.randint(50, 200),
    )
    for y in range(height):
        for x in range(width):
            r = int(r_start + (x / width) * 80) % 256
            g = int(g_start + (y / height) * 80) % 256
            b = (b_start + (x + y) // 10) % 256
            pixels[x, y] = (r, g, b)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def apply_blur(image_bytes: bytes, sigma: float = 5.0) -> bytes:
    """Apply Gaussian blur to simulate motion blur / out-of-focus."""
    img = Image.open(io.BytesIO(image_bytes))
    blurred = img.filter(ImageFilter.GaussianBlur(radius=sigma))
    buf = io.BytesIO()
    blurred.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def apply_brightness(image_bytes: bytes, factor: float = 1.0) -> bytes:
    """Adjust image brightness (factor > 1 = overexposed, < 1 = underexposed)."""
    img = Image.open(io.BytesIO(image_bytes))
    enhancer = ImageEnhance.Brightness(img)
    adjusted = enhancer.enhance(factor)
    buf = io.BytesIO()
    adjusted.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def add_noise(image_bytes: bytes, noise_amount: int = 15) -> bytes:
    """Add small random pixel noise to create a 'similar but different' image."""
    import random

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    pixels = img.load()
    w, h = img.size
    for _ in range(w * h // 10):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        r, g, b = pixels[x, y]
        pixels[x, y] = (
            max(0, min(255, r + random.randint(-noise_amount, noise_amount))),
            max(0, min(255, g + random.randint(-noise_amount, noise_amount))),
            max(0, min(255, b + random.randint(-noise_amount, noise_amount))),
        )
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue()


def save(name: str, data: bytes) -> str:
    path = os.path.join(OUTPUT_DIR, name)
    with open(path, "wb") as f:
        f.write(data)
    size_kb = len(data) // 1024
    print(f"  [OK] {name} ({size_kb} KB)")
    return path


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output directory: {os.path.abspath(OUTPUT_DIR)}\n")

    saved = []
    base_images: list[bytes] = []  # store originals for synthetic processing

    # ── Landscape photos (5) ─────────────────────────────────────────────────
    print("=== Landscape photos (5) ===")
    landscape_ids = [10, 15, 29, 37, 42]
    for i, pid in enumerate(landscape_ids, 1):
        data = download_image(pid, 1600, 900)
        if data is None:
            data = make_gradient_image(1600, 900)
        base_images.append(data)
        saved.append(save(f"landscape_{i:02d}.jpg", data))
        time.sleep(0.3)

    # ── Portrait / person photos (3) ─────────────────────────────────────────
    print("\n=== Portrait photos (3) ===")
    portrait_ids = [64, 91, 177]
    for i, pid in enumerate(portrait_ids, 1):
        data = download_image(pid, 600, 800)
        if data is None:
            data = make_gradient_image(600, 800)
        base_images.append(data)
        saved.append(save(f"portrait_{i:02d}.jpg", data))
        time.sleep(0.3)

    # ── Food / indoor photos (2) ──────────────────────────────────────────────
    print("\n=== Food/indoor photos (2) ===")
    food_ids = [292, 326]
    for i, pid in enumerate(food_ids, 1):
        data = download_image(pid, 800, 800)
        if data is None:
            data = make_gradient_image(800, 800)
        base_images.append(data)
        saved.append(save(f"food_{i:02d}.jpg", data))
        time.sleep(0.3)

    # Use first landscape as base for synthetic images
    base = base_images[0]

    # ── Blurry photos (3) ────────────────────────────────────────────────────
    print("\n=== Blurry photos (3, GaussianBlur sigma=5) ===")
    for i in range(1, 4):
        src = base_images[i % len(base_images)]
        blurred = apply_blur(src, sigma=5.0)
        saved.append(save(f"blurry_{i:02d}.jpg", blurred))

    # ── Overexposed photos (2) ───────────────────────────────────────────────
    print("\n=== Overexposed photos (2, brightness=3.0) ===")
    for i in range(1, 3):
        src = base_images[(i + 2) % len(base_images)]
        bright = apply_brightness(src, factor=3.0)
        saved.append(save(f"overexposed_{i:02d}.jpg", bright))

    # ── Underexposed photos (2) ──────────────────────────────────────────────
    print("\n=== Underexposed photos (2, brightness=0.1) ===")
    for i in range(1, 3):
        src = base_images[(i + 4) % len(base_images)]
        dark = apply_brightness(src, factor=0.1)
        saved.append(save(f"underexposed_{i:02d}.jpg", dark))

    # ── Screenshot (1) ───────────────────────────────────────────────────────
    print("\n=== Screenshot (1, 1170×2532 white background) ===")
    screenshot = make_synthetic_image(1170, 2532, color=(240, 240, 240))
    saved.append(save("screenshot_01.jpg", screenshot))

    # ── Similar pair (2) ─────────────────────────────────────────────────────
    print("\n=== Similar pair (2, same image + small noise) ===")
    base_for_pair = base_images[0]  # first landscape
    saved.append(save("similar_pair_a.jpg", base_for_pair))
    similar_b = add_noise(base_for_pair, noise_amount=10)
    saved.append(save("similar_pair_b.jpg", similar_b))

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'=' * 50}")
    print(f"Total images saved: {len(saved)}")
    print(f"Directory: {os.path.abspath(OUTPUT_DIR)}")

    categories = {
        "landscape": [f for f in saved if "landscape" in f],
        "portrait": [f for f in saved if "portrait" in f],
        "food": [f for f in saved if "food" in f],
        "blurry": [f for f in saved if "blurry" in f],
        "overexposed": [f for f in saved if "overexposed" in f],
        "underexposed": [f for f in saved if "underexposed" in f],
        "screenshot": [f for f in saved if "screenshot" in f],
        "similar_pair": [f for f in saved if "similar_pair" in f],
    }
    for cat, files in categories.items():
        print(f"  {cat}: {len(files)} files")

    return 0


if __name__ == "__main__":
    sys.exit(main())
