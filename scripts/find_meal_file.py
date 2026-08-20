import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

search_roots = [
    r"d:\SynologyDrive团队\antigravity",
    r"d:\SynologyDrive团队",
    r"C:\Users\ashan\Downloads",
    r"C:\Users\ashan\Desktop"
]

print("Searching for '订餐记录' across directories...")
for root in search_roots:
    if not os.path.exists(root):
        continue
    print(f"Scanning {root}...")
    for dirpath, dirnames, filenames in os.walk(root):
        for f in filenames:
            if "订餐" in f or "餐" in f:
                print("FOUND:", os.path.join(dirpath, f))
