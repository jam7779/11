# Hermes nginx 反代 — 2026-06-19 18:29

## 作用

把 hermes gateway + dashboard 的随机端口 (30000-40000) 藏到稳定的 80 端口后面。

## 路由

```
http://localhost/            → 127.0.0.1:35238  (chat gateway)
http://localhost/dashboard/  → 127.0.0.1:31496  (web dashboard)
```

## Windows 桌面入口

`C:\Users\openc\Desktop\Hermes Dashboard.url` → `http://localhost/dashboard/`
(稳定 URL, 跟随机端口解耦)

## 集成方式

每次跑 `hermes-random-stack-restart.sh` 末尾自动调 `hermes-nginx-sync.sh`:
1. 扫 `/proc/*/cmdline` 找当前 gateway + dashboard 端口
2. 写 `/etc/nginx/sites-available/hermes`
3. `nginx -t && nginx -s reload`
4. 同步 Windows 桌面快捷方式
5. 落 `~/.hermes/runtime/ports.env`

## 端口文件

`~/.hermes/runtime/ports.env`:
```
export HERMES_GATEWAY_PORT=35238
export HERMES_DASHBOARD_PORT=31496
export HERMES_NGINX_URL=http://localhost/
export HERMES_DASHBOARD_URL=http://localhost/dashboard/
```

## 关键文件

- `~/.hermes/scripts/hermes-nginx-sync.sh` — 端口同步 script (chmod +x)
- `~/.hermes/scripts/hermes-random-stack-restart.sh` — 已 patch, 末尾调 sync
- `/etc/nginx/sites-available/hermes` — 反代 config (自动生成, 不要手改)

## 验证

| URL | 响应 |
|:----|:-----|
| `http://localhost/dashboard/` | HTTP 200, 721 字节 HTML |
| `http://localhost/` | HTTP 404, 14 字节 (gateway 自己的 404, 证明反代通了) |
| `http://localhost/nginx-status` | 403 (nginx 自己, 没暴露) |

## 优势

- **稳定 URL**: 用户/快捷方式只用记 `http://localhost/`
- **端口随机化保留**: 底层 gateway/dashboard 仍然每次启动换端口
- **零额外 token**: 全本地, 不依赖外部服务
- **WSL2 友好**: nginx 跑 WSL 内, Windows 通过 `localhost` 透明访问
