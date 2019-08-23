# coding:utf-8
import tornado.web,importlib,time
import tornado.ioloop,re
import psutil,json,os
from multiprocessing import Process
from cfunction import *

# 路由
class mainHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        self.write('爬虫监控V1')

#系统信息
class infoHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        res = {'cpu':getCPUstate(),'memery':getMemorystate()}
        res = json.dumps(res)
        self.write(res)

# 爬虫信息
class spiderinfoHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        # filelist = glob.glob('./spider/*.py')
        # spiderinfo = []
        # for name in filelist:
        #     name = re.findall('./spider/(?!__init__)(.*).py', name)
        spiderinfo = []
        for name in spiders.keys():
            if spiders[name]['process'].is_alive():
                spiders[name]['state'] = 1
                spiderinfo.append({'name':name,'state':1})
            else:
                spiders[name]['state'] = 1
                spiderinfo.append({'name':name,'state':0})
        self.write(json.dumps(spiderinfo))

#心跳检测
class heartHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        self.write('ok')

# 上传爬虫
class uploadHander(tornado.web.RequestHandler):
    def get(self):
        self.write('''
            <html>
              <head><title>Upload File</title></head>
              <body>
                <form action='upload' enctype="multipart/form-data" method='post'>
                <input type='file' name='file'/><br/>
                <input type='submit' value='submit'/>
                </form>
              </body>
            </html>
         ''')
    def post(self, *args, **kwargs):
        upload_path = os.path.join(os.path.dirname(__file__), 'spider')  # 文件的暂存路径
        file_metas = self.request.files.get('file', None)  # 提取表单中‘name’为‘file’的文件元数据
        for meta in file_metas:
            filename = meta['filename']
            file_path = os.path.join(upload_path, filename)
            with open(file_path, 'wb') as up:
                up.write(meta['body'])
                # OR do other thing
        # self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write("上传成功")

# 爬虫文件列表
class fileList(tornado.web.RequestHandler):
    def get(self):
        files = os.listdir(os.getcwd()+"\spider")
        data = []
        for info in files:
            if "__" not in info:
                data.append(info)
        self.write(json.dumps(data))

# 删除爬虫文件
class deleteHander(tornado.web.RequestHandler):
    def get(self):
        name = getparam(self=self,name='filename')
        if name != None:
            check = True
            try:
                check = os.remove('./spider/'+name)
            except:
                pass
            if check == None:
                successmsg(self,'删除成功')
            else:
                errormsg(self,'删除失败')

# 开启爬虫进程
class startHander(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        name = getparam(self,'name')
        if name == None:
            return
        filename = getparam(self,'filename')
        if filename == None:
            return
        num = None
        try:
            num = self.get_argument('num')
        except:
            pass
        if num == None or int(num) == 0 or int(num) == 1:
            if name not in spiders.keys():
                module = importlib.import_module('spider.'+filename)
                # 重载模块，保证模块修改后能重新加载
                importlib.reload(module)
                spiders[name] = {}
                spiders[name]['process'] = Process(target=module.start,args=(name,))
                spiders[name]['process'].start()
                spiders[name]['file'] = filename
                successmsg(self,'启动成功')
            else:
                res = {'code':0,'message':'NameAlreadyRun'}
                self.write(json.dumps(res))
        else:
            for i in range(int(num)):
                name2 = name + str(i)
                if name2 not in spiders.keys():
                    module = importlib.import_module('spider.' + filename)
                    spiders[name2] = {}
                    spiders[name2]['process'] = Process(target=module.start, args=(name2,))
                    spiders[name2]['process'].start()
                    spiders[name2]['file'] = filename
                else:
                    res = {'code': 0, 'message': 'NameAlreadyRun'}
                    self.write(json.dumps(res))
                    return
                time.sleep(0.1)
            successmsg(self, '启动成功' + str(num) + '个爬虫')




# 重启爬虫
class reloadHander(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        name = getparam(self,'name')
        if name == None:
            return
        print(spiders.keys())
        if name in spiders.keys():
            filename = spiders[name]['file']
            try:
                spiders[name]['process'].terminate()
                spiders[name]['process'].join()
            except:
                pass
            module = importlib.import_module('spider.'+filename)
            spiders[name]['process'] = Process(target=module.start,args=(name,))
            spiders[name]['process'].start()
            successmsg(self,'重启成功')
        else:
            errormsg(self,'进程未启动')

#停止爬虫进程
class stopHander(tornado.web.RequestHandler):
    def get(self):
        name = getparam(self=self, name='name')
        if name != None:
            if name in spiders.keys():
                spiders[name]['process'].terminate()
                check = spiders[name]['process'].join()
                if check == None:
                    spiders.pop(name)
                    successmsg(self, '停止成功')
            else:
                errormsg(self,'爬虫未启动')
                return


if __name__ == '__main__':
    redis = conRedis(db=3)
    app = tornado.web.Application([
        ('/',mainHandler),
        ('/sysinfo',infoHandler),
        ('/spiderinfo',spiderinfoHandler),
        ('/heart',heartHandler),
        ('/upload',uploadHander),
        ('/start',startHander),
        ('/delete',deleteHander),
        ('/stop',stopHander),
        ('/reload',reloadHander),
        ('/fileList',fileList)
    ])
    spiders = {}
    app.listen(9015)
    print('服务开启完成！')
    tornado.ioloop.IOLoop.current().start()
