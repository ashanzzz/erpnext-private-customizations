# -*- coding: utf-8 -*-
import os
import paramiko
import json

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

export_py = """# -*- coding: utf-8 -*-
import frappe
import json

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

cf = frappe.get_doc("Custom Field", "Purchase Invoice-custom_items_summary")
print(json.dumps(cf.as_dict(), indent=2, ensure_ascii=False))
"""

stdin, stdout, stderr = ssh.exec_command(f"docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 -c '{export_py}'")
out = stdout.read().decode('utf-8')
print("Exported CF:", out[:500])

ssh.close()
