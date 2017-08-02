# coding:utf-8
'''
Created on 2015-11-30

@author: stone
'''
from django.db import models
from django_redis import get_redis_connection

from analyst.models import Analyst
from article.models import Article
from lottery.models import Match
import dateutil

class Order(models.Model):
    userid = models.IntegerField()
    author = models.ForeignKey(Analyst,db_column="authorid",null=True)
    product = models.ForeignKey(Article,db_column="productid",null=True)
    ordertype = models.IntegerField()
    orderstatus = models.IntegerField()
    createtime = models.DateTimeField(auto_now_add=True)
    appid = models.CharField(max_length=10)
    discountid = models.IntegerField()
    unitprice = models.IntegerField()

    class Meta:
        db_table = 'jcs_order'

class AppUser(models.Model):
    USE_TYPE_JCS = 0
    USE_TYPE_HEINIU =1

    userid = models.IntegerField(primary_key=True)
    phonenumber = models.CharField(max_length=13,unique=True,db_index=True)
    password = models.CharField(max_length=64)
    nickname = models.CharField(max_length=20,null=True)
    age = models.SmallIntegerField(null=True)
    securitykey = models.CharField(max_length=32,null=True)
    payinfo = models.SmallIntegerField()
    money = models.IntegerField()
    goldcoin = models.IntegerField()
    picpath =  models.CharField(max_length=1024)
    isactive = models.BooleanField(default=True)
    usertype = models.SmallIntegerField()
    channelname = models.CharField(max_length=100)
    client_version = models.CharField(max_length=8, db_column="clientver", null=True)
    appid = models.CharField(max_length=1,null=True)

    os = models.CharField(max_length=16)
    version = models.CharField(max_length=16)
    deviceno = models.CharField(max_length=100)
    inviter = models.ForeignKey(Analyst,db_column="inviteid",null=True)
    channel = models.IntegerField(db_column="channelid",null=True)
    cdate = models.DateTimeField(auto_now_add=True)
    udate = models.DateTimeField()

    def __unicode__(self):
        return str(self.userid)

    class Meta:
        db_table = "users"
        managed = True

'''
购买表数据定义:
CREATE TABLE PURCHASE (
     ID             SERIAL,
     USERID         INTEGER  NOT NULL,
     AUTHORID       INTEGER  NOT NULL,
     ARTICLEID      INTEGER  NOT NULL,
     PRICE          INTEGER  NOT NULL,
     STATUS         SMALLINT DEFAULT 0,
     PAYTYPE        SMALLINT,
     PAYMENTID      INTEGER,#支付表
     CDATE          timestamp
);
PAYTYPE
1:微信支付
2:支付宝支付
3:金币支付
STATUS: 0 未成功  1 成功
'''
class Purchase(models.Model):
    PAY_TYPE_WX     = 1
    PAY_TYPE_ALIPAY = 2
    PAY_TYPE_GOLD   = 3
    PAY_TYPE_MONEY  = 4

    PURCHASE_TYPE_ARTICLE = 0
    PURCHASE_TYPE_ASK     = 1
    PURCHASE_TYPE_MONTH   = 2
    PURCHASE_TYPE_VIDEO   = 3
    PURCHASE_TYPE_FLOWER   = 4

    PURCHASE_TYPE_NAMES= [u"文章",u"问答",u"服务", u"视频", u"买花"]

    PAY_TYPE_NAMES = [u"微信",u"支付宝",u"精彩币",u"支付精彩币",u"任务精彩币", u'',  u'6+支付']

    STATUS_UNSUCCESS = 0
    STATUS_SUCCESS   = 1
    STATUS_DEPOSIT = 2
    STATUS_REFUND = 3


    user = models.ForeignKey(AppUser,db_column="userid" ,db_index=True)
    author = models.ForeignKey(Analyst,db_column="authorid")
    purchasetype = models.SmallIntegerField()
    target = models.IntegerField(db_column="targetid")
    price = models.IntegerField()
    status = models.SmallIntegerField()
    paytype = models.SmallIntegerField()
    paymentid = models.IntegerField()
    cdate = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order, db_column='orderid')

    class Meta:
        db_table = "purchase"
        managed = True

