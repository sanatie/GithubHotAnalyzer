# AGENTS.md —— GitHub 热榜分析器协作守则

本文件供 AI 与协作者在**修改本项目代码前**阅读并全程遵守。优先级高于临场推断；与 README 冲突时以此为准。

## 项目速览

- 全栈 + 桌面壳：`backend/`（FastAPI + SQLAlchemy + SQLite）、`frontend/`（Vue 3 + Pinia + Element Plus + Vite + Electron）。

- 开发启动：根目录 `start-dev.bat`（后端 8000 / 前端 5173）。

- 后端入口 `backend/run.py`，前端开发服务 `frontend/` 下 `npm run dev`。

## 编码铁律（必须遵守）

- **API 一律英文 RESTful，带** **`/api/v1/`** **前缀**，禁止中文路径。

- **只做最小改动**：只改任务涉及的代码，不做周边重构，不添加"未来可能用到"的抽象或特性。

- **默认不新增依赖**；确需新增须先说明用途。

- 后端注释保持克制，只写"为什么"类注释，不写"做了什么"。

- 请求体入参模型优先用 Pydantic 模型自动解析校验。

- 前端路由必须使用 `createWebHashHistory()`（Electron 兼容），不得改用 history 模式。

- Electron 自定义标题栏：窗口控制最小化/最大化/关闭走 IPC；关闭按钮 hover 红色；非 Electron 环境不渲染控制按钮。

## 验证要求

- **每轮后端逻辑改动后，必须能通过测试才算完成：**

  ```
  backend\.venv\Scripts\python.exe -m pytest tests -q
  ```

- 新增下载链接构造 / 安全白名单 / URL 规范化类逻辑时，**在** **`backend/tests/test_downloader_service.py`** **同步补用例**。

- 涉及下载 / 鉴权 / 上报给外部的新改动，改完跑一次真实用例确认网络链路可用。

- 前端改动不得破坏 `npm run build`。

## 安全红线（最高优先级）

- **GitHub Token 只允许发往** **`api.github.com`**（含子域）。任何镜像/下载/codeload/raw 请求都不得附加该 token；不得绕过 `github_service` 内的域名白名单剥离逻辑。

- **AI API Key 只允许发往** **`AI_BASE_ALLOWLIST`** **白名单内域名**；不得发给任何第三方镜像或任意 URL，不得发往纯 IP 或内网地址。

- **SSH 私钥只放** **`~/.ssh`**（标准、不同步 OneDrive）；项目内、临时目录、日志里不得出现或持久化私钥/`.env` 明文。若发现私钥曾进项目目录，一律迁出并清理。

- 下载 URL 必须先过 `_sanitize_url` 的 GitHub 域名白名单（防 SSRF/路径注入），archive 链接按 `_normalize_download_url` 转 codeload 直链。

- API 返回中对 key 一律脱敏（`_mask_api_key`），不得回显明文。

- `.env` 属于运行时配置（不进版本库）；`.env` 加载顺序：默认配置 → 用户 exe 同级配置覆盖。

## 结项收口（每轮任务结束前）

- 影响行为的功能/配置，**同步更新** **`README.md`** **与** **`backend/.env.example`**（默认值、开关、白名单）。

- 涉及规则性约定，同步回写本文件，保持本守则与项目一致。

- 习惯小步提交：一个需求一次提交，说明清晰。

- 打包类改动注意 `extraResources` 需要的是单文件 `backend/dist/backend.exe`（`build_backend.py` 已用 `--onefile`）。

