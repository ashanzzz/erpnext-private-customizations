# 本地开发与现场验收工作流 (Local Dev & Hot-Sync Workflow)

在 `erpnext16` 项目中进行任何功能修改、Bug 修复或 UI 调整时，必须严格遵守以下工作流程：

1. **本地修改 (Local Edits)**：
   - 所有的代码编写（Python 控制器、JS 脚本、DocType、Workspace JSON 等）均在本地工程中完成。
2. **极速热同步 (Direct Hot-Sync)**：
   - 本地修改完成后，**绝对禁止先推送 GitHub**，而是直接运行自动化热同步与验收一体化脚本：
     ```bash
     python dev_sync_and_verify.py
     ```
     或（涉及数据库字段结构变更时）：
     ```bash
     python dev_sync_and_verify.py --migrate
     ```
   - 脚本会自动通过 SFTP 将修改直传到 Unraid 宿主机，通过 `docker cp` 注入 `erpnext16` 容器，完成 `bench build`、`bench clear-cache` 并重启容器。
3. **AI 内置浏览器全真验收 (Live Browser Acceptance)**：
   - 同步完成后，脚本会自动调用 Playwright 内置无头浏览器访问 `http://192.168.8.11:6888/desk`。
   - 进行全真模拟点击、检查 SPA 路由、检查 DOM 状态并生成最新现场截图。
   - 将测试截图与结果直观汇报给用户进行确认验收。
4. **用户确认后再推送 GitHub (Git Push on Acceptance)**：
   - 只有在现场验收无误且用户确认后，才执行 `git commit` 和 `git push` 将修改推送到 GitHub 远程仓库进行代码归档。
