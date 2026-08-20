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

# 重新生成 2026-07 和 2026-08 的月结草稿
cmd = """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.db.sql('DELETE FROM \\`tabProperty Lease Charge Item\\`'); frappe.db.sql('DELETE FROM \\`tabProperty Monthly Summary\\`'); frappe.db.sql('UPDATE \\`tabProperty Monthly Settlement\\` SET status=\\'草稿\\''); frappe.db.commit();" """
stdin, stdout, stderr = client.exec_command(cmd)
print("Reset settlement cache:", stdout.read().decode('utf-8'))

client.close()
