# coding:utf-8
'''
Created on 2015-11-10

@author: stone
'''
from datetime import timedelta, datetime

from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from mongoengine import StringField,ObjectIdField,FloatField,URLField,BooleanField,Document
from pyquery import PyQuery
import json

from django.db import models
from django.db import transaction
from django.utils import timezone
from django.utils.html import strip_tags
from django.core.signing import Signer
from django.contrib.auth.models import Group


from analyst.models import Analyst,Analystlevel, AnalystConfig
from jauth.models import create_psUser
from jcsbms.settings import TENNIS_ID
from lottery.models import Lotterytype,Lotteryentry
from jcsbms.utils import connect_mongodb, is_xiaomishu

from django_redis import get_redis_connection



# Create your models here


class TaskResult(Document):
    connect_mongodb()
    id = ObjectIdField("_id")
    result = StringField()
    updatetime = FloatField()
    taskid = StringField()
    author = StringField()
    title = StringField(null=True)
    project = StringField(null=True)
    url = URLField()
    is_synced = BooleanField(null=True)
    #work_owner = userid 后期多人编辑时,可以做为任务领取字段

    meta = {
        'collection': 'all_results'
    }



class Articletimeline(models.Model):
    article_id=models.IntegerField()
    m_cdate=models.DateTimeField()
    cut_cdate=models.DateTimeField()
    cut_author=models.CharField(max_length=50)
    translate_cdate=models.DateTimeField()
    translate_author=models.CharField(max_length=50)
    teacher_id=models.IntegerField()
    teacher_thai=models.IntegerField()


class Article(models.Model):
    Porject_Origin={
        "blog163":u"网易博客",
        "cai139":u"139彩票网",
        "fivehblog":u"500彩票网",
        "fivehzucai":u"500彩票网",
        "lofter":u"网易Lofer",
        "nowscore":u"捷报比分网",
        "sinablog":u"新浪博客",
        "vipc":u"唯彩会",
        "web_17mcp":u"众彩网",
        "web_310win":u"彩客网",
        "web_8win":u"章鱼彩票",
        "web_fox008":u"精彩说编辑部",
        "web_sina":u"新浪彩票",
        "web_sporttery":u"竞彩网",
        "web_sporttery_person":u"竞彩网资讯",
        "web_win007":u"球探体育",
    }

    LANGUAGE ={
        'M': u'',
        'C': u'_cantonese',
    }

    FREE_TOPPAGE_MAX_COUNT = 4
    CHARGEABLE_TOPPAGE_MAX_COUNT = 2
    M_FREE_TOPPAGE_MAX_COUNT = 4
    M_CHARGEABLE_TOPPAGE_MAX_COUNT = 2
    C_FREE_TOPPAGE_MAX_COUNT = 4
    C_CHARGEABLE_TOPPAGE_MAX_COUNT = 2


    #收费文章自动解锁时间
    AUTO_UNLOCK_HOURS = 3

    taskid = models.CharField(null=True,max_length=32,unique=True)
    title = models.CharField(max_length=200,null=True)
    text = models.TextField()
    digest = models.CharField(max_length=300,null=True)
    author = models.ForeignKey(Analyst)
    lotteries = models.ManyToManyField(Lotteryentry,through='ArticleLotteries',through_fields=('article', 'lottery'))
    portal_tags = models.ManyToManyField("mobileapp.Portal", through='ArticlePortalTags', through_fields=('article', 'portal'))

    chargeable = models.BooleanField(default=False)
    end_time = models.DateTimeField(null=True)

    istop = models.BooleanField(default=False)
    is_toppage = models.BooleanField(default=False)
    top_time = models.DateTimeField(null=True)
    origin = models.CharField(max_length=32,null=True)

    sign_key =models.CharField(max_length=32,default="")

    invisible = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    price = models.IntegerField(null=True)

    top_order = models.SmallIntegerField(null=False, default=1)

    language = models.CharField(null=False, default='M', max_length=16)
    sport_type = models.CharField(max_length=1)
    type = models.CharField(max_length=5)
    status=models.IntegerField()
    digest_origin=models.CharField(max_length=10240)
    text_origin=models.CharField(max_length=10240)
    digest_edit = models.CharField(max_length=10240)
    text_edit = models.CharField(max_length=10240)

    def toppage_check(self):
        if is_xiaomishu(self.author.user_id):
            return True
        today = timezone.localtime(self.date_added).strftime("%Y-%m-%d")
        today0hour = datetime.strptime(today + " 00:00:00", "%Y-%m-%d %H:%M:%S")
        today24hour = today0hour+timedelta(hours=24)
        today0hour = timezone.make_aware(today0hour)
        today24hour = timezone.make_aware(today24hour)

        analyst_configs = AnalystConfig.objects.filter(analyst_id=self.author.id)
        configMap = {}
        for config in analyst_configs:
            configMap[config.key] = config.value

        m_top_page_charge_max = int(configMap.get('m_top_page_charge_max', Article.M_CHARGEABLE_TOPPAGE_MAX_COUNT))
        m_top_page_free_max = int(configMap.get('m_top_page_free_max', Article.M_FREE_TOPPAGE_MAX_COUNT))
        c_top_page_charge_max = int(configMap.get('c_top_page_charge_max', Article.C_CHARGEABLE_TOPPAGE_MAX_COUNT))
        c_top_page_free_max = int(configMap.get('c_top_page_free_max', Article.C_FREE_TOPPAGE_MAX_COUNT))

        if self.language == u'M':
            max_charge_count = m_top_page_charge_max
            max_free_count = m_top_page_free_max
        else:
            max_charge_count = c_top_page_charge_max
            max_free_count = c_top_page_free_max

        if self.chargeable:
            if Article.objects.filter(author=self.author, chargeable=self.chargeable, date_added__gte=today0hour,is_toppage=True,
                                      date_added__lt=today24hour, language = self.language).exclude(id=self.id).count() >= max_charge_count:
                return False
        else:

            if Article.objects.filter(author=self.author, chargeable=self.chargeable,is_toppage=True,
                                      date_added__gte=today0hour, date_added__lt=today24hour, language = self.language).exclude(id=self.id).count() >= max_free_count:
                return False

        return True


