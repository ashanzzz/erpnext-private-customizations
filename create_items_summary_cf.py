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

create_cf_py = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

print("--- 1. 创建/更新 Custom Field: Purchase Invoice - custom_items_summary ---")
cf_name = "Purchase Invoice-custom_items_summary"

if not frappe.db.exists("Custom Field", cf_name):
    cf = frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Purchase Invoice",
        "fieldname": "custom_items_summary",
        "label": "开票物料明细",
        "fieldtype": "Small Text",
        "insert_after": "bill_no",
        "in_list_view": 1,
        "in_standard_filter": 1,
        "in_global_search": 1,
        "read_only": 1,
        "columns": 3,
        "module": "Ashan CN Procurement"
    })
    cf.insert(ignore_permissions=True)
    print(f"[OK] 创建 Custom Field {cf_name} 成功！")
else:
    cf = frappe.get_doc("Custom Field", cf_name)
    cf.label = "开票物料明细"
    cf.in_list_view = 1
    cf.in_standard_filter = 1
    cf.in_global_search = 1
    cf.read_only = 1
    cf.columns = 3
    cf.save(ignore_permissions=True)
    print(f"[OK] 更新 Custom Field {cf_name} 成功！")

frappe.db.commit()

print("\\n--- 2. 批量回填历史采购发票的【开票物料明细】 ---")
invoices = frappe.get_all("Purchase Invoice", fields=["name"])
print(f"共找到 {len(invoices)} 张采购发票待同步...")

def get_items_summary(doc):
    if not doc.items:
        return "无物料"
    item_strs = []
    for it in doc.items:
        name = (it.item_name or it.item_code or "").strip()
        qty = float(it.qty or 0)
        qty_str = f"{qty:g}"
        item_strs.append(f"{name} (x{qty_str})")
    
    if len(item_strs) > 3:
        return "、".join(item_strs[:3]) + f" 等共{len(item_strs)}项"
    return "、".join(item_strs)

updated_count = 0
for inv in invoices:
    doc = frappe.get_doc("Purchase Invoice", inv.name)
    summary = get_items_summary(doc)
    frappe.db.set_value("Purchase Invoice", inv.name, "custom_items_summary", summary, update_modified=False)
    updated_count += 1
    print(f"  [{inv.name}]: {summary}")

frappe.db.commit()
frappe.clear_cache(doctype="Purchase Invoice")
print(f"[OK] 成功同步 {updated_count} 张发票的物料明细！")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/create_items_summary_cf.py', 'wb') as f:
    f.write(create_cf_py.encode('utf-8'))

cmd1 = "docker cp /tmp/create_items_summary_cf.py erpnext16:/tmp/create_items_summary_cf.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/create_items_summary_cf.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
