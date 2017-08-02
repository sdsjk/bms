# coding:utf-8

from django.db import models
from django.utils.html import strip_tags
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django_redis import get_redis_connection
from article.models import Article

from datetime import date, datetime

class CrazySportAnalyst(models.Model):
    #565 - 574
    ANALYST_LIST = {
        '148923676': {
            'jcs_analyst_id': 565,
            'price': 108
        },
        '150633485': {
            'jcs_analyst_id': 566,
            'price': 108
        },
        '150386188': {
            'jcs_analyst_id': 567,
            'price': 88
        },
        '150302920': {
            'jcs_analyst_id': 568,
            'price': 88
        },
        '150258166': {
            'jcs_analyst_id': 569,
            'price': 58
        },
        '150276627': {
            'jcs_analyst_id': 570,
            'price': 58
        },
        '150373612': {
            'jcs_analyst_id': 571,
            'price': 58
        },
        '150343258': {
            'jcs_analyst_id': 572,
            'price': 58
        },
        '150627360': {
            'jcs_analyst_id': 573,
            'price': 58
        },
        '150449182': {
            'jcs_analyst_id': 574,
            'price': 58
        },

    }

    expert_name = models.CharField(primary_key=True, max_length=100) #讲师编号
    head_portrait = models.CharField(max_length=255) #讲师头像
    introduction = models.CharField(max_length=255) #讲师介绍
    expert_nick_name = models.CharField(max_length=255) #讲师中文昵称
    create_time = models.DateTimeField()

    def __unicode__(self):
        return "%s" % self.expert_nick_name

    class Meta:
        db_table = 'crazy_sport_analyst'

class CrazySportArticle(models.Model):

    LOTTERY_MAPPING = {
        u'1': 21,
        u'2': 18,
        u'3': 19,
    }
    article_id = models.IntegerField(primary_key=True) #文章id
    content = models.CharField(max_length=1000)
    create_time2 = models.DateTimeField() #导入时间
    close_status = models.CharField(max_length=255) #方案状态 1 在售 3 已截止
    summary = models.CharField(max_length=255) #摘要
    publish_time = models.CharField(max_length=40) #疯直播的文章发布时间
    price = models.FloatField() #价格
    is_free = models.CharField(max_length= 10) #是否免费 0 否， 1 是
    expect = models.ForeignKey(CrazySportAnalyst, to_field='expert_name', db_column='expert_name')
    lottery_type = models.CharField(max_length=255)  #'彩种1、竞足单关；2、竞足二串一；3、竞篮单关';
    expert_nick_name = models.CharField(max_length=255) #'专家昵称';
    head_portrait = models.CharField(max_length=255) #'专家头像';

    class Meta:
        db_table = 'crazy_sport_article'

class CrazySportMatch(models.Model):

    create_time = models.DateTimeField()
    article = models.ForeignKey(CrazySportArticle, to_field='article_id', db_column='crazy_sport_article_id')
    league_name = models.CharField(max_length=255) #'联赛名';
    home_name = models.CharField(max_length=255) #'主队名';
    guest_name = models.CharField(max_length=255)  #客队名
    match_time = models.CharField(max_length=255) #比赛时间
    match_num = models.CharField(max_length=255) #比赛编号
    sp = models.CharField(max_length=255) #赔率
    match_result = models.CharField(max_length=255) #推荐结果
    match_content = models.CharField(max_length=255) #推荐内容
    play_type = models.CharField(max_length=255) #玩法
    expert_nick_name  = models.CharField(max_length=255) #专家昵称

    class Meta:
        db_table = 'crazy_sport_match'

class CrazySportImportResult(models.Model):

    crazy_article = models.OneToOneField(CrazySportArticle, to_field='article_id', )
    jcs_article = models.OneToOneField(Article)

    class Meta:
        db_table = 'crazy_sport_import_result'

#转存缓存数据到疯狂直播老师专用文章列表中
def copy_cache_between_sorted_set(score, from_name, to_name):
    con = get_redis_connection("default")

    item_set_json = con.zrangebyscore(from_name, score, score)
    if len(item_set_json) > 0:
        con.zremrangebyscore(to_name, score, score)
        con.zadd(to_name, score, item_set_json[0])
