import os
import paramiko
from dotenv import load_dotenv

load_dotenv()
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.8.11', port=22, username='root', password=os.getenv('UNRAID_SSH_PASSWORD', ''), timeout=10)

remote_script = """import os, frappe
os.chdir('/home/frappe/frappe-bench/sites')
frappe.init(site='site1.local')
frappe.connect()

emps = frappe.get_all(
    'Ashan Employee Salary Profile',
    filters={'company': '天津吉众科技有限公司'},
    fields=['name', 'employee_no', 'employee_name', 'employee_type', 'employment_status'],
    order_by='employee_no asc'
)
for e in emps:
    print(f"{e.employee_no}\t{e.employee_name}\t{e.employee_type}\t{e.employment_status}")

# Also check monthly payroll items for 2026-06
items = frappe.get_all(
    'Ashan Monthly Payroll Item',
    filters={'parent': '天津吉众科技有限公司-2026-06'},
    fields=['employee_no', 'employee_name', 'employee_type']
)
print('--- 2026-06 items ---')
for it in items:
    if it.employee_no in ['QG0001', 'QF0001', 'QF0002', 'QG0002', 'QG0003', 'QG0004']:
        print(f"{it.employee_no}\t{it.employee_name}\t{it.employee_type}")

frappe.destroy()
"""

sftp = c.open_sftp()
with sftp.file('/tmp/inspect_emps.py', 'w') as f:
    f.write(remote_script)
sftp.close()

res = c.exec_command('docker cp /tmp/inspect_emps.py erpnext16:/home/frappe/frappe-bench/inspect_emps.py')[1].channel.recv_exit_status()
stdin, stdout, stderr = c.exec_command('docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 /home/frappe/frappe-bench/env/bin/python inspect_emps.py')
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("STDOUT:\n", out)
print("STDERR:\n", err)
c.close()
