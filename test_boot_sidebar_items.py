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
from frappe.boot import get_sidebar_items
frappe.init('site1.local')
frappe.connect()

items = get_sidebar_items(['My Business'])
print('my business in items:', 'my business' in items)
if 'my business' in items:
    print('Item count for my business:', len(items['my business']['items']))
    for it in items['my business']['items'][:8]:
        print(' ->', it['label'], it['type'], it.get('child'))
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/test_boot_fn.py', 'wb') as f:
    f.write(py_content.encode('utf-8'))
sftp.close()

cmd = "docker cp /tmp/test_boot_fn.py erpnext16:/tmp/test_boot_fn.py && docker exec -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python /tmp/test_boot_fn.py"
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print(stdout.read().decode('utf-8', errors='replace'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='replace'))

ssh.close()
