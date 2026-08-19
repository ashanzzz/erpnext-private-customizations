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

print("=== 1. get_apps() ===")
out, _ = run_cmd(client, "docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute frappe.apps.get_apps")
print(out)

print("=== 2. System Settings ===")
out, _ = run_cmd(client, """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.db.get_value('System Settings', None, 'default_app')" """)
print("System Settings default_app:", out)

print("=== 3. Users default_app ===")
out, _ = run_cmd(client, """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.db.get_all('User', fields=['name', 'default_app'])" """)
print("Users:", out)

print("=== 4. Check all hooks add_to_apps_screen ===")
out, _ = run_cmd(client, """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.get_hooks('add_to_apps_screen')" """)
print("add_to_apps_screen:", out)

print("=== 5. Check all hooks website_user_home_page / role_home_page ===")
out, _ = run_cmd(client, """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.get_hooks('get_website_user_home_page')" """)
print("get_website_user_home_page hooks:", out)

print("=== 6. Check login flow in auth.py ===")
out, _ = run_cmd(client, "docker exec erpnext16 grep -n -C 5 'redirect_to\\|home_page\\|get_default_path' /home/frappe/frappe-bench/apps/frappe/frappe/auth.py")
print(out)

print("=== 7. Check /apps or website route routing ===")
out, _ = run_cmd(client, "docker exec erpnext16 grep -rn 'get_default_path' /home/frappe/frappe-bench/apps/frappe/")
print(out)

client.close()
