import os
import sys
import paramiko
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

def run_bench_eval(py_code):
    remote_script = f"/tmp/check_oil.py"
    sftp = client.open_sftp()
    with sftp.file(remote_script, 'w') as f:
        f.write(py_code)
    sftp.close()

    client.exec_command(f"docker cp {remote_script} erpnext16:{remote_script}")
    cmd = f"docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 /home/frappe/frappe-bench/env/bin/python {remote_script}"
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print("OUTPUT:\n", out)
    if err: print("ERR:\n", err)

code = """
import sys
sys.path.insert(0, '/home/frappe/frappe-bench/apps/frappe')
sys.path.insert(0, '/home/frappe/frappe-bench/apps/erpnext')
sys.path.insert(0, '/home/frappe/frappe-bench/apps/ashan_cn_procurement')

import frappe
frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

cards = frappe.get_all('Oil Card', fields=['name', 'card_name', 'opening_balance', 'current_balance'])
print('Cards:', cards)

closings = frappe.get_all('Oil Card Monthly Closing', fields=['name', 'oil_card', 'fiscal_year', 'fiscal_month', 'is_locked', 'closing_balance'])
print('Closings:', closings)

recharges = frappe.get_all('Oil Card Recharge', fields=['name', 'oil_card', 'posting_date', 'effective_amount'])
refuels = frappe.get_all('Oil Card Refuel Log', fields=['name', 'oil_card', 'posting_date', 'amount'])
print(f'Total Recharges: {len(recharges)}, Total Refuels: {len(refuels)}')
"""

run_bench_eval(code)
client.close()
