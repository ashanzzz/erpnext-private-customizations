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

print("--- 构建极具对称美感的两分区平衡布局 ---")

# Section 1: 物料信息 (item_code, col_break1, item_name, description)
# Section 2: 数量、单价与财税核算 (quantity_and_rate)
#   左列: qty, rate, amount, custom_line_remark
#   列断: col_break2
#   右列: uom, custom_gross_rate, custom_tax_rate, custom_tax_amount, custom_gross_amount

field_config = [
    # 分区 1: 物料基本信息
    ("item_code", 1, 0, "物料编码"),
    ("col_break1", 2, 0, ""),
    ("item_name", 3, 0, "物料名称"),
    ("description", 4, 0, "规格型号 / 描述"),
    
    # 分区 2: 数量与财税核算
    ("quantity_and_rate", 5, 0, "数量与财税核算"),
    # 左列
    ("qty", 6, 0, "数量"),
    ("rate", 7, 0, "不含税单价"),
    ("amount", 8, 0, "金额 (未税)"),
    ("custom_line_remark", 9, 0, "行备注"),
    # 列断
    ("col_break2", 10, 0, ""),
    # 右列 (完美对应: 单位、含税单价、税率、税额、价税合计)
    ("uom", 11, 0, "单位"),
    ("custom_gross_rate", 12, 0, "含税单价"),
    ("custom_tax_rate", 13, 0, "税率 (%)"),
    ("custom_tax_amount", 14, 0, "税额"),
    ("custom_gross_amount", 15, 0, "价税合计")
]

# 隐藏所有其他字段
all_dfs = frappe.db.get_all("DocField", filters={"parent": "Purchase Invoice Item"}, fields=["name", "fieldname"])
config_fns = [item[0] for item in field_config]

for df in all_dfs:
    if df.fieldname not in config_fns:
        frappe.db.set_value("DocField", df.name, "hidden", 1)

# 应用配置
for fn, idx, hid, lbl in field_config:
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
print("[OK] 对称结构设置完成！")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/build_symmetric_sections.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/build_symmetric_sections.py erpnext16:/tmp/build_symmetric_sections.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/build_symmetric_sections.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
