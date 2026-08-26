# Google Antigravity 接入

Google Antigravity 使用开放的 `SKILL.md` 结构，并支持项目级与全局技能目录。因此复制整个技能目录（包括 `references/`）即可，无需转写内容。

## 项目级安装

```text
<目标项目>/.agents/skills/erpnext16-customization/
```

将本插件中的 `skills/erpnext16-customization/` 完整复制到上述位置；新开任务后询问“使用 erpnext16-customization 审查/实现……”。

## 全局安装

```text
~/.gemini/config/skills/erpnext16-customization/
```

适用于所有项目都应遵循的个人开发风格。项目里若已有更严格的 `AGENTS.md`，二者同时生效，项目业务规则优先。

官方依据：<https://antigravity.google/docs/skills>。
