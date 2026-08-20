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

py_code = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

# 强制确保所有需要的 custom field 和 docfield 的 hidden 均为 0
cfs = [
    "Purchase Invoice Item-custom_gross_rate",
    "Purchase Invoice Item-custom_tax_rate",
    "Purchase Invoice Item-custom_tax_amount",
    "Purchase Invoice Item-custom_gross_amount",
    "Purchase Invoice Item-custom_line_remark"
]

for cf in cfs:
    frappe.db.set_value("Custom Field", cf, "hidden", 0)

dfs = ["item_code", "item_name", "description", "qty", "uom", "rate", "amount"]
for df in dfs:
    frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": df}, "hidden", 0)

frappe.db.commit()
frappe.clear_cache(doctype="Purchase Invoice Item")
print("[OK] All required fields verified hidden=0")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/ensure_visible.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/ensure_visible.py erpnext16:/tmp/ensure_visible.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/ensure_visible.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
