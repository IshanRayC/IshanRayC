#!/usr/bin/env python3

"""
Generate a high-resolution circular dot-matrix portrait.

Source:
    assets/portrait-source.png

Output:
    assets/portrait.svg

Design goals:
    - Preserve source colours
    - Preserve the complete visible portrait
    - Circular dots similar to a halftone/dot-matrix portrait
    - Transparent dark background so the GitHub profile background shows through
    - Bottom-to-top reveal
    - Individual particles fall from above and settle into position
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from PIL import Image, ImageOps


# ============================================================
# IMAGE LOADING
# ============================================================

def load_image(path: Path, cols: int):
    """
    Load the source image and resize it to a dense grid.

    IMPORTANT:
        The RGB values used for the dots come directly from
        the original source image.

    We do NOT recolour the image.
    """

    image = ImageOps.exif_transpose(
        Image.open(path)
    )

    # Work in RGB so every dot gets an actual source colour.
    image = image.convert("RGB")

    source_width, source_height = image.size

    # Preserve the source image aspect ratio.
    rows = max(
        1,
        round(cols * source_height / source_width)
    )

    # High-quality downsampling.
    small = image.resize(
        (cols, rows),
        Image.Resampling.LANCZOS
    )

    pixels = small.load()

    grid = []

    for y in range(rows):

        row = []

        for x in range(cols):

            r, g, b = pixels[x, y]

            # Luminance is used ONLY to determine dot radius.
            #
            # RGB itself is kept untouched.
            luminance = (
                0.2126 * r +
                0.7152 * g +
                0.0722 * b
            ) / 255.0

            row.append(
                {
                    "r": r,
                    "g": g,
                    "b": b,
                    "luminance": luminance,
                }
            )

        grid.append(row)

    return cols, rows, grid


# ============================================================
# DOT GENERATION
# ============================================================

def build_dots(
    cols: int,
    rows: int,
    grid,
    cell: float,
    dot_scale: float,
    seed: int,
    fall_duration: float,
    row_spread: float,
):
    """
    Convert every image cell into a circular dot.

    Dark pixels become very small dots.
    Bright pixels become larger dots.

    The original source RGB colour is retained.
    """

    random.seed(seed)

    max_radius = (
        cell * 0.5 * dot_scale
    )

    dots = []

    for y in range(rows):

        for x in range(cols):

            pixel = grid[y][x]

            luminance = pixel["luminance"]

            r = pixel["r"]
            g = pixel["g"]
            b = pixel["b"]

            # ------------------------------------------------
            # DOT SIZE
            # ------------------------------------------------
            #
            # Bright pixels:
            #     larger circles
            #
            # Dark pixels:
            #     extremely small circles
            #
            # Nothing from the original image is discarded.
            #

           # Dense, fully filled circular dot matrix.
#
# Every cell has a clearly visible dot.
# Brightness still changes the size slightly,
# but dark areas never collapse into tiny specks.

min_radius = cell * 0.34
max_radius = cell * 0.48

radius = (
    min_radius
    + (
        max_radius - min_radius
    )
    * (luminance ** 0.82)
)

            # ------------------------------------------------
            # FINAL POSITION
            # ------------------------------------------------

            cx = (
                x * cell
                + cell / 2
            )

            cy = (
                y * cell
                + cell / 2
            )

            # Very small positional variation.
            # This prevents the pattern from looking like
            # a perfectly rigid computer-generated grid.
            

            # ------------------------------------------------
            # ORIGINAL IMAGE COLOUR
            # ------------------------------------------------

            color = (
                f"#{r:02x}"
                f"{g:02x}"
                f"{b:02x}"
            )

            # ------------------------------------------------
            # FALLING ANIMATION
            # ------------------------------------------------
            #
            # Bottom rows are FIRST.
            #
            # Therefore:
            #
            # bottom -> delay near zero
            # top    -> larger delay
            #

            reverse_y = (
                rows - 1 - y
            )

            vertical_delay = (
                reverse_y
                * row_spread
            )

            random_delay = (
                random.random()
                * row_spread
                * 0.8
            )

            delay = (
                vertical_delay
                + random_delay
            )

            # Slight variation between particles.
            duration = (
                fall_duration
                + random.uniform(
                    -0.12,
                    0.12
                )
            )

            # Every particle begins well above
            # the final portrait.
            fall_distance = (
                rows * cell
                * (
                    0.80
                    + random.random() * 0.45
                )
            )

            dots.append(
                f"""
