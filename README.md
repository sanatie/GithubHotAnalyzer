# GitHub 仓库 AI 智能分析器

一个基于 AI 大模型的 GitHub 仓库智能分析与热榜追踪工具。它集**仓库 AI 分析、热榜排行榜、需求驱动 AI 对话推荐、购物车、内置下载管理器、历史与收藏管理**于一体，同时支持 Web 与 Electron 桌面端。

---

## 功能特性

### 仓库分析（核心）
- 输入 GitHub 仓库地址，自动获取仓库数据（Star、Fork、语言、协议等）
- AI 大模型分析 README，生成中文项目报告：
  - 项目摘要、技术栈分析、项目亮点、项目缺点、学习建议、综合评分（0-100 分）
- 缓存机制：已分析过的仓库直接返回缓存结果，支持强制刷新

### 热榜排行榜（Trending）
- 浏览 GitHub 热门项目，支持**今日 / 每周 / 每月**三种时间范围切换
- 按编程语言筛选（Python、JavaScript、C 等）
- 丰富的可视化：语言分布统计、排名变化（↑/↓/新上榜）、汇总数据面板（总 Star、总 Fork、平均 Star、上榜语言数）
- 榜单项目可一键加入购物车、收藏或发起分析

### AI 智能对话（Chat）
- 用自然语言描述需求，AI 自动推荐匹配的 GitHub 项目
- 提供 Prompt 注入检测，识别异常请求
- 对话/推荐记录历史管理（查看、删除、清空）

### 购物车 + 内置下载管理器
- 将感兴趣的项目加入购物车统一管理
- 内置下载器（无需 wget/curl）：支持
  - **源码 ZIP**、**Release 文件**、**README 文档**、**git clone**
- 下载前自动探测仓库的可下载内容（默认分支、ZIP 链接、README、最新 Release）
- **GitHub 加速镜像源**：github.com 直连被墙时可配置镜像前缀（中继 zip/readme 下载也做了 codeload 直链优化）
- 实时进度、下载速度、任务列表、取消 / 删除 / 打开目录

### 历史与收藏
- 历史记录：查看、搜索、单条删除 / 批量删除 / 一键清空，删除时同步删除对应收藏
- 收藏管理：收藏 / 取消收藏、收藏列表、看图报告详情

### 设置功能
- 自定义大模型配置（API Key、API 地址、模型名称），内置通义千问 / DeepSeek / OpenAI 预设
- 提供 AI 配置连通性测试
- 配置持久化保存，关闭不丢失

### 安全扫描
- 对已生成报告的分析结果执行安全扫描（`/security-scan/{report_id}`）

### 桌面端
- 一键开发启动脚本 `start-dev.bat`，自动安装依赖、生成 `.env`、同时拉起前后端
- 打包成独立 `.exe` 桌面应用，自动启动 / 停止后端服务
- Vercel 风格设计，简洁高效

---

## 技术栈

### 后端
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ / 3.13 | 开发语言 |
| FastAPI | 0.104.1 | Web 框架 |
| Uvicorn | 0.24.0 | ASGI 服务器 |
| SQLAlchemy | 2.0.23 | ORM 框架 |
| SQLite + aiosqlite | 内置 | 数据库 |
| Pydantic | 1.10.13 | 数据验证（v1，配合补丁兼容 3.13） |
| httpx | 0.25.2 | 异步 HTTP 客户端 |
| OpenAI SDK | 1.3.7 | AI 大模型调用（兼容通义/DeepSeek） |
| python-dotenv | 1.0.0 | 环境变量加载 |
| loguru | 0.7.2 | 日志库 |
| beautifulsoup4 / markdown | - | README 解析 |

### 前端
| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | 3.3+ | 前端框架 |
| Vite | 5.0 | 构建工具 |
| Element Plus | 2.4 | UI 组件库 |
| Pinia | 2.1 | 状态管理 |
| Vue Router | 4.2 | 路由管理（哈希模式） |
| Axios | 1.6 | HTTP 客户端 |

### 桌面端
| 技术 | 版本 | 用途 |
|------|------|------|
| Electron | 28.0 | 桌面应用框架 |
| electron-builder | 24.9.1 | 打包工具 |
| PyInstaller | - | 后端打包 |

---

## 项目结构

