"""Brand assets: article image (1200x675), GitHub banner (1280x640), favicon.

    python -m scripts.make_brand_assets

Deterministic (seeded particle scatter, system fonts). Output:
  docs/assets/article-image.png   1200x675  (submission form article image)
  docs/assets/banner.png          1280x640  (GitHub social preview / README top)
  docs/assets/banner.svg          vector master for the banner
  frontend/src/app/icon.svg       favicon (Next.js file convention)
  frontend/src/app/opengraph-image.png      1200x675 social card
"""
from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BG = (5, 7, 10)
GRID = (139, 152, 165, 14)
EMERALD = (52, 211, 153)
EMERALD_DIM = (52, 211, 153, 120)
ROSE = (251, 113, 133)
WHITE = (232, 237, 242)
MUTED = (139, 152, 165)
LINE = (27, 35, 44)


def _font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        ["consolab.ttf", "arialbd.ttf"] if mono else
        (["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"])
    )
    for name in candidates:
        path = Path("C:/Windows/Fonts") / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _grid(draw: ImageDraw.ImageDraw, w: int, h: int, step: int = 44) -> None:
    for x in range(0, w, step):
        draw.line([(x, 0), (x, h)], fill=GRID, width=1)
    for y in range(0, h, step):
        draw.line([(0, y), (w, y)], fill=GRID, width=1)


def _particles(draw: ImageDraw.ImageDraw, w: int, h: int, seed: int = 20260828,
               n: int = 170, x0: float = 0.42) -> None:
    """Signal scatter on the right side: emerald survivors, a few rose rejects."""
    rng = random.Random(seed)
    for _ in range(n):
        cx = w * x0 + rng.random() * w * (0.98 - x0)
        cy = rng.random() * h
        r = rng.choice([2, 2, 3, 3, 4, 5, 7, 9])
        if rng.random() < 0.12:
            color = (113, 47, 54, rng.randint(60, 130))       # muted rose
        else:
            alpha = rng.randint(36, 150)
            color = (20 + EMERALD[0] * 0, 90, 68, alpha) if False else \
                    (int(20 + 32 * (alpha / 150)), int(90 + 121 * (alpha / 150)),
                     int(68 + 85 * (alpha / 150)), alpha)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def _mark(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 44) -> None:
    draw.rounded_rectangle([x, y, x + size, y + size], radius=10,
                           outline=LINE, width=2,
                           fill=(10, 14, 19))
    f = _font(int(size * 0.42), bold=True)
    draw.text((x + size / 2, y + size / 2), "SG", font=f, fill=EMERALD, anchor="mm")


def _footer(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    f = _font(20, mono=True)
    draw.text((x, y), "0.925 catch vs 0.475 baseline   ·   0.0 false rejects   ·   F2 1.0   ·   McNemar p = 0.00029",
              font=f, fill=MUTED)
    draw.text((x, y + 30), "github.com/Prakhar2025/SignalGate", font=f, fill=(95, 104, 115))


def article_image() -> None:
    w, h = 1200, 675
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img, "RGBA")
    _grid(d, w, h)
    _particles(d, w, h)
    d.line([(0, h - 110), (w, h - 110)], fill=LINE, width=1)

    _mark(d, 56, 52)
    kf = _font(19, mono=True)
    d.text((114, 60), "AGENTIC RESEARCH-INTEGRITY GATE", font=kf, fill=MUTED)
    d.ellipse([100, 66, 106, 72], fill=EMERALD)

    hf = _font(62, bold=True)
    d.text((56, 210), "Research teams", font=hf, fill=WHITE)
    d.text((56, 288), "don't lack signals.", font=hf, fill=WHITE)
    d.text((56, 366), "They lack gates.", font=hf, fill=EMERALD)

    sf = _font(24)
    d.text((56, 470), "Statistical probes investigate every candidate signal.", font=sf, fill=MUTED)
    d.text((56, 504), "Verdicts with receipts. Silence unless it deserves an hour.", font=sf, fill=MUTED)

    _footer(d, 56, h - 74)
    out = ROOT / "docs/assets/article-image.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print("wrote", out)


