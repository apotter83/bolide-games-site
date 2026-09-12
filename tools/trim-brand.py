#!/usr/bin/env python3
"""Trim the delivered 1000x1000 brand artboards to the mark. Reads the designer's
files, never writes to them; output goes to img/. Re-run when finals arrive:
    python3 tools/trim-brand.py "/home/andrew/bolide_games/logo_files/main"
Requires ImageMagick `convert` and Pillow."""
import re, sys, os, subprocess, tempfile
from PIL import Image

src = sys.argv[1] if len(sys.argv) > 1 else "/home/andrew/bolide_games/logo_files/main"
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
MARGIN = 3   # viewBox units, so antialiased edges are not clipped
os.makedirs("img", exist_ok=True)
for name, rel in FILES.items():
    s = open(os.path.join(src, rel)).read()
    s = re.sub(r'<rect[^>]*width="1000"[^>]*height="1000"[^>]*/>', '', s)   # the artboard ground
    s = re.sub(r'<rect[^>]*height="1000"[^>]*width="1000"[^>]*/>', '', s)
    with tempfile.TemporaryDirectory() as td:
        full = os.path.join(td, "full.svg"); png = os.path.join(td, "probe.png")
        open(full, "w").write(s)
        subprocess.run(["convert", "-background", "none", "-density", "96", full, "-resize", "1000x1000", png], check=True)
        x0, y0, x1, y1 = Image.open(png).convert("RGBA").getbbox()   # px == viewBox units at 1000x1000
    vb = f"{x0-MARGIN} {y0-MARGIN} {x1-x0+2*MARGIN} {y1-y0+2*MARGIN}"
    s = re.sub(r'viewBox="[^"]*"', f'viewBox="{vb}"', s, count=1)
    s = re.sub(r'\s*style="enable-background:[^"]*"', '', s)
    s = re.sub(r'\s+x="0px"\s+y="0px"', '', s)
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    s = re.sub(r'<\?xml[^>]*\?>\s*', '', s)
    tag = name.replace("-", "")   # unique class names so two inline copies never collide
    s = re.sub(r'\.st(\d)', lambda m: f'.{tag}{m.group(1)}', s)
    s = re.sub(r'class="st(\d)"', lambda m: f'class="{tag}{m.group(1)}"', s)
    s = s.replace(' xml:space="preserve"', '').replace(' id="Layer_1"', '')
    open(os.path.join("img", name + ".svg"), "w").write(s.strip() + "\n")
    print(f"{name:16s} viewBox={vb}")
