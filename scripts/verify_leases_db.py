import os
import json
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

cmd = """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.db.sql('SELECT name, company, property_name, supplier, area, property_certificate_no, location_address, rent_pricing_mode, rent_annual_amount, rent_monthly_amount, rent_daily_rate, rent_tax_rate, property_fee_mode, property_fee_tax_rate, total_annual_amount FROM \\`tabProperty Lease\\`', as_dict=1)" """
stdin, stdout, stderr = client.exec_command(cmd)
out = stdout.read().decode('utf-8', errors='replace')
print("Lease records:")
try:
    records = json.loads(out)
    for r in records:
        print(json.dumps(r, ensure_ascii=False, indent=2))
except Exception as e:
    print(out)

client.close()
