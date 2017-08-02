# coding:utf-8
'''
Created by dengel on 16/2/26.

@author: stone

'''

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

from article.models import Article
from datetime import datetime,timedelta
from django.utils import timezone
import requests
import json






def push_link():
    now = timezone.now()
    yesterday = now - timedelta(days=1)
    #yyesterday = yesterday - timedelta(days=1)
    articles = Article.objects.filter(date_added__gte=yesterday)
    i =0
    for article in articles:
        i =i+1
        url = "http://www.jingcaishuo.com/wenzhang/fenxiang/?key="+article.sign_key

        r = requests.post(url="http://data.zz.baidu.com/urls?site=www.jingcaishuo.com&token=Pj1KqjquwCquzRvF",data=url)
        remain = int(json.loads(r.text)["remain"])
        if remain <=0:
            break
    print("remain:"+str(remain))
    print("succssed:"+str(i))





if __name__ == '__main__':

    print str(datetime.now())+"::"+'Start push article'
    push_link()