'''

CREATE TABLE CHARGE (
     ID           SERIAL,
     USERID       INTEGER NOT NULL,
     MONEY        INTEGER  NOT NULL,
     GOLDCOIN     INTEGER  NOT NULL,
     BANK         VARCHAR(48),
     TYPE         SMALLINT,
     PAYMENTID    INTEGER,
     STATUS       SMALLINT DEFAULT 0,
     CDATE        timestamp
);
STATUS: 0 未成功  1 成功
TYPE
1: wx 2:zfb 3:上传头像  4: 任务  5: 分享 6:打折赠送
'''
class Charge(models.Model):
    CHARGE_TYPE_NAMES = [u"微信",u"支付宝",u"头像上传",u"每日打开",u"分享",u"注册",u"退钱",u"系统赠送", u"谷歌支付",u"苹果支付",u"网页支付"]

    user = models.ForeignKey(AppUser,db_column="userid")
    money = models.IntegerField()
    gold = models.IntegerField(db_column="goldcoin")
    bank = models.CharField(max_length=48)
    type = models.SmallIntegerField()
    status = models.SmallIntegerField()
    cdate = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order, db_column='orderid')
    paymentid = models.IntegerField()
    operator_id = models.IntegerField()
    comment = models.CharField(max_length=255)

    class Meta:
        db_table = "charge"
        managed = True

class Follow(models.Model):
    user = models.ForeignKey(AppUser,db_column="userid",db_index=True,null=True)
    author = models.ForeignKey(Analyst,db_column="authorid",db_index=True,null=True)

    class Meta:
        db_table = "follow"
        managed = True



class Recharge(models.Model):
    gold_number = models.SmallIntegerField()
    cost = models.SmallIntegerField()
'''
CREATE TABLE MONEY_CHANGE_HISTORY (
     ID             SERIAL,
     USERID         INTEGER  NOT NULL,
     ORIGMONEY      INTEGER  NOT NULL,
     OPERATOR       CHAR(1)  NOT NULL,
     CHANGEMONEY    INTEGER  NOT NULL,
     LEFTMONEY      INTEGER  NOT NULL,
     TRANSCTID      INTEGER  NOT NULL,
     CDATE          timestamp
);
'''
class MoneyChangeHistory(models.Model):
    user = models.ForeignKey(AppUser,db_column="userid")
    origmoney = models.IntegerField()
    operator = models.CharField(max_length=1)
    changemoney = models.IntegerField()
    leftmoney = models.IntegerField()
    transctid = models.IntegerField()
    cdate = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "money_change_history"
        managed = True

class Banner(models.Model):
    TARGET_TYPE_ANALYST = "analyst"
    TARGET_TYPE_ARTICLE = "article"
    TARGET_TYPE_LOTTERY = "lottery"
    TARGET_TYPE_H5 = "h5"


    is_online = models.BooleanField(default=True)
    img_url = models.CharField(max_length=120)
    target_type = models.CharField(max_length=58)
    target_id = models.IntegerField()
    date_added = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    target_url = models.CharField(default='', max_length=100, blank=True)
    project = models.CharField(max_length=32, default='M')


class Portal(models.Model):
    id=models.IntegerField
    is_online = models.BooleanField(default=True)
    can_selected = models.BooleanField(default=True)
    name = models.CharField(max_length=32)
    img_url = models.CharField(max_length=120)
    date_added = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    target_url = models.CharField(default='', max_length=100, blank=True)
    rank = models.IntegerField(default = 0)
    project = models.CharField(max_length = 32, default = 'M')
    show_user_flag = models.BooleanField(default=False)
    show_user_value = models.CharField(max_length=32, null=True, blank=True)
    show_channel_flag = models.BooleanField(default=False)
    show_channel_value = models.CharField(max_length=32, null=True, blank=True)

class BigVIP(models.Model):
    name = models.CharField(max_length=10)
    avatar = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

