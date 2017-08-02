# coding:utf-8
'''
Created on 2015-11-30

@author: stone
'''

# Create your views here.
import calendar
import csv
import random
import time
from datetime import datetime,timedelta
import json

import redis
from django.core.paginator import Paginator
from django.db import transaction, connection
from django.template.response import TemplateResponse
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import permission_required, login_required
from django.db.models import Sum, Max, Q, Count
from django.utils import timezone
from django_redis import get_redis_connection

from DjangoUeditor.templatetags.ueditor_tags import register
from jcs.models import ActionLog, BannedLettor, BmsLog
from jcs.views import bms_operation_log
from jcsbms.settings import REDIS_HOST
from jcsbms.settings import REDIS_PASSOWRD
from lottery.models import portal_add_post
from .models import AppUser,Purchase,Charge,Recharge, MoneyChangeHistory, Banner, Portal, charge_add, auser_deactivate, Refund_red_log, \
    WxPayment, Order, OmnipotenceCardIssue
from .forms import RechargeForm, BannerForm, PortalForm,GiveGoldlForm

from analyst.models import Analyst, AnalystChannel, AnalystChannelRelation, AnalystConfig
from article.models import Article, ArticlePortalTags, Articletimeline
from jcsbms.utils import formerror_cat, outputCSV, getLocalDateTime, SettablePaginator, outputdoc
from django.conf import settings
import requests
import logging
import xlrd
from django.shortcuts import redirect
import urllib, urllib2
from actions import RefundRed

logger = logging.getLogger("django")

