import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

def run_cmd(client, cmd):
    print(f">> {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        print(out)
    if err:
        print("ERR:", err)
    return out, err

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

py_code = """
import frappe
frappe.init(site='site1.local', sites_path='.')
frappe.connect()

from ashan_cn_procurement.tests.test_tax_invoice_suite import run_all_tests
res = run_all_tests()
print('TEST RESULTS:', res)

# 查看 Tax Invoice 表总数和样本
count = frappe.db.count('Tax Invoice')
print('TAX INVOICE TOTAL COUNT:', count)

invoices = frappe.get_all('Tax Invoice', fields=['name', 'company', 'seller_name', 'invoice_grand_total', 'match_status', 'business_status'], limit=5)
print('SAMPLE INVOICES:', invoices)

frappe.destroy()
"""

# 在容器中执行 Python 脚本
sftp = client.open_sftp()
with sftp.file('/tmp/check_tax_inv.py', 'w') as f:
    f.write(py_code)
sftp.close()

run_cmd(client, "docker cp /tmp/check_tax_inv.py erpnext16:/home/frappe/frappe-bench/sites/check_tax_inv.py")
run_cmd(client, "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python check_tax_inv.py")

client.close()
