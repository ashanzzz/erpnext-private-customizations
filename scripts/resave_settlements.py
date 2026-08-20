import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

script = """
import frappe
from ashan_cn_procurement.services.property_settlement import get_month_settlement_data, save_draft_settlement

frappe.init(site="site1.local")
frappe.connect()

# 重新生成 2026-07 和 2026-08 的草稿并保存
for m in [7, 8]:
    data = get_month_settlement_data(2026, m)
    save_draft_settlement(data)
    print(f"Refreshed and saved 2026-{m} settlement")
"""

sftp = client.open_sftp()
with sftp.file("/tmp/resave_settle.py", "w") as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/resave_settle.py erpnext16:/tmp/resave_settle.py && docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 python3 /tmp/resave_settle.py")
print("Exec output:", stdout.read().decode('utf-8'))
client.close()
