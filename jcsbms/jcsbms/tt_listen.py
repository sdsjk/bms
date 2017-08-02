# coding:utf-8
import json
import sys,os,django
import redis
import traceback
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) #manage.py的目录
#sys.path.append("/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages")
os.environ['DJANGO_SETTINGS_MODULE'] = 'jcsbms.settings' #setting的目录
django.setup()
from mobileapp.models import Portal
from django.forms import model_to_dict
from article.models import Article
from lottery.models import Match
from analyst.models import Analyst, AnalystPriceRange, AnalystChannelRelation
from datetime import datetime
from settings import REDIS_HOST, REDIS_PASSOWRD
from jcsbms.utils import DatetimeJsonEncoder
from jcs.models import get_system_config


class Task(object):
    def __init__(self):
        self.rcon = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0, password=REDIS_PASSOWRD)
        self.ps = self.rcon.pubsub()
        self.ps.subscribe('article_add','article_del','match_add','portal_add','analyst_add') #'match_put','match_del'

    def listen_task(self):


        for i in self.ps.listen():
            print str(i)
            if i['type'] == 'message' and i['channel'] == 'article_add':
                try:
                    print str(datetime.now())+"::"+"article_add Task get", i['data']
                    article = Article.objects.get(id=i['data'])
                    tt_push_analyst_ids = get_system_config('TT_PUSH_ANALYST_IDS')
                    can_push_analyst = str(article.author_id) in tt_push_analyst_ids.split(',')
                    if can_push_analyst:
                        url = "http://bms.tuisaishi.com/restapi/article/"
                        data = model_to_dict(article) #将obj转化为dict
                        headers = {"Content-Type":"application/json"}
                        result = requests.post(url=url, headers=headers, data=json.dumps(data, default=DatetimeJsonEncoder))
                        print str(datetime.now())+"::"+" add TT article ", i['data'], result.status_code
                    else:
                        print "This author don't push"
                except Exception as e:
                    print "add TT article error:%s" % str(e)
                    traceback.print_exc()

            if i['type'] == 'message' and i['channel'] == 'article_del':
                try:
                    print str(datetime.now()) + "::" + "article_del Task get", i['data']
                    article = Article.objects.get(id=i['data'])
                    url = "http://bms.tuisaishi.com/restapi/article/%d" % article.id
                    data = model_to_dict(article)  # 将obj转化为dict
                    headers = {"Content-Type": "application/json"}
                    result = requests.delete(url=url, headers=headers, data=json.dumps(data, default=DatetimeJsonEncoder))
                    print str(datetime.now()) + "::" + " del TT article ", i['data'], result.status_code
                except Exception as e:
                    print "del TT article error:%s" % str(e)
                    traceback.print_exc()

            if i['type'] == 'message' and i['channel'] == 'match_add':
                try:
                    print str(datetime.now()) + "::" + "match_add Task get", i['data']
                    match = Match.objects.get(id=i['data'])
                    print match.start_time
                    url = "http://bms.tuisaishi.com/restapi/match/"
                    data = model_to_dict(match)  # 将obj转化为dict
                    headers = {"Content-Type": "application/json"}
                    result = requests.post(url=url, headers=headers, data=json.dumps(data, default=DatetimeJsonEncoder))# data中有datatime类型元素
                    print str(datetime.now()) + "::" + " add TT match ", i['data'], result.status_code
                except Exception as e:
                    print "add TT match error:%s" % str(e)
                    traceback.print_exc()

            if i['type'] == 'message' and i['channel'] == 'match_put':
                try:
                    print str(datetime.now()) + "::" + "match_put Task get", i['data']
                    match = Match.objects.get(id=i['data'])
                    url = "http://bms.tuisaishi.com/restapi/match/%d" % match.id
                    data = model_to_dict(match)  # 将obj转化为dict
                    headers = {"Content-Type": "application/json"}
                    result = requests.put(url=url, headers=headers, data=json.dumps(data, default=DatetimeJsonEncoder))
                    print str(datetime.now()) + "::" + " put TT match ", i['data'], result.status_code
                except Exception as e:
                    print "put TT match error:%s" % str(e)
                    traceback.print_exc()

            if i['type'] == 'message' and i['channel'] == 'match_del':
                try:
                    print str(datetime.now()) + "::" + "match_del Task get", i['data']
                    match = Match.objects.get(id=i['data'])
                    url = "http://bms.tuisaishi.com/restapi/match/%d" % match.id
                    result = requests.delete(url=url)
                    print str(datetime.now()) + "::" + " del TT match ", i['data'], result.status_code
                except Exception as e:
                    print "del TT match error:%s" % str(e)
                    traceback.print_exc()

            if i['type'] == 'message' and i['channel'] == 'portal_add':
                try:
                    print str(datetime.now()) + "::" + "portal_add Task get", i['data']
                    portal = Portal.objects.get(id=i['data'])
                    url = "http://bms.tuisaishi.com/restapi/portal/"
                    data = model_to_dict(portal)  # 将obj转化为dict
                    headers = {"Content-Type": "application/json"}
                    result = requests.post(url=url, headers=headers, data=json.dumps(data, default=DatetimeJsonEncoder))
                    print str(datetime.now()) + "::" + " add TT portal ", i['data'], result.status_code
                except Exception as e:
                    print "add TT portal error:%s" % str(e)
                    traceback.print_exc()

            if i['type'] == 'message' and i['channel'] == 'analyst_add':
                try:
                    print str(datetime.now()) + "::" + "analyst_add Task get", i['data']
                    analyst = Analyst.objects.get(id=i['data'])
                    url = "http://bms.tuisaishi.com/restapi/analyst/"
                    data = model_to_dict(analyst)  # 将obj转化为dict
                    data['username'] = analyst.user.username
                    data['email'] = analyst.user.email

                    if AnalystPriceRange.objects.filter(analyst_id=analyst.id).count() > 0:
                        analystpricerange = AnalystPriceRange.objects.get(analyst_id=analyst.id)
                        data['low_price'] = analystpricerange.low_price
                        data['high_price'] = analystpricerange.high_price
                        data['default_price'] = analystpricerange.default_price
                        data['price_status'] = analystpricerange.status
                        data['price_op_id'] = analystpricerange.op_id

                    if AnalystChannelRelation.objects.filter(analyst_id=analyst.id).count() > 0:
                        analystchannelrelation = AnalystChannelRelation.objects.get(analyst_id=analyst.id)
                        data['channel_id'] = analystchannelrelation.channel_id
                        data['channel_status'] = analystchannelrelation.status
                        data['channel_price_op_id'] = analystchannelrelation.op_id

                    headers = {"Content-Type": "application/json"}
                    result = requests.post(url=url, headers=headers, json=data)
                    print str(datetime.now()) + "::" + " add TT analyst ", i['data'], result.status_code
                except Exception as e:
                    print "add TT analyst error:%s" % str(e)
                    traceback.print_exc()

if __name__ == '__main__':

    print str(datetime.now())+"::"+'start listen'
    Task().listen_task()
