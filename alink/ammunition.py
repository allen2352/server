from alink.request import Request
from alink.tool import UniDict,URL,Debug
from alink.response import parse_response,_404,_timeout,Http_Response
from ssl import wrap_socket,CERT_NONE,PROTOCOL_SSLv23,SSLError
from socket import socket,AF_INET,SOCK_STREAM,gethostname,gethostbyname,SOL_SOCKET,SO_REUSEADDR,timeout,gaierror
from time import time,sleep


d=Debug('ammunition.py')

class Bullet:                         # 空子彈
    def __init__(self):
        self.request=Request()
    def to_bytes(self):
        return self.request.to_bytes()
class Domain_Bullet:                    #產生與 domain 相關的 request
    def __init__(self,url):
        curl=URL(url)
        self.request=Request(f'GET {curl.uri} HTTP/1.1\r\nHOST: {curl.domain}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)'.encode('utf-8'))
    def to_bytes(self):
        return self.request.to_bytes()
class Depot:              #彈藥庫
    def __init__(self):
        self.bullet_dict=UniDict({'void':Bullet,'domain':Domain_Bullet})
    def get_bullet(self,bullet_name):
        return self.bullet_dict[bullet_name]
#--------------------------------------------------------------
class Gun:
    def __init__(self,gun_setting,timeout=5):
        self.setting=gun_setting
        self.timeout=timeout
        self.connecting=False
        self.rebuild_times=3     #有三次重射機會
        self.rebuild()
    def rebuild(self):
        self.rebuild_times-=1
        if self.connecting:
            self.conn.close()
        self.conn = socket(AF_INET, SOCK_STREAM)
        self.connecting = False
    def shot(self,bullet=None):
        if bullet==None:
            bullet=Bullet()
        if not self.connecting:
            try:
                if self.setting['ssl']:
                    self.conn = wrap_socket(self.conn, ssl_version=PROTOCOL_SSLv23, cert_reqs=CERT_NONE)
            except:
                d.log('ssl 錯誤',color='fail')
                return _404
            try:
                self.conn.connect((self.setting['ip'],self.setting['port']))
            except gaierror:
                d.log(self.setting['ip']+'  不存在',color='fail')
                return _404
            except SSLError:
                d.log('SSL error',color='fail')
                return _404
            #self.conn.settimeout(self.timeout)
            self.connecting=True
       # print('send:\n',bullet.to_bytes())
        self.conn.send(bullet.to_bytes())
        #----------------------------------------------------開始接受資料
        try:
            result=self.recv(2**14)
        except timeout:
            d.log('收取表頭時間超時',color='fail')
            if self.rebuild_times>0:
                d.log('重射，剩餘',self.rebuild_times,'次',color='warning')
                self.rebuild()
                return self.shot(bullet)
            else:
                return _timeout
        try:
           # print('result:\n',result)
            return parse_response(result,self)
        except Exception as e:
            d.log('遇到無法解析的result:\n',result,color='fail')
            raise e
       # return _404
    def recv(self,n,time_out=None):
        if time_out==None:
            time_out=self.timeout
        st=time()+time_out
        self.conn.setblocking(False)
        ok=False
        while time()<=st:
            try:
                code=self.conn.recv(n)
                ok=True
                break
            except:sleep(0.1)
        self.conn.setblocking(True)
        if not ok or len(code)==0:
            raise timeout()
        return code
    def recv_all(self):     #接收到沒資料
        recv_size = 2**10
        recv_max_size=2**20
        recv_time_out=self.timeout
        recv_min_time_out=1
        #-------------------------------------
        content_list=[]
        st=time()
       # print('recv_all')
        while True:
            try:
                #print('收',recv_size,recv_time_out)
                code = self.recv(recv_size, recv_time_out)
                content_list.append(code)
                #-----------------------------------------
                recv_size=min(recv_size*2,recv_max_size)
                recv_time_out = min(max(recv_time_out*0.9,time()-st+recv_min_time_out),self.timeout)
                st=time()
            except timeout:
                #print('請求timeout，原大小:', len(content_list[0]))
                break
        return b''.join(content_list)
    def destroy(self):
        pass
#--------------------------------------------------------------------
import requests
class Accurate_Gun:
    def __init__(self, gun_setting, timeout=5):
        self.setting = gun_setting
        self.timeout = timeout
    def shot(self,bullet=None):
        if bullet==None:
            bullet=Bullet()
        request=bullet.request
        #-----------------------------------------------------
        url=self.setting['effective_domain']+request.uri.rstrip('/')
        headers=request.header_params.data
        #------------------------------------------------
        method=request.method.upper()
       # print('url:',url)
       # print('headers:',headers)
        if method=='GET':
            r=requests.get(url,headers=headers,timeout=self.timeout,stream=True)
        elif method=='POST':
            r=requests.post(url,data={},headers=headers,timeout=self.timeout,stream=True)
        else:
            raise Exception('ammunition.py  未收錄的method:'+method)
        #----------------------------------------------------開始接受資料
        response=Http_Response(r.status_code,r.content)
        #open('ss.html','wb').write(r.content)
        response.header_params=UniDict(r.headers)
        response.header_params['Content-Encoding']=r.encoding
        response.encoding=r.encoding
        #print('content長:',len(r.content))
        #print(response.to_bytes())
        return response
    def recv(self,n):
        pass
    def destroy(self):
        pass