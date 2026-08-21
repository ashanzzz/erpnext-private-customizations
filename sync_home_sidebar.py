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

sync_sidebar_py = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

print("--- 同步 Sidebar Items 到 Home ---")
# 清除旧的 Home 侧边栏子项
frappe.db.sql("DELETE FROM `tabWorkspace Sidebar Item` WHERE parent = 'Home'")

# 从 My Business 复制全部子项
my_biz_items = frappe.db.sql("SELECT * FROM `tabWorkspace Sidebar Item` WHERE parent = 'My Business' ORDER BY idx", as_dict=True)

for item in my_biz_items:
    new_item = frappe.get_doc({
        "doctype": "Workspace Sidebar Item",
        "parent": "Home",
        "parenttype": "Workspace Sidebar",
        "parentfield": "sidebar_items",
        "idx": item.idx,
        "type": item.type,
        "label": item.label,
        "icon": item.icon,
        "link_type": item.link_type,
        "link_to": "Home" if item.link_to == "My Business" else item.link_to,
        "child": item.child,
        "is_hidden": item.is_hidden,
        "keep_closed": item.keep_closed
    })
    new_item.insert(ignore_permissions=True)

frappe.db.commit()
print(f"[OK] 成功向 Home Workspace Sidebar 注入 {len(my_biz_items)} 个中文导航项！")

frappe.clear_cache()
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/sync_home_sidebar.py', 'wb') as f:
    f.write(sync_sidebar_py.encode('utf-8'))

cmd1 = "docker cp /tmp/sync_home_sidebar.py erpnext16:/tmp/sync_home_sidebar.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/sync_home_sidebar.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
