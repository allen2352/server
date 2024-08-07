HttpsServer(crt,key) 或 HttpServer()                                                                           //httpserver.py
每次接受http請求時，會取得裡面的cookie來自動辨識user並配給，若不存在cookie會自動配給一個新user 
.add_route(path,method_list,func)              添加route和對應方法
._404_func                                     若無route匹配，用此方法
.set_template_path(folderpath)                 設置DocumentRoot
.mainloop()                                    開始執行
mainloop期間，接受請求與方法，透過設定的route查找對應的請求和方法，將user和request投入
被啟動的method需要return 「Http_Response」 物件給 HttpsServer 回傳
會配給 Cookie 的id

user是一個字典，裡面包著一個字典cookie物件，cookie中包著一個和其他user不一樣的id                                   //---   service.py
user最初長這樣: {'cookie':Cookie() }
user在server mainloop狀態下存在資料庫中，不會消失也不會損失資料
user可於每次連線重新讀取上次的資料

Cookie為一個可當字典的物件                                                                                      //---      services.py
cookie[key]=value    ;set
cookie[key]          ;get
.__str__             轉換為「Cookie內容」

Request為發送者解析後的請求                                                                                     //---      request.py
.http_content            為此次請求的全內容(含表頭和body)
.method                  此次的請求方法
.url                     不含?之前的請求網址
.GET_params              為一個字典{}，放著GET的參數值
.header_params           為一個字典{header_key : header_content}，e.g. Connection:keep-alive,Cookie : 「Cookie內容」
.content                 此次請求的body
.form_data               表單上傳檔案時，放置檔案物件
.get_name(name)          請求為post時，用name取得內容
.copy()                  重造一個相同的請求
.set_uri(uri)            重設uri
.clear_header()          清除header
.del_headers(key)        清除某個標頭行
.set_header(key,value)   設定標頭
.to_bytes()              轉換回byte

Http_Response(status_code,content) 放入 狀態碼 和 body                                                           //---       response.py
初始 header 為空
.encoding                    content的編碼，未設定時為unknow
.content                     內容
.add_header(header_dict)     添加header項目
.set_header(key,value)       設置header單項
.get_header_bytes()          獲得 response 的header轉換成bytes部分
.to_bytes()                  獲得 response 的全部byte部分(header 和 body)
.get_text()                  獲得解碼(gzip,utf-8)後的content內容

HttpClient                  向外發送請求的用戶端                                                               //---       roaming.py
.send(url,Request)          向特定目標發送請求


