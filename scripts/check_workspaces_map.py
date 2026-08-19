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
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

def check_workspaces_map():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)

    cmd = """docker exec erpnext16 grep -rn "frappe.workspaces" /home/frappe/frappe-bench/apps/frappe/frappe/public/js/"""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8'))

    cmd2 = """docker exec erpnext16 grep -rn "show_not_found" /home/frappe/frappe-bench/apps/frappe/frappe/public/js/"""
    stdin2, stdout2, stderr2 = ssh.exec_command(cmd2)
    print(stdout2.read().decode('utf-8'))

    # Check setup_workspaces in workspace.js
    cmd3 = """docker exec erpnext16 grep -A 30 "setup_workspaces" /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/views/workspace/workspace.js"""
    stdin3, stdout3, stderr3 = ssh.exec_command(cmd3)
    print("setup_workspaces:")
    print(stdout3.read().decode('utf-8'))

    ssh.close()

if __name__ == '__main__':
    check_workspaces_map()
