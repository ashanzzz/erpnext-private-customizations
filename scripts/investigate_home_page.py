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

# 1. Key: desk.js around line 383 - what home_page check does
print("=== frappe/desk.js lines 370-410 ===")
out, _ = run_cmd(client, "docker exec erpnext16 sed -n '370,415p' /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/desk.js 2>/dev/null")
print(out)

# 2. pageview.js line 52 context
print("\n=== frappe/views/pageview.js lines 45-65 ===")
out, _ = run_cmd(client, "docker exec erpnext16 sed -n '44,68p' /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/views/pageview.js 2>/dev/null")
print(out)

# 3. Check the Workspace "my-business" - what name does the DB have
print("\n=== DB: All Workspaces name+title ===")
out, _ = run_cmd(client, """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.db.sql(\\\"SELECT name,title FROM \\`tabWorkspace\\` LIMIT 30\\\", as_dict=1)" """)
print(out)

# 4. Check what the my_business.json workspace_sidebar looks like
print("\n=== workspace_sidebar my_business.json ===")
out, _ = run_cmd(client, "docker exec erpnext16 cat /home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/workspace_sidebar/my_business.json 2>/dev/null")
print(out[:3000])

# 5. Check if there's a custom Page "my-business" in DB
print("\n=== DB: All Pages ===")
out, _ = run_cmd(client, """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.db.sql(\\\"SELECT name, title, module FROM \\`tabPage\\` ORDER BY name LIMIT 50\\\", as_dict=1)" """)
print(out[:3000])

# 6. desk.js init / show_home_page / navigate_to flow
print("\n=== desk.js navigate_to / home_page init ===")
out, _ = run_cmd(client, "docker exec erpnext16 grep -n 'home_page\\|navigate_to\\|show_page\\|boot.home' /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/desk.js 2>/dev/null | head -30")
print(out)

# 7. What does the get_default_path return for System Manager now?
print("\n=== get_default_path result for sys manager ===")
out, _ = run_cmd(client, """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.apps.get_default_path" """)
print(out)

client.close()