class ArticleLotteries(models.Model):
    article= models.ForeignKey(Article)
    lottery = models.ForeignKey(Lotteryentry)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("article", "lottery")


class Articlethai(models.Model):
    id=models.IntegerField
    digest_untanslate=models.CharField(max_length=300,null=True)
    text_untranslate=models.TextField(max_length=1000000)

class ArticlePortalTags(models.Model):
    article = models.ForeignKey(Article)
    portal = models.ForeignKey("mobileapp.Portal")
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("article", "portal")



def make_endtime(article):

    end_time = None
    lotto_type = Lotterytype.objects.get(name =u"数字彩")
    match_type = Lotterytype.objects.get(name =u"竞技彩")
    #endtime设为文章关联的彩票的最晚时间
    for lotto in article.lotteries.all():
        if lotto.type.parent.id == lotto_type.id:
            new_time = lotto.lotto.end_time
        elif lotto.type.parent.id == match_type.id:
            new_time = lotto.match.start_time
        if end_time == None or new_time > end_time:
            end_time = new_time
    #判断文章中是否含有网球标签
    unlock_hour = article.AUTO_UNLOCK_HOURS
    for portal_tags_id in article.portal_tags.all().values_list('id'):
        if TENNIS_ID in portal_tags_id:
            unlock_hour = 12

    if end_time != None:
        #避免加时赛
        article.end_time = end_time+timedelta(hours=unlock_hour)
        #未关联比赛的收费文章24小时之后自动解锁
    elif article.chargeable == True and ArticleLotteries.objects.filter(article_id=article.id).count() == 0:
        article.end_time = timezone.now() + timedelta(hours=24)
    else:
        article.end_time = None
    article.date_added=timezone.now()
    article.save()



def merge_lotteries(lotteries,article):
    new_set = set([lottery.id for lottery in lotteries])
    old_set = set([lottery["id"] for lottery in article.lotteries.values()])

    if old_set != new_set:

        for old_id in old_set:
            if old_id not in new_set:
                lotteryentry = Lotteryentry.objects.get(id=old_id)
                ArticleLotteries.objects.get(lottery=lotteryentry,article=article).delete()
        for new_id in new_set:
            if new_id not in old_set:
                lotteryentry = Lotteryentry.objects.get(id=new_id)
                ArticleLotteries.objects.create(lottery=lotteryentry,article=article)

