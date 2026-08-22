import os
import shlex

import paramiko


def load_env_file(env_path=".env"):
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


load_env_file()
HOST = os.getenv("UNRAID_SSH_HOST", "192.168.8.11")
PORT = int(os.getenv("UNRAID_SSH_PORT", "22"))
USER = os.getenv("UNRAID_SSH_USER", "root")
PASSWORD = os.getenv("UNRAID_SSH_PASSWORD", "")
MYSQL_USER = os.getenv("MYSQL_USER", "erpnext16")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "erpnext16")
MYSQL_CONTAINER = os.getenv("MYSQL_CONTAINER", "1Panel-mariadb")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)

mysql_password_arg = f"-p{MYSQL_PASSWORD}" if MYSQL_PASSWORD else ""
sql = "SELECT name, title, app FROM `tabWorkspace Sidebar`"
cmd = (
    f"docker exec -i {shlex.quote(MYSQL_CONTAINER)} mysql "
    f"-u{shlex.quote(MYSQL_USER)} {shlex.quote(mysql_password_arg)} "
    f"{shlex.quote(MYSQL_DATABASE)} -e {shlex.quote(sql)}"
)
stdin, stdout, stderr = ssh.exec_command(cmd)
print("ALL WORKSPACE SIDEBARS IN MARIADB:\n", stdout.read().decode("utf-8"))
err = stderr.read().decode("utf-8").strip()
if err:
    print("STDERR:\n", err)
ssh.close()
