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

transplant_py = """# -*- coding: utf-8 -*-
import frappe
import json

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

print("--- 1. 读取 My Business / 总控 Dashboard 的完整配置 ---")
my_biz = frappe.get_doc("Workspace", "My Business") if frappe.db.exists("Workspace", "My Business") else None

if not my_biz:
    print("My Business not found in DB! Searching for any business workspace...")
    my_biz = frappe.get_doc("Workspace", "Ashan CN Procurement")

print("Source Workspace Title:", my_biz.title)
print("Shortcuts count:", len(my_biz.shortcuts))
print("Links count:", len(my_biz.links))

print("\\n--- 2. 移植到 Workspace 'Home' ---")
home_doc = frappe.get_doc("Workspace", "Home")
home_doc.title = "我的业务 (总控主页)"
home_doc.icon = "home"
home_doc.indicator_color = "green"
home_doc.content = my_biz.content
home_doc.public = 1
home_doc.is_hidden = 0

# 复制 shortcuts
home_doc.shortcuts = []
for sc in my_biz.shortcuts:
    home_doc.append("shortcuts", {
        "type": sc.type,
        "link_to": sc.link_to,
        "doc_view": sc.doc_view,
        "label": sc.label,
        "color": getattr(sc, "color", "Grey"),
        "format": getattr(sc, "format", "")
    })

# 复制 links (卡片)
home_doc.links = []
for lk in my_biz.links:
    home_doc.append("links", {
        "type": lk.type,
        "label": lk.label,
        "hidden": lk.hidden,
        "link_type": lk.link_type,
        "link_to": lk.link_to,
        "onboard": lk.onboard,
        "is_query_report": lk.is_query_report,
        "link_count": lk.link_count,
        "dependencies": getattr(lk, "dependencies", "")
    })

home_doc.save(ignore_permissions=True)
frappe.db.commit()
print("[OK] Workspace 'Home' 已成功更新为【我的业务 (总控主页)】！")

print("\\n--- 3. 隐藏/合并旧的重复工作区 'My Business' ---")
if frappe.db.exists("Workspace", "My Business"):
    frappe.db.set_value("Workspace", "My Business", "is_hidden", 1)
    frappe.db.commit()
    print("[OK] 旧的 'My Business' 工作区已置为隐藏，防止侧边栏出现重复！")

frappe.clear_cache()
print("[OK] 缓存已刷新！")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/transplant_home_workspace.py', 'wb') as f:
    f.write(transplant_py.encode('utf-8'))

cmd1 = "docker cp /tmp/transplant_home_workspace.py erpnext16:/tmp/transplant_home_workspace.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/transplant_home_workspace.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
