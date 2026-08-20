import os
import json
import paramiko
from dotenv import load_dotenv

load_dotenv()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.getenv('UNRAID_SSH_HOST', '192.168.8.11'), port=int(os.getenv('UNRAID_SSH_PORT', '22')), username=os.getenv('UNRAID_SSH_USER', 'root'), password=os.getenv('UNRAID_SSH_PASSWORD', ''), timeout=15)
stdin, stdout, stderr = client.exec_command("""docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.db.sql('DESCRIBE \\`tabWorkspace Sidebar Item\\`', as_dict=1)" """)
print("Columns:", stdout.read().decode('utf-8'))

stdin, stdout, stderr = client.exec_command("""docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.db.sql('SELECT parent, item_label, link_to, type, idx FROM \\`tabWorkspace Sidebar Item\\` WHERE parent IN (\'My Business\', \'Property and Lease\', \'Vehicle Fuel Hub\', \'Business Extensions\') ORDER BY parent, idx', as_dict=1)" """)
print("Items:", stdout.read().decode('utf-8'))
client.close()
