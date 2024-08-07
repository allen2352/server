from alink.ammunition import Depot,Gun,Accurate_Gun
from alink.tool import URL,Debug
#---------------------------------------------------------
from ssl import wrap_socket,CERT_NONE,PROTOCOL_SSLv23
from socket import socket,AF_INET,SOCK_STREAM,gethostname,gethostbyname,SOL_SOCKET,SO_REUSEADDR,timeout
from threading import Lock
from time import sleep,time
from os.path import isfile
#import ssl
#ssl._create_default_https_context =ssl._create_unverified_context

d=Debug('roaming')

class DNS:                                #用來查詢網址要連結的
    def __init__(self):
        self.database={}
        self.save_path='alink/data/.DNS'
        self.depot=Depot()
        self.load()
    def load(self):        #載入 DNS資料
        if isfile(self.save_path):
            content=open(self.save_path,'r',encoding='utf-8').read().split('\n')
            for line in content:
                if '/' in line:
                    domain,ip,port,is_ssl,effective_domain=line.split('//\\\\')
                    self.database[domain]={'ip':ip,'port':int(port),'ssl':int(is_ssl),'effective_domain':effective_domain}
    def get(self,url,try_times=1):                             #返回 gun_setting
        curl=URL(url)
        if curl.domain in self.database:
            gun_setting=self.database[curl.domain]
            return gun_setting
        if curl.https:
            try_order=(1,0,443,80)
        else:
            try_order=(0,1,80,443)
        bullet = self.depot.get_bullet('domain')(url)
        need_301=False
        for try_method in range(2):
            for is_ssl in try_order[:2]:
                for port in try_order[2:]:
                    gun_setting={'ip':curl.ip,'port':port,'ssl':is_ssl,'url':url}
                    gun = Gun(gun_setting)
                    result=gun.shot(bullet)
                    gun.destroy()
                    rc=('成功','ok') if result.status_code==200 else ('失敗','fail')
                    d.log(f'DNS 嘗試連線 {curl.ip}:{port} {rc[0]} with status_code:{result.status_code}',color=rc[1])
                    if result.status_code==200:
                        curl.effective(https=is_ssl)
                        gun_setting['effective_domain']=curl.effective_domain
                        open(self.save_path, 'a', encoding='utf-8').write('\n'+'//\\\\'.join([curl.domain,curl.ip,str(port),str(is_ssl),curl.effective_domain]))
                        self.database[curl.domain]=gun.setting
                        return gun.setting
                    elif result.status_code==301 and try_times>0:
                        d.log('response結果:\n',result.header_params)
                        d.log('重新導向...',color='warning')
                        domain=curl.domain
                        if 'www.'==curl.domain[:4]:
                            try_domain=domain[4:]
                        else:
                            try_domain='www.'+domain
                        try:
                            return self.get(try_domain,try_times-1)
                        except Exception as e:
                            d.log(str(e),color='fail')
                            d.log('重新導向失敗',color='fail')
        raise Exception('roaming.py  DNS:無效的網址 > '+url)
dns=DNS()
lock=Lock()
#f=open('log.txt','w',encoding='utf-8')
class HttpClient:
    def __init__(self,timeout=5,threads=False):
        self.speed = 2 ** 20      # 1MB
        self.timeout=timeout
        self.guns={}
        self.multiple_threads=threads
    def send(self,url,request):
        if not self.multiple_threads:
            lock.acquire()
        try:
            curl=URL(url)
            if curl.domain not in self.guns:       #同一個域名用同一把槍
                gun_setting=dns.get(url)
                #gun=Gun(gun_setting,self.timeout)
                gun =Gun(gun_setting, self.timeout)
                if not self.multiple_threads:
                    self.guns[curl.domain]=gun
            else:
                gun=self.guns[curl.domain]
            response=gun.shot(request)
            if self.multiple_threads:
                gun.destroy()
        finally:
            if not self.multiple_threads:
                lock.release()
        return response
    def browse(self,url):      #瀏覽一個網站，每次使用會自動依據上次 response 變更 header 狀態
        request=Request()
        reply=self.send(url,request)
        return reply





















