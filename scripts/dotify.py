#!/usr/bin/env python3
from __future__ import annotations
import argparse, random, sys
from pathlib import Path
from PIL import Image, ImageOps

def load_image(path: Path, cols: int):
    image=ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    w,h=image.size
    rows=max(1,round(cols*h/w))
    small=image.resize((cols,rows),Image.Resampling.LANCZOS)
    px=small.load()
    return cols,rows,[[px[x,y] for x in range(cols)] for y in range(rows)]

def build_svg(cols,rows,pixels,cell,seed,fall_duration,row_spread):
    random.seed(seed)
    dots=[]
    min_r=cell*0.34; max_r=cell*0.48
    for y,row in enumerate(pixels):
        for x,(r,g,b) in enumerate(row):
            lum=(0.2126*r+0.7152*g+0.0722*b)/255
            radius=min_r+(max_r-min_r)*(lum**0.82)
            cx=x*cell+cell/2; cy=y*cell+cell/2
            delay=(rows-1-y)*row_spread+random.random()*row_spread*0.8
            duration=fall_duration+random.uniform(-0.12,0.12)
            fall=rows*cell*(0.80+random.random()*0.45)
            dots.append(f'''<circle class="dot" cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.3f}" fill="#{r:02x}{g:02x}{b:02x}" style="--fall:{fall:.2f}px;--delay:{delay:.3f}s;--duration:{duration:.3f}s;"/>''')
    width=cols*cell; height=rows*cell
    css='''<style>
.dot{opacity:0;transform:translateY(calc(var(--fall) * -1));animation-name:matrix-fall;animation-duration:var(--duration);animation-delay:var(--delay);animation-iteration-count:1;animation-fill-mode:forwards;animation-timing-function:cubic-bezier(.12,.82,.22,1)}
@keyframes matrix-fall{
0%{opacity:0;transform:translateY(calc(var(--fall) * -1))}
12%{opacity:.10}
48%{opacity:.65}
76%{opacity:.95;transform:translateY(6px)}
86%{opacity:1;transform:translateY(-2px)}
93%{transform:translateY(1px)}
100%{opacity:1;transform:translateY(0)}
}
@media (prefers-reduced-motion:reduce){.dot{animation:none;opacity:1;transform:none}}
</style>'''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" width="{width:.0f}" height="{height:.0f}" role="img" aria-label="Ishan Ray Chaudhuri dot matrix portrait">{css}<g>{"".join(dots)}</g></svg>'''

def main():
    p=argparse.ArgumentParser()
    p.add_argument("image",type=Path);p.add_argument("-o","--out",type=Path,default=Path("assets/portrait.svg"))
    p.add_argument("--cols",type=int,default=150);p.add_argument("--cell",type=float,default=6.0)
    p.add_argument("--dot-scale",type=float,default=.90);p.add_argument("--fall-duration",type=float,default=1.15)
    p.add_argument("--row-spread",type=float,default=.030);p.add_argument("--seed",type=int,default=42)
    a=p.parse_args()
    if not a.image.exists():sys.exit(f"Image not found: {a.image}")
    a.out.parent.mkdir(parents=True,exist_ok=True)
    cols,rows,pixels=load_image(a.image,a.cols)
    a.out.write_text(build_svg(cols,rows,pixels,a.cell,a.seed,a.fall_duration,a.row_spread),encoding="utf-8")
    print(f"Generated {a.out} ({cols} x {rows} cells)")

if __name__=="__main__":main()
