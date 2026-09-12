#!/usr/bin/env python3
"""Structural rules for the site. Run from the repo root: python3 tools/check.py"""
import re, sys, os
from html.parser import HTMLParser

# What a correctly trimmed mark looks like, as the ASPECT of its viewBox. Exact viewBox
# numbers are NOT checked: each delivery from the designer uses different artboards
# (delivery 1 was 1000x1000 throughout, delivery 2 used 1000x440 plus tight icon boxes),
# so the crop numbers legitimately change while the artwork does not. What must hold is
# that the mark fills its box — an untrimmed file shows up as a wrong aspect.
EXPECT_ASPECT = {
    "bolide-on-light.svg": 3.05, "bolide-on-dark.svg": 3.05,
    "bolide-black.svg": 3.05, "bolide-white.svg": 3.05,
    "meteor-black.svg": 1.61, "meteor-red.svg": 1.61,
    "app-icon-black.svg": 1.00, "app-icon-red.svg": 1.00,
}
ASPECT_TOL = 0.06        # 6%: covers antialiasing and a designer's minor redraw, not an untrimmed box

errors = []

class P(HTMLParser):
    def __init__(s): super().__init__(); s.ids=set(); s.title=False; s.lang=None; s.links=[]
    def handle_starttag(s, tag, attrs):
        a = dict(attrs)
        if tag == "html": s.lang = a.get("lang")
        if tag == "title": s.title = True
        if "id" in a: s.ids.add(a["id"])
        if tag == "img":
            for k in ("alt", "width", "height"):
                if k not in a: errors.append(f"{s.f}: <img src={a.get('src')}> missing {k}")
        for k in ("src", "href"):
            v = a.get(k)
            if v and re.match(r"https?://", v): errors.append(f"{s.f}: external {k}={v}")
            if v: s.links.append(v)

def page(f):
    p = P(); p.f = f; p.feed(open(f).read())
    if p.lang != "en": errors.append(f"{f}: html lang != en")
    if not p.title: errors.append(f"{f}: no <title>")
    return p

for name, want in EXPECT_ASPECT.items():
    path = os.path.join("img", name)
    if not os.path.exists(path): errors.append(f"missing {path}"); continue
    txt = open(path).read()
    m = re.search(r'viewBox="\s*([-\d.]+)[ ,]+([-\d.]+)[ ,]+([-\d.]+)[ ,]+([-\d.]+)', txt)
    if not m: errors.append(f"{path}: no viewBox"); continue
    vw, vh = float(m.group(3)), float(m.group(4))
    if vh <= 0: errors.append(f"{path}: zero-height viewBox"); continue
    got = vw / vh
    if abs(got - want) / want > ASPECT_TOL:
        errors.append(f"{path}: aspect {got:.3f} != {want:.2f} (+/-{ASPECT_TOL:.0%}) — is it trimmed?")
    for r in re.findall(r'<rect\b[^>]*/>', txt):
        rw = re.search(r'width="([\d.]+)', r); rh = re.search(r'height="([\d.]+)', r)
        if rw and rh and float(rw.group(1)) >= vw * 0.99 and float(rh.group(1)) >= vh * 0.99:
            errors.append(f"{path}: full-artboard rect still present (the ground, not the mark)")

for f in ("img/favicon.svg", "img/apple-touch-icon.png", "img/og.png", "img/dodgeball-vr-logo.webp",
          "img/dodgeball-vr-menu-1600.webp", "img/dodgeball-vr-menu-800.webp"):
    if not os.path.exists(f): errors.append(f"missing {f}")

if os.path.exists("index.html"):
    idx = page("index.html")
    for i in ("games", "about"):
        if i not in idx.ids: errors.append(f"index.html: no id={i}")
    if "/privacy" not in idx.links: errors.append("index.html: footer does not link /privacy")
    if "mailto:support@bolide.games" not in idx.links: errors.append("index.html: no contact mailto")
    for bad in ("trailer", "store", "youtube", "discord", "twitter"):
        if re.search(bad, open("index.html").read(), re.I): errors.append(f"index.html: mentions '{bad}' (nothing may point at what does not exist)")
if os.path.exists("privacy.html"):
    pv = page("privacy.html")
    if "/" not in pv.links: errors.append("privacy.html: no link back to /")
for f in ("index.html", "privacy.html", "style.css"):
    if os.path.exists(f) and re.search(r"<script|fonts\.googleapis|fonts\.gstatic", open(f).read()): errors.append(f"{f}: script or Google Fonts reference")

print("\n".join(errors) if errors else "check: ok"); sys.exit(1 if errors else 0)
