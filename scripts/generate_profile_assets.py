#!/usr/bin/env python3
from __future__ import annotations
import html,json,math,os,re,urllib.parse,urllib.request
from collections import Counter
from datetime import date,timedelta
from pathlib import Path
USER="IshanRayC"; ROOT=Path(__file__).resolve().parents[1]; A=ROOT/"assets"
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
    m = re.search(r'<svg\\b[^>]*\\bviewBox=["\\\']([^"\\\']+)["\\\']', raw, re.I)
    vb = m.group(1) if m else "0 0 1000 1000"
    body = re.search(r"<svg\\b[^>]*>(.*)</svg>\\s*$", raw, re.I | re.S)
    return (body.group(1) if body else raw), vb

def hero(theme):
    bg, panel, stroke, text, muted = DARK if theme == "dark" else LIGHT
    body, vb = read_portrait()
    if theme == "dark":
        shell, label, dotted, visual, value = "#0D1016", "#67E8F9", "#16343E", "#06080B", "#F8FAFC"
    else:
        shell, label, dotted, visual, value = "#FFFFFF", "#0E7490", "#D6EAF0", "#050608", "#0F172A"
    portrait = f'<svg x="52" y="130" width="420" height="420" viewBox="{esc(vb)}" preserveAspectRatio="xMidYMid meet" overflow="hidden">{body}</svg>'
    rows = [
        ("Subject","ISHAN RAY CHAUDHURI"),("Role","CSE AND DATA SCIENCE STUDENT"),
        ("Origin","CHENNAI, INDIA"),("Education","BTECH CSE · VIT CHENNAI"),
        ("","BS DATA SCIENCE · IIT MADRAS"),("Status","LEARNING + BUILDING + SHIPPING"),
        ("Core.Lang","C · C++ · PYTHON · JAVA · R"),("Core.Data","NUMPY · PANDAS · MATLAB"),
        ("Core.Infra","DOCKER · WSL · CLOUD · DEVOPS")]
    p = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="610" viewBox="0 0 1180 610" role="img" aria-label="Ishan Ray Chaudhuri system profile">
<defs><clipPath id="v"><rect x="52" y="130" width="420" height="420" rx="14"/></clipPath></defs>
<rect width="1180" height="610" rx="18" fill="{bg}"/><rect x="18" y="18" width="1144" height="574" rx="16" fill="{shell}" stroke="{stroke}"/>
<rect x="42" y="42" width="1100" height="44" rx="10" fill="{CYAN}"/>
<circle cx="66" cy="64" r="6" fill="#FFF"/><circle cx="86" cy="64" r="6" fill="#FFF"/><circle cx="106" cy="64" r="6" fill="#FFF"/>
<text x="134" y="70" fill="#FFF" font-size="14" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">ISHAN LABS</text>
<rect x="954" y="42" width="44" height="44" fill="#FFF"/><text x="976" y="70" fill="#0F172A" font-size="14" font-weight="700" text-anchor="middle" font-family="ui-monospace,monospace">IR</text>
<rect x="998" y="42" width="144" height="44" fill="{CYAN}"/><text x="1070" y="69" fill="#FFF" font-size="14" font-weight="700" text-anchor="middle" font-family="ui-monospace,monospace">02</text>
<text x="60" y="116" fill="{label}" font-size="13" font-family="ui-monospace,monospace">VISUAL.MAP</text><text x="504" y="116" fill="{label}" font-size="13" font-family="ui-monospace,monospace">SYSTEM.INFO</text>
<rect x="52" y="130" width="420" height="420" rx="14" fill="{visual}" stroke="{CYAN}" stroke-width="2"/><g clip-path="url(#v)">{portrait}</g>
<g font-size="14" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">''']
    y = 154
    for k, v in rows:
        p.append(f'<text x="522" y="{y}" fill="{muted}">{esc(k)}</text>' if k else f'<text x="522" y="{y}" fill="{muted}"> </text>')
        p.append(f'<path d="M610 {y-4} H900" stroke="{dotted}" stroke-dasharray="2 6"/><text x="930" y="{y}" fill="{value}" text-anchor="end">{esc(v)}</text>')
        y += 23
    p.append(f'''</g><rect x="522" y="378" width="408" height="34" rx="17" fill="{CYAN}" fill-opacity=".10" stroke="{CYAN}" stroke-opacity=".75"/>
<text x="726" y="400" fill="{CYAN}" font-size="14" text-anchor="middle" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">@IshanRayC</text>
<text x="522" y="448" fill="{CYAN}" font-size="13" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">TARGET</text>
<text x="522" y="472" fill="{value}" font-size="15" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">SOFTWARE · AI/ML · CLOUD · DEVOPS · QUANT · HFT</text>
<text x="522" y="496" fill="{value}" font-size="15" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">AUTOMATION · SYSTEM DESIGNS</text></svg>''')
    return "".join(p)

def signature(theme):
    bg = "#FFFFFF" if theme == "light" else "#0D1016"
    text = "#0F172A" if theme == "light" else "#F8FAFC"
    stroke = "#B8DCE4" if theme == "light" else "#12313B"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="72" viewBox="0 0 1040 72" role="img" aria-label="Ishan signature stripe">
