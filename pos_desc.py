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

# 设置 description 位于 item_name 后面 (Column 2)
# idx 顺序: item_code (1), col_break1 (2), item_name (3), description (4), col_break7 (5), quantity_and_rate (6)
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "item_code"}, "idx", 1)
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "col_break1"}, "idx", 2)
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "item_name"}, "idx", 3)
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "description"}, "idx", 4)
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "description"}, "hidden", 0)

frappe.db.commit()
frappe.clear_cache(doctype="Purchase Invoice Item")
print("[OK] Description positioned right after item_name!")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/pos_desc.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/pos_desc.py erpnext16:/tmp/pos_desc.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/pos_desc.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
