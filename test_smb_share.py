import os

candidate_unc_paths = [
    r"\\192.168.8.11\appdata",
    r"\\192.168.8.11\appdata\erpnext16",
    r"\\192.168.8.11\appdata\erpnext16\sites",
    r"\\192.168.8.11\flash",
    r"\\192.168.8.11\root"
]

print("Checking Windows UNC paths on 192.168.8.11...")
for p in candidate_unc_paths:
    try:
        exists = os.path.exists(p)
        print(f"Path '{p}' exists? {exists}")
        if exists:
            print("Contents:", os.listdir(p)[:10])
    except Exception as e:
        print(f"Path '{p}' error:", e)

