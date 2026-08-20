import json
import os

import paramiko
from dotenv import load_dotenv


load_dotenv()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    os.getenv("UNRAID_SSH_HOST", "192.168.8.11"),
    port=int(os.getenv("UNRAID_SSH_PORT", "22")),
    username=os.getenv("UNRAID_SSH_USER", "root"),
    password=os.getenv("UNRAID_SSH_PASSWORD", ""),
    timeout=15,
)

expression = (
    "frappe.get_all('Workspace Sidebar Item', "
    "filters={'parent': ['in', ['My Business', 'Property and Lease', "
    "'Vehicle Fuel Hub', 'Ashan CN Procurement', 'Home']]}, "
    "fields=['parent', 'label', 'link_to', 'link_type', 'type', 'idx'], "
    "order_by='parent asc, idx asc')"
)
remote_command = (
    "docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 "
    "bench --site site1.local execute " + json.dumps(expression)
)
stdin, stdout, stderr = client.exec_command(remote_command)
print("Items:", stdout.read().decode("utf-8"))
client.close()
