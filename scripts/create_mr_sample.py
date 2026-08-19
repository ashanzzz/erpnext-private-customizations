import os, paramiko
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

comp = frappe.get_all("Company", limit=1)[0].name
items = frappe.get_all("Item", limit=5)

mr = frappe.new_doc("Material Request")
mr.material_request_type = "Purchase"
mr.company = comp
mr.schedule_date = "2026-08-30"
for it in items[:3]:
    mr.append("items", {
        "item_code": it.name,
        "qty": 20,
        "uom": "Nos",
        "schedule_date": "2026-08-30"
    })
mr.insert(ignore_permissions=True)
update_doc_details(mr)
mr.save(ignore_permissions=True)
frappe.db.commit()
print("MR committed:", mr.name, mr.custom_doc_details)
"""

sftp = client.open_sftp()
with sftp.file("/tmp/create_mr_sample.py", "w") as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/create_mr_sample.py erpnext16:/tmp/create_mr_sample.py && docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 ./env/bin/python /tmp/create_mr_sample.py")
client.close()
