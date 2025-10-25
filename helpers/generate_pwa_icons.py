#!/usr/bin/env python3
"""
Generate PWA icons from SVG for Android installation.

This script generates all required icon sizes for PWA installation on Android.
"""

import shutil
import subprocess
from pathlib import Path


def generate_icons():
    """Generate PWA icons in various sizes."""
    # Icon sizes needed for Android PWA
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]

    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    svg_path = project_root / "static" / "icons" / "icon.svg"
    icons_dir = project_root / "static" / "icons"

    if not svg_path.exists():
        print(f"❌ SVG file not found: {svg_path}")
        return False

    print("🎨 Generating PWA icons...")

    # Check if ImageMagick or Inkscape is available
    has_convert = shutil.which("convert") is not None
    has_inkscape = shutil.which("inkscape") is not None

    if not has_convert and not has_inkscape:
        print("⚠️  Neither ImageMagick nor Inkscape found.")
        print("📝 Creating placeholder icons...")
        create_placeholder_icons(icons_dir, sizes)
        return True

    # Generate icons
    for size in sizes:
        output_path = icons_dir / f"icon-{size}x{size}.png"

        if has_inkscape:
            # Use Inkscape (better quality)
            cmd = [
                "inkscape",
                str(svg_path),
                "--export-type=png",
                f"--export-filename={output_path}",
                f"--export-width={size}",
                f"--export-height={size}",
            ]
        else:
            # Use ImageMagick
            cmd = [
                "convert",
                "-background",
                "none",
                "-resize",
                f"{size}x{size}",
                str(svg_path),
                str(output_path),
            ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)  # noqa: S603
            print(f"✅ Generated {size}x{size} icon")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate {size}x{size} icon: {e}")

    print("✨ Icon generation complete!")
    return True


def create_placeholder_icons(icons_dir, sizes):
    """Create placeholder icon files."""
    readme_path = icons_dir / "GENERATE_ICONS.md"
    with readme_path.open("w") as f:
        f.write(
            """# PWA Icons Generation

## Required Icons

The following icon sizes are needed for Android PWA installation:

""",
        )
        for size in sizes:
            f.write(f"- icon-{size}x{size}.png\n")

        f.write(
            """
## How to Generate

### Option 1: Using Inkscape (Recommended)
```bash
sudo apt-get install inkscape
python3 helpers/generate_pwa_icons.py
```

### Option 2: Using ImageMagick
```bash
sudo apt-get install imagemagick
python3 helpers/generate_pwa_icons.py
```

### Option 3: Manual Generation
Use any image editor to export icon.svg to PNG files at the sizes listed above.

### Option 4: Online Tool
1. Go to https://realfavicongenerator.net/
2. Upload static/icons/icon.svg
3. Download the generated icons
4. Place them in static/icons/
""",
        )

    print(f"📝 Created instructions at {readme_path}")


if __name__ == "__main__":
    generate_icons()
