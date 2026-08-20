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

cmd = """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "ashan_cn_procurement.ashan_cn_procurement.page.lease_settlement_workbench.lease_settlement_workbench.get_settlement" --args "[2026, 7]" """
stdin, stdout, stderr = client.exec_command(cmd)
print("Workbench get_settlement for (2026, 7):")
print(stdout.read().decode('utf-8'))

client.close()
