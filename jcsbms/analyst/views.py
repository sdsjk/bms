# coding:utf-8
'''
Created on 2015-11-18

@author: stone
'''
import json
from datetime import timedelta,datetime

import sys
from django.contrib.sites import requests
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Group
from django.db import transaction, connection
from django.http import JsonResponse,HttpResponseRedirect
from django.core.paginator import Paginator
from django.utils import timezone
from django.core import serializers


from jcs.views import bms_operation_log
from jcsbms import settings
from jcs.models import make_actionlog, get_system_config, ActionLog
from jcsbms.settings import SERVER_HOST, ZHUANQU_AUTH_EDITOR_IDS, ZHUANQU_AUTHOR_ID, ZOUDI_ID
from measured.models import MeasuredActivity, MeasuredActivityAnalyst, MeasuredActivityArticle
from mobileapp.models import AppUser, Portal, Purchase
from .models import Analyst,Apply,Priceplan,Analystlevel, AnalystGroup, LivePriceplan, analyst_post, GroupLivePrices, AnalystChannel, AnalystChannelRelation, AnalystPriceRange, \
    AnalystConfig
from .forms import UsernameForm,AnalystForm,AnalystinfoForm,ActivateAnalystForm,PriceplanForm,ApplyResultForm, \
    AnalystGroupForm, LivePriceplanForm

from jauth.models import create_user
from jcsbms.utils import formerror_cat, random_string, getClientIp, getUserAgent, is_xiaomishu, \
    push_article_examine_toppage, outputCSV, getLocalDateTime
from jcsbms.image_processing import crop_avatar
from article.models import Article,merge_lotteries,redis_article_post,add_articlekey, article_update_post, \
    article_add_post, merge_portaltags, ArticleLotteries, Article_Examine, ArticleLotteriesResult
from article.forms import ChargeableAnalystArticleForm,FreeAnalystArticleForm, ModifyAnalystArticleForm
from lottery.models import Lotteryentry,Lotterytype, Match, analyst_add_post
from jauth.models import send_notify
from actions import BanFree, BanLetter, BanChargeable, ChangePriceRange, BanChargeableCantonese, BanFreeCantonese, \
    CanChargeable, CanFree, CanChargeableCantonese, CanFreeCantonese, CanLetter
import logging

logger = logging.getLogger("django")

@permission_required("analyst.analyst_action")
def index(request):
    return HttpResponseRedirect("/laoshi/wodewenzhang/");

@permission_required("article.junior_editor")
def author_sousuo(request):

    analysts = Analyst.objects.filter(nick_name__contains = request.GET["nick_name"])
    authors = []
    for analyst in analysts:
        author_value = {}
        author_value["id"] = analyst.id
        author_value["nick_name"] = analyst.nick_name
        authors.append(author_value)

    return JsonResponse(authors,safe=False)

