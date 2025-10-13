# PWA Icons Generation

## Required Icons

The following icon sizes are needed for Android PWA installation:

- icon-72x72.png
- icon-96x96.png
- icon-128x128.png
- icon-144x144.png
- icon-152x152.png
- icon-192x192.png
- icon-384x384.png
- icon-512x512.png

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
