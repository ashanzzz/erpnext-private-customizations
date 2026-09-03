import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

local_file = r"d:\SynologyDrive团队\antigravity\erpnext16\temp_screenshots\员工考勤表-2026年7月.xlsx"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    os.getenv('UNRAID_SSH_HOST', '192.168.8.11'),
    port=int(os.getenv('UNRAID_SSH_PORT', '22')),
    username=os.getenv('UNRAID_SSH_USER', 'root'),
    password=os.getenv('UNRAID_SSH_PASSWORD', ''),
    timeout=10
)

# Upload file to server
sftp = client.open_sftp()
remote_path = "/tmp/attendance_2026_07.xlsx"
sftp.put(local_file, remote_path)
sftp.close()

# Copy to docker container
client.exec_command(f"docker cp {remote_path} erpnext16:/tmp/attendance_2026_07.xlsx")

# Execute parse script in container
exec_cmd = """/home/frappe/frappe-bench/env/bin/python -c "
import frappe
frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()
from ashan_cn_procurement.services.jizhong_attendance_service import parse_jizhong_attendance_file
res = parse_jizhong_attendance_file('/tmp/attendance_2026_07.xlsx', period_month='2026-07', company='天津吉众科技有限公司')
print('PARSE RESULT:', res['success'], 'Total employees:', res['employee_count'], 'Regular hours:', res['total_regular_hours'], 'Meals:', res['total_meals'])
" """

stdin, stdout, stderr = client.exec_command(f"docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 {exec_cmd}")
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')

print("OUT:", out)
if err:
    print("ERR:", err)

client.close()
