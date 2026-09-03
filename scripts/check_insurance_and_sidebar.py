import os
import paramiko
from dotenv import load_dotenv

load_dotenv()
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.8.11', port=22, username='root', password=os.getenv('UNRAID_SSH_PASSWORD', ''), timeout=10)

py_code = """import os, frappe
os.chdir('/home/frappe/frappe-bench/sites')
frappe.init(site='site1.local')
frappe.connect()

records = frappe.get_all(
    'Ashan Insurance Setting',
    fields=['name', 'company', 'effective_year', 'ss_company_injury', 'ss_person_pension', 'hf_person_rate']
)
print('Existing Insurance Settings:')
for r in records:
    print(r)

# Check if Jizhong exists
jz_setting = frappe.db.get_value(
    'Ashan Insurance Setting',
    {'company': '天津吉众科技有限公司', 'effective_year': 2026},
    '*',
    as_dict=True
)
print('Jizhong 2026 setting exists:', bool(jz_setting))
if jz_setting:
    print('Jizhong setting:', jz_setting.get('name'), 'injury rate:', jz_setting.get('ss_company_injury'))

frappe.destroy()
"""

sftp = c.open_sftp()
with sftp.file('/tmp/check_ins.py', 'w') as f:
    f.write(py_code)
sftp.close()

c.exec_command('docker cp /tmp/check_ins.py erpnext16:/home/frappe/frappe-bench/check_ins.py')
stdin, stdout, stderr = c.exec_command('docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 /home/frappe/frappe-bench/env/bin/python check_ins.py')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))
c.close()
