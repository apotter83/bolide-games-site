# bolide.games

Static site for Bolide Games. Two pages, one stylesheet, no build step. Cloudflare Pages deploys `main`.

- **Add a game:** copy the `<article class="game">` block in `index.html`; put a 16:9 capture in `img/` at 1600 and 800 wide (webp).
- **Swap the Dodgeball VR image:** replace `img/dodgeball-vr-menu-1600.webp` and `-800.webp` (16:9).
- **New brand finals:** `python3 tools/trim-brand.py "/path/to/logo_files/main"` rewrites `img/*.svg` from the designer's 1000×1000 artboards. The originals are never edited.
- **Fonts:** self-hosted (SIL OFL); `tools/fetch-fonts.sh` re-pulls them.
- **Check:** `python3 tools/check.py` — alt text, no third-party requests, required anchors, nothing pointing at what does not exist.
- **www → apex:** a Cloudflare zone Redirect Rule (Rules → Redirect Rules, the "Redirect from WWW to root" template). Pages' `_redirects` file does not fire for a cross-host source, so there is none here.
- **Preview:** `python3 -m http.server 8765` then http://localhost:8765/ (locally `/privacy.html`; Pages serves it as `/privacy`).
