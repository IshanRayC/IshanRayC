#!/usr/bin/env python3

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
except ImportError:
    sys.exit("Pillow is required. Install it with: python -m pip install Pillow")


# ============================================================
# IMAGE PROCESSING
# ============================================================

def load_grid(
    path: Path,
    cols: int,
    contrast: float,
    gamma: float,
    detail: float,
    equalize: bool,
):
    img = ImageOps.exif_transpose(Image.open(path))

    # Handle transparency correctly.
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        alpha = img.getchannel("A")

        # Composite against black so the dark background disappears
        # naturally when converted to luminance.
        bg = Image.new("RGBA", img.size, (0, 0, 0, 255))
        bg.alpha_composite(img)
        img = bg.convert("RGB")

        # Use alpha to suppress transparent pixels.
        alpha_rgb = alpha
    else:
        img = img.convert("RGB")
        alpha_rgb = None

    gray = img.convert("L")

    if equalize:
        gray = ImageOps.equalize(gray)

    if detail > 0:
        radius = max(1, round(min(img.size) / 60))
        gray = gray.filter(
            ImageFilter.UnsharpMask(
                radius=radius,
                percent=round(detail * 100),
                threshold=1,
            )
        )

    gray = ImageEnhance.Contrast(gray).enhance(contrast)

    width, height = img.size

    # Preserve aspect ratio.
    rows = max(1, round(cols * height / width))

    gray_small = gray.resize(
        (cols, rows),
        Image.Resampling.LANCZOS,
    )

    if alpha_rgb is not None:
        alpha_small = alpha_rgb.resize(
            (cols, rows),
            Image.Resampling.LANCZOS,
        )
    else:
        alpha_small = None

    px = gray_small.load()
    apx = alpha_small.load() if alpha_small else None

    values = []

    for y in range(rows):
        row = []

        for x in range(cols):
            value = px[x, y] / 255.0

            if apx is not None:
                value *= apx[x, y] / 255.0

            value = max(0.0, min(1.0, value))
            value = value ** gamma

            row.append(value)

        values.append(row)

    return cols, rows, values


# ============================================================
# MATRIX GREEN PALETTE
# ============================================================

def green_color(v: float) -> str:
    """
    Matrix-style monochrome green.
    Dark values -> deep green
    Bright values -> vivid/lime green
    """

    stops = [
        (0.00, (0, 20, 4)),
        (0.18, (0, 45, 8)),
        (0.38, (0, 85, 14)),
        (0.58, (0, 135, 28)),
        (0.75, (35, 190, 55)),
        (0.90, (110, 225, 100)),
        (1.00, (180, 255, 170)),
    ]

    for i in range(len(stops) - 1):
        a_v, a_c = stops[i]
        b_v, b_c = stops[i + 1]

        if v <= b_v:
            t = (v - a_v) / max(b_v - a_v, 1e-9)

            r = round(a_c[0] + (b_c[0] - a_c[0]) * t)
            g = round(a_c[1] + (b_c[1] - a_c[1]) * t)
            b = round(a_c[2] + (b_c[2] - a_c[2]) * t)

            return f"#{r:02x}{g:02x}{b:02x}"

    return "#b4ffa8"


# ============================================================
# SVG GENERATION
# ============================================================

