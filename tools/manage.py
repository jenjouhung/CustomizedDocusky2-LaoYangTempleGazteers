"""Local file-management bridge. Search always runs in browser; public build excludes this."""
import argparse, http.server, json, secrets, threading, urllib.parse, subprocess, sys, socket, webbrowser, errno
from pathlib import Path
from packages import ROOT,DATA,import_file,manifest,backup,restore,set_current,public_build
from updater import update
TOKEN=secrets.token_urlsafe(32)
def choose(kind):
    prompt='選擇 Excel 修訂版' if kind=='xlsx' else '選擇 ZIP 備份'
    script=f'POSIX path of (choose file with prompt "{prompt}")'
    p=subprocess.run(['osascript','-e',script],capture_output=True,text=True)
    return Path(p.stdout.strip()) if p.returncode==0 else None
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT/'web'),**kwargs)
    def translate_path(self,path):
        path=urllib.parse.unquote(urllib.parse.urlsplit(path).path)
        base=DATA if path.startswith('/data/') else ROOT/'web'
        relative=path[6:] if path.startswith('/data/') else path.lstrip('/')
        candidate=(base/relative).resolve()
        if not candidate.is_relative_to(base.resolve()) or 'originals' in candidate.parts:return str(ROOT/'web'/'not-found')
        return str(candidate)
    def reply(self,obj,status=200):
        raw=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        if self.headers.get('Host') not in ('127.0.0.1:4180','localhost:4180'):return self.reply({'error':'Host 不符'},403)
        if self.path=='/local-info':return self.reply({'token':TOKEN,'app':'docusky-local'})
        return super().do_GET()
    def do_POST(self):
        if self.headers.get('Host') not in ('127.0.0.1:4180','localhost:4180') or self.headers.get('X-Local-Token')!=TOKEN:return self.reply({'error':'無效本機請求'},403)
        if self.headers.get('Origin') not in (None,'http://127.0.0.1:4180','http://localhost:4180'):return self.reply({'error':'來源不符'},403)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length>4096:raise ValueError('請求過大')
            payload=json.loads(self.rfile.read(length) or b'{}');action=self.path.removeprefix('/manage/');result={}
            if action=='import':
                path=choose('xlsx')
                if path is None:result={'cancelled':True,'message':'已取消'}
                else:
                    v=import_file(path);result={'message':f"已建立 {v['id']}，{v['count']} 筆，{len(v['warnings'])} 項警告"}
            elif action=='current':set_current(payload['version']);result={'message':'現行版本已切換'}
            elif action=='backup':result={'message':'備份已保存：'+str(backup())}
            elif action=='restore-backup':
                path=choose('zip')
                if path is None:result={'cancelled':True,'message':'已取消'}
                else:restore(path);result={'message':'備份已還原；舊資料已另行備份'}
            elif action=='build':result={'message':'靜態網站已建立：'+str(public_build())+'（尚未上傳）'}
            elif action=='update':
                path=choose('zip')
                if path is None:result={'cancelled':True,'message':'已取消'}
                else:update(path);result={'message':'前端核心已更新；請重新整理頁面。資料已備份，舊版程式保留於 previous-release。'}
            elif action=='stop':threading.Thread(target=self.server.shutdown,daemon=True).start();result={'message':'本機服務已停止'}
            else:raise ValueError('未知管理操作')
            self.reply(result)
        except Exception as e:self.reply({'error':str(e)},400)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['serve','import','build','backup','restore','current']);parser.add_argument('value',nargs='?');args=parser.parse_args()
    if args.action=='import':print(json.dumps(import_file(Path(args.value)),ensure_ascii=False))
    elif args.action=='build':print(public_build())
    elif args.action=='backup':print(backup())
    elif args.action=='restore':restore(Path(args.value))
    elif args.action=='current':set_current(args.value)
    else:
        try:server=http.server.HTTPServer(('127.0.0.1',4180),Handler)
        except OSError as error:
            if error.errno!=errno.EADDRINUSE:raise
            from urllib.request import urlopen
            with urlopen('http://127.0.0.1:4180/local-info') as r:
                if json.load(r).get('app')!='docusky-local':raise RuntimeError('4180 已被其他服務使用')
            webbrowser.open('http://127.0.0.1:4180');return
        subprocess.run(['open','-a','Google Chrome','http://127.0.0.1:4180'],check=False)
        print('http://127.0.0.1:4180',flush=True)
        try:server.serve_forever()
        finally:server.server_close()
if __name__=='__main__':main()
