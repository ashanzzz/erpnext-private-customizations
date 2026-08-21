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
from frappe.utils import nowdate, add_days

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

companies = frappe.get_all("Company")
company = companies[0].name if companies else "My Company"

suppliers = frappe.get_all("Supplier")
supplier = suppliers[0].name if suppliers else "其它供应商"

mops = frappe.get_all("Mode of Payment")
mop = mops[0].name if mops else None

vehicle_name = "粤B·8888"

# 4. 充值流水 1 (月初)
if frappe.db.count("Oil Card Recharge") == 0:
    r1 = frappe.get_doc({
        "doctype": "Oil Card Recharge",
        "naming_series": "OCR-.YYYY.-.#####",
        "company": company,
        "supplier": supplier,
        "oil_card": "CARD-001",
        "transaction_type": "主卡充值",
        "posting_date": "2026-08-01",
        "recharge_amount": 2000.00,
        "bonus_amount": 100.00,
        "effective_amount": 2100.00,
        "mode_of_payment": mop,
        "reference_no": "RC-20260801-01",
        "status": "Submitted",
        "remark": "公司财务公户8月月初批量充值"
    })
    r1.insert(ignore_permissions=True)

    r2 = frappe.get_doc({
        "doctype": "Oil Card Recharge",
        "naming_series": "OCR-.YYYY.-.#####",
        "company": company,
        "supplier": supplier,
        "oil_card": "CARD-001",
        "transaction_type": "主卡充值",
        "posting_date": "2026-08-10",
        "recharge_amount": 1000.00,
        "bonus_amount": 50.00,
        "effective_amount": 1050.00,
        "mode_of_payment": mop,
        "reference_no": "RC-20260810-02",
        "status": "Submitted",
        "remark": "业务拓展临时加充"
    })
    r2.insert(ignore_permissions=True)
    print("Created Recharges for CARD-001")

# 5. 加油记录 (月中多笔)
if frappe.db.count("Oil Card Refuel Log") == 0:
    f1 = frappe.get_doc({
        "doctype": "Oil Card Refuel Log",
        "naming_series": "OCRL-.YYYY.-.#####",
        "company": company,
        "supplier": supplier,
        "oil_card": "CARD-001",
        "vehicle": vehicle_name,
        "fuel_grade": "95",
        "posting_date": "2026-08-05",
        "odometer": 45200,
        "previous_odometer": 44700,
        "distance_since_last": 500,
        "liters": 48.50,
        "unit_price": 8.25,
        "amount": 400.13,
        "km_per_liter": 10.31,
        "liter_per_100km": 9.70,
        "invoice_status": "未开票",
        "remark": "业务送客户往返"
    })
    f1.insert(ignore_permissions=True)

    f2 = frappe.get_doc({
        "doctype": "Oil Card Refuel Log",
        "naming_series": "OCRL-.YYYY.-.#####",
        "company": company,
        "supplier": supplier,
        "oil_card": "CARD-001",
        "vehicle": vehicle_name,
        "fuel_grade": "95",
        "posting_date": "2026-08-12",
        "odometer": 45720,
        "previous_odometer": 45200,
        "distance_since_last": 520,
        "liters": 49.00,
        "unit_price": 8.25,
        "amount": 404.25,
        "km_per_liter": 10.61,
        "liter_per_100km": 9.42,
        "invoice_status": "未开票",
        "remark": "项目现场巡检往返"
    })
    f2.insert(ignore_permissions=True)

    cur_bal = 1500.00 + 2100.00 + 1050.00 - 400.13 - 404.25
    frappe.db.set_value("Oil Card", "CARD-001", "current_balance", cur_bal)
    frappe.db.set_value("Oil Card", "CARD-001", "uninvoiced_amount", 400.13 + 404.25)
    print("Created Refuel Logs for CARD-001")

frappe.db.commit()
frappe.clear_cache()
print("[OK] All sample data successfully committed!")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/insert_sample_oil_perfect.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/insert_sample_oil_perfect.py erpnext16:/tmp/insert_sample_oil_perfect.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/insert_sample_oil_perfect.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
