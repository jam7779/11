#!/usr/bin/env python3
"""SEO Agent 3: Content Brief Generator (LLM via MiniMax-M3)"""
import argparse, json, os, sqlite3, sys
DB = os.path.expanduser("~/.hermes/sqlite-data/seo.db")

def init_db():
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS content_briefs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, keyword TEXT NOT NULL,
        title_suggestions TEXT, h2_outline TEXT, meta_description TEXT,
        target_word_count INTEGER, keyword_density_target REAL, model TEXT,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit(); return conn

def get_env_var(name):
    val = os.environ.get(name, "")
    if val: return val
    env_path = os.path.expanduser("~/.hermes/.env")
    if not os.path.exists(env_path): return ""
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or "=" not in line: continue
            if line.startswith(name + "=") or line.startswith(f"export {name}="):
                _, v = line.split("=", 1)
                return v.strip().strip('"').strip("'")
    return ""

def generate_brief_via_llm(keyword, serp_context=None):
    import requests
    api_key = get_env_var("MINIMAX_CN_API_KEY")
    if not api_key: return None, None
    prompt = f'你是 SEO 专家。基于关键词 "{keyword}" 生成内容大纲。输出严格 JSON (无 markdown): {{"title_suggestions": ["标题1-5"], "h2_outline": ["H2 1-7"], "meta_description": "160 字符内", "target_word_count": 2000, "keyword_density_target": 1.5, "search_intent": "informational", "lsi_keywords": ["5个相关词"]}}'
    if serp_context: prompt += "\n\n参考 SERP top 3:\n" + "\n".join(f"- {r['title']}" for r in serp_context[:3])
    try:
        r = requests.post("https://api.minimaxi.com/v1/chat/completions",
            headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
            json={"model": "MiniMax-M3", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 4000}, timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        import re
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        s = content.find("{"); e = content.rfind("}") + 1
        if s < 0 or e <= s: return None, None
        return json.loads(content[s:e]), "MiniMax-M3"
    except Exception as e:
        print(f"  llm err: {e}", file=sys.stderr); return None, None

def mock_brief(keyword):
    return {
        "title_suggestions": [f"What is {keyword}? A Complete Guide for 2026", f"{keyword}: Definition, Examples & Best Practices", f"How to Use {keyword}", f"The Ultimate {keyword} Strategy", f"Top 10 {keyword} Tips"],
        "h2_outline": [f"What is {keyword}?", f"Why {keyword} Matters", f"How {keyword} Works", f"Benefits", f"Common Mistakes", f"Best Tools", f"FAQ"],
        "meta_description": f"Learn everything about {keyword} in our 2026 guide. Strategies, tools, and tips to help you succeed.",
        "target_word_count": 2200, "keyword_density_target": 1.5, "search_intent": "informational",
        "lsi_keywords": [keyword + " guide", keyword + " tips", "best " + keyword, keyword + " strategy", keyword + " examples"]
    }, "mock"

def generate(keyword, use_llm=True):
    conn = init_db(); c = conn.cursor()
    print(f"[keyword] {keyword}")
    serp_context = []
    for r in c.execute("SELECT rank, title, url, snippet FROM serp_snapshots WHERE keyword=? ORDER BY rank LIMIT 3", (keyword,)).fetchall():
        serp_context.append({"rank": r[0], "title": r[1], "url": r[2], "snippet": r[3]})
    brief, model = generate_brief_via_llm(keyword, serp_context) if use_llm else (None, None)
    if brief is None: brief, model = mock_brief(keyword)
    print(f"  model: {model}")
    c.execute("""INSERT INTO content_briefs (keyword, title_suggestions, h2_outline, meta_description, target_word_count, keyword_density_target, model) VALUES (?,?,?,?,?,?,?)""",
              (keyword, json.dumps(brief["title_suggestions"], ensure_ascii=False), json.dumps(brief["h2_outline"], ensure_ascii=False), brief["meta_description"], brief["target_word_count"], brief["keyword_density_target"], model))
    conn.commit()
    for i, t in enumerate(brief["title_suggestions"], 1): print(f"  {i}. [{len(t)}ch] {t}")
    for h in brief["h2_outline"]: print(f"  - {h}")
    print(f"  meta: {brief['meta_description']} ({len(brief['meta_description'])} 字符)")
    print(f"  字数: {brief['target_word_count']} | 密度: {brief['keyword_density_target']}%")
    out_path = f"/tmp/seo-brief-{keyword.replace(' ', '_')}.json"
    with open(out_path, "w") as f: json.dump({"keyword": keyword, "model": model, **brief}, f, ensure_ascii=False, indent=2)
    print(f"[export] {out_path}")
    conn.close()
    return brief

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("keyword"); p.add_argument("--no-llm", action="store_true")
    args = p.parse_args()
    generate(args.keyword, use_llm=not args.no_llm)
