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
from frappe.utils import flt

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

plate = "津AF9527"
if frappe.db.exists("Vehicle", plate):
    frappe.delete_doc("Vehicle", plate, ignore_permissions=True)
    frappe.db.commit()

companies = frappe.get_all("Company", fields=["name"], limit=1)
comp = companies[0].name if companies else None

doc = frappe.new_doc("Vehicle")
doc.license_plate = plate
doc.model = "货车"
doc.fuel_type = "Diesel"
doc.last_odometer = 18500
doc.company = comp
doc.insert(ignore_permissions=True)
frappe.db.commit()

print("SUCCESSFULLY CREATED VEHICLE:", doc.name, doc.license_plate, doc.fuel_type, doc.last_odometer)
"""

with sftp.open('/tmp/test_vehicle_create.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

ssh.exec_command("docker cp /tmp/test_vehicle_create.py erpnext16:/tmp/test_vehicle_create.py")[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command("docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/test_vehicle_create.py")
print("STDOUT:", stdout.read().decode('utf-8'))
print("STDERR:", stderr.read().decode('utf-8'))

sftp.close()
ssh.close()
