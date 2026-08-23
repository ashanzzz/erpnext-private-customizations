import os
import sys
import paramiko
from dotenv import load_dotenv

load_dotenv()

LAN_HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
TAILSCALE_HOST = os.getenv('UNRAID_TAILSCALE_HOST', '100.80.0.4')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

def run_test(test_cmd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(LAN_HOST, port=PORT, username=USER, password=PASSWORD, timeout=5)
    except Exception:
        client.connect(TAILSCALE_HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)

    full_cmd = f"docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 {test_cmd}"
    print(f">> {full_cmd}")
    stdin, stdout, stderr = client.exec_command(full_cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        print(out)
    if err:
        print(err)
    client.close()

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "bench --site site1.local execute ashan_cn_procurement.services.test_procurement_picker.run_tests"
    run_test(cmd)
