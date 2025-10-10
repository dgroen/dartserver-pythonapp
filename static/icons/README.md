# PWA Icons

This directory contains icons for the Progressive Web App.

## Current Status

A placeholder SVG icon (`icon.svg`) has been created. For production, you should:

1. **Generate PNG icons** from the SVG or create custom icons in the following sizes:
   - 72x72
   - 96x96
   - 128x128
   - 144x144
   - 152x152
   - 192x192
   - 384x384
   - 512x512

2. **Using ImageMagick** (if available):
   ```bash
   # Install ImageMagick if not available
   sudo apt-get install imagemagick librsvg2-bin
   
   # Generate icons
   for size in 72 96 128 144 152 192 384 512; do
     rsvg-convert -w $size -h $size icon.svg -o icon-${size}x${size}.png
   done
   ```

3. **Using online tools**:
   - Upload `icon.svg` to https://realfavicongenerator.net/
   - Or use https://www.pwabuilder.com/ to generate all required assets

4. **Using design software**:
   - Open `icon.svg` in Inkscape, Adobe Illustrator, or Figma
   - Export to PNG at each required size

## Icon Design Guidelines

- **Simple and recognizable**: The icon should be clear at small sizes
- **High contrast**: Ensure good visibility on various backgrounds
- **Maskable**: Consider creating a maskable version for Android
- **Consistent branding**: Match your app's color scheme and style

## Maskable Icons

For better Android support, create maskable icons with safe zones:
- The important content should be in the center 80% of the icon
- The outer 20% may be cropped on some devices

## Current Placeholder

The current `icon.svg` features:
- Dartboard design with rings
- Dart graphic
- "DARTS" text
- Color scheme: #1a1a2e (dark blue), #e94560 (red), #0f3460 (blue)

Replace this with your actual app branding before production deployment.