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

test_script = r"""# -*- coding: utf-8 -*-
import json
import frappe
from frappe.utils import flt

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

# 1. 检查已有的所有 Purchase Invoices
pis = frappe.get_all("Purchase Invoice", fields=["name", "docstatus", "net_total", "grand_total", "creation"])
print("Existing Purchase Invoices in DB:", len(pis))

# 2. 删除测试单据
for p in pis:
    try:
        if p.docstatus == 1:
            doc = frappe.get_doc("Purchase Invoice", p.name)
            doc.cancel()
        frappe.delete_doc("Purchase Invoice", p.name, force=1)
    except Exception as e:
        print("Delete error:", e)
frappe.db.commit()
print("Cleaned up existing invoices!")

# 3. 创建全新多税率发票
comp = frappe.get_all("Company")[0].name
supp_name = "天津市某某科技有限公司"

pi = frappe.new_doc("Purchase Invoice")
pi.company = comp
pi.supplier = supp_name
pi.currency = "CNY"
pi.posting_date = frappe.utils.today()
pi.credit_to = frappe.db.get_value("Account", {"account_type": "Payable", "company": comp})

pi.append("items", {
    "item_code": "ITEM-GOODS-13",
    "qty": 10,
    "custom_gross_rate": 113.0,
    "custom_tax_rate": 13.0,
    "custom_spec_model": "M10*50 高强螺栓"
})

pi.append("items", {
    "item_code": "ITEM-TRANS-9",
    "qty": 1,
    "custom_gross_rate": 109.0,
    "custom_tax_rate": 9.0,
    "custom_spec_model": "天津-北京 往返干线运输"
})

pi.append("items", {
    "item_code": "ITEM-SERV-6",
    "qty": 1,
    "custom_gross_rate": 106.0,
    "custom_tax_rate": 6.0,
    "custom_spec_model": "现场设备调试与技术指导"
})

pi.insert(ignore_permissions=True)
frappe.db.commit()

print("--- NEW PI RESULT ---")
print("PURCHASE_INVOICE_NAME:", pi.name)
print("NET_TOTAL:", pi.net_total)
print("TOTAL_TAXES:", pi.total_taxes_and_charges)
print("GRAND_TOTAL:", pi.grand_total)

for idx, row in enumerate(pi.items, 1):
    print(f"ITEM_{idx}: code={row.item_code} qty={row.qty} gross_rate={row.custom_gross_rate} tax_rate={row.custom_tax_rate}% rate={row.rate} amount={row.amount} tax_amount={row.custom_tax_amount} gross_amount={row.custom_gross_amount}")

# 4. 提交发票过账
pi.submit()
frappe.db.commit()
print("SUBMITTED PI:", pi.name)

# 5. 检查 GL Entry 会计分录
gl_entries = frappe.get_all("GL Entry", filters={"voucher_no": pi.name}, fields=["account", "debit", "credit"])
print("GL_ENTRIES_COUNT:", len(gl_entries))
for gle in gl_entries:
    print(f"GL_ENTRY: {gle['account']} | Dr: {gle['debit']} | Cr: {gle['credit']}")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/run_tax_test.py', 'wb') as f:
    f.write(test_script.encode('utf-8'))

cmd1 = "docker cp /tmp/run_tax_test.py erpnext16:/tmp/run_tax_test.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/run_tax_test.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("STDOUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
