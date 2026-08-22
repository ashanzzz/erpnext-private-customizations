import os
import paramiko

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()
HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER_SSH = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

# 1. Clean boot.py - NO overwriting bootinfo.home_page!
CLEAN_BOOT_PY = """import frappe

def set_login_redirect(*args, **kwargs):
    \"\"\"
    Hook for on_session_creation.
    \"\"\"
    for arg in args:
        if hasattr(arg, "home_page"):
            arg.home_page = "/desk/my-business"
    if hasattr(frappe.local, "login_manager") and frappe.local.login_manager:
        frappe.local.login_manager.home_page = "/desk/my-business"
    if hasattr(frappe, "local") and hasattr(frappe.local, "response"):
        frappe.local.response["home_page"] = "/desk/my-business"
"""

# 2. Clean hooks.py
CLEAN_HOOKS_PY = """app_name = "ashan_cn_procurement"
app_title = "业务扩展"
app_publisher = "Ashan CN Procurement"
app_description = "ERPNext 16 采购与仓储定制业务扩展"
app_email = "dev@example.invalid"
app_license = "mit"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/ashan_cn_procurement/css/ashan_cn_procurement.css"
app_include_js = "/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js"

# App Switcher Dropdown Registration
add_to_apps_screen = [
    {
        "name": "ashan_cn_procurement",
        "title": "业务扩展",
        "route": "/desk/my-business"
    }
]

# Post-Login Default Page (Dashboard / Workspace)
on_session_creation = "ashan_cn_procurement.boot.set_login_redirect"

# Website Redirects: Route root / and /app to /desk/my-business
website_redirects = [
    {"source": "/", "target": "/desk/my-business"},
    {"source": "/app", "target": "/desk/my-business"},
    {"source": r"/app/(.*)", "target": r"/desk/\1", "forward_query_parameters": True},
]
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER_SSH, password=PASSWORD, timeout=10)

sftp = ssh.open_sftp()
with sftp.open('/tmp/boot.py', 'w') as f:
    f.write(CLEAN_BOOT_PY)
with sftp.open('/tmp/hooks.py', 'w') as f:
    f.write(CLEAN_HOOKS_PY)
sftp.close()

cmd1 = "docker cp /tmp/boot.py erpnext16:/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/boot.py"
cmd2 = "docker cp /tmp/hooks.py erpnext16:/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/hooks.py"
ssh.exec_command(cmd1)[1].channel.recv_exit_status()
ssh.exec_command(cmd2)[1].channel.recv_exit_status()
print("[OK] Replaced boot.py and hooks.py")

# Clear cache on site1.local
cmd3 = "docker exec -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache"
ssh.exec_command(cmd3)[1].channel.recv_exit_status()
print("[OK] Cache cleared")

ssh.close()
