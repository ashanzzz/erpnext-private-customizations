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

print("--- 构建 3 个 2x2 完美对称卡片布局 ---")

# 1. 解锁并配置必要字段与断点
fields_to_show = {
    # 物料信息
    "item_code": (1, "物料编码"),
    "col_break1": (2, ""),
    "item_name": (3, "物料名称"),
    "description": (4, "规格型号 / 描述"),
    # 分区 2: 数量与含税开票
    "quantity_and_rate": (5, "数量与含税信息"),
    "qty": (6, "数量"),
    "custom_gross_rate": (7, "含税单价"),
    "col_break2": (8, ""),
    "uom": (9, "单位"),
    "custom_tax_rate": (10, "税率 (%)"),
    # 分区 3: 不含税金额与税额核算
    "sec_break2": (11, "未税金额与税额核算"),
    "rate": (12, "不含税单价"),
    "amount": (13, "金额 (未税)"),
    "col_break4": (14, ""),
    "custom_tax_amount": (15, "税额"),
    "custom_gross_amount": (16, "价税合计"),
    "custom_line_remark": (17, "行备注")
}

# 隐藏所有其他字段
all_dfs = frappe.db.get_all("DocField", filters={"parent": "Purchase Invoice Item"}, fields=["name", "fieldname"])
for df in all_dfs:
    if df.fieldname not in fields_to_show:
        frappe.db.set_value("DocField", df.name, "hidden", 1)

# 应用显隐与顺序
for fn, (idx, lbl) in fields_to_show.items():
    if frappe.db.exists("DocField", {"parent": "Purchase Invoice Item", "fieldname": fn}):
        updates = {"idx": idx, "hidden": 0}
        if lbl:
            updates["label"] = lbl
        frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": fn}, updates)
    elif frappe.db.exists("Custom Field", {"dt": "Purchase Invoice Item", "fieldname": fn}):
        updates = {"hidden": 0}
        if lbl:
            updates["label"] = lbl
        frappe.db.set_value("Custom Field", {"dt": "Purchase Invoice Item", "fieldname": fn}, updates)

frappe.db.commit()
frappe.clear_cache(doctype="Purchase Invoice")
frappe.clear_cache(doctype="Purchase Invoice Item")
print("[OK] 3 个 2x2 完美对称卡片构建完成！")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/build_3_cards.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/build_3_cards.py erpnext16:/tmp/build_3_cards.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/build_3_cards.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
