import os

search_roots = [
    r"d:\SynologyDrive团队\antigravity\erpnext16",
    r"C:\Users\ashan\.gemini\antigravity"
]

for root in search_roots:
    for dirpath, dirnames, filenames in os.walk(root):
        if os.path.basename(dirpath) == 'assets' and 'frappe' in dirnames:
            print("Found assets dir:", dirpath)

