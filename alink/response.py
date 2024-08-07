from alink.tool import UniDict
from time import sleep,time
from socket import timeout,socket,AF_INET,SOCK_STREAM
from gzip import decompress
class Http_file_object:
    def __init__(self,header_byte,file_object,file_object_len):
        self.set_header(header_byte)
        self.file_object=file_object
        self.file_object_len=file_object_len
        self.content_range=[0,self.file_object_len]
    def set_header(self,header_byte):
        self.header_byte=header_byte
        self.header_len=len(header_byte)
    def update(self,header_dict):
        for key in header_dict:
            self[key]=header_dict[key]
    def __len__(self):
        return self.header_len+self.content_range[1]-self.content_range[0]
    def __getitem__(self, item):
        start=item.start
        stop=item.stop
        return_box=[]
        if start<self.header_len:
            return_box.append(self.header_byte[start:])
        file_start=max(0,start-self.header_len)
        file_stop=max(0,stop-self.header_len)

        content_slice=[self.content_range[0]+file_start,min(self.content_range[1],self.content_range[0]+file_stop)]
        self.file_object.seek(content_slice[0], 0)
        content2 = self.file_object.read(content_slice[1]-content_slice[0])
        return_box.append(content2)
        return b''.join(return_box)
    def close(self):
        self.file_object.close()
def parse_response(http_response,conn=None):
    n = len(http_response)
    try:k = http_response.index(b'\n')
    except:k = n
    first_line = http_response[:k].decode('utf-8').split(' ')
   # print(first_line)
    http_version = first_line[0]
    status_code=first_line[1]
    # -----------------------------------------    處理首部欄位
    header_params = UniDict()             # 首部欄位參數
    while k < n:
        p = k + 1          # k 是 \n 的位置
        try:
            k = http_response.index(b'\n', p)
        except:
            k = n
        if http_response[k - 1] == 10:     # \r
            k2 = k - 1  # b'\r'
        else:
            k2 = k
        if abs(k - p) < 2:  # 代表接下來是content
            break
        deal_line = http_response[p:k2].decode('utf-8')
        if ':' in deal_line:
            ck=deal_line.index(':')
            header_key=deal_line[:ck]
            header_value=deal_line[ck+1:]
            if header_value[-1] == '\r':
                header_value = header_value[:-1]
            header_params[header_key] = header_value
    #避免有 \r\n的漏網之魚，再抓最後一次
   # if '\r\n'.encode('utf-8') in http_response[k + 1:k + 10]:
    #    k=http_response.index('\r\n'.encode('utf-8'),k+1)+1
    content_list = [http_response[k + 1:]]
    if 'Content-Length' in header_params and conn != None:
        content_length = int(header_params['Content-Length'])
        recv_length = len(content_list[0])
        if recv_length < content_length:
            # print('重新接收content，content_length=',content_length)
            while recv_length < content_length:
                try:
                    _content = conn.recv(2**20)  # 重新接收
                    recv_length += len(_content)
                    content_list.append(_content)
                except timeout:
                    print(f'收到Content Length:{content_length}      實際收到{recv_length}')
                    content_list.append(('0'*(content_length-recv_length)).encode('utf-8'))    #缺項補0
                    break
    elif conn!=None:     #依據文件接受設定timeout
        content_list.append(conn.recv_all())
    content = b''.join(content_list)

    response=Http_Response(status_code,content)
    response.http_version=http_version
    response.header_params=header_params
    if 'Content-Encoding' in header_params:
        response.encoding=header_params['Content-Encoding']
    return response
class Http_Response:
    def __init__(self,status_code,content=b''):
        self.status_code=int(status_code)
        self.header_params=UniDict()
        self.output_port=None      #輸出口
        self.encoding='unknow'
        self.content=content
        self.http_version='HTTP/1.1'
    def get_text(self):
        if self.encoding=='gzip':
            return decompress(self.content).decode('utf-8')
        return self.content.decode(self.encoding)
    def set_file_obj(self,filepath,disk):
        self.content=Http_file_object(b'',disk.open(filepath,'rb'),disk.getsize(filepath))
    def add_header(self,header_dict):
        self.header_params.update(header_dict)
    def set_header(self,key,value):
        self.header_params[key]=value
    def get_header_bytes(self):
        return self.header_params.to_bytes()
    def to_bytes(self):
        status_phrase={200:'OK',404:'Not Found',206:'Partial Content',304:'Not Modified',416:'Range Not Satisfiable'}
        byte_box=[]
        if self.status_code in status_phrase:
            byte_box.append(f'{self.http_version} {self.status_code} {status_phrase[self.status_code]}'.encode('utf-8'))
        else:
            byte_box.append(f'{self.http_version} {self.status_code} OK'.encode('utf-8'))
        for key in self.header_params:
            byte_box.append(f'{key}:{self.header_params[key]}'.encode('utf-8'))
        byte_box.append(b'')
        if type(self.content)==str:
            self.content=self.content.encode('utf-8')
        elif type(self.content)==Http_file_object:
            byte_box.append(b'')
            self.content.set_header(b'\r\n'.join(byte_box))
            return self.content
        elif type(self.content)!=bytes:
            print('content:')
            print(self.content)
            raise Exception('content不是bytes')
        byte_box.append(self.content)
        #print(b'\r\n'.join(byte_box))
        return b'\r\n'.join(byte_box)
_200=Http_Response(200)
_404=Http_Response(404,'''<html>
 <body>
   <center>
    <h3>Error 404: File not found</h3>
    <p>Python HTTP Server</p>
    </center>
 </body>
</html>
'''.encode('utf-8'))
_timeout=Http_Response(404,'''<html>
 <body>
   <center>
    <h3>Error 404: timeout </h3>
    <p>Python HTTP Server</p>
    </center>
 </body>
</html>
'''.encode('utf-8'))