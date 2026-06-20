#!/usr/bin/env python3
"""SEO Agent 1: Keyword Research
- 输入: 种子词 (1 个)
- 输出: 50+ 扩展词 (Google Suggest + PAA + 相关搜索)
- 存储: SQLite seo.db
"""
import argparse
import os
import sqlite3
import json
import subprocess
import sys
from urllib.parse import quote

DB = os.path.expanduser("~/.hermes/sqlite-data/seo.db")

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seed TEXT NOT NULL,
        keyword TEXT NOT NULL,
        source TEXT NOT NULL,
        lang TEXT DEFAULT 'en',
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(seed, keyword, source)
    )""")
    conn.commit()
    return conn

def google_suggest(seed, lang="en"):
    import urllib.request
    url = f"https://suggestqueries.google.com/complete/search?client=firefox&q={quote(seed)}&hl={lang}"
    try:
        r = urllib.request.urlopen(url, timeout=10)
        data = json.loads(r.read())
        return data[1] if len(data) > 1 else []
    except Exception as e:
        print(f"suggest err: {e}", file=sys.stderr)
        return []

def alphabet_suggest(seed, lang="en"):
    out = []
    for c in "abcdefghijklmnopqrstuvwxyz":
        out.extend(google_suggest(f"{seed} {c}", lang))
    return list(set(out))

def paa_questions(seed, lang="en"):
    starters = ["how", "what", "why", "when", "is", "are", "can", "do", "does", "should"]
    out = []
    for s in starters:
        out.extend(google_suggest(f"{s} {seed}", lang))
    return list(set(out))[:30]

def research(seed, lang="en"):
    conn = init_db()
    c = conn.cursor()
    print(f"[seed] {seed}")
    direct = google_suggest(seed, lang)
    print(f"  suggest: {len(direct)}")
    for kw in direct:
        try: c.execute("INSERT OR IGNORE INTO keywords (seed, keyword, source, lang) VALUES (?,?,?,?)", (seed, kw, "suggest", lang))
        except: pass
    alpha = alphabet_suggest(seed, lang)
    print(f"  alphabet: {len(alpha)}")
    for kw in alpha:
        try: c.execute("INSERT OR IGNORE INTO keywords (seed, keyword, source, lang) VALUES (?,?,?,?)", (seed, kw, "alphabet", lang))
        except: pass
    paa = paa_questions(seed, lang)
    print(f"  paa: {len(paa)}")
    for kw in paa:
        try: c.execute("INSERT OR IGNORE INTO keywords (seed, keyword, source, lang) VALUES (?,?,?,?)", (seed, kw, "paa", lang))
        except: pass
    conn.commit()
    c.execute("SELECT source, COUNT(*) FROM keywords WHERE seed=? GROUP BY source", (seed,))
    print(f"\n[summary] seed={seed}")
    for row in c.fetchall():
        print(f"  {row[0]:<10} {row[1]}")
    c.execute("SELECT DISTINCT keyword FROM keywords WHERE seed=? ORDER BY keyword", (seed,))
    kws = [r[0] for r in c.fetchall()]
    out = {"seed": seed, "lang": lang, "count": len(kws), "keywords": kws}
    out_path = f"/tmp/seo-keywords-{seed.replace(' ', '_')}.json"
    with open(out_path, "w") as f: json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n[export] {out_path}")
    conn.close()
    return kws

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("seed")
    p.add_argument("--lang", default="en")
    args = p.parse_args()
    research(args.seed, args.lang)
