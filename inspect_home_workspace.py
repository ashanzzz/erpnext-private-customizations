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

check_home_py = """# -*- coding: utf-8 -*-
import frappe
import json

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

print("--- List of all Workspaces ---")
ws_list = frappe.db.sql("SELECT name, title, label, module, app, public, is_hidden FROM `tabWorkspace`", as_dict=True)
for ws in ws_list:
    print(f"Name: {ws.name:<30} Title: {str(ws.title):<25} Module: {str(ws.module):<20} App: {str(ws.app):<20} Hidden: {ws.is_hidden}")

print("\\n--- Checking 'Home' Workspace document in Frappe ---")
if frappe.db.exists("Workspace", "Home"):
    doc = frappe.get_doc("Workspace", "Home")
    print("Home Title:", doc.title)
    print("Home Label:", doc.label)
    print("Home Content JSON:", doc.content)
elif frappe.db.exists("Workspace", "home"):
    doc = frappe.get_doc("Workspace", "home")
    print("home Doc:", doc.as_dict())
else:
    print("No Workspace named Home or home!")

print("\\n--- Checking 'my-business' or other custom workspaces ---")
custom_list = [w for w in ws_list if w.app == 'ashan_cn_procurement' or 'business' in w.name.lower() or '总控' in str(w.title)]
for cw in custom_list:
    doc = frappe.get_doc("Workspace", cw.name)
    print(f"Custom WS [{cw.name}]: title={doc.title}, content={doc.content[:300] if doc.content else 'None'}")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/check_home_workspace.py', 'wb') as f:
    f.write(check_home_py.encode('utf-8'))

cmd1 = "docker cp /tmp/check_home_workspace.py erpnext16:/tmp/check_home_workspace.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/check_home_workspace.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
