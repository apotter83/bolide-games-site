#!/usr/bin/env python3
"""Trim the delivered brand artboards down to the mark itself. Reads the designer's
files, never writes to them; output goes to img/. Re-run when new finals arrive:
    python3 tools/trim-brand.py "/home/andrew/bolide_games/logo_files/files"

Two things bit this script once each, so both are load-bearing:

1. The artboard size is NOT fixed. The first delivery was 1000x1000 throughout; the
   second used 1000x440 for the lockups and tight boxes for the icons. The bbox is
   therefore measured in render pixels and converted back through the file's own
   viewBox — never assume one unit equals the other.
2. MEASURE WITH CHROME, NOT IMAGEMAGICK. There is no rsvg binary on this machine, so
   ImageMagick falls back to its internal SVG renderer, which drew a solid red block
   over half of the second delivery's lockups. A wrong render means a wrong bbox and
   a silently mangled crop. Chrome is the reference renderer and screenshots with a
   real alpha channel (--default-background-color=00000000).

The folder case varies between deliveries (icon / Icon), so the lookup is
case-insensitive.

Requires Google Chrome and Pillow."""
import re, sys, os, shutil, subprocess, tempfile
from PIL import Image

src = sys.argv[1] if len(sys.argv) > 1 else "/home/andrew/bolide_games/logo_files/files"
FILES = {
    "bolide-on-light": "without dot/bolide_A5 without dot.svg",
    "bolide-on-dark":  "without dot/bolide_A6 without dot.svg",
    "bolide-black":    "without dot/bolide_A7 without dot.svg",
    "bolide-white":    "without dot/bolide_A8 without dot.svg",
    "meteor-black":    "icon/bolide_icon black.svg",
    "meteor-red":      "icon/bolide_icon red.svg",
    "app-icon-black":  "icon/bolide_squar icon black.svg",
    "app-icon-red":    "icon/bolide_squar icon red.svg",
}
MARGIN_FRAC = 0.004     # a whisker of the mark's size, so antialiased edges are not clipped
PROBE_W = 1600          # probe width in px; the taller the render, the finer the bbox


def find(src, rel):
    """The delivered folder's case varies between deliveries (icon / Icon)."""
    path = os.path.join(src, rel)
    if os.path.exists(path):
        return path
    d, base = os.path.split(rel)
    for cand in os.listdir(src):
        if cand.lower() == d.lower() and os.path.exists(os.path.join(src, cand, base)):
            return os.path.join(src, cand, base)
    raise SystemExit("missing: " + rel + "   (under " + src + ")")


def content_bbox(svg_text, vw, vh):
    """Fraction of the viewBox the drawn marks actually occupy: (x0, y0, x1, y1) in 0..1.
    Rendered by Chrome; ImageMagick cannot be trusted with these files (see the docstring)."""
    h_px = max(1, int(round(PROBE_W * vh / vw)))
    with tempfile.TemporaryDirectory() as td:
        svg = os.path.join(td, "m.svg"); open(svg, "w").write(svg_text)
        page = os.path.join(td, "p.html")
        open(page, "w").write('<style>html,body{margin:0;background:transparent}'
                              'img{display:block;width:%dpx}</style><img src="m.svg">' % PROBE_W)
        png = os.path.join(td, "s.png")
        r = subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            "--default-background-color=00000000",
                            "--window-size=%d,%d" % (PROBE_W, h_px),
                            "--virtual-time-budget=4000", "--screenshot=" + png,
                            "file://" + page], capture_output=True)
        if not os.path.exists(png):
            raise SystemExit("chrome render failed: " + r.stderr.decode()[:200])
        im = Image.open(png)
        if im.mode != "RGBA":
            raise SystemExit("chrome returned no alpha channel — check the Chrome version")
        bb = im.getchannel("A").getbbox()
        w, h = im.size
    if bb is None:
        raise SystemExit("renders empty")
    return bb[0] / w, bb[1] / h, bb[2] / w, bb[3] / h


