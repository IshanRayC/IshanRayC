#!/usr/bin/env python3

from pathlib import Path
import argparse
import random
import sys

from PIL import Image, ImageOps


def load_image(path: Path, cols: int):
    image = ImageOps.exif_transpose(
        Image.open(path)
    ).convert("RGB")

    width, height = image.size

    rows = max(
        1,
        round(cols * height / width)
    )

    image = image.resize(
        (cols, rows),
        Image.Resampling.LANCZOS
    )

    pixels = image.load()

    data = []

    for y in range(rows):
        row = []

        for x in range(cols):

            r, g, b = pixels[x, y]

            # Brightness is used ONLY to determine dot size.
            # The colour remains the ORIGINAL RGB.
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


def generate_svg(
    cols,
    rows,
    data,
    cell,
    dot_scale,
    fall_duration,
    row_delay,
    seed,
):
    random.seed(seed)

    width = cols * cell
    height = rows * cell

    # ----------------------------------------------------------
    # IMPORTANT:
    #
    # Every cell gets a dot.
    #
    # Nothing is removed.
    # No floor.
    # No alpha mask.
    # No background removal.
    # ----------------------------------------------------------

    circles = []

    for y in range(rows):

        for x in range(cols):

            luminance, r, g, b = data[y][x]

            # Dot size is based on brightness,
            # just like a halftone/dot-matrix image.

            min_radius = cell * 0.075
            max_radius = cell * 0.46

            radius = (
                min_radius +
                (max_radius - min_radius)
                * (luminance ** 0.85)
            )

            cx = x * cell + cell / 2
            cy = y * cell + cell / 2

            # ORIGINAL COLOUR.
            color = (
                f"#{r:02x}"
                f"{g:02x}"
                f"{b:02x}"
            )

            # --------------------------------------------------
            # BOTTOM → TOP FALL
            # --------------------------------------------------

            reverse_y = rows - 1 - y

            delay = (
                reverse_y * row_delay
                + random.uniform(
                    0,
                    row_delay * 0.8
                )
            )

            duration = (
                fall_duration
                + random.uniform(
                    -0.10,
                    0.12
                )
            )

            # Start well above the image.
            start_y = -(
                height * (
                    0.75 +
                    random.uniform(0, 0.5)
                )
            )

            circles.append(
                f"""
<circle
    class="dot"
    cx="{cx:.2f}"
    cy="{cy:.2f}"
    r="{radius:.2f}"
    fill="{color}"
    style="
        --start-y:{start_y:.2f}px;
        animation-delay:{delay:.3f}s;
        animation-duration:{duration:.3f}s;
    "
/>
"""
            )

    # ----------------------------------------------------------
    # FALLING DOT ANIMATION
    # ----------------------------------------------------------

    css = """
<style>

.dot {
    opacity: 0;

    transform:
        translateY(var(--start-y));

    animation:
        matrix-fall
        var(--duration)
        cubic-bezier(0.12, 0.82, 0.22, 1)
        forwards;
}

@keyframes matrix-fall {

    0% {
        opacity: 0;

        transform:
            translateY(var(--start-y));
    }

    12% {
        opacity: 0.15;
    }

    55% {
        opacity: 0.75;
    }

    78% {
        opacity: 1;

        transform:
            translateY(6px);
    }

    90% {
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

    # ----------------------------------------------------------
    # NO TRANSPARENCY CHECKERBOARD
    #
    # We deliberately give the SVG the same dark base colour
    # used by the GitHub dark profile environment.
    #
    # The dots still contain the entire source image.
    # ----------------------------------------------------------

    background = """
<rect
    width="100%"
    height="100%"
    fill="#0d1117"
/>
"""

    return f"""
<svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 {width:.0f} {height:.0f}"
    width="{width:.0f}"
    height="{height:.0f}"
    role="img"
    aria-label="Ishan Ray Chaudhuri dot matrix portrait"
>

{css}

{background}

<g>
{''.join(circles)}
</g>

</svg>
"""


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "image",
        type=Path
    )

    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        default=Path(
            "assets/portrait.svg"
        )
    )

    parser.add_argument(
        "--cols",
        type=int,
        default=140
    )

    parser.add_argument(
        "--cell",
        type=float,
        default=7
    )

    parser.add_argument(
        "--dot-scale",
        type=float,
        default=0.92
    )

    parser.add_argument(
        "--fall-duration",
        type=float,
        default=1.10
    )

    parser.add_argument(
        "--row-delay",
        type=float,
        default=0.035
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42
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

    cols, rows, data = load_image(
        args.image,
        args.cols
    )

    svg = generate_svg(
        cols=cols,
        rows=rows,
        data=data,
        cell=args.cell,
        dot_scale=args.dot_scale,
        fall_duration=args.fall_duration,
        row_delay=args.row_delay,
        seed=args.seed,
    )

    args.out.write_text(
        svg,
        encoding="utf-8"
    )

    print(
        f"Generated {args.out}"
        f" ({cols} x {rows})"
    )


if __name__ == "__main__":
    main()