@permission_required("article.junior_editor")
def post_analyst(request):
    change_analyst_type = request.user.has_perm("analyst.change_analyst_type") #判断用户是否有修改讲师合作类型权限
    if request.method == "GET":
        channels = AnalystChannel.objects.all()
        if "id" not in request.GET:
            return TemplateResponse(request,"analyst/post_analyst.html", {'channels': channels})
        else:
            aid = request.GET["id"]
            analyst = Analyst.objects.get(id = aid)
            analyst_channel_relation = None
            try:
                analyst_channel_relation = AnalystChannelRelation.objects.get(analyst_id=aid, status=AnalystChannelRelation.VALID_STATUS)
            except AnalystChannelRelation.DoesNotExist, e:
                logger.warn("%s has no channel", analyst.nick_name)
            channel_id = analyst_channel_relation.channel_id if analyst_channel_relation else -1
            price_range = None
            analyst_configs = AnalystConfig.objects.filter(analyst_id = aid)
            configMap = {}
            for config in analyst_configs:
                configMap[config.key] = config.value
            try:
                price_range = AnalystPriceRange.objects.get(analyst=analyst, status=AnalystPriceRange.VALID_STATUS)
            except:
                logger.warn("%s has no price range", analyst.nick_name)
            return TemplateResponse(request,"analyst/post_analyst.html",{"analyst":analyst, 'channels':channels, 'channel_id': channel_id, 'price_range':price_range,
                                                                          "configMap": configMap,'change_analyst_type':change_analyst_type})
    elif request.method == "POST":
        if "id" not in request.POST:
            try:
                channel_id = int(request.POST.get('channel', -1))
                low_price = request.POST.get('low_price', '')
                high_price = request.POST.get('high_price', '')
                default_price = request.POST.get('default_price', '')
                low_price = -1 if low_price == '' else int(low_price)
                high_price = -1 if high_price == '' else int(high_price)
                default_price = None if default_price == '' else int(default_price)

                m_top_page_charge_max = request.POST.get('m_top_page_charge_max', str(Article.M_CHARGEABLE_TOPPAGE_MAX_COUNT))
                m_top_page_free_max = request.POST.get('m_top_page_free_max', str(Article.M_FREE_TOPPAGE_MAX_COUNT))
                c_top_page_charge_max = request.POST.get('c_top_page_charge_max', str(Article.C_CHARGEABLE_TOPPAGE_MAX_COUNT))
                c_top_page_free_max = request.POST.get('c_top_page_free_max',str(Article.C_FREE_TOPPAGE_MAX_COUNT))

                usernameform = UsernameForm(request.POST)
                analystform = AnalystForm(request.POST)

                with transaction.atomic():

                    if usernameform.is_valid() and analystform.is_valid():
                        user = create_user(usernameform.cleaned_data['username'],usernameform.cleaned_data['email'])

                        analystform.instance.user = user
                        analystform.save()
                        analystId = analystform.instance.id
                        if channel_id > 0 :
                            analyst_channel_relation = AnalystChannelRelation()
                            analyst_channel_relation.channel_id = channel_id
                            analyst_channel_relation.analyst_id = analystform.instance.id
                            analyst_channel_relation.op_id = request.user.id
                            analyst_channel_relation.save()
                        if analystform.instance.analyst_type == Analyst.ANALYST_TYPE_CHARGE and low_price > 0 and high_price > 0:
                            #收费老师才能自主定价
                            price_range = AnalystPriceRange(analyst=analystform.instance, low_price=low_price, high_price=high_price, default_price=default_price, op_id=request.user.id)
                            price_range.save()
                            ChangePriceRange().makeLog(request.user, price_range.id, u"添加定价%d-%d" % (low_price, high_price) )
                        analyst_post(analystform.instance)

                        user.groups.add(Group.objects.get(name="Analyst"))

                        AnalystConfig.objects.create(analyst_id = analystId, key = 'm_top_page_charge_max', value = m_top_page_charge_max)
                        AnalystConfig.objects.create(analyst_id = analystId, key = 'm_top_page_free_max', value = m_top_page_free_max)
                        AnalystConfig.objects.create(analyst_id = analystId, key = 'c_top_page_charge_max', value = c_top_page_charge_max)
                        AnalystConfig.objects.create(analyst_id = analystId, key = 'c_top_page_free_max', value = c_top_page_free_max)
                    else:
                        return JsonResponse({"result":False,"message":formerror_cat(analystform)+formerror_cat(usernameform)})

                analyst_add_post(analystform.instance)  # 推消息队列同步推推数据库
                # 新增讲师记录日志
                bms_operation_log(request.user.id, "新增讲师", "讲师ID%s" % str(Analyst.objects.all().latest('id').id))
                return JsonResponse({"result":True})

            except Exception as e:
                return JsonResponse({"result":False,"message":e.message})
        else:
            try:
                analyst = Analyst.objects.get(id=request.POST["id"])
                analystform = AnalystForm(request.POST,instance=analyst)
                channel_id = int(request.POST.get('channel', -1))

                low_price = request.POST.get('low_price', '')
                high_price = request.POST.get('high_price', '')
                default_price = request.POST.get('default_price', '')
                low_price = -1 if low_price == '' else int(low_price)
                high_price = -1 if high_price == '' else int(high_price)
                default_price = None if default_price == '' else int(default_price)

                m_top_page_charge_max = request.POST.get('m_top_page_charge_max', str(Article.M_CHARGEABLE_TOPPAGE_MAX_COUNT))
                m_top_page_free_max = request.POST.get('m_top_page_free_max', str(Article.M_FREE_TOPPAGE_MAX_COUNT))
                c_top_page_charge_max = request.POST.get('c_top_page_charge_max', str(Article.C_CHARGEABLE_TOPPAGE_MAX_COUNT))
                c_top_page_free_max = request.POST.get('c_top_page_free_max',str(Article.C_FREE_TOPPAGE_MAX_COUNT))

                if analystform.is_valid():
                    analystform.save()
                    #使之前的渠道关系无效
                    analyst_channel_relation = None
                    try:
                        analyst_channel_relation = AnalystChannelRelation.objects.get(analyst_id=analyst.id, status=AnalystChannelRelation.VALID_STATUS)
                    except AnalystChannelRelation.DoesNotExist, e:
                        logger.warn("%s has no channel", analyst.nick_name)
                    if analyst_channel_relation and analyst_channel_relation.channel_id != channel_id:
                        analyst_channel_relation.status = AnalystChannelRelation.INVALID_STATUS
                        analyst_channel_relation.op_id = request.user.id
                        analyst_channel_relation.save()
                    #建新的关系
                    if (analyst_channel_relation == None or analyst_channel_relation.channel_id != channel_id) and channel_id > 0 :
                        analyst_channel_relation = AnalystChannelRelation()
                        analyst_channel_relation.channel_id = channel_id
                        analyst_channel_relation.analyst_id = analyst.id
                        analyst_channel_relation.op_id = request.user.id
                        analyst_channel_relation.save()

                    #处理定价
                    price_range = None
                    try:
                        price_range = AnalystPriceRange.objects.get(analyst=analyst, status=AnalystPriceRange.VALID_STATUS)
                    except AnalystPriceRange.DoesNotExist, e:
                        logger.warn("%s has no price range", analyst.nick_name)
                    if price_range :
                        if analyst.analyst_type != Analyst.ANALYST_TYPE_CHARGE or low_price != price_range.low_price or high_price != price_range.high_price :
                            #收费变免费或者区间变动,都废掉旧定价
                            price_range.status = AnalystPriceRange.INVALID_STATUS
                            price_range.save()
                        if analyst.analyst_type == Analyst.ANALYST_TYPE_CHARGE and low_price >0 and high_price>0 and (low_price != price_range.low_price or high_price != price_range.high_price):
                            #新建定价
                            price_range = AnalystPriceRange(analyst=analystform.instance, low_price=low_price, high_price=high_price, default_price=default_price, op_id=request.user.id)
                            price_range.save()
                            ChangePriceRange().makeLog(request.user, price_range.id, u"更改定价%d-%d" % (low_price, high_price) )
                        elif analyst.analyst_type == Analyst.ANALYST_TYPE_CHARGE and low_price == price_range.low_price and high_price == price_range.high_price:
                            price_range.default_price = default_price
                            price_range.save()
                    else:
                        if analyst.analyst_type == Analyst.ANALYST_TYPE_CHARGE and low_price>0 and high_price>0:
                            #新建定价
                            price_range = AnalystPriceRange(analyst=analystform.instance, low_price=low_price, high_price=high_price, default_price=default_price, op_id=request.user.id)
                            price_range.save()
                            ChangePriceRange().makeLog(request.user, price_range.id, u"添加定价%d-%d" % (low_price, high_price) )

                    analyst_post(analystform.instance)

                    AnalystConfig.objects.filter(analyst_id = analyst.id, key = 'm_top_page_charge_max' ).delete()
                    AnalystConfig.objects.filter(analyst_id = analyst.id, key = 'm_top_page_free_max' ).delete()
                    AnalystConfig.objects.filter(analyst_id = analyst.id, key = 'c_top_page_charge_max' ).delete()
                    AnalystConfig.objects.filter(analyst_id = analyst.id, key = 'c_top_page_free_max' ).delete()
                    AnalystConfig.objects.create(analyst_id=analyst.id, key='m_top_page_charge_max',
                                                 value=m_top_page_charge_max)
                    AnalystConfig.objects.create(analyst_id=analyst.id, key='m_top_page_free_max',
                                                 value=m_top_page_free_max)
                    AnalystConfig.objects.create(analyst_id=analyst.id, key='c_top_page_charge_max',
                                                 value=c_top_page_charge_max)
                    AnalystConfig.objects.create(analyst_id=analyst.id, key='c_top_page_free_max',
                                                 value=c_top_page_free_max)
                    # 修改讲师记录日志
                    bms_operation_log(request.user.id, "修改讲师", "讲师ID%s" % str(request.POST["id"]))
                    return JsonResponse({"result":True})
                else:
                    return JsonResponse({"result":False,"message":formerror_cat(analystform)})

            except Exception as e:
                return JsonResponse({"result":False,"message":e.message})


