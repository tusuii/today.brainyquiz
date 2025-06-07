#!/usr/bin/env python3
"""
Generate favicon files from SVG for the Quiz App
This script uses cairosvg to convert the SVG to various PNG sizes and favicon.ico
"""
import os
import sys
try:
    import cairosvg
except ImportError:
    print("Please install cairosvg: pip install cairosvg")
    sys.exit(1)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SVG_PATH = os.path.join(BASE_DIR, 'app', 'static', 'images', 'favicon.svg')
OUTPUT_DIR = os.path.join(BASE_DIR, 'app', 'static', 'images')

# Ensure the SVG exists
if not os.path.exists(SVG_PATH):
    print(f"SVG file not found: {SVG_PATH}")
    sys.exit(1)

# Generate PNG files in different sizes
sizes = [16, 32, 48, 96, 144, 192]
for size in sizes:
    output_path = os.path.join(OUTPUT_DIR, f'favicon-{size}x{size}.png')
    print(f"Generating {output_path}...")
    cairosvg.svg2png(url=SVG_PATH, write_to=output_path, output_width=size, output_height=size)

# Generate favicon.ico (uses 16x16, 32x32, 48x48)
try:
    from PIL import Image
    print("Generating favicon.ico...")
    
    # Load the PNG files
    icons = []
    for size in [16, 32, 48]:
        png_path = os.path.join(OUTPUT_DIR, f'favicon-{size}x{size}.png')
        if os.path.exists(png_path):
            icons.append(Image.open(png_path))
    
    # Save as ICO
    if icons:
        icons[0].save(
            os.path.join(OUTPUT_DIR, 'favicon.ico'),
            format='ICO',
            sizes=[(icon.width, icon.height) for icon in icons]
        )
        print("favicon.ico created successfully")
    else:
        print("No PNG files found to create favicon.ico")
except ImportError:
    print("PIL not installed. Install with: pip install pillow")
    print("favicon.ico not generated")

print("Favicon generation complete!")
