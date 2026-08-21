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

test_py = """
import frappe
frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

frappe.clear_cache()

hooks = frappe.get_hooks("doc_events")
print("Purchase Invoice doc_events hooks AFTER clear_cache:", hooks.get("Purchase Invoice"))
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/test_hook_reload.py', 'wb') as f:
    f.write(test_py.encode('utf-8'))

cmd1 = "docker cp /tmp/test_hook_reload.py erpnext16:/tmp/test_hook_reload.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/test_hook_reload.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("STDOUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
