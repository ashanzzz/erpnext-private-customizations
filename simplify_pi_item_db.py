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

print("--- 优化 Purchase Invoice Item 字段与分区 ---")

# 白名单字段：保留且显示的字段
KEEP_VISIBLE_FIELDS = [
    "item_code", "item_name", "custom_spec_model", "uom", "description",
    "qty", "custom_gross_rate", "custom_tax_rate", "rate", "amount",
    "custom_tax_amount", "custom_gross_amount", "custom_line_remark",
    # 结构列断
    "col_break1", "col_break2", "col_break4", "col_break7",
    "quantity_and_rate", "description_section"
]

# 1. 隐藏所有不在白名单中的 DocField
docfields = frappe.db.get_all("DocField", filters={"parent": "Purchase Invoice Item"}, fields=["name", "fieldname", "fieldtype", "hidden"])
hidden_count = 0
for df in docfields:
    fn = df.fieldname
    if fn and fn not in KEEP_VISIBLE_FIELDS:
        frappe.db.set_value("DocField", df.name, "hidden", 1)
        hidden_count += 1
    elif fn in KEEP_VISIBLE_FIELDS:
        frappe.db.set_value("DocField", df.name, "hidden", 0)

print(f"已隐藏 Purchase Invoice Item 冗余字段数: {hidden_count}")

# 2. 优化关键字段中文标签
label_updates = {
    "qty": "数量",
    "custom_gross_rate": "含税单价",
    "custom_tax_rate": "税率(%)",
    "rate": "不含税单价",
    "amount": "金额 (未税)",
    "custom_tax_amount": "税额",
    "custom_gross_amount": "价税合计",
    "custom_line_remark": "行备注",
    "custom_spec_model": "规格型号"
}

for fn, lbl in label_updates.items():
    if frappe.db.exists("DocField", {"parent": "Purchase Invoice Item", "fieldname": fn}):
        frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": fn}, "label", lbl)
    if frappe.db.exists("Custom Field", {"dt": "Purchase Invoice Item", "fieldname": fn}):
        frappe.db.set_value("Custom Field", {"dt": "Purchase Invoice Item", "fieldname": fn}, "label", lbl)

frappe.db.commit()
frappe.clear_cache(doctype="Purchase Invoice")
frappe.clear_cache(doctype="Purchase Invoice Item")
print("[OK] 子表 DocField 数据库精简优化完成！")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/simplify_pi_item_db.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/simplify_pi_item_db.py erpnext16:/tmp/simplify_pi_item_db.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/simplify_pi_item_db.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
