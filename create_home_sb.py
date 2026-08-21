# -*- coding: utf-8 -*-
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

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER_SSH, password=PASSWORD, timeout=10)

py_code = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

print("--- 创建并同步 Workspace Sidebar 'Home' ---")

# 1. 确保 tabWorkspace Sidebar 中有 'Home'
if not frappe.db.exists("Workspace Sidebar", "Home"):
    sb = frappe.get_doc({
        "doctype": "Workspace Sidebar",
        "name": "Home",
        "title": "Home",
        "header_icon": "home",
        "module": "Ashan CN Procurement",
        "app": "ashan_cn_procurement"
    })
    sb.insert(ignore_permissions=True)
    print("Created Workspace Sidebar 'Home'")
else:
    frappe.db.set_value("Workspace Sidebar", "Home", {
        "title": "Home",
        "header_icon": "home",
        "module": "Ashan CN Procurement",
        "app": "ashan_cn_procurement"
    })

# 2. 复制 My Business 的 sidebar items 到 Home
frappe.db.sql("DELETE FROM `tabWorkspace Sidebar Item` WHERE parent = 'Home'")
my_biz_items = frappe.db.sql("SELECT * FROM `tabWorkspace Sidebar Item` WHERE parent = 'My Business' ORDER BY idx", as_dict=True)
for item in my_biz_items:
    new_item = frappe.get_doc({
        "doctype": "Workspace Sidebar Item",
        "parent": "Home",
        "parenttype": "Workspace Sidebar",
        "parentfield": "items",
        "idx": item.idx,
        "type": item.type,
        "label": item.label,
        "icon": item.icon,
        "link_type": item.link_type,
        "link_to": "Home" if item.link_to in ["My Business", "my-business"] else item.link_to,
        "child": item.child,
        "is_hidden": item.is_hidden,
        "keep_closed": item.keep_closed
    })
    new_item.insert(ignore_permissions=True)

print(f"Copied {len(my_biz_items)} items to Workspace Sidebar 'Home'")

frappe.db.commit()
frappe.clear_cache()
print("[OK] Workspace Sidebar 'Home' 成功建立！")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/create_home_sb.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/create_home_sb.py erpnext16:/tmp/create_home_sb.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/create_home_sb.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
