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

# 调整 idx 让 description 位于 item_code 下方 (Column 1)
# 原始: [1] item_code, [2] product_bundle, [3] col_break1, [4] item_name, [5] description_section, [6] description
# 调整: item_code (idx=1), description (idx=2), col_break1 (idx=3), item_name (idx=4)
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "description"}, "idx", 2)
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "description"}, "hidden", 0)
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "description_section"}, "hidden", 1)

frappe.db.commit()
frappe.clear_cache(doctype="Purchase Invoice Item")
print("[OK] Description moved to Column 1 under item_code!")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/reorder_desc.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/reorder_desc.py erpnext16:/tmp/reorder_desc.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/reorder_desc.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
