import os, paramiko
from dotenv import load_dotenv

load_dotenv()
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.8.11', port=22, username='root', password=os.getenv('UNRAID_SSH_PASSWORD', ''), timeout=10)

cmd = """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute ashan_cn_procurement.services.jizhong_payroll_service.calculate_jizhong_monthly_payroll --args "['天津吉众科技有限公司', '2026-07']" """
stdin, stdout, stderr = c.exec_command(cmd)
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')
print("CALC 2026-07 OUT:", out)
if err:
    print("ERR:", err)
c.close()
