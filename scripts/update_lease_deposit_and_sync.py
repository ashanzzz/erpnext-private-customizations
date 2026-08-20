import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

script = """import frappe

frappe.init(site='site1.local')
frappe.connect()

# 更新租约的押金金额
leases = frappe.get_all('Property Lease', fields=['name', 'property_name', 'area', 'deposit_amount'])
for l in leases:
    doc = frappe.get_doc('Property Lease', l.name)
    if '3338' in doc.property_name:
        doc.deposit_amount = 100000.00
    elif '930' in doc.property_name:
        doc.deposit_amount = 30000.00
    elif '360' in doc.property_name:
        doc.deposit_amount = 10000.00
    else:
        doc.deposit_amount = 20000.00
    doc.save(ignore_permissions=True)
    print(f"Updated {doc.name}: deposit = {doc.deposit_amount}")

# 重新计算并保存当月月结草稿
from ashan_cn_procurement.services.property_settlement import get_month_settlement_data, save_draft_settlement
data = get_month_settlement_data(2026, 8)
save_draft_settlement(data)
print("Saved 2026-08 settlement draft with new structure!")

frappe.db.commit()
"""

sftp = client.open_sftp()
with sftp.file('/tmp/update_lease_deposit.py', 'wb') as f:
    f.write(script.encode('utf-8'))
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/update_lease_deposit.py erpnext16:/tmp/update_lease_deposit.py && docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 ../env/bin/python /tmp/update_lease_deposit.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
