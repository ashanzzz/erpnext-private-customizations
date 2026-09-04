import os
import sys
import json
import base64
import paramiko
from dotenv import load_dotenv

load_dotenv()

json_path = r"d:\SynologyDrive团队\antigravity\erpnext16\scripts\jizhong_history_records.json"
with open(json_path, "r", encoding="utf-8") as f:
    history_data = json.load(f)

print(f"Loaded {len(history_data)} periods from {json_path}")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    os.getenv('UNRAID_SSH_HOST', '192.168.8.11'),
    port=int(os.getenv('UNRAID_SSH_PORT', '22')),
    username=os.getenv('UNRAID_SSH_USER', 'root'),
    password=os.getenv('UNRAID_SSH_PASSWORD', ''),
    timeout=30
)

# We send history_data in base64 chunks or as a temporary JSON file to the container
b64_json = base64.b64encode(json.dumps(history_data, ensure_ascii=False).encode('utf-8')).decode('ascii')

script = f"""
import sys
import json
import base64
import frappe
from frappe.utils import flt

frappe.init(site="site1.local")
frappe.connect()

raw_json = base64.b64decode('{b64_json}').decode('utf-8')
periods_data = json.loads(raw_json)

company = "天津吉众科技有限公司"

total_inserted_settlements = 0
total_inserted_items = 0

for period_month, items in periods_data.items():
    doc_name = f"{{company}}-{{period_month}}"
    
    # 检查或新建 Settlement
    if frappe.db.exists("Ashan Monthly Payroll Settlement", doc_name):
        doc = frappe.get_doc("Ashan Monthly Payroll Settlement", doc_name)
        doc.items = []
    else:
        doc = frappe.new_doc("Ashan Monthly Payroll Settlement")
        doc.name = doc_name
        doc.company = company
        doc.period_month = period_month

    doc.status = "已核定锁定"
    doc.locked = 1
    doc.workflow_stage = "归档"
    
    tot_gross = 0.0
    tot_net = 0.0
    tot_tax = 0.0
    tot_ss_pers = 0.0
    tot_hf_pers = 0.0

    for it in items:
        tot_gross += flt(it.get("gross_salary", 0))
        tot_net += flt(it.get("net_salary", 0))
        tot_tax += flt(it.get("tax_amount", 0))
        tot_ss_pers += flt(it.get("ss_person_total", 0))
        tot_hf_pers += flt(it.get("hf_person_total", 0))

        doc.append("items", {{
            "employee_no": it.get("employee_no"),
            "employee_name": it.get("employee_name"),
            "id_card": it.get("id_card"),
            "salary_mode": it.get("salary_mode"),
            "base_salary": flt(it.get("base_salary", 0)),
            "post_allowance": flt(it.get("post_allowance", 0)),
            "performance_salary": flt(it.get("performance_salary", 0)),
            "meal_unit_price": flt(it.get("meal_unit_price", 0)),
            "salary_adjustment": flt(it.get("salary_adjustment", 0)),
            "ss_base": flt(it.get("ss_base", 0)),
            "hf_base": flt(it.get("hf_base", 0)),
            "ss_person_total": flt(it.get("ss_person_total", 0)),
            "hf_person_total": flt(it.get("hf_person_total", 0)),
            "special_deductions_total": flt(it.get("special_deductions_total", 0)),
            "tax_threshold": flt(it.get("tax_threshold", 5000)),
            "tax_amount": flt(it.get("tax_amount", 0)),
            "net_salary": flt(it.get("net_salary", 0)),
            "gross_salary": flt(it.get("gross_salary", 0)),
            "cash_pay": flt(it.get("net_salary", 0)),
        }})
        total_inserted_items += 1

    doc.total_employees = len(doc.items)
    doc.total_gross_salary = round(tot_gross, 2)
    doc.total_net_salary = round(tot_net, 2)
    doc.total_tax = round(tot_tax, 2)
    doc.total_social_security_person = round(tot_ss_pers, 2)
    doc.total_housing_fund_person = round(tot_hf_pers, 2)

    doc.save(ignore_permissions=True)
    total_inserted_settlements += 1

frappe.db.commit()
print(f"SUCCESS: Inserted/Updated {{total_inserted_settlements}} settlements and {{total_inserted_items}} items.")
"""

b64_script = base64.b64encode(script.encode('utf-8')).decode('ascii')
cmd = f'''/home/frappe/frappe-bench/env/bin/python -c "import base64; exec(base64.b64decode('{b64_script}').decode('utf-8'))"'''
stdin, stdout, stderr = client.exec_command(f"docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 {cmd}")
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')

print("OUT:", out)
if err:
    print("ERR:", err)

client.close()
