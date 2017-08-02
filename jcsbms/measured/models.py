# coding:utf-8

from django.db import models
from django.utils.html import strip_tags
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django_redis import get_redis_connection

from analyst.models import Analyst
from article.models import Article
from mobileapp.models import AppUser

from datetime import date, datetime

class MeasuredActivity(models.Model):

    activity_name = models.CharField(max_length=255, verbose_name ='活动名称')
    def __unicode__(self):
        return self.activity_name

    class Meta:
        managed = True
        db_table = "measured_activity"
        verbose_name = '活动'

class MeasuredActivityAnalyst(models.Model):

    activity = models.ForeignKey(MeasuredActivity, verbose_name ='活动')
    analyst = models.ForeignKey(Analyst, verbose_name ='老师')
    class Meta:
        managed = True
        db_table = "measured_activity_analyst"
        verbose_name = '活动和老师关联'



class MeasuredActivityArticle(models.Model):

    activity = models.ForeignKey(MeasuredActivity, verbose_name ='活动')
    article = models.ForeignKey(Article, verbose_name ='文章ID')

    class Meta:
        managed = True
        db_table = "measured_activity_article"
        verbose_name = '活动和文章关联'


class MeasuredCard(models.Model):

    type = models.IntegerField(default=1)
    name = models.CharField(max_length=120, verbose_name ='产品名称')
    valid_days = models.IntegerField(default=0)
    price = models.IntegerField(default=1)
    once_fee = models.IntegerField(default=1)
    max_times = models.IntegerField(default=1)
    max_cards_per_one = models.IntegerField(default=1)
    day_max_times = models.IntegerField(default=1)
    price_range_max = models.IntegerField(default=10)
    price_range_min = models.IntegerField(default=1)
    usable = models.BooleanField(default=True)
    status = models.IntegerField(default=0)
    max_releases  = models.IntegerField(default=0)
    user_instruction  = models.CharField(default='', max_length=2000)
    author_instruction =  models.CharField(default='', max_length=2000)

    def __unicode__(self):
        return self.name

    class Meta:
        managed = True
        db_table = "measured_card"
        verbose_name = '产品'


@receiver(post_save, sender = MeasuredCard)
def delete_card_self_cache(sender, instance, **kwargs):
    """添加删除cardredis缓存的操作，缓存名称是mcard.{card.id}"""
    con = get_redis_connection("default")
    con.delete("mcard."+str(instance.id))

class MeasuredCardRules(models.Model):

    card = models.ForeignKey(MeasuredCard, db_column='measured_card_id', verbose_name='产品名称')
    rule_key = models.CharField(max_length=120, verbose_name ='规则名称',
                                choices=[('cup','杯赛'),
                                         ( 'white','白名单'),
                                         ( 'black','黑名单'),
                                         ('lottery','彩种'),
                                         ('team', '球队')],)
    rule_value = models.CharField(max_length=2000, verbose_name ='规则内容')

    class Meta:
        managed = True
        db_table = "measured_card_rules"
        verbose_name = '产品使用规则'

@receiver([post_save, pre_delete], sender = MeasuredCardRules)
def delete_card_cache(sender, instance, **kwargs):
    """添加删除cardredis缓存的操作，缓存名称是mcard.{card.id}"""
    con = get_redis_connection("default")
    con.delete("mcard."+str(instance.card.id))


class MeasuredCardActivity(models.Model):
    card = models.ForeignKey(MeasuredCard, verbose_name ='产品')
    activity = models.ForeignKey(MeasuredActivity, verbose_name ='活动')
    class Meta:
        managed = True
        db_table = "measured_card_activity"
        verbose_name = '产品和活动关联'


class MeasuredCardSale(models.Model):
    EXPIRE_DATE = date(2017, 5, 31)
    user = models.ForeignKey(AppUser, verbose_name ='购买用户', db_column = 'userid')
    card = models.ForeignKey(MeasuredCard, verbose_name ='产品', db_column='cardid')
    start_time = models.DateField(auto_now_add=True, verbose_name ='生效时间', editable = False)
    end_time = models.DateField(verbose_name ='过期时间', default=EXPIRE_DATE, editable=False)
    remains = models.IntegerField(verbose_name ='剩余数量', default = 9999, editable= False)
    usable = models.BooleanField(default=True, verbose_name ='是否有效', editable = False)
    cdate = models.DateField(auto_now_add=True, verbose_name ='购买时间', editable = False)


    class Meta:
        managed = True
        db_table = "measured_card_sale"
        verbose_name = '用户购买产品记录'
