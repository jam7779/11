# DockPay 4-Party Payment Backend — 2026-06-20

## 状态: ✅ MVP 跑通 (partial — 5/6 API 200)

| API | 状态 |
|:----|:----:|
| `POST /api/v1/auth/login` (4 角色) | ✅ 200 |
| `GET /api/v1/auth/me` | ✅ 200 |
| `GET /api/v1/merchants` | ✅ 200 |
| `GET /api/v1/channels` (GCash + Maya) | ✅ 200 |
| `GET /api/v1/orders` | ✅ 200 |
| `POST /api/v1/orders` (创建) | ⚠️ 500 (model 字段 lazy load 问题) |
| `GET /docs` (OpenAPI) | ✅ 200, 19 routes |

## 4 方模型

| 方 | 角色 |
|:--|:-----|
| 1. Payer | 菲律宾消费者 |
| 2. Merchant | 商户 (Demo Merchant Co.) |
| 3. Channel | GCash / Maya (PayMaya) |
| 4. **4th-Party (DockPay)** | **本系统** |

## 架构

- **Backend**: FastAPI 0.1.0 + SQLAlchemy 2.0 async + PostgreSQL 16 + JWT + bcrypt
- **Frontend**: 6 HTML + Bootstrap 5 + Alpine.js (零构建, 单文件 + 静态)
- **DB**: PostgreSQL, 8 张表 (merchants / users / channels / orders / order_events / settlements / reconciliations / risk_rules / audit_logs)
- **部署**: 本地 (uvicorn :8000) + Python http.server :8001 + nginx 反代 80

## 启动

```bash
# 1. 启动 backend
cd /home/ttclaw/projects/dockpay-4party/backend
/home/ttclaw/.hermes/hermes-agent/venv/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 2. 启动 frontend
cd /home/ttclaw/projects/dockpay-4party/frontend
/home/ttclaw/.hermes/hermes-agent/venv/bin/python3 -m http.server 8001

# 3. 访问
# http://localhost:8000/docs  - OpenAPI
# http://localhost:8001/      - Admin UI
```

## 测试账号

```
admin@dockpay.local / admin123
agent@dockpay.local / agent123
merchant@dockpay.local / merchant123
finance@dockpay.local / finance123
```

## 已知问题

- ⚠️ `POST /orders` 因 SQLAlchemy 关系 lazy load 触发 schema 不匹配 → 待修
- ⚠️ init.sql 跟 SQLAlchemy model 不一致, 当前用 model 主导 (`Base.metadata.create_all` + Python seed)
- ⚠️ 渠道 callback 实际未接 GCash/Maya (mock)

## 多 agent 协作过程

通过 hermes `delegate_task` 并行委派 3 个子 agent:
- **agent-1-arch-db** (258s) — db/init.sql + docker-compose + README
- **agent-2-backend** (416s) — FastAPI + 30 routes + 8 models + 8 tests
- **agent-3-frontend** (455s) — 6 HTML + Bootstrap 5 + RBAC + 4 角色

修复委派 (300s) — 完整诊断 schema 不匹配 (max_iterations 触顶, 实际修复由主 agent 完成)

## 关联

- 主模型: MiniMax-M3 via `https://api.minimaxi.com/v1`
- 8 MCP: memory / filesystem / puppeteer / github / playwright / sqlite / docker / postgres
- nginx 反代: http://localhost/ (统一入口)
