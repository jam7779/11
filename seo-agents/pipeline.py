#!/usr/bin/env python3
"""SEO Pipeline orchestrator: keyword_research → serp_analyzer → content_brief"""
import argparse, json, os, subprocess, sys, sqlite3
from datetime import datetime
DB = os.path.expanduser("~/.hermes/sqlite-data/seo.db")
SCRIPTS = os.path.expanduser("~/.hermes/seo-agents/scripts")
VENV_PY = "/home/ttclaw/.hermes/hermes-agent/venv/bin/python3"

def run_agent(script, *args):
    r = subprocess.run([VENV_PY, os.path.join(SCRIPTS, script), *args], capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout, r.stderr

def pipeline(seed_keyword, engine="bing", skip_brief=False):
    print("=" * 60)
    print(f"  SEO Pipeline — {seed_keyword}")
    print(f"  引擎: {engine}  时间: {datetime.now().isoformat()}")
    print("=" * 60)
    print("\n[1/3] keyword_research")
    rc, out, _ = run_agent("keyword_research.py", seed_keyword, "--lang", "en")
    print(out)
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("""SELECT keyword FROM keywords WHERE seed=? AND length(keyword) > length(?) + 2 ORDER BY length(keyword), source LIMIT 5""", (seed_keyword, seed_keyword))
    candidates = [r[0] for r in c.fetchall()]
    print(f"\n[2/3] serp_analyzer  (top {min(3, len(candidates))} candidates)")
    target_keywords = [seed_keyword] + [k for k in candidates[:3] if k != seed_keyword]
    print(f"  target: {target_keywords}")
    for kw in target_keywords:
        rc, out, _ = run_agent("serp_analyzer.py", kw, "--engine", engine)
        print(f"  {kw}: ✓")
    if not skip_brief:
        print(f"\n[3/3] content_brief  (主关键词: {seed_keyword})")
        rc, out, _ = run_agent("content_brief.py", seed_keyword)
        print(out)
    report_path = f"/tmp/seo-report-{seed_keyword.replace(' ', '_')}.md"
    with open(report_path, "w") as f:
        f.write(f"# SEO Report: {seed_keyword}\n\n**Generated**: {datetime.now().isoformat()}\n\n")
        f.write("## Keywords\n")
        c.execute("SELECT source, COUNT(*) FROM keywords WHERE seed=? GROUP BY source", (seed_keyword,))
        for src, n in c.fetchall(): f.write(f"- {src}: {n}\n")
        f.write("\n## SERP\n")
        for kw in target_keywords:
            json_path = f"/tmp/seo-serp-{kw.replace(' ', '_')}.json"
            if os.path.exists(json_path):
                d = json.load(open(json_path))
                f.write(f"\n### `{kw}` ({d['count']} results)\n")
                for r in d["results"][:5]:
                    f.write(f"- #{r['rank']} [{r['title_len']}ch] {r['title']}\n  {r['url'][:80]}\n")
        if not skip_brief:
            brief_path = f"/tmp/seo-brief-{seed_keyword.replace(' ', '_')}.json"
            if os.path.exists(brief_path):
                brief = json.load(open(brief_path))
                f.write(f"\n## Content Brief\n\n**Model**: {brief.get('model','?')}\n\n")
                f.write("### Titles\n")
                for t in brief["title_suggestions"]: f.write(f"- {t} ({len(t)}ch)\n")
                f.write("\n### H2\n")
                for h in brief["h2_outline"]: f.write(f"- {h}\n")
                f.write(f"\n### Meta ({len(brief['meta_description'])} chars)\n\n> {brief['meta_description']}\n")
    print(f"\n[report] {report_path}")
    desktop = "/mnt/c/Users/openc/Desktop"
    if os.path.isdir(desktop):
        import shutil
        dst = f"{desktop}/SEO-{seed_keyword.replace(' ', '_')}.md"
        shutil.copy(report_path, dst)
        print(f"✅ 桌面: {dst}")
    conn.close()
    return report_path

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("seed"); p.add_argument("--engine", default="bing", choices=["bing","ddg"]); p.add_argument("--skip-brief", action="store_true")
    args = p.parse_args()
    pipeline(args.seed, args.engine, args.skip_brief)
