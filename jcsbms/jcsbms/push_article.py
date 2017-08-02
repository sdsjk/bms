# coding:utf-8
import sys,os,django
import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) #manage.py的目录
os.environ['DJANGO_SETTINGS_MODULE'] = 'jcsbms.settings' #setting的目录
django.setup()
from lottery.models import Lotteryentry, Match
from jcsbms.utils import push_article
from apscheduler.schedulers.blocking import BlockingScheduler
from article.models import Article, redis_article_post, merge_portaltags, add_articlekey, article_add_post, \
     merge_lotteries


def myDef():
    print 'start schedule'
    articles = Article.objects.filter(id__gte=292212)
    # 不在HongDanBaoArticle表里的数据


    for article in articles:
        print article.id
        portal_ids = [p.portal_id for p in article.articleportaltags_set.all()]

        lid_list = [lottery["id"] for lottery in article.lotteries.values()]

        matches = Match.objects.filter(lottery_entry__in=lid_list)
        match_list = []
        if matches != None:
            match_list = [x.getDictForCache() for x in matches]

        #推redis
        merge_portaltags(portal_ids, article, match_list)
        add_articlekey(article)
        redis_article_post(article, match_list)
        article_add_post(article)
        #推消息提醒
        try:
            push_article(article)
        except Exception as e:
            print e



if __name__ == '__main__':
    myDef()
    # sched = BlockingScheduler()
    # sched.add_job(myDef, 'interval', seconds=10)
    # sched.start()