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

py_code = """
import frappe
frappe.init('site1.local')
frappe.connect()

print('desktop:home_page default:', frappe.db.get_default('desktop:home_page'))
print('all defaults with home_page:', frappe.db.get_values('Singles', {'field': 'home_page'}, ['doctype', 'value'], as_dict=True))
print('all tabDefaultValue with home:', frappe.db.sql('select * from `tabDefaultValue` where defkey like %s', '%home%', as_dict=True))
print('User default for Administrator:', frappe.db.get_defaults(user='Administrator'))
"""

cmd = f"docker exec -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python -c \"{py_code}\""
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print("STDOUT:\n", stdout.read().decode('utf-8', errors='replace'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='replace'))

ssh.close()
