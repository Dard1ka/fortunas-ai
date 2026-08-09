"""Hasilkan seluruh aset ikon Fortunas dari SATU sumber transparan.

Jalankan manual setelah mengganti assets/brand/logo-mark-source.png:

    python scripts/gen_brand_assets.py

Butuh Pillow. Bukan bagian build/CI — hasilnya di-commit ke repo supaya
`npm run build` tidak pernah bergantung pada Python.

Kenapa tile putih hanya untuk ikon sistem (bukan untuk mark di dalam app):
  - favicon: mark navy transparan tidak terlihat di tab bertema gelap;
  - apple-touch: iOS mengganti area transparan menjadi HITAM;
  - maskable: Android memotong ikon jadi lingkaran, butuh latar penuh.
Mark di dalam app dipakai di atas latar krem/putih, jadi tetap transparan.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "brand" / "logo-mark-source.png"
OUT = ROOT / "frontend" / "public"
TILE_BG = (255, 255, 255, 255)
RADIUS_RATIO = 0.22


def load_mark() -> Image.Image:
    """Sumber dipangkas ke bounding box agar padding kita yang menentukan."""
    im = Image.open(SRC).convert("RGBA")
    return im.crop(im.split()[-1].getbbox())


def fit(mark: Image.Image, box: int) -> Image.Image:
    """Skala mark agar muat di kotak box x box TANPA mengubah proporsi."""
    w, h = mark.size
    scale = min(box / w, box / h)
    return mark.resize(
        (max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS
    )


def tile_bg(size: int, rounded: bool) -> Image.Image:
    """Latar tile. rounded=False -> persegi penuh (full-bleed).

    apple-touch-icon dan ikon maskable WAJIB persegi penuh: iOS memangkasnya
    jadi squircle dan Android jadi lingkaran/rounded. Kalau kita sudah
    membulatkannya duluan, sudut transparan sisa kita muncul sebagai sliver
    hitam di iOS dan potongan janggal di Android.
    """
    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    if not rounded:
        tile.paste(TILE_BG, [0, 0, size, size])
        return tile
    draw = ImageDraw.Draw(tile)
    draw.rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=round(size * RADIUS_RATIO), fill=TILE_BG
    )
    return tile


def compose(size: int, pad_ratio: float, tile: bool, rounded: bool = True) -> Image.Image:
    """Kanvas persegi; mark di tengah dengan padding pad_ratio di tiap sisi."""
    canvas = tile_bg(size, rounded) if tile else Image.new("RGBA", (size, size), (0, 0, 0, 0))
    inner = max(1, round(size * (1 - 2 * pad_ratio)))
    mark = fit(load_mark(), inner)
    canvas.alpha_composite(mark, ((size - mark.width) // 2, (size - mark.height) // 2))
    return canvas


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # (nama, ukuran, padding, pakai tile, tile membulat)
    jobs = [
        ("logo-mark.png", 512, 0.06, False, False),     # dalam app: transparan
        ("favicon-16.png", 16, 0.08, True, True),
        ("favicon-32.png", 32, 0.08, True, True),
        ("apple-touch-icon.png", 180, 0.12, True, False),   # iOS yang memangkas
        ("icon-192.png", 192, 0.10, True, True),
        ("icon-512.png", 512, 0.10, True, True),
        ("icon-512-maskable.png", 512, 0.20, True, False),  # Android yang memangkas
    ]
    for name, size, pad, tile, rounded in jobs:
        img = compose(size, pad, tile, rounded)
        img.save(OUT / name)
        print(f"  {name:24} {img.size[0]}x{img.size[1]}")

    ico = compose(64, 0.08, True, True)
    ico.save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print("  favicon.ico              16/32/48")


if __name__ == "__main__":
    main()
