# ERPNext16 定制百科与 Ashan 风格

这是一个**知识型、无代码执行权限**的智能体插件。它把本仓库已验证的 ERPNext 16 定制方法、Ashan UI/交互设计、权限边界、财务数据纪律和验收方式，整理为可按需加载的 `SKILL.md` 与参考资料。

它不包含账户、密码、令牌、真实员工资料或生产数据；也不会取代当前项目的 `AGENTS.md`。项目内实际源码、站点配置和当前业务规则始终优先。

## 内容层次

```text
erpnext16-customization-encyclopedia/
├── .codex-plugin/plugin.json       # Codex / ChatGPT 原生插件清单
├── skills/
│   └── erpnext16-customization/
│       ├── SKILL.md                # 所有智能体通用的主入口
│       └── references/             # 按任务类型按需加载的知识
└── adapters/                       # 各智能体的接入说明与轻量入口
```

主入口是 `skills/erpnext16-customization/SKILL.md`。参考资料不是静态“规定集”：它们要求智能体以当前仓库、Frappe/ERPNext v16 源码和官方文档核对不稳定信息。

其中 `references/PERSONALIZED_UI_CHARTER.md` 专门沉淀了您的报销中心个性化取舍：纯中文且不含装饰性 Emoji、严谨字段标题、流式不折行分段控件、安全草稿恢复、发票联锁、草稿置顶和 PI—PR—RR 的纯净闭环。

`references/ASHAN_WORKBENCH_ARCHITECTURE.md` 规定 Ashan 全模块的统一工作台方向：共享轻量 UI 骨架与交互组件，业务状态机、权限和单据链保持独立适配。

## 安装与使用

### Codex

本仓库已创建本地市场清单：`.agents/plugins/marketplace.json`。在 Codex 中将此仓库根目录添加为本地市场后，安装 `erpnext16-customization-encyclopedia`，并在**新任务**中使用它。每次更新插件后，需要重新安装并新开任务，让技能索引刷新。

### Google Antigravity

将整个 `skills/erpnext16-customization/` 文件夹（必须连同 `references/`）复制到目标工作区：

```text
<workspace>/.agents/skills/erpnext16-customization/
```

或复制到全局目录 `~/.gemini/config/skills/erpnext16-customization/`。详见 `adapters/ANTIGRAVITY.md`。

### Hermes Agent

将完整技能文件夹复制到：

```text
~/.hermes/skills/erpnext/erpnext16-customization/
```

新会话中可直接说“使用 erpnext16-customization”，或使用对应斜杠技能。详见 `adapters/HERMES.md`。

### OpenClaw

将完整技能文件夹放到受信任的技能目录，或把本插件的 `skills/` 目录加入 OpenClaw 的 `skills.load.extraDirs`。不要把宽泛目录（如整个用户目录）加入扫描范围。详见 `adapters/OPENCLAW.md`。

### 其他兼容 SKILL.md / AGENTS.md 的智能体

复制完整技能文件夹；若宿主只支持项目级说明文件，则将 `adapters/AGENTS.md` 合并到该项目的现有说明中，并让智能体在执行前读取本技能的 `SKILL.md` 与相关 `references/`。

## 维护方法

1. 业务、视觉或交互偏好发生变化时，优先修改 `references/` 中对应主题，并在 `references/CHANGELOG.md` 记录原因与生效日期。
2. 官方文档链接失效、Frappe/ERPNext 主版本变化时，只更新 `OFFICIAL_DOCUMENTS.md`，不要把可能过时的 API 细节写进核心规则。
3. 修改后运行插件校验器；Codex 更新时再刷新插件版本缓存并重新安装。
4. 不将真实敏感数据、连接串、令牌或个人资料放进此插件。

## 版本与边界

当前版本聚焦 **ERPNext / Frappe 16**。它是开发与审查辅助知识，而非 ERPNext 业务应用；它不会自动改变任何站点或生产数据。
