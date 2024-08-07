from alink.tool import UniDict
from random import random
class DataBase:
    def __init__(self):
        self.users = {}
        self.set_init_user_data(UniDict())
    def set_init_user_data(self, object):
        self.init_user_data = object
    def __new_user(self,id=None):
        user = self.init_user_data.copy()
        user['cookie'] = Cookie()
        #---------------------------------------
        if id==None:
            user['cookie']['id'] = cache['id']
            while cache['id'] in self.users:
                cache['id']+=1
        else:
            user['cookie']['id'] = id
        #---------------------------------------
        user['output_port'] = {}  # 輸出口列表{outputportname:time(),...}
        return user
    def get_user(self, id=None):
        if id==None:                         #註冊Cookie
            user=self.__new_user(id)
            id=user['cookie']['id']
            self.users[id] = user
        id=str(id)                    # id 可能是 數字、none、address
        if id not in self.users:
            user = self.__new_user(id)
            self.users[id] = user
        return self.users[id]
cache={'id':0}
class Cookie:
    def __init__(self,cookie_string=None):
        self.__cook_dict = {}
        if cookie_string!=None:
            items = cookie_string.split(';')
            for item in items:
                ck = item.index('=')
                self.__cook_dict[item[:ck]] = item[ck + 1:]
    def __setitem__(self, key, value):
        self.__cook_dict[key]=value
    def __delitem__(self, key):
        del self.__cook_dict[key]
    def __getitem__(self, item):
        return self.__cook_dict[item]
    def __contains__(self, item):
        return item in self.__cook_dict
    def __str__(self):
        cookie=[]
       # print(self.__cook_dict)
        for key in self.__cook_dict:
            cookie.append(f'{key}={self.__cook_dict[key]}')
        return ';'.join(cookie)
def html_convert(text):      #將文字內容轉換成可顯示在網頁上
    replace_box = [ ('>', '&gt;'), ('<', '&lt;'),(' ', '&ensp;'),
                    ("[91m",'<p style="color=red;">'),("[92m",'<span style="color=green;">'),
                    ("[0m",'</span>'),
                    ('\n', '<br>')]
    for rtext in replace_box:
        text = text.replace(rtext[0], rtext[1])
    return text
def display_size(size):   #Byte轉size
    for i in range(4):
        base=2**((3-i)*10)
        if size>base:
            return f'{round(size/base,2)}'+('GB','MB','KB','bit')[i]
class Timer:       #計時器
    def __init__(self,t=0):
        self.t=t
    def count(self):
        self.t+=1
        return self.t
