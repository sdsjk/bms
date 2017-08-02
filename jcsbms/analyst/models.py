# coding:utf-8
'''
Created on 2015-11-17

@author: stone
'''

from django.db import models
from django.contrib.auth.models import User
from django_redis import get_redis_connection

from lottery.models import Lotterytype
from ask.models import AnswerLevel

class AnalystGroup(models.Model):
    level_number = models.SmallIntegerField(unique=True)
    name = models.CharField(max_length=16)
    #article_cost = models.SmallIntegerField(default=0)
    liveprices = models.ManyToManyField("LivePriceplan", through="GroupLivePrices",through_fields=('analyst_group', 'live_price'))
    def __unicode__(self):
        return self.name

class LivePriceplan(models.Model):
    days = models.SmallIntegerField()
    cost = models.SmallIntegerField()
    period_name =models.CharField(max_length=16,null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now = True)

    def __unicode__(self):
        return str(self.days)

    class Meta:
        unique_together = ("days", "cost")

class GroupLivePrices(models.Model):
    analyst_group = models.ForeignKey(AnalystGroup)
    live_price = models.ForeignKey(LivePriceplan)
    date_added = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("analyst_group", "live_price")

class Analystlevel(models.Model):
    level_number = models.SmallIntegerField(unique=True)
    name = models.CharField(max_length=16)

    def __unicode__(self):
        return self.name


class Priceplan(models.Model):
    lottery_type = models.ForeignKey(Lotterytype)
    analyst_level = models.ForeignKey(Analystlevel)
    cost = models.SmallIntegerField()

    class Meta:
        unique_together = ("lottery_type", "analyst_level")

    def __unicode__(self):
        return u"%s %s老师 %d元" % (self.lottery_type.name, self.analyst_level.name, self.cost)


class Analyst(models.Model):

    ANALYST_TYPE_CHARGE    = 0  #邀请的收费分析师
    ANALYST_TYPE_FREE      = 1  #邀请来的免费分析师
    ANALYST_TYPE_CRAWL     = 2  #爬来的分析师

    #老师信息
    user = models.OneToOneField(User)
    analyst_type = models.SmallIntegerField()
    nick_name = models.CharField(max_length=16,unique=True)
    brief = models.CharField(max_length=160)
    lottery_type = models.ForeignKey(Lotterytype)
    level = models.ForeignKey(Analystlevel,null=True)
    invisible = models.BooleanField(default=False)

    answer_level = models.ForeignKey(AnswerLevel,null=True,blank=True)

    analyst_group = models.ForeignKey(AnalystGroup, default=1)

    #爬取信息
    author_name = models.CharField(max_length=16,unique=True,null=True,editable=False)

    #财务信息
    real_name   = models.CharField(max_length=4,null=True)
    id_number   = models.CharField(max_length=20,null=True)
    bank_branch = models.CharField(max_length=200,null=True)
    card_number = models.CharField(max_length=32,null=True)

    #联系信息:
    weichat = models.CharField(max_length=32,null=True)
    mobile = models.CharField(max_length=11,null=True)
    address = models.CharField(max_length=100,null=True)
    post_code = models.CharField(max_length=6,null=True)

    #惩罚信息
    ban_free = models.BooleanField(default=False)
    banfree_time = models.DateTimeField(null=True)
    ban_chargeable = models.BooleanField(default=False)
    banchargeable_time = models.DateTimeField(null=True)
    ban_free_cantonese = models.BooleanField(default=False)
    banfree_time_cantonese = models.DateTimeField(null=True)
    ban_chargeable_cantonese = models.BooleanField(default=False)
    banchargeable_time_cantonese = models.DateTimeField(null=True)
    ban_letter = models.BooleanField(default=False)
    banletter_time = models.DateTimeField(null=True)

    #时间信息
    date_added = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now = True)

    #语言信息
    is_cantonese_perm = models.BooleanField(default=False)
    is_mandarin_perm = models.BooleanField(default=True)

    #订阅者
    followers = models.ManyToManyField("mobileapp.AppUser", related_name="followers" , through="mobileapp.Follow", through_fields=('author', 'user'))
    banned_lettors = models.ManyToManyField("mobileapp.AppUser", through="jcs.BannedLettor", through_fields=('analyst', 'auser'))
    def __unicode__(self):
        return self.nick_name


class Analystreflect(models.Model):
    teacher_jcs_id=models.IntegerField()
    teacher_thai_id=models.IntegerField()
    portal_jcs_id=models.IntegerField()
    portal_thai_id=models.IntegerField()

class Apply(models.Model):
    STATUS_UNHANDLED = 0
    STATUS_HANDLED   = 1

    real_name = models.CharField(max_length=4)
    email   = models.EmailField(max_length=100,null=True)
    weichat = models.CharField(max_length=32,null=True)
    mobile  = models.CharField(max_length=11)
    skill   = models.CharField(max_length=100)
    brief   = models.CharField(max_length=320)


    handle_status  = models.SmallIntegerField(default=STATUS_UNHANDLED)
    handle_result  = models.CharField(max_length=120,null=True)

    date_added    = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now = True)

def analyst_post(analyst):
    con = get_redis_connection("default")
    con.publish("author_info_changed", str(analyst.id))

class AnalystNewPassword(models.Model):

    analyst_id = models.IntegerField()
    analyst_name = models.CharField(max_length=30)
    password = models.CharField(max_length=32)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analyst_new_password"

class AnalystChannel(models.Model):
    channel_name = models.CharField(max_length=30, unique=True)
    type = models.SmallIntegerField(null=False, default=0)
    status = models.SmallIntegerField(null=False, default=0)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    op_id = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.channel_name

    class Meta:
        db_table = 'analyst_channel'

class AnalystChannelRelation(models.Model):
    VALID_STATUS = 0
    INVALID_STATUS = -1

    analyst_id = models.IntegerField()
    channel_id = models.IntegerField()
    type = models.SmallIntegerField()
    status = models.SmallIntegerField(null=False, default=0)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    op_id = models.IntegerField()

    class Meta:
        db_table = 'analyst_channel_relation'

class AnalystPriceRange(models.Model):
    VALID_STATUS = 0
    INVALID_STATUS = -1

    analyst = models.ForeignKey(to=Analyst)
    low_price = models.SmallIntegerField()
    high_price = models.SmallIntegerField()
    default_price = models.SmallIntegerField()
    type = models.SmallIntegerField()
    status = models.SmallIntegerField(null=False, default=VALID_STATUS)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    op_id = models.IntegerField()

    class Meta:
        db_table = 'analyst_price_range'


class AnalystConfig(models.Model):

    analyst_id = models.IntegerField()
    key = models.CharField(null = False, max_length = 255)
    value = models.CharField(max_length= 255)

    class Meta:
        db_table = 'analyst_config'