#refined by zhaozhi, 2016-08-04
def merge_portaltags(portal_ids,article,match_list):
    new_set = set(portal_ids)
    old_set = set([str(portal.id) for portal in article.portal_tags.all()])

    if old_set == new_set:
        return

    con = get_redis_connection("default")

    #用sorted set存portal_id => 多个文章id -> 文章的json
    for old_id in old_set:
        #清理旧缓存
        con.zremrangebyscore("portal_"+old_id, article.id, article.id)
        if old_id not in new_set:
            #清理数据库中废弃的旧关联关系
            ArticlePortalTags.objects.get(portal_id=old_id,article=article).delete()

    for new_id in new_set:
        if new_id not in old_set:
            #数据库中建立新的关联关系
            ArticlePortalTags.objects.create(portal_id=new_id,article=article)

    if len(new_set) > 0:
        article_set_object = {}

        article_set_object["id"] = article.id
        article_set_object["title"] = article.title
        article_set_object["chargeable"] = article.chargeable
        article_set_object["is_toppage"] = article.is_toppage
        if article.chargeable and article.digest != None:
            article_set_object["digest"] = article.digest
        else:
            article_set_object["digest"] = ' '.join(strip_tags(article.text)[:100].split())
        article_set_object["price"] = article.price if article.price != None else ""
        article_set_object["author_id"] = article.author.id
        article_set_object["last_modified"] = timezone.localtime(article.last_modified).strftime(
            "%Y-%m-%d %H:%M:%S")
        article_set_object["date_added"] = timezone.localtime(article.date_added).strftime("%Y-%m-%d %H:%M:%S")
        portal_list = []
        portal_dict_list = []
        portal_tags = article.portal_tags.all()
        for portal in portal_tags:
            #兼容旧缓存格式
            portal_list.append(portal.id)
            #新缓存数据
            portal_dict_list.append({"id": portal.id, "name": portal.name})
        article_set_object["portals"] = portal_list
        article_set_object["portal_list"] = portal_dict_list
        article_set_object["matches"] = match_list
        article_set_json = json.dumps(article_set_object)
        #建立新缓存
        for new_id in new_set:
            con.zadd("portal_"+str(new_id), article.id, article_set_json)


def clean_text(text):
    doc = PyQuery(text)
    doc.find("a").removeAttr("href")
    doc.find('[class]').removeAttr("class")
    doc.find('[style]').removeAttr("style")
    doc.find('img[real_src]').each(lambda i,e : PyQuery(e).attr("src",PyQuery(e).attr.real_src))
    return doc.html()

def create_psAnalyst(nick_name):
    with transaction.atomic():

        analyst = Analyst()
        analyst.analyst_type = Analyst.ANALYST_TYPE_CRAWL
        analyst.nick_name = nick_name
        analyst.author_name = nick_name
        analyst.brief=""
        analyst.lottery_type = Lotterytype.objects.all()[0]
        analyst.level = Analystlevel.objects.get(level_number=0)
        analyst.user = create_psUser()
        analyst.user.groups.add(Group.objects.get(name="Analyst"))
        analyst.save()
        return analyst



