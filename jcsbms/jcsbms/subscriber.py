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
from jcsbms.utils import push_article, sysMonitorSMS, push_article_new_ios, push_article_from_service, \
    push_article_from_service_qiumi, push_article_from_service_yiqiying
from article.models import Article
from jcs.models import PushTaskResult, get_system_config
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
                    push_tasks = push_article_from_service(article)
                    for push_task in push_tasks:
                        pushtaskresult = PushTaskResult()
                        pushtaskresult.push_article_id = push_task['article_id']
                        pushtaskresult.user_id = push_task['user_id']
                        pushtaskresult.token = push_task['token']
                        pushtaskresult.push_type = push_task['push_type']
                        pushtaskresult.author_id = push_task['author_id']
                        pushtaskresult.save()
                    #不成功直接抛异常,无需检查返回码
                        try:
                            push_article(article)
                            push_article_new_ios(article)
                        except Exception as e:
                            pass
                    # elif article.language == u'C':
                    print str(datetime.now())+"::"+"push sucessed:", i['data']
                except Exception as e:
                    print "push error:%s" % str(e)
                    if 'cannot find user by this audience' not in str(e):
                        sysMonitorSMS(ALARM_CELLPHONES, errorMsg=str(e))
                    traceback.print_exc()

if __name__ == '__main__':

    print str(datetime.now())+"::"+'Start listen article_add channel'
    Task().listen_task()