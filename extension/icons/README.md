# Extension Icons

This directory should contain the following icon files for the Chrome extension:

- `icon16.png` - 16x16 pixels (toolbar icon)
- `icon32.png` - 32x32 pixels (extension management page)
- `icon48.png` - 48x48 pixels (extension management page)
- `icon128.png` - 128x128 pixels (Chrome Web Store)

## Icon Requirements

- **Format**: PNG with transparency
- **Design**: Should represent the Cambridge AI Tutor brand
- **Colors**: Use the brand colors (green #4CAF50 as primary)
- **Content**: Should include elements suggesting education/tutoring (e.g., graduation cap, book, question mark)

## Temporary Placeholders

For development purposes, you can create simple colored squares or use online icon generators until proper icons are designed.

Example using ImageMagick to create placeholder icons:

```bash
# Create placeholder icons with green background and white text
convert -size 16x16 xc:#4CAF50 -pointsize 10 -fill white -gravity center -annotate +0+0 "T" icon16.png
convert -size 32x32 xc:#4CAF50 -pointsize 20 -fill white -gravity center -annotate +0+0 "T" icon32.png
convert -size 48x48 xc:#4CAF50 -pointsize 30 -fill white -gravity center -annotate +0+0 "T" icon48.png
convert -size 128x128 xc:#4CAF50 -pointsize 80 -fill white -gravity center -annotate +0+0 "T" icon128.png
```