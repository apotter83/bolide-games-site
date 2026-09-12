#!/usr/bin/env python3
"""Structural rules for the site. Run from the repo root: python3 tools/check.py"""
import re, sys, os
from html.parser import HTMLParser

EXPECT_VIEWBOX = {
    "bolide-on-light.svg": "336 444 329 113", "bolide-on-dark.svg": "336 444 329 113",
    "bolide-black.svg": "336 444 329 113", "bolide-white.svg": "336 444 329 113",
    "meteor-red.svg": "369 417 263 167", "meteor-black.svg": "369 417 263 167",
    "app-icon-red.svg": "324 324 353 353", "app-icon-black.svg": "324 324 353 353",
}
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

for name, vb in EXPECT_VIEWBOX.items():
    path = os.path.join("img", name)
    if not os.path.exists(path): errors.append(f"missing {path}"); continue
    txt = open(path).read()
    m = re.search(r'viewBox="([^"]+)"', txt)
    if not m or m.group(1) != vb: errors.append(f"{path}: viewBox {m and m.group(1)} != {vb}")
    if "<rect" in txt and 'width="1000"' in txt: errors.append(f"{path}: artboard rect still present")
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
