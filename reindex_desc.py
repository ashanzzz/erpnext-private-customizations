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

# 调整 idx 顺序，让 description 位于第1个分区 (col_break1 下面，与 item_name 同列)
# [1] item_code, [2] col_break1, [3] item_name, [4] description, [5] col_break7 (隐藏), [6] quantity_and_rate (Section Break)
frappe.db.sql('''
    UPDATE `tabDocField`
    SET idx = CASE fieldname
        WHEN 'item_code' THEN 1
        WHEN 'col_break1' THEN 2
        WHEN 'item_name' THEN 3
        WHEN 'description' THEN 4
        WHEN 'quantity_and_rate' THEN 5
        ELSE idx + 10
    END
    WHERE parent = 'Purchase Invoice Item'
''')

# 确保 description_section 为 hidden: 1
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "description_section"}, "hidden", 1)
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "description"}, "hidden", 0)

frappe.db.commit()
frappe.clear_cache(doctype="Purchase Invoice Item")
print("[OK] Re-indexed description to idx 4 (inside Section 1)!")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/reindex_desc.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/reindex_desc.py erpnext16:/tmp/reindex_desc.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/reindex_desc.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
