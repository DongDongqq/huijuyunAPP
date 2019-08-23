"""
    @author: 王帅帅
    @project: huijiyunAPP
    @file: huijuyun_spider.py
    @time: 2019/8/19/019 14:31
    @desc:
"""
import requests
from spider.pycrypto_code import *
from spider.function import *
import json
from pymongo.errors import DuplicateKeyError
import pika
import threading
import time

headers = {
    'Accept-Encoding': '*',
    'User-Agent': 'Mozilla/4.0',
    'user-source': 'yun.wtoip.com/app',
    'Connection': 'Keep-Alive',
    'Content-Encoding': 'application/json',
    'Host': 'openapi.huijuyun.com'
}

def get_data(id):
    global proxy
    enc_data = encrypt_des('{"id":"%s"}'%id)
    try:
        url = 'http://openapi.huijuyun.com/openapi/V2/open/patent/getPatentById?token=&enc_data='+enc_data
        resp = requests.get(url=url, headers=headers,timeout=5, proxies=proxy)
        # print(resp.text)
        # print(decrypt_des(resp.text))
        # # data = json.loads(decrypt_des(resp.text))
        # # print(data)
        # time.sleep(3600)
        data = json.loads(decrypt_des(resp.text))
        if data['data']:
            data = {
                '_id': id,
                'data': data['data'],
            }
            try:
                db.test0819.insert_one(data)
            except DuplicateKeyError as D:
                pass
            return {
                'status': 1,
                'content': '获取信息成功'
            }
        else:
            return {
                'status': 1,
                'content': '没有此信息'
            }
    except requests.exceptions.ConnectionError as r:
        r.status_code = "Connection refused"
        proxy = get_proxy()
        return {
            'status': 0,
            'content': '请求错误，更换ip'
        }
    except Exception as e:
        print(e)
        proxy = get_proxy()
        return {
            'status': 0,
            'content': '请求错误，更换ip'
        }


def start():
    proxy = get_proxy()
    queue = 'wss_huijuyun'
    credentials = pika.PlainCredentials('guest', 'guest')
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        '192.168.1.157', 5672, '/', credentials, heartbeat=2000))
    channel = connection.channel()
    channel.queue_declare(queue=queue, durable=True)

    def callback(ch, method, properties, body):
        data_id = body.decode('utf-8')
        # data_id = 'CN201910010289.8'
        print('查询信息：', data_id)
        try:
            check = get_data(data_id)
            print(check)
            if check['status'] == 0:
                ch.basic_nack(delivery_tag=method.delivery_tag)
                return
            else:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
        except AttributeError:
            # redis 中 cookie 完了
            print("redis队列为空：AttributeError")
            channel.close()


    # 公平调度
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue, callback)
    channel.start_consuming()


if __name__ == '__main__':
    start()








