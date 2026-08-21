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

py_code = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

# 1. 为 Purchase Invoice Item-description 创建 Property Setter，将其类型改为 Data (单行文本)
frappe.make_property_setter({
    "doctype": "Purchase Invoice Item",
    "fieldname": "description",
    "property": "fieldtype",
    "value": "Data",
    "property_type": "Select"
}, validate_fields_for_doctype=False)

# 2. 为 Item-description 也设为 Data (单行文本)
frappe.make_property_setter({
    "doctype": "Item",
    "fieldname": "description",
    "property": "fieldtype",
    "value": "Data",
    "property_type": "Select"
}, validate_fields_for_doctype=False)

# 3. 设置中文标签为 说明
frappe.make_property_setter({
    "doctype": "Purchase Invoice Item",
    "fieldname": "description",
    "property": "label",
    "value": "说明",
    "property_type": "Data"
}, validate_fields_for_doctype=False)

frappe.db.commit()
frappe.clear_cache(doctype="Purchase Invoice")
frappe.clear_cache(doctype="Purchase Invoice Item")
frappe.clear_cache(doctype="Item")
print("[OK] Description converted to Data (单行文本) successfully via Property Setter!")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/convert_desc_to_data.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/convert_desc_to_data.py erpnext16:/tmp/convert_desc_to_data.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/convert_desc_to_data.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
