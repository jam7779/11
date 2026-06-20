#!/usr/bin/env python3
"""SEO Agent 2: SERP Analyzer (Bing RSS, no anti-bot)"""
import argparse, json, os, sqlite3, sys, xml.etree.ElementTree as ET
from urllib.parse import quote
DB = os.path.expanduser("~/.hermes/sqlite-data/seo.db")

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS serp_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT, keyword TEXT NOT NULL,
        engine TEXT DEFAULT 'bing_rss', rank INTEGER, title TEXT, url TEXT,
        snippet TEXT, pub_date TEXT, title_len INTEGER,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit(); return conn

def fetch_bing_rss(keyword, count=10):
    import requests
    url = f"https://www.bing.com/search?format=rss&q={quote(keyword)}&count={count}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=15); r.raise_for_status()
    except Exception as e:
        print(f"  err: {e}", file=sys.stderr); return []
    try: root = ET.fromstring(r.content)
    except: return []
    results = []
    for i, item in enumerate(root.findall(".//item")[:count], 1):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        desc = item.findtext("description", "").strip()
        pub = item.findtext("pubDate", "").strip()
        import re
        desc_clean = re.sub(r"<[^>]+>", "", desc)
        results.append({"rank": i, "title": title, "url": link, "snippet": desc_clean, "pub_date": pub, "title_len": len(title)})
    return results

def analyze(keyword, engine="bing"):
    conn = init_db(); c = conn.cursor()
    print(f"[keyword] {keyword}  [engine] {engine}")
    c.execute("DELETE FROM serp_snapshots WHERE keyword=?", (keyword,))
    results = fetch_bing_rss(keyword) if engine == "bing" else []
    print(f"  fetched: {len(results)}")
    for r in results:
        c.execute("""INSERT INTO serp_snapshots (keyword, engine, rank, title, url, snippet, pub_date, title_len) VALUES (?,?,?,?,?,?,?,?)""",
                  (keyword, engine, r["rank"], r["title"], r["url"], r["snippet"], r.get("pub_date", ""), r["title_len"]))
    conn.commit()
    if results:
        avg = sum(r["title_len"] for r in results) / len(results)
        print(f"  avg title len: {avg:.0f}")
        for r in results:
            print(f"    #{r['rank']:>2} [{r['title_len']:>2}ch] {r['title'][:60]}")
            print(f"           {r['url'][:80]}")
    out = {"keyword": keyword, "engine": engine, "count": len(results), "results": results}
    out_path = f"/tmp/seo-serp-{keyword.replace(' ', '_')}.json"
    with open(out_path, "w") as f: json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n[export] {out_path}")
    conn.close()
    return results

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("keyword"); p.add_argument("--engine", default="bing", choices=["bing", "ddg"])
    args = p.parse_args()
    analyze(args.keyword, args.engine)
