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

workspaces = frappe.get_all('Workspace', fields=['name', 'title', 'module', 'public', 'for_user', 'app'])
print('ALL WORKSPACES IN DB (' + str(len(workspaces)) + '):')
for w in workspaces:
    if 'business' in w.name.lower() or 'ashan' in w.name.lower() or 'stock' in w.name.lower() or 'procure' in w.name.lower() or 'fuel' in w.name.lower() or 'compliance' in w.name.lower() or 'account' in w.name.lower() or w.get('app') == 'ashan_cn_procurement':
        print(' ->', json.dumps(w, ensure_ascii=False))

# Check Page doctype records
pages = frappe.get_all('Page', fields=['name', 'title', 'module'])
print('\\nALL CUSTOM PAGES IN DB (' + str(len(pages)) + '):')
for p in pages:
    if 'business' in p.name.lower() or 'ashan' in p.name.lower():
        print(' ->', json.dumps(p, ensure_ascii=False))
"""

cmd = f"docker exec -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python -c \"{py_code}\""
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print("STDOUT:\n", stdout.read().decode('utf-8', errors='replace'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='replace'))

ssh.close()