os.makedirs("img", exist_ok=True)
for name, rel in FILES.items():
    s = open(find(src, rel)).read()
    m = re.search(r'viewBox="\s*([-\d.]+)[ ,]+([-\d.]+)[ ,]+([-\d.]+)[ ,]+([-\d.]+)', s)
    if not m:
        raise SystemExit(name + ": no viewBox")
    vx, vy, vw, vh = (float(g) for g in m.groups())

    # drop any rect covering the whole artboard: that is the ground, not the mark
    def drop_ground(mm):
        t = mm.group(0)
        w = re.search(r'width="([\d.]+)', t); h = re.search(r'height="([\d.]+)', t)
        if w and h and float(w.group(1)) >= vw * 0.99 and float(h.group(1)) >= vh * 0.99:
            return ""
        return t
    s = re.sub(r'<rect\b[^>]*/>', drop_ground, s)
    s = re.sub(r'\s*style="enable-background:[^"]*"', '', s)
    s = re.sub(r'\s+x="0px"\s+y="0px"', '', s)
    # Strip width/height from the ROOT <svg> TAG ONLY so the page can size it.
    # A blanket strip is catastrophic here: the "l" of "bolide" is a <rect>, and
    # removing its width/height silently renders the wordmark as "bo ide".
    def strip_root_size(mm):
        return re.sub(r'\s+(?:width|height)="[^"]*"', '', mm.group(0))
    s = re.sub(r'<svg\b[^>]*>', strip_root_size, s, count=1)
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    s = re.sub(r'<\?xml[^>]*\?>\s*', '', s)

    fx0, fy0, fx1, fy1 = content_bbox(s, vw, vh)
    x0 = vx + fx0 * vw; y0 = vy + fy0 * vh
    x1 = vx + fx1 * vw; y1 = vy + fy1 * vh
    mrg = max(x1 - x0, y1 - y0) * MARGIN_FRAC
    vb = "%s %s %s %s" % tuple(round(v, 3) for v in (x0 - mrg, y0 - mrg,
                                                    x1 - x0 + 2 * mrg, y1 - y0 + 2 * mrg))
    s = re.sub(r'viewBox="[^"]*"', 'viewBox="%s"' % vb, s, count=1)

    tag = name.replace("-", "")      # unique class names so two inline copies never collide
    s = re.sub(r'\.(?:st|cls-)(\d)', lambda mm: '.%s%s' % (tag, mm.group(1)), s)
    s = re.sub(r'class="(?:st|cls-)(\d)"', lambda mm: 'class="%s%s"' % (tag, mm.group(1)), s)
    s = s.replace(' xml:space="preserve"', '').replace(' id="Layer_1"', '')
    open(os.path.join("img", name + ".svg"), "w").write(s.strip() + "\n")
    aspect = (x1 - x0) / (y1 - y0)
    print("%-16s viewBox=%-34s aspect=%.4f  <- %s" % (name, vb, aspect, rel))

# Derived assets. These used to be hand-copied after a re-trim, which is exactly how the
# favicon silently stayed on the previous delivery's crop while every other mark moved on.
shutil.copyfile(os.path.join("img", "meteor-red.svg"), os.path.join("img", "favicon.svg"))
print("%-16s <- img/meteor-red.svg" % "favicon.svg")

with tempfile.TemporaryDirectory() as td:
    page = os.path.join(td, "p.html")
    open(page, "w").write('<style>html,body{margin:0;background:transparent}'
                          'img{display:block;width:180px;height:180px}</style>'
                          '<img src="%s">' % os.path.abspath("img/app-icon-red.svg"))
    out = os.path.join(td, "i.png")
    subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--default-background-color=00000000", "--window-size=180,180",
                    "--virtual-time-budget=4000", "--screenshot=" + out, "file://" + page],
                   capture_output=True)
    if not os.path.exists(out):
        raise SystemExit("apple-touch-icon render failed")
    shutil.copyfile(out, os.path.join("img", "apple-touch-icon.png"))
print("%-16s <- img/app-icon-red.svg (180x180)" % "apple-touch-icon.png")

# img/og.png is NOT derived here: it composes the lockup with the Dodgeball VR title art
# and a line of type, so it is rebuilt by hand when the brand or that art changes.
