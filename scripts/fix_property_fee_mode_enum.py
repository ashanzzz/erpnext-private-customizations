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

script = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local')
frappe.connect()

# 1. 批量修复 Property Lease 中的旧 enum 值
frappe.db.sql("UPDATE `tabProperty Lease` SET property_fee_mode = '免物业费' WHERE property_fee_mode = '房租含物业' OR property_fee_mode IS NULL OR property_fee_mode = ''")
frappe.db.sql("UPDATE `tabProperty Lease` SET property_fee_mode = '单独计物业费' WHERE property_fee_mode = '单独计收物业费'")

# 2. 为各租约设定押金
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

# 3. 将 2026-08 改为草稿并重新计算
s_name = 'PROP-SET-2026-08-01'
if frappe.db.exists('Property Monthly Settlement', s_name):
    frappe.db.set_value('Property Monthly Settlement', s_name, 'status', '草稿')

from ashan_cn_procurement.services.property_settlement import get_month_settlement_data, save_draft_settlement
data = get_month_settlement_data(2026, 8)
save_draft_settlement(data)
print("Saved 2026-08 settlement draft successfully!")

frappe.db.commit()
"""

sftp = client.open_sftp()
with sftp.file('/tmp/fix_lease_enum.py', 'wb') as f:
    f.write(script.encode('utf-8'))
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/fix_lease_enum.py erpnext16:/tmp/fix_lease_enum.py && docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 ../env/bin/python /tmp/fix_lease_enum.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
