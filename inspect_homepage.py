import urllib.request

req = urllib.request.Request('http://127.0.0.1:8000/')
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        print('STATUS', r.status)
        print(r.headers)
        print(r.read(4096).decode('utf-8', errors='replace'))
except Exception as exc:
    import traceback
    traceback.print_exc()
