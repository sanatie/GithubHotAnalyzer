# GitHub 仓库 AI 智能分析器

一个基于 AI 大模型的 GitHub 仓库智能分析工具，输入仓库地址即可自动获取仓库数据并生成中文项目分析报告。

## 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [部署打包](#部署打包)
- [踩坑记录](#踩坑记录)

---

## 功能特性

### 核心功能
- **仓库分析**：输入 GitHub 仓库地址，自动获取仓库数据（Star、Fork、语言、协议等）
- **AI 智能分析**：使用大模型分析 README，生成中文项目报告，包含：
  - 项目摘要
  - 技术栈分析
  - 项目亮点
  - 项目缺点
  - 学习建议
  - 综合评分（0-100 分）
- **缓存机制**：已分析过的仓库直接返回缓存结果，支持强制刷新

### 历史记录
- 查看所有分析历史
- 按仓库名搜索
- 单条删除 / 批量删除 / 一键清空
- 删除历史时同步删除对应收藏

### 收藏管理
- 收藏/取消收藏仓库
- 收藏列表管理
- 快速查看报告详情

### 设置功能
- 支持自定义大模型配置（API Key、API 地址、模型名称）
- 内置通义千问、DeepSeek、OpenAI 预设
- 配置持久化保存，关闭应用不丢失

### 桌面应用
- 打包成独立 `.exe` 文件，开箱即用
- 自动启动/停止后端服务
- Vercel 设计风格，简洁高效

---

## 技术栈

### 后端
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.13 | 开发语言 |
| FastAPI | 0.104.1 | Web 框架 |
| Uvicorn | 0.24.0 | ASGI 服务器 |
| SQLAlchemy | 2.0.23 | ORM 框架 |
| SQLite | 内置 | 数据库 |
| Pydantic | 1.10.13 | 数据验证（v1 版本） |
| httpx | 0.25.2 | 异步 HTTP 客户端 |
| OpenAI SDK | 1.3.7 | AI 大模型调用 |
| python-dotenv | 1.0.0 | 环境变量加载 |
| loguru | 0.7.2 | 日志库 |

### 前端
| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | 3.3+ | 前端框架 |
| Vite | 5.0 | 构建工具 |
| Element Plus | 2.4 | UI 组件库 |
| Pinia | 2.1 | 状态管理 |
| Vue Router | 4.2 | 路由管理 |
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
├── backend/                     # 后端代码
│   ├── app/
│   │   ├── models/              # 数据库模型
│   │   │   ├── repository.py    # 仓库模型
│   │   │   ├── report.py        # 报告模型
│   │   │   └── favorite.py      # 收藏模型
│   │   ├── schemas/             # Pydantic 数据模型
│   │   │   ├── repository.py
│   │   │   ├── report.py
│   │   │   ├── analysis.py
│   │   │   ├── favorite.py
│   │   │   └── settings.py
│   │   ├── services/            # 业务逻辑层
│   │   │   ├── github_service.py    # GitHub API 服务
│   │   │   ├── ai_service.py        # AI 分析服务
│   │   │   ├── repository_service.py # 仓库服务
│   │   │   └── report_service.py    # 报告服务
│   │   ├── routes/              # API 路由
│   │   │   ├── analysis.py      # 分析相关接口
│   │   │   ├── repositories.py  # 仓库相关接口
│   │   │   ├── favorites.py     # 收藏相关接口
│   │   │   └── settings.py      # 设置相关接口
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # 数据库连接
│   │   └── main.py              # FastAPI 应用入口
│   ├── run.py                   # 启动脚本（含 Pydantic 补丁）
│   ├── pydantic_patch.py        # Python 3.13 兼容性补丁
│   ├── backend.spec             # PyInstaller 打包配置
│   ├── requirements.txt         # Python 依赖
│   └── .env                     # 环境变量配置
│
├── frontend/                    # 前端代码
│   ├── src/
│   │   ├── views/               # 页面组件
│   │   │   ├── Home.vue         # 首页（分析页面）
│   │   │   ├── History.vue      # 历史记录页
│   │   │   ├── Favorites.vue    # 收藏页
│   │   │   └── Settings.vue     # 设置页
│   │   ├── layouts/             # 布局组件
│   │   │   └── Layout.vue       # 主布局
│   │   ├── components/          # 公共组件
│   │   ├── router/              # 路由配置
│   │   ├── stores/              # Pinia 状态管理
│   │   ├── api/                 # API 封装
│   │   ├── utils/               # 工具函数
│   │   ├── assets/              # 静态资源
│   │   └── App.vue
│   ├── electron/                # Electron 主进程
│   │   ├── main.js              # 主进程入口
│   │   └── preload.js           # 预加载脚本
│   ├── dist-electron-final/     # 最终打包输出
│   └── package.json
│
└── README.md                    # 项目文档
```

---

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 16+
- npm 或 yarn

### 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
# 复制 .env 文件并填入你的 AI API 配置
# AI_API_KEY=your_api_key
# AI_API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# AI_MODEL=qwen-plus

# 启动服务
python run.py
```

后端服务将在 `http://localhost:8000` 启动，API 文档地址：`http://localhost:8000/docs`

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build
```

前端开发服务器默认在 `http://localhost:5173` 启动

### 桌面应用开发模式

```bash
cd frontend

# 先确保后端服务已启动
# 然后启动 Electron
npm run electron:dev
```

---

## 部署打包

### 后端打包（PyInstaller）

```bash
cd backend

# 安装 PyInstaller
pip install pyinstaller

# 使用 spec 文件打包
pyinstaller backend.spec
```

打包产物：`backend/dist/backend.exe`

### 前端打包 + Electron 打包

```bash
cd frontend

# 构建前端
npm run build

# 打包 Electron 应用
npm run electron:build:win
```

打包产物：`frontend/dist-electron-final/win-unpacked/`

### 手动整合（推荐）

1. 先用 PyInstaller 打包后端得到 `backend.exe`
2. 前端执行 `npm run build` 得到 `dist/` 目录
3. 手动创建 Electron 目录结构：
   - `app/dist/` - 前端构建产物
   - `app/electron/main.js` - 主进程
   - `app/electron/preload.js` - 预加载脚本
4. 用 `asar` 工具打包成 `app.asar`
5. 创建最终目录结构：
   - `resources/app.asar` - 前端代码
   - `resources/backend.exe` - 后端服务
   - `resources/github_analyzer.db` - 数据库（可选）
6. 放入 Electron 的 win-unpacked 目录中

---

## 踩坑记录

> 这是本项目最有价值的部分，记录了开发过程中遇到的所有坑和解决方案。

### 1. Python 3.13 与 Pydantic v1 兼容性问题

**现象**：
```
TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'
```

**原因**：
Python 3.13 更新了 `typing.ForwardRef._evaluate` 方法的签名，新增了 `recursive_guard` 参数，但 Pydantic v1 没有适配。

**解决方案**：
创建猴子补丁 `pydantic_patch.py`，在启动时给 `_evaluate` 方法添加默认参数：

```python
import sys

if sys.version_info >= (3, 13):
    from typing import ForwardRef

    _orig_evaluate = ForwardRef._evaluate

    def _patched_evaluate(self, *args, **kwargs):
        if "recursive_guard" not in kwargs:
            kwargs["recursive_guard"] = set()
        return _orig_evaluate(self, *args, **kwargs)

    ForwardRef._evaluate = _patched_evaluate
```

在入口文件 `run.py` 中首先导入这个补丁。

**相关文件**：
- [pydantic_patch.py](backend/pydantic_patch.py)
- [run.py](backend/run.py)

---

### 2. Electron 页面空白（路由模式问题）

**现象**：
打包成桌面应用后打开是空白页面，开发者工具里显示 `net::ERR_FILE_NOT_FOUND`。

**原因**：
Vue Router 默认使用 `createWebHistory()`（HTML5 History 模式），这种模式依赖浏览器的 history API。但在 Electron 中使用 `file://` 协议加载本地文件，没有服务器来处理路由重定向，导致页面找不到。

**解决方案**：
将路由模式改为 `createWebHashHistory()`（哈希模式），使用 URL 的 hash 部分来管理路由：

```javascript
// router/index.js
import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory(),  // 改成这个
  routes: [...]
})
```

**相关文件**：
- [frontend/src/router/index.js](frontend/src/router/index.js)

---

### 3. PyInstaller 打包后 .env 文件无法读取

**现象**：
打包成 `backend.exe` 后，AI API 调用失败，日志显示 API Key 为空。但直接用 Python 运行是正常的。

**原因**：
PyInstaller 打包后，程序运行在一个临时目录（`_MEIPASS`）中，`python-dotenv` 默认在当前工作目录找 `.env` 文件，找不到。

**解决方案**：
修改 `config.py`，支持从多个位置加载 `.env` 文件：
1. PyInstaller 的 `_MEIPASS` 临时目录（打包进去的默认配置）
2. exe 文件所在目录（用户自定义配置）
3. 当前工作目录

```python
def _get_env_path():
    """获取 .env 文件路径，支持 PyInstaller 打包"""
    import sys
    import os
    
    # 优先级1：exe 同级目录（用户配置）
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        env_path = os.path.join(exe_dir, '.env')
        if os.path.exists(env_path):
            return env_path
    
    # 优先级2：PyInstaller 临时目录（默认配置）
    if hasattr(sys, '_MEIPASS'):
        env_path = os.path.join(sys._MEIPASS, '.env')
        if os.path.exists(env_path):
            return env_path
    
    # 优先级3：当前目录（开发模式）
    return '.env'
```

同时在 `backend.spec` 中将 `.env` 添加到 `datas` 中打包进 exe。

**相关文件**：
- [config.py](backend/app/config.py)
- [backend.spec](backend/backend.spec)

---

### 4. AI 配置无法持久化保存

**现象**：
在设置页面修改了 API Key 并保存，关闭应用后再打开，又变回原来的值了。

**原因**：
`_load_env()` 函数先从 `_MEIPASS`（默认配置）加载，找到后就返回了，不会再加载 exe 同级目录的用户配置。`dotenv.load_dotenv` 默认不会覆盖已存在的环境变量，导致用户配置不生效。

**解决方案**：
修改加载逻辑，先加载默认配置，再加载用户配置并覆盖：

```python
def _load_env():
    """加载 .env 文件，用户配置覆盖默认配置"""
    import sys
    import os
    from dotenv import load_dotenv
    
    # 先加载默认配置（_MEIPASS 中）
    if hasattr(sys, '_MEIPASS'):
        default_env = os.path.join(sys._MEIPASS, '.env')
        if os.path.exists(default_env):
            load_dotenv(default_env)
    
    # 再加载用户配置（exe 同级目录），覆盖默认值
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        user_env = os.path.join(exe_dir, '.env')
        if os.path.exists(user_env):
            load_dotenv(user_env, override=True)  # 关键：override=True
```

**相关文件**：
- [config.py](backend/app/config.py)

---

### 5. 关键指标无显示（字段名不匹配）

**现象**：
分析完成后，首页的关键指标（Stars、Forks、关注者、Issues）全部显示为 0，但报告内容是正常的。

**原因**：
后端返回的 `repository` 字段中使用的字段名和前端期望的不一致：
- 后端：`stars`、`forks`、`watchers`、`open_issues`
- 前端：`stargazers_count`、`forks_count`、`watchers_count`、`open_issues_count`

前端 `formattedReport` 读取的是 GitHub API 原生字段名，后端自定义的字段名不匹配。

**解决方案**：
统一后端返回的字段名，使用与 GitHub API 一致的命名：
- `stars` → `stargazers_count`
- `forks` → `forks_count`
- `watchers` → `watchers_count`
- `open_issues` → `open_issues_count`

**经验总结**：
前后端字段命名要统一，最好直接复用第三方 API 的字段名，避免转换出错。

**相关文件**：
- [analysis.py](backend/app/routes/analysis.py)

---

### 6. GitHub API SSL 证书错误

**现象**：
```
SSL: CERTIFICATE_VERIFY_FAILED - unable to get local issuer certificate
```

**原因**：
某些网络环境下，SSL 证书验证失败（可能是代理、防火墙或证书问题）。

**解决方案**：
在 httpx 客户端配置中添加 `verify=False` 跳过证书验证（仅限开发环境，生产环境不建议）：

```python
client = httpx.AsyncClient(verify=False, follow_redirects=True)
```

或者配置正确的 CA 证书路径。

---

### 7. GitHub API 301 重定向

**现象**：
请求 GitHub API 返回 301 状态码，但内容为空。

**原因**：
GitHub API 某些端点会重定向，httpx 默认不跟随重定向。

**解决方案**：
在 httpx 客户端配置中启用自动跟随重定向：

```python
client = httpx.AsyncClient(follow_redirects=True)
```

---

### 8. API baseURL 路径问题

**现象**：
Electron 应用中 API 请求失败，URL 变成了 `file:///localhost:8000/api/...`。

**原因**：
前端 axios 的 baseURL 配置为相对路径 `/api`，在 `file://` 协议下，相对路径会基于文件路径解析，而不是基于 HTTP 地址。

**解决方案**：
将 baseURL 固定为完整的 HTTP 地址：

```javascript
// api/request.js
const request = axios.create({
  baseURL: 'http://localhost:8000/api',  // 写死完整地址
  timeout: 30000
})
```

---

### 9. Pydantic 不能直接接收 SQLAlchemy 模型对象

**现象**：
```
AttributeError: 'Report' object has no attribute 'dict'
```

**原因**：
Pydantic v2 的 `model_validate` 不能直接接收 SQLAlchemy 的 ORM 对象，需要先转成字典。（本项目用的是 Pydantic v1，v1 可以用 `from_orm`，但某些场景也会有问题）

**解决方案**：
在返回响应前，先将 SQLAlchemy 对象转换为字典：

```python
# 方法1：手动转字典
def to_dict(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

# 方法2：Pydantic v1 使用 from_orm
ReportResponse.from_orm(report_obj)

# 方法3：SQLAlchemy 2.0 使用 obj._asdict()（仅限于 Query 结果）
```

---

### 10. 同步删除收藏的逻辑设计

**需求**：
删除历史记录时，对应的收藏也应该被删除。

**实现思路**：
在报告删除的三个入口处都加上同步删除收藏的逻辑：
1. 单条删除 `delete_report()`
2. 批量删除 `delete_reports_batch()`
3. 一键清空 `delete_all_reports()`

通过 `repo_full_name` 关联报告和收藏，删除报告时根据仓库全名查找并删除对应的收藏记录。

**关键代码**：
```python
def delete_report(db: Session, report_id: int) -> bool:
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return False
    
    repo_full_name = report.repo_full_name
    db.delete(report)
    
    # 同步删除收藏
    fav = db.query(Favorite).filter(
        Favorite.repo_full_name == repo_full_name
    ).first()
    if fav:
        db.delete(fav)
    
    db.commit()
    return True
```

**相关文件**：
- [report_service.py](backend/app/services/report_service.py)

---

### 11. Electron 主进程启动后端服务

**关键点**：
1. 后端 exe 放在 `resources/backend.exe`
2. 使用 `child_process.spawn` 启动
3. 应用退出时要杀掉后端进程
4. 注意路径处理，开发环境和生产环境路径不同

**简化示例**：
```javascript
const { spawn } = require('child_process')
const path = require('path')

let backendProcess = null

function startBackend() {
  const isDev = process.env.NODE_ENV === 'development'
  const backendPath = isDev
    ? path.join(__dirname, '../../backend/dist/backend.exe')
    : path.join(process.resourcesPath, 'backend.exe')
  
  backendProcess = spawn(backendPath, [], {
    stdio: 'ignore',
    detached: false
  })
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill()
    backendProcess = null
  }
}

app.on('before-quit', () => {
  stopBackend()
})
```

**相关文件**：
- [main.js](frontend/electron/main.js)

---

### 12. app.asar 手动打包的目录结构

**现象**：
手动用 `asar` 打包 `app.asar` 后，页面空白。

**原因**：
目录结构不对。`main.js` 中加载的是 `dist/index.html`，但打包时把 `index.html` 直接放在了根目录。

**正确的目录结构**：
```
app/
├── dist/
│   ├── index.html
│   └── assets/
│       ├── index-xxx.js
│       └── index-xxx.css
└── electron/
    ├── main.js
    └── preload.js
```

`main.js` 中的加载路径：
```javascript
mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
```

打包命令：
```bash
asar pack app app.asar
```

---

## API 接口列表

所有接口前缀：`/api`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /分析/仓库 | 分析 GitHub 仓库 |
| GET | /分析/报告/{id} | 获取报告详情 |
| GET | /仓库 | 获取仓库列表 |
| GET | /仓库/{id} | 获取仓库详情 |
| GET | /报告 | 获取报告列表 |
| DELETE | /报告/{id} | 删除报告 |
| POST | /报告/批量删除 | 批量删除报告 |
| DELETE | /报告全部 | 清空所有报告 |
| GET | /收藏 | 获取收藏列表 |
| POST | /收藏 | 添加收藏 |
| DELETE | /收藏/{id} | 删除收藏 |
| GET | /设置/ai配置 | 获取 AI 配置 |
| PUT | /设置/ai配置 | 更新 AI 配置 |

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
| license | String | 开源协议 |
| default_branch | String | 默认分支 |
| homepage | String | 主页 |
| avatar_url | String | 头像 URL |
| html_url | String | GitHub 地址 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### reports（报告表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| repo_id | Integer | 关联仓库 ID |
| repo_full_name | String | 仓库全名 |
| summary | Text | 摘要 |
| tech_stack | Text | 技术栈（JSON） |
| highlights | Text | 亮点（JSON） |
| drawbacks | Text | 缺点（JSON） |
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

---

## 许可证

MIT License
