import urllib.request

url = 'http://127.0.0.1:8000/'
try:
    with urllib.request.urlopen(url, timeout=10) as resp:
        print('status', resp.status)
        print('content-type', resp.getheader('Content-Type'))
        body = resp.read(200)
        print('body-prefix', body.decode('utf-8', 'ignore').replace('\n', ' ')[:200])
except Exception as exc:
    print('error', repr(exc))
