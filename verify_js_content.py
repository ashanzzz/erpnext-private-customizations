import os
import requests

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()
SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')

# Fetch the JS file from the server to verify its content
js_url = f"{SITE_URL}/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js"
resp = requests.get(js_url, timeout=10)
print(f"Status: {resp.status_code}")
content = resp.text

# Check for key strings that confirm the fix
checks = [
    ("ASHAN_SIDEBAR_KEY", "ashan-cn-sidebar-state isolation key"),
    ("restore_sidebar_states", "state restore function"),
    ("patch_frappe_sidebar_item", "Frappe patch function"),
    ("set_section_state", "individual section state setter"),
    ("get_section_state", "individual section state getter"),
    ("sidebar_setup", "sidebar_setup event listener"),
]
print("\n=== Content Verification ===")
all_pass = True
for key, desc in checks:
    found = key in content
    status = "PASS" if found else "FAIL"
    if not found:
        all_pass = False
    print(f"[{status}] {desc}: '{key}'")

# Check that old problematic pattern is removed
old_patterns = [
    "section-breaks-state",
]
print("\n=== Old Pattern Check (should use our isolated key) ===")
for pat in old_patterns:
    count = content.count(pat)
    print(f"  '{pat}' appears {count} times (expected: 0 if fully isolated)")

# Show first 500 chars to confirm it's the new file
print(f"\n=== File Preview (first 300 chars) ===")
print(content[:300])

print(f"\n{'ALL CHECKS PASSED' if all_pass else 'SOME CHECKS FAILED'}")
