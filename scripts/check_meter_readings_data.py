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
import json

frappe.init(site='site1.local')
frappe.connect()

from ashan_cn_procurement.services.property_settlement import get_month_settlement_data

for y, m in [(2026, 7), (2026, 8)]:
    data = get_month_settlement_data(y, m)
    print(f"=== Year {y} Month {m} ===")
    print(f"Meter Readings count: {len(data.get('meter_readings', []))}")
    for mr in data.get('meter_readings', [])[:5]:
        print(f"  Meter: {mr.get('meter_no')} | Comp: {mr.get('company')} | Type: {mr.get('utility_type')} | Prev: {mr.get('previous_reading')} | Curr: {mr.get('current_reading')} | Usage: {mr.get('usage')} | Mult: {mr.get('multiplier')} | SettleUsage: {mr.get('settlement_usage')} | Amount: {mr.get('amount')}")
    print(f"Company summaries count: {len(data.get('company_summaries', []))}")
    for cs in data.get('company_summaries', []):
        print(f"  Summary: {cs.get('company')} | Elec: {cs.get('electricity_amount')} | Water: {cs.get('water_amount')} | Tot: {cs.get('total_amount')}")
"""

sftp = client.open_sftp()
with sftp.file('/tmp/check_meters.py', 'wb') as f:
    f.write(script.encode('utf-8'))
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/check_meters.py erpnext16:/tmp/check_meters.py && docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 ../env/bin/python /tmp/check_meters.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
