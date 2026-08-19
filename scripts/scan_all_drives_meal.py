import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

for drive in ['C:\\', 'D:\\', 'E:\\', 'F:\\']:
    if not os.path.exists(drive):
        continue
    print(f"Scanning drive {drive} for *订餐记录*...")
    for root, dirs, files in os.walk(drive):
        # 排除 Windows 系统核心大目录
        if any(p in root for p in ['\\Windows', '\\Program Files', '\\AppData', '\\.gemini', '\\node_modules', '\\.git', '\\$Recycle.Bin']):
            continue
        for f in files:
            if "订餐" in f:
                print("FOUND:", os.path.join(root, f))
