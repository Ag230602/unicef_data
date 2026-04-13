# Publish the Visualization Publicly (Not Localhost)

Your public-ready file is:
- `deploy/index.html`

## Option A: GitHub Pages (free)
1. Create a new GitHub repo.
2. Upload the `deploy` folder contents (so `index.html` is at repo root or `/docs`).
3. In GitHub repo settings:
   - Pages → Build and deployment → Source: Deploy from a branch
   - Branch: `main`, folder: `/root` (or `/docs` if you used docs)
4. Wait ~1–2 minutes.
5. Open the generated URL: `https://<username>.github.io/<repo>/`

## Option B: Netlify Drop (fastest)
1. Go to https://app.netlify.com/drop
2. Drag and drop the `deploy` folder.
3. Netlify instantly gives a public URL.

## Option C: Cloudflare Pages
1. Go to https://pages.cloudflare.com/
2. Create project → Upload assets.
3. Upload `deploy` folder.
4. You get a public URL.

## Notes
- This file is fully offline/self-contained, so it deploys as a static single-page site.
- No backend required.
