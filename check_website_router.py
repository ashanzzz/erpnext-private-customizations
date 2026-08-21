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

# Check Frappe's website router resolution for "/"
cmd = "docker exec erpnext16 grep -rn 'get_website_user_home_page' /home/frappe/frappe-bench/apps/frappe/"
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print("get_website_user_home_page occurrences:\n", stdout.read().decode('utf-8', errors='replace'))

# Check how Frappe resolves home_page in website routing
cmd2 = "docker exec erpnext16 grep -A 25 'def get_home_page' /home/frappe/frappe-bench/apps/frappe/frappe/website/utils.py 2>/dev/null || docker exec erpnext16 grep -rn 'def get_home_page' /home/frappe/frappe-bench/apps/frappe/"
stdin2, stdout2, stderr2 = ssh.exec_command(cmd2)
stdout2.channel.recv_exit_status()
print("\ndef get_home_page:\n", stdout2.read().decode('utf-8', errors='replace'))

# Check Website Settings
cmd3 = "docker exec erpnext16 bash -c \"cd /home/frappe/frappe-bench && bench --site erpnext.localhost execute frappe.db.get_value --args '(\\\"Website Settings\\\", \\\"Website Settings\\\", [\\\"home_page\\\", \\\"app_name\\\"])'\""
stdin3, stdout3, stderr3 = ssh.exec_command(cmd3)
stdout3.channel.recv_exit_status()
print("\nWebsite Settings values:\n", stdout3.read().decode('utf-8', errors='replace'))

ssh.close()
