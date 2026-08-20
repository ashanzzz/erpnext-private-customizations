import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

macro_path = r"d:\SynologyDrive团队\antigravity\erpnext16\scripts\extracted_vba_macros.txt"

with open(macro_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 找出所有的 Sub 和 Function
subs = re.findall(r'(?:Sub|Function)\s+([A-Za-z0-9_\u4e00-\u9fa5]+)\s*\(', content)
print("=== 提取到的 VBA 过程与函数列表 ===")
for idx, s in enumerate(set(subs), 1):
    print(f"{idx}. {s}")

print("\n=== VBA 模块列表与行数 ===")
modules = content.split('============================================================')
for m in modules:
    lines = m.strip().split('\n')
    if lines and 'MODULE:' in lines[0]:
        print(f"{lines[0]}: {len(lines)} 行")
