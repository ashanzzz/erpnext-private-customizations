import os
import paramiko
from dotenv import load_dotenv

load_dotenv()
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.getenv('UNRAID_SSH_HOST', '192.168.8.11'), port=int(os.getenv('UNRAID_SSH_PORT', '22')), username=os.getenv('UNRAID_SSH_USER', 'root'), password=os.getenv('UNRAID_SSH_PASSWORD', ''), timeout=15)
stdin, stdout, stderr = client.exec_command("docker exec -u frappe erpnext16 ls -la /home/frappe/frappe-bench/sites")
print(stdout.read().decode('utf-8'))
client.close()