@permission_required("article.junior_editor")
def analysts_winning_probability(request):
    from_datestr = request.GET.get("from_date", (timezone.now() - timedelta(days=2)).strftime("%Y-%m-%d 12:00:00"))
    from_date = timezone.make_aware(datetime.strptime(from_datestr, "%Y-%m-%d %H:%M:%S"))
    to_datestr = request.GET.get("to_date", (timezone.now() - timedelta(days=1)).strftime("%Y-%m-%d 11:59:59"))
    to_date = timezone.make_aware(datetime.strptime(to_datestr, "%Y-%m-%d %H:%M:%S"))

    #老师昵称
    author_word=request.GET.get("author_word","")
    sql_nickname = u""
    sql_articleid = u""
    try:
         author_word=int(author_word)
         sql_articleid = u"WHERE ttt1.author_id= '%s' " % (author_word)
    except :

        if author_word != u"":
            sql_nickname = u"WHERE ttt2.nick_name='%s'" % author_word


    #最近查询天数
    days=request.GET.get("days","0")
    if days!="0":
        try:
            day=int(days)
            from_datestr =  (timezone.now() - timedelta(days=(day+1))).strftime("%Y-%m-%d 12:00:00")
            from_date = timezone.make_aware(datetime.strptime(from_datestr, "%Y-%m-%d %H:%M:%S"))
            to_datestr = (timezone.now() - timedelta(days=1)).strftime("%Y-%m-%d 11:59:59")
            to_date = timezone.make_aware(datetime.strptime(to_datestr, "%Y-%m-%d %H:%M:%S"))

        except:
            print "转换异常"
    else:
        from_datestr = request.GET.get("from_date", (timezone.now() - timedelta(days=2)).strftime("%Y-%m-%d 12:00:00"))
        from_date = timezone.make_aware(datetime.strptime(from_datestr, "%Y-%m-%d %H:%M:%S"))
        to_datestr = request.GET.get("to_date", (timezone.now() - timedelta(days=1)).strftime("%Y-%m-%d 11:59:59"))
        to_date = timezone.make_aware(datetime.strptime(to_datestr, "%Y-%m-%d %H:%M:%S"))

    #是否收费
    chargeable=request.GET.get("chargeable","")
    if chargeable==u"0": #免费
        sql_chargeable=u"AND chargeable='f'"
    elif chargeable==u"1": #收费
        sql_chargeable = u"AND chargeable='t'"
    else:
        sql_chargeable = ""
    #标签
    portal_tag=request.GET.get("portal_tag","")
    if portal_tag==u"-1":
        sql_portal_tag=u"and a.playname<>'滚球'"
    elif portal_tag==u"-2":
        sql_portal_tag = u""
    elif portal_tag==u"":
        sql_portal_tag = u"and a.playname<>'滚球'"
    else:
        playName=u""
        if portal_tag==u"0":
            playName=u"亚盘"
        elif portal_tag==u"1":
            playName = u"竞彩"
        elif portal_tag==u"2":
            playName = u"滚球"
        elif portal_tag == u"3":
            playName = u"比分"
        elif portal_tag == u"4":
            playName = u"大小球"
        elif portal_tag == u"5":
            playName = u"大小分"
        elif portal_tag == u"6":
            playName = u"篮彩"
        elif portal_tag == u"7":
            playName = u"竞足串"
        elif portal_tag == u"8":
            playName = u"竞篮串"
        elif portal_tag == u"9":
            playName = u"福彩3D"
        sql_portal_tag=u"and a.playname= '%s' " %playName
    #联赛
    lian_sai = request.GET.get("lian_sai", u"")
    sql_lian_sai=u""
    if lian_sai==u"":
         sql_lian_sai=u""
    else:
        sql_lian_sai =u"and a.league LIKE  '%"+lian_sai +"%' "
    #语言
    language=request.GET.get("language","0")
    if language ==u"0":
        sql_language=u"and language='M'"
    elif language ==u"1":
        sql_language = u"and language='C'"
    else:
        sql_language=u""

    # 渠道
    analyst_channel=request.GET.get("analyst_channel","")
    analyst_channel_id=0
    if analyst_channel ==u"-1":
        sql_analyst_channel = u""
    elif analyst_channel ==u"":
        sql_analyst_channel=u""
    else:
        analyst_channel_id=int(analyst_channel)
        sql_analyst_channel=u"WHERE zyb03.channel_name= '%s' " %(AnalystChannel.objects.get(id=analyst_channel).channel_name)


    portalTags = Portal.objects.filter(can_selected=True)
    analystchannels = AnalystChannel.objects.all()
    cursor = connection.cursor()


    sql = u"""
    select tttt1.author_id as 讲师ID,tttt1.nick_name as 讲师,
    (tttt1.total_red +tttt1.total_hei+tttt1.total_zoushui) as 总数,
    tttt1.total_red as 红,
    tttt1.total_hei as 黑 ,
    tttt1.total_zoushui as 走水,
    round (((tttt1.total_red * 1.0)/(tttt1.total_red+tttt1.total_hei+ (CASE  WHEN  tttt1.total_red=0 AND tttt1.total_hei=0 THEN 1 ELSE 0 END)))*100,2)  as 胜率
    FROM
    (
                SELECT zyb02.* , zyb03.channel_name
            FROM
            (
            SELECT zyb.* ,zyb01.channel_id
                FROM
            (SELECT ttt1.*, ttt2.nick_name FROM
                  (
                            select tt1.author_id,
                                        sum(tt1.stat_red) total_red,
                                        sum(tt1.stat_hei) total_hei,
                                        sum(tt1.stat_zoushui) total_zoushui
                             FROM
                            (
                                select t1.*, t2.id, t2.author_id ,t2.chargeable  from
                                (
                                    SELECT
                                        a.article_id,
                                        sum(case when a.black_red_decide='红' then 1 else 0 END) stat_red,
                                        sum(case when a.black_red_decide='黑' then 1 else 0 END) stat_hei,
                                        sum(case when a.black_red_decide='走水' then 1 else 0 END) stat_zoushui

                                      from article_articlelotteries_result a
                                      where a.black_red_decide is not NULL and a.black_red_decide <> ''

                                                    %s
                                                    %s


                                                 GROUP BY a.article_id
                                ) t1
                                  left join (
                                  select id,date_added,author_id,chargeable,language from article_article
                                    WHERE
                                            1 = 1
                                        AND date_added >= '%s'
                                        AND date_added <='%s'
                                          %s
                                          %s
                                    )


                                  t2 on t1.article_id = t2.id
                            ) tt1 group by tt1.author_id
                  ) ttt1 left join analyst_analyst ttt2 on ttt1.author_id= ttt2.id

                        %s
                        %s
                )zyb
                    LEFT JOIN  analyst_channel_relation  zyb01 ON  zyb.author_id=zyb01.analyst_id
                    WHERE zyb01.status='0'OR zyb01.status ISNULL
            )zyb02
              LEFT JOIN analyst_channel zyb03 ON zyb02.channel_id=zyb03.id
              %s
    ) tttt1
     WHERE tttt1.author_id  IS NOT NULL
     ORDER  BY  胜率 DESC ;
    """% (sql_portal_tag,sql_lian_sai,from_date,to_date,sql_language,sql_chargeable, sql_nickname,sql_articleid,sql_analyst_channel)
    cursor.execute(sql)
    unionInfos=cursor.fetchall()

    if request.GET.get("for_export", "") == "on" and (from_datestr != "" or to_datestr != ""):

        headers = [u"老师ID", u"老师昵称", u"总料数", u"红", u"黑", u"走水", u"胜率%"]

        def genRows():
            for unionInfo in unionInfos:
                techerID=str(unionInfo[0])
                techerName=unionInfo[1]
                allarticle=str(unionInfo[2])
                red = str(unionInfo[3])
                black = str(unionInfo[4])
                zoushui=str(unionInfo[5])
                shenglv = str(unionInfo[6])
                yield [
                    techerID,
                    techerName,
                    allarticle,
                    red,
                    black,
                    zoushui,
                    shenglv
                ]

        return outputCSV(genRows(), "articles_red_black.csv", headers)


    return TemplateResponse(request, "analyst/teacher_probability.html",locals())



