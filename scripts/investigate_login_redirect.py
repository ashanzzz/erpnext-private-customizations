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

print("=== 1. frappe/www/login.py ===")
out, _ = run_cmd(client, "docker exec erpnext16 cat /home/frappe/frappe-bench/apps/frappe/frappe/www/login.py")
print(out)

print("=== 2. check /apps endpoint and www/apps.py ===")
out, _ = run_cmd(client, "docker exec erpnext16 find /home/frappe/frappe-bench/apps/frappe -name 'apps.py' -o -name 'apps.html'")
print(out)
out, _ = run_cmd(client, "docker exec erpnext16 cat /home/frappe/frappe-bench/apps/frappe/frappe/www/apps.py 2>/dev/null")
print(out)

print("=== 3. user.py get_default_path / redirect ===")
out, _ = run_cmd(client, "docker exec erpnext16 sed -n '965,990p' /home/frappe/frappe-bench/apps/frappe/frappe/core/doctype/user/user.py 2>/dev/null")
print(out)

print("=== 4. check System Settings fields ===")
out, _ = run_cmd(client, """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.get_meta('System Settings').get_field('default_app')" """)
print(out)

print("=== 5. check User fields related to default_app ===")
out, _ = run_cmd(client, """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.get_meta('User').get_field('default_app')" """)
print(out)

client.close()