<circle
    class="dot"
    cx="{cx:.2f}"
    cy="{cy:.2f}"
    r="{radius:.3f}"
    fill="{color}"
    style="
        --fall:{fall_distance:.2f}px;
        --delay:{delay:.3f}s;
        --duration:{duration:.3f}s;
    "
/>
"""
            )

    return "".join(dots)


# ============================================================
# SVG
# ============================================================

def build_svg(
    cols: int,
    rows: int,
    grid,
    cell: float,
    dot_scale: float,
    seed: int,
    fall_duration: float,
    row_spread: float,
):
    """
    Build the final SVG.

    There is intentionally NO background rectangle.

    This means the SVG itself is transparent and the portrait
    can blend into GitHub's dark profile background.
    """

    width = cols * cell
    height = rows * cell

    dots = build_dots(
        cols=cols,
        rows=rows,
        grid=grid,
        cell=cell,
        dot_scale=dot_scale,
        seed=seed,
        fall_duration=fall_duration,
        row_spread=row_spread,
    )

    # --------------------------------------------------------
    # ANIMATION
    # --------------------------------------------------------

    css = """
<style>

.dot {
    opacity: 0;

    transform:
        translateY(
            calc(var(--fall) * -1)
        );

    animation-name:
        matrix-fall;

    animation-duration:
        var(--duration);

    animation-delay:
        var(--delay);

    animation-fill-mode:
        forwards;

    animation-timing-function:
        cubic-bezier(
            0.12,
            0.82,
            0.22,
            1
        );
}


/*
 * FALL → IMPACT → SMALL BOUNCE → SETTLE
 */
@keyframes matrix-fall {

    0% {
        opacity: 0;

        transform:
            translateY(
                calc(var(--fall) * -1)
            );
    }

    12% {
        opacity: 0.10;
    }

    48% {
        opacity: 0.65;
    }

    76% {
        opacity: 0.95;

        transform:
            translateY(6px);
    }

    86% {
        opacity: 1;

        transform:
            translateY(-2px);
    }

    93% {
        transform:
            translateY(1px);
    }

    100% {
        opacity: 1;

        transform:
            translateY(0);
    }
}


/*
 * Respect users who disable animation.
 */
@media (prefers-reduced-motion: reduce) {

    .dot {
        animation: none;
        opacity: 1;
        transform: none;
    }

}

</style>
"""

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # NO BACKGROUND <rect>
    #
    # The surrounding GitHub page supplies the background.
    # --------------------------------------------------------

    svg = f"""<svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 {width:.0f} {height:.0f}"
    width="{width:.0f}"
    height="{height:.0f}"
    role="img"
    aria-label="Ishan Ray Chaudhuri dot matrix portrait"
>

{css}

<g>
{dots}
</g>

</svg>
"""

    return svg


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Generate a high-resolution "
            "coloured dot-matrix portrait."
        )
    )

    parser.add_argument(
        "image",
        type=Path,
        help="source portrait image"
    )

    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        default=Path(
            "assets/portrait.svg"
        ),
        help="output SVG"
    )

    # --------------------------------------------------------
    # IMAGE RESOLUTION
    # --------------------------------------------------------

    parser.add_argument(
        "--cols",
        type=int,
        default=150,
        help="number of circular cells across"
    )

    parser.add_argument(
        "--cell",
        type=float,
        default=6.0,
        help="distance between dot centres"
    )

    parser.add_argument(
        "--dot-scale",
        type=float,
        default=0.90,
        help="maximum dot size"
    )

    # --------------------------------------------------------
    # ANIMATION
    # --------------------------------------------------------

    parser.add_argument(
        "--fall-duration",
        type=float,
        default=1.15,
        help="fall duration"
    )

    parser.add_argument(
        "--row-spread",
        type=float,
        default=0.030,
        help=(
            "delay between successive rows "
            "from bottom to top"
        )
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="deterministic randomness"
    )

    args = parser.parse_args()

    if not args.image.exists():

        sys.exit(
            f"Image not found: {args.image}"
        )

    args.out.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    cols, rows, grid = load_image(
        args.image,
        args.cols
    )

    svg = build_svg(
        cols=cols,
        rows=rows,
        grid=grid,
        cell=args.cell,
        dot_scale=args.dot_scale,
        seed=args.seed,
        fall_duration=args.fall_duration,
        row_spread=args.row_spread,
    )

    args.out.write_text(
        svg,
        encoding="utf-8"
    )

    print(
        f"Generated {args.out}"
        f" ({cols} x {rows} cells)"
    )


if __name__ == "__main__":
    main()
