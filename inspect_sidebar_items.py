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

check_sidebar_py = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

print("--- Workspace Sidebars ---")
if frappe.db.table_exists("Workspace Sidebar"):
    sidebars = frappe.db.sql("SELECT name, title, module, app FROM `tabWorkspace Sidebar`", as_dict=True)
    for sb in sidebars:
        print(sb)

print("\\n--- Checking Sidebar Items for 'My Business' vs 'Home' ---")
if frappe.db.table_exists("Workspace Sidebar Item"):
    my_biz_items = frappe.db.sql("SELECT * FROM `tabWorkspace Sidebar Item` WHERE parent = 'My Business' ORDER BY idx", as_dict=True)
    print(f"My Business items count: {len(my_biz_items)}")
    for it in my_biz_items[:10]:
        print(" ", it.label, it.type, it.link_type, it.link_to)

    home_items = frappe.db.sql("SELECT * FROM `tabWorkspace Sidebar Item` WHERE parent = 'Home' ORDER BY idx", as_dict=True)
    print(f"Home items count: {len(home_items)}")
    for it in home_items[:10]:
        print(" ", it.label, it.type, it.link_type, it.link_to)
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/check_sidebars.py', 'wb') as f:
    f.write(check_sidebar_py.encode('utf-8'))

cmd1 = "docker cp /tmp/check_sidebars.py erpnext16:/tmp/check_sidebars.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/check_sidebars.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
