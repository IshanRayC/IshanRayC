#!/usr/bin/env python3

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

try:
    from PIL import (
        Image,
        ImageChops,
        ImageEnhance,
        ImageFilter,
        ImageOps,
    )
except ImportError:
    sys.exit("Pillow is required: python -m pip install Pillow")


# ============================================================
# IMAGE → GRID
# ============================================================

def load_grid(
    path: Path,
    cols: int,
    contrast: float,
    gamma: float,
    detail: float,
):
    """
    Convert the source image into a dense dot grid.

    IMPORTANT:
    - Source RGB colours are preserved.
    - Alpha is preserved as a subject mask.
    - We only improve the luminance used to determine dot size.
    """

    img = ImageOps.exif_transpose(Image.open(path))

    # Keep the original RGB information.
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    alpha = img.getchannel("A")

    # Flatten only for luminance calculation.
    # The actual dot colours still come from the original image.
    black = Image.new("RGBA", img.size, (0, 0, 0, 255))
    flattened = Image.alpha_composite(black, img).convert("RGB")

    gray = flattened.convert("L")

    # Improve facial/detail contrast WITHOUT changing
    # the colours that will be used by the dots.
    gray = ImageEnhance.Contrast(gray).enhance(contrast)

    if detail > 0:
        radius = max(1, round(min(img.size) / 70))

        gray = gray.filter(
            ImageFilter.UnsharpMask(
                radius=radius,
                percent=round(detail * 100),
                threshold=1,
            )
        )

    width, height = img.size

    # Maintain aspect ratio.
    rows = max(
        1,
        round(cols * (height / width)),
    )

    small_gray = gray.resize(
        (cols, rows),
        Image.Resampling.LANCZOS,
    )

    small_alpha = alpha.resize(
        (cols, rows),
        Image.Resampling.LANCZOS,
    )

    small_color = img.resize(
        (cols, rows),
        Image.Resampling.LANCZOS,
    )

    gp = small_gray.load()
    ap = small_alpha.load()
    cp = small_color.load()

    luminance = []
    colors = []

    for y in range(rows):

        lum_row = []
        color_row = []

        for x in range(cols):

            v = gp[x, y] / 255.0

            # Alpha controls whether the dot exists.
            v *= ap[x, y] / 255.0

            # Gamma controls detail in darker regions.
            v = max(0.0, min(1.0, v ** gamma))

            lum_row.append(v)

            # Preserve ORIGINAL colour.
            r, g, b, _ = cp[x, y]
            color_row.append((r, g, b))

        luminance.append(lum_row)
        colors.append(color_row)

    return cols, rows, luminance, colors


# ============================================================
# SVG
# ============================================================

