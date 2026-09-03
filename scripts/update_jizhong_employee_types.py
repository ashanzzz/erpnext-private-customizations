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

EMP_TYPE_MAP = {
    'QG0001': '其他-返聘工',
    'QF0001': '其他-返聘工',
    'QF0002': '其他-返聘工',
    'QG0003': '其他-返聘工',
    'QG0004': '其他-返聘工',
    'QG0002': '其他-正式工',
}

# 1. Update Ashan Employee Salary Profile
for emp_no, emp_type in EMP_TYPE_MAP.items():
    prof_name = frappe.db.get_value(
        'Ashan Employee Salary Profile',
        {'company': '天津吉众科技有限公司', 'employee_no': emp_no}
    )
    if prof_name:
        frappe.db.set_value('Ashan Employee Salary Profile', prof_name, 'employee_type', emp_type)
        print(f"Updated Profile {emp_no} -> {emp_type}")
    else:
        # Check if profile exists under just employee_no
        profs = frappe.get_all('Ashan Employee Salary Profile', filters={'employee_no': emp_no})
        for p in profs:
            frappe.db.set_value('Ashan Employee Salary Profile', p.name, 'employee_type', emp_type)
            print(f"Updated Profile {emp_no} ({p.name}) -> {emp_type}")

# 2. Update Ashan Monthly Payroll Item across all periods for Jizhong
for emp_no, emp_type in EMP_TYPE_MAP.items():
    frappe.db.sql('''
        UPDATE `tabAshan Monthly Payroll Item` pi
        JOIN `tabAshan Monthly Payroll Settlement` ps ON pi.parent = ps.name
        SET pi.employee_type = %s
        WHERE ps.company = '天津吉众科技有限公司' AND pi.employee_no = %s
    ''', (emp_type, emp_no))
    print(f"Updated child items for {emp_no} -> {emp_type}")

# Set default '正式工' for other employees whose employee_type is null or empty
frappe.db.sql('''
    UPDATE `tabAshan Monthly Payroll Item` pi
    JOIN `tabAshan Monthly Payroll Settlement` ps ON pi.parent = ps.name
    SET pi.employee_type = '正式工'
    WHERE ps.company = '天津吉众科技有限公司' AND (pi.employee_type IS NULL OR pi.employee_type = '' OR pi.employee_type = 'None')
''')

frappe.db.commit()
print("All employee types updated and committed successfully!")

# Verify
items = frappe.db.sql('''
    SELECT pi.employee_no, pi.employee_name, pi.employee_type, COUNT(*) as cnt
    FROM `tabAshan Monthly Payroll Item` pi
    JOIN `tabAshan Monthly Payroll Settlement` ps ON pi.parent = ps.name
    WHERE ps.company = '天津吉众科技有限公司'
    GROUP BY pi.employee_no, pi.employee_name, pi.employee_type
    ORDER BY pi.employee_no ASC
''', as_dict=True)

for it in items:
    print(f"{it.employee_no}\t{it.employee_name}\t{it.employee_type}\t(records: {it.cnt})")

frappe.destroy()
"""

sftp = c.open_sftp()
with sftp.file('/tmp/update_emp_types.py', 'w') as f:
    f.write(remote_script)
sftp.close()

c.exec_command('docker cp /tmp/update_emp_types.py erpnext16:/home/frappe/frappe-bench/update_emp_types.py')
stdin, stdout, stderr = c.exec_command('docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 /home/frappe/frappe-bench/env/bin/python update_emp_types.py')
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("STDOUT:\n", out)
print("STDERR:\n", err)
c.close()
