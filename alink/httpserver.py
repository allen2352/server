from alink.services import DataBase,Cookie,Timer
from alink.request import Request
from alink.response import Http_Response,_200,_404
#-------------------------------------------------------------
from vm import RDisk
from socket import socket,AF_INET,SOCK_STREAM,gethostname,gethostbyname,SOL_SOCKET,SO_REUSEADDR,timeout,SOCK_DGRAM
from os import getcwd,listdir
from os.path import isfile,isdir
from ssl import SSLContext,PROTOCOL_TLS_SERVER,SSLError,SSLEOFError
from threading import Thread
from time import sleep,time,localtime

HttpDB=DataBase()
def display_time(t):
    lt=localtime(t)
    return f'{lt.tm_year}/{lt.tm_mon}/{lt.tm_mday} {lt.tm_hour}:{lt.tm_min}:{lt.tm_sec}'
def get_host_ip():
    s = socket(AF_INET,SOCK_DGRAM)
    s.settimeout(2)
    try:
        s.connect(("8.8.8.8", 80))    #https://dns.google/
        ip=s.getsockname()[0]
    except timeout:
        ip=gethostbyname(gethostname())
    s.close()
    return ip
#傳回封包:版本 狀態碼 短語
void_html='''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
</head>
<body>
    
</body>
</html>'''
file_timer=Timer()
def return_http_file(filepath,disk=None,need_execute=True,output_port=None):
    if disk==None:
        disk=RDisk()
    if disk.isfile(filepath):
        mime_dict={
            'jpg':'image/jpg','png':'image/png','gif':'image/gif','jpeg':'image/jpeg','jfif':'image/jfif',    #圖片
            'mp3': 'audio/mpeg',                                                                              #音樂
            'mpeg': 'video/mpeg', 'mp4': 'video/mp4',                                                         #影片
            'html':'text/html','css':'text/css','js':'text/plain',                                            #網頁
            'pdf':'application/pdf','doc':'application/msword','docx':'application/msword',                   #文件
            'py':'text/plain','cpp':'text/plain','c':'text/plain','cs':'text/plain',                          #程式碼
            'ino':'text/plain','php':'text/plain',
            'txt': 'text/plain','csv': 'text/plain','json': 'text/plain','url': 'text/plain',                 #純文字
            'ttc':'Font'                                                                                      #字型
        }
        http_response=Http_Response(200)
        http_response.set_file_obj(filepath,disk)
        #file = disk.open(filepath, 'rb')  # open file , r => read , b => byte format
        #response = file.read()
        #http_response.content = response

        content_length=disk.getsize(filepath)
        filetype=filepath.split('.')[-1]
        if filetype in mime_dict:
            mimetype=mime_dict[filetype]
            if not need_execute and filetype in ('html','css'):
                mimetype='text/html'
        else:
            mimetype = 'text/html'
        http_response.add_header({'Content-Type':mimetype,'Content-Length':content_length})
        if mimetype.split('/')[0]=='video':
            http_response.add_header({'Accept-Ranges':'bytes','Connection': 'keep-alive'})
       # http_response.content=response
        if filepath.split('/')[-1]!='favicon.ico':                     #發送停止請求
            http_response.output_port=output_port
    else:http_response=_404
    return http_response
