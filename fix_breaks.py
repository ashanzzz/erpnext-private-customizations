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

# 设置必要的分区分列为可见
VISIBLE_BREAKS = ["col_break1", "col_break7", "quantity_and_rate", "col_break2", "sec_break2", "col_break4"]
for b in VISIBLE_BREAKS:
    if frappe.db.exists("DocField", {"parent": "Purchase Invoice Item", "fieldname": b}):
        frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": b}, "hidden", 0)

# 修改 quantity_and_rate 标签为 "数量、价格与税额"
if frappe.db.exists("DocField", {"parent": "Purchase Invoice Item", "fieldname": "quantity_and_rate"}):
    frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "quantity_and_rate"}, "label", "数量、价格与税额")

# 隐藏 description_section
if frappe.db.exists("DocField", {"parent": "Purchase Invoice Item", "fieldname": "description_section"}):
    frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "description_section"}, "hidden", 1)

frappe.db.commit()
frappe.clear_cache(doctype="Purchase Invoice Item")
print("[OK] Breaks updated successfully!")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/fix_breaks.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/fix_breaks.py erpnext16:/tmp/fix_breaks.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/fix_breaks.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
