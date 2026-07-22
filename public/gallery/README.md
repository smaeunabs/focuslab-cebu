# Gallery photos

The 8 photos for the homepage Gallery section live here, resized and compressed
from the originals (each was several MB; these are optimized to ~80-190KB each
so the section stays fast on mobile):

- `gallery-1.jpg` through `gallery-8.jpg`

Tips:
- Currently sized to fit a 3:4 portrait tile (900x1200), since the source photos
  were portrait. If you add landscape photos, resizing them to roughly the same
  height keeps the grid looking even.
- Keep each file under ~300KB (export as JPG, "web quality" ~70-80%) so the page
  stays fast to load.
- Want more than 8? Add `gallery-9.jpg`, etc., and add a matching
  `<div class="gallery-item"><img src="/public/gallery/gallery-9.jpg" ...></div>` line in the
  Gallery section of `index.html`.
- Until a file exists at one of these paths, that tile is skipped automatically (no broken-image icon).
