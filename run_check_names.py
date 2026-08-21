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

py_content = """# -*- coding: utf-8 -*-
import frappe
frappe.init('site1.local')
frappe.connect()

ws_list = frappe.get_all('Workspace', fields=['name', 'title', 'module', 'app'])
sb_list = frappe.get_all('Workspace Sidebar', fields=['name', 'title', 'module', 'app'])

print('--- WORKSPACES (' + str(len(ws_list)) + ') ---')
for w in ws_list:
    if w.module == 'Ashan CN Procurement' or 'Business' in w.name:
        print(f"Workspace name: '{w.name}', title: '{w.title}'")

print('\\n--- WORKSPACE SIDEBARS (' + str(len(sb_list)) + ') ---')
for s in sb_list:
    if s.app == 'ashan_cn_procurement' or '业务' in s.name:
        print(f"Sidebar name: '{s.name}', title: '{s.title}', app: '{s.app}'")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/check_names.py', 'wb') as f:
    f.write(py_content.encode('utf-8'))
sftp.close()

cmd = "docker cp /tmp/check_names.py erpnext16:/tmp/check_names.py && docker exec -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python /tmp/check_names.py"
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print(stdout.read().decode('utf-8', errors='replace'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='replace'))

ssh.close()
