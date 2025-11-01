# Custom Images Directory

This directory is for storing custom images for your Women Safety web application.

## Current Images
The landing page currently uses professional illustrations from **popsy.co** (free, open-source, no attribution required):
- Hero Section: `woman-and-man-holding-safe-sign.svg`
- How It Works: `work-from-home.svg`
- Trust Section: `app-launch.svg`

## Adding Your Own Images

### Step 1: Add Images Here
Place your custom images in this directory:
```
app/static/images/
├── your-image-1.jpg
├── your-image-2.png
└── your-logo.svg
```

### Step 2: Use in Templates
Reference them in HTML templates using Flask's `url_for()`:

```html
<!-- Example: Replace hero image -->
<img src="{{ url_for('static', filename='images/your-hero-image.png') }}" 
     alt="Description" 
     class="img-fluid">
```

### Step 3: Supported Formats
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- **Vectors**: `.svg` (recommended for logos and icons)

## Recommended Image Sizes

### Landing Page
- **Hero Image**: 600x600px (square) or 800x600px (landscape)
- **Section Illustrations**: 400x400px to 600x600px
- **Logos/Icons**: 100x100px or SVG for scalability

### Community & Profile
- **Profile Pictures**: 200x200px (square)
- **Post Images**: 1200x675px (16:9 ratio)

### Incident Reports
- **Evidence Photos**: Any size (will be stored as uploaded)

## Example: Replace Landing Page Images

To replace the current popsy.co illustrations with your own:

1. **Hero Section** (in `templates/landing.html` line ~60):
```html
<!-- Old -->
<img src="https://illustrations.popsy.co/white/woman-and-man-holding-safe-sign.svg">

<!-- New -->
<img src="{{ url_for('static', filename='images/my-hero.png') }}">
```

2. **How It Works** (line ~120):
```html
<!-- Old -->
<img src="https://illustrations.popsy.co/white/work-from-home.svg">

<!-- New -->
<img src="{{ url_for('static', filename='images/how-it-works.png') }}">
```

3. **Trust Section** (line ~180):
```html
<!-- Old -->
<img src="https://illustrations.popsy.co/white/app-launch.svg">

<!-- New -->
<img src="{{ url_for('static', filename='images/trust-badge.png') }}">
```

## Free Image Resources

If you need more free images:
- **Illustrations**: [popsy.co/illustrations](https://illustrations.popsy.co/)
- **Photos**: [Unsplash](https://unsplash.com/) | [Pexels](https://pexels.com/)
- **Icons**: [Bootstrap Icons](https://icons.getbootstrap.com/) | [Heroicons](https://heroicons.com/)
- **Illustrations**: [unDraw](https://undraw.co/) | [Storyset](https://storyset.com/)

## Tips
- ✅ Use **SVG** for scalable graphics (logos, icons, illustrations)
- ✅ Optimize images before uploading (compress JPG/PNG)
- ✅ Use descriptive filenames: `hero-safety-banner.png` not `IMG_001.png`
- ✅ Keep consistent color scheme (current: purple/pink accents)
- ✅ Test images on mobile devices (responsive design)

---

**Need help?** Just ask me to update the templates with your custom images!