```
Github热榜分析器/
├── start-dev.bat / start-dev.ps1   # 一键开发启动（前端+后端）
├── build-prod.bat / build-prod.ps1 # 一键生产打包
├── README.md                       # 项目文档
│
├── backend/                        # 后端代码
│   ├── app/
│   │   ├── api/                    # API 路由层
│   │   │   ├── analysis.py         # 仓库分析与报告
│   │   │   ├── repositories.py     # 仓库管理
│   │   │   ├── favorites.py        # 收藏
│   │   │   ├── settings.py         # AI 配置
│   │   │   ├── trending.py         # 热榜排行榜
│   │   │   ├── chat.py             # AI 对话推荐
│   │   │   ├── chat_history.py     # 对话历史
│   │   │   └── downloader.py       # 下载任务管理
│   │   ├── services/               # 业务逻辑层
│   │   │   ├── github_service.py   # GitHub API 服务
│   │   │   ├── ai_service.py       # AI 分析服务
│   │   │   ├── repository_service.py
│   │   │   ├── report_service.py
│   │   │   └── downloader_service.py  # 内置下载器（zip/readme/release/clone + 镜像）
│   │   ├── models/                 # 数据库模型
│   │   │   ├── repository.py / report.py / favorite.py
│   │   │   ├── chat_history.py / download_task.py
│   │   ├── schemas/                # Pydantic 数据模型
│   │   ├── config.py               # 配置管理（.env 多路径加载）
│   │   ├── database.py             # 数据库连接
│   │   ├── main.py                 # FastAPI 应用入口
│   │   └── __init__.py
│   ├── run.py                      # 启动脚本（含 Pydantic 补丁）
│   ├── run_backend.bat             # 后端启动（供 start-dev 调用）
│   ├── scripts/                    # 打包脚本
│   │   ├── pydantic_patch.py       # Python 3.13 兼容补丁
│   │   ├── backend.spec            # PyInstaller 配置
│   │   └── build_backend.py        # 后端打包入口
│   ├── requirements.txt
│   ├── .env / .env.example         # 环境变量配置
│   └── tests/
│
├── frontend/                       # 前端代码
│   ├── src/
│   │   ├── views/                  # 页面
│   │   │   ├── Home.vue            # 首页（仓库分析）
│   │   │   ├── Trending.vue        # 热榜排行榜
│   │   │   ├── Chat.vue            # AI 对话推荐
│   │   │   ├── Cart.vue            # 购物车 + 下载管理器
│   │   │   ├── History.vue         # 历史记录
│   │   │   ├── Favorites.vue       # 收藏
│   │   │   └── Settings.vue        # 设置
│   │   ├── layouts/Layout.vue      # 主布局
│   │   ├── components/             # 公共组件（RepoCard、ScorePanel 等）
│   │   ├── router/index.js         # 路由（哈希模式）
│   │   ├── stores/                 # Pinia（cart.js / repoStore.js）
│   │   ├── api/index.js            # API 封装
│   │   ├── utils/request.js        # Axios 实例
│   │   └── assets/ styles/         # 静态资源与样式
│   ├── electron/                   # Electron 主进程（main.js / preload.js）
│   ├── package.json / vite.config.js
│   └── dist-electron/              # 最终打包输出
└── downloads/                      # 默认下载目录（运行时自动创建）
```

---

## 快速开始

### 环境要求
- Python 3.10+（3.13 亦可）
- Node.js 16+、npm

### 方式一：一键启动（推荐）

在项目根目录双击运行 `start-dev.bat`：

1. 自动检测 Python / Node.js
2. 自动安装 Python 依赖（`requirements.txt`）与前端依赖（无 `node_modules` 时）
3. 若 `backend/.env` 不存在，自动从 `.env.example` 生成
4. 同时启动后端（端口 8000）与前端（端口 5173），并自动打开浏览器
5. 关闭该窗口即停止前后端服务

### 方式二：手动启动

**后端**

```bash
cd backend
pip install -r requirements.txt
# 编辑 .env，填入 AI API 配置（参考 .env.example）
python run.py
```

后端服务将在 `http://localhost:8000` 启动，API 文档：`http://localhost:8000/docs`

**前端**

```bash
cd frontend
npm install
npm run dev        # 开发模式，默认 http://localhost:5173
npm run build      # 生产构建
```

**桌面开发模式**

```bash
cd frontend
npm run electron:dev   # 需先启动后端
```

### 环境变量（backend/.env）

参考 [.env.example](backend/.env.example)，常用项：

