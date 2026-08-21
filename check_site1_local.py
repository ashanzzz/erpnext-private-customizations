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

# Check Website Settings on site1.local
cmd = "docker exec erpnext16 bash -c \"cd /home/frappe/frappe-bench && bench --site site1.local execute frappe.db.get_value --args '(\\\"Website Settings\\\", \\\"Website Settings\\\", [\\\"home_page\\\", \\\"app_name\\\"])'\""
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print("Website Settings on site1.local:\n", stdout.read().decode('utf-8', errors='replace'))

# Check resolve_path on site1.local
cmd2 = "docker exec erpnext16 bash -c \"cd /home/frappe/frappe-bench && bench --site site1.local execute --args '(\\\"\\\")' frappe.website.path_resolver.resolve_path\""
stdin2, stdout2, stderr2 = ssh.exec_command(cmd2)
stdout2.channel.recv_exit_status()
print("resolve_path('') on site1.local:\n", stdout2.read().decode('utf-8', errors='replace'))

# Check get_home_page on site1.local
cmd3 = "docker exec erpnext16 bash -c \"cd /home/frappe/frappe-bench && bench --site site1.local execute frappe.website.utils.get_home_page\""
stdin3, stdout3, stderr3 = ssh.exec_command(cmd3)
stdout3.channel.recv_exit_status()
print("get_home_page on site1.local:\n", stdout3.read().decode('utf-8', errors='replace'))

ssh.close()
