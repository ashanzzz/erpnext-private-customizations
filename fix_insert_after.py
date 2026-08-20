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

print("--- 设置 Custom Field 的 insert_after 实现完美左右平衡 ---")

# Section 2:
# 左列: qty (数量) -> custom_gross_rate (含税单价)
# 右列: uom (单位) -> custom_tax_rate (税率%)
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

# Section 3:
# 左列: rate (不含税单价) -> amount (金额未税) -> custom_line_remark (行备注)
# 右列: col_break4 -> custom_tax_amount (税额) -> custom_gross_amount (价税合计)
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "col_break4"}, "hidden", 0)
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_tax_amount", {
    "insert_after": "col_break4",
    "label": "税额",
    "hidden": 0
})
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_gross_amount", {
    "insert_after": "custom_tax_amount",
    "label": "价税合计",
    "hidden": 0
})
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_line_remark", {
    "insert_after": "amount",
    "label": "行备注",
    "hidden": 0
})

frappe.db.commit()
frappe.clear_cache(doctype="Purchase Invoice")
frappe.clear_cache(doctype="Purchase Invoice Item")
print("[OK] Custom Field insert_after 调整完毕！")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/fix_insert_after.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/fix_insert_after.py erpnext16:/tmp/fix_insert_after.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/fix_insert_after.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
