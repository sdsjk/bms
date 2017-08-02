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

from jcs.models import Letter
from jcsbms.utils import sendJMessage, sendJMessageCantonese
from datetime import datetime
from settings import ALARM_CELLPHONES, REDIS_HOST, REDIS_PASSOWRD



class Task(object):
    def __init__(self):
        self.rcon = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0, password=REDIS_PASSOWRD)
        self.ps = self.rcon.pubsub()
        self.ps.subscribe('send_letter_topic')

    def listen_task(self):
        for i in self.ps.listen():
            #print(str(i))
            if i['type'] == 'message':
                try:
                    print str(datetime.now())+"::"+"Task get", i['data']
                    letter = Letter.objects.get(id=i['data'])
                    if letter.project == 'M':
                        ret = sendJMessage(letter.to_auser_id, letter.to_analyst_id, letter.to_analyst.nick_name, letter.content)
                        if ret.err != 0:
                            print("send jmessage error %s", ret)
                    else:
                        ret = sendJMessageCantonese(letter.to_auser_id, letter.to_analyst_id, letter.to_analyst.nick_name, letter.content)
                        if ret.err != 0:
                            print("send jmessage to Cantonese error %s", ret)
                    print str(datetime.now())+"::"+"push sucessed:", i['data']
                except Exception as e:
                    print "push error:%s" % str(e)
                    # if 'cannot find user by this audience' not in str(e):
                    #     sysMonitorSMS(ALARM_CELLPHONES, errorMsg=str(e))
                    traceback.print_exc()

if __name__ == '__main__':

    print str(datetime.now())+"::"+'Start listen send_letter_topic channel'
    Task().listen_task()