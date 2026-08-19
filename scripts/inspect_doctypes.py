import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.getenv('UNRAID_SSH_HOST', '192.168.8.11'), port=int(os.getenv('UNRAID_SSH_PORT', '22')), username=os.getenv('UNRAID_SSH_USER', 'root'), password=os.getenv('UNRAID_SSH_PASSWORD', ''), timeout=15)

script = """
import frappe, json
frappe.init(site="site1.local")
frappe.connect()

doctypes = ["Material Request", "Purchase Order", "Purchase Receipt", "Purchase Invoice", "Reimbursement Request"]
res = {}
for dt in doctypes:
    if frappe.db.exists("DocType", dt):
        meta = frappe.get_meta(dt)
        table_fields = [f.fieldname for f in meta.fields if f.fieldtype == "Table"]
        custom_fields = [f.fieldname for f in meta.fields if f.fieldname.startswith("custom_")]
        res[dt] = {
            "table_fields": table_fields,
            "custom_fields": custom_fields
        }

print(json.dumps(res, indent=2, ensure_ascii=False))
"""

sftp = client.open_sftp()
with sftp.file("/tmp/inspect_doctypes.py", "w") as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/inspect_doctypes.py erpnext16:/tmp/inspect_doctypes.py && docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 python3 /tmp/inspect_doctypes.py")
print("Inspection result:")
print(stdout.read().decode('utf-8'))
client.close()
