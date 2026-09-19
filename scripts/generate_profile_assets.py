#!/usr/bin/env python3
from __future__ import annotations
import base64,html,io,json,math,os,re,subprocess,urllib.parse,urllib.request,zipfile
from collections import Counter
from datetime import date,timedelta
from pathlib import Path
USER="IshanRayC"; ROOT=Path(__file__).resolve().parents[1]; A=ROOT/"assets"  # IS monogram is sourced from assets/is-monogram.png; embed for profile branding
CYAN="#22D3EE";TEAL="#06B6D4";BLUE="#0EA5E9"
DARK=("#070B10","#0B1118","#12313B","#F8FAFC","#94A3B8"); LIGHT=("#F5FAFC","#FFFFFF","#B8DCE4","#0F172A","#64748B")
def rest(path,token):
 req=urllib.request.Request("https://api.github.com"+path,headers={"Accept":"application/vnd.github+json","Authorization":f"Bearer {token}","User-Agent":"IshanRayC-profile"})
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
def gql(q,token):
 data=json.dumps({"query":q}).encode();req=urllib.request.Request("https://api.github.com/graphql",data=data,headers={"Accept":"application/vnd.github+json","Authorization":f"Bearer {token}","Content-Type":"application/json","User-Agent":"IshanRayC-profile"})
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)["data"]
def esc(x):return html.escape(str(x or ""),quote=True)
def count(q,token,kind):
 try:return int(rest(f"/search/{kind}?q={urllib.parse.quote(q)}&per_page=1",token)["total_count"])
 except:return 0
def collect(token):
 u=rest(f"/users/{USER}",token);rs=[r for r in rest(f"/users/{USER}/repos?per_page=100&type=owner&sort=pushed",token) if not r.get("fork")]
 langs=Counter()
 for r in rs:
  try:langs.update({k:int(v) for k,v in rest(f"/repos/{r['full_name']}/languages",token).items()})
  except:pass
 q=f'''query {{ user(login:"{USER}") {{ contributionsCollection {{ contributionCalendar {{ totalContributions weeks {{ contributionDays {{ date contributionCount }} }} }} }} }} }}'''
 cal=gql(q,token)["user"]["contributionsCollection"]["contributionCalendar"]
 days={d["date"]:d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]}
 return {"repos":len(rs),"stars":sum(r.get("stargazers_count",0) for r in rs),"followers":u.get("followers",0),"commits":count(f"author:{USER}",token,"commits"),"prs":count(f"author:{USER} is:pr",token,"issues"),"issues":count(f"author:{USER} is:issue",token,"issues"),"langs":langs,"days":days,"total":cal["totalContributions"],"repo_data":rs}
def streak(days):
 active={date.fromisoformat(d) for d,v in days.items() if v};today=date.today();anchor=today if today in active else today-timedelta(days=1) if today-timedelta(days=1) in active else None;cur=0
 if anchor:
  cur=1
  while anchor-timedelta(days=cur) in active:cur+=1
 longest=run=0;prev=None
 for d in sorted(active):
  run=run+1 if prev and d==prev+timedelta(days=1) else 1;longest=max(longest,run);prev=d
 return len(active),cur,longest

def read_portrait():
    path = A / "portrait.svg"
    if not path.exists():
        return "", "0 0 1000 1000"
    raw = path.read_text(encoding="utf-8")
    m = re.search(r'<svg\b[^>]*\bviewBox=["\']([^"\']+)["\']', raw, re.I)
    vb = m.group(1) if m else "0 0 1000 1000"
    body = re.search(r"<svg\b[^>]*>(.*)</svg>\s*$", raw, re.I | re.S)
    return (body.group(1) if body else raw), vb

def read_logo_data():
    path = A / "is-monogram.png"
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("ascii")


