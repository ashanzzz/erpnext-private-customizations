import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

def run_cmd(client, cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace'), stderr.read().decode('utf-8', errors='replace')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

print("=== 1. Check get_route ===")
out, _ = run_cmd(client, """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.apps.get_route" --args "['ashan_cn_procurement']" """)
print("get_route(ashan_cn_procurement):", out)

print("=== 2. Check get_default_path before setting ===")
out, _ = run_cmd(client, """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.apps.get_default_path" """)
print("get_default_path():", out)

client.close()
