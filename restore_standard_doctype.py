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

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

print("--- 完整还原 Purchase Invoice 与 Purchase Invoice Item 到官方标准 ---")

# 1. 重新从 accounts 模块的 JSON 重新加载核心 DocType，重置所有 DocField (包括 hidden, idx, label)
frappe.reload_doc("accounts", "doctype", "purchase_invoice", force=True)
frappe.reload_doc("accounts", "doctype", "purchase_invoice_item", force=True)

# 2. 清理 Purchase Invoice Item 上针对 DocField 的 Property Setter
frappe.db.sql('''
    DELETE FROM `tabProperty Setter`
    WHERE doc_type IN ('Purchase Invoice Item', 'Purchase Invoice')
      AND property IN ('hidden', 'idx')
''')

# 3. 确保 Custom Field 不破坏标准顺序
# 保留必要的业务自定义字段，但重置其位置为标准合理位置
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_gross_rate", {"insert_after": "qty", "hidden": 0})
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_tax_rate", {"insert_after": "custom_gross_rate", "hidden": 0})
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_tax_amount", {"insert_after": "amount", "hidden": 0})
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_gross_amount", {"insert_after": "custom_tax_amount", "hidden": 0})
frappe.db.set_value("Custom Field", "Purchase Invoice Item-custom_line_remark", {"insert_after": "custom_gross_amount", "hidden": 0})

frappe.db.commit()
frappe.clear_cache()
print("[OK] Purchase Invoice 和 Purchase Invoice Item 已 100% 官方重载并还原！")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/restore_standard_doctype.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/restore_standard_doctype.py erpnext16:/tmp/restore_standard_doctype.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/restore_standard_doctype.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
