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

check_py = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

print("--- Workspace: Home ---")
ws_home = frappe.get_doc("Workspace", "Home")
print("Workspace Home module:", ws_home.module, "app:", ws_home.app, "sequence_id:", ws_home.sequence_id)

print("\\n--- Workspace Sidebar: Home ---")
if frappe.db.exists("Workspace Sidebar", "Home"):
    sb_home = frappe.get_doc("Workspace Sidebar", "Home")
    print("Sidebar Home module:", sb_home.module, "app:", sb_home.app)
    print("Sidebar Home items count:", len(sb_home.sidebar_items))
    for it in sb_home.sidebar_items[:5]:
        print("  ", it.label, it.type, it.link_type, it.link_to)
else:
    print("Workspace Sidebar 'Home' does NOT exist!")

print("\\n--- Workspace Sidebar: My Business ---")
if frappe.db.exists("Workspace Sidebar", "My Business"):
    sb_mb = frappe.get_doc("Workspace Sidebar", "My Business")
    print("Sidebar My Business module:", sb_mb.module, "app:", sb_mb.app)
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/check_sidebar_home_details.py', 'wb') as f:
    f.write(check_py.encode('utf-8'))

cmd1 = "docker cp /tmp/check_sidebar_home_details.py erpnext16:/tmp/check_sidebar_home_details.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/check_sidebar_home_details.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
