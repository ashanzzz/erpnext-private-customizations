import os
import paramiko

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()
HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER_SSH = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER_SSH, password=PASSWORD, timeout=10)

# Check Workspace doctype records in ERPNext
cmd1 = "docker exec erpnext16 bash -c \"cd /home/frappe/frappe-bench && bench --site erpnext.localhost execute frappe.db.get_list --args '(\\\"Workspace\\\", fields=[\\\"name\\\", \\\"title\\\", \\\"public\\\", \\\"for_user\\\"], limit_page_length=50)' 2>/dev/null\""
stdin1, stdout1, stderr1 = ssh.exec_command(cmd1)
stdout1.channel.recv_exit_status()
print("Workspaces in DB:\n", stdout1.read().decode('utf-8', errors='replace'))

# Check hooks.py in ashan_cn_procurement
cmd2 = "docker exec erpnext16 cat /home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/hooks.py"
stdin2, stdout2, stderr2 = ssh.exec_command(cmd2)
stdout2.channel.recv_exit_status()
print("\nhooks.py:\n", stdout2.read().decode('utf-8', errors='replace'))

# Check ashan_cn_boot_route.js
cmd3 = "docker exec erpnext16 cat /home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/public/js/ashan_cn_boot_route.js 2>/dev/null || echo 'NOT FOUND'"
stdin3, stdout3, stderr3 = ssh.exec_command(cmd3)
stdout3.channel.recv_exit_status()
print("\nashan_cn_boot_route.js:\n", stdout3.read().decode('utf-8', errors='replace'))

ssh.close()
