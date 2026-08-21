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

test_py = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

supplier = frappe.db.get_value("Supplier", {}, "name") or "默认供应商"
item_code = frappe.db.get_value("Item", {"is_purchase_item": 1}, "name")
company = frappe.db.get_value("Company", {}, "name")

print("Using Supplier:", supplier, "Company:", company, "Item:", item_code)

# 1. 测试 Case 1: 无发票 -> bill_no 自动清空
doc1 = frappe.get_doc({
    "doctype": "Purchase Invoice",
    "company": company,
    "supplier": supplier,
    "custom_invoice_type": "无发票",
    "bill_no": "TEST-NO-INV-001",
    "items": [{
        "item_code": item_code,
        "qty": 1,
        "rate": 100,
        "custom_tax_rate": 0
    }]
})
doc1.save(ignore_permissions=True)
print("[PASS] Case 1 (无发票自动清空发票号): doc1.bill_no =", repr(doc1.bill_no))

# 2. 测试 Case 2: 专用发票未填发票号 -> 报错拦截
try:
    doc2 = frappe.get_doc({
        "doctype": "Purchase Invoice",
        "company": company,
        "supplier": supplier,
        "custom_invoice_type": "专用发票",
        "bill_no": "",
        "items": [{
            "item_code": item_code,
            "qty": 1,
            "rate": 100,
            "custom_tax_rate": 13
        }]
    })
    doc2.save(ignore_permissions=True)
    print("[FAIL] Case 2 应该抛出异常但没有！")
except Exception as e:
    print("[PASS] Case 2 (专用发票未填发票号被成功拦截):", str(e))

# 3. 创建一张有效发票用于查重
test_bill_no = "FP-UNIQUE-TEST-888"
frappe.db.sql("DELETE FROM `tabPurchase Invoice` WHERE bill_no = %s", (test_bill_no,))
doc3 = frappe.get_doc({
    "doctype": "Purchase Invoice",
    "company": company,
    "supplier": supplier,
    "custom_invoice_type": "专用发票",
    "bill_no": test_bill_no,
    "bill_date": "2026-08-14",
    "items": [{
        "item_code": item_code,
        "qty": 1,
        "rate": 100,
        "custom_tax_rate": 13
    }]
})
doc3.save(ignore_permissions=True)
print(f"[PASS] Case 3 (首次录入发票号 {test_bill_no} 成功): doc name = {doc3.name}")

# 4. 测试 Case 4: 重复录入相同发票号 -> 报错拦截
try:
    doc4 = frappe.get_doc({
        "doctype": "Purchase Invoice",
        "company": company,
        "supplier": supplier,
        "custom_invoice_type": "普通发票",
        "bill_no": test_bill_no,
        "bill_date": "2026-08-14",
        "items": [{
            "item_code": item_code,
            "qty": 1,
            "rate": 100,
            "custom_tax_rate": 13
        }]
    })
    doc4.save(ignore_permissions=True)
    print("[FAIL] Case 4 重复发票号应该抛出异常但没有！")
except Exception as e:
    print(f"[PASS] Case 4 (重复发票号 {test_bill_no} 被精准拦截):", str(e))

# 5. 测试前端查重 API
from ashan_cn_procurement.ashan_cn_procurement.overrides.purchase_invoice_tax import check_bill_no_duplicate
res_dup = check_bill_no_duplicate(test_bill_no, docname=None)
print("[PASS] Case 5 (前端查重 API 响应):", res_dup)

res_non_dup = check_bill_no_duplicate("RANDOM-NOT-EXIST-999", docname=None)
print("[PASS] Case 6 (非重复发票号 API 响应):", res_non_dup)
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/test_invoice_rules.py', 'wb') as f:
    f.write(test_py.encode('utf-8'))

cmd1 = "docker cp /tmp/test_invoice_rules.py erpnext16:/tmp/test_invoice_rules.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/test_invoice_rules.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
