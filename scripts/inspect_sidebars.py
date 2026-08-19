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
frappe.init(site="site1.local")
frappe.connect()

print("--- Workspace Sidebars in DB ---")
sidebars = frappe.get_all("Workspace Sidebar", fields=["name", "title", "header_icon"])
for s in sidebars:
    print(f"Sidebar: {s.name} ({s.title})")
    items = frappe.get_all("Workspace Sidebar Item", filters={"parent": s.name}, fields=["title", "link_type", "link_to", "type", "idx"], order_by="idx asc")
    for item in items:
        print(f"   [{item.type}] {item.title} -> {item.link_to} ({item.link_type})")

print("\n--- Workspaces in DB ---")
workspaces = frappe.get_all("Workspace", fields=["name", "title", "public", "is_hidden"])
for w in workspaces:
    print(f"Workspace: {w.name} (title: {w.title}, public: {w.public}, hidden: {w.is_hidden})")
"""

sftp = client.open_sftp()
with sftp.file("/tmp/inspect_sidebars.py", "w") as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/inspect_sidebars.py erpnext16:/tmp/inspect_sidebars.py && docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 python3 /tmp/inspect_sidebars.py")
print(stdout.read().decode('utf-8'))
client.close()
