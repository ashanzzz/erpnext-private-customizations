# Hermes Agent 接入

Hermes 以带 YAML frontmatter 的 `SKILL.md` 加载按需知识，并允许随技能携带 `references/`。将完整目录复制到：

```text
~/.hermes/skills/erpnext/erpnext16-customization/
```

重新开启会话后，可通过自然语言“使用 erpnext16-customization”或该技能的斜杠入口调用。只复制 `SKILL.md` 会失去按需参考资料，不能这样安装。

官方依据：<https://hermes-agent.nousresearch.com/docs/guides/work-with-skills/>。
