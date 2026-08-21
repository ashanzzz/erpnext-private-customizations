# -*- coding: utf-8 -*-
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

sftp = ssh.open_sftp()
py_code = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

meta = frappe.get_meta("Vehicle")
fields = [{"fieldname": f.fieldname, "label": f.label, "fieldtype": f.fieldtype, "reqd": f.reqd, "options": f.options} for f in meta.fields]
print("VEHICLE FIELDS:")
for f in fields:
    if f["fieldname"]:
        print(" ", f)
"""

with sftp.open('/tmp/check_vehicle_meta.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

ssh.exec_command("docker cp /tmp/check_vehicle_meta.py erpnext16:/tmp/check_vehicle_meta.py")[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command("docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/check_vehicle_meta.py")
print("STDOUT:", stdout.read().decode('utf-8'))

sftp.close()
ssh.close()
