# Gallery photos

Drop the photos for the homepage Gallery section in this folder, named:

- `gallery-1.jpg`
- `gallery-2.jpg`
- `gallery-3.jpg`
- `gallery-4.jpg`
- `gallery-5.jpg`
- `gallery-6.jpg`

Tips:
- Roughly 4:3 aspect ratio (e.g. 1200x900) looks best in the grid, since each tile crops to that shape.
- Keep each file under ~500KB (export as JPG, "web quality" ~70-80%) so the page stays fast to load.
- Want more than 6? Just add `gallery-7.jpg`, `gallery-8.jpg`, etc., and add a matching
  `<div class="gallery-item"><img src="/public/gallery/gallery-7.jpg" ...></div>` line in the
  Gallery section of `index.html`.
- Until a file exists at one of these paths, that tile is skipped automatically (no broken-image icon).
