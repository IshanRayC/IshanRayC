#!/usr/bin/env python3

from __future__ import annotations

import argparse
import math
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


def load_grid(
    path: Path,
    cols: int,
    contrast: float,
    gamma: float,
    equalize: bool,
    detail: float,
):
    img = ImageOps.exif_transpose(Image.open(path))

    mask = None

    # Preserve alpha if the source has it.
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")

        if img.getchannel("A").getextrema()[0] < 250:
            mask = img.getchannel("A")

        flat = Image.new(
            "RGBA",
            img.size,
            (0, 0, 0, 255),
        )

        flat.alpha_composite(img)
        img = flat

    img = img.convert("RGB")

    gray = img.convert("L")

    # Exactly the kind of processing Gargi uses:
    # improve tonal separation while preserving source colours.
    if equalize:
        gray = ImageOps.equalize(
            gray,
            mask=(
                mask.point(
                    lambda v: 255 if v > 127 else 0
                )
                if mask
                else None
            ),
        )

    if detail > 0:
        radius = max(
            2,
            round(min(img.size) / 52),
        )

        gray = gray.filter(
            ImageFilter.UnsharpMask(
                radius=radius,
                percent=round(detail * 100),
                threshold=0,
            )
        )

    if contrast != 1.0:
        gray = ImageEnhance.Contrast(
            gray
        ).enhance(contrast)

    width, height = img.size

    rows = max(
        1,
        round(cols * (height / width)),
    )

    small_g = gray.resize(
        (cols, rows),
        Image.Resampling.LANCZOS,
    )

    if mask is not None:
        small_m = mask.resize(
            (cols, rows),
            Image.Resampling.LANCZOS,
        )

        small_g = ImageChops.multiply(
            small_g,
            small_m,
        )

    small_c = img.resize(
        (cols, rows),
        Image.Resampling.LANCZOS,
    )

    gp = small_g.load()
    cp = small_c.load()

    rgb = []
    lum = []

    for y in range(rows):

        rgb_row = []
        lum_row = []

        for x in range(cols):

            rgb_row.append(cp[x, y])

            value = gp[x, y] / 255.0

            value = min(
                1.0,
                max(
                    0.0,
                    value ** gamma,
                ),
            )

            lum_row.append(value)

        rgb.append(rgb_row)
        lum.append(lum_row)

    return cols, rows, lum, rgb


def build_dots(
    cols,
    rows,
    lum,
    rgb,
    cell,
    dot_scale,
    floor,
    fall_duration,
    row_delay,
    seed,
):
    random.seed(seed)

    max_r = cell * 0.5 * dot_scale

    output = []

    for y in range(rows):

        row = []

        for x in range(cols):

            v = lum[y][x]

            # THIS is what prevents the background from becoming
            # a giant field of dots.
            if v < floor:
                continue

            r = max_r * (v ** 0.85)

            if r < 0.18:
                continue

            cx = x * cell + cell / 2
            cy = y * cell + cell / 2

            # ORIGINAL SOURCE COLOUR.
            cr, cg, cb = rgb[y][x]

            fill = (
                f"#{cr:02x}"
                f"{cg:02x}"
                f"{cb:02x}"
            )

            # --------------------------------------------------
            # BOTTOM -> TOP REVEAL
            # --------------------------------------------------

            reverse_y = rows - 1 - y

            delay = (
                reverse_y * row_delay
                + random.uniform(0, row_delay * 0.75)
            )

            duration = (
                fall_duration
                + random.uniform(-0.12, 0.12)
            )

            # Each dot starts above the final position.
            fall_distance = (
                rows * cell * (
                    0.65 +
                    random.uniform(0.0, 0.35)
                )
            )

            row.append(
                f"""
<circle
    class="dot"
    cx="{cx:.2f}"
    cy="{cy:.2f}"
    r="{r:.2f}"
    fill="{fill}"
    style="
        --fall:{fall_distance:.2f}px;
        animation-delay:{delay:.3f}s;
        animation-duration:{duration:.3f}s;
    "
/>
"""
            )

        output.append("".join(row))

    return "".join(output)


def build_svg(
    cols,
    rows,
    lum,
    rgb,
    cell,
    dot_scale,
    floor,
    fall_duration,
    row_delay,
    seed,
):
    width = cols * cell
    height = rows * cell

    dots = build_dots(
        cols,
        rows,
        lum,
        rgb,
        cell,
        dot_scale,
        floor,
        fall_duration,
        row_delay,
        seed,
    )

    css = """
<style>

.dot {
    opacity: 0;

    transform:
        translateY(calc(var(--fall) * -1));

    animation-name: dot-fall;

    animation-fill-mode: forwards;

    animation-timing-function:
        cubic-bezier(
            0.12,
            0.82,
            0.22,
            1
        );
}

@keyframes dot-fall {

    0% {
        opacity: 0;
        transform:
            translateY(calc(var(--fall) * -1));
    }

    15% {
        opacity: 0.25;
    }

    65% {
        opacity: 0.85;
    }

    82% {
        opacity: 1;
        transform:
            translateY(5px);
    }

    92% {
        transform:
            translateY(-2px);
    }

    100% {
        opacity: 1;
        transform:
            translateY(0);
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

    # IMPORTANT:
    # NO rect.
    # NO white background.
    # NO black background.
    #
    # The SVG is transparent.

    return f"""<svg
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

    # Higher than Gargi's default 88/100,
    # but still reasonable for GitHub.
    parser.add_argument(
        "--cols",
        type=int,
        default=140,
    )

    # Same visual idea as her circular dot cells.
    parser.add_argument(
        "--cell",
        type=float,
        default=7.0,
    )

    parser.add_argument(
        "--dot-scale",
        type=float,
        default=0.92,
    )

    parser.add_argument(
        "--gamma",
        type=float,
        default=1.0,
    )

    parser.add_argument(
        "--contrast",
        type=float,
        default=1.25,
    )

    parser.add_argument(
        "--equalize",
        action="store_true",
    )

    parser.add_argument(
        "--detail",
        type=float,
        default=0.5,
    )

    # Same fundamental concept as Gargi:
    # don't draw insignificant background pixels.
    parser.add_argument(
        "--floor",
        type=float,
        default=0.06,
    )

    parser.add_argument(
        "--fall-duration",
        type=float,
        default=1.15,
    )

    parser.add_argument(
        "--row-delay",
        type=float,
        default=0.035,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    args = parser.parse_args()

    if not args.image.exists():
        sys.exit(
            f"no such image: {args.image}"
        )

    args.out.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cols, rows, lum, rgb = load_grid(
        args.image,
        args.cols,
        args.contrast,
        args.gamma,
        args.equalize,
        args.detail,
    )

    svg = build_svg(
        cols,
        rows,
        lum,
        rgb,
        args.cell,
        args.dot_scale,
        args.floor,
        args.fall_duration,
        args.row_delay,
        args.seed,
    )

    args.out.write_text(
        svg,
        encoding="utf-8",
    )

    print(
        f"wrote {args.out} "
        f"({cols}x{rows} cells)"
    )


if __name__ == "__main__":
    main()
