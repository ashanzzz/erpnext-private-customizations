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
        print(f"API Error on {method} {endpoint}: {e}")
        return None

# 读取本地 ashan_cn_sidebar.js
js_file_path = os.path.join('ashan_cn_procurement', 'ashan_cn_procurement', 'public', 'js', 'ashan_cn_sidebar.js')
if not os.path.exists(js_file_path):
    print("错误: 找不到侧边栏 JS 文件:", js_file_path)
    sys.exit(1)

with open(js_file_path, 'r', encoding='utf-8') as f:
    js_code = f.read()

# 推送为 ERPNext 系统的全局 Client Script
script_name = "Global Desk Two Level Sidebar"
encoded_name = urllib.parse.quote(script_name)

existing = call_api(f'/api/resource/Client%20Script/{encoded_name}')

payload = {
    "dt": "User",  # 绑到全局
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
    print(f" [SUCCESS] 成功{action}全局一二级侧边栏 Client Script: '{script_name}'")
else:
    print(f" [INFO] 提交全局 Client Script 完成")
