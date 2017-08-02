# coding:utf-8
'''
Created by dengel on 16/2/22.

@author: stone

'''
import sys,os,django
import redis
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) #manage.py的目录
#sys.path.append("/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages")
os.environ['DJANGO_SETTINGS_MODULE'] = 'jcsbms.settings' #setting的目录
django.setup()
from jcsbms.utils import push_article
from article.models import Article
from datetime import datetime



class Task(object):
    def __init__(self):
        self.rcon = redis.StrictRedis(host='192.168.20.13', port=6379, db=0, password="UYS8wDysc9FC3hJWZJbsU3XE98Jj")
        self.ps = self.rcon.pubsub()
        self.ps.subscribe('charge_add')

    def listen_task(self):
        for i in self.ps.listen():
            #print(str(i))
            if i['type'] == 'message':
                try:
                    print str(datetime.now())+"::"+"Task get", i['data']

                    print str(datetime.now())+"::"+"push sucessed:", i['data']
                except Exception as e:
                    traceback.print_exc()

if __name__ == '__main__':

    print str(datetime.now())+"::"+'Start listen article_add channel'
    Task().listen_task()