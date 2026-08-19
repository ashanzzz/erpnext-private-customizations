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

script_content = """
import frappe
frappe.init(site="site1.local")
frappe.connect()
frappe.db.sql("DELETE FROM `tabProperty Lease Charge Item`")
frappe.db.sql("DELETE FROM `tabProperty Monthly Summary`")
frappe.db.sql("UPDATE `tabProperty Monthly Settlement` SET status='草稿'")
frappe.db.commit()
print("Successfully refreshed settlements table")
"""

sftp = client.open_sftp()
with sftp.file("/tmp/refresh_settle.py", "w") as f:
    f.write(script_content)
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/refresh_settle.py erpnext16:/tmp/refresh_settle.py && docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 python3 /tmp/refresh_settle.py")
print("Result:", stdout.read().decode('utf-8'))
client.close()
