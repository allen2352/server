from os import listdir
from os.path import isdir,getsize
def listfile(folderpath):
    def listfolder(folderpath):
        for i in listdir(folderpath):
            if isdir(f'{folderpath}/{i}'):
                box.append(f'{i}**0')
                listfolder(f'{folderpath}/{i}')
            else:box.append(i+'**'+str(getsize(f'{folderpath}/{i}')))
    box=[]
    listfolder(folderpath)
    open('output.txt','w',encoding='utf-8').write('\n'.join(box))
def compare(filepath1,filepath2):
    f=open(filepath1,'r',encoding='utf-8').read().split('\n')
    g=open(filepath2,'r',encoding='utf-8').read().split('\n')
    print('檔案一長度:',len(f))
    print('檔案2長度:', len(g))
    for i in range(len(f)):
        if f[i]!=g[i]:
            print(f[i],'   ',g[i])
    print('結束')
listfile(r'D:\Games\Grand Theft Auto V')
