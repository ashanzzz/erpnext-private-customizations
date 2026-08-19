import os
import json
import paramiko
from dotenv import load_dotenv

load_dotenv()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.getenv('UNRAID_SSH_HOST', '192.168.8.11'), port=int(os.getenv('UNRAID_SSH_PORT', '22')), username=os.getenv('UNRAID_SSH_USER', 'root'), password=os.getenv('UNRAID_SSH_PASSWORD', ''), timeout=15)
stdin, stdout, stderr = client.exec_command("""docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "ashan_cn_procurement.ashan_cn_procurement.page.lease_settlement_workbench.lease_settlement_workbench.get_settlement" --args "[2026, 7]" """)
out = stdout.read().decode('utf-8')
try:
    data = json.loads(out)
    for l in data.get('lease_charges', []):
        print(l.get('property_name'), '-> rent_amount_tax_incl:', l.get('rent_amount_tax_incl'), 'rent_annual_amount:', l.get('rent_annual_amount'), 'rent_rate_snapshot:', l.get('rent_rate_snapshot'))
except Exception as e:
    print("Error:", e, out)
client.close()
