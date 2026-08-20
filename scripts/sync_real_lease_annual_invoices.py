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

# 1. 查找 3338 平米的租约并注入真实发票数据
leases = frappe.get_all('Property Lease', fields=['name', 'property_name', 'company'])
for l in leases:
    doc = frappe.get_doc('Property Lease', l.name)
    if '3338' in doc.property_name and '空港' in doc.property_name:
        doc.area = 3338.0
        doc.deposit_amount = 100000.00
        doc.start_date = '2025-09-22'
        doc.end_date = '2026-09-21'
        doc.rent_annual_amount = 959466.00
        doc.rent_invoice_no = '25122000000068752502'
        doc.rent_invoice_date = '2025-09-23'
        doc.rent_invoice_amount = 959466.00
        doc.rent_invoice_tax = 45688.86

        doc.property_fee_mode = '单独计物业费'
        doc.property_fee_pricing_mode = '按年单价 (元/㎡·年)'
        doc.property_fee_annual_rate = 18.00
        doc.property_fee_annual_amount = 60084.00
        doc.property_fee_invoice_no = '25122000000068723440'
        doc.property_fee_invoice_date = '2025-09-23'
        doc.property_fee_invoice_amount = 60084.00
        doc.property_fee_invoice_tax = 3400.98
        doc.invoice_status = '全额已开票'
        doc.save(ignore_permissions=True)
        print(f"Injected Real Invoice to {doc.name}")
    elif '930' in doc.property_name:
        doc.deposit_amount = 30000.00
        doc.start_date = '2026-07-01'
        doc.end_date = '2027-06-30'
        doc.rent_annual_amount = 238800.00
        doc.property_fee_mode = '免物业费'
        doc.save(ignore_permissions=True)

frappe.db.commit()
print("Committed lease invoice updates!")
"""

sftp = client.open_sftp()
with sftp.file('/tmp/sync_real_invoices.py', 'wb') as f:
    f.write(script.encode('utf-8'))
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/sync_real_invoices.py erpnext16:/tmp/sync_real_invoices.py && docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 ../env/bin/python /tmp/sync_real_invoices.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