def redis_article_post(article,match_list=[]):
    con = get_redis_connection("default")
    #print(dir(con))

    make_endtime(article)

    article_cache_object = {}

    article_cache_object["id"]=article.id
    article_cache_object["title"]=article.title
    if article.end_time != None:
        article_cache_object["end_time"] = timezone.localtime(article.end_time).strftime("%Y-%m-%d %H:%M:%S")
    if article.chargeable and article.digest != None:
        article_cache_object["digest"] = article.digest
        #print article_cache_object
    else:
        article_cache_object["digest"]=' '.join(strip_tags(article.text)[:100].split())
    article_cache_object["text"]=article.text
    article_cache_object["chargeable"]=article.chargeable
    article_cache_object["is_toppage"] = article.is_toppage
    article_cache_object["sign_key"]=article.sign_key
    article_cache_object["price"]=article.price if article.price != None else ""
    article_cache_object["origin"]=article.origin
    article_cache_object["author_id"]=article.author.id
    article_cache_object["last_modified"]=timezone.localtime(article.last_modified).strftime("%Y-%m-%d %H:%M:%S")
    article_cache_object["date_added"] = timezone.localtime(article.date_added).strftime("%Y-%m-%d %H:%M:%S")

    portal_list = []
    portal_dict_list = []
    portal_tags = article.portal_tags.all()
    for portal in portal_tags:
        portal_list.append(str(portal.id))
        portal_dict_list.append({"id": portal.id, "name": portal.name})
    article_cache_object["portals"] = ",".join(portal_list)
    article_cache_object["portal_list"] = portal_dict_list
    article_cache_object["matches"] = match_list
    article_cache_object["language"] = article.language
    old_article_cache = con.get("article_"+str(article.id))
    if old_article_cache:
        old_article_cache_obj = json.loads(old_article_cache)
        article_cache_object['praiseNums'] = old_article_cache_obj.get('praiseNums', 0)
    #print(con.zremrangebyscore)
    con.setex("article_"+str(article.id),60*60*24*30,json.dumps(article_cache_object))

    article_set_object={}

    article_set_object["id"]=article.id
    article_set_object["title"]=article.title
    article_set_object["chargeable"]=article.chargeable
    article_set_object["is_toppage"] = article.is_toppage
    if article.chargeable and article.digest != None:
        article_set_object["digest"]=article.digest
    else:
        article_set_object["digest"]=' '.join(strip_tags(article.text)[:100].split())
    article_set_object["price"]=article.price if article.price != None else ""
    article_set_object["author_id"]=article.author.id
    article_set_object["last_modified"]=timezone.localtime(article.last_modified).strftime("%Y-%m-%d %H:%M:%S")
    article_set_object["date_added"] = timezone.localtime(article.date_added).strftime("%Y-%m-%d %H:%M:%S")
    portal_list = []
    for portal in portal_tags:
        portal_list.append(portal.id)
    article_set_object["portals"] = portal_list
    article_set_object["portal_list"] = portal_dict_list
    article_set_object["matches"] = match_list
    article_set_object['origin'] = article.origin

    authorset_name = "author"  + str(Article.LANGUAGE[article.language]) +  "_set_" + str(article.author.id)
    con.zremrangebyscore(authorset_name,article.id,article.id)
    article_set_json = json.dumps(article_set_object)
    con.zadd(authorset_name,article.id, article_set_json)
    allarticle_name = "all" + str(Article.LANGUAGE[article.language]) +  "_article"
    con.zremrangebyscore(allarticle_name, article.id, article.id)
    con.zadd(allarticle_name, article.id, article_set_json)

    toppageset_name = "toppage" + str(Article.LANGUAGE[article.language]) +  "_set"
    con.zremrangebyscore(toppageset_name,article.id,article.id)

    # if article.is_toppage:
    #     if not article.toppage_check():
    #         article.is_toppage = False
    #         article.save()
    if article.is_toppage:
        con.zadd(toppageset_name,article.id,article_set_json)



def redis_article_remove(article):
    con = get_redis_connection("default")

    con.delete("article_"+str(article.id))

    authorset_name = "author"  + str(Article.LANGUAGE[article.language]) +  "_set_" + str(article.author.id)
    con.zremrangebyscore(authorset_name,article.id,article.id)

    allarticle_name = "all" + str(Article.LANGUAGE[article.language]) +  "_article"
    con.zremrangebyscore(allarticle_name,article.id,article.id)

    toppageset_name = "toppage" + str(Article.LANGUAGE[article.language]) +  "_set"
    con.zremrangebyscore(toppageset_name, article.id, article.id)


    con.publish("article_remove",str(article.id))

def article_post_save(sender, **kwargs):
    if kwargs["created"]:
        article = kwargs["instance"]
        con = get_redis_connection("default")
        if article.language == u'M':
            con.publish("author_article_add", str(article.author.id))
        else:
            con.publish("c_author_article_add", str(article.author.id))
        con.publish("article_add",str(article.id))
    else:
        article = kwargs["instance"]
        con = get_redis_connection("default")
        con.publish("article_update", str(article.id))

def article_add_post(article):
    con = get_redis_connection("default")
    if article.language == u'M':
        con.publish("author_article_add", str(article.author.id))
    else:
        con.publish("c_author_article_add", str(article.author.id))
    con.publish("article_add", str(article.id))

def article_update_post(article):
    con = get_redis_connection("default")
    con.publish("article_update", str(article.id))


signer = Signer()
def add_articlekey(article):
    value = signer.sign(str(article.id))
    sign_value = value[value.find(":")+1:]
    article.sign_key = sign_value
    article.save()

