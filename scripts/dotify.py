#!/usr/bin/env python3

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is required: python -m pip install Pillow")


def load_image(path: Path, cols: int):
    """
    Convert the source image into a dense grid.

    IMPORTANT:
    - No color correction.
    - No contrast adjustment.
    - No equalization.
    - No background removal.
    - No brightness floor.
    - Original image colors are preserved.
    """

    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")

    width, height = img.size

    # Preserve the source aspect ratio.
    rows = max(1, round(cols * height / width))

    small = img.resize(
        (cols, rows),
        Image.Resampling.LANCZOS,
    )

    pixels = small.load()

    data = []

    for y in range(rows):
        row = []

        for x in range(cols):
            r, g, b = pixels[x, y]

            # Only use luminance to decide how large the dot is.
            # The actual colour remains the original RGB value.
            luminance = (
                0.2126 * r +
                0.7152 * g +
                0.0722 * b
            ) / 255.0

            row.append(
                (luminance, r, g, b)
            )

        data.append(row)

    return cols, rows, data


def build_svg(
    cols: int,
    rows: int,
    data,
    cell: float,
    dot_scale: float,
    seed: int,
    fall_duration: float,
    row_spread: float,
):
    random.seed(seed)

    width = cols * cell
    height = rows * cell

    circles = []

    for y in range(rows):

        for x in range(cols):

            luminance, r, g, b = data[y][x]

            # --------------------------------------------------
            # DOT SIZE
            # --------------------------------------------------
            #
            # IMPORTANT:
            # Every pixel gets a dot.
            #
            # Dark pixels are NOT deleted.
            #
            # That preserves the complete picture, including
            # the dark jacket, hair, shadows and blue background.
            #

            min_radius = cell * 0.13
            max_radius = cell * 0.47

            radius = (
                min_radius +
                (max_radius - min_radius)
                * (luminance ** 0.72)
            )

            cx = x * cell + cell / 2
            cy = y * cell + cell / 2

            # Tiny spacing variation, similar to a physical
            # dot-matrix / halftone surface.
            cx += random.uniform(-0.04, 0.04) * cell
            cy += random.uniform(-0.04, 0.04) * cell

            # --------------------------------------------------
            # ORIGINAL COLOUR
            # --------------------------------------------------

            fill = f"#{r:02x}{g:02x}{b:02x}"

            # --------------------------------------------------
            # FALLING ANIMATION
            # --------------------------------------------------
            #
            # BOTTOM ROWS MUST FINISH FIRST.
            #
            # So:
            #
            # bottom -> small delay
            # top    -> large delay
            #

            reverse_y = rows - 1 - y

            base_delay = (
                reverse_y / max(rows - 1, 1)
            ) * row_spread

            # Small randomness stops every dot from moving
            # in a perfectly rigid horizontal line.
            random_delay = random.uniform(
                0.0,
                0.22,
            )

            delay = base_delay + random_delay

            duration = (
                fall_duration +
                random.uniform(-0.10, 0.12)
            )

            # Every dot begins ABOVE the canvas.
            #
            # The distance varies slightly so the animation
            # looks like independent falling particles.
            start_y = -(
                height * (
                    0.65 +
                    random.uniform(0.0, 0.45)
                )
            )

            circles.append(
                f"""
<circle
    class="dot"
    cx="{cx:.2f}"
    cy="{cy:.2f}"
    r="{radius:.2f}"
    fill="{fill}"
    style="
        --start-y: {start_y:.2f}px;
        animation-delay: {delay:.3f}s;
        animation-duration: {duration:.3f}s;
    "
/>
"""
            )

    # ----------------------------------------------------------
    # MATRIX-LIKE FALL
    # ----------------------------------------------------------

    css = """
<style>

.dot {
    opacity: 0;
    transform: translateY(var(--start-y));

    animation-name: falling-dots;

    animation-fill-mode: forwards;

    /*
     * Fast falling motion followed by a smooth landing.
     */
    animation-timing-function:
        cubic-bezier(0.12, 0.82, 0.22, 1);
}

@keyframes falling-dots {

    /*
     * Particle begins far above the portrait.
     */
    0% {
        opacity: 0;
        transform: translateY(var(--start-y));
    }

    /*
     * Becomes visible while falling.
     */
    12% {
        opacity: 0.18;
    }

    55% {
        opacity: 0.68;
    }

    /*
     * Slight overshoot.
     */
    78% {
        opacity: 1;
        transform: translateY(7px);
    }

    88% {
        transform: translateY(-2px);
    }

    /*
     * Final position.
     */
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

    # ----------------------------------------------------------
    # TRANSPARENT SVG
    # ----------------------------------------------------------
    #
    # NO <rect>
    # NO white background
    # NO black background
    #

    svg_start = f"""
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
"""

    svg_end = """
</g>
</svg>
"""

    return svg_start + "".join(circles) + svg_end


def main():

    parser = argparse.ArgumentParser()

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
        default=220,
    )

    parser.add_argument(
        "--cell",
        type=float,
        default=4.5,
    )

    parser.add_argument(
        "--dot-scale",
        type=float,
        default=0.92,
    )

    parser.add_argument(
        "--fall-duration",
        type=float,
        default=1.10,
    )

    parser.add_argument(
        "--row-spread",
        type=float,
        default=3.20,
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

    cols, rows, data = load_image(
        args.image,
        args.cols,
    )

    svg = build_svg(
        cols=cols,
        rows=rows,
        data=data,
        cell=args.cell,
        dot_scale=args.dot_scale,
        seed=args.seed,
        fall_duration=args.fall_duration,
        row_spread=args.row_spread,
    )

    args.out.write_text(
        svg,
        encoding="utf-8",
    )

    print(
        f"Generated {args.out}"
        f" ({cols} x {rows})"
    )


if __name__ == "__main__":
    main()
