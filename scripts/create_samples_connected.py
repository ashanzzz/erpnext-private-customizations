import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.getenv('UNRAID_SSH_HOST', '192.168.8.11'), port=int(os.getenv('UNRAID_SSH_PORT', '22')), username=os.getenv('UNRAID_SSH_USER', 'root'), password=os.getenv('UNRAID_SSH_PASSWORD', ''), timeout=15)

script = """
import frappe, os
from ashan_cn_procurement.overrides.document_details import update_doc_details

os.chdir("/home/frappe/frappe-bench/sites")
frappe.init(site="site1.local")
frappe.connect()



# 1. 确保 Material Request
comp = frappe.get_all("Company", limit=1)[0].name
items = frappe.get_all("Item", limit=2)
item_name = items[0].name if items else "紧固件-01"

mr = frappe.new_doc("Material Request")
mr.material_request_type = "Purchase"
mr.company = comp
mr.schedule_date = "2026-08-30"
mr.append("items", {
    "item_code": item_name,
    "qty": 50,
    "uom": "Nos",
    "schedule_date": "2026-08-30"
})
mr.insert(ignore_permissions=True)
update_doc_details(mr)
mr.save(ignore_permissions=True)
print("MR created:", mr.name, "-> details:", mr.custom_doc_details)

# 2. 确保 Reimbursement Request
user = frappe.db.get_value("User", {"email": "dev@example.invalid"}, "name") or "Administrator"
rr = frappe.new_doc("Reimbursement Request")
rr.applicant = user
rr.company = comp
rr.custom_biz_mode = "报销申请"
rr.posting_date = "2026-08-18"
rr.reimbursement_reason = "8月份车间应急耗材及差旅费用"
rr.total_tax_inclusive_amount = 438.50
rr.append("invoice_items", {
    "invoice_type": "增值税专用发票",
    "invoice_number": "26122000008888",
    "tax_inclusive_amount": 350.00,
    "tax_exclusive_amount": 309.73,
    "custom_line_remark": "工业润滑油脂 (1桶)"
})
rr.append("invoice_items", {
    "invoice_type": "电子发票(普通发票)",
    "invoice_number": "26122000009999",
    "tax_inclusive_amount": 88.50,
    "tax_exclusive_amount": 85.92,
    "custom_line_remark": "跨区配送快递运费 (3单)"
})

rr.insert(ignore_permissions=True)
update_doc_details(rr)
rr.save(ignore_permissions=True)
print("RR created:", rr.name, "-> details:", rr.custom_doc_details)

frappe.db.commit()
"""

sftp = client.open_sftp()
with sftp.file("/tmp/create_samples_connected.py", "w") as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/create_samples_connected.py erpnext16:/tmp/create_samples_connected.py && docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 ./env/bin/python /tmp/create_samples_connected.py")
print("Exec output:")
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))
client.close()
