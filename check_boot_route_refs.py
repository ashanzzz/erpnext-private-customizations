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

# Check all places where ashan_cn_boot_route.js is referenced
cmd = "docker exec erpnext16 grep -rn 'ashan_cn_boot_route' /home/frappe/frappe-bench/apps/ /home/frappe/frappe-bench/sites/ 2>/dev/null"
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print("References to ashan_cn_boot_route:\n", stdout.read().decode('utf-8', errors='replace'))

# Check all js files in ashan_cn_procurement
cmd2 = "docker exec erpnext16 ls -la /home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/public/js/"
stdin2, stdout2, stderr2 = ssh.exec_command(cmd2)
stdout2.channel.recv_exit_status()
print("\nJS files in apps:\n", stdout2.read().decode('utf-8', errors='replace'))

cmd3 = "docker exec erpnext16 ls -la /home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/"
stdin3, stdout3, stderr3 = ssh.exec_command(cmd3)
stdout3.channel.recv_exit_status()
print("\nJS files in sites/assets:\n", stdout3.read().decode('utf-8', errors='replace'))

ssh.close()
