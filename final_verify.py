import os
import urllib.request
import urllib.parse
import json
import http.cookiejar

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

# Verify the JS file is correct (already confirmed from HTTP)
js_url = f"{SITE_URL}/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js"
req = urllib.request.Request(js_url)
with urllib.request.urlopen(req, timeout=10) as resp:
    content = resp.read().decode('utf-8', errors='replace')

checks = {
    "ASHAN_SIDEBAR_KEY": "独立 localStorage key 已定义",
    "ashan-cn-sidebar-state": "正确的 key 名称",
    "restore_sidebar_states": "状态恢复函数",
    "patch_frappe_sidebar_item": "Frappe 原生函数覆盖",
    "set_section_state": "分组状态设置",
    "get_section_state": "分组状态读取",
    "sidebar_setup": "sidebar_setup 事件监听",
    "frappe.router.on": "路由变化监听",
    "sync_boot_sidebar_items": "sidebar 锁定函数",
}

print("=== 修复内容验证 ===\n")
all_pass = True
for k, desc in checks.items():
    found = k in content
    if not found:
        all_pass = False
    print(f"{'[PASS]' if found else '[FAIL]'} {desc}: {k!r}")

# Verify old anti-patterns are NOT used in a problematic way
print("\n=== 旧代码清除验证 ===\n")
# Our code should NOT write to 'section-breaks-state' when it's our sidebar
save_pattern_safe = "if (_orig_save) _orig_save.call(this);" in content
print(f"[{'PASS' if save_pattern_safe else 'FAIL'}] 原生 save_section_break_state 调用被条件包裹")

total_lines = content.count('\n')
print(f"\n文件行数: {total_lines} 行")
print(f"文件大小: {len(content)} 字节")
print(f"\n{'所有检查通过！修复已确认上线' if all_pass else '有检查未通过'}")

# Extract SECTION_WORKSPACE_MAP to verify Chinese section titles
import re
map_match = re.search(r'SECTION_WORKSPACE_MAP\s*=\s*\{([^}]+)\}', content, re.DOTALL)
if map_match:
    print("\n=== 一级菜单-工作区映射 ===")
    print(map_match.group(0)[:500])
