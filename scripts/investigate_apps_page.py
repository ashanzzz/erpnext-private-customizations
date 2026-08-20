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

print("=== 1. Find /apps web page / route in frappe ===")
out, _ = run_cmd(client, "docker exec erpnext16 find /home/frappe/frappe-bench/apps/frappe/frappe/www -name '*app*'")
print(out)

print("=== 2. Check www/apps.html or www/apps.py ===")
out, _ = run_cmd(client, "docker exec erpnext16 cat /home/frappe/frappe-bench/apps/frappe/frappe/www/apps.html 2>/dev/null")
print(out[:1000])

print("=== 3. Check what is the default_app in System Settings ===")
out, _ = run_cmd(client, "docker exec erpnext16 grep -rn 'default_app' /home/frappe/frappe-bench/apps/frappe/frappe/core/doctype/system_settings/ 2>/dev/null")
print(out)

print("=== 4. Check how Frappe 16 determines home page / apps switch ===")
out, _ = run_cmd(client, "docker exec erpnext16 grep -rn 'add_to_apps_screen' /home/frappe/frappe-bench/apps/ 2>/dev/null")
print(out)

client.close()
