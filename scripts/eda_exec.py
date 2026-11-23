# -*- coding: utf-8 -*-
"""把 JS 文件发到 EasyEDA Bridge 执行。用法: python eda_exec.py code.js [windowId]"""
import json, sys, urllib.request
port = 49620
code = open(sys.argv[1], encoding='utf-8').read()
body = {'code': code}
if len(sys.argv) > 2:
    body['windowId'] = sys.argv[2]
data = json.dumps(body).encode('utf-8')
req = urllib.request.Request(f'http://127.0.0.1:{port}/execute', data=data,
                             headers={'Content-Type': 'application/json'})
try:
    r = json.load(urllib.request.urlopen(req, timeout=90))
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', 'ignore')
    print('HTTP', e.code, body[:1500]); sys.exit(1)
except Exception as e:
    print('HTTP ERROR:', e); sys.exit(1)
print(json.dumps(r, ensure_ascii=False, indent=1))
