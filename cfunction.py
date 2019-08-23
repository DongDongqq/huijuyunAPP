# coding:utf-8
import json,redis,psutil
from pymongo import MongoClient

redisip = '192.168.1.157'
mongoip = '192.168.1.170'

# 获取系统信息函数
def getCPUstate(interval=1):
    return (str(psutil.cpu_percent(interval)) + "%")
def getMemorystate():
        phymem = psutil.virtual_memory()
        line = "%6s/%s"%(
            str(int(phymem.used/1024/1024))+"M",
            str(int(phymem.total/1024/1024))+"M"
            )
        return line
# 获取参数函数
def getparam(self,name):
    if name in self.request.arguments:
        param = self.get_argument(name)
        return param
    else:
        res = json.dumps({'code':0,'message':'badparam'})
        self.write(res)

# mongodb连接
def conMongo():
    conMongo = MongoClient(host=mongoip,port=27017)
    db = conMongo.gsxt
    return db

# redis连接
def conRedis(db=0):
    return redis.Redis(host=redisip, password='1234as', port=6379,db=db)

# err状态码
def errormsg(self,msg):
    data = {'code':0,'message':msg}
    self.write(json.dumps(data))
# success状态码
def successmsg(self,msg):
    data = {'code':1,'message':msg}
    self.write(json.dumps(data))

