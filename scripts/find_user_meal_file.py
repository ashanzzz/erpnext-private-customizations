import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("Searching C:\\Users\\ashan for 订餐记录...")
for root, dirs, files in os.walk(r"C:\Users\ashan"):
    # 忽略过深或大型缓存目录
    if any(p in root for p in ['.git', 'node_modules', 'venv', 'env', 'AppData\\Local\\Microsoft', 'AppData\\Local\\Google']):
        continue
    for f in files:
        if "订餐" in f:
            print("FOUND:", os.path.join(root, f))
