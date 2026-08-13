import os
import json
import urllib.request
import urllib.parse
import http.cookiejar

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()

def main():
    site_url = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
    username = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
    password = os.getenv('ERPNEXT_PASSWORD', '')
    
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    # 1. Login
    login_url = f"{site_url}/api/method/login"
    login_data = json.dumps({"usr": username, "pwd": password}).encode('utf-8')
    req = urllib.request.Request(login_url, data=login_data, headers={'Content-Type': 'application/json'})
    
    try:
        resp = opener.open(req)
        print("Login response:", resp.read().decode('utf-8'))
    except Exception as e:
        print("Login failed:", e)
        return

    # 2. Save sidebar in User Settings for ashanzzz1213@gmail.com
    pages = [
        {"name": "Home", "title": "Home", "type": "workspace"},
        {"name": "My Business", "title": "我的业务", "type": "workspace"},
        {"name": "Vehicle Management", "title": "车油管理", "type": "workspace", "parent_page": "My Business"},
        {"name": "Compliance Center", "title": "公司合规中心", "type": "workspace", "parent_page": "My Business"},
        {"name": "Reimbursements", "title": "报销申请", "type": "workspace", "parent_page": "My Business"},
        {"name": "Oil Cards", "title": "油卡", "type": "workspace", "parent_page": "My Business"}
    ]
    
    save_url = f"{site_url}/api/method/frappe.model.utils.user_settings.save"
    save_data = json.dumps({
        "doctype": "Workspace",
        "user_settings": json.dumps({"sidebar_items": pages})
    }).encode('utf-8')
    
    req_save = urllib.request.Request(save_url, data=save_data, headers={'Content-Type': 'application/json'})
    try:
        resp_save = opener.open(req_save)
        print("Save user settings response:", resp_save.read().decode('utf-8'))
    except Exception as e:
        print("Save failed:", e)

if __name__ == '__main__':
    main()