def build_svg(
    cols: int,
    rows: int,
    luminance,
    colors,
    cell: float,
    dot_scale: float,
    floor: float,
    fall_duration: float,
    spread: float,
    seed: int,
):
    """
    Create a transparent SVG dot portrait.

    Every visible dot:
      1. starts above the portrait,
      2. falls downward,
      3. slightly overshoots,
      4. settles into its final position.

    The dots retain the source image's original colours.
    """

    random.seed(seed)

    width = cols * cell
    height = rows * cell

    max_radius = cell * 0.5 * dot_scale

    circles = []

    for y in range(rows):

        for x in range(cols):

            value = luminance[y][x]

            # Remove almost-black / transparent background cells.
            if value < floor:
                continue

            # Same basic idea as Gargi's dots mode:
            # brighter pixel = larger circle.
            radius = max_radius * (value ** 0.85)

            if radius < 0.20:
                continue

            cx = x * cell + cell / 2
            cy = y * cell + cell / 2

            r, g, b = colors[y][x]

            fill = f"#{r:02x}{g:02x}{b:02x}"

            # ------------------------------------------------
            # MATRIX-STYLE FALL
            # ------------------------------------------------

            # Every dot starts above the visible canvas.
            start_y = -(
                height
                * (0.35 + random.random() * 0.75)
            )

            # Columns begin at slightly different times,
            # producing a falling-rain / Matrix-like flow.
            column_delay = (
                x / max(cols - 1, 1)
            ) * spread * 0.45

            # Random stagger prevents a rigid synchronized wave.
            random_delay = random.uniform(
                0,
                spread * 0.65,
            )

            # Small vertical influence.
            vertical_delay = (
                y / max(rows - 1, 1)
            ) * spread * 0.20

            delay = (
                column_delay
                + random_delay
                + vertical_delay
            )

            duration = (
                fall_duration
                + random.uniform(-0.12, 0.18)
            )

            circles.append(
                f'''
<circle
    class="dot"
    cx="{cx:.2f}"
    cy="{cy:.2f}"
    r="{radius:.2f}"
    fill="{fill}"
    style="
        --start-y:{start_y:.2f}px;
        animation-delay:{delay:.3f}s;
        animation-duration:{duration:.3f}s;
    "
/>
'''
            )

    # --------------------------------------------------------
    # ANIMATION
    # --------------------------------------------------------

    css = """
<style>

.dot {
    opacity: 0;
    transform: translateY(var(--start-y));

    animation-name: matrix-drop;
    animation-fill-mode: forwards;

    /*
     * Fast start, smooth landing.
     * This gives the "fall → settle" feeling.
     */
    animation-timing-function:
        cubic-bezier(0.18, 0.86, 0.24, 1);
}

@keyframes matrix-drop {

    /* invisible above the portrait */
    0% {
        opacity: 0;
        transform: translateY(var(--start-y));
    }

    /* particle appears while falling */
    12% {
        opacity: 0.25;
    }

    /* falling toward its final position */
    60% {
        opacity: 0.80;
    }

    /* slight overshoot */
    82% {
        opacity: 1;
        transform: translateY(7px);
    }

    /* bounce back */
    91% {
        transform: translateY(-2px);
    }

    /* settle */
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

    # --------------------------------------------------------
    # NO BACKGROUND RECTANGLE
    # --------------------------------------------------------
    #
    # This is deliberate.
    #
    # The SVG is transparent.
    # GitHub supplies the surrounding profile background.
    #

    svg_start = f'''
<svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 {width:.0f} {height:.0f}"
    width="{width:.0f}"
    height="{height:.0f}"
    role="img"
    aria-label="Ishan Ray Chaudhuri dot matrix portrait"
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
# COMMAND LINE
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description="Generate a high-resolution coloured dot-matrix portrait."
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

    # Dense grid.
    parser.add_argument(
        "--cols",
        type=int,
        default=170,
    )

    # Physical spacing between circles.
    parser.add_argument(
        "--cell",
        type=float,
        default=5.0,
    )

    # Dot size.
    parser.add_argument(
        "--dot-scale",
        type=float,
        default=0.84,
    )

    parser.add_argument(
        "--contrast",
        type=float,
        default=1.35,
    )

    parser.add_argument(
        "--gamma",
        type=float,
        default=0.90,
    )

    parser.add_argument(
        "--detail",
        type=float,
        default=0.75,
    )

    parser.add_argument(
        "--floor",
        type=float,
        default=0.045,
    )

    # Animation.
    parser.add_argument(
        "--fall-duration",
        type=float,
        default=1.15,
    )

    parser.add_argument(
        "--spread",
        type=float,
        default=2.8,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    args = parser.parse_args()

    if not args.image.exists():
        sys.exit(
            f"Image not found: {args.image}"
        )

    args.out.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cols, rows, luminance, colors = load_grid(
        args.image,
        args.cols,
        args.contrast,
        args.gamma,
        args.detail,
    )

    svg = build_svg(
        cols=cols,
        rows=rows,
        luminance=luminance,
        colors=colors,
        cell=args.cell,
        dot_scale=args.dot_scale,
        floor=args.floor,
        fall_duration=args.fall_duration,
        spread=args.spread,
        seed=args.seed,
    )

    args.out.write_text(
        svg,
        encoding="utf-8",
    )

    print(
        f"Generated {args.out} "
        f"({cols} x {rows} cells)"
    )


if __name__ == "__main__":
    main()
