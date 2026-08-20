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

# 删除数据库中所有关联 Property Charge Rate 的 Sidebar Item
cmd = """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.db.sql('DELETE FROM \\`tabWorkspace Sidebar Item\\` WHERE link_to = \\'Property Charge Rate\\' OR label = \\'收费标准版本\\''); frappe.db.commit(); frappe.clear_cache()" """
stdin, stdout, stderr = client.exec_command(cmd)
print("Cleaned database sidebar items:", stdout.read().decode('utf-8'))

# 清理 Redis 和 Desk 缓存
cmd2 = """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache"""
stdin, stdout, stderr = client.exec_command(cmd2)
print("Cleared cache:", stdout.read().decode('utf-8'))

client.close()
