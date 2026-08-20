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

debug_script = r"""# -*- coding: utf-8 -*-
import json
import frappe
from frappe.utils import flt

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

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
    "rate": 100.0,
    "custom_gross_rate": 113.0,
    "custom_tax_rate": 13.0,
    "custom_spec_model": "M10*50 高强螺栓"
})

vat_acc = frappe.db.get_value("Account", {"account_type": "Tax", "company": comp})
pi.append("taxes", {
    "charge_type": "Actual",
    "account_head": vat_acc,
    "tax_amount": 130.0,
    "description": "进项税额 (增值税)",
    "category": "Total",
    "add_deduct_tax": "Add"
})

pi.save(ignore_permissions=True)

print("Saved PI:", pi.name)
print("Items rate:", [i.rate for i in pi.items])
print("Items amount:", [i.amount for i in pi.items])
print("Net total:", pi.net_total)
print("Total taxes:", pi.total_taxes_and_charges)
print("Grand total:", pi.grand_total)
print("Taxes rows:", [(t.account_head, t.tax_amount) for t in pi.taxes])
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/run_debug.py', 'wb') as f:
    f.write(debug_script.encode('utf-8'))

cmd1 = "docker cp /tmp/run_debug.py erpnext16:/tmp/run_debug.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/run_debug.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("STDOUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
