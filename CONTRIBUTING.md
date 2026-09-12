# 贡献指南

感谢你对本项目的兴趣！这是一个个人维护的开源工具，欢迎任何形式的贡献：提 Bug、提需求、改进文档、修代码。

## 开发环境

按 [README](README.md) 的"快速开始"搭好环境即可：

- Python 3.10+ / 3.13（本项目基于 3.13 开发）
- Node.js 16+ / npm
- 在 `backend/.env` 配置 AI API Key，参考 `backend/.env.example`

## 提 Bug / 提需求

- 在 [Issues](https://github.com/sanatie/GithubHotAnalyzer/issues) 新建 issue，尽量包含：
  - **复现步骤**、期望结果、实际结果
  - 前端/后端日志、报错原文、浏览器/控制台截图
  - 你的运行方式（`start-dev.bat`、手动、Electron 打包版）

> 说明：作者是学生，精力有限，Bug 不保证立即修复，但会尽量尽快处理。

## 提交代码

1. Fork 本仓库并 clone 到本地。
2. 新建分支：`git checkout -b feature/你的改动`。
3. 改动完成后**自测通过**：
   ```bash
   # 后端
   cd backend
   ..\.venv\Scripts\python.exe -m pytest tests -q
   ```
4. Commit 提交信息建议写明"做了什么 + 为什么"。
5. Push 后向 `main` 发起 Pull Request，在描述里说明改动点。

## 编码规范与注意

- **不要提交敏感信息**：`.env`、SSH 私钥、Token 一律不提交（`.gitignore` 已排除，提交前用 `git status` 再核对一遍）。
- **Python 3.13 兼容**：后端基于 3.13，改动注意 Pydantic v1 补丁（`backend/scripts/pydantic_patch.py`）是否仍需要同步适配。
- **下载链接 / 安全白名单类逻辑**：必须在 `backend/tests/test_downloader_service.py` 补对应用例，防止回归。
- **新增下载源或 DNS/域名相关入口**：遵循 README"安全加固"章节的白名单原则。