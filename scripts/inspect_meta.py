import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.getenv('UNRAID_SSH_HOST', '192.168.8.11'), port=int(os.getenv('UNRAID_SSH_PORT', '22')), username=os.getenv('UNRAID_SSH_USER', 'root'), password=os.getenv('UNRAID_SSH_PASSWORD', ''), timeout=15)

cmd = """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "ashan_cn_procurement.setup.get_doctypes_info" """

# 让我们直接通过 python-c 运行 bench execute
py_code = """
def get_info():
    import frappe, json
    dts = ['Material Request', 'Purchase Order', 'Purchase Receipt', 'Purchase Invoice', 'Reimbursement Request']
    res = {}
    for dt in dts:
        meta = frappe.get_meta(dt)
        tf = [{'fieldname': f.fieldname, 'options': f.options} for f in meta.fields if f.fieldtype == 'Table']
        cf = [f.fieldname for f in meta.fields if f.fieldname.startswith('custom_')]
        res[dt] = {'tables': tf, 'custom_fields': cf}
    print(json.dumps(res, ensure_ascii=False))
"""
stdin, stdout, stderr = client.exec_command("""docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.get_meta" --args "['Purchase Invoice']" """)
out = stdout.read().decode('utf-8')
print("PI Meta:", out[:200])
client.close()
