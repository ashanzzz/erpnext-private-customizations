import urllib.request

try:
    with urllib.request.urlopen("http://192.168.8.11:8000", timeout=3) as resp:
        print("Port 8000 headers:", resp.headers)
        print("Port 8000 content snippet:", resp.read()[:500].decode('utf-8', errors='ignore'))
except Exception as e:
    print("Port 8000 Error:", e)

