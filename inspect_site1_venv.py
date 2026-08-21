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

py_script = """
import os, sys
sys.path.insert(0, '/home/frappe/frappe-bench/apps/frappe')
sys.path.insert(0, '/home/frappe/frappe-bench/apps/erpnext')
sys.path.insert(0, '/home/frappe/frappe-bench/apps/ashan_cn_procurement')

import frappe
frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

print('Website Settings home_page:', frappe.db.get_single_value('Website Settings', 'home_page'))
print('Portal Settings default_portal_home:', frappe.db.get_single_value('Portal Settings', 'default_portal_home'))
print('get_home_page_via_hooks():', frappe.website.utils.get_home_page_via_hooks())
print('get_home_page():', frappe.website.utils.get_home_page())
print('hooks get_website_user_home_page:', frappe.get_hooks('get_website_user_home_page'))
print('hooks role_home_page:', frappe.get_hooks('role_home_page'))
print('hooks website_redirects:', frappe.get_hooks('website_redirects'))
"""

cmd = f"docker exec erpnext16 /home/frappe/frappe-bench/env/bin/python -c \"{py_script}\""
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print("STDOUT:\n", stdout.read().decode('utf-8', errors='replace'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='replace'))

ssh.close()
