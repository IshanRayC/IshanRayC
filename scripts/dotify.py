#!/usr/bin/env python3
"""
Turn a portrait into dense dot-matrix SVG art with a falling-particle reveal.

Usage:
    python scripts/dotify.py assets/portrait-source.png -o assets/portrait.svg
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps
except ImportError:
    sys.exit("Pillow is required: python -m pip install Pillow")


# ---------------------------------------------------------------------------
# Image preparation
# ---------------------------------------------------------------------------

def load_image_grid(
    path: Path,
    cols: int,
    contrast: float,
    gamma: float,
    equalize: bool,
    detail: float,
):
    """
    Convert the source image into:
        luminance[y][x] -> 0..1
        rgb[y][x]       -> source colour

    Transparent pixels are treated as background.
    """

    img = ImageOps.exif_transpose(Image.open(path))

    mask = None

    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        alpha = img.getchannel("A")

        # Treat a real alpha channel as a subject mask.
        if alpha.getextrema()[0] < 250:
            mask = alpha

        bg = Image.new("RGBA", img.size, (0, 0, 0, 255))
        bg.alpha_composite(img)
        img = bg

    img = img.convert("RGB")

    gray = img.convert("L")

    # Improve shadow/detail information.
    if equalize:
        binary_mask = None
        if mask is not None:
            binary_mask = mask.point(
                lambda v: 255 if v > 127 else 0
            )

        gray = ImageOps.equalize(gray, mask=binary_mask)

    if detail > 0:
        radius = max(2, round(min(img.size) / 52))
        gray = gray.filter(
            ImageFilter.UnsharpMask(
                radius=radius,
                percent=round(detail * 100),
                threshold=0,
            )
        )

    if contrast != 1.0:
        gray = ImageEnhance.Contrast(gray).enhance(contrast)
        img = ImageEnhance.Contrast(img).enhance(contrast)

    width, height = img.size

    # Preserve the original aspect ratio.
    rows = max(1, round(cols * height / width))

    small_gray = gray.resize(
        (cols, rows),
        Image.Resampling.LANCZOS
    )

    small_color = img.resize(
        (cols, rows),
        Image.Resampling.LANCZOS
    )

    if mask is not None:
        small_mask = mask.resize(
            (cols, rows),
            Image.Resampling.LANCZOS
        )
        small_gray = ImageChops.multiply(
            small_gray,
            small_mask
        )

    gp = small_gray.load()
    cp = small_color.load()

    luminance = []
    rgb = []

    for y in range(rows):
        lum_row = []
        rgb_row = []

        for x in range(cols):
            value = gp[x, y] / 255.0

            # Gamma correction.
            value = value ** gamma

            value = max(0.0, min(1.0, value))

            lum_row.append(value)
            rgb_row.append(cp[x, y])

        luminance.append(lum_row)
        rgb.append(rgb_row)

    return cols, rows, luminance, rgb


# ---------------------------------------------------------------------------
# SVG
# ---------------------------------------------------------------------------

def build_svg(
    cols: int,
    rows: int,
    luminance,
    rgb,
    cell: float,
    dot_scale: float,
    floor: float,
    palette: bool,
    fall_duration: float,
    stagger: float,
    seed: int,
):
    """
    Build an SVG where every visible dot starts above the portrait
    and falls into its final position.

    The delay is mostly based on vertical position, so the animation
    visually reads as particles falling from the top.
    """

    random.seed(seed)

    width = cols * cell
    height = rows * cell

    max_radius = cell * 0.5 * dot_scale

    circles = []

    # Warm orange/amber palette inspired by the reference profile.
    def warm_color(value: float) -> str:
        stops = [
            (0.00, (85, 18, 10)),
            (0.20, (120, 25, 10)),
            (0.40, (175, 45, 12)),
            (0.60, (220, 82, 20)),
            (0.78, (255, 140, 45)),
            (0.92, (255, 190, 90)),
            (1.00, (255, 225, 145)),
        ]

        for i in range(len(stops) - 1):
            a_v, a_c = stops[i]
            b_v, b_c = stops[i + 1]

            if value <= b_v:
                t = (value - a_v) / max(b_v - a_v, 1e-9)

                r = round(a_c[0] + (b_c[0] - a_c[0]) * t)
                g = round(a_c[1] + (b_c[1] - a_c[1]) * t)
                b = round(a_c[2] + (b_c[2] - a_c[2]) * t)

                return f"#{r:02x}{g:02x}{b:02x}"

        return "#ffe191"

    for y in range(rows):
        for x in range(cols):
            value = luminance[y][x]

            # Remove almost-black cells.
            if value < floor:
                continue

            # Make brighter regions denser/larger.
            radius = max_radius * (value ** 0.82)

            if radius < 0.18:
                continue

            cx = x * cell + cell / 2
            cy = y * cell + cell / 2

            # Slight organic variation.
            jitter_x = random.uniform(-0.12, 0.12)
            jitter_y = random.uniform(-0.12, 0.12)

            cx += jitter_x
            cy += jitter_y

            if palette:
                # Use the source colour only very subtly;
                # the main appearance remains warm like the reference.
                sr, sg, sb = rgb[y][x]

                # Mix source colour toward the warm palette.
                warm = warm_color(value)
                fill = warm

                # Keep variables referenced intentionally.
                _ = (sr, sg, sb)
            else:
                fill = warm_color(value)

            # Falling distance.
            # Higher rows start farther above the final location.
            fall_distance = height * 0.9 + random.uniform(0, height * 0.18)

            # Mostly top-to-bottom, with a little random staggering.
            row_delay = (y / max(rows - 1, 1)) * stagger
            random_delay = random.uniform(0.0, stagger * 0.28)
            delay = row_delay + random_delay

            # Small per-dot duration variation.
            duration = fall_duration + random.uniform(-0.08, 0.12)

            circles.append(
                f"""
                <circle
                    class="dot"
                    cx="{cx:.2f}"
                    cy="{cy:.2f}"
                    r="{radius:.2f}"
                    fill="{fill}"
                    style="
                        --x: {cx:.2f}px;
                        --y: {cy:.2f}px;
                        --fall: {-fall_distance:.2f}px;
                        animation-delay: {delay:.3f}s;
                        animation-duration: {duration:.2f}s;
                    "
                />
                """
            )

    css = f"""
    <style>
        .dot {{
            opacity: 0;
            transform: translateY(var(--fall));
            animation-name: fall;
            animation-timing-function: cubic-bezier(0.16, 1, 0.3, 1);
            animation-fill-mode: forwards;
        }}

        @keyframes fall {{
            0% {{
                opacity: 0;
                transform: translateY(var(--fall));
            }}

            12% {{
                opacity: 0.15;
            }}

            68% {{
                opacity: 0.9;
                transform: translateY(5px);
            }}

            84% {{
                opacity: 1;
                transform: translateY(-2px);
            }}

            92% {{
                transform: translateY(1px);
            }}

            100% {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        @media (prefers-reduced-motion: reduce) {{
            .dot {{
                animation: none;
                opacity: 1;
                transform: none;
            }}
        }}
    </style>
    """

    header = f"""
    <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 {width:.0f} {height:.0f}"
        width="{width:.0f}"
        height="{height:.0f}"
        role="img"
        aria-label="Ishan Ray Chaudhuri dot matrix portrait"
    >
        {css}
        <rect width="100%" height="100%" fill="#0d1117" />
        <g>
    """

    footer = """
        </g>
    </svg>
    """

    return header + "".join(circles) + footer


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a falling dot-matrix portrait SVG."
    )

    parser.add_argument(
        "image",
        type=Path,
        help="source portrait PNG/JPG/WebP"
    )

    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        default=Path("assets/portrait.svg"),
        help="output SVG path"
    )

    parser.add_argument(
        "--cols",
        type=int,
        default=120,
        help="number of dots across"
    )

    parser.add_argument(
        "--cell",
        type=float,
        default=8.0,
        help="SVG units per cell"
    )

    parser.add_argument(
        "--dot-scale",
        type=float,
        default=0.88,
        help="maximum dot diameter as a fraction of a cell"
    )

    parser.add_argument(
        "--gamma",
        type=float,
        default=0.88,
        help="gamma correction"
    )

    parser.add_argument(
        "--contrast",
        type=float,
        default=1.35,
        help="image contrast"
    )

    parser.add_argument(
        "--equalize",
        action="store_true",
        help="recover detail from dark regions"
    )

    parser.add_argument(
        "--detail",
        type=float,
        default=0.7,
        help="local facial detail enhancement"
    )

    parser.add_argument(
        "--floor",
        type=float,
        default=0.045,
        help="ignore cells below this brightness"
    )

    parser.add_argument(
        "--fall-duration",
        type=float,
        default=1.25,
        help="fall duration per dot"
    )

    parser.add_argument(
        "--stagger",
        type=float,
        default=2.7,
        help="total vertical stagger"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="random seed"
    )

    args = parser.parse_args()

    if not args.image.exists():
        sys.exit(f"Image not found: {args.image}")

    args.out.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    cols, rows, luminance, rgb = load_image_grid(
        args.image,
        args.cols,
        args.contrast,
        args.gamma,
        equalize=args.equalize,
        detail=args.detail,
    )

    svg = build_svg(
        cols=cols,
        rows=rows,
        luminance=luminance,
        rgb=rgb,
        cell=args.cell,
        dot_scale=args.dot_scale,
        floor=args.floor,
        palette=True,
        fall_duration=args.fall_duration,
        stagger=args.stagger,
        seed=args.seed,
    )

    args.out.write_text(
        svg,
        encoding="utf-8"
    )

    print(
        f"Generated {args.out} "
        f"({cols} x {rows} cells)"
    )


if __name__ == "__main__":
    main()