def pro_racing_95_svg(fill="#F0FDFF", target_height=15, center_x=1080, baseline_y=71.5):
    """Return actual Pro Racing Slant 95 glyph outlines as inline SVG paths."""
    try:
        from fontTools.ttLib import TTFont
        from fontTools.pens.svgPathPen import SVGPathPen
        from fontTools.pens.boundsPen import BoundsPen
    except ImportError:
        subprocess.run(["python3", "-m", "pip", "install", "--quiet", "fonttools"], check=True)
        from fontTools.ttLib import TTFont
        from fontTools.pens.svgPathPen import SVGPathPen
        from fontTools.pens.boundsPen import BoundsPen

    url = "https://dl.dafont.com/dl/?f=pro_racing"
    req = urllib.request.Request(url, headers={"User-Agent": "IshanRayC-profile"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        font_name = next((n for n in names if n.lower().endswith("pro racing slant.otf".lower())), None)
        if not font_name:
            raise RuntimeError("Pro Racing Slant.otf not found in downloaded archive")
        font_bytes = z.read(font_name)

    font = TTFont(io.BytesIO(font_bytes))
    upm = float(font["head"].unitsPerEm)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"].metrics

    glyphs = []
    max_height = 1.0
    total_advance = 0.0
    for ch in "95":
        gname = cmap.get(ord(ch))
        if not gname:
            raise RuntimeError(f"Missing glyph for {ch}")
        pen = SVGPathPen(glyph_set)
        glyph_set[gname].draw(pen)
        bounds_pen = BoundsPen(glyph_set)
        glyph_set[gname].draw(bounds_pen)
        bounds = bounds_pen.bounds
        if not bounds:
            raise RuntimeError(f"Empty glyph for {ch}")
        x0, y0, x1, y1 = bounds
        max_height = max(max_height, float(y1 - y0))
        advance = float(hmtx[gname][0])
        glyphs.append((pen.getCommands(), advance, x0, y0, x1, y1))
        total_advance += advance

    scale = float(target_height) / max_height
    start_x = float(center_x) - (total_advance * scale / 2.0)
    parts = [f'<g transform="translate({start_x:.3f} {baseline_y:.3f}) scale({scale:.6f} {-scale:.6f})" fill="{fill}" fill-rule="nonzero">']
    advance_x = 0.0
    for path_d, advance, *_ in glyphs:
        parts.append(f'<path d="{path_d}" transform="translate({advance_x:.3f} 0)"/>')
        advance_x += advance
    parts.append('</g>')
    return "".join(parts)

def hero(theme):
    bg, panel, stroke, text, muted = DARK if theme == "dark" else LIGHT
    body, vb = read_portrait()
    logo_data = read_logo_data()
    # Logo and 95 sit directly on the single rounded header — no separate boxes,
    # no outlines, and no divider strokes.
    logo_img = f'<image href="data:image/png;base64,{logo_data}" x="960" y="47" width="32" height="34" preserveAspectRatio="xMidYMid meet"/>' if logo_data else ""
    if theme == "dark":
        shell, label, dotted, visual, value = "#0D1016", "#67E8F9", "#16343E", "#06080B", "#F8FAFC"
    else:
        shell, label, dotted, visual, value = "#FFFFFF", "#0E7490", "#D6EAF0", "#050608", "#0F172A"

    portrait_vb = vb
    try:
        vx, vy, vw, vh = [float(v) for v in vb.split()]
        crop_top = min(80.0, vh * 0.071)
        crop_bottom = min(80.0, vh * 0.071)
        portrait_vb = f"{vx:.2f} {vy + crop_top:.2f} {vw:.2f} {vh - crop_top - crop_bottom:.2f}"
    except Exception:
        portrait_vb = vb
    portrait = f'<svg x="52" y="130" width="420" height="420" viewBox="{esc(portrait_vb)}" preserveAspectRatio="xMidYMid meet" overflow="hidden">{body}</svg>'
    rows = [
        ("Subject","ISHAN RAY CHAUDHURI"),("Role","CSE AND DATA SCIENCE STUDENT"),
        ("Origin","CHENNAI, INDIA"),("Education","BTECH CSE · VIT CHENNAI"),
        ("","BS DATA SCIENCE · IIT MADRAS"),("Status","LEARNING + BUILDING + SHIPPING"),
        ("Core.Lang","C · C++ · PYTHON · JAVA · R"),("Core.Data","NUMPY · PANDAS · MATLAB"),
        ("Core.Infra","DOCKER · WSL · CLOUD · DEVOPS")
    ]

    p = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="610"
viewBox="0 0 1180 610" role="img" aria-label="Ishan Ray Chaudhuri system profile">
<defs>
  <clipPath id="v"><rect x="52" y="130" width="420" height="420" rx="14"/></clipPath>
  <linearGradient id="headerGradient" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#062A35"/>
    <stop offset=".18" stop-color="#0B596A"/>
    <stop offset=".50" stop-color="#0E8AA3"/>
    <stop offset=".82" stop-color="#0B596A"/>
    <stop offset="1" stop-color="#062A35"/>
  </linearGradient>
  <linearGradient id="labsText" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#ECFEFF"/>
    <stop offset="1" stop-color="#A5F3FC"/>
  </linearGradient>
  <clipPath id="headerClip">
    <rect x="42" y="42" width="1100" height="44" rx="12"/>
  </clipPath>
</defs>

<rect width="1180" height="610" rx="18" fill="{bg}"/>
<rect x="18" y="18" width="1144" height="574" rx="16" fill="{shell}" stroke="{stroke}"/>

<!-- ONE rounded header: logo + 95 are directly on it -->
<rect x="42" y="42" width="1100" height="44" rx="12" fill="url(#headerGradient)"/>
<circle cx="66" cy="64" r="6" fill="#ECFEFF"/>
<circle cx="86" cy="64" r="6" fill="#ECFEFF"/>
<circle cx="106" cy="64" r="6" fill="#ECFEFF"/>
<text x="134" y="70" fill="url(#labsText)" font-size="14" font-weight="700"
      letter-spacing=".7" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">ISHAN LABS</text>
{logo_img}
{pro_racing_95_svg()}

<text x="60" y="116" fill="{label}" font-size="13" font-family="ui-monospace,monospace">VISUAL.MAP</text>
<text x="504" y="116" fill="{label}" font-size="13" font-family="ui-monospace,monospace">SYSTEM.INFO</text>
<rect x="52" y="130" width="420" height="420" rx="14" fill="{visual}" stroke="{CYAN}" stroke-width="2"/>
<g clip-path="url(#v)">{portrait}</g>
<g font-size="14" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">''']

    y = 154
    for k, v in rows:
        p.append(f'<text x="522" y="{y}" fill="{muted}">{esc(k)}</text>' if k else f'<text x="522" y="{y}" fill="{muted}"> </text>')
        p.append(f'<path d="M610 {y-4} H900" stroke="{dotted}" stroke-dasharray="2 6"/><text x="930" y="{y}" fill="{value}" text-anchor="end">{esc(v)}</text>')
        y += 23

    p.append(f'''</g>
<rect x="522" y="378" width="408" height="34" rx="17" fill="{CYAN}" fill-opacity=".10" stroke="{CYAN}" stroke-opacity=".75"/>
<text x="726" y="400" fill="{CYAN}" font-size="14" text-anchor="middle" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">@IshanRayC</text>
<text x="522" y="448" fill="{CYAN}" font-size="13" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">TARGET</text>
<text x="522" y="472" fill="{value}" font-size="15" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">SOFTWARE · AI/ML · CLOUD · DEVOPS · QUANT · HFT</text>
<text x="522" y="496" fill="{value}" font-size="15" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">AUTOMATION · SYSTEM DESIGNS</text>
</svg>''')
    return "".join(p)

def signature(theme):
    bg = "#FFFFFF" if theme == "light" else "#0D1016"
    stroke = "#B8DCE4" if theme == "light" else "#12313B"
    logo_data = read_logo_data()
    logo_img = f'<rect x="12" y="9" width="132" height="54" rx="8" fill="#0B1118"/><image href="data:image/png;base64,{logo_data}" x="18" y="14" width="30" height="44" preserveAspectRatio="xMidYMid meet"/>{pro_racing_95_svg(target_height=25, center_x=94.60, baseline_y=48.50)}' if logo_data else pro_racing_95_svg(target_height=25, center_x=94.60, baseline_y=48.50)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="72" viewBox="0 0 1040 72" role="img" aria-label="Ishan signature stripe">
<rect x="1" y="1" width="1038" height="70" rx="8" fill="{bg}" stroke="{CYAN}" stroke-width="2"/>
{logo_img}
<rect x="156" y="10" width="1" height="52" fill="{stroke}"/>
<text x="184" y="44" fill="{CYAN}" font-size="20" font-weight="700" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">BUILD • BREAK • DEBUG • LEARN • DEPLOY</text>
</svg>'''

def snake_body():
    url = "https://raw.githubusercontent.com/IshanRayC/IshanRayC/gh-pages/github-contribution-snake.svg"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "IshanRayC-profile", "Accept": "image/svg+xml,text/plain,*/*"},
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode("utf-8")
        raw = raw.replace("--ce:#071A2F", "--ce:#343942").replace("--ce:#071a2f", "--ce:#343942")
        m = re.search(r"<svg\b[^>]*>(.*)</svg>\s*$", raw, re.I | re.S)
        return m.group(1) if m else ""
    except Exception:
        return ""


def activity(d, theme):
    bg, panel, stroke, text, muted = DARK if theme == "dark" else LIGHT
    active, cur, longest = streak(d["days"])

    if theme == "dark":
        frame = "#06080B"
        card = "#111116"
        card_border = "#12313B"
        divider = "#155E75"
        primary = CYAN
        secondary = "#67E8F9"
        sub = "#94A3B8"
        snake_default = "#071A2F"
    else:
        frame = "#F6FAFC"
        card = "#FFFFFF"
        card_border = "#B8DCE4"
        divider = "#8CCAD8"
        primary = "#0891B2"
        secondary = "#0E7490"
        sub = "#64748B"
        snake_default = "#D9EEF2"

    # This mirrors the reference profile's activity composition:
    # one large outer frame, 3 streak columns, 2 statistic cards,
    # then the full contribution snake across the bottom.
    p = [
        f'''<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="670"
viewBox="0 0 1180 670" role="img"
aria-label="GitHub activity, stats, languages and contribution snake">
<defs>
  <clipPath id="activityFrame"><rect x="1" y="1" width="1178" height="668" rx="16"/></clipPath>
  <mask id="streakMask"><rect x="0" y="0" width="1180" height="195" fill="white"/><ellipse cx="590" cy="32" rx="13" ry="18" fill="black"/></mask>
</defs>
<rect x="1" y="1" width="1178" height="668" rx="16"
      fill="{frame}" stroke="{card_border}" stroke-width="2"/>
<g clip-path="url(#activityFrame)">
  <rect x="16" y="16" width="1148" height="178" rx="12"
        fill="{card}" stroke="{card_border}"/>
  <line x1="393.33" y1="44" x2="393.33" y2="170" stroke="{divider}"/>
  <line x1="786.67" y1="44" x2="786.67" y2="170" stroke="{divider}"/>

  <!-- ACTIVE DAYS -->
  <g transform="translate(196.67 34) scale(0.78)">
    <ellipse cx="0" cy="29" rx="25" ry="4" fill="#000000" opacity="0.12"/>
    <rect x="-28" y="-18" width="56" height="48" rx="7" fill="{primary}"/>
    <rect x="-28" y="-18" width="56" height="16" rx="7" fill="{primary}"/>
    <rect x="-28" y="-10" width="56" height="8" fill="{primary}"/>
    <rect x="-23" y="-1" width="46" height="26" rx="3" fill="{card}"/>
    <g fill="none" stroke="{primary}" stroke-width="1.7">
      <path d="M-12 -6 V-20"/><path d="M0 -6 V-20"/><path d="M12 -6 V-20"/>
    </g>
    <g fill="{primary}">
      <circle cx="-19" cy="5" r="1.7"/><circle cx="-7" cy="5" r="1.7"/><circle cx="5" cy="5" r="1.7"/><circle cx="17" cy="5" r="1.7"/>
      <circle cx="-19" cy="14" r="1.7"/><circle cx="-7" cy="14" r="1.7"/><circle cx="5" cy="14" r="1.7"/><circle cx="17" cy="14" r="1.7"/>
    </g>
    <g fill="{card}">
      <circle cx="-12" cy="-18" r="5"/><circle cx="0" cy="-18" r="5"/><circle cx="12" cy="-18" r="5"/>
    </g>
    <g fill="{primary}">
      <circle cx="-12" cy="-18" r="2"/><circle cx="0" cy="-18" r="2"/><circle cx="12" cy="-18" r="2"/>
    </g>
  </g>
  <text x="196.67" y="94" text-anchor="middle" fill="{primary}" font-family="Segoe UI,Ubuntu,sans-serif" font-size="34.5" font-weight="700">{active}</text>
  <text x="196.67" y="124" text-anchor="middle" fill="{primary}" font-family="Segoe UI,Ubuntu,sans-serif" font-size="16.1" font-weight="700">Active Days</text>
  <text x="196.67" y="148" text-anchor="middle" fill="{sub}" font-family="Segoe UI,Ubuntu,sans-serif" font-size="13.8">last 400 days</text>
  <rect x="172" y="158" width="49" height="4" rx="2" fill="{primary}"/>

  <!-- CURRENT STREAK -->
  <g mask="url(#streakMask)">
    <circle cx="590" cy="71" r="40" fill="none" stroke="{primary}" stroke-width="5"/>
  </g>
  <g transform="translate(590 19.5)" stroke-opacity="0">
    <path d="M 1.5 0.67 C 1.5 0.67 2.24 3.32 2.24 5.47 C 2.24 7.53 0.89 9.2 -1.17 9.2 C -3.23 9.2 -4.79 7.53 -4.79 5.47 L -4.76 5.11 C -6.78 7.51 -8 10.62 -8 13.99 C -8 18.41 -4.42 22 0 22 C 4.42 22 8 18.41 8 13.99 C 8 8.6 5.41 3.79 1.5 0.67 Z M -0.29 19 C -2.07 19 -3.51 17.6 -3.51 15.86 C -3.51 14.24 -2.46 13.1 -0.7 12.74 C 1.07 12.38 2.9 11.53 3.92 10.16 C 4.31 11.45 4.51 12.81 4.51 14.2 C 4.51 16.85 2.36 19 -0.29 19 Z" fill="{primary}"/>
  </g>
  <text x="590" y="80" text-anchor="middle" fill="{text}" font-family="Segoe UI,Ubuntu,sans-serif" font-weight="700" font-size="32.2">{cur}</text>
  <text x="590" y="140" text-anchor="middle" fill="{primary}" font-family="Segoe UI,Ubuntu,sans-serif" font-weight="700" font-size="16.1">Current Streak</text>
  <text x="590" y="166" text-anchor="middle" fill="{sub}" font-family="Segoe UI,Ubuntu,sans-serif" font-weight="400" font-size="13.8">recent contribution run</text>

  <!-- LONGEST STREAK -->
  <g transform="translate(983.33 34) scale(0.78)">
    <ellipse cx="0" cy="29" rx="27" ry="4" fill="#000000" opacity="0.12"/>
    <path d="M-10 -20 H10 V-3 C10 7 5 14 0 17 C-5 14 -10 7 -10 -3 Z" fill="{secondary}"/>
    <path d="M-10 -15 H-22 V-5 C-22 6 -15 13 -7 13 V7 C-12 6 -15 2 -15 -4 H-10 Z" fill="{secondary}"/>
    <path d="M10 -15 H22 V-5 C22 6 15 13 7 13 V7 C12 6 15 2 15 -4 H10 Z" fill="{secondary}"/>
    <path d="M-3 15 H3 V23 H-3 Z" fill="{secondary}"/>
    <rect x="-18" y="22" width="36" height="8" rx="3" fill="{secondary}"/>
  </g>
  <text x="983.33" y="94" text-anchor="middle" fill="{secondary}" font-family="Segoe UI,Ubuntu,sans-serif" font-size="34.5" font-weight="700">{longest}</text>
  <text x="983.33" y="124" text-anchor="middle" fill="{secondary}" font-family="Segoe UI,Ubuntu,sans-serif" font-size="16.1" font-weight="700">Longest Streak</text>
  <text x="983.33" y="148" text-anchor="middle" fill="{sub}" font-family="Segoe UI,Ubuntu,sans-serif" font-size="13.8">all-time record</text>
  <rect x="958" y="158" width="51" height="4" rx="2" fill="{secondary}"/>

  <!-- GITHUB STATS CARD -->
  <rect x="26" y="210" width="550" height="220" rx="14"
        fill="{card}" stroke="{card_border}"/>
  <text x="50" y="242" fill="{primary}" font-size="15.6" font-weight="700"
        font-family="ui-monospace,SFMono-Regular,Menlo,monospace">GITHUB STATS</text>
  <path d="M178 238 H550" stroke="{card_border}" stroke-dasharray="2 7"/>

  <g fill="none" stroke="{primary}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
    <path d="M-8 -4.5 H-1.5 L0 -3 H8 V6 H-8 Z" transform="translate(31 279)"/>
    <path d="M0 -8 L2.1 -2.6 L7.8 -2.1 L3.4 1.5 L4.8 7.4 L0 4.3 L-4.8 7.4 L-3.4 1.5 L-7.8 -2.1 L-2.1 -2.6 Z" transform="translate(267 279)"/>
    <circle cx="28.3" cy="319.1" r="3.2"/><path d="M22.5 329.5 C23.3 325.8 25.3 324.1 28.3 324.1 C31.2 324.1 33.3 325.8 34.1 329.5"/>
    <circle cx="36.2" cy="320.6" r="2.3"/><path d="M34.6 324.4 C37 324.5 38.4 325.7 39.1 327.8"/>
    <path d="M-8 0 H-3 M3 0 H8" transform="translate(267 327.5)"/><circle cx="267" cy="327.5" r="3.4" fill="{primary}" stroke="none"/>
    <circle cx="28.3" cy="371" r="2.15"/><circle cx="28.3" cy="383" r="2.15"/><circle cx="39.3" cy="371" r="2.15"/>
    <path d="M28.3 373.15 V380.85 M30.6 383 C36.2 383 39.3 380 39.3 374.8 V373.15"/>
    <circle cx="267" cy="376" r="7.2"/><path d="M267 372.4 V377.2"/><circle cx="267" cy="380.2" r=".75" fill="{primary}" stroke="none"/>
  </g>
  <text x="82" y="282" fill="{muted}" font-size="10.8" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">Repositories</text>
  <text x="82" y="303" fill="{text}" font-size="20.4" font-weight="700" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">{d["repos"]}</text>
  <text x="348" y="282" fill="{muted}" font-size="10.8" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">Stars</text>
  <text x="348" y="303" fill="{text}" font-size="20.4" font-weight="700" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">{d["stars"]}</text>
  <text x="82" y="329" fill="{muted}" font-size="10.8" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">Followers</text>
  <text x="82" y="350" fill="{text}" font-size="20.4" font-weight="700" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">{d["followers"]}</text>
  <text x="348" y="329" fill="{muted}" font-size="10.8" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">Commits</text>
  <text x="348" y="350" fill="{text}" font-size="20.4" font-weight="700" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">{d["commits"]}</text>
  <text x="82" y="376" fill="{muted}" font-size="10.8" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">Pull Requests</text>
  <text x="82" y="397" fill="{text}" font-size="20.4" font-weight="700" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">{d["prs"]}</text>
  <text x="348" y="376" fill="{muted}" font-size="10.8" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">Issues</text>
  <text x="348" y="397" fill="{text}" font-size="20.4" font-weight="700" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">{d["issues"]}</text>
  <text x="50" y="414" fill="{secondary}" font-size="10.8"
        font-family="ui-monospace,SFMono-Regular,Menlo,monospace">generated by GitHub Actions</text>

  <!-- TOP LANGUAGES CARD -->
  <rect x="604" y="210" width="550" height="220" rx="14"
        fill="{card}" stroke="{card_border}"/>
  <text x="628" y="242" fill="{primary}" font-size="15.6" font-weight="700"
        font-family="ui-monospace,SFMono-Regular,Menlo,monospace">TOP LANGUAGES</text>
  <path d="M752 238 H1128" stroke="{card_border}" stroke-dasharray="2 7"/>

  <rect x="628" y="264" width="500" height="12" rx="2" fill="{snake_default}"/>
'''.strip()]
    langs = sorted(d["langs"].items(), key=lambda x: x[1], reverse=True)[:5]
    total = sum(v for _, v in langs) or 1
    cursor = 628
    lang_colors = ["#22D3EE", "#00E5FF", "#38BDF8", "#2DD4BF", "#60A5FA"]
    for i, (lang, n) in enumerate(langs):
        w = max(3, 500 * n / total)
        p.append(f'<rect x="{cursor:.1f}" y="264" width="{w:.1f}" height="14" fill="{lang_colors[i]}"/>')
        cursor += w
        y = 301 + i * 21
        p.append(
            f'<circle cx="632" cy="{y-5}" r="4" fill="{lang_colors[i]}"/>'
            f'<text x="646" y="{y}" fill="{text}" font-size="13.2" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">{esc(lang)}</text>'
            f'<text x="1128" y="{y}" text-anchor="end" fill="{muted}" font-size="13.2" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">{n/total*100:.1f}%</text>'
        )
    p.append(
        f'<text x="628" y="414" fill="{secondary}" font-size="10.8" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">calculated from GitHub language bytes</text>'
    )

    # Full animated snake, inlined into the generated activity SVG so GitHub
    # doesn't need to render a nested external SVG.
    snake = snake_body()
    if snake:
        p.append(f'<g transform="translate(46.5 486.3) scale(1.2818 0.8854)">{snake}</g>')
    else:
        # Fallback: keep the panel visually intact if the published snake is
        # temporarily unavailable.
        p.append(
            f'<text x="590" y="535" text-anchor="middle" fill="{muted}" '
            f'font-size="12.65" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">'
            f'CONTRIBUTION SNAKE REFRESHING…</text>'
        )

    p.append(
        '</g></svg>'
    )
    return "".join(p)

def projects(d,theme):
 bg,panel,stroke,text,muted=DARK if theme=="dark" else LIGHT;wanted=["VITalWatch-Prototype","AI_Agents_Hackathon","DeepFake_shield","n8n-workflows","Free-Certifications","project-based-learning"];by={r["name"]:r for r in d["repo_data"]};rs=[by[x] for x in wanted if x in by];h=58+math.ceil(len(rs)/2)*146
 p=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="{h}" viewBox="0 0 1180 {h}"><rect x="1" y="1" width="1178" height="{h-2}" rx="16" fill="{bg}" stroke="{stroke}" stroke-width="2"/>']
 for i,r in enumerate(rs):
  x=5+(i%2)*570;y=42+(i//2)*146;desc=esc(r.get("description") or "Repository project")
  p.append(f'<a href="https://github.com/{r["full_name"]}"><rect x="{x}" y="{y}" width="560" height="132" rx="12" fill="{panel}" stroke="{stroke}"/><text x="{x+16}" y="{y+23}" fill="{muted}" font-family="monospace" font-size="9">● {esc(r["full_name"])}</text><text x="{x+16}" y="{y+57}" fill="{text}" font-family="monospace" font-size="15" font-weight="700">{esc(r["name"])}</text><text x="{x+16}" y="{y+81}" fill="{muted}" font-family="monospace" font-size="10">{desc[:80]}</text><rect x="{x+16}" y="{y+98}" width="86" height="18" rx="9" fill="#06232A" stroke="{stroke}"/><text x="{x+59}" y="{y+111}" text-anchor="middle" fill="{CYAN}" font-family="monospace" font-size="9">{esc(r.get("language") or "GitHub")}</text><text x="{x+542}" y="{y+111}" text-anchor="end" fill="{muted}" font-family="monospace" font-size="10">★ {r.get("stargazers_count",0)}</text></a>')
 p.append("</svg>");return "".join(p)
def main():
 token=os.environ.get("GITHUB_TOKEN");assert token,"GITHUB_TOKEN missing";A.mkdir(exist_ok=True);d=collect(token)
 for t in ("dark","light"):
  (A/f"profile-activity-{t}.svg").write_text(activity(d,t),encoding="utf-8");(A/f"projects-{t}.svg").write_text(projects(d,t),encoding="utf-8");(A/f"hero-{t}.svg").write_text(hero(t),encoding="utf-8");(A/f"signature-stripe-{t}.svg").write_text(signature(t),encoding="utf-8")
if __name__=="__main__":main()
