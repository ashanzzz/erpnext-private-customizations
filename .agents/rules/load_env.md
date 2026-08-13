---
description: 强制要求项目内的脚本自动从 .env 文件读取配置
trigger: always_on
---
# 环境变量读取约束 (Environment Variables)

在 `erpnext16` 项目中编写、修改任何独立脚本（如 Python 脚本）时，必须遵守以下规则：
1. **绝对禁止硬编码**任何认证 Token、密码、数据库连接串或环境专属的 URL（如 `ERPNEXT_SITE_URL`）。
2. **必须支持自动读取 `.env`**：在脚本初始化阶段，必须包含读取当前目录下 `.env` 文件的逻辑。例如在 Python 中，必须实现或调用类似于 `load_env_file()` 的方法来将 `.env` 注入到 `os.environ` 中。
3. **优先使用环境变量**：所有敏感或可变的配置参数必须通过 `os.getenv('KEY', 'default')` 的方式获取。
