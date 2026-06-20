# SEO Agents — Hermes-powered SEO 工具集

3 个 agent + 1 个 pipeline, 跑在 Hermes 8-MCP 稳态上 (MiniMax-M3 + 8 MCP + Nginx 反代)。

## Agents

| Agent | 文件 | 输入 | 输出 | 引擎 |
|:------|:-----|:-----|:-----|:-----|
| **keyword-research** | `scripts/keyword_research.py` | 1 种子词 | 50+ 扩展词 | Google Suggest API |
| **serp-analyzer** | `scripts/serp_analyzer.py` | 1 关键词 | Top 10 标题/URL/描述 | **Bing RSS** (无反爬) |
| **content-brief** | `scripts/content_brief.py` | 1 关键词 | 5 标题 + 7 H2 + meta + LSI | **MiniMax-M3 LLM** |

## Pipeline

```bash
python3 ~/.hermes/seo-agents/scripts/pipeline.py "vibe growth"
# 自动跑: keyword_research → serp_analyzer(3 candidates) → content_brief
# 输出: /tmp/seo-report-vibe_growth.md
# 同步: /mnt/c/Users/openc/Desktop/SEO-vibe_growth.md
```

## 实测 (2026-06-20, 种子词 "vibe growth")

- **90 keywords** (10 suggest + 80 alphabet)
- **40 SERP rows** (4 keywords × 10)
- **1 content brief** (MiniMax-M3, 2200 字目标, 5 标题 53-61 字符, 7 H2, meta 150 字符)
- **报告 5062 字节**, 同步到 Windows 桌面

## 数据存储

SQLite: `~/.hermes/sqlite-data/seo.db`
- `keywords` (seed, keyword, source, lang)
- `serp_snapshots` (keyword, engine, rank, title, url, snippet, title_len, pub_date)
- `content_briefs` (keyword, title_suggestions JSON, h2_outline JSON, meta, target, model)

## 已知限制

| 维度 | 现状 | 解决方向 |
|:-----|:-----|:---------|
| SERP 引擎 | Bing RSS (相关度低于 Google) | 付费 SerpAPI / DataForSEO |
| PAA | 0 个 (Google 反爬) | AnswerThePublic API / Bing PAA |
| 搜索量 | 无 | Keyword Planner / Ahrefs / SEMrush |

## 关联 Hermes 8-MCP 稳态

- venv: `~/.hermes/hermes-agent/venv/bin/python3`
- API key: 自动从 `~/.hermes/.env` 读 (不需 source)
- 数据: `~/.hermes/sqlite-data/seo.db`
- 桌面: `C:\Users\openc\Desktop\`
- LLM: MiniMax-M3 via `https://api.minimaxi.com/v1`
