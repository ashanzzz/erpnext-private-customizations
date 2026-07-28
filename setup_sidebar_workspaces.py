import urllib.request
import urllib.parse
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = 'http://192.168.8.11:6888'
token = 'token 781e6538a0816f3:ebfe8d61c03e289'
headers = {'Authorization': token, 'Content-Type': 'application/json'}

def call_api(endpoint, method='GET', data=None):
    req_url = f"{url}{endpoint}"
    encoded_data = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(req_url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8')
            return json.loads(content) if content else {}
    except Exception as e:
        print(f"API Exception: {e}")
        return None

# 读取 JS 源码
js_file_path = os.path.join('ashan_cn_procurement', 'ashan_cn_procurement', 'public', 'js', 'ashan_cn_sidebar.js')
with open(js_file_path, 'r', encoding='utf-8') as f:
    js_code = f.read()

# 为多种场景绑定 Client Script，确保在 /app, /desk, /workspace 下全部执行
target_doctypes = ["Workspace", "DocType", "User"]

for dt in target_doctypes:
    script_name = f"Global Desk Sidebar Menu for {dt}"
    encoded_name = urllib.parse.quote(script_name)
    
    existing = call_api(f'/api/resource/Client%20Script/{encoded_name}')
    
    payload = {
        "dt": dt,
        "script": js_code,
        "enabled": 1,
        "view": "List"
    }
    
    if existing and 'data' in existing:
        res = call_api(f'/api/resource/Client%20Script/{encoded_name}', method='PUT', data=payload)
        action = "更新"
    else:
        payload["name"] = script_name
        res = call_api('/api/resource/Client%20Script', method='POST', data=payload)
        action = "新建"
        
    if res and 'data' in res:
        print(f" [SUCCESS] 成功{action} Client Script for {dt}")
    else:
        print(f" [INFO] 提交 Client Script for {dt} 完成")
