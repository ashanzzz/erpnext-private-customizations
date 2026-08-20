import urllib.request
import urllib.parse
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = 'http://192.168.8.11:6888'
token = os.environ["ERPNEXT_TOKEN"]
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

# 读取侧边栏 JS 源码
js_file_path = os.path.join('ashan_cn_procurement', 'ashan_cn_procurement', 'public', 'js', 'ashan_cn_sidebar.js')
with open(js_file_path, 'r', encoding='utf-8') as f:
    js_code = f.read()

# 在 Navbar Settings 中插入一个 Action
nav_doc = call_api('/api/resource/Navbar%20Settings/Navbar%20Settings')

if nav_doc and 'data' in nav_doc:
    nav_data = nav_doc['data']
    items = nav_data.get('settings_dropdown', [])
    
    # 构造包裹的 JS Action 字符串
    action_js = f"eval: (function(){{ {js_code} if(typeof init_ashan_cn_sidebar === 'function') init_ashan_cn_sidebar(); }})()"
    
    # 查找是否有现有的 Sidebar Action
    found = False
    for item in items:
        if item.get('item_label') == 'Ashan Sidebar Init':
            item['action'] = action_js
            item['hidden'] = 0
            found = True
            break
            
    if not found:
        items.append({
            "item_label": "Ashan Sidebar Init",
            "item_type": "Action",
            "action": action_js,
            "hidden": 0,
            "is_standard": 0
        })
        
    upd_res = call_api('/api/resource/Navbar%20Settings/Navbar%20Settings', method='PUT', data={"settings_dropdown": items})
    if upd_res and 'data' in upd_res:
        print(" [SUCCESS] 成功在 Navbar Settings 中植入 Navbar Action JS 脚本！")
    else:
        print(" [FAILED] 更新 Navbar Settings 失败")
