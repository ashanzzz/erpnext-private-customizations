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

insert_committed_py = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

supplier = frappe.db.get_value("Supplier", {}, "name") or "测试供应商"
item_code = frappe.db.get_value("Item", {"is_purchase_item": 1}, "name")
company = frappe.db.get_value("Company", {}, "name")

test_bill_no = "FP-2026-88888888"
frappe.db.sql("DELETE FROM `tabPurchase Invoice` WHERE bill_no = %s", (test_bill_no,))

doc = frappe.get_doc({
    "doctype": "Purchase Invoice",
    "company": company,
    "supplier": supplier,
    "custom_invoice_type": "专用发票",
    "bill_no": test_bill_no,
    "bill_date": "2026-08-14",
    "items": [{
        "item_code": item_code,
        "qty": 1,
        "rate": 100,
        "custom_tax_rate": 13
    }]
})
doc.insert(ignore_permissions=True)
frappe.db.commit()

print(f"[OK] Committed Invoice: {doc.name} with bill_no: {test_bill_no}")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/insert_committed.py', 'wb') as f:
    f.write(insert_committed_py.encode('utf-8'))

cmd1 = "docker cp /tmp/insert_committed.py erpnext16:/tmp/insert_committed.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/insert_committed.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
