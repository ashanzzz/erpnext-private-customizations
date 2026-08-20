import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("Listing all xlsx/xls/xlsm files in d:\\SynologyDrive团队\\antigravity...")
for root, dirs, files in os.walk(r"d:\SynologyDrive团队\antigravity"):
    for f in files:
        if f.endswith(('.xlsx', '.xls', '.xlsm')):
            print(os.path.join(root, f))
