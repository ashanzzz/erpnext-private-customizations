import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.getenv('UNRAID_SSH_HOST', '192.168.8.11'), port=int(os.getenv('UNRAID_SSH_PORT', '22')), username=os.getenv('UNRAID_SSH_USER', 'root'), password=os.getenv('UNRAID_SSH_PASSWORD', ''), timeout=15)

script = """
import frappe
frappe.init(site="site1.local")
frappe.connect()

# 1. 确保 Material Request 有测试数据
if not frappe.db.exists("Material Request", {"docstatus": ["<", 2]}):
    try:
        mr = frappe.new_doc("Material Request")
        mr.material_request_type = "Purchase"
        mr.schedule_date = "2026-08-30"
        mr.append("items", {
            "item_code": "紧固件-01",
            "item_name": "高强度外六角螺栓 M12*50",
            "qty": 50,
            "uom": "套",
            "schedule_date": "2026-08-30"
        })
        mr.append("items", {
            "item_code": "密封件-02",
            "item_name": "耐高温氟胶O型圈",
            "qty": 100,
            "uom": "个",
            "schedule_date": "2026-08-30"
        })
        mr.insert(ignore_permissions=True)
        print("Created sample Material Request:", mr.name)
    except Exception as e:
        print("MR sample err:", e)

# 2. 确保 Reimbursement Request 有测试数据
if not frappe.db.exists("Reimbursement Request", {"docstatus": ["<", 2]}):
    try:
        user = frappe.db.get_value("User", {"email": "dev@example.invalid"}, "name") or "Administrator"
        rr = frappe.new_doc("Reimbursement Request")
        rr.applicant = user
        rr.custom_biz_mode = "报销申请"
        rr.posting_date = "2026-08-18"
        rr.reimbursement_reason = "8月份车间应急采购及差旅报销"
        rr.append("invoices", {
            "invoice_type": "增值税专用发票",
            "invoice_number": "26122000008888",
            "tax_inclusive_amount": 350.00,
            "tax_exclusive_amount": 309.73,
            "custom_line_remark": "工业润滑油脂 (1桶)"
        })
        rr.append("invoices", {
            "invoice_type": "电子发票(普通发票)",
            "invoice_number": "26122000009999",
            "tax_inclusive_amount": 88.50,
            "tax_exclusive_amount": 85.92,
            "custom_line_remark": "跨区配送快递运费 (3单)"
        })
        rr.insert(ignore_permissions=True)
        print("Created sample Reimbursement Request:", rr.name)
    except Exception as e:
        print("RR sample err:", e)

frappe.db.commit()
"""

sftp = client.open_sftp()
with sftp.file("/tmp/create_sample_docs.py", "w") as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/create_sample_docs.py erpnext16:/tmp/create_sample_docs.py && docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 python3 /tmp/create_sample_docs.py")
print("Exec out:", stdout.read().decode('utf-8'))
client.close()