@permission_required("article.junior_editor")
def user_search(request):

    users = AppUser.objects.filter(usertype=AppUser.USE_TYPE_JCS)

    phonenumber = request.GET.get("phonenumber","")
    if phonenumber != "":
        users = users.filter(phonenumber=phonenumber)

    userid = request.GET.get("userid", "")
    if userid != "":
        userid = int(userid)
        users = users.filter(userid=userid)

    from_cdatestr = request.GET.get("from_cdate", "2015-01-01")
    if from_cdatestr != "":
        from_cdate = timezone.make_aware(datetime.strptime(from_cdatestr + " 00:00:00", "%Y-%m-%d %H:%M:%S"))
        users = users.filter(cdate__gte=from_cdate + timedelta(hours=8))

    to_cdatestr = request.GET.get("to_cdate", datetime.now().strftime("%Y-%m-%d"))
    if to_cdatestr != "":
        to_cdate = timezone.make_aware(datetime.strptime(to_cdatestr + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        users = users.filter(cdate__lte=to_cdate + timedelta(hours=8))

    from_udatestr = request.GET.get("from_udate", "")
    if from_udatestr != "":
        from_udate = timezone.make_aware(datetime.strptime(from_udatestr + " 00:00:00", "%Y-%m-%d %H:%M:%S"))
        users = users.filter(udate__gte=from_udate)

    to_udatestr = request.GET.get("to_udate", "")
    if to_udatestr != "":
        to_udate = timezone.make_aware(datetime.strptime(to_udatestr + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        users = users.filter(udate__lte=to_udate)

    os = request.GET.get("os", "")
    if os !="":
        users = users.filter(os=os)

    inviter = request.GET.get("inviter","")
    if inviter!="":
        users = users.filter(inviter__nick_name=inviter)

    language = int(request.GET.get("language", -1))
    if language == 1:  # 国语
        users = users.filter(appid='M')
    elif language == 0:  # 粤语
        users = users.filter(appid='C')

    if request.GET.get("for_export","")=="on" and (from_cdate!="" or to_cdate!="") and request.user.has_perm("moblieapp.export_user"):

        headers = [u"用户ID",u"手机号",u"注册时间",u"最后登录",u"操作系统", u"操作系统版本", u"app版本", u"渠道来源",u"注册客户端",u"状态"]
        def genRows():
            for user in users.order_by("-userid"):
                yield       [str(user.userid),
                             str(user.phonenumber),
                             getLocalDateTime(user.cdate).strftime("%Y-%m-%d %H:%M:%S"),
                             getLocalDateTime(user.udate).strftime("%Y-%m-%d %H:%M:%S"),
                             user.os or '',
                             user.version or '',
                             user.client_version or '',
                             user.channelname or '',
                             u"国语" if user.appid == 'M' else u"粤语",
                             u"可登录" if user.isactive else u"不可登录"]

        # 用户导出记录日志
        bms_operation_log(request.user.id, "用户导出", "")
        return outputCSV(genRows(), "users.csv", headers)

    channelname = request.GET.get("channelname", "")
    if channelname != "":
        users = users.filter(channelname=channelname)

    is_invited = int(request.GET.get("is_invited", -1))
    if is_invited == 1:
        users = users.filter(inviter__isnull=False)
    elif is_invited == 0:
        users = users.filter(inviter__isnull=True)

    users = users.order_by("-userid")

    paginator = Paginator(users,30)

    page_index = int(request.GET.get("page_index",1))
    pager = paginator.page(page_index)

    user_last_active_time_api = settings.ALS_DATA_APIS["user_last_active_time"]
    userIds = []
    for obj in pager.object_list:
        userIds.append(str(obj.userid))
    userLastActiveTime = ["" for i in xrange(len(userIds)) ]
    try:
        resp = requests.get(user_last_active_time_api, params={"userids": ",".join(userIds)})
        respJson = json.loads(resp.text)
        if respJson["code"] == 0 :
            for i in xrange(len(userIds)):
                if userIds[i] in respJson["data"]:
                    userLastActiveTime[i] = respJson["data"][userIds[i]].split(".")[0]
    except Exception, e:
        print str(e)

    return TemplateResponse(request,"mobileapp/users.html",locals())

@permission_required("article.junior_editor")
def followers(request):

    analyst = Analyst.objects.get(id=request.GET["id"])

    follows = analyst.followers.all() #讲师的关注粉丝
    #关注粉丝搜索
    follower_id = request.GET.get("follower_id", "")
    if follower_id != "":
        follows = follows.filter(userid = follower_id)

    follows = follows.order_by("-userid")
    paginator = Paginator(follows,30)
    page_index = int(request.GET.get("page_index",1))
    pager = paginator.page(page_index)

    #获取被屏蔽的粉丝
    bannedlettors = BannedLettor.objects.all().filter(analyst_id=analyst.id)
    banned_userids = [x.auser_id for x in bannedlettors]
    for user in pager.object_list:
        if user.userid in banned_userids:
            user.banned = True
        else:
            user.banned = False

    return TemplateResponse(request,"mobileapp/followers.html",{"pager":pager,"analyst":analyst,"follower_id":follower_id})

@permission_required("article.junior_editor")
def follow_analysts(request):
    user = AppUser.objects.get(userid=request.GET["id"])

    paginator = Paginator(user.followers.all()  ,30)

    page_index = int(request.GET.get("page_index",1))

    pager = paginator.page(page_index)

    return TemplateResponse(request,"mobileapp/analysts.html",{"pager":pager,"appuser":user})

@permission_required("article.junior_editor")
def deactivate_user(request):

    appuser = AppUser.objects.get(userid=request.POST["id"])
    appuser.isactive=False
    appuser.save()
    auser_deactivate(appuser)
    # 用户登录无效记录日志
    bms_operation_log(request.user.id, "用户登录无效", "用户ID%s" % str(request.POST["id"]))
    return JsonResponse({"result":True})

@permission_required("article.junior_editor")
def activate_user(request):

    appuser = AppUser.objects.get(userid=request.POST["id"])
    appuser.isactive=True
    appuser.save()
    return JsonResponse({"result":True})


@permission_required("mobileapp.add_purchase", raise_exception=True)
def pullnew(request):
    fristdays=time.localtime().tm_mday-1
    lastday=calendar.monthrange(time.localtime().tm_year, time.localtime().tm_mon)[1]

   # from_datestr = request.GET.get("from_cdate", (timezone.now() - timedelta(days=fristdays)).strftime("%Y-%m-%d 00:00:00"))
    #to_datestr = request.GET.get("to_cdate", (timezone.now() - timedelta(days=fristdays-lastday+1)).strftime("%Y-%m-%d 23:59:59"))
    month=request.GET.get("month","")
    if month!=u"":
        if month==u"4":
            from_datestr=u"2017-04-01 00:00:00"
            to_datestr=u"2017-04-30 23:59:59"
        elif month==u"5":
            from_datestr = u"2017-05-01 00:00:00"
            to_datestr = u"2017-05-31 23:59:59"
        elif month == u"6":
            from_datestr = u"2017-06-01 00:00:00"
            to_datestr = u"2017-06-30 23:59:59"
        elif month == u"7":
            from_datestr = u"2017-07-01 00:00:00"
            to_datestr = u"2017-07-31 23:59:59"
        elif month == u"8":
            from_datestr = u"2017-08-01 00:00:00"
            to_datestr = u"2017-08-31 23:59:59"
        elif month == u"9":
            from_datestr = u"2017-09-01 00:00:00"
            to_datestr = u"2017-09-30 23:59:59"
        elif month == u"10":
            from_datestr = u"2017-10-01 00:00:00"
            to_datestr = u"2017-10-31 23:59:59"
        elif month == u"11":
            from_datestr = u"2017-11-01 00:00:00"
            to_datestr = u"2017-11-30 23:59:59"
        elif month == u"12":
            from_datestr = u"2017-12-01 00:00:00"
            to_datestr = u"2017-12-31 23:59:59"

    else:
        month=str(time.localtime().tm_mon)
        from_datestr= request.GET.get("from_cdate", (timezone.now() - timedelta(days=fristdays)).strftime("%Y-%m-%d 00:00:00"))
            #(timezone.now() - timedelta(days=fristdays)).strftime("%Y-%m-%d 00:00:00")
        to_datestr =request.GET.get("to_cdate", (timezone.now() - timedelta(days=fristdays-lastday+1)).strftime("%Y-%m-%d 23:59:59"))
            #(timezone.now() - timedelta(days=fristdays - lastday + 1).strftime("%Y-%m-%d 23:59:59"))
    from_date = timezone.make_aware(datetime.strptime(from_datestr, "%Y-%m-%d %H:%M:%S"))
    to_date = timezone.make_aware(datetime.strptime(to_datestr, "%Y-%m-%d %H:%M:%S"))
    zhuce_date=timezone.make_aware(datetime.strptime("2017-06-30 23:59:59", "%Y-%m-%d %H:%M:%S"))

    #计算注册时间后者to
    zhuce_last_time=to_date
    #需要修改
    name=to_date<zhuce_date
    if name:
        zhuce_last_time=to_date
    else:
        zhuce_last_time=zhuce_date


    cursor = connection.cursor()
    sql = u"""
        SELECT techer.nick_name ,t.* from (SELECT
                u.inviteid,
                u.userid,
                to_date(to_char(u.cdate,'YYYY-mm-dd'),'YYYY-mm-dd') as createtime,
                to_date(to_char(to_timestamp(to_char(u.cdate,'YYYY-mm-dd'),'YYYY-mm-dd hh:mi:ss')+interval '6 month' -INTERVAL '1 second','YYYY-mm-dd'),'YYYY-mm-dd')as endtime,
                CASE WHEN u.cdate>'%s' THEN to_date(to_char(u.cdate,'YYYY-mm-dd'),'YYYY-mm-dd') ELSE '%s' END as user_frist_time,
               to_date(to_char( CASE WHEN (to_timestamp(to_char(u.cdate,'YYYY-mm-dd'),'YYYY-mm-dd hh:mi:ss')+interval '6 month' -INTERVAL '1 second')>'%s' THEN '%s' ELSE (to_timestamp(to_char(u.cdate,'YYYY-mm-dd'),'YYYY-mm-dd hh:mi:ss')+interval '6 month' -INTERVAL '1 second') END,'YYYY-mm-dd'),'YYYY-mm-dd') as user_last_time,
                to_char(date_part('day',
                  (CASE WHEN (to_timestamp(to_char(u.cdate,'YYYY-mm-dd'),'YYYY-mm-dd hh:mi:ss')+interval '6 month' -INTERVAL '1 second')>'%s' THEN '%s' ELSE (to_timestamp(to_char(u.cdate,'YYYY-mm-dd'),'YYYY-mm-dd hh:mi:ss')+interval '6 month' -INTERVAL '1 second') END )-
                   (CASE WHEN u.cdate>'%s' THEN to_timestamp(to_char(u.cdate,'YYYY-mm-dd'),'YYYY-mm-dd hh:mi:ss') ELSE '%s' END )

                 )+1,'9999') as xiangcha_days,
                sum(case when  (P .cdate) >= (CASE WHEN u.cdate>'%s' THEN u.cdate ELSE '%s' END )
                    AND  (P .cdate) <= (CASE WHEN (to_timestamp(to_char(u.cdate,'YYYY-mm-dd'),'YYYY-mm-dd hh:mi:ss')+interval '6 month' -INTERVAL '1 second')>'%s' THEN '%s' ELSE (to_timestamp(to_char(u.cdate,'YYYY-mm-dd'),'YYYY-mm-dd hh:mi:ss')+interval '6 month' -INTERVAL '1 second') END) AND P .status = 1
                then (P .price / 100) else 0 end
                ) price,
                 sum(case when  (P .cdate) >= (CASE WHEN u.cdate>'%s' THEN u.cdate ELSE '%s' END )
                    AND  (P .cdate) <= (CASE WHEN (to_timestamp(to_char(u.cdate,'YYYY-mm-dd'),'YYYY-mm-dd hh:mi:ss')+interval '6 month' -INTERVAL '1 second')>'%s' THEN '%s' ELSE (to_timestamp(to_char(u.cdate,'YYYY-mm-dd'),'YYYY-mm-dd hh:mi:ss')+interval '6 month' -INTERVAL '1 second') END) AND P .status = 1
                then ((P .price / 100)*0.25)else 0 end
                )  total
            FROM
                users u
            LEFT JOIN purchase P ON u.userid = P .userid
            WHERE
                u.inviteid is not NULL and
                 (u.cdate) >= '2017-04-01 00:00:00+08:00'
            AND  (u.cdate) <= '%s'

            GROUP BY
                u.userid
            )t LEFT JOIN analyst_analyst techer ON techer.id=t.inviteid
            WHERE price>0
            ORDER BY techer.nick_name  desc;
    """%(from_date,from_date,to_date,to_date,to_date,to_date,from_date,from_date,from_date,from_date,to_date,to_date,from_date,from_date,to_date,to_date,zhuce_last_time)
    cursor.execute(sql)
    unionInfos = cursor.fetchall()

    paginator = Paginator(unionInfos, 30)
    page_index = request.GET.get("page_index", 1)
    pager = paginator.page(page_index)

    if request.GET.get("for_export", "") == "on" and (from_datestr != "" or to_datestr != ""):

        headers = [u"推荐老师", u"用户ID", u"注册时间",u"活动返现截止时间", u"当月返现开始时间", u"当月返现截止时间", u"当月返现天数", u"当月返现应计金额",u"当月返现金额"]

        def genRows():
            for unionInfo in unionInfos:
                techerID = unionInfo[0]
                techerName = str(unionInfo[2])
                allarticle =  str(unionInfo[3])
                red = str(unionInfo[4])
                black = str(unionInfo[5])
                zoushui = str(unionInfo[6])
                shenglv = str(unionInfo[7])
                shenglv1 = str(unionInfo[8])
                shenglv2 = str(unionInfo[9])
                yield [
                    techerID,
                    techerName,
                    allarticle,
                    red,
                    black,
                    zoushui,
                    shenglv,
                    shenglv1,
                    shenglv2
                ]

        return outputCSV(genRows(), "pull_new_teacher.csv", headers)

    return TemplateResponse(request, "mobileapp/pull_new_list.html",locals())

@permission_required("mobileapp.add_purchase", raise_exception=True)
def purchase_search(request):
    #排除`梅花彩数`和`子墨`
    purchases  = Purchase.objects.all().exclude(purchasetype=Purchase.PURCHASE_TYPE_MONTH).exclude(author__in=(15,23))

    status = 1

    if request.GET.get("from_date","") != "" :
        from_datestr = request.GET.get("from_date")
        to_datestr =request.GET.get("to_date")
        if "status" not in request.GET:
            status = 0
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        from_datestr = today + " 00:00:00"
        to_datestr = today + " 23:59:59"

    purchases = purchases.filter(status=status)

    from_date = datetime.strptime(from_datestr,"%Y-%m-%d %H:%M:%S") + timedelta(hours=8)
    to_date = datetime.strptime(to_datestr + ".999999","%Y-%m-%d %H:%M:%S.%f") + timedelta(hours=8)
    purchases= purchases.filter(cdate__gte=from_date, cdate__lte=to_date)

    nick_name = request.GET.get("nick_name","")
    if nick_name!="":
        purchases = purchases.filter(user__nickname=nick_name)


    paytype =  int(request.GET.get("paytype","0"))
    if paytype == 5:
        purchases = purchases.filter(paytype__in=[3,5])
    elif paytype>0:
        purchases = purchases.filter(paytype=paytype)

    buy_id = request.GET.get("buy_id", "")
    if buy_id != "":
        buy_id = int(buy_id)
        purchases = purchases.filter(id=buy_id)

    userid = request.GET.get("userid", "")
    if userid != "":
        userid = int(userid)
        purchases = purchases.filter(user_id=userid)

    anick_name = request.GET.get("anick_name", "")
    if anick_name != "":
        names = anick_name.strip().split(" ")
        purchases = purchases.filter(author__nick_name__in=names)

    price_low = request.GET.get('price_low', '')
    price_high = request.GET.get('price_high', '')
    if price_low != '':
        purchases = purchases.filter(price__gte=int(price_low) * 100)
    if price_high != '':
        purchases = purchases.filter(price__lte=int(price_high) * 100)

    language = int(request.GET.get("language", -1))
    if language == 1:  # 国语
        purchases = purchases.filter(order__appid='M')
    elif language == 0:  # 粤语
        purchases = purchases.filter(order__appid='C')

    user_inviteid =  request.GET.get('user_inviteid', '')
    if user_inviteid != '':
        purchases = purchases.filter(user__inviter=user_inviteid)

    purchasetype = int(request.GET.get("purchasetype", -1))
    article_keywords = ""
    if purchasetype >= 0:
        purchases = purchases.filter(purchasetype=purchasetype)
        if purchasetype == 0:
            #只适用于购买文章的
            article_keywords = request.GET.get("article_keywords", "")
            portal_tag = int(request.GET.get("portal_tag", -1))
            articles = None
            if article_keywords != "" or portal_tag >= 0:
                #文章表的时区是东八区
                articles = Article.objects.filter(date_added__gte=from_date-timedelta(hours=8)).filter(date_added__lte=to_date-timedelta(hours=8))
            if article_keywords != "":
                words = article_keywords.strip().split(" ")
                conds = Q()
                for word in words:
                    conds |= Q(text__contains=word) | Q(title__contains=word) | Q(digest__contains=word) | Q(portal_tags__name__contains=word)
                articles = articles.filter(conds)
            if portal_tag == 0:
                #无标签
                articles = articles.filter(portal_tags=None)
            elif portal_tag > 0:
                articles = articles.filter(portal_tags=portal_tag)



            if articles != None:
                ids = articles.only("id")
                purchases = purchases.filter(target__in=ids)



    target_id = request.GET.get("target_id", "")
    if target_id != "":
        ids = [int(x) for x in target_id.strip().split(" ") ]
        purchases = purchases.filter(target__in=ids)

    if request.GET.get("for_export","")=="on" and request.user.has_perm("mobileapp.export_purchase") and (from_datestr!="" or to_datestr!=""):

        headers = [u"ID",u"用户ID",u"老师",u"目标",u"标签",u"时间",u"来源",u"语言",u"金额",u"状态"]
        def genRows():
            for purchase in purchases.order_by("-cdate"):
                author = None
                article = Article.objects.get(id=purchase.target)
                tags = " ".join([x.name for x in article.portal_tags.all()])
                try:
                    author = purchase.author
                except Exception, e:
                    logger.error("purchase export: {id:%d}, error:%s", purchase.id, str(e))
                paytype = purchase.paytype if purchase.paytype != 3 else 5
                language = u'国语'
                if purchase.order_id != 0:
                    if purchase.order.appid:
                        if purchase.order.appid == 'C':
                            language = u'粤语'
                yield           [str(purchase.id),
                                 str(purchase.user_id),
                                 author.nick_name if author != None else "",
                                 Purchase.PURCHASE_TYPE_NAMES[purchase.purchasetype]+":"+str(purchase.target),
                                 tags or '',
                                 str(purchase.cdate),
                                 Purchase.PAY_TYPE_NAMES[paytype-1],
                                 language,
                                 str(float(purchase.price)/100),
                                 u"成功"if purchase.status==Purchase.STATUS_SUCCESS else u"失败"]

        # 文章购买导出数据记录日志
        bms_operation_log(request.user.id, "文章购买导出数据", "")
        return outputCSV(genRows(), "purchases.csv", headers)

    gold_sum= purchases.aggregate(gold_sum=Sum('price'))["gold_sum"]

    paginator = Paginator(purchases.order_by("-cdate"),30)
    page_index = int(request.GET.get("page_index","1"))
    pager = paginator.page(page_index)

    portalTags = Portal.objects.all()

    return TemplateResponse(request,"mobileapp/purchase_list.html",locals())

@permission_required("mobileapp.add_purchase", raise_exception=True)
def monthpurchase_search(request):
    purchases  = Purchase.objects.all().filter(purchasetype=Purchase.PURCHASE_TYPE_MONTH)

    status = True
    if request.GET.get("from_date","") != "" :
        from_datestr = request.GET.get("from_date")
        to_datestr =request.GET.get("to_date")
        if "status" not in request.GET:
            status = False
    else:
        from_datestr = datetime.now().strftime("%Y-%m-%d")
        to_datestr =from_datestr

    from_date = datetime.strptime(from_datestr+" 00:00:00","%Y-%m-%d %H:%M:%S")
    to_date = datetime.strptime(to_datestr+" 23:59:59","%Y-%m-%d %H:%M:%S")
    purchases= purchases.filter(cdate__gte=from_date+timedelta(hours=8),cdate__lte=to_date+timedelta(hours=8))

    nick_name = request.GET.get("nick_name","")
    if nick_name!="":
        purchases = purchases.filter(user__nickname=nick_name)


    paytype =  request.GET.get("paytype","0")
    if int(paytype)>0:
        purchases = purchases.filter(paytype=paytype)

    anick_name = request.GET.get("anick_name", "")
    if anick_name != "":
        purchases = purchases.filter(author__nick_name=anick_name)



    if request.GET.get("for_export","")=="on":

        headers = [u"ID",u"用户",u"老师",u"文章ID",u"时间",u"来源",u"金额",u"状态"]
        def genRows():
            for purchase in purchases.filter(status=Purchase.STATUS_SUCCESS).order_by("-cdate"):
                yield           [str(purchase.id),
                                 purchase.user.phonenumber,
                                 purchase.author.nick_name,
                                 Purchase.PURCHASE_TYPE_NAMES[purchase.purchasetype]+":"+str(purchase.target),
                                 str(purchase.cdate),
                                 Purchase.PAY_TYPE_NAMES[purchase.paytype-1],
                                 str(float(purchase.price)/100),
                                 u"成功"if purchase.status==Purchase.STATUS_SUCCESS else u"失败"]

        return outputCSV(genRows(), "month_purchases.csv", headers)

    if status==True:
        purchases = purchases.filter(status=Purchase.STATUS_SUCCESS)
        gold_sum= purchases.aggregate(gold_sum=Sum('price'))["gold_sum"]
    else:
        purchases_success = purchases.filter(status =Purchase.STATUS_SUCCESS)
        gold_sum= purchases_success.aggregate(gold_sum=Sum('price'))["gold_sum"]

    paginator = Paginator(purchases.order_by("-cdate"),30)
    page_index = int(request.GET.get("page_index","1"))
    pager = paginator.page(page_index)

    return TemplateResponse(request,"mobileapp/monthpurchase_list.html",locals())

@permission_required("mobileapp.add_purchase", raise_exception=True)
def charge_search(request):
    charges = Charge.objects.all()

    from_datestr  = request.GET.get("from_date", (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
    if  from_datestr!= "":
        from_date = timezone.make_aware(datetime.strptime(from_datestr+" 00:00:00","%Y-%m-%d %H:%M:%S"))
        #charge表cdate是东八区
        charges = charges.filter(cdate__gte=from_date)

    to_datestr  = request.GET.get("to_date", datetime.now().strftime("%Y-%m-%d") )

    if  to_datestr!= "":
        to_date = timezone.make_aware(datetime.strptime(to_datestr+" 23:59:59","%Y-%m-%d %H:%M:%S"))
        charges = charges.filter(cdate__lte=to_date)

    nick_name = request.GET.get("nick_name","")
    if nick_name!="":
        charges = charges.filter(Q(user__nickname=nick_name) | Q(user__userid=nick_name))

    type = int(request.GET.get("type","0"))
    if type > 0:
        charges = charges.filter(type=type)

    status = int(request.GET.get("status", -1))
    if status >= 0:
        charges = charges.filter(status=status)

    language = int(request.GET.get("language", -1))
    if language == 1:  # 国语
        charges = charges.filter(order__appid='M')
    elif language == 0:  # 粤语
        charges = charges.filter(order__appid='C')

    if request.GET.get("for_export","")=="on" and (from_datestr!="" or to_datestr!="") and request.user.has_perm("mobileapp.export_charge") :
        headers = [u"ID",u'用户ID', u"价格",u"金币数",u"银行",u"来源",u'语言',u"状态",u"时间",u"备注理由"]
        def genRows():
            for charge in charges.order_by("-cdate"):
                ol = u'国语'
                try:
                    if charge.order:
                        if charge.order.appid == 'C':
                            ol = u'粤语'
                except:
                    pass
                yield [str(charge.id),
                       str(charge.user.userid),
                       str(charge.money/100),
                       str(charge.gold),
                       str(charge.bank),
                       charge.CHARGE_TYPE_NAMES[charge.type-1],
                       ol,
                       u"成功" if charge.status else u"失败",
                       str(getLocalDateTime(charge.cdate).strftime("%Y-%m-%d %H:%M:%S")),
                       charge.comment or ''
                      ]

        # 账户流水明细导出数据记录日志
        bms_operation_log(request.user.id, "账户流水明细导出数据", "")
        return outputCSV(genRows(), "charges.csv", headers)

    paginator = Paginator(charges.order_by("-cdate"),30)
    page_index = int(request.GET.get("page_index",1))
    pager = paginator.page(page_index)

    return TemplateResponse(request,"mobileapp/charges_list.html",locals())

@permission_required("mobileapp.add_purchase", raise_exception=True)
def recharge_list(request):
    recharges = Recharge.objects.all();

    paginator = Paginator(recharges.order_by("id"),30)
    page_index = int(request.GET.get("page_index",1))
    pager = paginator.page(page_index)

    return TemplateResponse(request,"mobileapp/recharge_list.html",{"pager":pager})

@permission_required("article.operation_editor")
def post_recharge(request):
    if request.method=="GET":
        if "id" in request.GET:
            recharge = Recharge.objects.get(id=request.GET["id"])
            return TemplateResponse(request,"mobileapp/post_recharge.html",{"recharge":recharge})
        else:
            return TemplateResponse(request,"mobileapp/post_recharge.html",{})
    elif request.method == "POST":
        if "id" in request.POST:
            recharge = Recharge.objects.get(id=request.GET["id"])
            form = RechargeForm(request.POST,instance=recharge)
        else:
            form = RechargeForm(request.POST)

        if form.is_valid():
            try:
                form.save()
                return JsonResponse({"result":True})
            except Exception as e:
                return JsonResponse({"result":False,"message":e.message})
        else:
            return JsonResponse({"result":False,"message":formerror_cat(form)})

@permission_required("analyst.analyst_action")
def analyst_purchases(request):
    purchases  = Purchase.objects.filter(status=1)
    purchases = purchases.filter(author=request.user.analyst).filter(purchasetype=Purchase.PURCHASE_TYPE_ARTICLE)
    analyst = request.user.analyst
    if request.GET.get("from_date","") != "" :
        from_datestr = request.GET.get("from_date")+" 00:00:00"
        to_datestr =request.GET.get("to_date")+" 23:59:59"
        from_date = datetime.strptime(from_datestr,"%Y-%m-%d %H:%M:%S")
        to_date = datetime.strptime(to_datestr,"%Y-%m-%d %H:%M:%S")


    else:
        now = datetime.now()
        daybefore7day= now - timedelta(days=6)

        from_datestr = daybefore7day.strftime("%Y-%m-%d")+" 00:00:00"
        to_datestr =now.strftime("%Y-%m-%d")+" 23:59:59"
        from_date = datetime.strptime(from_datestr,"%Y-%m-%d %H:%M:%S")
        to_date = datetime.strptime(to_datestr,"%Y-%m-%d %H:%M:%S")

    purchases= purchases.filter(cdate__gte=from_date+timedelta(hours=8),cdate__lte=to_date+timedelta(hours=8))
    gold_sum= purchases.aggregate(gold_sum=Sum('price'))["gold_sum"]

    paginator = Paginator(purchases.order_by("-cdate"),30)
    page_index = int(request.GET.get("page_index",1))
    pager = paginator.page(page_index)

    s = '2017-03-11 03:00:00'
    timeTuple = datetime.strptime(s, '%Y-%m-%d %H:%M:%S')

    for obj in pager.object_list:
        value = obj.paytype
        if not analyst.is_mandarin_perm and obj.cdate > timeTuple:
            value = hash(str(obj.id) + "sldjfdsjfljsdfl") % 5
        value = value if value != 3 else 5
        obj.ran_pay = Purchase.PAY_TYPE_NAMES[value - 1]

    return TemplateResponse(request,
                            "mobileapp/analyst_purchases.html",
                            {"pager":pager,
                            "from_date":from_date.strftime("%Y-%m-%d"),
                             "to_date":to_date.strftime("%Y-%m-%d"),
                             "gold_sum":gold_sum})


@permission_required("mobileapp.add_purchase", raise_exception=True)
def article_log(request):
    bmslogs = Articletimeline.objects.all()
    #国语发布时间
    from_datestr = request.GET.get("from_date", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d") + " 00:00:00")
    to_datestr = request.GET.get("to_date", (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d") + " 23:59:59")

    from_date = datetime.strptime(from_datestr, "%Y-%m-%d %H:%M:%S")
    to_date = datetime.strptime(to_datestr, "%Y-%m-%d %H:%M:%S")
    #
    bmslogs = bmslogs.filter(m_cdate__gte=from_date)
    bmslogs = bmslogs.filter(m_cdate__lte=to_date)
    # 审阅时间
    from_datestr1 = request.GET.get("from_date1", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d") + " 00:00:00")
    to_datestr1 = request.GET.get("to_date1", (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d") + " 23:59:59")

    from_date1 = datetime.strptime(from_datestr1, "%Y-%m-%d %H:%M:%S")
    to_date1 = datetime.strptime(to_datestr1, "%Y-%m-%d %H:%M:%S")
    bmslogs = bmslogs.filter(cut_cdate__gte=from_date1)
    bmslogs = bmslogs.filter(cut_cdate__lte=to_date1)
    # 翻译发布时间
    from_datestr2 = request.GET.get("from_date2",
                                    (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d") + " 00:00:00")
    to_datestr2 = request.GET.get("to_date2", (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d") + " 23:59:59")

    from_date2 = datetime.strptime(from_datestr2, "%Y-%m-%d %H:%M:%S")
    to_date2 = datetime.strptime(to_datestr2, "%Y-%m-%d %H:%M:%S")
    bmslogs = bmslogs.filter(translate_cdate__gte=from_date2)
    bmslogs = bmslogs.filter(translate_cdate__lte=to_date2)

    article_id = request.GET.get("article_id", "")
    if article_id != "":
        bmslogs = bmslogs.filter(article_id=article_id)

    cut_author = request.GET.get("cut_author", "")
    if cut_author != "":
        bmslogs = bmslogs.filter(cut_author__contains=cut_author)

    translate_author = request.GET.get("translate_author", "")
    if translate_author != "":
        bmslogs = bmslogs.filter(translate_author__contains=translate_author)

    teacher_id = request.GET.get("teacher_id", "")
    if teacher_id != "":
        analysts=Analyst.objects.get(nick_name__contains=teacher_id)
        teacher_ids=analysts.id
        bmslogs = bmslogs.filter(teacher_id=teacher_ids)
    teacher_thai = request.GET.get("teacher_thai", "")
    if teacher_thai != "":
        analysts = Analyst.objects.get(nick_name__contains=teacher_thai)
        teacher_ids = analysts.id
        bmslogs = bmslogs.filter(teacher_thai=teacher_ids)

    paginator = Paginator(bmslogs.order_by("-id"), 30)
    page_index = request.GET.get("page_index", 1)
    pager = paginator.page(page_index)

    return TemplateResponse(request, "mobileapp/bms_article_logs.html", locals())


@permission_required("mobileapp.add_purchase", raise_exception=True)
def analyst_revenue(request):
    purchases  = Purchase.objects.filter(status=1).exclude(purchasetype=Purchase.PURCHASE_TYPE_MONTH).exclude(purchasetype=Purchase.PURCHASE_TYPE_FLOWER)

    if request.GET.get("from_date","") != "" :
        from_datestr = request.GET.get("from_date")+" 00:00:00"
        to_datestr =request.GET.get("to_date")+" 23:59:59"
        from_date = datetime.strptime(from_datestr,"%Y-%m-%d %H:%M:%S")
        to_date = datetime.strptime(to_datestr,"%Y-%m-%d %H:%M:%S")
    else:
        now = datetime.now()
        daybefore7day= now - timedelta(days=6)

        from_datestr = daybefore7day.strftime("%Y-%m-%d")+" 00:00:00"
        to_datestr =now.strftime("%Y-%m-%d")+" 23:59:59"
        from_date = datetime.strptime(from_datestr,"%Y-%m-%d %H:%M:%S")
        to_date = datetime.strptime(to_datestr,"%Y-%m-%d %H:%M:%S")

    analysts  = Analyst.objects.filter(analyst_type__in=[Analyst.ANALYST_TYPE_FREE,Analyst.ANALYST_TYPE_CHARGE])

    nick_name = request.GET.get("nick_name", "")
    if nick_name != "":
        analysts = analysts.filter(nick_name=nick_name)

    purchases = purchases.filter(cdate__gte=from_date+timedelta(hours=8),cdate__lte=to_date+timedelta(hours=8))
    users = AppUser.objects.filter(cdate__gte=from_date+timedelta(hours=8),cdate__lte=to_date+timedelta(hours=8), inviter__isnull=False)

    channel_id = int(request.GET.get('channel', -1))
    analyst_channel_relation = AnalystChannelRelation.objects.filter(status=AnalystChannelRelation.VALID_STATUS)
    channels = AnalystChannel.objects.all()
    channel_id_name_dict = {}
    for channel in channels :
        channel_id_name_dict[channel.id] = channel.channel_name
    analyst_channel_dict = {}
    if channel_id > 0 :
        #指定了渠道
        analyst_channel_relation = analyst_channel_relation.filter(channel_id=channel_id)
    for ca in analyst_channel_relation :
        analyst_channel_dict[ca.analyst_id] = ca.channel_id
    if channel_id > 0 :
        aids = analyst_channel_dict.keys()
        analysts = analysts.filter(id__in=aids)
        purchases = purchases.filter(author__in=aids)
        users = users.filter(inviter__in=aids)
    #分别计算老师邀请人数和收入
    # 类似: select count(userid) from xxx group by inviter
    inviter_count = users.values("inviter").annotate(Count("userid"))
    author_revenue = purchases.values("author").annotate(Sum("price"))
    inviter_count_dict = {}
    author_revenue_dict = {}
    for ic in inviter_count:
        inviter_count_dict[ ic['inviter'] ] = ic['userid__count']
    for ar in author_revenue:
        author_revenue_dict[ ar['author'] ] = ar['price__sum']

    if request.GET.get("for_export","")=="on":

        headers = [u"老师ID",u"老师昵称",u"渠道", u"金额",u"邀请人数"]

        def genRows():
            for analyst in analysts:
                analyst.invite_count = inviter_count_dict.get(analyst.id, 0)
                analyst.revenue = author_revenue_dict.get(analyst.id, 0)
                analyst.channel = channel_id_name_dict.get(analyst_channel_dict.get(analyst.id, 0), '')

                yield [str(analyst.id),
                       analyst.nick_name,
                       analyst.channel,
                       str(float(analyst.revenue)/100),
                       str(analyst.invite_count)
                      ]

        # 老师收入导出数据记录日志
        bms_operation_log(request.user.id, "老师收入导出数据", "")
        return outputCSV(genRows(), "revenues.csv", headers)

    paginator = Paginator(analysts.order_by("id"),30)
    page_index = int(request.GET.get("page_index",1))
    pager = paginator.page(page_index)

    for object in pager.object_list:
        object.invite_count = inviter_count_dict.get(object.id, 0)
        object.revenue = author_revenue_dict.get(object.id, 0)
        object.channel = channel_id_name_dict.get(analyst_channel_dict.get(object.id, 0), '')

    return TemplateResponse(request,"mobileapp/analyst_revenue.html",{"pager":pager,"from_date":from_date.strftime("%Y-%m-%d"),"to_date":to_date.strftime("%Y-%m-%d"), "channels":channels, "channel_id":channel_id})

@permission_required("mobileapp.add_purchase", raise_exception=True)
def charge_rank(request):
    charges = Charge.objects.all();

    if request.GET.get("from_date","") != "" :
        from_datestr = request.GET.get("from_date")+" 00:00:00"
        to_datestr =request.GET.get("to_date")+" 23:59:59"
        from_date = timezone.make_aware(datetime.strptime(from_datestr,"%Y-%m-%d %H:%M:%S"))
        to_date = timezone.make_aware(datetime.strptime(to_datestr,"%Y-%m-%d %H:%M:%S"))
    else:
        now = datetime.now()
        daybefore1day= now - timedelta(hours=24)


        from_datestr = daybefore1day.strftime("%Y-%m-%d %H:%M:%S")
        to_datestr =now.strftime("%Y-%m-%d %H:%M:%S")
        from_date = timezone.make_aware(datetime.strptime(from_datestr,"%Y-%m-%d %H:%M:%S"))
        to_date = timezone.make_aware(datetime.strptime(to_datestr,"%Y-%m-%d %H:%M:%S"))


    charges = charges.filter(cdate__gte=from_date+timedelta(hours=8),cdate__lte=to_date+timedelta(hours=8))
    charges = charges.values('user__phonenumber','user__goldcoin', 'user__userid').annotate(revenue=Sum('gold'))

    paginator = Paginator(charges.order_by("-revenue"),30)
    page_index = int(request.GET.get("page_index",1))
    pager = paginator.page(page_index)

    return TemplateResponse(request,"mobileapp/recharge_ranklist.html",{"pager":pager})


@permission_required("mobileapp.add_purchase", raise_exception=True)
def money_changes(request):
    changes = MoneyChangeHistory.objects.all()


    to_datestr = request.GET.get("to_date", "")
    if to_datestr != "":
        to_date = datetime.strptime(to_datestr,"%Y-%m-%d %H:%M")
        changes = changes.filter(cdate__lte=to_date + timedelta(hours=8))

    phonenumber = request.GET.get("phonenumber", "")
    if phonenumber != "":
        changes = changes.filter(Q(user__phonenumber=phonenumber) | Q(user__userid=int(phonenumber)))

    latest_changes = changes.values("user").annotate(max_id= Max("id"))



    if request.GET.get("for_export", "") == "on":

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="money_changes.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [u"用户".encode("utf-8"), u"最后交易时间".encode("utf-8"), u"剩余金额".encode("utf-8")])
        for object in latest_changes:
            change = MoneyChangeHistory.objects.get(id=object["max_id"])
            writer.writerow([change.user.phonenumber,
                             str(change.cdate),
                             str(change.leftmoney / 100)]),

        # 现金余额导出数据记录日志
        bms_operation_log(request.user.id, "现金余额导出数据", "")
        return response

    paginator = Paginator(latest_changes, 30)
    page_index = int(request.GET.get("page_index", 1))
    pager = paginator.page(page_index)
    for object in pager.object_list:

        change = MoneyChangeHistory.objects.get(id=object["max_id"])
        object["leftmoney"] = change.leftmoney
        object["id"] = object["max_id"]
        object["cdate"] = change.cdate
        object["phonenumber"] = change.user.phonenumber
        object['user_id'] = change.user.userid

    return TemplateResponse(request, "mobileapp/money_changes.html", {"pager": pager, "phonenumber":phonenumber})

@permission_required("article.operation_editor")
def banner_list(request):
    banners = Banner.objects.all()

    paginator = Paginator(banners.order_by("-id"), 30)
    page_index = int(request.GET.get("page_index", 1))
    pager = paginator.page(page_index)

    return TemplateResponse(request, "mobileapp/banner_list.html", {"pager": pager})
@permission_required("article.operation_editor")
def post_banner(request):
    if request.method == "GET":
        if "id" in request.GET:
            banner = Banner.objects.get(id=request.GET["id"])
            return TemplateResponse(request, "mobileapp/post_banner.html", {"banner": banner})
        else:
            return TemplateResponse(request, "mobileapp/post_banner.html", {})
    elif request.method == "POST":
        if "id" in request.POST:
            banner = Banner.objects.get(id=request.POST["id"])
            form = BannerForm(request.POST, instance=banner)
        else:
            form = BannerForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                if "id" in request.POST:
                    # 修改广告记录日志
                    bms_operation_log(request.user.id, "修改广告", "广告ID%s" % str(request.POST["id"]))
                else:
                    # 新增广告记录日志
                    bms_operation_log(request.user.id, "新增广告", "广告ID%s" % str(Banner.objects.all().latest('id').id))
                return JsonResponse({"result": True})
            except Exception as e:
                return JsonResponse({"result": False, "message": e.message})
        else:
            return JsonResponse({"result": False, "message": formerror_cat(form)})

@permission_required("article.operation_editor")
def online_banner(request):
    banner  = Banner.objects.get(id=request.POST["id"])
    if banner.is_online:
        return JsonResponse({"result": False,"message":u"此广告目前就是上线状态"})

    else:
        banner.is_online=True
        banner.save()
        # 广告上线记录日志
        bms_operation_log(request.user.id, "广告上线", "广告ID%s" % str(banner.id))
        return JsonResponse({"result": True})
@permission_required("article.operation_editor")
def down_banner(request):
    banner  = Banner.objects.get(id=request.POST["id"])
    if not banner.is_online:
        return JsonResponse({"result": False,"message":u"此广告目前就是下线状态"})
    else:
        banner.is_online=False
        banner.save()
        return JsonResponse({"result": True})
@permission_required("article.operation_editor")
def portal_list(request):
    portals = Portal.objects.all()

    paginator = Paginator(portals.order_by("-id"), 30)
    page_index = int(request.GET.get("page_index", 1))
    pager = paginator.page(page_index)

    return TemplateResponse(request, "mobileapp/portal_list.html", {"pager": pager})

@permission_required("article.operation_editor")
def post_portal(request):
    if request.method == "GET":
        if "id" in request.GET:
            portal = Portal.objects.get(id=request.GET["id"])
            return TemplateResponse(request, "mobileapp/post_portal.html", {"portal": portal})
        else:
            return TemplateResponse(request, "mobileapp/post_portal.html", {})
    elif request.method == "POST":
        if "id" in request.POST:
            portal = Portal.objects.get(id=request.POST["id"])
            form = PortalForm(request.POST, instance=portal)
            if form.is_valid():
                try:
                    form.save()
                    # 新增修改入口记录日志
                    bms_operation_log(request.user.id, "修改入口", "入口ID%s" % str(portal.id))
                    return JsonResponse({"result": True})
                except Exception as e:
                    return JsonResponse({"result": False, "message": e.message})
            else:
                return JsonResponse({"result": False, "message": formerror_cat(form)})

        else:
            form = PortalForm(request.POST)
            if form.is_valid():
                try:
                    form.save()
                    # 新增时消息列队推送消息
                    portal_add_post(form.instance) # 拿到form的实例对象
                    # 新增入口记录日志
                    bms_operation_log(request.user.id, "新增入口", "入口ID%s" % str(Portal.objects.all().latest('id').id))
                    return JsonResponse({"result": True})
                except Exception as e:
                    return JsonResponse({"result": False, "message": e.message})
            else:
                return JsonResponse({"result": False, "message": formerror_cat(form)})

@permission_required("article.operation_editor")
def online_portal(request):
    portal = Portal.objects.get(id=request.POST["id"])
    if portal.is_online:
        return JsonResponse({"result": False, "message": u"此入口目前就是上线状态"})

    else:
        portal.is_online = True
        portal.save()
        # 入口上线记录日志
        bms_operation_log(request.user.id, "入口上线", "入口ID%s" % str(portal.id))
        return JsonResponse({"result": True})

@permission_required("article.operation_editor")
def down_portal(request):
    portal = Portal.objects.get(id=request.POST["id"])
    if not portal.is_online:
        return JsonResponse({"result": False, "message": u"此入口目前就是下线状态"})
    else:
        portal.is_online = False
        portal.save()
        return JsonResponse({"result": True})


@permission_required("mobileapp.give_gold")
def deduct_gold(request):

    form = GiveGoldlForm(request.POST)
    '''user = models.ForeignKey(AppUser,db_column="userid")
    money = models.IntegerField()
    gold = models.IntegerField(db_column="goldcoin")
    bank = models.CharField(max_length=48)
    type = models.SmallIntegerField()
    status = models.SmallIntegerField()
    cdate = models.DateTimeField(auto_now_add=True)
    comment = models.CharField(max_length=255)'''
    users= AppUser.objects.get(userid=request.POST["id"])

    if form.is_valid():
      if users.goldcoin>=form.cleaned_data["gold"]:
        with transaction.atomic():
            charge = Charge()
            charge.money = 0
            louchujine = (0 - form.cleaned_data["gold"])
            charge.gold = louchujine
            charge.bank = "GC"
            charge.type = 8
            charge.status = 1
            auser = AppUser.objects.select_for_update().get(userid=request.POST["id"])
            charge.user = auser

            auser.goldcoin = auser.goldcoin +louchujine
            charge.comment = form.cleaned_data["comment"]
            charge.operator_id = request.user.id
            auser.save()
            charge.save()
        charge_add(charge)
        # 扣除精彩币记录日志
        bms_operation_log(request.user.id, "扣除精彩币", "用户ID%s" % str(request.POST["id"]))
        return JsonResponse({"result": True})
      else:return JsonResponse({"result": False, "message": "扣除数量大于用户余额数量"})
    else:
        return JsonResponse({"result": False, "message": formerror_cat(form)})
@permission_required("mobileapp.give_gold")
def give_gold(request):

    form = GiveGoldlForm(request.POST)
    '''user = models.ForeignKey(AppUser,db_column="userid")
    money = models.IntegerField()
    gold = models.IntegerField(db_column="goldcoin")
    bank = models.CharField(max_length=48)
    type = models.SmallIntegerField()
    status = models.SmallIntegerField()
    cdate = models.DateTimeField(auto_now_add=True)
    comment = models.CharField(max_length=255)'''
    if form.is_valid():
        with transaction.atomic():
            charge = Charge()
            charge.money = 0
            charge.gold = form.cleaned_data["gold"]
            charge.bank = "GC"
            charge.type = 8
            charge.status = 1
            auser = AppUser.objects.select_for_update().get(userid=request.POST["id"])
            charge.user = auser
            auser.goldcoin = auser.goldcoin + form.cleaned_data["gold"]
            charge.comment = form.cleaned_data["comment"]
            charge.operator_id = request.user.id
            auser.save()
            charge.save()
        charge_add(charge)
        # 赠送精彩币记录日志
        bms_operation_log(request.user.id, "赠送精彩币", "用户ID%s" % str(request.POST["id"]))
        return JsonResponse({"result": True})
    else:
        return JsonResponse({"result": False, "message": formerror_cat(form)})
@login_required
def channel_users(request):
    ausers = AppUser.objects.filter(channel__isnull=False).filter(channel__gte=8000,channel__lte=9000)
    channel = request.GET.get("channel","")
    if channel!="":
        ausers=ausers.filter(channel=channel)

    paginator = Paginator(ausers, 30)

    page_index = int(request.GET.get("page_index", 1))
    pager = paginator.page(page_index)

    return TemplateResponse(request, "mobileapp/channel_users.html", {"pager": pager})

@permission_required("article.junior_editor")
def comment_list(request):

    return TemplateResponse(request, "mobileapp/comment_list.html")

@permission_required("article.junior_editor")
def new_comments(request):
    con = get_redis_connection("default")
    '''
    for i in range(12):
        comment = {}
        comment["id"] = i
        comment["content"] = "content_" + str(i)
        comment["user"] = '7788'
        comment["time"] = 'xxxx'
        con.zadd("new_comments", i, json.dumps(comment))
    '''
    list1 = con.zrange("new_comments", 0, 10)

    list2 = []
    for item1 in list1:
        print item1
        list2.append(json.loads(item1.replace("'", '"')))
    return JsonResponse(list2,safe=False)

@permission_required("article.junior_editor")
def verify_comment(request):
    id = int(request.POST["id"])
    con = get_redis_connection("default")
    items = con.zrangebyscore("new_comments", id, id)
    if len(items)>0:
        item = items[0]
        i =  con.zremrangebyscore("new_comments", id, id)
        if i>0:
            con.zadd("liverank",1,str(json.loads(item.replace("'", '"'))['user']))
            con.publish("pub_comments", item)
            return JsonResponse({"result": True})

    pass

@permission_required("article.junior_editor")
def deny_comment(request):
    id = int(request.POST["id"])
    con = get_redis_connection("default")
    items = con.zrange("new_comments", id, id)
    if len(items) > 0:
        con.zremrangebyscore("new_comments", id, id)
        return JsonResponse({"result": True})

@permission_required("mobileapp.add_purchase", raise_exception=True)
@permission_required("mobileapp.give_gold", raise_exception=True)
def batch_refund(request):
    fl = request.GET.get("fail_list", "[]")

    fail_list = json.loads(fl)
    success = int(request.GET.get("success", 0))
    if request.method == "POST":
        fileHandle = request.FILES.get("input_file", None)
        if fileHandle != None:
            data = xlrd.open_workbook(file_contents=fileHandle.read())
            table = data.sheets()[0]
            for i in xrange(table.nrows):
                cols = table.row_values(i)
                if len(cols) < 2:
                    continue
                phonenumber = int(cols[0])
                goldcoin = int(cols[1])
                comment_reson=cols[2]
                try:
                    with transaction.atomic():
                        charge = Charge()
                        charge.money = 0
                        charge.gold = goldcoin
                        charge.bank = "GC"
                        charge.type = 8
                        charge.status = 1
                        auser = AppUser.objects.select_for_update().get(userid=phonenumber)
                        charge.user = auser
                        auser.goldcoin = auser.goldcoin + goldcoin
                        charge.comment = comment_reson
                        auser.save()
                        charge.save()
                    charge_add(charge)
                except Exception,e:
                    logger.error("batch refund for [%d, %d] error: %s", phonenumber, goldcoin, str(e))
                    fail_list.append({"phonenumber": phonenumber, "goldcoin": goldcoin,"comment_reson": comment_reson})
        success = int(len(fail_list) == 0)
        # 批量退费记录日志
        bms_operation_log(request.user.id, "批量退费", "")
        return redirect(request.path + "?success=%d&fail_list=%s" % (success, json.dumps(fail_list)))
    return TemplateResponse(request, "mobileapp/batch_refund.html", {"fail_list": fail_list, "success":success})

@permission_required("mobileapp.give_gold")
def refund_red(request):
    if request.method == "POST":
        article_id = int(request.POST.get("article_id", 0));
        if article_id > 0:
            #查询是否有红单退款记录
            if ActionLog.objects.filter(action=RefundRed.action, target_id=article_id) :
                return JsonResponse({"result": False, "message": u"已经退过款了!"})
            purchases = Purchase.objects.filter(purchasetype=Purchase.PURCHASE_TYPE_ARTICLE, target=article_id, status=1)
            total = 0
            success = 0
            failed = 0
            for purchase in purchases:
                total += 1
                goldcoin = purchase.price / 100
                refund_red_log = Refund_red_log()
                refund_red_log.user_id = purchase.user_id
                refund_red_log.article_id = purchase.target
                refund_red_log.op_id = request.user.id
                refund_red_log.goldcoin = goldcoin
                try:
                    with transaction.atomic():
                        charge = Charge()
                        charge.money = 0
                        charge.gold = goldcoin
                        charge.bank = "GC"
                        charge.type = 9
                        charge.status = 1
                        auser = AppUser.objects.select_for_update().get(userid=purchase.user_id)
                        charge.user = auser
                        auser.goldcoin = auser.goldcoin + goldcoin
                        auser.save()
                        charge.save()
                    charge_add(charge)
                    refund_red_log.status = Refund_red_log.STATUS_SUCCESS
                    success += 1
                except Exception,e:
                    logger.error("refund red for [%d, %d] error: %s", purchase.user_id, purchase.price, str(e))
                    refund_red_log.status = Refund_red_log.STATUS_FAILED
                    failed += 1
                finally:
                    refund_red_log.save()

            RefundRed().makeLog(request.user, article_id)
            return JsonResponse({"result":True, "message":u"退款成功(%d/%d)" % (success, total)})
    return JsonResponse({"result":False, "message":u"invalid request"})

@permission_required("article.junior_editor")
def refund_red_log(request):
    article_id = int(request.GET.get("article_id", 0))
    user_id = request.GET.get("user_id", "")
    phonenumber = request.GET.get("phonenumber", "")
    status = request.GET.get("status", "")
    logs = Refund_red_log.objects.filter(article_id=article_id)
    if user_id != "":
        user_id = int(user_id)
        logs = logs.filter(user_id=user_id)

    if phonenumber != "":
        logs = logs.filter(user__phonenumber=phonenumber)

    if status != "":
        status = int(status)
        logs = logs.filter(status=status)

    if request.GET.get("for_export", "") == "on":
        headers = [u'用户ID', u'手机号', u'退款时间', u'金额', u'状态']
        def genRows():
            for log in logs:
                yield [
                    str(log.user_id),
                    log.user.phonenumber,
                    getLocalDateTime(log.create_time).strftime('%Y-%m-%d %H:%M:%S'),
                    str(log.goldcoin),
                    u'成功' if log.status == Refund_red_log.STATUS_SUCCESS else u'失败'
                ]
        return outputCSV(genRows(), "refund_red_logs_%d.csv" % article_id, headers)

    paginator = Paginator(logs, 30)
    page_index = int(request.GET.get("page_index", 1))
    pager = paginator.page(page_index)

    num_total = logs.count()
    num_success = logs.filter(status=1).count()
    num_failed = logs.filter(status=-1).count()
    return TemplateResponse(request, "mobileapp/refund_red_log.html", locals())


@permission_required("article.junior_editor")
def cheat_monitor(request):
    queryParams = {}
    if request.GET.get("for_export","") != "on":
        #导出不限制页数
        page_index = int(request.GET.get("page_index", 1))
        queryParams["_page"] = page_index
    from_datestr  = request.GET.get("from_date", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"))
    to_datestr = request.GET.get("to_date", from_datestr)
    queryParams["stadate_ge"] = from_datestr
    queryParams["stadate_le"] = to_datestr
    cheat_type = request.GET.get("cheat_type", "")
    if cheat_type != "":
        queryParams["cheat_type"] = cheat_type.encode("utf-8")
    nick_name = request.GET.get("nick_name", "")
    if nick_name != "":
        queryParams["nick_name"] = nick_name.encode("utf-8")
    deviceno = request.GET.get("deviceno", "")
    if deviceno != "":
        queryParams["deviceno"] = deviceno.encode("utf-8")


    resp = urllib2.urlopen(settings.ALS_DATA_APIS["cheat_monitor_data"] + "&" + urllib.urlencode(queryParams))
    content = resp.read()
    jsonData = json.loads(content)

    columns = jsonData["data"]["columns"];
    for i in xrange(len(columns)):
        columns[i]["name"] = columns[i]["name"].upper()

    if request.GET.get("for_export","")=="on" and (from_datestr!="" or to_datestr!=""):
        headers = [u"日期",u"userid",u"昵称",u"用户类型",u"作弊类型",u"操作系统",u"操作系统版本",u"设备号", u"邀请人id", u"渠道"]
        def genRows():
            for row in jsonData["data"]["datas"]:
                csvRow = []
                for column in columns:
                    val = row.get( column["name"], "")
                    if isinstance(val, int):
                        val = str(val)
                    csvRow.append( val )
                yield csvRow

        # 作弊监控导出数据记录日志
        bms_operation_log(request.user.id, "作弊监控导出数据", "")
        return outputCSV(genRows(), "cheat_monitor_data.csv", headers)

    paginator = SettablePaginator(jsonData["data"]["datas"], 30)
    paginator.num_pages = jsonData["data"]["totalPage"]
    paginator.count = jsonData["data"]["totalRecords"]
    #always get first page, because backend server will return the correct page
    pager = paginator.page(1)
    pager.number = page_index

    return TemplateResponse(request, "mobileapp/cheat_monitor.html", {"pager":pager, "columns":columns, "datas":jsonData["data"]["datas"], "from_datestr":from_datestr, "to_datestr":to_datestr, "cheat_type":cheat_type, "nick_name":nick_name})

@permission_required("article.junior_editor")
def user_last_active_time(request):
    if request.method == "POST":
        fileHandle = request.FILES.get("input_file", None)
        if fileHandle != None:
            data = xlrd.open_workbook(file_contents=fileHandle.read())
            table = data.sheets()[0]
            userIds = []
            for i in xrange(table.nrows):
                cols = table.row_values(i)
                userIds.append(str(int(cols[0])))

            userLastActiveTime = ["" for i in xrange(len(userIds)) ]
            user_last_active_time_api = settings.ALS_DATA_APIS["user_last_active_time"]
            try:
                resp = requests.get(user_last_active_time_api, params={"userids": ",".join(userIds)})
                respJson = json.loads(resp.text)
                if respJson["code"] == 0 :
                    headers = ['userid', u'最后活动时间']
                    for i in xrange(len(userIds)):
                        if userIds[i] in respJson["data"]:
                            userLastActiveTime[i] = respJson["data"][userIds[i]].split(".")[0]

                    rows = []
                    for i in xrange(len(userIds)):
                        rows.append([ userIds[i], userLastActiveTime[i] ])
                    return outputCSV(rows, "user_last_active_time.csv", headers)
            except Exception, e:
                print str(e)
    return TemplateResponse(request, "mobileapp/user_last_active.html")

@permission_required("article.junior_editor")
def wx_checkorder(request):
    #调用微信订单查询接口
    if request.POST["page"] == 'charge':
        charge = Charge.objects.get(id = request.POST["id"])
        paymentid = charge.paymentid
        id = charge.id
        if charge.type == 1:
            jcs_orderid = "C_"+str(paymentid)+"_"+str(id)
            data = {"out_trade_no": jcs_orderid}
            url = "http://192.168.10.232:8080"
            headers = {"X-Target": "PrreService.QueryModWx"}
            result = requests.post(url=url, data=json.dumps(data), headers=headers)

    if request.POST["page"] == 'purchase':
        purchase = Purchase.objects.get(id = request.POST["id"])
        paymentid = purchase.paymentid
        id = purchase.id
        if purchase.paytype == 1:
            jcs_orderid = "P_" + str(paymentid) + "_" + str(id)
            data = {"out_trade_no": jcs_orderid}
            url = "http://192.168.10.232:8080"
            headers = {"X-Target": "PrreService.QueryModWx"}
            result = requests.post(url=url, data=json.dumps(data), headers=headers)

    wx_payment = WxPayment.objects.get(paymentid=paymentid)
    trade_state = wx_payment.trade_state
    orderid = wx_payment.orderid

    # 查询订单状态记录日志
    bms_operation_log(request.user.id, "查询订单状态", "")

    return JsonResponse({"result": True, "message": '','trade_state':trade_state,'orderid':orderid})

@permission_required("admin.check_bms_log")
def bms_log_search(request):
    bmslogs = BmsLog.objects.all()

    from_datestr = request.GET.get("from_date", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d") + " 00:00:00")
    to_datestr = request.GET.get("to_date", (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d") + " 23:59:59")

    from_date = datetime.strptime(from_datestr, "%Y-%m-%d %H:%M:%S")
    to_date = datetime.strptime(to_datestr, "%Y-%m-%d %H:%M:%S")

    bmslogs = bmslogs.filter(cdate__gte=from_date)
    bmslogs = bmslogs.filter(cdate__lte=to_date)

    username = request.GET.get("username", "")
    if username != "":
        bmslogs = bmslogs.filter(operator__username=username)

    even_name = request.GET.get("even_name", "")
    if even_name != "":
        bmslogs = bmslogs.filter(even_name__contains=even_name)

    even_deatil= request.GET.get("even_deatil", "")
    if even_deatil != "":
        bmslogs = bmslogs.filter(even_message__contains=even_deatil)
    paginator = Paginator(bmslogs.order_by("-id"), 30)
    page_index = request.GET.get("page_index", 1)
    pager = paginator.page(page_index)

    return TemplateResponse(request, "mobileapp/bms_log_search.html", locals())

def present_search(request):

    orders = Order.objects.filter(ordertype=4,orderstatus=2)

    from_datestr = request.GET.get("from_date", (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d") + " 00:00:00")
    to_datestr = request.GET.get("to_date", datetime.now().strftime("%Y-%m-%d") + " 23:59:59")

    from_date = datetime.strptime(from_datestr, "%Y-%m-%d %H:%M:%S")
    to_date = datetime.strptime(to_datestr, "%Y-%m-%d %H:%M:%S")

    orders = orders.filter(createtime__gte=from_date)
    orders = orders.filter(createtime__lte=to_date)

    author_nick_name = request.GET.get("author_nick_name", "")
    if author_nick_name != "":
        orders = orders.filter(author__nick_name=author_nick_name)

    userid = request.GET.get("userid", "")
    if userid != "":
        orders = orders.filter(userid=userid)

    article_id = request.GET.get("article_id", "")
    if article_id != "":
        orders = orders.filter(product=article_id)

    appid = int(request.GET.get("appid", -1))
    if appid == 1:
        orders = orders.filter(appid='M')
    elif appid == 0:
        orders = orders.filter(appid='C')

    paginator = Paginator(orders.order_by("-id"), 30)
    page_index = request.GET.get("page_index", 1)
    pager = paginator.page(page_index)

    gold_sum = orders.aggregate(gold_sum=Sum('unitprice'))["gold_sum"]

    for order in pager.object_list:
        issue = OmnipotenceCardIssue.objects.get(id=order.discountid)
        order.card_value = issue.card.card_value

    return TemplateResponse(request, "mobileapp/present_article_list.html", locals())

def analyst_present_search(request):

    orders = Order.objects.filter(ordertype=4,orderstatus=2,author=request.user.analyst.id)

    from_datestr = request.GET.get("from_date", (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d") + " 00:00:00")
    to_datestr = request.GET.get("to_date", datetime.now().strftime("%Y-%m-%d") + " 23:59:59")

    from_date = datetime.strptime(from_datestr, "%Y-%m-%d %H:%M:%S")
    to_date = datetime.strptime(to_datestr, "%Y-%m-%d %H:%M:%S")

    orders = orders.filter(createtime__gte=from_date)
    orders = orders.filter(createtime__lte=to_date)

    paginator = Paginator(orders.order_by("-id"), 30)
    page_index = request.GET.get("page_index", 1)
    pager = paginator.page(page_index)

    return TemplateResponse(request, "mobileapp/analyst_present_article.html", locals())

def redis_operation(request):
    return TemplateResponse(request, "mobileapp/redis_operation_list.html", locals())

def del_article_redis(request):
    con = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0, password=REDIS_PASSOWRD)
    article_id = str(request.POST.get('article_id'))
    key = "article_"+article_id
    if con.get(key) == None:
        return JsonResponse({"result": False, "message": u"缓存不存在"})
    else:
        con.delete(key)
        return JsonResponse({"result": True, "message": u"缓存删除成功"})

def push_article_redis(request):
    con = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0, password=REDIS_PASSOWRD)
    push_article_id = str(request.POST.get('push_article_id'))
    con.publish("article_add", push_article_id)
    return JsonResponse({"result": True, "message": u"发布成功!"})

def del_user_redis(request):
    con = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0, password=REDIS_PASSOWRD)
    user_id = str(request.POST.get('user_id'))
    user_hash_name = "user.info."+user_id
    hexists = con.hexists(user_hash_name, 'msgnum')
    if hexists:
        con.hdel(user_hash_name, 'msgnum')
        return JsonResponse({"result": True, "message": u"缓存删除成功"})
    else:
        return JsonResponse({"result": False, "message": u"缓存不存在"})

def del_redis_hash(request):
    con = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0, password=REDIS_PASSOWRD)
    hash_name = str(request.POST.get('hash_name'))
    hash_key = str(request.POST.get('hash_key'))
    hexists = con.hexists(hash_name, hash_key)
    if hexists:
        con.hdel(hash_name,hash_key)
        return JsonResponse({"result": True, "message": u"缓存删除成功"})
    else:
        return JsonResponse({"result": False, "message": u"缓存不存在"})

def del_redis_zset(request):
    con = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0, password=REDIS_PASSOWRD)
    zset_name = str(request.POST.get('zset_name'))
    zset_score = request.POST.get('zset_score')
    zset_count = con.zcount(zset_name, zset_score, zset_score)
    if zset_count == 0:
        return JsonResponse({"result": False, "message": u"缓存不存在"})
    else:
        con.zremrangebyscore(zset_name,zset_score,zset_score)
        return JsonResponse({"result": True, "message": u"缓存删除成功"})

def update_redis_hash(request):
    con = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0, password=REDIS_PASSOWRD)
    update_hash_name = str(request.POST.get('update_hash_name'))
    update_hash_key = str(request.POST.get('update_hash_key'))
    update_hash_value = str(request.POST.get('update_hash_value'))
    hexists = con.hexists(update_hash_name, update_hash_key)
    if hexists:
        con.hset(update_hash_name,update_hash_key,update_hash_value)
        return JsonResponse({"result": True, "message": u"缓存更新成功"})
    else:
        return JsonResponse({"result": False, "message": u"HASH_KEY不存在"})

def batch_set_toppage_count(request):
    try:
        m_charge_count = request.POST["m_charge_count"]
        m_free_count = request.POST["m_free_count"]
        c_charge_count = request.POST["c_charge_count"]
        c_free_count = request.POST["c_free_count"]
        if m_charge_count != '':
            AnalystConfig.objects.filter(key="m_top_page_charge_max").update(value=m_charge_count)
        if m_free_count != '':
            AnalystConfig.objects.filter(key="m_top_page_free_max").update(value=m_free_count)
        if c_charge_count != '':
            AnalystConfig.objects.filter(key="c_top_page_charge_max").update(value=c_charge_count)
        if c_free_count != '':
            AnalystConfig.objects.filter(key="c_top_page_free_max").update(value=c_free_count)
        return JsonResponse({"result": True, "message": u"保存成功！"})
    except Exception as e:
        return JsonResponse({"result": False, "message": e.message})


@permission_required("admin.check_bms_log")
def traslate_balance(request):
    bmslogs = BmsLog.objects.all()

    from_datestr = request.GET.get("from_date", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d") + " 00:00:00")
    to_datestr = request.GET.get("to_date", (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d") + " 23:59:59")

    from_date = datetime.strptime(from_datestr, "%Y-%m-%d %H:%M:%S")
    to_date = datetime.strptime(to_datestr, "%Y-%m-%d %H:%M:%S")

    bmslogs = bmslogs.filter(cdate__gte=from_date)
    bmslogs = bmslogs.filter(cdate__lte=to_date)

    username = request.GET.get("username", "")
    if username != "":
        bmslogs = bmslogs.filter(operator__username=username)

    even_name = request.GET.get("even_name", "发布人工翻译文章")
    if even_name != "":
        bmslogs = bmslogs.filter(even_name__contains=even_name)

    even_deatil = request.GET.get("even_deatil", "")
    if even_deatil != "":
        bmslogs = bmslogs.filter(even_message__contains=even_deatil)

    articleids=[]
    for info in bmslogs:
        articleid=info.even_message
        id=articleid.split("ID")[1]
        articleids.append(id)

    alltext=[]
    articles=Article.objects.filter(id__in=articleids)

    for article in articles:
        alltext.append(article.digest_edit.strip().replace(' ', '').replace("\n\t",""))
        alltext.append(article.text_edit.strip().replace(' ', '').replace("\n\t",""))
    if request.GET.get("for_export","")=="on" and request.user.has_perm("mobileapp.export_purchase") and (from_datestr!="" or to_datestr!=""):


        # # 打开文档
        # document = Document()
        # paragraph = document.add_paragraph(u'添加了文本')
        # document.save('demo.docx')

        return outputdoc(alltext,'alltext.docx')



    paginator = Paginator(bmslogs.order_by("-id"), 30)
    page_index = request.GET.get("page_index", 1)
    pager = paginator.page(page_index)

    return TemplateResponse(request, "mobileapp/traslate_balance.html", locals())

