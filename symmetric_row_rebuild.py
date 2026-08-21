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

print("--- 重构 Purchase Invoice Item 为 6+6 完美对称两列 ---")

# 左列: item_code, item_name, description, qty, uom, custom_line_remark
# 右列: rate, custom_gross_rate, custom_tax_rate, amount, custom_tax_amount, custom_gross_amount

# 1. 重构 DocField 顺序与显隐
field_order = [
    # 左列
    ("item_code", 1, 0),
    ("item_name", 2, 0),
    ("description", 3, 0),
    ("qty", 4, 0),
    ("uom", 5, 0),
    ("custom_line_remark", 6, 0),
    # 列断 (分列)
    ("col_break1", 7, 0),
    # 右列
    ("rate", 8, 0),
    ("custom_gross_rate", 9, 0),
    ("custom_tax_rate", 10, 0),
    ("amount", 11, 0),
    ("custom_tax_amount", 12, 0),
    ("custom_gross_amount", 13, 0),
]

for fn, idx, hid in field_order:
    if frappe.db.exists("DocField", {"parent": "Purchase Invoice Item", "fieldname": fn}):
        frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": fn}, {"idx": idx, "hidden": hid})
    if frappe.db.exists("Custom Field", {"dt": "Purchase Invoice Item", "fieldname": fn}):
        frappe.db.set_value("Custom Field", {"dt": "Purchase Invoice Item", "fieldname": fn}, {"hidden": hid})

# 隐藏所有其他 Section Break / Column Break，消除多余空白与分割线
all_dfs = frappe.db.get_all("DocField", filters={"parent": "Purchase Invoice Item"}, fields=["name", "fieldname", "fieldtype"])
known_fns = [f[0] for f in field_order]
for df in all_dfs:
    if df.fieldname not in known_fns:
        frappe.db.set_value("DocField", df.name, "hidden", 1)

frappe.db.commit()
frappe.clear_cache(doctype="Purchase Invoice")
frappe.clear_cache(doctype="Purchase Invoice Item")
print("[OK] 6+6 对称重构完成！")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/symmetric_row_rebuild.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/symmetric_row_rebuild.py erpnext16:/tmp/symmetric_row_rebuild.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/symmetric_row_rebuild.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
