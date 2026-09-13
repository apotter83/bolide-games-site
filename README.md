# bolide.games

Static site for Bolide Games. Two pages, one stylesheet, no build step. Cloudflare Pages deploys `main`.

- **Add a game:** copy the `<article class="game">` block in `index.html`; put a 16:9 capture in `img/` at 1600 and 800 wide (webp).
- **Swap a Dodgeball VR screenshot:** replace `img/dodgeball-vr-match-*.webp` (the action shot) or `img/dodgeball-vr-menu-*.webp` (the VS screen), each at 1600 and 800 wide, 16:9. Quest captures are 3840x2160, already 16:9, so they only need resizing. Update the `alt` text to describe the new shot.
- **New brand finals:** `python3 tools/trim-brand.py "/path/to/logo_files/files"` rewrites `img/*.svg` from the designer's artboards (any size), plus `favicon.svg` and `apple-touch-icon.png`. The originals are never edited. Measuring is done by Chrome, not ImageMagick, which renders these files wrong. `img/og.png` is composed by hand and is the one asset the script does not rebuild.
- **After replacing an image:** purge it at Cloudflare (zone → Caching → Configuration → Custom Purge → URL). Filenames are stable, so the edge can otherwise keep serving the old bytes.
- **Fonts:** self-hosted (SIL OFL); `tools/fetch-fonts.sh` re-pulls them.
- **Check:** `python3 tools/check.py` — alt text, no third-party requests, required anchors, nothing pointing at what does not exist.
- **www → apex:** a Cloudflare zone Redirect Rule (Rules → Redirect Rules, the "Redirect from WWW to root" template). Pages' `_redirects` file does not fire for a cross-host source, so there is none here.
- **Preview:** `python3 -m http.server 8765` then http://localhost:8765/ (locally `/privacy.html`; Pages serves it as `/privacy`).
