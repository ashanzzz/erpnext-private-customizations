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

# Test website redirect resolution with python inside bench
test_cmd = """docker exec erpnext16 bash -c "cd /home/frappe/frappe-bench && bench --site erpnext.localhost execute --args '(\\\"\\\")' frappe.website.path_resolver.resolve_path" """
stdin, stdout, stderr = ssh.exec_command(test_cmd)
stdout.channel.recv_exit_status()
print("resolve_path(''):\n", stdout.read().decode('utf-8', errors='replace'))

# Check Website Settings home_page in DB
test_cmd2 = """docker exec erpnext16 bash -c "cd /home/frappe/frappe-bench && bench --site erpnext.localhost execute frappe.db.get_single_value --args '(\\\"Website Settings\\\", \\\"home_page\\\")' " """
stdin2, stdout2, stderr2 = ssh.exec_command(test_cmd2)
stdout2.channel.recv_exit_status()
print("Website Settings home_page:\n", stdout2.read().decode('utf-8', errors='replace'))

ssh.close()
