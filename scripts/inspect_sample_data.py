import os
import json
import paramiko
from dotenv import load_dotenv

load_dotenv()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.getenv('UNRAID_SSH_HOST', '192.168.8.11'), port=int(os.getenv('UNRAID_SSH_PORT', '22')), username=os.getenv('UNRAID_SSH_USER', 'root'), password=os.getenv('UNRAID_SSH_PASSWORD', ''), timeout=15)

script = """
import frappe, json
dts = ['Material Request', 'Purchase Order', 'Purchase Receipt', 'Purchase Invoice', 'Reimbursement Request']
for dt in dts:
    if frappe.db.exists('DocType', dt):
        meta = frappe.get_meta(dt)
        print('=== ' + dt + ' ===')
        tables = [f.fieldname + ' (' + str(f.options) + ')' for f in meta.fields if f.fieldtype == 'Table']
        print('Tables:', ', '.join(tables))
        # 查看最新的一条数据子表行
        docs = frappe.get_all(dt, limit=1)
        if docs:
            d = frappe.get_doc(dt, docs[0].name)
            for t_field in [f.fieldname for f in meta.fields if f.fieldtype == 'Table']:
                rows = d.get(t_field) or []
                if rows:
                    sample = [f"{r.get('item_name') or r.get('item_code') or r.get('invoice_title') or r.get('description') or r.name} (qty: {r.get('qty')}, amt: {r.get('amount') or r.get('tax_inclusive_amount')})" for r in rows[:3]]
                    print(f"  Row sample [{t_field}]:", ' | '.join(sample))
"""

cmd = f"""docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 python3 -c "{script}" """
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))
client.close()
