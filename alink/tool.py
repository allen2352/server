from urllib.parse import unquote,quote
from time import time,localtime
class UniDict:                   #一個通俗字典，Content-Length、content-length 裡面的key不分大小寫
    def __init__(self,data=None):
        self.clear()
        if data!=None:
            for key in data:
                self[key]=data[key]
    def clear(self):
        self.data = {}  # key : value
        self.collect_keys = {}  # lower key : orig key
    def __setitem__(self, key, value):
        if type(key)==str:
            if key.lower() in self.collect_keys:
                key=self.collect_keys[key.lower()]
            else:
                self.collect_keys[key.lower()]=key
        self.data[key]=value
    def __getitem__(self, key):
        if type(key)==str:
            key=self.collect_keys[key.lower()]
        return self.data[key]
    def __delitem__(self, key):
        if type(key)==str:
            key=self.collect_keys[key.lower()]
            del self.collect_keys[key.lower()]
        del self.data[key]
    def __contains__(self,key):
        if type(key)==str:
            return key.lower() in self.collect_keys
        return key in self.data
    def __str__(self):
        box=[]
        for key in self.data:
            box.append(f'{key}:{self.data[key]}')
        return '\n'.join(box)
    def __iter__(self):
        for key in self.data:
            yield key
    def items(self):
        return self.data.items()
    def copy(self):
        ud=UniDict()
        ud.data=self.data.copy()
        ud.collect_keys=self.collect_keys.copy()
        return ud
    def update(self,_dict):
        for key in _dict:
            self[key]=_dict[key]
    def to_bytes(self):
        byte_box = []
        for key in self.data:
            byte_box.append(f'{key}:{self.data[key]}'.encode('utf-8'))
        return b'\r\n'.join(byte_box)
class URL:
    def __init__(self,url):
        url = url.replace('\\', '/')
        self.url=url
        # ---------------------------------------------------------判斷為https 或 http 或都不是
        self.https=url[:8]=='https://'
        #----------------------------------------------------------擷取domain
        if url[:4] != 'http':
            url = 'http://' + url
        p, n = url.index('//') + 2, len(url)
        try:
            k = url.index('/', p)
            self.uri=url[k:]
        except:
            k = n
            self.uri='/'
        self.domain = unquote(url[p:k])
        #-----------------------------------------------------------domain 轉 ip
        try:
            self.ip = gethostbyname(self.domain)
        except:
            self.ip = self.domain
        self.effective()
    def __str__(self):
        return f'url:{self.url}\nis https:{self.https}\neffective_url:{self.effective_url}\nuri:{self.uri}\ndomain:{self.domain}\nip:{self.ip}'
    def effective(self,https=None):      #讓自己的 url 正規化
        if https==None:
            if 'https://'!=self.url[:8] or 'http://'!=self.url[:7]:
                self.effective_url='http://'+self.url.lstrip('/')
            else:self.effective_url=self.url
        else:
            _url=(self.domain+self.uri).rstrip('/')
            if https:
                self.effective_url='https://'+_url
            else:self.effective_url='http://'+_url
        p=self.effective_url.index('//')
        self.effective_domain=self.effective_url[:p+2+len(self.domain)]
bcolors={
    'OK' : "[92m",  # GREEN
    'WARNING' : "[93m",  # YELLOW
    'FAIL' : "[91m",  # RED
    'RESET' : "[0m"}  # RESET COLOR
def now_time():
    l=localtime(time())
    return f'{l.tm_year}/{l.tm_mon}/{l.tm_mday} {l.tm_hour}:{l.tm_min}:{l.tm_sec}'
_debug=True
class Debug:
    def __init__(self,log_name):
        self.log_name=log_name
        self.__f=open(f'alink/data/{log_name}.debug','w',encoding='utf-8')
        self.__f.write(f'{now_time()}  start debug...')
    def log(self,*args,**kwargs):
        if _debug:
            color=''
            if 'color' in kwargs:
                color=bcolors[kwargs['color'].upper()]
            string=' '.join(map(str,args))
            self.__f.write(f'{now_time()}  {string}\n')
            print(color+self.log_name+' : '+string+bcolors['RESET'])

