<rect x="1" y="1" width="1038" height="70" rx="8" fill="{bg}" stroke="{CYAN}" stroke-width="2"/><rect x="82" y="10" width="1" height="52" fill="{stroke}"/>
<text x="24" y="44" fill="{text}" font-size="18" font-weight="700" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">IR</text>
<text x="110" y="44" fill="{CYAN}" font-size="20" font-weight="700" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">BUILD • BREAK • DEBUG • LEARN • DEPLOY</text>
<text x="1000" y="44" fill="{CYAN}" font-size="20" font-weight="700" text-anchor="end" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">02</text></svg>'''



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
</defs>
<rect x="1" y="1" width="1178" height="668" rx="16"
      fill="{frame}" stroke="{card_border}" stroke-width="2"/>
<g clip-path="url(#activityFrame)">
  <rect x="16" y="16" width="1148" height="178" rx="12"
        fill="{card}" stroke="{card_border}"/>
  <line x1="393.33" y1="44" x2="393.33" y2="170" stroke="{divider}"/>
  <line x1="786.67" y1="44" x2="786.67" y2="170" stroke="{divider}"/>

  <!-- ACTIVE DAYS -->
  <g fill="{primary}">
    <rect x="193" y="42" width="24" height="22" rx="4"/>
    <rect x="193" y="40" width="24" height="7" rx="3"/>
    <rect x="197" y="36" width="3" height="7" rx="1"/>
    <rect x="210" y="36" width="3" height="7" rx="1"/>
    <rect x="197" y="50" width="3" height="3" rx="1"/>
    <rect x="203" y="50" width="3" height="3" rx="1"/>
    <rect x="209" y="50" width="3" height="3" rx="1"/>
    <rect x="197" y="56" width="3" height="3" rx="1"/>
    <rect x="203" y="56" width="3" height="3" rx="1"/>
    <rect x="209" y="56" width="3" height="3" rx="1"/>
  </g>
  <text x="205" y="98" text-anchor="middle" fill="{primary}"
        font-family="Segoe UI,Ubuntu,sans-serif"
        font-size="30" font-weight="700">{active}</text>
  <text x="205" y="126" text-anchor="middle" fill="{primary}"
        font-family="Segoe UI,Ubuntu,sans-serif"
        font-size="14" font-weight="700">Active Days</text>
  <text x="205" y="150" text-anchor="middle" fill="{sub}"
        font-family="Segoe UI,Ubuntu,sans-serif"
        font-size="12">last 400 days</text>
  <rect x="180" y="158" width="50" height="4" rx="2" fill="{primary}"/>

  <!-- CURRENT STREAK -->
  <circle cx="590" cy="91" r="40" fill="none" stroke="{primary}" stroke-width="5"/>
  <g fill="{primary}">
    <path d="M590 37 C594 44 591 48 597 53 C603 58 600 66 594 70 C600 67 606 63 606 57 C606 52 604 48 600 44 C601 51 596 55 594 51 C592 47 595 42 590 37 Z"/>
    <path d="M586 56 C582 60 581 64 583 68 C585 72 589 74 593 74 C589 71 588 68 590 65 C592 62 590 59 586 56 Z"/>
  </g>
  <text x="590" y="99" text-anchor="middle" fill="{text}"
        font-family="Segoe UI,Ubuntu,sans-serif"
        font-size="28" font-weight="700">{cur}</text>
  <text x="590" y="140" text-anchor="middle" fill="{primary}"
        font-family="Segoe UI,Ubuntu,sans-serif"
        font-size="14" font-weight="700">Current Streak</text>
  <text x="590" y="166" text-anchor="middle" fill="{sub}"
        font-family="Segoe UI,Ubuntu,sans-serif"
        font-size="12">active contribution days</text>

  <!-- LONGEST STREAK -->
  <g fill="{secondary}">
    <path d="M983 39 L987 49 L998 50 L990 57 L992 68 L983 63 L974 68 L976 57 L968 50 L979 49 Z"/>
    <rect x="979" y="63" width="8" height="13" rx="1"/>
    <rect x="970" y="76" width="26" height="6" rx="2"/>
    <path d="M976 48 H963 C963 58 967 63 975 64 V58 C970 57 968 54 968 51 H976 Z"/>
    <path d="M990 48 H1003 C1003 58 999 63 991 64 V58 C996 57 998 54 998 51 H990 Z"/>
  </g>
  <text x="983" y="98" text-anchor="middle" fill="{secondary}"
        font-family="Segoe UI,Ubuntu,sans-serif"
        font-size="30" font-weight="700">{longest}</text>
  <text x="983" y="126" text-anchor="middle" fill="{secondary}"
        font-family="Segoe UI,Ubuntu,sans-serif"
        font-size="14" font-weight="700">Longest Streak</text>
  <text x="983" y="150" text-anchor="middle" fill="{sub}"
        font-family="Segoe UI,Ubuntu,sans-serif"
        font-size="12">all-time record</text>
  <rect x="958" y="158" width="51" height="4" rx="2" fill="{secondary}"/>

  <!-- GITHUB STATS CARD -->
  <rect x="26" y="210" width="550" height="220" rx="14"
        fill="{card}" stroke="{card_border}"/>
  <text x="50" y="242" fill="{primary}" font-size="13" font-weight="700"
        font-family="ui-monospace,SFMono-Regular,Menlo,monospace">GITHUB STATS</text>
  <path d="M178 238 H550" stroke="{card_border}" stroke-dasharray="2 7"/>

  <g font-family="Segoe UI Emoji, Segoe UI, sans-serif" font-size="10">
    <path d="M50 274 H59 L63 278 H75 V289 H50 Z" fill="{primary}"/>
    <text x="68" y="282" fill="{muted}" font-size="10">Repositories</text>
    <text x="68" y="304" fill="{text}" font-size="18" font-weight="700">{d["repos"]}</text>

    <path d="M330 274 L332.5 280 L339 280.5 L334 284.5 L335.5 291 L330 287.5 L324.5 291 L326 284.5 L321 280.5 L327.5 280 Z" fill="{primary}"/>
    <text x="336" y="282" fill="{muted}" font-size="10">Stars</text>
    <text x="336" y="304" fill="{text}" font-size="18" font-weight="700">{d["stars"]}</text>

    <g fill="{primary}"><circle cx="57" cy="322" r="4"/><circle cx="68" cy="324" r="3"/><path d="M50 336 C50 330 53 327 57 327 C61 327 64 330 64 336 Z"/><path d="M63 336 C63 332 66 330 69 330 C72 330 75 332 75 336 Z"/></g>
    <text x="68" y="329" fill="{muted}" font-size="10">Followers</text>
    <text x="68" y="351" fill="{text}" font-size="18" font-weight="700">{d["followers"]}</text>

    <g fill="{primary}"><rect x="50" y="319" width="23" height="15" rx="2"/><rect x="56" y="336" width="11" height="2" rx="1"/></g>
    <text x="336" y="329" fill="{muted}" font-size="10">Commits</text>
    <text x="336" y="351" fill="{text}" font-size="18" font-weight="700">{d["commits"]}</text>

    <g fill="none" stroke="{primary}" stroke-width="2"><circle cx="56" cy="372" r="3.5"/><circle cx="70" cy="372" r="3.5"/><circle cx="63" cy="384" r="3.5"/><path d="M56 376 V384 M70 376 V379 C70 382 68 384 63 384"/></g>
    <text x="68" y="376" fill="{muted}" font-size="10">Pull Requests</text>
    <text x="68" y="398" fill="{text}" font-size="18" font-weight="700">{d["prs"]}</text>

    <g fill="{primary}"><circle cx="330" cy="377" r="8"/><rect x="329" y="372" width="2" height="6" rx="1" fill="{card}"/><circle cx="330" cy="381" r="1.2" fill="{card}"/></g>
    <text x="336" y="376" fill="{muted}" font-size="10">Issues</text>
    <text x="336" y="398" fill="{text}" font-size="18" font-weight="700">{d["issues"]}</text>
  </g>
  <text x="50" y="414" fill="{secondary}" font-size="9"
        font-family="ui-monospace,SFMono-Regular,Menlo,monospace">generated by GitHub Actions</text>

  <!-- TOP LANGUAGES CARD -->
  <rect x="604" y="210" width="550" height="220" rx="14"
        fill="{card}" stroke="{card_border}"/>
  <text x="628" y="242" fill="{primary}" font-size="13" font-weight="700"
        font-family="ui-monospace,SFMono-Regular,Menlo,monospace">TOP LANGUAGES</text>
  <path d="M752 238 H1128" stroke="{card_border}" stroke-dasharray="2 7"/>

  <rect x="628" y="264" width="500" height="12" rx="2" fill="{snake_default}"/>
'''.strip()]
    langs = sorted(d["langs"].items(), key=lambda x: x[1], reverse=True)[:8]
    total = sum(v for _, v in langs) or 1
    cursor = 628
    lang_colors = [CYAN, TEAL, BLUE, "#155E75", "#164E63", "#1E7490", "#287F9B", "#3B91AA"]
    for i, (lang, n) in enumerate(langs):
        w = max(3, 500 * n / total)
        p.append(f'<rect x="{cursor:.1f}" y="264" width="{w:.1f}" height="12" fill="{lang_colors[i]}"/>')
        cursor += w
        y = 301 + i * 21
        p.append(
            f'<circle cx="632" cy="{y-4}" r="3.6" fill="{lang_colors[i]}"/>'
            f'<text x="646" y="{y}" fill="{text}" font-size="11" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">{esc(lang)}</text>'
            f'<text x="1128" y="{y}" text-anchor="end" fill="{muted}" font-size="11" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">{n/total*100:.1f}%</text>'
        )
    p.append(
        f'<text x="628" y="414" fill="{secondary}" font-size="9" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">calculated from GitHub language bytes</text>'
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
            f'font-size="11" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">'
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
