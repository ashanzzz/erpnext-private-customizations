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

print("--- 开始规格型号向 Description 全面迁移 ---")

# 1. 迁移历史数据：将 custom_spec_model 的值合并回填到 description (若有的话)
tables = [
    ("tabPurchase Invoice Item", "Purchase Invoice Item"),
    ("tabPurchase Order Item", "Purchase Order Item"),
    ("tabPurchase Receipt Item", "Purchase Receipt Item"),
    ("tabMaterial Request Item", "Material Request Item")
]

for table_name, dt in tables:
    cols = frappe.db.get_table_columns(dt)
    if "custom_spec_model" in cols:
        print(f"迁移 {dt} 的 custom_spec_model 数据至 description...")
        frappe.db.sql(f'''
            UPDATE `{table_name}`
            SET description = custom_spec_model
            WHERE custom_spec_model IS NOT NULL 
              AND custom_spec_model != '' 
              AND (description IS NULL OR description = '' OR description = item_name OR description = item_code)
        ''')

# 2. 将所有涉及物料行及 Item 主数据的 description 字段类型改为 Data (单行文本)，标签为 "规格型号 / 描述"
for dt in ["Purchase Invoice Item", "Purchase Order Item", "Purchase Receipt Item", "Material Request Item", "Item"]:
    frappe.make_property_setter({
        "doctype": dt,
        "fieldname": "description",
        "property": "fieldtype",
        "value": "Data",
        "property_type": "Select"
    }, validate_fields_for_doctype=False)

    frappe.make_property_setter({
        "doctype": dt,
        "fieldname": "description",
        "property": "label",
        "value": "规格型号 / 说明",
        "property_type": "Data"
    }, validate_fields_for_doctype=False)

# 3. 设置 Purchase Invoice Item 中的 description 在子表网格中展示 (in_list_view: 1, columns: 2)
frappe.make_property_setter({
    "doctype": "Purchase Invoice Item",
    "fieldname": "description",
    "property": "in_list_view",
    "value": "1",
    "property_type": "Check"
}, validate_fields_for_doctype=False)

frappe.make_property_setter({
    "doctype": "Purchase Invoice Item",
    "fieldname": "description",
    "property": "columns",
    "value": "2",
    "property_type": "Int"
}, validate_fields_for_doctype=False)

# 4. 删除所有 custom_spec_model Custom Fields
deleted_cfs = []
for dt in ["Purchase Invoice Item", "Purchase Order Item", "Purchase Receipt Item", "Material Request Item"]:
    cf_name = f"{dt}-custom_spec_model"
    if frappe.db.exists("Custom Field", cf_name):
        frappe.db.delete("Custom Field", {"name": cf_name})
        deleted_cfs.append(cf_name)

print("已删除的 custom_spec_model Custom Fields:", deleted_cfs)

frappe.db.commit()
frappe.clear_cache()
print("[OK] 全面迁移与清理完成！")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/migrate_spec_to_desc.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/migrate_spec_to_desc.py erpnext16:/tmp/migrate_spec_to_desc.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/migrate_spec_to_desc.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
