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

comp = frappe.get_all("Company")[0].name
supp_name = "天津市某某科技有限公司"

# 1. 创建包含 3 种不同税率 (13%, 9%, 6%) 的多税率采购发票
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

print("==================================================")
print(" PURCHASE_INVOICE_NAME: ", pi.name)
print("==================================================")
print("NET_TOTAL   : CNY ", pi.net_total)
print("TOTAL_TAXES : CNY ", pi.total_taxes_and_charges)
print("GRAND_TOTAL : CNY ", pi.grand_total)

for idx, row in enumerate(pi.items, 1):
    print(f"ROW #{idx} [{row.custom_tax_rate}% TAX] {row.item_name} ({row.custom_spec_model})")
    print(f"       QTY: {row.qty} | GROSS_RATE: {row.custom_gross_rate} -> RATE: {row.rate} | AMOUNT: {row.amount} | TAX: {row.custom_tax_amount} | GROSS_AMOUNT: {row.custom_gross_amount}")

# 2. 提交发票过账
pi.submit()
frappe.db.commit()
print("\n[OK] SUBMITTED SUCCESS: ", pi.name)

# 3. 检查 GL Entry 会计分录
gl_entries = frappe.get_all("GL Entry", filters={"voucher_no": pi.name}, fields=["account", "debit", "credit"])
print("\n==================================================")
print(" GL Entries (Accounting Ledger)")
print("==================================================")
for gle in gl_entries:
    d = f"CNY {gle['debit']}" if flt(gle['debit']) > 0 else "-"
    c = f"CNY {gle['credit']}" if flt(gle['credit']) > 0 else "-"
    print(f"  {gle['account']:<35} | Dr: {d:<14} | Cr: {c:<14}")
print("==================================================")

with open('/tmp/last_created_pi.txt', 'w', encoding='utf-8') as f:
    f.write(pi.name)
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
print("OUTPUT:\n", out.encode('ascii', errors='replace').decode('ascii'))
if err:
    print("STDERR:\n", err.encode('ascii', errors='replace').decode('ascii'))

cmd3 = "docker cp erpnext16:/tmp/last_created_pi.txt /tmp/last_created_pi.txt"
ssh.exec_command(cmd3)[1].channel.recv_exit_status()
with sftp.open('/tmp/last_created_pi.txt', 'r', encoding='utf-8') as f:
    created_pi_name = f.read().strip()
print(f"Last Created PI: {created_pi_name}")

sftp.close()
ssh.close()
