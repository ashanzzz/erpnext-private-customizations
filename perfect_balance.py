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

print("--- 彻底解决两列平衡对齐问题 ---")

# Section 1 (物料基础):
# 左列: item_code
# 右列: item_name -> description
# (或通过 Property Setter 调整 description 的 insert_after)

# Section 2 (数量与含税):
# 左列 (Col 0): qty -> custom_gross_rate (insert_after: qty)
# 右列 (Col 1): uom -> custom_tax_rate (insert_after: uom)
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_gross_rate", {
    "insert_after": "qty",
    "label": "含税单价",
    "hidden": 0
})
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_tax_rate", {
    "insert_after": "uom",
    "label": "税率 (%)",
    "hidden": 0
})

# Section 3 (未税金额与税额):
# 左列 (Col 0): rate -> amount -> custom_line_remark (insert_after: amount)
# 右列 (Col 1): custom_tax_amount (insert_after: base_amount) -> custom_gross_amount (insert_after: custom_tax_amount)
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_line_remark", {
    "insert_after": "amount",
    "label": "行备注",
    "hidden": 0
})
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_tax_amount", {
    "insert_after": "base_amount",
    "label": "税额",
    "hidden": 0
})
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_gross_amount", {
    "insert_after": "custom_tax_amount",
    "label": "价税合计",
    "hidden": 0
})

frappe.db.commit()
frappe.clear_cache(doctype="Purchase Invoice")
frappe.clear_cache(doctype="Purchase Invoice Item")
print("[OK] Balanced Column Placements committed!")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/perfect_balance.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/perfect_balance.py erpnext16:/tmp/perfect_balance.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/perfect_balance.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
