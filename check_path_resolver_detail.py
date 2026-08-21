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

# Check path_resolver.py
cmd = "docker exec erpnext16 sed -n '1,60p' /home/frappe/frappe-bench/apps/frappe/frappe/website/path_resolver.py"
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print("path_resolver.py top:\n", stdout.read().decode('utf-8', errors='replace'))

# Check website_route_rules hook in frappe
cmd2 = "docker exec erpnext16 grep -A 20 'website_route_rules' /home/frappe/frappe-bench/apps/frappe/frappe/hooks.py"
stdin2, stdout2, stderr2 = ssh.exec_command(cmd2)
stdout2.channel.recv_exit_status()
print("\nfrappe hooks website_route_rules:\n", stdout2.read().decode('utf-8', errors='replace'))

# Check website_redirects hook in frappe
cmd3 = "docker exec erpnext16 grep -A 20 'website_redirects' /home/frappe/frappe-bench/apps/frappe/frappe/hooks.py"
stdin3, stdout3, stderr3 = ssh.exec_command(cmd3)
stdout3.channel.recv_exit_status()
print("\nfrappe hooks website_redirects:\n", stdout3.read().decode('utf-8', errors='replace'))

ssh.close()
