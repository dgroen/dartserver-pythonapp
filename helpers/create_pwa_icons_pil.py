#!/usr/bin/env python3
"""
Generate PWA icons using PIL/Pillow from SVG.

This script creates PNG icons in various sizes for PWA installation.
"""

import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("❌ Pillow not installed. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pillow"], check=True)  # noqa: S603
    from PIL import Image, ImageDraw


def create_dartboard_icon(size):
    """Create a dartboard icon programmatically."""
    # Create image with transparent background
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Colors
    bg_color = (26, 26, 46, 255)  # #1a1a2e
    ring_color = (233, 69, 96, 255)  # #e94560
    accent_color = (15, 52, 96, 255)  # #0f3460

    # Background circle
    draw.ellipse([0, 0, size, size], fill=bg_color)

    # Outer ring
    ring_width = max(2, size // 25)
    draw.ellipse(
        [size * 0.1, size * 0.1, size * 0.9, size * 0.9],
        outline=ring_color,
        width=ring_width,
    )

    # Middle ring
    draw.ellipse(
        [size * 0.2, size * 0.2, size * 0.8, size * 0.8],
        outline=accent_color,
        width=max(1, ring_width // 2),
    )

    # Inner ring
    draw.ellipse(
        [size * 0.3, size * 0.3, size * 0.7, size * 0.7],
        outline=ring_color,
        width=max(1, ring_width // 3),
    )

    # Bullseye outer
    draw.ellipse(
        [size * 0.42, size * 0.42, size * 0.58, size * 0.58],
        fill=accent_color,
    )

    # Bullseye center
    draw.ellipse(
        [size * 0.46, size * 0.46, size * 0.54, size * 0.54],
        fill=ring_color,
    )

    # Add dart (simplified)
    dart_start_x = int(size * 0.65)
    dart_start_y = int(size * 0.35)
    dart_end_x = int(size * 0.8)
    dart_end_y = int(size * 0.2)
    dart_width = max(1, size // 80)

    # Dart body
    draw.line(
        [(dart_start_x, dart_start_y), (dart_end_x, dart_end_y)],
        fill=(22, 33, 62, 255),
        width=dart_width * 2,
    )

    # Dart point
    draw.polygon(
        [
            (dart_end_x, dart_end_y),
            (dart_end_x + dart_width * 3, dart_end_y - dart_width),
            (dart_end_x + dart_width * 3, dart_end_y + dart_width),
        ],
        fill=(192, 192, 192, 255),
    )

    return img


def generate_icons():
    """Generate all required icon sizes."""
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]

    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    icons_dir = project_root / "static" / "icons"

    print("🎨 Generating PWA icons with PIL...")

    for size in sizes:
        output_path = icons_dir / f"icon-{size}x{size}.png"

        try:
            img = create_dartboard_icon(size)
            img.save(output_path, "PNG", optimize=True)
            print(f"✅ Generated {size}x{size} icon")
        except Exception as e:
            print(f"❌ Failed to generate {size}x{size} icon: {e}")

    print("✨ Icon generation complete!")
    print(f"📁 Icons saved to: {icons_dir}")


if __name__ == "__main__":
    generate_icons()