def banner() -> None:
    w, h = 1280, 640
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img, "RGBA")
    _grid(d, w, h)
    _particles(d, w, h, n=150, x0=0.40)
    d.line([(0, h - 100), (w, h - 100)], fill=LINE, width=1)

    _mark(d, 56, 48)
    d.text((114, 56), "SignalGate", font=_font(26, bold=True), fill=WHITE)

    hf = _font(58, bold=True)
    d.text((56, 190), "Research teams", font=hf, fill=WHITE)
    d.text((56, 264), "don't lack signals.", font=hf, fill=WHITE)
    d.text((56, 338), "They lack gates.", font=hf, fill=EMERALD)

    kf = _font(17, mono=True)
    probes = ["timestamp_alignment_probe", "label_permutation_test",
              "regime_subsample", "turnover_and_cost_sanity"]
    for i, name in enumerate(probes):
        y = 200 + i * 30
        d.ellipse([w - 380, y + 7, w - 372, y + 15], fill=EMERALD_DIM)
        d.text((w - 356, y), name, font=kf, fill=MUTED)

    d.text((56, h - 74), "0.925 catch vs 0.475 baseline   ·   0.0 false rejects   ·   p = 0.00029   ·   100% synthetic, seed 20260828",
           font=_font(19, mono=True), fill=MUTED)
    out = ROOT / "docs/assets/banner.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)

    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="640" viewBox="0 0 1280 640">
  <rect width="1280" height="640" fill="#05070a"/>
  <rect x="0" y="540" width="1280" height="2" fill="#1b232c"/>
  <rect x="56" y="48" width="44" height="44" rx="10" fill="#0a0e13" stroke="#1b232c" stroke-width="2"/>
  <text x="78" y="78" font-family="Consolas, monospace" font-size="19" font-weight="700" fill="#34d399" text-anchor="middle">SG</text>
  <text x="114" y="76" font-family="Segoe UI, Arial" font-size="26" font-weight="700" fill="#e8edf2">SignalGate</text>
  <text x="56" y="234" font-family="Segoe UI, Arial" font-size="58" font-weight="700" fill="#e8edf2">Research teams</text>
  <text x="56" y="308" font-family="Segoe UI, Arial" font-size="58" font-weight="700" fill="#e8edf2">don't lack signals.</text>
  <text x="56" y="382" font-family="Segoe UI, Arial" font-size="58" font-weight="700" fill="#34d399">They lack gates.</text>
  <text x="56" y="576" font-family="Consolas, monospace" font-size="19" fill="#8b98a5">0.925 catch vs 0.475 baseline · 0.0 false rejects · p = 0.00029 · 100% synthetic, seed 20260828</text>
</svg>"""
    (ROOT / "docs/assets/banner.svg").write_text(svg, encoding="utf-8")
    print("wrote", out)


def favicon() -> None:
    out = ROOT / "frontend/src/app/icon.svg"
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#05070a"/>
  <rect x="1.5" y="1.5" width="61" height="61" rx="12.5" fill="none" stroke="#1b232c" stroke-width="3"/>
  <circle cx="18" cy="40" r="3.5" fill="#34d399" opacity="0.85"/>
  <circle cx="32" cy="24" r="2.5" fill="#34d399" opacity="0.55"/>
  <circle cx="46" cy="32" r="3" fill="#fb7185" opacity="0.6"/>
  <text x="32" y="47" font-family="Consolas, monospace" font-size="26" font-weight="700" fill="#34d399" text-anchor="middle">SG</text>
</svg>"""
    out.write_text(svg, encoding="utf-8")
    print("wrote", out)


def opengraph() -> None:
    w, h = 1200, 675
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img, "RGBA")
    _grid(d, w, h)
    _particles(d, w, h)
    d.line([(0, h - 110), (w, h - 110)], fill=LINE, width=1)
    _mark(d, 56, 52)
    d.text((114, 60), "SignalGate", font=_font(24, bold=True), fill=WHITE)
    hf = _font(58, bold=True)
    d.text((56, 220), "Research teams don't lack signals.", font=hf, fill=WHITE)
    d.text((56, 296), "They lack gates.", font=hf, fill=EMERALD)
    d.text((56, 400), "An agentic research-integrity gate for candidate trading signals.",
           font=_font(24), fill=MUTED)
    d.text((56, 436), "0.925 catch · 0.0 false rejects · byte-identically reproducible, zero keys",
           font=_font(24), fill=MUTED)
    _footer(d, 56, h - 74)
    out = ROOT / "frontend/src/app/opengraph-image.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print("wrote", out)


if __name__ == "__main__":
    article_image()
    banner()
    favicon()
    opengraph()