@permission_required("article.junior_editor")
def analysts_search(request):
    #判断用户是否有批量设置讲师首页次数权限
    can_batch_set_toppage_count = get_system_config('CAN_SET_TOPPAGE_COUNT')
    batch_set_toppage_count_user = str(request.user.id) in can_batch_set_toppage_count.split(',')

    analysts = Analyst.objects.all()
    analystchannels = AnalystChannel.objects.all()
    nick_name = request.GET.get("nick_name","")
    is_active = int(request.GET.get("is_active", -1))
    analyst_type = int(request.GET.get("analyst_type", -1))
    language = int(request.GET.get('language', -1))
    if "nick_name" in request.GET:
        analysts = analysts.filter(nick_name__contains = nick_name)
    if is_active >= 0 and is_active <= 1:
        analysts = analysts.filter(user__is_active=bool(is_active)).exclude(invisible=True)
    elif is_active ==2:
        analysts = analysts.filter(invisible=True)

    if analyst_type >= 0:
        analysts = analysts.filter(analyst_type = analyst_type)

    if language == 0:
        analysts = analysts.filter(is_mandarin_perm=True)
    elif language == 1:
        analysts = analysts.filter(is_cantonese_perm=True)

    #讲师渠道过滤
    analyst_channel_id = int(request.GET.get("analyst_channel",-1))
    if analyst_channel_id != -1:
        releations = AnalystChannelRelation.objects.filter(channel_id=analyst_channel_id, status=0)
        analysts = analysts.filter(id__in=releations.values('analyst_id'))

    # 时间设置
    from_datestr = request.GET.get("from_date", "2015-01-01")
    to_datestr = request.GET.get("to_date", (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
    from_date = datetime.strptime(from_datestr + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    to_date = datetime.strptime(to_datestr + " 23:59:59", "%Y-%m-%d %H:%M:%S")

    #获取当前时间
    datetime_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # paginator = Paginator(matches.filter(start_time__gte=from_date, start_time__lte=to_date).order_by("start_time"), 30)
    paginator = Paginator(analysts.filter(date_added__gte=from_date, date_added__lte=to_date).order_by("-last_modified"),30)
    page_index = int(request.GET.get("page_index",1))
    pager = paginator.page(page_index)

    return TemplateResponse(request,"analyst/analysts.html", locals())

@permission_required("article.operation_editor")
def apply_search(request):
    applies = Apply.objects.all()

    handle_status = True
    if request.GET.get("action","")!="" and "handle_status" not in request.GET:
        handle_status = False

    if handle_status == True:
        applies = applies.filter(handle_status=Apply.STATUS_UNHANDLED)

    paginator = Paginator(applies.order_by("-last_modified"),30)
    page_index = int(request.GET.get("page_index",1))
    pager = paginator.page(page_index)

    return TemplateResponse(request,"analyst/apply_list.html",{"pager":pager,"handle_status":handle_status})
@permission_required("article.junior_editor")
def deactivate_analyst(request):
    aid = request.POST["id"]
    analyst = Analyst.objects.get(id = aid)
    analyst.user.is_active=False
    analyst.user.save()
    # 讲师登录无效记录日志
    bms_operation_log(request.user.id, "讲师登录无效", "讲师ID%s" % str(analyst.id))
    return JsonResponse({"result":True})

@permission_required("article.junior_editor")
@transaction.atomic
def make_invisible(request):
    aid = request.POST["id"]
    analyst = Analyst.objects.get(id = aid)
    analyst.user.is_active=False
    analyst.user.save()
    analyst.invisible=True
    analyst.save()
    # 增加消息通知
    analyst_post(analyst)
    # 删除讲师记录日志
    bms_operation_log(request.user.id, "删除讲师", "讲师ID%s" % analyst.id)
    return JsonResponse({"result":True})


@permission_required("article.junior_editor")
def upload_avatar(request):
    if request.method == "GET":
        analyst = Analyst.objects.get(id = request.GET["id"])
        return TemplateResponse(request, "analyst/upload_avator.html",{"analyst":analyst})
    else:
        analyst = Analyst.objects.get(id = request.POST["aid"])
        userinfo = analyst.user.userinfo

        img_url = request.POST.get("img_url","")
        #user_dir = img_url[8:24]
        #if userinfo.user_dir != user_dir:
        #    return HttpResponse(json.dumps({"result":False,"message":u"非法数据操作已记录"}),content_type="application/json")
        size = (int(request.POST["x1"]),int(request.POST["y1"]),int(request.POST["x2"]),int(request.POST["y2"]))
        userinfo.avatar = crop_avatar(img_url,size)
        userinfo.save()
        #讲师头像推送redis
        analyst_post(analyst)
        # 修改讲师头像记录日志
        bms_operation_log(request.user.id, "修改讲师头像", "讲师ID%s" % str(request.POST["aid"]))
        return JsonResponse({"result":True})
@permission_required("analyst.analyst_action")
def my_articles(request):
    #print serializers.serialize("json",Portal.objects.all())

    analyst = request.user.analyst
    articles = Article.objects.filter(author=analyst)

    paginator = Paginator(articles.order_by("-id"),30)
    page_index = int(request.GET.get("page_index",1) )
    pager = paginator.page(page_index)

    # 文章删除理由
    for article in pager.object_list:
        action_logs = ActionLog.objects.filter(target_id=article.id,action='del_article').order_by('-id')
        if len(action_logs) > 0:
            article.memo = action_logs[0].memo
        else:
            article.memo = ''

    if page_index == 1:
        logger.info("analyst `%s` visit, ip:%s, ua:%s" % (analyst.nick_name, getClientIp(request), getUserAgent(request)))

    return TemplateResponse(request,"analyst/articles_list.html",{"pager":pager})

@permission_required("analyst.analyst_action")
def my_invited(request):

    analyst = request.user.analyst
    #ausers = AppUser.objects.filter(inviter=analyst)

    from_datestr = request.GET.get("from_date", (datetime.now() - timedelta(days=750)).strftime("%Y-%m-%d 00:00:00"))
    from_date = timezone.make_aware(datetime.strptime(from_datestr, "%Y-%m-%d %H:%M:%S"))
    # articles表的时间字段带时区,不用手动纠正
    #ausers = ausers.filter(cdate__gte=from_date)

    to_datestr = request.GET.get("to_date", datetime.now().strftime("%Y-%m-%d 23:59:59"))
    to_date = timezone.make_aware(datetime.strptime(to_datestr, "%Y-%m-%d %H:%M:%S"))
    #ausers = ausers.filter(cdate__lte=to_date)

    # 用户购买开始时间
    purchase_from_datestr = request.GET.get("purchase_from_date", (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00"))
    purchase_from_date = timezone.make_aware(datetime.strptime(purchase_from_datestr, "%Y-%m-%d %H:%M:%S"))

    purchase_to_datestr = request.GET.get("purchase_to_date", datetime.now().strftime("%Y-%m-%d 23:59:59"))
    purchase_to_date = timezone.make_aware(datetime.strptime(purchase_to_datestr, "%Y-%m-%d %H:%M:%S"))




    cursor = connection.cursor()
    sql = u"""
SELECT * from (SELECT
	u.userid,
	u.phonenumber,
	u.cdate,
	sum(case when DATE (P .cdate) >= '%s'   AND DATE (P .cdate) <= '%s' AND P .status = 1
	then (P .price / 100) else 0 end
	) price
FROM
	users u
LEFT JOIN purchase P ON u.userid = P .userid
WHERE
	u.inviteid=%s and
	DATE (u.cdate) >= '%s'
AND DATE (u.cdate) <= '%s'
GROUP BY
	u.userid
)t ORDER BY price desc;
    """%(purchase_from_date,purchase_to_date,analyst.id,from_date,to_date)

    cursor.execute(sql)
    unionInfos = cursor.fetchall()

    paginator = Paginator(unionInfos, 30)
    page_index = request.GET.get("page_index", 1)
    pager = paginator.page(page_index)




    #paginator = Paginator(ausers.order_by("-cdate"),30)

    #page_index = request.GET.get("page_index",1)

    #pager = paginator.page(page_index)

    return TemplateResponse(request,"analyst/my_invited.html",locals())

@permission_required("analyst.analyst_action")
def today_count(request):
    if is_xiaomishu(request.user.id):
        return JsonResponse({"m_left_count": Article.FREE_TOPPAGE_MAX_COUNT,
                          "m_max_count" : Article.FREE_TOPPAGE_MAX_COUNT,
                          "c_left_count": Article.FREE_TOPPAGE_MAX_COUNT,
                          "c_max_count": Article.FREE_TOPPAGE_MAX_COUNT,
                          "m_top_page_charge_max": Article.FREE_TOPPAGE_MAX_COUNT,
                         "m_top_page_free_max": Article.FREE_TOPPAGE_MAX_COUNT,
                         "c_top_page_charge_max": Article.FREE_TOPPAGE_MAX_COUNT,
                         "c_top_page_free_max": Article.FREE_TOPPAGE_MAX_COUNT
                         })
    analyst  = Analyst.objects.get(user=request.user)
    today0hour = datetime.now().strftime("%Y-%m-%d")
    today0hour = datetime.strptime(today0hour + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    today0hour = timezone.make_aware(today0hour)

    analyst_configs = AnalystConfig.objects.filter(analyst_id=analyst.id)
    configMap = {}
    for config in analyst_configs:
        configMap[config.key] = config.value

    m_top_page_charge_max = int(configMap.get('m_top_page_charge_max', Article.M_CHARGEABLE_TOPPAGE_MAX_COUNT))
    m_top_page_free_max = int(configMap.get('m_top_page_free_max', Article.M_FREE_TOPPAGE_MAX_COUNT))
    c_top_page_charge_max = int(configMap.get('c_top_page_charge_max', Article.C_CHARGEABLE_TOPPAGE_MAX_COUNT))
    c_top_page_free_max = int(configMap.get('c_top_page_free_max', Article.C_FREE_TOPPAGE_MAX_COUNT))

    articles = Article.objects.filter(author=analyst,date_added__gte=today0hour,is_toppage=True)
    if request.GET.get("chargeable","false") == "true":
        m_articles = articles.filter(chargeable = True, language = 'M')
        m_left_count = m_top_page_charge_max - m_articles.count()
        m_max_count = m_top_page_charge_max
        c_articles = articles.filter(chargeable = True, language = 'C')
        c_left_count = c_top_page_charge_max - c_articles.count()
        c_max_count = c_top_page_charge_max
    else:
        m_articles = articles.filter(chargeable = False, language = 'M')
        m_left_count = m_top_page_free_max - m_articles.count()
        m_max_count = m_top_page_free_max
        c_articles = articles.filter(chargeable = False, language = 'C')
        c_left_count = c_top_page_free_max - c_articles.count()
        c_max_count = c_top_page_free_max

    if "id" in request.GET:
        articles = articles.exclude(id=request.GET["id"])

    return JsonResponse({"m_left_count": m_left_count,
                          "m_max_count" : m_max_count,
                          "c_left_count": c_left_count,
                          "c_max_count": c_max_count,
                          "m_top_page_charge_max": m_top_page_charge_max,
                         "m_top_page_free_max": m_top_page_free_max,
                         "c_top_page_charge_max": c_top_page_charge_max,
                         "c_top_page_free_max": c_top_page_free_max
                         })


@permission_required("analyst.analyst_action")
def my_letters(request):
    pass

'''
老师发布文章
'''
@permission_required("analyst.analyst_action")
def post_article(request):
    analyst  = Analyst.objects.get(user=request.user)
    if request.method == "GET":
        if "id" in request.GET:
            article = Article.objects.get(id=request.GET["id"],author=analyst)
            #if article.end_time != None:
            #    if article.end_time - timedelta(hours=2) < timezone.now():
            #        return TemplateResponse(request, "analyst/article_info.html",{"article":article, "message": u"文章在赛事开始之后不可修改"})
            #else:
            return TemplateResponse(request, "analyst/article_info.html", {"article":article, "message": u"所有文章不可修改", "serverhost": SERVER_HOST})
            #return TemplateResponse(request, "analyst/post_article.html", {"article": article,"analyst":analyst})
        else:
            defaultPrice = 0
            price_range = None
            if analyst.analyst_type == Analyst.ANALYST_TYPE_CHARGE:
                form = ChargeableAnalystArticleForm(request.POST)
                if analyst.level.level_number == 4:
                    lotteryType = analyst.lottery_type.parent_id if analyst.lottery_type.parent_id is not None else analyst.lottery_type
                    defaultPrice = Priceplan.objects.get(lottery_type=lotteryType, analyst_level=analyst.level)
                    if defaultPrice != None:
                        defaultPrice = defaultPrice.cost
                try:
                    price_range = AnalystPriceRange.objects.get(analyst=analyst, status=AnalystPriceRange.VALID_STATUS)
                except AnalystPriceRange.DoesNotExist, e:
                    logger.warn("%s has no price range", analyst.nick_name)
                if defaultPrice == 0 and price_range != None:
                    defaultPrice = price_range.default_price
            elif analyst.analyst_type == Analyst.ANALYST_TYPE_FREE:
                form = FreeAnalystArticleForm(request.POST)
            aas = MeasuredActivityAnalyst.objects.filter(analyst = analyst)
            activitys = []
            for ii in aas:
                activitys.append(ii.activity)
            is_zhuanqu_editor = analyst.id in ZHUANQU_AUTH_EDITOR_IDS

            zoudi_id = ZOUDI_ID

            can_post_cantonese = AnalystConfig.objects.filter(analyst_id = analyst.id,
                                                              key='can_post_cantonese', value='1').count() > 0
            return TemplateResponse(request, "analyst/post_article.html", {"analyst":analyst,"form":form,
                                                                           "auto_unlock_hours": Article.AUTO_UNLOCK_HOURS,
                                                                           "free_toppage_max_count":Article.M_FREE_TOPPAGE_MAX_COUNT,
                                                                           "chargeable_toppage_max_count":Article.M_CHARGEABLE_TOPPAGE_MAX_COUNT,
                                                                           "default_price": defaultPrice, "price_range":price_range,
                                                                           "activitys": activitys,
                                                                           'is_zhuanqu_editor': is_zhuanqu_editor,
                                                                           'can_post_cantonese': can_post_cantonese,
                                                                           'zoudi_id' : zoudi_id})
    elif request.method == "POST":
        if "id" in request.POST:
            article = Article.objects.get(id=request.POST["id"],author=analyst)
            if article.end_time!=None:
                if article.end_time-timedelta(hours=2)<timezone.now():
                    return JsonResponse({"result": False, "message": u"文章在赛事开始之后不可修改"})
            else:
                return JsonResponse({"result": False, "message": u"无相关赛事文章不可修改"})

            form = ModifyAnalystArticleForm(request.POST,instance=article)
            if form.is_valid():
                form.save()

                lid_list = [ int(id) for id in request.POST.getlist("relLottery")]
                lotteries  = Lotteryentry.objects.filter(pk__in=lid_list)
                merge_lotteries(lotteries,article)
                matches = Match.objects.filter(lottery_entry__in=lid_list)
                match_list = []
                if matches != None:
                    match_list = [ x.getDictForCache() for x in matches]

                portal_ids = request.POST.getlist("portaltags")
                merge_portaltags(portal_ids, article, match_list)

                redis_article_post(article, match_list)
                article_update_post(article)
                return JsonResponse({"result":True})
            else:
                return JsonResponse({"result":False,"message":formerror_cat(form)})
        else:
            logger.info("analyst `%s` post a article, ip:%s, ua:%s" % (analyst.nick_name, getClientIp(request), getUserAgent(request) ) )


            if request.POST.get("language", "M") == "M":
                if request.POST.get("chargeable", "") == "":
                    if analyst.ban_free and timezone.now()< analyst.banfree_time:
                        return JsonResponse({"result": False, "message": u"您目前被禁止发布国语免费文章"})
                else:
                    if analyst.ban_chargeable and timezone.now() < analyst.banchargeable_time:
                        return JsonResponse({"result": False, "message": u"您目前被禁止发布国语收费文章"})
            elif request.POST.get("language", "M") == "C":
                if request.POST.get("chargeable", "") == "":
                    if analyst.ban_free_cantonese and timezone.now()< analyst.banfree_time_cantonese:
                        return JsonResponse({"result": False, "message": u"您目前被禁止发布粤语免费文章"})
                else:
                    if analyst.ban_chargeable_cantonese and timezone.now() < analyst.banchargeable_time_cantonese:
                        return JsonResponse({"result": False, "message": u"您目前被禁止发布粤语收费文章"})

            is_zhuanqu_editor = analyst.id in ZHUANQU_AUTH_EDITOR_IDS
            can_zhiding_author_ids = get_system_config('CAN_ZHIDING_AUTHOR_IDS')
            can_zhiding_author = str(analyst.id) in can_zhiding_author_ids.split(',')
            article = Article()

            if is_zhuanqu_editor:
                if Analyst.objects.filter(id=request.POST.get('origin_author')).count() > 0:
                    article.is_toppage = False
                    article.author_id = ZHUANQU_AUTHOR_ID
                    article.origin = request.POST.get('origin_author', '')
                else:
                    return JsonResponse({"result":False,"message":u"原老师编号不存在"})
            else:
                if request.POST.get("is_toppage", "") != "":
                    article.is_toppage = True
                article.author = Analyst.objects.get(user=request.user)
            #有指定讲师权限的用户
            if  can_zhiding_author:
                if request.POST.get("nick_name") != '':
                    if Analyst.objects.filter(nick_name=request.POST.get("nick_name")).count() > 0:
                        analyst_zhiding = Analyst.objects.get(nick_name=request.POST.get("nick_name"))
                        article.author_id = analyst_zhiding.id
                    else:
                        return JsonResponse({"result":False,"message":u"老师昵称不存在"})

            #增加接收语言的地方
            article.language = request.POST.get("language", "M")

            if analyst.analyst_type == Analyst.ANALYST_TYPE_CHARGE:
                form = ChargeableAnalystArticleForm(request.POST,instance=article)
            elif analyst.analyst_type == Analyst.ANALYST_TYPE_FREE:
                form = FreeAnalystArticleForm(request.POST,instance=article)
            if form.is_valid():
                with transaction.atomic():
                    form.save()
                    #先判断是否已经不能上首页，并且修改上首页的字段值，防止进其它几个缓存的数据有问题
                    if article.is_toppage:
                        if not article.toppage_check():
                            article.is_toppage = False
                            article.save()
                    lid_list = [ int(id) for id in request.POST.getlist("relLottery")]
                    lotteries  = Lotteryentry.objects.filter(pk__in=lid_list)
                    merge_lotteries(lotteries,article)
                    matches = Match.objects.filter(lottery_entry__in=lid_list)
                    match_list = []
                    if matches != None:
                        match_list = [ x.getDictForCache() for x in matches]

                    portal_ids = request.POST.getlist("portaltags")
                    #如果是专区老师发的文章,则将勾选的标签置为空
                    if is_zhuanqu_editor :
                        portal_ids = []
                    merge_portaltags(portal_ids, article, match_list)

                #判断如果文章上首页，则将该文章推送到article_examine表
                if article.is_toppage == True and article.language == 'M':
                    article_examine = article.article_examine if hasattr(article, 'article_examine') else Article_Examine()
                    article_examine.article_id = article.id
                    article_examine.status = '10'  # 待审核
                    article_examine.save()
                    #手机推送提醒
                    push_article_examine_toppage(article)

                if Article.objects.filter(id=article.id).count()==1:
                    add_articlekey(article)
                    redis_article_post(article, match_list)
                    article_add_post(article) #往消息队列扔消息
                    #add into activity
                    if request.POST.get("activityid", "") != "":
                        maa = MeasuredActivityArticle()
                        maa.article = article
                        maa.activity_id = request.POST.get("activityid")
                        maa.save()

                    return JsonResponse({"result":True})
            else:
                return JsonResponse({"result":False,"message":formerror_cat(form)})


@permission_required("analyst.analyst_action")
def analyst_info(request):
    if request.method == "GET":
        analyst = request.user.analyst
        return TemplateResponse(request, "analyst/analyst_info.html", {"analyst":analyst})
    elif request.method == "POST":
        analyst = request.user.analyst

        form = AnalystinfoForm(request.POST,instance=analyst)
        if form.is_valid():
            form.save()
            request.user.email = request.POST["email"]
            request.user.save()
            return JsonResponse({"result":True})
        else:
            return JsonResponse({"result":False,"message":formerror_cat(form)})
@permission_required("article.junior_editor")
def activate_analyst(request):
    if request.method == "GET":
        analyst = Analyst.objects.get(id = request.GET["id"])
        return TemplateResponse(request, "analyst/activate_analyst.html", {"analyst":analyst})
    elif request.method == "POST":
        form = ActivateAnalystForm(request.POST)
        if form.is_valid():
            analyst = Analyst.objects.get(id=request.POST["id"])
            analyst.user.username=form.cleaned_data['username']
            analyst.user.email= form.cleaned_data['email']
            analyst.mobile= form.cleaned_data['mobile']
            analyst.analyst_type= form.cleaned_data['analyst_type']
            password = random_string(8)
            analyst.user.set_password(password)

            analyst.user.is_active=True
            analyst.user.save()
            analyst.save()
            analyst.user.groups.add(Group.objects.get(name="Analyst"))
            send_notify(analyst.user.username,password,analyst.user.email)
            return JsonResponse({"result":True})
        else:
            return JsonResponse({"result":False,"message":formerror_cat(form)})

@permission_required("mobileapp.add_purchase", raise_exception=True)
def priceplan_search(request):

    paginator = Paginator(Priceplan.objects.all(),30)
    page_index = int(request.GET.get("page_index",1))
    pager = paginator.page(page_index)

    return TemplateResponse(request,"analyst/price_list.html",{"pager":pager})

@permission_required("article.operation_editor")
def post_priceplan(request):
    if request.method=="GET":
        return TemplateResponse(request,"analyst/post_price.html",{})
    elif request.method == "POST":
        price = Priceplan()
        price.analyst_level = Analystlevel.objects.get(id=request.POST["level"])
        price.lottery_type = Lotterytype.objects.get(id=request.POST["lottery_type"])
        form = PriceplanForm(request.POST,instance=price)
        if form.is_valid():
            try:
                form.save()
                return JsonResponse({"result":True})
            except Exception as e:
                return JsonResponse({"result":False,"message":e.message})
        else:
            return JsonResponse({"result":False,"message":formerror_cat(form)})
        
@permission_required("article.operation_editor")
def apply_info(request):
    if request.method == "GET" and "id" in request.GET:
        return TemplateResponse(request,"analyst/apply_info.html",{"apply":Apply.objects.get(id=request.GET["id"])})
    elif request.method == "POST" and "id" in request.POST:
        apply = Apply.objects.get(id= request.POST["id"])
        apply.handle_status=Apply.STATUS_HANDLED
        form = ApplyResultForm(request.POST,instance=apply)
        if form.is_valid():
            form.save()
            # 处理老师申请记录日志
            bms_operation_log(request.user.id, "处理老师申请", "")
            return JsonResponse({"result":True})
        else:
            return JsonResponse({"result":False,"message":formerror_cat(form)})

@permission_required("analyst.analyst_action")
def make_toppage(request):
    article = Article.objects.get(id=request.POST["id"],author=request.user.analyst)
    if article.is_toppage:
        return JsonResponse({"result": False, "message": u"该文目前就是收费文章"})


    if article.chargeable:
        if not article.toppage_check():
            return JsonResponse({"result": False, "message": u"收费文章今日上首页数已满"})
    else:
        if not article.toppage_check():
            return JsonResponse({"result": True, "message": u"免费文章今日上首页数已满"})

    article.is_toppage = True
    article.save()

    #上首页后推送article_examine表
    if article.language == 'M':
        article_examine = article.article_examine if hasattr(article, 'article_examine') else Article_Examine()
        article_examine.article_id = article.id
        article_examine.status = '10'  # 待审核
        article_examine.save()
        # 手机推送提醒
        push_article_examine_toppage(article)

    article_update_post(article)  # 文章上首页后推送redis
    lotteries = ArticleLotteries.objects.filter(article=article)
    matches = Match.objects.filter(lottery_entry__in=lotteries.values("lottery"))
    match_list = []
    if matches != None:
        match_list = [ x.getDictForCache() for x in matches]
    redis_article_post(article, match_list)
    return JsonResponse({"result": True})
@permission_required("analyst.analyst_action")
def cancel_toppage(request):
    article = Article.objects.get(id=request.POST["id"],author=request.user.analyst)
    article.is_toppage=False
    article.save()
    lotteries = ArticleLotteries.objects.filter(article=article)
    matches = Match.objects.filter(lottery_entry__in=lotteries.values("lottery"))
    match_list = []
    if matches != None:
        match_list = [ x.getDictForCache() for x in matches]
    redis_article_post(article, match_list)
    return JsonResponse({"result": True})

@permission_required("article.operation_editor")
def agroup_list(request):
    groups = AnalystGroup.objects.all()

    return TemplateResponse(request, "analyst/group_list.html", {"groups": groups})



@permission_required("article.operation_editor")
def post_agroup(request):
    if request.method=="GET":
        if "id" in request.GET:
            group = AnalystGroup.objects.get(id =request.GET["id"])
            return TemplateResponse(request, "analyst/post_group.html", {"group": group})
        else:
            return TemplateResponse(request, "analyst/post_group.html", {})
    elif request.method=="POST":

        if "id" in request.POST:
            group = AnalystGroup.objects.get(id= request.POST["id"])
            form = AnalystGroupForm(request.POST,instance=group)
            if form.is_valid():
                form.save()
                return JsonResponse({"result": True})
            else:
                return JsonResponse({"result": False, "message": form.errors.as_text()})
        else:
            #group = Group()
            group = AnalystGroup()
            form = AnalystGroupForm(request.POST, instance=group)
            if form.is_valid():
                form.save()
                return JsonResponse({"result": True})
            else:
                return JsonResponse({"result": False, "message": form.errors.as_text()})
@permission_required("article.operation_editor")
def group_prices(request):
    group = AnalystGroup.objects.get(id=request.GET["groupid"])
    price_list = []
    for price in group.liveprices.all():
        price_value = {}
        price_value["id"] = price.id
        price_value["name"] = str(price.cost)+u"元/"+price.period_name
        price_list.append(price_value)
    return JsonResponse(price_list,safe=False)
@permission_required("article.operation_editor")
def group_delprice(request):
    GroupLivePrices.objects.get(analyst_group_id=request.POST["groupid"],live_price_id=request.POST["priceid"]).delete()
    return JsonResponse({"result": True})
@permission_required("article.operation_editor")
def group_addprice(request):
    GroupLivePrices.objects.create(analyst_group_id=request.POST["groupid"],live_price_id=request.POST["priceid"])
    return JsonResponse({"result": True})

@permission_required("article.operation_editor")
def lpriceplan_list(request):
    paginator = Paginator(LivePriceplan.objects.all(),30)
    page_index = int(request.GET.get("page_index",1))
    pager = paginator.page(page_index)

    return TemplateResponse(request,"analyst/lprice_list.html",{"pager":pager})


@permission_required("article.operation_editor")
def post_lpriceplan(request):
    if request.method=="GET":
        if "id" not in request.GET:
            return TemplateResponse(request,"analyst/post_lprice.html")
    elif request.method == "POST":
        if "id" not in request.POST:
            form = LivePriceplanForm(request.POST)
            if form.is_valid():
                form.save()
                return JsonResponse({"result":True})
            else:

                return JsonResponse({"result":False,"message":form.errors.as_text()})

@permission_required("article.junior_editor")
def ban_action(request):
    action = request.POST["action"]
    analyst = Analyst.objects.get(id=request.POST["analyst"])
    if action == "ban_chargeable":
        analyst.ban_chargeable=True
        analyst.banchargeable_time= timezone.now()+timedelta(days=int(request.POST["ban_days"]))
        analyst.save()
        # 讲师禁发国语收费记录日志
        bms_operation_log(request.user.id, "讲师禁发国语收费文章", "讲师ID%s" % str(analyst.id))
        BanChargeable().makeLog(request.user, analyst.id, request.POST["ban_reason"])
        return JsonResponse({"result": True})

    elif action == "ban_free":
        analyst.ban_free = True
        analyst.banfree_time = timezone.now() + timedelta(days=int(request.POST["ban_days"]))
        analyst.save()
        # 讲师禁发国语免费记录日志
        bms_operation_log(request.user.id, "讲师禁发国语免费文章", "讲师ID%s" % str(analyst.id))
        BanFree().makeLog(request.user, analyst.id, request.POST["ban_reason"])
        return JsonResponse({"result": True})

    elif action == "ban_chargeable_cantonese":
        analyst.ban_chargeable_cantonese=True
        analyst.banchargeable_time_cantonese= timezone.now()+timedelta(days=int(request.POST["ban_days"]))
        analyst.save()
        # 讲师禁发粤语收费记录日志
        bms_operation_log(request.user.id, "讲师禁发粤语收费文章", "讲师ID%s" % str(analyst.id))
        BanChargeableCantonese().makeLog(request.user, analyst.id, request.POST["ban_reason"])
        return JsonResponse({"result": True})

    elif action == "ban_free_cantonese":
        analyst.ban_free_cantonese = True
        analyst.banfree_time_cantonese = timezone.now() + timedelta(days=int(request.POST["ban_days"]))
        analyst.save()
        # 讲师禁发粤语免费记录日志
        bms_operation_log(request.user.id, "讲师禁发粤语免费文章", "讲师ID%s" % str(analyst.id))
        BanFreeCantonese().makeLog(request.user, analyst.id, request.POST["ban_reason"])
        return JsonResponse({"result": True})

    elif action == "ban_letter":
        analyst.ban_letter = True
        analyst.banletter_time = timezone.now() + timedelta(days=int(request.POST["ban_days"]))
        analyst.save()
        # 讲师禁止发私信记录日志
        bms_operation_log(request.user.id, "讲师禁止发私信", "讲师ID%s" % str(analyst.id))
        BanLetter().makeLog(request.user, analyst.id, request.POST["ban_reason"])
        return JsonResponse({"result": True})

@permission_required("article.junior_editor")
def can_action(request):
    action = request.POST["action"]
    analyst = Analyst.objects.get(id=request.POST["analyst"])
    if action == "can_chargeable":
        analyst.ban_chargeable = False
        analyst.save()
        CanChargeable().makeLog(request.user, analyst.id, request.POST["ban_reason"])
        return JsonResponse({"result": True})
    elif action == "can_free":
        analyst.ban_free = False
        analyst.save()
        CanFree().makeLog(request.user, analyst.id, request.POST["ban_reason"])
        return JsonResponse({"result": True})
    elif action == "can_chargeable_cantonese":
        analyst.ban_chargeable_cantonese = False
        analyst.save()
        CanChargeableCantonese().makeLog(request.user, analyst.id, request.POST["ban_reason"])
        return JsonResponse({"result": True})
    elif action == "can_free_cantonese":
        analyst.ban_free_cantonese = False
        analyst.save()
        CanFreeCantonese().makeLog(request.user, analyst.id, request.POST["ban_reason"])
        return JsonResponse({"result": True})
    elif action == "can_letter":
        analyst.ban_letter = False
        analyst.save()
        CanLetter().makeLog(request.user, analyst.id, request.POST["ban_reason"])
        return JsonResponse({"result": True})
