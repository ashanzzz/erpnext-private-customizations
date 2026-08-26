# OpenClaw 接入

OpenClaw 可以扫描额外的受信任技能目录。最简做法是把本插件的 `skills/` 目录加入 `~/.openclaw/openclaw.json` 的 `skills.load.extraDirs`，然后让它监视变更：

```json
{
  "skills": {
    "load": {
      "extraDirs": [
        "D:/SynologyDrive团队/antigravity/erpnext16/plugins/erpnext16-customization-encyclopedia/skills"
      ],
      "watch": true
    }
  }
}
```

也可复制 `skills/erpnext16-customization/` 到你现有的受信任 OpenClaw 技能目录。保持目录范围精确，勿把整个用户目录或项目父目录加入扫描；本技能不需要环境变量或外部命令。

官方依据：<https://github.com/openclaw/docs/blob/main/docs/tools/skills-config.md>。
