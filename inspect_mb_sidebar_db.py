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

py_code = """
import json
import frappe
frappe.init('site1.local')
frappe.connect()

# Check Workspace "My Business"
mb_doc = frappe.get_doc('Workspace', 'My Business')
print('\\nWorkspace "My Business" doc:')
for k, v in mb_doc.as_dict().items():
    if k not in ['content']:
        print(f'  {k}: {repr(v)}')

# Check Workspace Sidebar for "我的业务"
if frappe.db.exists('Workspace Sidebar', '我的业务'):
    sb = frappe.get_doc('Workspace Sidebar', '我的业务')
    print('\\nWorkspace Sidebar "我的业务" items count:', len(sb.items))
    for it in sb.items:
        print('  ->', it.type, it.label, it.link_to, it.indent)
"""

cmd = f"docker exec -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python -c \"{py_code}\""
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print("STDOUT:\n", stdout.read().decode('utf-8', errors='replace'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='replace'))

ssh.close()
