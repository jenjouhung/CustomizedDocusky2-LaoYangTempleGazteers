import json
from urllib.request import urlopen, Request
try:
    with urlopen('http://127.0.0.1:4180/local-info') as r: info=json.load(r)
    req=Request('http://127.0.0.1:4180/manage/stop',data=b'{}',headers={'X-Local-Token':info['token'],'Content-Type':'application/json'})
    with urlopen(req) as r: print(json.load(r)['message'])
except OSError: print('平台未啟動。')
