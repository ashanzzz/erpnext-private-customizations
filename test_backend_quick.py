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
from frappe.utils import flt, getdate

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

def test_quick():
    oil_card = 'CARD-001'
    posting_date = '2026-08-16'
    vehicle = '粤B·8888'
    odo = 46250
    lit = 50.0
    amt = 410.0
    norm_grade = '95'
    u_price = round(amt / lit, 2)
    remark = '测试快速保存'

    card = frappe.get_doc("Oil Card", oil_card)
    veh = frappe.get_doc("Vehicle", vehicle)

    dist = odo - flt(veh.last_odometer) if odo > flt(veh.last_odometer) else 0
    consum = round((lit / dist) * 100, 2) if dist > 0 and lit > 0 else 0

    doc = frappe.new_doc("Oil Card Refuel Log")
    doc.naming_series = "OCRL-.YYYY.-.#####"
    doc.oil_card = oil_card
    doc.company = card.company
    doc.supplier = card.supplier
    doc.posting_date = posting_date
    doc.vehicle = vehicle
    doc.odometer = odo
    doc.fuel_grade = norm_grade
    doc.liters = lit
    doc.unit_price = u_price
    doc.amount = amt
    doc.invoice_status = "未开票"
    doc.remark = remark or ""
    doc.insert(ignore_permissions=True)

    frappe.db.set_value("Oil Card Refuel Log", doc.name, {
        "distance_since_last": dist,
        "liter_per_100km": consum
    }, update_modified=False)
    frappe.db.commit()
    print("SUCCESS INSERT REFUEL:", doc.name)

test_quick()
"""

with sftp.open('/tmp/test_quick.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

ssh.exec_command("docker cp /tmp/test_quick.py erpnext16:/tmp/test_quick.py")[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command("docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/test_quick.py")
print("STDOUT:", stdout.read().decode('utf-8'))
print("STDERR:", stderr.read().decode('utf-8'))

sftp.close()
ssh.close()
