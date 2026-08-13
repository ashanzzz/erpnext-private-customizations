# ERPNext 16 项目核心映射与约束 (PROJECT_MAP.md)

> **⚠️ 核心修改原则与关联仓库声明**
> 本文件记录了本项目的核心 App 标识、GitHub 远程仓库关联、Docker 构建仓库以及 Unraid 运维部署接口。AI 助手与开发人员在执行任何代码修改或部署指令前，必须优先读取并遵守本声明，防止改错目录或项目。

---

## 📌 1. 核心 App 标识与修改对象

- **App 模块标识 (Python & Frappe App Name)**: `ashan_cn_procurement`
- **App 标题 (Title)**: `业务扩展` (ERPNext 16 采购、报销、油卡与受限单据业务扩展)
- **App 核心代码目录**: `ashan_cn_procurement/ashan_cn_procurement`
- **入口 Hooks**: `ashan_cn_procurement/ashan_cn_procurement/hooks.py`
- **安装包元数据**: `ashan_cn_procurement/pyproject.toml`

---

## 🌐 2. 远程 GitHub 仓库映射

### 业务 App 源码仓库 (App Remote Repository)
- **仓库名称**: `ashanzzz/erpnext-private-customizations`
- **Git Remote**: `https://github.com/ashanzzz/erpnext-private-customizations.git`
- **当前工作区**: `d:\SynologyDrive团队\antigravity\erpnext16`（即该仓库本地工作区）

### Docker 构建镜像仓库 (Docker Build Remote Repository)
- **仓库名称**: `ashanzzz/docker`
- **构建工作流**: `.github/workflows/erpnext16-single-container-aio.yml`
- **Containerfile 路径**: `erpnext16/single-aio/Containerfile`
- **已产出 GHCR 镜像**: `ghcr.io/ashanzzz/erpnext16:latest`
- **本地修复补丁包**: `ashanzzz-docker-erpnext16-complete-fix/`

---

## 🖥️ 3. Unraid 服务器与 Docker 运维配置

- **Unraid 服务器 IP**: `192.168.8.11`
- **Unraid 官方 GraphQL API**: `http://192.168.8.11/graphql`
- **Unraid 官方 API Key**: 记录于 `.env` 中的 `UNRAID_OFFICIAL_API_KEY`
- **Unraid 容器名称**:
  - `/erpnext16` (镜像: `ghcr.io/ashanzzz/erpnext16:latest`, 核心部署容器)
  - `/ERPNext` (镜像: `ghcr.io/ashanzzz/erpnext15-aio:latest`, 备用/运行端口 8888)
- **UnraidClaw 网关**: `http://192.168.8.11:9876`

---

## 📂 4. 本地目录分工与文件结构

```text
d:\SynologyDrive团队\antigravity\erpnext16/
├── ashan_cn_procurement/             # ⭐️ 核心 App 模块源码 (Doctype/Custom/Hooks/Public)
│   ├── pyproject.toml
│   └── ashan_cn_procurement/
│       ├── custom/                   # 字段与单据 Custom 属性
│       ├── doctype/                  # 自定义 DocType 模块
│       ├── public/                   # 前端 JS/CSS 静态资源与侧边栏
│       ├── workspace/                # Workspace 布局配置
│       └── hooks.py                  # App 核心钩子文件
│
├── ashanzzz-docker-erpnext16-complete-fix/ # 🐳 给 ashanzzz/docker 仓库准备的 CI/Dockerfile 完整修复包
│   ├── README_FIX.md                 # 包含 Docker 镜像构建失败修复指南
│   ├── apply-to-existing-repo.sh     # 自动应用修复文件到 ashanzzz/docker 的脚本
│   └── erpnext16/                    # 修复后的 Containerfile 与脚本
│
├── docs/                             # 📖 ERPNext 16 AI 开发文档与规范指南
│   └── ai/
│       ├── ERPNext_PROJECT_RULES.md
│       ├── ERPNext16_LEARN.md
│       └── ERPNext16_API_MAP.md
│
├── PROJECT_MAP.md                    # ⭐️ 本规范与映射说明文件
├── AGENTS.md & .agents/              # 🤖 AI 开发指导规则与环境限制
├── .env & .env.example               # 🔑 环境变量配置文件 (含 ERPNext & Unraid API)
└── *.py                              # 🛠️ 自动化初始化、测试与侧边栏配置脚本工具
```
