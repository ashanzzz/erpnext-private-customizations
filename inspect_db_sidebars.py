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

# List all Workspace Sidebar records
sidebars = frappe.get_all('Workspace Sidebar', fields=['name', 'title', 'module', 'app', 'is_standard'])
print('ALL Workspace Sidebar records (' + str(len(sidebars)) + '):')
for s in sidebars:
    print(' ->', json.dumps(s, ensure_ascii=False))

# Check items for our sidebars
our_sidebars = [s['name'] for s in sidebars if '业务' in s['name'] or 'ashan' in s['name'].lower() or 'business' in s['name'].lower() or 'stock' in s['name'].lower() or 'procure' in s['name'].lower()]
print('\\nOUR SIDEBAR DETAILS:')
for sname in our_sidebars:
    doc = frappe.get_doc('Workspace Sidebar', sname)
    print(f'=== {doc.name} (title: {doc.title}, app: {doc.app}) ===')
    print(f'Items count: {len(doc.items)}')
    for item in doc.items[:10]:
        print('   ', item.type, item.title or item.label or item.link_to, 'indent:', item.indent)

# Check Workspace "My Business" to see what sidebar it links to
mb_doc = frappe.get_doc('Workspace', 'My Business')
print('\\nWorkspace "My Business" doc dict:')
for k, v in mb_doc.as_dict().items():
    if k not in ['content']:
        print(f'  {k}: {v}')
"""

cmd = f"docker exec -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python -c \"{py_code}\""
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print("STDOUT:\n", stdout.read().decode('utf-8', errors='replace'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='replace'))

ssh.close()
