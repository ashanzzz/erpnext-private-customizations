import os
import sys
import paramiko
from dotenv import load_dotenv

load_dotenv()
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    os.getenv('UNRAID_SSH_HOST', '192.168.8.11'),
    port=int(os.getenv('UNRAID_SSH_PORT', '22')),
    username=os.getenv('UNRAID_SSH_USER', 'root'),
    password=os.getenv('UNRAID_SSH_PASSWORD', ''),
    timeout=15
)

import base64

script = """
import sys
import json
import frappe
frappe.init(site="site1.local")
frappe.connect()

data = {
    "companies": frappe.get_all("Company", fields=["name", "company_name"]),
    "jz_employees": frappe.get_all("Employee", filters={"company": ["like", "%吉众%"]}, fields=["name", "employee_name", "company", "status"]),
    "jz_salary_profiles": frappe.get_all("Ashan Employee Salary Profile", filters={"company": ["like", "%吉众%"]}, fields=["name", "employee_no", "employee_name", "company", "employee_type", "employment_status", "salary_mode", "base_salary", "post_allowance", "performance_base"]),
    "jz_attendance": frappe.get_all("Ashan Monthly Attendance", filters={"company": ["like", "%吉众%"]}, fields=["name", "period_month", "company", "employee_no", "employee_name", "attendance_days", "work_hours_regular"]),
    "insurance_settings": frappe.get_all("Ashan Insurance Setting", fields=["*"]),
    "settlement_2026_06": frappe.get_all("Ashan Monthly Payroll Settlement", filters={"company": ["like", "%吉众%"]}, fields=["*"]),
    "payroll_items_2026_06": frappe.get_all("Ashan Monthly Payroll Item", filters={"parent": ["like", "%吉众%"]}, fields=["*"], limit=5)
}

print("JSON_START")
print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
print("JSON_END")
"""

b64_script = base64.b64encode(script.encode('utf-8')).decode('ascii')
cmd = f'''/home/frappe/frappe-bench/env/bin/python -c "import base64; exec(base64.b64decode('{b64_script}').decode('utf-8'))"'''
stdin, stdout, stderr = client.exec_command(f"docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 {cmd}")
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
with open(r'd:\SynologyDrive团队\antigravity\erpnext16\scripts\jizhong_db_dump.json', 'w', encoding='utf-8') as f:
    f.write(out)
print("Dumped to jizhong_db_dump.json")
if err:
    print("ERR:", err)
client.close()
