# coding:utf-8
'''
Created by dengel on 16/2/22.

@author: stone

'''
import sys,os,django
import redis
import traceback
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction, connection
import sys
reload(sys)
sys.setdefaultencoding('utf8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) #manage.py的目录
os.environ['DJANGO_SETTINGS_MODULE'] = 'jcsbms.settings' #setting的目录
django.setup()

from article.models import Article, ArticleLotteries, merge_portaltags, Article_Examine, add_articlekey, \
    redis_article_post, article_add_post
from jcsbms.utils import push_article_examine_toppage
from thiredparty.models import CrazySportArticle, CrazySportAnalyst, CrazySportImportResult, \
    copy_cache_between_sorted_set
from lottery.models import Match


def crazy_article_import():
    from_datestr = (datetime.now()).strftime("%Y-%m-%d 00:00:00")
    from_date = timezone.make_aware(datetime.strptime(from_datestr,"%Y-%m-%d %H:%M:%S"))
    #查找过去1天内，尚未被录入的疯狂体育文章
    crazy_articles = CrazySportArticle.objects.filter(crazysportimportresult__isnull=True)
    # crazy_articles = crazy_articles.filter(create_time2__gte=from_date)
    crazy_articles = crazy_articles.order_by('article_id')
    # print crazy_articles.query
    for crazy_article in crazy_articles:
        try:
            jcs_article = Article()

            #查找对应的精彩说老师和价格
            expect_id = crazy_article.expect_id
            jcs_analyst_info = CrazySportAnalyst.ANALYST_LIST.get(expect_id)
            if not jcs_analyst_info:
                print u'文章%s无法找到对应的精彩说老师信息' % expect_id
                CrazySportImportResult.objects.create(crazy_article=crazy_article, jcs_article_id=0)
                continue

            publish_time = timezone.make_aware(datetime.strptime(str(crazy_article.publish_time), "%Y-%m-%d %H:%M:%S"))
            if publish_time < from_date :
                print u'文章%s日期过久，不作处理' % expect_id
                CrazySportImportResult.objects.create(crazy_article=crazy_article, jcs_article_id=0)
                continue

            print crazy_article.article_id, crazy_article.summary, jcs_analyst_info.get('jcs_analyst_id')

            jcs_article.author_id = jcs_analyst_info.get('jcs_analyst_id')
            # jcs_article.author_id = 15
            jcs_article.price = jcs_analyst_info.get('price')
            digest = crazy_article.summary
            jcs_article.chargeable = True
            jcs_article.language = 'M'
            #默认不上首页
            jcs_article.is_toppage = False

            #标签按照竞彩的来，1：21,2:18,3：19
            portal_ids = [CrazySportArticle.LOTTERY_MAPPING[crazy_article.lottery_type]]
            # portal_ids = [1]

            text = crazy_article.content or u''
            matches = set()
            match_text = set()
            crazy_matchs = crazy_article.crazysportmatch_set.all()

            for crazy_match in crazy_matchs:
                match_text.add(u'%s %s %s VS %s' %( crazy_match.league_name,crazy_match.match_num,
                                                   crazy_match.home_name, crazy_match.guest_name))

                text = u'''%s <p>%s %s %s VS %s</p>
    <p>玩法：%s</p>
    <p>推荐内容：%s</p>
    <p>推荐结果：%s</p>
    <p>赔率：%s</p>
    ''' % ( text, crazy_match.league_name, crazy_match.match_num, crazy_match.home_name,
                  crazy_match.guest_name, crazy_match.play_type or u'',crazy_match.match_content or u'',
                 crazy_match.match_result or u'',crazy_match.sp or u'')

                match_date = datetime.strptime(crazy_match.match_time[0:10], "%Y-%m-%d").date()

                #尝试去自动匹配赛事
                jcs_match = Match.objects.filter(start_time__year= match_date.year,
                                                 start_time__month=match_date.month,
                                                 start_time__day=match_date.day,
                                                 match_id=crazy_match.match_num,
                                                 project='M')
                for m in jcs_match:
                    matches.add(m)

            for single_match_text in match_text:
                digest = digest + u'<br>' + single_match_text
            jcs_article.digest = digest[0:100]
            jcs_article.text = text

            print u'摘要：', jcs_article.digest, len(matches)

            match_list = [m.getDictForCache() for m in matches]
            #开始事务
            with transaction.atomic():
                #保存文章
                jcs_article.save()

                #把文章存到已导入表
                CrazySportImportResult.objects.create(crazy_article = crazy_article, jcs_article = jcs_article)

                #加文章赛事关联
                for match in matches:
                    ArticleLotteries.objects.create(lottery=match.lottery_entry, article=jcs_article)
                #加文章和portal以及加缓存
                merge_portaltags(portal_ids, jcs_article, match_list)

                add_articlekey(jcs_article)
                # 增加文章缓存
                redis_article_post(jcs_article, match_list)

                #转存缓存数据到疯狂直播老师专用文章列表中
                # copy_cache_between_sorted_set(jcs_article.id, 'all_article', 'zhibo_article_list')

            # 往消息队列扔消息
            if Article.objects.filter(id=jcs_article.id).count() == 1:
                article_add_post(jcs_article)

            print u'编号%s的文章已经导入到精彩说%s' % (crazy_article.article_id, jcs_article.id)

            # #加首页审核通知，放到事务以外
            # article_examine = Article_Examine()
            # article_examine.article_id = jcs_article.id
            # article_examine.status = '10'  # 待审核
            # article_examine.save()
            # # 手机推送提醒
            # push_article_examine_toppage(jcs_article)

        except Exception as e:
            traceback.print_exc()
            print u'编号%s的文章导入错误:%s' % (crazy_article.article_id, e.message)

if __name__ == '__main__':

    if len(sys.argv) == 1:
        print '定时任务启动'
        scheduler = BlockingScheduler()
        scheduler.add_job(crazy_article_import, 'interval', minutes=10)

        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
    else:
        print '单次任务启动'
        crazy_article_import()