| 变量 | 说明 |
|------|------|
| `AI_API_KEY` | AI 大模型 API Key（通义/DeepSeek/OpenAI 任选其一） |
| `AI_API_BASE_URL` | 兼容 OpenAI 协议的接口地址 |
| `AI_MODEL` | 模型名，如 `qwen-plus` / `deepseek-chat` |
| `GITHUB_TOKEN` | 可选，GitHub Token，提高 API 限流配额 |
| `GITHUB_VERIFY_SSL` | 可选，默认 `true`，GitHub API 及下载请求是否校验 TLS 证书 |
| `GITHUB_CLONE_MIRROR` | 可选，git clone 默认镜像前缀 |
| `GITHUB_CLONE_MIRRORS` | 可选，逗号分隔的镜像回退列表（直连失败后依次尝试） |
| `AI_VERIFY_SSL` | 可选，默认 `true`，AI 请求是否校验 TLS 证书 |
| `AI_BASE_ALLOWLIST` | 可选，AI 服务官方域名白名单（逗号分隔）；**整体覆盖**内置默认，见下方安全加固 |
| `AI_STRICT_BASE` | 可选，默认 `true`，AI base url 必须命中白名单且禁止纯 IP/内网 |

> 镜像前缀填法：形如 `https://ghfast.top/https://github.com`；也可在下载对话框中按仓库单独填写。
> 安全开关的默认值与完整说明见 [安全加固](#安全加固) 章节，示例见 [.env.example](backend/.env.example)。

---

## 部署打包

### 一键打包（推荐）

在项目根目录运行 `build-prod.bat`，依次自动完成：

1. **后端**：PyInstaller 打包 `backend/dist/backend.exe`
2. **前端**：Vite 构建 `frontend/dist/`
3. **桌面端**：electron-builder 打包 `frontend/dist-electron/`

### 分步打包

**后端**

```bash
cd backend
python scripts\build_backend.py     # 或 pyinstaller scripts\backend.spec
```

**前端 + Electron**

```bash
cd frontend
npm run build
npm run electron:build:win
```

---

## 运行测试

后端使用 [pytest](https://docs.pytest.org/) 编写自动化单元测试，目前覆盖下载器的
URL 构造 / 安全校验 / 镜像拼接 / SSH 通道等纯函数逻辑。

```bash
cd backend
# 若新环境尚未安装依赖，先安装（requirements.txt 已含 pytest）
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
# 运行全部测试
python -m pytest tests -q
```

> 测试不联网、不触碰真实数据库与 `~/.ssh`（通过 monkeypatch 隔离），可放心本地反复执行。
> 新增各"下载链接构造 / 安全白名单"类逻辑时，建议在 `backend/tests/test_downloader_service.py`
> 中同步补充用例，防止回归。

---

## 踩坑记录

> 这是本项目最有价值的部分，记录了开发过程中遇到的主要坑和解决方案。

### 1. Python 3.13 与 Pydantic v1 兼容问题

**现象**：`TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'`

**原因**：Python 3.13 修改了 `typing.ForwardRef._evaluate` 签名，Pydantic v1 未适配。

**解决**：`scripts/pydantic_patch.py` 猴子补丁，在 `run.py` 入口首先导入；打包时通过 `pyi_rth_pydantic_fix.py` 保证 exe 内同样生效。

### 2. Electron 页面空白（路由模式）

**现象**：桌面端打开空白，`net::ERR_FILE_NOT_FOUND`。

**原因**：`createWebHistory()` 依赖浏览器 history API，`file://` 协议下无服务器处理路由。

**解决**：改用 `createWebHashHistory()`（[router/index.js](frontend/src/router/index.js)）。

### 3. PyInstaller 后 .env 读取不到

**现象**：打包成 exe 后 AI API Key 为空。

**解决**：[config.py](backend/app/config.py) 支持多路径加载 `.env`：`_MEIPASS` 默认配置 → exe 同级用户配置（`override=True`）→ 当前目录，并打包 `.env` 进 `datas`。

### 4. AI 配置无法持久化

**原因**：`_load_env()` 先从 `_MEIPASS` 加载后就返回，用户配置不生效。

**解决**：先加载默认配置，再用 `load_dotenv(user_env, override=True)` 覆盖用户配置。

### 5. 关键指标显示 0（字段名不匹配）

**原因**：后端自定义字段名（`stars`）与前端期望的 GitHub API 字段名（`stargazers_count`）不一致。

**解决**：统一使用 GitHub API 原生字段命名。经验：尽量复用第三方 API 字段名，避免转换出错。

### 6. GitHub API SSL 证书错误

**现象**：`SSL: CERTIFICATE_VERIFY_FAILED`。

**解决**：httpx 客户端 `verify=False`（仅开发环境）。

### 7. GitHub API 301 重定向

**现象**：请求返回 301 且内容为空。

**解决**：httpx 开启 `follow_redirects=True`。

### 8. API baseURL 在 Electron 中解析错误

**现象**：`file:///localhost:8000/api/...`。

**解决**：`request.js` 中写死完整地址 `http://localhost:8000/api`。

### 9. Pydantic 不能直接接收 SQLAlchemy 对象

**解决**：返回前先转为字典，或使用 `from_orm` / `from_attributes`。

### 10. 同步删除收藏

删除历史记录时按 `repo_full_name` 关联同步删除对应收藏，覆盖单删 / 批量 / 清空三个入口。

### 11. 内置下载器下载失败（本网络 github.com 直连被墙）

**现象**：下载源码报 `All connection attempts failed`。

**原因**：`github.com/.../archive` 链接在本网络直连超时，而 `codeload.github.com` 可直连。

**解决**（[downloader_service.py](backend/app/services/downloader_service.py)）：
1. 将 `github.com/{o}/{r}/archive/...zip` 规范化为 `codeload.github.com` 直链
2. 流式请求加 `Accept-Encoding: identity`，否则 httpx 自动解压会导致字节数 > content-length、**进度超过 100%**
3. 提供镜像源方案：`apply_mirror()` 拼接镜像前缀，`.env` 配置 `GITHUB_CLONE_MIRROR(S)`；clone 直连失败时按序回退并清理残留目录

---

## 安全加固

对项目涉及的敏感凭据（GitHub Token、AI API Key、SSH 私钥）做了系统性防护，防止泄露给镜像、代理或第三方中转服务。

### 1. GitHub Token —— 域名白名单 + 请求层纵深防御

- **`_get_headers(url)` 白名单守卫**：仅在请求目标为 GitHub 官方 API（`api.github.com`，含子域）时才附加 `Authorization: token ...`；目标为其它域名时拒绝附加并告警。
- **`_request_with_retry` 请求层兜底**：无论调用方是否显式传 url，只要请求 host 非官方，就剥离 `Authorization` 并告警——覆盖现在和未来的所有调用点。
- **`GITHUB_VERIFY_SSL`**（默认开启）：GitHub API 及下载请求校验 TLS 证书，防止携带 Token 的请求被劫持、下载内容被中间人篡改。
- 下载路径（ZIP / README / Release / git clone）使用**不带 token** 的自定义 header 或 git/SSH 通道，绝不携带 GitHub Token 到 codeload 或第三方镜像。

### 2. AI API Key —— 官方域名白名单 + TLS 校验

- **`AI_BASE_ALLOWLIST`**：内置 23 个国内外主流 AI 服务商官方域名（DeepSeek、阿里百炼、OpenAI、Claude、Gemini 等）。AI Key 仅发往白名单内的官方域名，其它域名、纯 IP 地址、内网地址一律拒绝，防止 Key 被引导到不可信主机。
- **`AI_VERIFY_SSL`**（默认开启）：所有 AI 请求均校验 TLS 证书。
- **`AI_STRICT_BASE`**（默认开启）：显式关闭方可放行任意地址（不推荐）。
- 附录：腾讯混元等未内置的官方域名，可在 `.env` 的 `AI_BASE_ALLOWLIST` **整体覆盖** 追加（会替换默认），需写全实际使用的域名。

### 3. SSH 私钥 —— 安全存放

- 下载管理器的 SSH-over-443 备用通道使用 `ed25519` 密钥对。**私钥必须存放在系统标准目录 `~/.ssh/`**（不随 OneDrive 同步），**不得**放在项目目录或被明文提交。
- 公钥可公开（用于 `~/.ssh/id_ed25519.pub` 添加到 GitHub），迁移私钥不改变公钥指纹，无需重复添加。
- Key 探测顺序：优先 `~/.ssh`（`id_ed25519` / `id_rsa` / `id_ecdsa`）→ 环境变量 → 项目兜底。

### 4. 通用防护

- 下载 URL 白名单：仅允许 GitHub 相关官方域名（`github.com` / `codeload` / `raw` / `api` / `objects` / `release-assets`），防 SSRF 与路径注入。
- 设置接口对 API Key **脱敏返回**（`aabb******efef`），不回显明文。
- 镜像源可配置且**不硬编码为默认**，避免私自使用不可靠的第三方镜像。

---

## API 接口列表

所有接口前缀：`/api/v1`，Base URL：`http://localhost:8000/api/v1`

### 仓库分析与报告
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /analysis/repositories | 分析 GitHub 仓库 |
| GET | /analysis/reports | 报告列表 |
| GET | /analysis/reports/{report_id} | 报告详情 |
| DELETE | /analysis/reports/{report_id} | 删除报告 |
| POST | /analysis/reports/batch-delete | 批量删除报告 |
| DELETE | /analysis/reports | 清空所有报告 |
| POST | /analysis/security-scan/{report_id} | 报告安全扫描 |

### 仓库
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /repositories | 仓库列表 |
| GET | /repositories/{repo_id} | 仓库详情 |
| GET | /repositories/by-name/{full_name} | 按全名查仓库 |
| GET | /repositories/search | 搜索仓库 |

### 收藏
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /favorites | 收藏列表 |
| POST | /favorites | 添加收藏 |
| PUT | /favorites/{fav_id} | 更新收藏 |
| DELETE | /favorites/{fav_id} | 删除收藏 |
| GET | /favorites/check/{repo_id} | 检查是否已收藏 |

### 设置
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /settings/ai | 获取 AI 配置 |
| PUT | /settings/ai | 更新 AI 配置 |
| POST | /settings/ai/test | 测试 AI 配置连通性 |

### 热榜排行榜
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /trending?language=&since=&limit= | 获取热门项目（since: daily/weekly/monthly，limit≤50） |

### AI 对话
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /chat/recommend | 按需求推荐项目 |
| GET | /chat/history | 对话历史 |
| DELETE | /chat/history/{record_id} | 删除单条 |
| DELETE | /chat/history | 清空历史 |

### 下载管理器
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /download/probe/{author}/{repository} | 探测项目可下载内容 |
| POST | /download | 创建下载任务（zip/release/readme/gitclone） |
| GET | /download | 任务列表（分页） |
| POST | /download/{task_id}/cancel | 取消任务 |
| DELETE | /download/{task_id} | 删除任务 |
| POST | /download/{task_id}/open-dir | 打开任务目录 |
| GET | /download/default-dir | 获取默认下载目录 |

### 其他
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /health | 健康检查 |

---

## 数据库设计

### repositories（仓库表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| github_id | Integer | GitHub ID |
| full_name | String | 仓库全名（owner/name） |
| description | Text | 描述 |
| language | String | 主要语言 |
| stargazers_count | Integer | Star 数 |
| forks_count | Integer | Fork 数 |
| watchers_count | Integer | 关注者数 |
| open_issues_count | Integer | 未解决 Issues 数 |
| license / default_branch / homepage | String | 协议 / 默认分支 / 主页 |
| avatar_url / html_url | String | 头像 / GitHub 地址 |
| created_at / updated_at | DateTime | 时间戳 |

### reports（报告表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| repo_id | Integer | 关联仓库 ID |
| repo_full_name | String | 仓库全名 |
| summary | Text | 摘要 |
| tech_stack | Text | 技术栈（JSON） |
| highlights / drawbacks | Text | 亮点 / 缺点（JSON） |
| learning_advice | Text | 学习建议 |
| score | Float | 综合评分 |
| score_breakdown | Text | 评分细分（JSON） |
| language | String | 报告语言 |
| created_at | DateTime | 创建时间 |

### favorites（收藏表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| repo_id | Integer | 关联仓库 ID（唯一） |
| repo_full_name | String | 仓库全名 |
| note | String | 备注 |
| created_at | DateTime | 创建时间 |

### chat_history（对话历史表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| query | String | 用户需求描述 |
| items | Text | AI 推荐项目列表（JSON） |
| total | Integer | 推荐数量 |
| injection_detected | Boolean | 是否检测到 Prompt 注入 |
| created_at | DateTime | 对话时间 |

### download_tasks（下载任务表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| author / repository | String | 作者 / 仓库 |
| content_type | String | zip / release / readme / gitclone |
| save_dir | String | 保存目录 |
| url | String | 下载地址（clone 时为镜像/远程地址） |
| filename | String | 保存文件名 |
| total_size / downloaded / speed | Float | 总大小 / 已下载 / 速度 |
| status | String | pending/downloading/completed/failed/cancelled |
| error | String | 错误信息 |
| proc_id | String | 子进程 ID（用于取消） |
| created_at / finished_at | DateTime | 时间戳 |

> 说明：热榜排行榜（Trending）不落库，直接调用 GitHub Search API 实时获取。

---

## 许可证

MIT License

---

## P.S.

> PS:大二菜鸡使用ds-v4-flash+trae平台开发的一个工具，由于只系统学了部分的后端技术所以运行可能会出现bug（绝大部分的问题开发中均已排除，若有可提交issue，可能会修的吧(๑´ڡ`๑)），后续会逐步完善功能并更新