@receiver(post_save,sender=ArticleLotteries)
def articlelottery_post_save(sender, **kwargs):
    if kwargs["created"]:
        articlelottery = kwargs["instance"]
        con = get_redis_connection("default")
        con.publish("articlelottery_add", str(articlelottery.article.id)+"_"+str(articlelottery.lottery.id))

@receiver(post_delete,sender=ArticleLotteries)
def articlelottery_post_del(sender, **kwargs):
        articlelottery = kwargs["instance"]
        con = get_redis_connection("default")
        con.publish("articlelottery_del", str(articlelottery.article.id)+"_"+str(articlelottery.lottery.id))

def redis_force_top(article):
    '''
    编辑强制置顶功能,直接将文章放入首页缓存,后续等待api服务再将其放入置顶缓存
    :param article_id:
    :return:
    '''
    article_id = article
    if isinstance(article, Article):
        article_id = article.id
    con = get_redis_connection("default")
    allarticle_name = "all" + str(Article.LANGUAGE[article.language]) + "_article"
    article_set_json = con.zrangebyscore(allarticle_name, article_id, article_id)
    if len(article_set_json) > 0:
        toppageset_name = "toppage" + str(Article.LANGUAGE[article.language]) + "_set"
        con.zremrangebyscore(toppageset_name, article_id, article_id)
        con.zadd(toppageset_name,article_id,article_set_json[0])

def redis_cancel_top(article):
    '''
    从缓存删除编辑强制置顶的文章,避免api服务将其又放回首页缓存
    :param article:
    :return:
    '''
    article_id = article
    if isinstance(article, Article):
        article_id = article.id
    con = get_redis_connection("default")
    toppagesetfixed_name = "toppage" + str(Article.LANGUAGE[article.language]) + "_set_fixed"
    con.zremrangebyscore(toppagesetfixed_name, article_id, article_id)

class Channel(models.Model):
    name = models.CharField(max_length=50)
    code = models.IntegerField()

    def __unicode__(self):
        return u'%s:%d' %(self.name , self.code)

    class Meta:
        managed = True
        db_table = "channel"

class ArticleChannel(models.Model):
    article = models.ForeignKey(Article)
    channel = models.ForeignKey('mobileapp.ExternalChannel', db_column='channel_id')
    author = models.ForeignKey(Analyst)
    status = models.SmallIntegerField(default=1)
    create_time = models.DateTimeField(auto_now_add=True)
    create_by_id = models.IntegerField()

    class Meta:
        managed = True
        db_table = "article_channel"

class ArticleLotteriesResult(models.Model):

    article = models.ForeignKey(Article, db_column='article_id')
    playname = models.CharField(max_length=255)
    score_prediction = models.CharField(max_length=255)
    score_practical = models.CharField(max_length=255)
    black_red_decide = models.CharField(max_length=255)
    user_id = models.IntegerField(32, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    league = models.CharField(max_length=255)
    match_name = models.CharField(max_length=255)
    match_time = models.DateTimeField()
    comment = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = "article_articlelotteries_result"

class Article_Examine(models.Model):
    article = models.OneToOneField(Article)
    examine_user_id = models.IntegerField()
    examine_time = models.DateTimeField()
    examine_opinion = models.CharField(max_length=255)
    status = models.CharField(max_length=20)

    class Meta:
        managed = True
        db_table = "article_examine"

def examine_toppage_upset(article_examine):
    con = get_redis_connection("default")
    examine_toppage_set_vaule = con.get("examine_toppage_set") or ''
    con.setex("examine_toppage_set", 60*60*24*30, examine_toppage_set_vaule + ',' + str(article_examine.article_id) + ',')  # 3个参数,键/时间/值
    con.publish('m_top_page_change', '')

def examine_toppage_downset(article_examine):
    con = get_redis_connection("default")
    examine_toppage_set_vaule = con.get("examine_toppage_set") or ''
    con.setex("examine_toppage_set", 60*60*24*30, examine_toppage_set_vaule.replace(','+str(article_examine.article_id)+',',''))
    con.publish('m_top_page_change', '')

class HongDanBaoArticle(models.Model):
    article_id = models.IntegerField()

    class Meta:
        managed = True
        db_table = "hongdanbao_article"