class LiveVedio(models.Model):
    BeiJing = 1
    ShangHai = 2
    Location_CHOICES = (
        (1, u'北京'),
        (2, u'上海'),
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    chargeable = models.BooleanField()
    url = models.CharField(max_length=200)
    #match = models.ForeignKey(Match, null=True, blank=True, default=0)
    match_id = models.IntegerField(default=None)
    location = models.SmallIntegerField(choices=Location_CHOICES, default=BeiJing)
    match_name = models.CharField(max_length=100)
    guests = models.ManyToManyField(BigVIP)
    cost = models.IntegerField(null=True, blank=True, default=0)

    def __unicode__(self):
        to_zone = dateutil.tz.tzlocal()
        local = self.start_time.astimezone(to_zone)
        return self.match_name + ": " + local.strftime("%Y-%m-%d %H:%M")

class LiveGift(models.Model):
    name = models.CharField(max_length=6)
    price = models.IntegerField()
    useable = models.BooleanField()


'''
STATUS: 0:未成功  1:成功 2:已过期

//购买服务详细表
CREATE TABLE PERIOD (
     ID             SERIAL,
     USERID         INTEGER  NOT NULL,
     AUTHORID       INTEGER  NOT NULL,
     FEETYPE        SMALLINT DEFAULT 0,
     FEE            INTEGER  NOT NULL,
     NUMS           SMALLINT DEFAULT 0,
     TOTALFEE       INTEGER  NOT NULL,
     STATUS         SMALLINT DEFAULT 0,
     USABLE         BOOLEAN,
     TRANSCTID      INTEGER  DEFAULT 0,
     STARTDATE      timestamp(0) with time zone,
     ENDDATE        timestamp(0) with time zone,
     CDATE          timestamp(0) with time zone
);
'''
class Period(models.Model):
    startdate = models.DateTimeField()
    enddate = models.DateTimeField()

    class Meta:
        db_table = "period"
        managed = True

def auser_post(auser):
    con = get_redis_connection("default")
    con.publish("user_info_changed", str(auser.userid))

def charge_add(charge):
    con = get_redis_connection("default")
    #print("charge_add publish")
    con.publish("charge_add", str(charge.id))

def auser_deactivate(auser):
    con = get_redis_connection("default")
    con.publish("auser_deactivate", str(auser.userid))

class H5_article_fixtop(models.Model):
    '''
    type_id: 表示业务类型, 自定义
    '''
    type_id = models.IntegerField(db_column="type", null=False)
    article_id = models.IntegerField(db_column="articleid", null=False)
    usable = models.BooleanField()
    cdate = models.DateField()

    def __unicode__(self):
        return u"文章:%d" % self.article_id

    class Meta:
        db_table = "h5_article_fixtop"
        managed = True

class H5_author_list(models.Model):
    author = models.ForeignKey(Analyst, db_column="authorid")
    usable = models.BooleanField()
    order_id = models.IntegerField(db_column="orderid")
    type = models.IntegerField()

    def __unicode__(self):
        return u"%s 排序:%d 类型:%d" % (self.author.nick_name, self.order_id, self.type)

    class Meta:
        db_table = "h5_author_list"
        managed = True

class Refund_red_log(models.Model):
    '''
    红单退款记录表
    '''
    STATUS_SUCCESS = 1
    STATUS_FAILED = -1

    user = models.ForeignKey(AppUser, db_column="user_id")
    article = models.ForeignKey(Article, db_column="article_id")
    goldcoin = models.IntegerField()
    status = models.SmallIntegerField()
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    op_id = models.IntegerField()

    class Meta:
        db_table = "refund_red_log"
        managed = True

class WxPayment(models.Model):
    paymentid = models.IntegerField(primary_key=True)
    orderid = models.CharField(max_length=64)
    status = models.IntegerField()
    trade_state = models.CharField(max_length=32)

    class Meta:
        db_table = "wx_payment"
        managed = True

class OmnipotenceCard(models.Model):

    id = models.AutoField(primary_key=True, db_column='card_id')
    card_img = models.CharField(max_length=1024, blank=True)
    card_name = models.CharField(max_length=200)
    card_type = models.SmallIntegerField()
    card_value = models.IntegerField()
    end_time = models.DateField()
    usable = models.BooleanField()
    status = models.IntegerField()
    ety_cd_nums = models.SmallIntegerField()
    ety_cd_keep_days = models.SmallIntegerField()
    ety_cd_valid_days = models.SmallIntegerField()
    cdate = models.DateField()
    cuser = models.IntegerField()
    udate = models.DateField()
    uuser = models.IntegerField()
    card_limit_pday = models.IntegerField()

    def __unicode__(self):
        return self.card_name

    class Meta:
        db_table = 'omnipotence_card'
        managed = True

class OmnipotenceCardIssue(models.Model):
    card = models.ForeignKey(OmnipotenceCard,db_column="card_id",null=True)

    class Meta:
        db_table = "omnipotence_card_issue"
        managed = True

class OmnipotenceCardRules(models.Model):

    card = models.ForeignKey(OmnipotenceCard)
    rule_type = models.SmallIntegerField()
    rule_key = models.CharField(max_length=120)
    rule_value = models.CharField(max_length=2000)

    class Meta:
        db_table = 'omnipotence_card_rules'
        unique_together = ('card', 'rule_type', 'rule_key')

class LetterHide(models.Model):
    userid = models.IntegerField()
    authorid = models.IntegerField()
    cdate = models.DateField(auto_now_add=True)


    class Meta:
        db_table = "letter_hide"
        managed = True

class PushChannel(models.Model):
    userid = models.IntegerField()
    type = models.IntegerField()
    token = models.CharField(max_length=128)
    cdate = models.DateTimeField(auto_now_add=True)
    appid = models.CharField(max_length=12)

    class Meta:
        db_table = "push_channel"
        managed = True

class UsersConfig(models.Model):
    start_hour = models.IntegerField()
    end_hour = models.IntegerField()
    start_minute = models.IntegerField()
    end_minute = models.IntegerField()
    users_id = models.IntegerField()
    notify_type = models.CharField(max_length=2)
    silence_type = models.CharField(max_length=1)

    class Meta:
        db_table = "users_config"
        managed = True

class ExternalChannel(models.Model):
    app_key = models.CharField(max_length=255)
    secret = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    mobile = models.CharField(max_length=255,blank=True)
    email = models.CharField(max_length=255,blank=True)
    name = models.CharField(max_length=255,blank=True)
    expirey_date = models.DateTimeField(blank=True)
    status = models.CharField(max_length=1)
    create_time = models.DateTimeField(auto_now_add=True)
    last_update_time = models.DateTimeField(auto_now=True)
    create_by_id = models.IntegerField()

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = "external_channel"
        managed = True

class ExternalOrder(models.Model):
    app_key = models.CharField(max_length=255)
    channel_id = models.IntegerField()
    channel_code = models.CharField(max_length=255)
    user_mobile = models.CharField(max_length=255,blank=True)
    user_email = models.CharField(max_length=255,blank=True)
    price = models.FloatField()
    user_id = models.CharField(max_length=255)
    wx_id = models.CharField(max_length=255,blank=True)
    wx_open_id = models.CharField(max_length=255,blank=True)
    wx_uuid = models.CharField(max_length=255,blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    last_update_time = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=1)
    article_id = models.IntegerField()
    order_sn = models.CharField(max_length=255)

    class Meta:
        db_table = "external_order"
        managed = True



class Play(models.Model):
    article = models.ForeignKey(Article, db_column='article_id')
    match = models.ForeignKey(Match, db_column='match_id')
    language=models.CharField(max_length=20)
    last_update_time=models.DateTimeField()
    create_time=models.DateTimeField(auto_now_add=True)
    recommend_reason=models.CharField(max_length=255)
    type=models.IntegerField()
    major_flag = models.CharField(max_length=1)
    scout_odds_flag=models.CharField(max_length=1)

    class Meta:
        db_table = "play"
        managed = True

class Playdetail(models.Model):
    play_id=models.IntegerField()
    key=models.CharField(max_length=255)
    value=models.CharField(max_length=255)
    select_flag=models.CharField(max_length=1)
    major_flag=models.CharField(max_length=1)

    class Meta:
        db_table = "play_detail"
        managed = True