import os
import re
import sys

vba_file = r"d:\SynologyDrive团队\antigravity\erpnext16\scripts\extracted_vba_macros_gbk.txt"
out_file = r"d:\SynologyDrive团队\antigravity\erpnext16\scripts\jizhong_vba_deep_dive.txt"

with open(vba_file, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

blocks = re.split(r'=== (.*?) ===', content)
modules = {}
for i in range(1, len(blocks), 2):
    mod_name = blocks[i].strip()
    mod_code = blocks[i+1].strip()
    modules[mod_name] = mod_code

with open(out_file, 'w', encoding='utf-8') as out:
    out.write("================================================================================\n")
    out.write("吉众人事综合.xlsm VBA 宏代码深度解析与业务逻辑全景梳理\n")
    out.write("================================================================================\n\n")

    out.write(f"共检测到 {len(modules)} 个 VBA 模块/表单代码对象：\n")
    for m in modules.keys():
        out.write(f"  - {m} (代码行数: {len(modules[m].splitlines())})\n")
    out.write("\n" + "="*80 + "\n\n")

    # 1. 查找 UserForm 按钮流程
    for m, code in modules.items():
        if "frm" in m.lower() or "button" in code.lower() or "click" in code.lower():
            out.write(f"--- [流程总控/界面交互] 模块: {m} ---\n")
            lines = code.splitlines()
            for line in lines:
                if any(k in line.lower() for k in ["sub commandbutton", "sub userform", "call ", "msgbox"]):
                    out.write(f"  {line.strip()}\n")
            out.write("\n")

    out.write("="*80 + "\n")
    out.write("--- 核心计算模块与关键算法代码摘录 ---\n")
    out.write("="*80 + "\n\n")

    # 2. 详细输出各业务模块的核心逻辑
    for m, code in modules.items():
        if any(keyword in m for keyword in ["工资", "工时", "个税", "税", "社保", "公积金", "考勤", "历史", "条"]):
            out.write(f"\n################################################################################\n")
            out.write(f"模块: {m}\n")
            out.write(f"################################################################################\n\n")
            out.write(code)
            out.write("\n\n")

print(f"Deep dive written to: {out_file}")
