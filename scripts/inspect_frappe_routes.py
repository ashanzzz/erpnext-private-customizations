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

def inspect_frappe():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)

    cmd = """docker exec erpnext16 bash -c '
    cd /home/frappe/frappe-bench
    bench --site site1.local execute frappe.boot.get_bootinfo
    '"""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8')

    print("Core check:")
    cmd2 = """docker exec erpnext16 bash -c "python3 -c \\"
import frappe
frappe.init('site1.local')
frappe.connect()
print('--- Workspaces ---')
for w in frappe.get_all('Workspace', fields=['name', 'title', 'public', 'is_hidden']):
    print(w)
print('--- Pages ---')
for p in frappe.get_all('Page', fields=['name', 'title']):
    print(p)
\\"" """
    stdin2, stdout2, stderr2 = ssh.exec_command(cmd2)
    print(stdout2.read().decode('utf-8'))

    # Also check how router.js in frappe v16 handles home_page and workspaces
    cmd3 = """docker exec erpnext16 grep -n "home_page" /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/router.js /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/views/workspace/workspace.js"""
    stdin3, stdout3, stderr3 = ssh.exec_command(cmd3)
    print("Router home_page:")
    print(stdout3.read().decode('utf-8'))

    # Check convert_to_standard_route in router.js or workspace.js
    cmd4 = """docker exec erpnext16 grep -A 20 "convert_to_standard_route" /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/router.js"""
    stdin4, stdout4, stderr4 = ssh.exec_command(cmd4)
    print("convert_to_standard_route:")
    print(stdout4.read().decode('utf-8'))

    ssh.close()

if __name__ == '__main__':
    inspect_frappe()
