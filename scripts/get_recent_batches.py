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

def run_cmd(cmd):
    print(f">> {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        print(out)
    if err:
        print("ERR:", err)
    return out, err

cmd = """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 /home/frappe/frappe-bench/env/bin/python -c "
import frappe
frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

batches = frappe.get_all('Tax Invoice Import Batch', fields=['name', 'source_filename', 'batch_status', 'current_message', 'error_log', 'creation', 'file_count', 'created_count', 'failed_count'], order_by='creation desc', limit=5)
for b in batches:
    print('----------------------------------------')
    print('Batch:', b.name)
    print('File:', b.source_filename)
    print('Status:', b.batch_status)
    print('Time:', str(b.creation))
    print('Msg:', b.current_message)
    print('Counts: file_count=', b.file_count, 'created=', b.created_count, 'failed=', b.failed_count)
    if b.error_log:
        print('Error Log:', b.error_log)

err_logs = frappe.get_all('Error Log', fields=['name', 'method', 'error', 'creation'], order_by='creation desc', limit=5)
print('================== RECENT ERROR LOGS ==================')
for el in err_logs:
    print('ErrorLog:', el.name, el.method, str(el.creation))
    print(el.error[:500])
    print('---')

frappe.destroy()
"
"""
run_cmd(cmd)

client.close()
