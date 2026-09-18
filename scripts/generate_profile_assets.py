#!/usr/bin/env python3
from __future__ import annotations
import html,json,math,os,urllib.parse,urllib.request
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
def activity(d,theme):
 bg,panel,stroke,text,muted=DARK if theme=="dark" else LIGHT;active,cur,longest=streak(d["days"])
 p=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="670" viewBox="0 0 1180 670"><rect x="1" y="1" width="1178" height="668" rx="16" fill="{bg}" stroke="{stroke}" stroke-width="2"/>',f'<rect x="16" y="16" width="1148" height="178" rx="12" fill="{panel}" stroke="{stroke}"/>']
 for i,(lab,val) in enumerate([("ACTIVE DAYS",active),("CURRENT STREAK",cur),("LONGEST STREAK",longest)]):
  x=205+i*385;p.append(f'<text x="{x}" y="68" text-anchor="middle" fill="{muted}" font-family="monospace" font-size="11">{lab}</text><text x="{x}" y="116" text-anchor="middle" fill="{CYAN}" font-family="monospace" font-size="36" font-weight="700">{val}</text><text x="{x}" y="144" text-anchor="middle" fill="{text}" font-family="monospace" font-size="10">LAST 400 DAYS</text>')
  if i<2:p.append(f'<line x1="{397+i*385}" y1="42" x2="{397+i*385}" y2="168" stroke="{stroke}"/>')
 for x,title in [(26,"GITHUB STATS"),(604,"TOP LANGUAGES")]:p.append(f'<rect x="{x}" y="210" width="550" height="220" rx="12" fill="{panel}" stroke="{stroke}"/><text x="{x+20}" y="239" fill="{CYAN}" font-family="monospace" font-size="12" font-weight="700">{title}</text>')
 stats=[("REPOSITORIES",d["repos"]),("STARS",d["stars"]),("FOLLOWERS",d["followers"]),("COMMITS",d["commits"]),("PULL REQUESTS",d["prs"]),("ISSUES",d["issues"])]
 for i,(lab,val) in enumerate(stats):
  x=48 if i<3 else 305;y=278+(i%3)*45;p.append(f'<text x="{x}" y="{y}" fill="{muted}" font-family="monospace" font-size="10">{lab}</text><text x="{x}" y="{y+20}" fill="{text}" font-family="monospace" font-size="16" font-weight="700">{val}</text>')
 langs=sorted(d["langs"].items(),key=lambda x:x[1],reverse=True)[:8];total=sum(v for _,v in langs) or 1;cursor=626;pal=[CYAN,TEAL,BLUE,"#155E75","#164E63","#1E7490","#287F9B","#3B91AA"]
 for i,(lang,n) in enumerate(langs):
  w=max(3,500*n/total);p.append(f'<rect x="{cursor:.1f}" y="268" width="{w:.1f}" height="12" fill="{pal[i]}"/>');cursor+=w;y=307+i*18;p.append(f'<circle cx="632" cy="{y-4}" r="3.5" fill="{pal[i]}"/><text x="645" y="{y}" fill="{text}" font-family="monospace" font-size="10">{esc(lang)}</text><text x="1118" y="{y}" text-anchor="end" fill="{muted}" font-family="monospace" font-size="10">{n/total*100:.1f}%</text>')
 p.append(f'<rect x="26" y="446" width="1128" height="198" rx="12" fill="{panel}" stroke="{stroke}"/><text x="48" y="474" fill="{CYAN}" font-family="monospace" font-size="11">CONTRIBUTION ACTIVITY</text>')
 if d["days"]:
  end=max(date.fromisoformat(x) for x in d["days"]);start=end-timedelta(days=364);x0=48;y0=500
  for i in range(365):
   day=start+timedelta(days=i);level=min(4,(d["days"].get(day.isoformat(),0)+1)//2) if d["days"].get(day.isoformat(),0) else 0;colors=["#0C1720","#0E2A35","#0E5B70",TEAL,CYAN];p.append(f'<rect x="{x0+(i//7)*13}" y="{y0+((day.weekday()+1)%7)*13}" width="10" height="10" rx="2" fill="{colors[level]}"/>')
 p.append(f'<text x="48" y="625" fill="{muted}" font-family="monospace" font-size="9">TOTAL CONTRIBUTIONS · {d["total"]} · generated by GitHub Actions</text></svg>');return "".join(p)
def projects(d,theme):
 bg,panel,stroke,text,muted=DARK if theme=="dark" else LIGHT;wanted=["VITalWatch-Prototype","AI_Agents_Hackathon","DeepFake_shield","n8n-workflows","Free-Certifications","project-based-learning"];by={r["name"]:r for r in d["repo_data"]};rs=[by[x] for x in wanted if x in by];h=58+math.ceil(len(rs)/2)*146
 p=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="{h}" viewBox="0 0 1180 {h}"><rect x="1" y="1" width="1178" height="{h-2}" rx="16" fill="{bg}" stroke="{stroke}" stroke-width="2"/><text x="590" y="28" text-anchor="middle" fill="{CYAN}" font-family="monospace" font-size="12" font-weight="700">PROJECTS</text>']
 for i,r in enumerate(rs):
  x=5+(i%2)*570;y=42+(i//2)*146;desc=esc(r.get("description") or "Repository project")
  p.append(f'<a href="https://github.com/{r["full_name"]}"><rect x="{x}" y="{y}" width="560" height="132" rx="12" fill="{panel}" stroke="{stroke}"/><text x="{x+16}" y="{y+23}" fill="{muted}" font-family="monospace" font-size="9">● {esc(r["full_name"])}</text><text x="{x+16}" y="{y+57}" fill="{text}" font-family="monospace" font-size="15" font-weight="700">{esc(r["name"])}</text><text x="{x+16}" y="{y+81}" fill="{muted}" font-family="monospace" font-size="10">{desc[:80]}</text><rect x="{x+16}" y="{y+98}" width="86" height="18" rx="9" fill="#06232A" stroke="{stroke}"/><text x="{x+59}" y="{y+111}" text-anchor="middle" fill="{CYAN}" font-family="monospace" font-size="9">{esc(r.get("language") or "GitHub")}</text><text x="{x+542}" y="{y+111}" text-anchor="end" fill="{muted}" font-family="monospace" font-size="10">★ {r.get("stargazers_count",0)}</text></a>')
 p.append("</svg>");return "".join(p)
def main():
 token=os.environ.get("GITHUB_TOKEN");assert token,"GITHUB_TOKEN missing";A.mkdir(exist_ok=True);d=collect(token)
 for t in ("dark","light"):
  (A/f"profile-activity-{t}.svg").write_text(activity(d,t),encoding="utf-8");(A/f"projects-{t}.svg").write_text(projects(d,t),encoding="utf-8")
if __name__=="__main__":main()