def build_svg(
    cols: int,
    rows: int,
    values,
    cell: float,
    dot_scale: float,
    floor: float,
    fall_time: float,
    max_delay: float,
    seed: int,
):
    random.seed(seed)

    width = cols * cell
    height = rows * cell

    max_radius = cell * 0.48 * dot_scale

    circles = []

    # We want a falling-rain feel:
    #
    #   •  •      •
    #   ↓  ↓      ↓
    #      ↓
    #   •  ↓  •   ↓
    #       ↓
    #  FINAL PORTRAIT
    #
    # Every dot begins above its final position.
    # Delay is randomized so it feels organic instead of row-by-row.

    for y in range(rows):
        for x in range(cols):
            value = values[y][x]

            # Remove empty/background cells.
            if value < floor:
                continue

            # Bright parts get larger dots.
            radius = max_radius * (value ** 0.78)

            if radius < 0.20:
                continue

            cx = x * cell + cell / 2
            cy = y * cell + cell / 2

            # Tiny jitter keeps the matrix organic.
            cx += random.uniform(-0.10, 0.10)
            cy += random.uniform(-0.10, 0.10)

            # Every particle starts above the canvas.
            start_y = -height * (
                0.35 + random.random() * 0.85
            )

            # Mix vertical position + randomness.
            #
            # This gives us a waterfall of individual drops instead
            # of a rigid top-to-bottom row reveal.
            vertical_component = (
                y / max(rows - 1, 1)
            ) * max_delay * 0.55

            random_component = (
                random.random() * max_delay * 0.75
            )

            delay = vertical_component + random_component

            # Slight variation prevents perfect synchronization.
            duration = fall_time + random.uniform(-0.16, 0.20)

            fill = green_color(value)

            circles.append(
                f'''
                <circle
                    class="dot"
                    cx="{cx:.2f}"
                    cy="{cy:.2f}"
                    r="{radius:.2f}"
                    fill="{fill}"
                    style="--start-y:{start_y:.2f}px;
                           animation-delay:{delay:.3f}s;
                           animation-duration:{duration:.3f}s"
                />
                '''
            )

    css = """
    <style>

        .dot {
            opacity: 0;
            transform: translateY(var(--start-y));
            animation-name: matrixFall;
            animation-timing-function: cubic-bezier(0.15, 0.85, 0.28, 1);
            animation-fill-mode: forwards;
        }

        /*
         * Matrix-style falling particle:
         *
         * 0%   = invisible above the image
         * 10%  = appears
         * 70%  = approaches destination
         * 88%  = tiny overshoot
         * 100% = settles
         */
        @keyframes matrixFall {

            0% {
                opacity: 0;
                transform: translateY(var(--start-y));
            }

            8% {
                opacity: 0.15;
            }

            45% {
                opacity: 0.65;
            }

            72% {
                opacity: 0.95;
                transform: translateY(8px);
            }

            86% {
                opacity: 1;
                transform: translateY(-3px);
            }

            94% {
                transform: translateY(1px);
            }

            100% {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @media (prefers-reduced-motion: reduce) {

            .dot {
                animation: none;
                opacity: 1;
                transform: none;
            }

        }

    </style>
    """

    # Transparent SVG background.
    #
    # This is important because GitHub can then supply its own
    # background instead of us drawing a giant rectangle.
    svg_start = f'''
<svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 {width:.0f} {height:.0f}"
    width="{width:.0f}"
    height="{height:.0f}"
    role="img"
    aria-label="Ishan Ray Chaudhuri Matrix dot portrait"
>
{css}
<g>
'''

    svg_end = """
</g>
</svg>
"""

    return svg_start + "".join(circles) + svg_end


# ============================================================
# CLI
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description="Generate a high-resolution Matrix-style falling dot portrait."
    )

    parser.add_argument(
        "image",
        type=Path,
    )

    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        default=Path("assets/portrait.svg"),
    )

    parser.add_argument(
        "--cols",
        type=int,
        default=160,
    )

    parser.add_argument(
        "--cell",
        type=float,
        default=5.5,
    )

    parser.add_argument(
        "--dot-scale",
        type=float,
        default=0.92,
    )

    parser.add_argument(
        "--gamma",
        type=float,
        default=0.82,
    )

    parser.add_argument(
        "--contrast",
        type=float,
        default=1.55,
    )

    parser.add_argument(
        "--detail",
        type=float,
        default=0.85,
    )

    parser.add_argument(
        "--floor",
        type=float,
        default=0.035,
    )

    parser.add_argument(
        "--fall-time",
        type=float,
        default=1.15,
    )

    parser.add_argument(
        "--max-delay",
        type=float,
        default=3.2,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    args = parser.parse_args()

    if not args.image.exists():
        sys.exit(f"Image not found: {args.image}")

    args.out.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cols, rows, values = load_grid(
        args.image,
        args.cols,
        args.contrast,
        args.gamma,
        args.detail,
        equalize=True,
    )

    svg = build_svg(
        cols=cols,
        rows=rows,
        values=values,
        cell=args.cell,
        dot_scale=args.dot_scale,
        floor=args.floor,
        fall_time=args.fall_time,
        max_delay=args.max_delay,
        seed=args.seed,
    )

    args.out.write_text(
        svg,
        encoding="utf-8",
    )

    print(
        f"Generated {args.out} "
        f"using {cols} x {rows} cells."
    )


if __name__ == "__main__":
    main()
