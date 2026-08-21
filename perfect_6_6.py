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

print("--- 重建 Purchase Invoice Item 为标准的单分区、双列 6+6 对称布局 ---")

field_structure = [
    # 唯一顶层分区
    ("sec_break1", 1, 0, "物料明细与财税核算"),
    # 左列 6 项 (基础与数量)
    ("item_code", 2, 0, "物料编码"),
    ("item_name", 3, 0, "物料名称"),
    ("description", 4, 0, "规格型号 / 描述"),
    ("qty", 5, 0, "数量"),
    ("uom", 6, 0, "单位"),
    ("custom_line_remark", 7, 0, "行备注"),
    # 分列断点
    ("col_break1", 8, 0, ""),
    # 右列 6 项 (单价与财税)
    ("rate", 9, 0, "不含税单价"),
    ("custom_gross_rate", 10, 0, "含税单价"),
    ("custom_tax_rate", 11, 0, "税率 (%)"),
    ("amount", 12, 0, "金额 (未税)"),
    ("custom_tax_amount", 13, 0, "税额"),
    ("custom_gross_amount", 14, 0, "价税合计")
]

# 1. 隐藏所有其他字段
all_dfs = frappe.db.get_all("DocField", filters={"parent": "Purchase Invoice Item"}, fields=["name", "fieldname"])
structure_fns = [item[0] for item in field_structure]

for df in all_dfs:
    if df.fieldname not in structure_fns:
        frappe.db.set_value("DocField", df.name, "hidden", 1)

# 2. 依次设置结构中字段的 idx, hidden, label
for fn, idx, hid, lbl in field_structure:
    if frappe.db.exists("DocField", {"parent": "Purchase Invoice Item", "fieldname": fn}):
        updates = {"idx": idx, "hidden": hid}
        if lbl:
            updates["label"] = lbl
        frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": fn}, updates)
    elif frappe.db.exists("Custom Field", {"dt": "Purchase Invoice Item", "fieldname": fn}):
        updates = {"hidden": hid}
        if lbl:
            updates["label"] = lbl
        frappe.db.set_value("Custom Field", {"dt": "Purchase Invoice Item", "fieldname": fn}, updates)

frappe.db.commit()
frappe.clear_cache(doctype="Purchase Invoice")
frappe.clear_cache(doctype="Purchase Invoice Item")
print("[OK] 单分区双列 6+6 完美重构完成！")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/perfect_6_6.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/perfect_6_6.py erpnext16:/tmp/perfect_6_6.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/perfect_6_6.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
