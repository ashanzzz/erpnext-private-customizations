import os
import json
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

setup_script = """
import os
import sys
import json
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

# 1. 确保税费会计科目 (Input VAT)
companies = frappe.get_all("Company", fields=["name", "abbr", "default_currency"])
for comp in companies:
    # 查找或创建 应交增值税 / 进项税额 科目
    tax_acc = frappe.db.get_value("Account", {"account_type": "Tax", "company": comp.name})
    if not tax_acc:
        parent = frappe.db.get_value("Account", {"is_group": 1, "account_name": ["like", "%税%"], "company": comp.name}) or \
                 frappe.db.get_value("Account", {"is_group": 1, "root_type": "Liability", "company": comp.name})
        if parent:
            new_acc = frappe.get_doc({
                "doctype": "Account",
                "account_name": "进项税额",
                "company": comp.name,
                "parent_account": parent,
                "account_type": "Tax"
            })
            new_acc.insert(ignore_permissions=True)
            print(f"[OK] Created Tax Account: {new_acc.name}")
        else:
            print(f"[WARN] Parent account not found for company {comp.name}")
    else:
        print(f"[OK] Found Tax Account: {tax_acc} for {comp.name}")

# 2. 检查与优化 Custom Fields 在 Purchase Invoice Item 上的显示属性
fields_to_ensure = [
    {
        "dt": "Purchase Invoice Item",
        "fieldname": "custom_gross_rate",
        "label": "含税单价",
        "fieldtype": "Currency",
        "options": "currency",
        "insert_after": "qty",
        "in_list_view": 1,
        "columns": 2
    },
    {
        "dt": "Purchase Invoice Item",
        "fieldname": "custom_tax_rate",
        "label": "税率(%)",
        "fieldtype": "Percent",
        "insert_after": "custom_gross_rate",
        "in_list_view": 1,
        "columns": 1,
        "default": "13"
    },
    {
        "dt": "Purchase Invoice Item",
        "fieldname": "custom_tax_amount",
        "label": "税额",
        "fieldtype": "Currency",
        "options": "currency",
        "insert_after": "amount",
        "in_list_view": 1,
        "columns": 1,
        "read_only": 0
    },
    {
        "dt": "Purchase Invoice Item",
        "fieldname": "custom_gross_amount",
        "label": "价税合计",
        "fieldtype": "Currency",
        "options": "currency",
        "insert_after": "custom_tax_amount",
        "in_list_view": 1,
        "columns": 2,
        "read_only": 0
    },
    {
        "dt": "Purchase Invoice Item",
        "fieldname": "custom_spec_model",
        "label": "规格型号",
        "fieldtype": "Data",
        "insert_after": "item_name",
        "in_list_view": 1,
        "columns": 1
    },
    {
        "dt": "Purchase Invoice Item",
        "fieldname": "custom_line_remark",
        "label": "行备注",
        "fieldtype": "Data",
        "insert_after": "custom_gross_amount",
        "in_list_view": 0
    }
]

for f in fields_to_ensure:
    name = f"{f['dt']}-{f['fieldname']}"
    if frappe.db.exists("Custom Field", name):
        doc = frappe.get_doc("Custom Field", name)
        doc.update(f)
        doc.save(ignore_permissions=True)
        print(f"[OK] Updated Custom Field {name}")
    else:
        doc = frappe.new_doc("Custom Field")
        doc.update(f)
        doc.name = name
        doc.insert(ignore_permissions=True)
        print(f"[OK] Created Custom Field {name}")

frappe.db.commit()
print("[ALL OK] Custom fields and tax accounts configured successfully!")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/setup_china_tax.py', 'wb') as f:
    f.write(setup_script.encode('utf-8'))

cmd0 = "docker exec erpnext16 bash -c 'mkdir -p /home/frappe/frappe-bench/sites/site1.local/logs && chown -R frappe:frappe /home/frappe/frappe-bench/sites/site1.local/logs'"
ssh.exec_command(cmd0)[1].channel.recv_exit_status()

cmd1 = "docker cp /tmp/setup_china_tax.py erpnext16:/tmp/setup_china_tax.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/setup_china_tax.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
print("STDOUT:", stdout.read().decode('utf-8'))
print("STDERR:", stderr.read().decode('utf-8'))

sftp.close()
ssh.close()
