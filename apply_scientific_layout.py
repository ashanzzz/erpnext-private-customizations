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

print("--- 科学调整 Purchase Invoice 主表与子表原生布局 ---")

# 1. 主表 Section 1：隐藏 column_break1，让 Section 1 成为标准双列
# 左列: custom_biz_mode
# 右列: posting_date, posting_time, custom_is_restricted_doc
frappe.db.set_value("DocField", {"parent": "Purchase Invoice", "fieldname": "column_break1"}, "hidden", 1)
frappe.db.set_value("Custom Field", "Purchase Invoice-custom_is_restricted_doc", {
    "insert_after": "posting_time",
    "hidden": 0
})

# 2. 主表 Section 2 (供应商与发票信息)：标准双列
# 左列: supplier, bill_date
# 右列: custom_invoice_type, bill_no
frappe.db.set_value("DocField", {"parent": "Purchase Invoice", "fieldname": "supplier_invoice_details"}, {
    "label": "供应商发票与凭证",
    "hidden": 0
})
frappe.db.set_value("Custom Field", "Purchase Invoice-custom_invoice_type", {
    "insert_after": "column_break_15",
    "hidden": 0
})
frappe.db.set_value("DocField", {"parent": "Purchase Invoice", "fieldname": "bill_no"}, {
    "label": "发票号码",
    "hidden": 0
})
frappe.db.set_value("DocField", {"parent": "Purchase Invoice", "fieldname": "bill_date"}, {
    "label": "开票日期",
    "hidden": 0
})

# 3. 子表 Purchase Invoice Item：标准 3 个 2x2 对称双列
# Section 1: 物料信息 (item_code, col_break1, item_name, description)
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "item_code"}, {"idx": 1, "hidden": 0, "label": "物料编码"})
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "col_break1"}, {"idx": 2, "hidden": 0})
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "item_name"}, {"idx": 3, "hidden": 0, "label": "物料名称"})
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "description"}, {"idx": 4, "hidden": 0, "label": "规格型号 / 描述"})

# Section 2: 数量与含税开票 (quantity_and_rate, qty, custom_gross_rate, col_break2, uom, custom_tax_rate)
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "quantity_and_rate"}, {"idx": 5, "hidden": 0, "label": "数量与含税开票"})
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "qty"}, {"idx": 6, "hidden": 0, "label": "数量"})
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_gross_rate", {"insert_after": "qty", "hidden": 0, "label": "含税单价"})
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "col_break2"}, {"idx": 8, "hidden": 0})
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "uom"}, {"idx": 9, "hidden": 0, "label": "单位"})
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_tax_rate", {"insert_after": "uom", "hidden": 0, "label": "税率 (%)"})

# Section 3: 财税核算与金额 (sec_break2, rate, amount, col_break4, custom_tax_amount, custom_gross_amount, custom_line_remark)
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "sec_break2"}, {"idx": 11, "hidden": 0, "label": "财税核算与金额"})
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "rate"}, {"idx": 12, "hidden": 0, "label": "不含税单价"})
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "amount"}, {"idx": 13, "hidden": 0, "label": "金额 (未税)"})
frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": "col_break4"}, {"idx": 14, "hidden": 0})
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_tax_amount", {"insert_after": "col_break4", "hidden": 0, "label": "税额"})
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_gross_amount", {"insert_after": "custom_tax_amount", "hidden": 0, "label": "价税合计"})
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_line_remark", {"insert_after": "custom_gross_amount", "hidden": 0, "label": "行备注"})

frappe.db.commit()
frappe.clear_cache()
print("[OK] 主表与子表科学双列布局配置完成！")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/apply_scientific_layout.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/apply_scientific_layout.py erpnext16:/tmp/apply_scientific_layout.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/apply_scientific_layout.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
