import os
import sys
import time
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(r"d:\SynologyDrive团队\antigravity\erpnext16\.env")

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')

session = requests.Session()

# 等待站点就绪
for i in range(10):
    try:
        r = session.get(f"{SITE_URL}/api/method/ping")
        if r.status_code == 200:
            print("Site is ready (ping ok)!")
            break
    except Exception as e:
        print("Waiting...", e)
    time.sleep(2)

login_resp = session.post(f"{SITE_URL}/api/method/login", data={
    "usr": USERNAME,
    "pwd": USER_PWD
})
print("Login status:", login_resp.status_code, login_resp.text[:100])

# 调用 set_qifu_housing_fund_batch
method_url = f"{SITE_URL}/api/method/ashan_cn_procurement.services.employee_salary_service.set_qifu_housing_fund_batch"
res_min = session.post(method_url, data={"mode": "min"})
print("\n[HTTP Call mode=min]:", res_min.status_code, res_min.text)

res_zero = session.post(method_url, data={"mode": "zero"})
print("\n[HTTP Call mode=zero]:", res_zero.status_code, res_zero.text)

res_restore = session.post(method_url, data={"mode": "min"})
print("\n[HTTP Restore mode=min]:", res_restore.status_code, res_restore.text)
