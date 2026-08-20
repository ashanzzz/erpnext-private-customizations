import os
import json
import paramiko
from dotenv import load_dotenv

load_dotenv()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.getenv('UNRAID_SSH_HOST', '192.168.8.11'), port=int(os.getenv('UNRAID_SSH_PORT', '22')), username=os.getenv('UNRAID_SSH_USER', 'root'), password=os.getenv('UNRAID_SSH_PASSWORD', ''), timeout=15)
stdin, stdout, stderr = client.exec_command("""docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.db.sql('SELECT name, property_name, area, rent_annual_amount, rent_pricing_mode, enabled FROM \\`tabProperty Lease\\`', as_dict=1)" """)
print("DB Leases:", stdout.read().decode('utf-8'))
client.close()
