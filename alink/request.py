from alink.tool import UniDict
from vm import RDisk
from urllib.parse import unquote,quote
class Form_Object:
    def __init__(self,form_content):
        self.form_content=form_content
        # -----------------------------------------    處理欄位
        self.Content_Disposition ={}
        self.params = {}  # 首部欄位參數
        k=-1
        n=len(form_content)
       # print('form:')
        #print(form_content)
        while k < n:
            p = k + 1
            try:
                k = form_content.index(b'\n',p)
            except:
                k = n
            if form_content[k - 1] == 13: k2 =k- 1  # b'\r'
            else:k2=k
            if abs(k2- p) < 2:  # 代表接下來是content
                break
            deal_line =form_content[p:k2].decode('utf-8')
            if ':' in deal_line:
                c = deal_line.split(':')
                self.params[c[0]] = c[1]
                if c[0]=='Content-Disposition':
                    attrs=c[1].split(';')
                    CD={'Content-Disposition':attrs[0]}
                    for item in attrs[1:]:
                        ck=item.index('=')
                        attr_name=item[:ck].lstrip(' ')
                        value=item[ck+1:]
                        CD[attr_name]=value
                    self.Content_Disposition=CD
        self.content = form_content[k + 1:]
    def __getitem__(self, item):
        if item=='content':return self.content
        elif item in self.Content_Disposition:
            return self.Content_Disposition[item]
        return None
    def save(self,filepath,disk=None):
        if disk==None:
            disk=RDisk()
        filename=filepath.split('/')[-1]
        if filename!='':
            f = disk.open(filepath, 'wb')
            f.write(self.content)
            f.close()
            return True
        else:
            print('檔名不可為空')
            return False
#簡單的request
simple_request_content='GET / HTTP/1.1\r\n\r\n'.encode()
class Request:
    def __init__(self,http_content=simple_request_content,conn=None,recv_func=None):   #recv_func(cookie_string,now,total):顯示進度條
        self.request=self                #為了可以同時當 Bullet 用
        self.http_content=http_content
        self.conn=conn
        #請求封包:方法 URL 版本
        n=len(http_content)
        try:
            k=http_content.index(b'\n')
        except:
            k=n
        first_line=http_content[:k].decode('utf-8').rstrip('\r').split(' ')
        self.method = first_line[0]
        #----------------------------------------
        param_line=first_line[1].lstrip('/')
        self.uri=first_line[1]
        self.http_version=first_line[2]
        self.GET_params={}
        if '?' in param_line:               #查看GET參數
            ck=param_line.index('?')
            self.url=unquote(param_line[:ck])
            params=param_line[ck+1:]
            for item in params.split('&'):
                c=item.split('=')
                self.GET_params[c[0]]=unquote(c[1])
        else:
            self.url=unquote(param_line)
        #--------------------------處理url
        replace_box = {'%20': ' '}
        for key in replace_box:
            self.url=self.url.replace(key,replace_box[key])
        #-----------------------------------------    處理首部欄位
        self.header_params=UniDict()      #首部欄位參數
        while k<n:
            p=k+1
            try:
                k = http_content.index(b'\n',p)
            except:
                k = n
            if http_content[k - 1] == 10:
                k2 = k - 1  # b'\r'
            else:k2=k
            if abs(k-p)<2:    #代表接下來是content
                break
            deal_line=http_content[p:k2].decode('utf-8')
            if ':' in deal_line:
                c=deal_line.split(':')
                if c[1][-1]=='\r':value=c[1][:-1]
                else:value=c[1]
                #--------------------------------
                self.header_params[c[0]]=value.lstrip(' ')
        if 'Content-Length' in self.header_params and conn!=None:
            #print('有Content Length')
            self.content = [http_content[k + 1:]]
            content_length = int(self.header_params['Content-Length'])
            recv_length = len(self.content[0])
            if recv_length < content_length:
                # print('重新接收content，content_length=',content_length)
                speed = 2 ** 16          #64KB
                while recv_length < content_length:
                    content = conn.recv(speed)  # 重新接收
                    recv_length += len(content)
                    self.content.append(content)
                    #檔案上傳進度條
                    if recv_func!=None and 'Cookie' in self.header_params:
                        recv_func(self.header_params['Cookie'],recv_length,content_length)
            self.content = b''.join(self.content)
        else:
            self.content =http_content[k + 1:]
        #-------------------------------------------    處理multipart/form-data
        self.form_data=[]
        if 'Content-Type' in self.header_params:
            c=self.header_params['Content-Type'].split(';')
            ctype=c[0]
            if ctype[0]==' ':ctype=ctype[1:]
            if ctype=='multipart/form-data':
                k=c[1].index('=')
                boundary=c[1][k+1:].encode('utf-8')
                if boundary in self.content:
                    k=self.content.index(boundary)
                    n=len(self.content)
                   # print('n=',n)
                    while True:
                        p=k+len(boundary)
                        try:
                            k=self.content.index(boundary,p)
                        except:break
                        while self.content[p] in (13,10):p+=1       #(b'\r',b'\n')
                        k2=k-1
                        while self.content[k2]==45:k2-=1            # b'-'
                        if self.content[k2]==10:
                            k2-=1
                            if self.content[k2]==13:k2-=1
                        k2+=1
                        form_content=self.content[p:k2]
                        form_object=Form_Object(form_content)
                        self.form_data.append((form_object.Content_Disposition,form_object))
    def get_name(self,attr_name):
        results=[]
        for form_data in self.form_data:
            if 'name' in form_data[0] and form_data[0]['name']==attr_name:
                results.append(form_data[1])
        return results
    def set_uri(self,path,Get_params=None):          #設定統一資源識別符
        if Get_params!=None:
            box=[]
            for key in Get_params:
                box.append(key+'='+quote(Get_params[key]))
            path+='?'+'&'.join(box)
        self.uri=path
    def clear_header(self):
        self.header_params.clear()
    def del_headers(self,key_list):
        for key in key_list:
            del self.header_params[key]
    def set_header(self,key,value):                #設定表頭內容
        self.header_params[key]=value
    def to_bytes(self):                            #轉化為byte
        first_line_bytes=f'{self.method.upper()} {self.uri} {self.http_version}'.encode('utf-8')
        header_bytes=self.header_params.to_bytes()
        request_list=[first_line_bytes]
        if len(header_bytes)>0:
            request_list.append(header_bytes)
        request_list+=[b'',self.content]
        request_byte=b'\r\n'.join(request_list)
    #    print('request:')
     #   print(request_byte.decode('utf-8'))
        return request_byte
    def copy(self):                                     #複製Request用於代理
        return Request(self.http_content,self.conn)