class HttpServer:
    def __init__(self):
        self.identify_user_method='cookie'    #利用 cookie 來辨識 來源使用者
        self.ssl=['','']
        self.reset()
    def reset(self):
        self.rdisk=RDisk()
        self.speed=2**16
        self.routes=[]          #[(route,methods_list,func),...]
        self._404_func=None     #如果沒有方法和檔案符合請求，就執行這個方法
        self.port=3030
        self.cookie=None
        self.template_path=getcwd().replace('\\','/')
    def set_identify(self,identify_user_method):      #可用: ip(xxx.xxx.xxx.xxx), cookie ,none(默認全為同一個使用者)
        self.identify_user_method=identify_user_method.lower()
    def set_template_path(self,folderpath):
        if isdir(folderpath):
            if folderpath[-1] not in ('\\','/'):
                folderpath+='/'
            self.template_path=folderpath
        else:
            raise FileNotFoundError('指定路徑不存在:',folderpath)
    def add_route(self,path,methods_list,func):
        for i in range(len(methods_list)):
            methods_list[i]=methods_list[i].upper()
        self.routes.append((path.lstrip('/'),methods_list,func))
    def mainloop(self):
        def deal_accept():
            self.now_accept+=1
            try:
                self.__accept_client()
            #except Exception as e:  #未知錯誤
             #   print(e)
              #  print('遇見未知錯誤')
            finally:
                self.now_accept -= 1
        my_ip =get_host_ip()
        listener = socket(AF_INET, SOCK_STREAM)
        #listener.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        listener.bind((my_ip, self.port))
        listener.listen(5)
        if self.ssl[0]!='':
            context = SSLContext(PROTOCOL_TLS_SERVER)              # 生成SSL上下文
            context.load_cert_chain(self.ssl[0],self.ssl[1])             # 加载服务器所用证书和私钥
            listener=context.wrap_socket(listener, server_side=True)
            print(f'連線位址: https://{my_ip}:{self.port}\n伺服器啟動中...')
        else:
            print(f'連線位址: http://{my_ip}:{self.port}\n伺服器啟動中...')
        #listener.setblocking(False)  # 將此socket設成非阻塞
        self.listening=True
        self.now_accept=0     #目前請求尚未處理完畢的次數
        while True:
            if self.now_accept>4:       #目前處理過多，暫停接客
                sleep(0.1)
            try:
                self.conn_address = listener.accept()
                #print('請求尚未完成:',self.now_accept)
            except SSLError:
                #print('\r[證書不被信任]',end='')
                continue
            except KeyboardInterrupt:
                print('KeyboardInterrupt')
                break
            except Exception as e:
                print(e)
                print('accept失敗')
                continue
            Thread(target=deal_accept).start()
            while self.conn_address!=0:
                sleep(0.1)
        listener.close()
        self.listening=False
    def __accept_client(self):
        conn,address=self.conn_address
        self.conn_address=0
        #--------------------------------------------------#處理收到的請求
        #print('處理收到')
        http_content=conn.recv(self.speed)
        if http_content==b'':
            print('收到空訊息:',http_content)
            conn.send(_404.to_bytes())
            conn.close()
            return
        #-------------------------------------------------- #取得請求資訊
       # print('-----------------------', display_time(time()))
        #print(http_content)
        try:
            request=Request(http_content,conn)
        except Exception as e:
            print(e)
            print('收到無法解析的請求')
            conn.send(_404.to_bytes())
            conn.close()
            return
        if self.identify_user_method=='cookie':
            if 'Cookie' not in request.header_params:
                id=None
            else:
                cookie=Cookie(request.header_params['Cookie'])
                id=int(cookie['id'])
            user=HttpDB.get_user(id)
        elif self.identify_user_method=='ip':
          #  print('address:  ',address)   ->  ('192.168.1.142', 56443)  port 每次都會變動，只有 ip 能作為辨識
            user=HttpDB.get_user(address[0])
        else:
            user=HttpDB.get_user('none')     #為 none 帳戶，所有人通用
        request.address=address
        #--------------------------------------------------
        method=request.method.upper()
        path=request.url
        reply=None
        #--------------------------------------------------投入函數
        for i in range(2):
            for route in self.routes:
                if path==route[0] and method in route[1]:
                    reply=route[2](user,request)
                    break
            if reply==None and self._404_func==None:
                if ':' not in path:  # 代表是相對路徑
                    path = path.lstrip('/')  # 去掉字串左方所有"/"
                    if path == '':
                        path = 'index.html'  # Load index file as default
            else:break
        #-------------------------------------------------回復用戶端
        if reply==None:
            if ':' not in path:
                path = self.template_path + path
            reply=return_http_file(path,self.rdisk)
            if reply==_404 and self._404_func!=None:
                reply=self._404_func(user,request)
        #------------------------------------------------------
        if self.identify_user_method == 'cookie':
            reply.set_header('Set-Cookie',user['cookie'])
        reply.set_header('Accept-Ranges','bytes')
        #------------------------------------------------------
        send_size=2**20       #32MB
        if 'Range' in request.header_params:
            reply.status_code=206
            send_range=request.header_params['Range'].split('bytes=')[-1].split('-')
            start_byte=int(send_range[0])
            if send_range[1]=='':
                end_byte=len(reply.content)
            else:
                end_byte=int(send_range[1])+1
            reply.set_header('Content-Range',f'bytes {start_byte}-{end_byte-1}/{len(reply.content)}')
            if type(reply.content)!=bytes:
                reply.content.content_range=[start_byte,end_byte]
            else:
                reply.content=reply.content[start_byte:end_byte]
            reply.set_header('Content-Length',str(end_byte-start_byte))
        send_byte=reply.to_bytes()
       # open('sss.html', 'wb').write(reply.content)
        #open('com1.txt','wb').write(send_byte)
        #print('send長度:',len(send_byte))
        process=0
        total=len(send_byte)
        conn.settimeout(5)  # 設定超時
        #----------------------------------------reply.cmds
        my_output_port=int(time())
        user['output_port'][reply.output_port]=my_output_port
      #  print('reply----------------',display_time(time()))
       # print(reply.get_header_bytes())
        while process<total:
            code=send_byte[process:process+send_size]
            try:
                if len(code)>0:
                    conn.send(code)
                    process+=len(code)
                else:break
            except ConnectionResetError as e:    #遠端連線被關閉
                print(e)
                break
            except timeout:
                print('\r傳送超時，重新傳送',end='')
                sleep(1)
            except ConnectionAbortedError:
                print('[連線被終止]')
                break
            #查看是否在請求終止符中
            if user['output_port'][reply.output_port]>my_output_port:
                print(f'\r{total}[當前輸出已停止]')
                break
            if total>send_size:
                print(f'\r處理:{path} 進度:{process}/{total} {round(process/total*100,2)}%',end='')
            if not self.listening:
                print('伺服器已關閉')
                break
        #------------------------------------------------關閉連線
        conn.close()
class HttpsServer(HttpServer):
    def __init__(self,crf_filepath,key_filepath):
        super().__init__()
        self.ssl=[crf_filepath,key_filepath]
        self.reset()