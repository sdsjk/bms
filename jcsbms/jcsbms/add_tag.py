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
from jcsbms.utils import push_article, sysMonitorSMS, push_article_new_ios, push_article_from_service
from article.models import Article, ArticleChannel
from datetime import datetime
from settings import ALARM_CELLPHONES, REDIS_HOST, REDIS_PASSOWRD



class Task(object):
    def __init__(self):
        self.rcon = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0, password=REDIS_PASSOWRD)
        self.ps = self.rcon.pubsub()
        self.ps.subscribe('article_add')

    def listen_task(self):
        for i in self.ps.listen():
            #print(str(i))
            if i['type'] == 'message':
                try:
                    print str(datetime.now())+"::"+"Task get", i['data']
                    article = Article.objects.get(id=i['data'])
                    #不成功直接抛异常,无需检查返回码
                    if article.language == u'M':
                        for ap in article.articleportaltags_set.all():
                            if ap.portal.id in [2, 14]:
                                article_channel = ArticleChannel()
                                article_channel.article = article
                                article_channel.channel_id = 2
                                article_channel.author_id = article.author_id
                                article_channel.create_by_id = 1
                                article_channel.save()

                    print str(datetime.now())+"::"+" add tag sucessed:", i['data']
                except Exception as e:
                    print "add tag error:%s" % str(e)

                    traceback.print_exc()

if __name__ == '__main__':

    print str(datetime.now())+"::"+'Start listen article_add channel'
    Task().listen_task()