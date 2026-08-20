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

host = os.getenv("UNRAID_SSH_HOST", "192.168.8.11")
port = int(os.getenv("UNRAID_SSH_PORT", "22"))
user = os.getenv("UNRAID_SSH_USER", "root")
password = os.getenv("UNRAID_SSH_PASSWORD", "")
container = os.getenv("CONTAINER_NAME", "erpnext16")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, password=password)

py_script = """
with open('/home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/router.js', 'r') as f:
    content = f.read()
    idx = content.find('render_page')
    if idx != -1:
        print('=== render_page ===')
        print(content[idx-100:idx+800])
    idx2 = content.find('render() {')
    if idx2 != -1:
        print('=== render() { ===')
        print(content[idx2:idx2+800])
"""

cmd = f"docker exec -w /home/frappe/frappe-bench/sites -u frappe erpnext16 /home/frappe/frappe-bench/env/bin/python -c \"{py_script}\""
stdin, stdout, stderr = client.exec_command(cmd)
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
client.close()
