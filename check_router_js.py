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

# Search workspace_factory or router in frappe public/js
cmd = "docker exec erpnext16 grep -A 40 'class Workspace' /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/views/workspace/workspace.js | head -45"
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print("Workspace class in JS:\n", stdout.read().decode('utf-8', errors='replace'))

# Check router.js for workspace / desk route matching
cmd2 = "docker exec erpnext16 grep -rn 'render_workspace' /home/frappe/frappe-bench/apps/frappe/frappe/public/js/ 2>/dev/null || docker exec erpnext16 grep -rn 'make_page' /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/router.js"
stdin2, stdout2, stderr2 = ssh.exec_command(cmd2)
stdout2.channel.recv_exit_status()
print("\nRouter make_page:\n", stdout2.read().decode('utf-8', errors='replace'))

# Check ashan_cn_boot_route.js
cmd3 = "docker exec erpnext16 cat /home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/ashan_cn_boot_route.js 2>/dev/null || echo 'No ashan_cn_boot_route.js'"
stdin3, stdout3, stderr3 = ssh.exec_command(cmd3)
stdout3.channel.recv_exit_status()
print("\nashan_cn_boot_route.js content:\n", stdout3.read().decode('utf-8', errors='replace'))

ssh.close()
