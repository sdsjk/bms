# coding:utf-8
'''
Created on 2015-11-10

@author: stone
'''

import json
import time
import traceback
from datetime import timedelta,datetime

from django.contrib.auth.models import User
from django.template.response import TemplateResponse
from django.http import JsonResponse,HttpResponseRedirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required,permission_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count
from django_redis import get_redis_connection

from article.actions import DelArticle, RestoreArticle
from jcs.dfa import DFASearch
from jcs.views import bms_operation_log, article_time_line_cut, article_time_line_translate
from measured.models import MeasuredActivity, MeasuredActivityArticle
from .models import TaskResult,clean_text,create_psAnalyst,Article,ArticleLotteries,merge_lotteries,redis_article_post, \
    article_add_post, article_update_post, merge_portaltags, Channel, ArticleChannel, ArticleLotteriesResult, \
    Article_Examine, examine_toppage_upset, examine_toppage_downset,Articlethai, ArticlePortalTags
from .models import add_articlekey,redis_article_remove, redis_force_top, redis_cancel_top
from .forms import ResultForm,ArticleSyncForm,ArticleForm, ModifyAnalystArticleForm


from analyst.models import Analyst, AnalystChannel, AnalystChannelRelation
from lottery.models import Lotteryentry, Lotterytype, Match, Fixture, article_del_post
from jcsbms.utils import jsend_message,formerror_cat, outputCSV, getLocalDateTime, validatePageIndex, is_xiaomishu, \
    push_article_examine_toppage
from mobileapp.models import Portal, ExternalChannel

import logging
from django.utils.html import strip_tags
from mobileapp.actions import RefundRed
from jcs.models import ActionLog

logger = logging.getLogger("django")
# Create your views here.

@login_required
def index(request):
    return HttpResponseRedirect("/wenzhang/authorsearch/")
#翻译界面
@permission_required("article.junior_editor_translate")
def article_view_translate(request):
    textcontent = u""
    digestcontent = u""
    tansaltedigest=u""
    translate_text=u""
    if request.method =="GET":
        if "id" in request.GET:
            article = Article.objects.get(id=request.GET["id"])
            if article.invisible==True:
                textcontent=article.text
                digestcontent=article.digest
            else:
                thaiarticle = Articlethai.objects.get(id=request.GET["id"])
                textcontent = thaiarticle.text_untranslate
                digestcontent = thaiarticle.digest_untanslate
                tansaltedigest=article.digest
                translate_text=article.text

            if article.end_time != None:
                article.end_time = article.end_time-timedelta(hours=2)
            return TemplateResponse(request, "article/post_article_translate.html", {"article": article,"textcontent":textcontent,"digestcontent":digestcontent,"tansaltedigest":tansaltedigest,"translate_text":translate_text})
        else:
            return TemplateResponse(request, "article/post_article_translate.html")
    elif request.method == "POST":
        if "id" in request.POST:

            article = Article.objects.get(id=request.POST["id"])
            if article.invisible==True:
                thai_article= Articlethai()
                thai_article.id=request.POST["id"]
                untanslatedigest=article.digest
                untanslatetext=article.text
                thai_article.digest_untanslate=untanslatedigest
                thai_article.text_untranslate=untanslatetext
                thai_article.save()
            form = ModifyAnalystArticleForm(request.POST,instance=article)
            if form.is_valid():

                form.save()
                article.is_toppage = True
                article.save()
                lid_list = [ int(id) for id in request.POST.getlist("relLottery")]
                lotteries  = Lotteryentry.objects.filter(pk__in=lid_list)
                merge_lotteries(lotteries,article)
                matches = Match.objects.filter(lottery_entry__in=lid_list)
                match_list = []
                if matches != None:
                    match_list = [ x.getDictForCache() for x in matches]

                portal_ids = request.POST.getlist("portaltags")
                merge_portaltags(portal_ids,article, match_list)

                redis_article_post(article, match_list)
                article_update_post(article)
                if article.invisible==True:
                    article_add_post(article)

                article.invisible = False

                article.save()
                article_time_line_translate(article.id,datetime.now(),request.user.username,article.author_id)
                bms_operation_log(request.user.id,"文章翻译发布","文章ID%s"%article.id) #修改文章保存日志
                return JsonResponse({"result":True})
            else:
                return JsonResponse({"result":False,"message":formerror_cat(form)})
        else:
            article =Article()
            if request.POST.get("is_toppage", "") != "":
                article.is_toppage = True
            article.author = Analyst.objects.get(id=request.POST["author_id"])

            form = ArticleForm(request.POST,instance=article)
            if form.is_valid():
                with transaction.atomic():
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

                if Article.objects.filter(id=article.id).count()==1:
                    add_articlekey(form.instance)
                    redis_article_post(article, match_list)
                    article_add_post(article)
                    return JsonResponse({"result":True})
            else:
                return JsonResponse({"result":False,"message":formerror_cat(form)})


@permission_required("article.junior_editor_cut")
def article_view(request):
    if request.method =="GET":
        if "id" in request.GET:
            article = Article.objects.get(id=request.GET["id"])
            analysts =Analyst.objects.filter(invisible=False)
            if article.end_time != None:
                article.end_time = article.end_time-timedelta(hours=2)
            return TemplateResponse(request, "article/post_article.html", {"article": article,"analysts":analysts})
        else:
            return TemplateResponse(request, "article/post_article.html")
    elif request.method == "POST":
        if "id" in request.POST:
            article = Article.objects.get(id=request.POST["id"])
            article_author=article.author_id
            form = ModifyAnalystArticleForm(request.POST,instance=article)
            teacher=request.POST["teacher"]
            teacherinfo=Analyst.objects.filter(nick_name=teacher)
            if len(teacherinfo)<=0:
                return JsonResponse({"result": False, "message": "老师不存在"})
            else:
                authorid=teacherinfo[0].id
                article.author_id=authorid
                article.save()
            if form.is_valid():
                form.save()
                article.status = 1
                article.save()
                lid_list = [ int(id) for id in request.POST.getlist("relLottery")]
                lotteries  = Lotteryentry.objects.filter(pk__in=lid_list)
                merge_lotteries(lotteries,article)
                matches = Match.objects.filter(lottery_entry__in=lid_list)
                match_list = []
                if matches != None:
                    match_list = [ x.getDictForCache() for x in matches]

                portal_ids = request.POST.getlist("portaltags")
                merge_portaltags(portal_ids,article, match_list)

                # redis_article_post(article, match_list)
                # article_update_post(article)

                article_time_line_cut(article.id,article.date_added,datetime.now(),request.user.username,article_author)
                bms_operation_log(request.user.id,"文章审阅","文章ID%s"%article.id) #修改文章保存日志
                return JsonResponse({"result":True})
            else:
                return JsonResponse({"result":False,"message":formerror_cat(form)})
        else:
            article =Article()
            if request.POST.get("is_toppage", "") != "":
                article.is_toppage = True
            article.author = Analyst.objects.get(id=request.POST["author_id"])

            form = ArticleForm(request.POST,instance=article)
            if form.is_valid():
                with transaction.atomic():
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

                if Article.objects.filter(id=article.id).count()==1:
                    add_articlekey(form.instance)
                    redis_article_post(article, match_list)
                    # article_add_post(article)
                    return JsonResponse({"result":True})
            else:
                return JsonResponse({"result":False,"message":formerror_cat(form)})

@permission_required("article.junior_editor")
def result_view(request,rid):
    if request.method == "GET":

        result = TaskResult.objects.get(id=rid)
        #print(result.is_synced)
        result_dict = json.loads(result.result)
        result_value = {}
        result_value["updatetime"] = time.strftime("%Y-%m-%d %H:%M:%S",
                                                       time.localtime(float(result.updatetime)))
        result_value["title"] = result_dict.get("title", "")
        result_value["text"] = clean_text(result_dict.get("text", ""))
        result_value["author"] = result_dict.get("author", "")
        result_value["date_added"] = result_dict.get("date_added", "")
        result_value["url"] = result.url
        result_value["id"] = result.id
        if result.is_synced:
            result_value["is_synced"] = result.is_synced

        return TemplateResponse(request, "article/post_result.html", {"result": result_value})
    elif request.method == "POST":

        form = ResultForm(request.POST)
        if form.is_valid():
            result = TaskResult.objects.get(id=request.POST["taskid"])
            result_value = json.loads(result.result)
            result_value["title"] = form.cleaned_data['title']
            result_value["text"] = form.cleaned_data['text']

            result.result = json.dumps(result_value).decode("utf-8")

            TaskResult.objects(id=request.POST["taskid"]).update_one(set__result=json.dumps(result_value).decode("utf-8"))
            return JsonResponse({"result":True})
        else:
            return JsonResponse({"result":False,"message":formerror_cat(form)})

@permission_required("article.junior_editor")
def del_result(request):
    TaskResult.objects(id=request.POST["id"]).delete()
    return JsonResponse({"result":True})

@permission_required("article.junior_editor_cut")
def del_article(request):
    article = Article.objects.get(id=request.POST["id"])
    article.delete()
    # try:
    #     with transaction.atomic():
    #         redis_article_remove(article)
    #         merge_portaltags([],article, [])
    #         if article.is_toppage == True and article.language == "M":
    #             article_examine = article.article_examine if hasattr(article, 'article_examine') else Article_Examine()
    #             article_examine.examine_user_id = request.user.id
    #             article_examine.examine_time = datetime.now()
    #             article_examine.examine_opinion = ''
    #             article_examine.status = '90'  # 审核不通过
    #             article_examine.save()
    #             # 修改redis
    #             examine_toppage_downset(article_examine)
    #         article.save()
    #         bms_operation_log(request.user.id, "删除文章", "文章ID%s"%article.id)
    #         # 删除文章推送消息队列
    #         article_del_post(article)
    #         # 删除文章理由
    #         del_reason = ' '.join(request.POST.getlist('reason'))
    #         del_reason__custom = request.POST.get('reason_custom')
    #         memo = del_reason + ' ' + del_reason__custom
    #         DelArticle().makeLog(request.user, request.POST["id"], memo)
    #         return JsonResponse({"result":True})
    # except Exception, e:
    #     logger.error("del article %d error %s", article.id, e)
    return JsonResponse({"result":True, "message": "sucess"})

@permission_required("article.junior_editor_cut")
def alldel_article(request):
    allarticle=request.POST["m1"]

    Article.objects.extra(where=['id IN ('+allarticle+')']).delete()

    # alllist=allarticle.split(",")
    # for i in alllist:
    #     if i!="" and Article.objects.filter(id=i).count()>0:
    #         article = Article.objects.get(id)
    #         article.delete()
    # article.save()
    bms_operation_log(request.user.id, "删除文章", "批量删除文章")
    return JsonResponse({"result":True, "message": "sucess"})


@permission_required("article.junior_editor_cut")
def del_article_shouye(request):
    article = Article.objects.get(id=request.POST["id"])
    article.invisible=True
    article.save()
    # article.delete()
    try:
        with transaction.atomic():
            redis_article_remove(article)
            merge_portaltags([],article, [])
            # if article.is_toppage == True and article.language == "M":
            #     article_examine = article.article_examine if hasattr(article, 'article_examine') else Article_Examine()
            #     article_examine.examine_user_id = request.user.id
            #     article_examine.examine_time = datetime.now()
            #     article_examine.examine_opinion = ''
            #     article_examine.status = '90'  # 审核不通过
            #     article_examine.save()
            #     # 修改redis
            #     examine_toppage_downset(article_examine)
            article.save()
            bms_operation_log(request.user.id, "删除文章", "文章ID%s"%article.id)
            # 删除文章推送消息队列
            article_del_post(article)
            # 删除文章理由
            del_reason = ' '.join(request.POST.getlist('reason'))
            del_reason__custom = request.POST.get('reason_custom')
            memo = del_reason + ' ' + del_reason__custom
            DelArticle().makeLog(request.user, request.POST["id"], memo)
            return JsonResponse({"result":True})
    except Exception, e:
        logger.error("del article %d error %s", article.id, e)
    return JsonResponse({"result":True, "message": "sucess"})
@permission_required("article.junior_editor")
def recover_article(request):
    article = Article.objects.get(id=request.POST["id"])
    article.invisible = False
    try:
        with transaction.atomic():
            redis_article_post(article, [])
            article_add_post(article)
            article.save()
            RestoreArticle().makeLog(request.user, request.POST['id'])
            return JsonResponse({"result":True})
    except Exception, e:
        logger.error("recover article %d error %s", article.id, e)
    return JsonResponse({"result":False, "message": str(e)})

@permission_required("article.junior_editor")
def make_top(request):
    article = Article.objects.get(id=request.POST["id"])
    article.istop=True
    article.top_order = 1
    article.top_time = timezone.now()+ timedelta(hours=24)
    article.save()
    bms_operation_log(request.user.id, "置顶", "文章ID%s" % article.id) #文章置顶记录日志
    if not article.is_toppage:
        #编辑强制置顶不在首页的文章
        redis_force_top(article)
    return JsonResponse({"result":True})

@permission_required("article.junior_editor")
def cancel_top(request):
    article = Article.objects.get(id=request.POST["id"])
    article.istop=False
    article.top_time = timezone.now()
    article.save()
    if not article.is_toppage:
        #这种不在首页的置顶文章是编辑操作的
        redis_cancel_top(article)
    return JsonResponse({"result":True})

@permission_required("article.junior_editor")
def modify_article_top_order(request):
    if request.method == 'POST':
        article_id = request.POST.get("article_id")
        order = request.POST.get("order")
        order = int(order) if order.isdigit() else None
        if order != None and order > 0:
            article = Article.objects.get(id=article_id)
            article.top_order = order
            article.save()
            return JsonResponse({"result": True, "message": "更新成功"})
        else:
            return JsonResponse({"result": False, "message": "序号不合法!"})
    return JsonResponse({"result": False, "message": "invalid request!"})

@permission_required("article.junior_editor")
def make_toppage(request):
    article = Article.objects.get(id=request.POST["id"])
    if article.is_toppage:
        return JsonResponse({"result": False, "message": u"该文目前就是首页文章"})

    if not article.toppage_check():
        if article.chargeable:
            return JsonResponse({"result": False, "message":u"该老师收费文章今日上首页数已满"})
        else:
            return JsonResponse({"result": True, "message":u"该老师免费文章今日上首页数已满"})


    article.is_toppage = True
    article.save()
    bms_operation_log(request.user.id, "上首页", "文章ID%s" % article.id) #文章上首页记录日志
    # 上首页成功后，则将该文章推送到article_examine表
    if article.language == 'M':
        article_examine = article.article_examine if hasattr(article, 'article_examine') else Article_Examine()
        article_examine.article = article
        article_examine.examine_user_id = request.user.id
        article_examine.examine_time = datetime.now()
        article_examine.examine_opinion = ''
        article_examine.status = '20'  # 审核通过
        article_examine.save()
        push_article_examine_toppage(article) # 手机推送提醒
        examine_toppage_upset(article_examine) # 修改redis

    article_update_post(article) #文章上首页后推送redis

    lotteries = ArticleLotteries.objects.filter(article=article)
    matches = Match.objects.filter(lottery_entry__in=lotteries.values("lottery"))
    match_list = []
    if matches != None:
        match_list = [ x.getDictForCache() for x in matches]
    redis_article_post(article, match_list)
    return JsonResponse({"result": True})

@permission_required("article.junior_editor")
def cancel_toppage(request):
    article = Article.objects.get(id=request.POST["id"])
    article.is_toppage=False
    article.save()

    # 国语文章下首页成功后，更新Article_Examine表
    # if article.language == "M":
    #     article_examine = Article_Examine.objects.get(article_id=article.id)
    #     article_examine.examine_user_id = request.user.id
    #     article_examine.examine_time = datetime.now()
    #     article_examine.examine_opinion = ''
    #     article_examine.status = '90'  # 审核不通过
    #     article_examine.save()
    #     examine_toppage_downset(article_examine) # 修改redis

    article_update_post(article) #文章取消上首页后推送redis
    lotteries = ArticleLotteries.objects.filter(article=article)
    matches = Match.objects.filter(lottery_entry__in=lotteries.values("lottery"))
    match_list = []
    if matches != None:
        match_list = [ x.getDictForCache() for x in matches]
    redis_article_post(article, match_list)
    return JsonResponse({"result": True})

@permission_required("article.junior_editor")
def author_search(request):

    if request.GET.get("from_date","") =="":
        now_date = timezone.now()
        yesterday = now_date - timedelta(days=1)
        date_str = now_date.strftime("%Y-%m-%d")
        from_datestr = yesterday.strftime("%Y-%m-%d")
        to_datestr =date_str
        from_date = time.mktime(time.strptime(from_datestr+" 00:00:00","%Y-%m-%d %H:%M:%S"))
        to_date = time.mktime(time.strptime(to_datestr+" 23:59:59","%Y-%m-%d %H:%M:%S",))

    else:
        from_datestr = request.GET.get("from_date")
        to_datestr =request.GET.get("to_date")
        from_date = time.mktime(time.strptime(request.GET.get("from_date")+" 00:00:00","%Y-%m-%d %H:%M:%S"))
        to_date = time.mktime(time.strptime(request.GET.get("to_date")+" 23:59:59","%Y-%m-%d %H:%M:%S"))

    aword=request.GET.get("author_word","")
    title=request.GET.get("title","")

    results = TaskResult.objects(author__contains=aword,title__contains=title,updatetime__gte=from_date, updatetime__lte=to_date,is_synced__exists=False).order_by("-updatetime")

    paginator = Paginator(results,30)
    page_index = int(request.GET.get("page_index",1) )
    page_index = validatePageIndex(page_index, paginator.num_pages)
    pager = paginator.page(page_index)


    result_list=[]
    for result in pager.object_list:
        result_value={}
        result_dict = json.loads(result.result)
        result_value["updatetime"] = time.strftime("%Y-%m-%d %H:%M:%S",
                                               time.localtime(float(result.updatetime)))
        result_value["title"] = result_dict.get("title", "")
        #print(result_dict.get("text", ""))
        if result_dict.get("text", "")==None or result_value["title"]==None:
            result_value["title"]=u"请提醒爬虫编写人员:此爬虫出故障了!!!!"
        else:
            result_value["text"] = result_dict.get("text", "").replace('<i style="display:none;" class="W_loading"/></li>',"")
        result_value["author"] = result_dict.get("author", "")
        result_value["date_added"] = result_dict.get("date_added", "")
        result_value["url"] = result.url
        result_value["id"] = result.id
        result_value["project"] = result.project
        result_list.append(result_value)

    return TemplateResponse(request,"article/search_results.html",{"results": result_list,"pager":pager,"from_date":from_datestr,"to_date":to_datestr})

@permission_required("article.junior_editor_translate")
def article_translate(request):
    articles = Article.objects.all()
    #可翻译的文章
    articles = articles.filter(status=1)
    userid = request.user.id
    aword=request.GET.get("author_word","")
    if aword !="":
        articles = articles.filter(author__nick_name__contains=aword)

    #讲师渠道过滤
    analystchannels = AnalystChannel.objects.all()
    analyst_channel_id = int(request.GET.get("analyst_channel",-1))
    if analyst_channel_id != -1:
        releations = AnalystChannelRelation.objects.filter(channel_id=analyst_channel_id, status=0)
        articles = articles.filter(author_id__in=releations.values('analyst_id'))



    author_type = int(request.GET.get("author_type", -1))
    if author_type >= 0:
        articles = articles.filter(author__analyst_type=author_type)

    from_datestr = request.GET.get("from_date", (datetime.now()-timedelta(days=7)).strftime("%Y-%m-%d 00:00:00") )
    from_date = timezone.make_aware(datetime.strptime(from_datestr,"%Y-%m-%d %H:%M:%S"))
    #articles表的时间字段带时区,不用手动纠正
    articles = articles.filter(date_added__gte=from_date)

    to_datestr =request.GET.get("to_date", datetime.now().strftime("%Y-%m-%d 23:59:59"))
    to_date = timezone.make_aware(datetime.strptime(to_datestr,"%Y-%m-%d %H:%M:%S"))
    articles = articles.filter(date_added__lte=to_date)

    articleid = request.GET.get("articleid","")
    if articleid !="":
        articles = articles.filter(id=articleid)

    is_toppage = int(request.GET.get("is_toppage", "-1"))
    if is_toppage >= 0:
        articles = articles.filter(is_toppage  =bool(is_toppage))

    invisible = int(request.GET.get("invisible", "1"))
    if invisible >= 0:
        articles = articles.filter(invisible=bool(invisible))

    chargeable = int(request.GET.get("chargeable", "-1"))
    if chargeable >= 0:
        articles = articles.filter(chargeable=bool(chargeable))
    key_word = request.GET.get("key_word","")
    if key_word != "":
        words = key_word.strip().split(" ")
        conds = Q()
        for word in words:
            conds |= Q(text__contains=word)
        articles = articles.filter(conds)

    match_related = int(request.GET.get("match_related", -1))
    if match_related == 0 :
        articles = articles.filter(lotteries=None)
    elif match_related == 1:
        articles = articles.exclude(lotteries=None)

    portal_tag = int(request.GET.get("portal_tag", -1))
    if portal_tag == 0:
        #无标签
        articles = articles.filter(portal_tags=None)
    elif portal_tag > 0:
        articles = articles.filter(portal_tags=portal_tag)

    refund_red = int(request.GET.get("refund_red", -1))
    if refund_red == 0:
        refund_red_logs = ActionLog.objects.filter(action=RefundRed.action).values("target_id")
        article_ids = [ x["target_id"] for x in refund_red_logs ]
        articles = articles.exclude(id__in=article_ids)
    elif refund_red == 1:
        refund_red_logs = ActionLog.objects.filter(action=RefundRed.action).values("target_id")
        article_ids = [ x["target_id"] for x in refund_red_logs ]
        articles = articles.filter(id__in=article_ids)

    language = int(request.GET.get("language", -1))
    if language == 1: #国语
        articles = articles.filter(language = 'M')
    elif language == 0: #粤语
        articles = articles.filter(language = 'C')

    #红黑结果数量
    articles = articles.annotate(articlelotteriesresult_count=Count('articlelotteriesresult'))
    #红黑搜索过滤
    black_red_count = int(request.GET.get("black_red_count", -1))
    if black_red_count == 1:
        articles = articles.filter(articlelotteriesresult_count__gt = 0)
    elif black_red_count == 0:
        articles = articles.filter(articlelotteriesresult_count__lte = 0)

    #所有活动
    measuredactivities = MeasuredActivity.objects.all()
    #活动搜索过滤
    activity_id = int(request.GET.get("article_activity", -1))
    if activity_id > 0:
        articles = articles.filter(measuredactivityarticle__activity_id=activity_id)

    #发布类型
    article_type = int(request.GET.get("article_type", -1))
    if article_type > 0:
        articles = articles.filter(type=article_type)
    if request.GET.get("for_export","")=="on" and (from_datestr!="" or to_datestr!=""):

        headers = [u"文章ID",u"上首页",u"概要",u"作者",u"合作类型",u"收费",u"语言", u"创建时间",u"最后修改"]
        def genRows():
            analystTypeNames = [u"收费", u"免费", u"代发"]
            for article in articles.order_by("-date_added"):
                chargeable_words = ''
                if article.chargeable:
                    chargeable_words = str(article.price) if article.price else u'是'
                else:
                    chargeable_words = u'否'

                yield       [str(article.id),
                             u"是" if article.is_toppage else u"否",
                             "None" if article.title == None else article.title,
                             article.author.nick_name,
                             analystTypeNames[article.author.analyst_type],
                             chargeable_words,
                             u"国语" if article.language == 'M' else u'粤语',
                             getLocalDateTime(article.date_added).strftime("%Y-%m-%d %H:%M:%S"),
                             getLocalDateTime(article.last_modified).strftime("%Y-%m-%d %H:%M:%S") ]

        bms_operation_log(request.user.id, "文章导出", "") #文章导出记录日志

        return outputCSV(genRows(), "articles.csv", headers)

    # articles = articles.exclude(istop=True, top_time__gte=timezone.now())
    paginator = Paginator(articles.order_by("date_added"), 30)
    page_index = request.GET.get("page_index",1)
    pager = paginator.page(page_index)

    # 文章删除理由
    for article in pager.object_list:
        action_logs = ActionLog.objects.filter(target_id=article.id, action='del_article').order_by('-id')
        if len(action_logs) > 0:
            article.memo = action_logs[0].memo
        else:
            article.memo = ''

    #文章讲师渠道
    for article in pager.object_list:
        analystchannelrelation = AnalystChannelRelation.objects.filter(analyst_id=article.author_id, status=0)
        if len(analystchannelrelation) > 0:
            analystchannel = AnalystChannel.objects.filter(id=analystchannelrelation[0].channel_id)
            article.channel = analystchannel[0].channel_name
        else:
            article.channel = ''


    digest_words = 9
    red_articles = {}
    for article in pager.object_list :
        article.tags = ",".join([x.name for x in article.portal_tags.all()])
        if article.digest != None:
            article.digest = article.digest[:digest_words]
        else:
            article.digest = ''
        #     article.digest = ' '.join(strip_tags(article.text)[:digest_words].split())
        #是否小秘书收费文章
        if article.chargeable and is_xiaomishu(article.author.user.id):
            article.is_xms = True
            #记录红单文章
            red_articles[ article.id ] = article
        article.istop = article.top_time > timezone.now() if article.top_time != None else False

    if refund_red in [0, 1] :
        #已确定是否红单就不用查库了
        for article_id, article in red_articles.iteritems():
            article.has_refund_red = True
    else:
        #查询是否有红单退款记录
        refund_red_logs = ActionLog.objects.filter(action=RefundRed.action, target_id__in=red_articles)
        for refund_red_log in refund_red_logs:
            article = red_articles.get(refund_red_log.target_id)
            article.has_refund_red = True

    portalTags = Portal.objects.filter(can_selected=True)

    # #查询置顶文章
    # top_articles = Article.objects.filter(istop=True).filter(top_time__gte=timezone.now()).order_by("top_order", "-top_time")
    # for article in top_articles:
    #     article.tags = ",".join([x.name for x in article.portal_tags.all()])
    #     if article.chargeable and article.digest != None:
    #         article.digest = article.digest[:digest_words]
    #     else:
    #         article.digest = ' '.join(strip_tags(article.text)[:digest_words].split())

    return TemplateResponse(request,"article/articles_list_translate.html",locals())




@permission_required("article.junior_editor_cut")
def article_search(request):
    '''
    for user  in User.objects.all():
        if (not hasattr(user,"analyst")) and  (not user.username.isdecimal() ):
            print user.groups.all()
            print user.username
    '''
    articles = Article.objects.all()
    userid = request.user.id
    aword=request.GET.get("author_word","")
    if aword !="":
        articles = articles.filter(author__nick_name__contains=aword)

    #讲师渠道过滤
    analystchannels = AnalystChannel.objects.all()
    analyst_channel_id = int(request.GET.get("analyst_channel",-1))
    if analyst_channel_id != -1:
        releations = AnalystChannelRelation.objects.filter(channel_id=analyst_channel_id, status=0)
        articles = articles.filter(author_id__in=releations.values('analyst_id'))



    author_type = int(request.GET.get("author_type", -1))
    if author_type >= 0:
        articles = articles.filter(author__analyst_type=author_type)

    from_datestr = request.GET.get("from_date", (datetime.now()-timedelta(days=7)).strftime("%Y-%m-%d 00:00:00") )
    from_date = timezone.make_aware(datetime.strptime(from_datestr,"%Y-%m-%d %H:%M:%S"))
    #articles表的时间字段带时区,不用手动纠正
    articles = articles.filter(date_added__gte=from_date)

    to_datestr =request.GET.get("to_date", datetime.now().strftime("%Y-%m-%d 23:59:59"))
    to_date = timezone.make_aware(datetime.strptime(to_datestr,"%Y-%m-%d %H:%M:%S"))
    articles = articles.filter(date_added__lte=to_date)

    articleid = request.GET.get("articleid","")
    if articleid !="":
        articles = articles.filter(id=articleid)

    is_toppage = int(request.GET.get("is_toppage", "-1"))
    if is_toppage >= 0:
        articles = articles.filter(is_toppage  =bool(is_toppage))

    invisible = int(request.GET.get("invisible", "1"))
    if invisible >= 0:
        articles = articles.filter(invisible=bool(invisible))

    chargeable = int(request.GET.get("chargeable", "-1"))
    if chargeable >= 0:
        articles = articles.filter(chargeable=bool(chargeable))
    key_word = request.GET.get("key_word","")
    if key_word != "":
        words = key_word.strip().split(" ")
        conds = Q()
        for word in words:
            conds |= Q(text__contains=word)
        articles = articles.filter(conds)

    match_related = int(request.GET.get("match_related", -1))
    if match_related == 0 :
        articles = articles.filter(lotteries=None)
    elif match_related == 1:
        articles = articles.exclude(lotteries=None)

    portal_tag = int(request.GET.get("portal_tag", -1))
    if portal_tag == 0:
        #无标签
        articles = articles.filter(portal_tags=None)
    elif portal_tag > 0:
        articles = articles.filter(portal_tags=portal_tag)

    refund_red = int(request.GET.get("refund_red", -1))
    if refund_red == 0:
        refund_red_logs = ActionLog.objects.filter(action=RefundRed.action).values("target_id")
        article_ids = [ x["target_id"] for x in refund_red_logs ]
        articles = articles.exclude(id__in=article_ids)
    elif refund_red == 1:
        refund_red_logs = ActionLog.objects.filter(action=RefundRed.action).values("target_id")
        article_ids = [ x["target_id"] for x in refund_red_logs ]
        articles = articles.filter(id__in=article_ids)

    language = int(request.GET.get("language", -1))
    if language == 1: #国语
        articles = articles.filter(language = 'M')
    elif language == 0: #粤语
        articles = articles.filter(language = 'C')

    #红黑结果数量
    articles = articles.annotate(articlelotteriesresult_count=Count('articlelotteriesresult'))
    #红黑搜索过滤
    black_red_count = int(request.GET.get("black_red_count", -1))
    if black_red_count == 1:
        articles = articles.filter(articlelotteriesresult_count__gt = 0)
    elif black_red_count == 0:
        articles = articles.filter(articlelotteriesresult_count__lte = 0)

    #所有活动
    measuredactivities = MeasuredActivity.objects.all()
    #活动搜索过滤
    activity_id = int(request.GET.get("article_activity", -1))
    if activity_id > 0:
        articles = articles.filter(measuredactivityarticle__activity_id=activity_id)

    #发布类型
    article_type = int(request.GET.get("article_type", -1))
    if article_type > 0:
        articles = articles.filter(type=article_type)
    translate_type=int(request.GET.get("translate_type",0))
    if translate_type==0:
        articles=articles.filter(status=0)
    elif translate_type==1:
        articles = articles.filter(status=1)

    if request.GET.get("for_export","")=="on" and (from_datestr!="" or to_datestr!=""):

        headers = [u"文章ID",u"上首页",u"概要",u"作者",u"合作类型",u"收费",u"语言", u"创建时间",u"最后修改"]
        def genRows():
            analystTypeNames = [u"收费", u"免费", u"代发"]
            for article in articles.order_by("-date_added"):
                chargeable_words = ''
                if article.chargeable:
                    chargeable_words = str(article.price) if article.price else u'是'
                else:
                    chargeable_words = u'否'

                yield       [str(article.id),
                             u"是" if article.is_toppage else u"否",
                             "None" if article.title == None else article.title,
                             article.author.nick_name,
                             analystTypeNames[article.author.analyst_type],
                             chargeable_words,
                             u"国语" if article.language == 'M' else u'粤语',
                             getLocalDateTime(article.date_added).strftime("%Y-%m-%d %H:%M:%S"),
                             getLocalDateTime(article.last_modified).strftime("%Y-%m-%d %H:%M:%S") ]

        bms_operation_log(request.user.id, "文章导出", "") #文章导出记录日志

        return outputCSV(genRows(), "articles.csv", headers)

    articles = articles.exclude(istop=True, top_time__gte=timezone.now())

    paginator = Paginator(articles.order_by("date_added"),30)
    page_index = request.GET.get("page_index",1)
    pager = paginator.page(page_index)

    # 文章删除理由
    for article in pager.object_list:
        action_logs = ActionLog.objects.filter(target_id=article.id, action='del_article').order_by('-id')
        if len(action_logs) > 0:
            article.memo = action_logs[0].memo
        else:
            article.memo = ''

    #文章讲师渠道
    for article in pager.object_list:
        analystchannelrelation = AnalystChannelRelation.objects.filter(analyst_id=article.author_id, status=0)
        if len(analystchannelrelation) > 0:
            analystchannel = AnalystChannel.objects.filter(id=analystchannelrelation[0].channel_id)
            article.channel = analystchannel[0].channel_name
        else:
            article.channel = ''


    digest_words = 9
    red_articles = {}
    for article in pager.object_list :
        article.tags = ",".join([x.name for x in article.portal_tags.all()])
        if article.digest != None:
            article.digest = article.digest[:digest_words]
        else:
            article.digest = ''
        #     article.digest = ' '.join(strip_tags(article.text)[:digest_words].split())
        #是否小秘书收费文章
        if article.chargeable and is_xiaomishu(article.author.user.id):
            article.is_xms = True
            #记录红单文章
            red_articles[ article.id ] = article
        article.istop = article.top_time > timezone.now() if article.top_time != None else False

    if refund_red in [0, 1] :
        #已确定是否红单就不用查库了
        for article_id, article in red_articles.iteritems():
            article.has_refund_red = True
    else:
        #查询是否有红单退款记录
        refund_red_logs = ActionLog.objects.filter(action=RefundRed.action, target_id__in=red_articles)
        for refund_red_log in refund_red_logs:
            article = red_articles.get(refund_red_log.target_id)
            article.has_refund_red = True

    portalTags = Portal.objects.filter(can_selected=True)

    #查询置顶文章
    top_articles = Article.objects.filter(istop=True).filter(top_time__gte=timezone.now()).order_by("top_order", "-top_time")
    for article in top_articles:
        article.tags = ",".join([x.name for x in article.portal_tags.all()])
        if article.chargeable and article.digest != None:
            article.digest = article.digest[:digest_words]
        else:
            article.digest = ' '.join(strip_tags(article.text)[:digest_words].split())

    return TemplateResponse(request,"article/articles_list.html",locals())


@permission_required("article.junior_editor")
def sync_article(request):
    analysts =Analyst.objects.filter(author_name=request.POST["author_name"])
    if not analysts :
        analyst = create_psAnalyst(request.POST["author_name"])
    else:
        analyst = analysts[0]
    article = Article()
    result = TaskResult.objects.get(id=request.POST["taskid"],is_synced__exists=False)
    article.origin = Article.Porject_Origin[result.project]
    article.author = analyst
    if request.POST.get("is_toppage", "") != "":
        article.is_toppage = True
    form = ArticleSyncForm(request.POST,instance=article)
    if form.is_valid():
        try:
            with transaction.atomic():
                form.save()
                lid_list = []
                for lottery_id in request.POST.getlist("relLottery"):
                    lottery = Lotteryentry.objects.get(id=lottery_id)
                    ArticleLotteries.objects.create(article=form.instance,lottery=lottery)
                    lid_list.append(int(lottery_id))

                matches = Match.objects.filter(lottery_entry__in=lid_list)
                match_list = []
                if matches != None:
                    match_list = [ x.getDictForCache() for x in matches]
                portal_ids = request.POST.getlist("portaltags")
                merge_portaltags(portal_ids, article, match_list)

            if Article.objects.filter(id=article.id).count()==1:
                TaskResult.objects(id=request.POST["taskid"],is_synced__exists=False).update_one(set__is_synced=True)
                add_articlekey(form.instance)
                redis_article_post(form.instance, match_list)
                article_add_post(article)
                return JsonResponse({"result":True})
            else:
                return JsonResponse({"result":False,"message":u"同步失败!"})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({"result":False,"message":u"同步失败!"})
    else:
        return JsonResponse({"result":False,"message":formerror_cat(form)})

def article_mobile(request):
    article = Article()
    is_from_app = (request.GET.get('is_from_app', '0') == '1')
    try:
        article = Article.objects.get(sign_key = request.GET.get("key", ""))
        language = article.language
        article.outdated = False
        if article.chargeable and article.end_time != None:
            if article.end_time <timezone.now():
                article.outdated=True
    except Exception,e :
        logger.error("article_mobile error: " + str(e))

    return TemplateResponse(request,"article/article_mobile.html",{"article":article, 'is_from_app':is_from_app, 'language':language})

def article_mobile_yqy(request):
    article = Article()
    is_from_app = (request.GET.get('is_from_app', '0') == '1')
    try:
        article = Article.objects.get(sign_key = request.GET.get("key", ""))
        language = article.language
        article.outdated = False
        if article.chargeable and article.end_time != None:
            if article.end_time <timezone.now():
                article.outdated=True
    except Exception,e :
        logger.error("article_mobile error: " + str(e))

    return TemplateResponse(request,"article/article_mobile_yqy.html",{"article":article, 'is_from_app':is_from_app, 'language':language})

@permission_required("article.junior_editor")
def redirect_orign(request):
    taskid = request.GET["taskid"]
    result = TaskResult.objects.get(id=taskid)
    return HttpResponseRedirect(result.url)


@permission_required("article.junior_editor")
def atoday_count(request):
    analyst  = Analyst.objects.get(author_name=request.GET["author_name"])
    today0hour = datetime.now().strftime("%Y-%m-%d")
    today0hour = datetime.strptime(today0hour + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    today0hour = timezone.make_aware(today0hour)
    articles = Article.objects.filter(author=analyst,date_added__gte=today0hour,is_toppage=True)

    articles = articles.filter(chargeable=False)


    if "id" in request.GET:
        articles = articles.exclude(id=request.GET["id"])

    return JsonResponse({"left_count":Article.FREE_TOPPAGE_MAX_COUNT-articles.count()})

@login_required
def has_banned(request):
    result = DFASearch.has_banned(request.POST.get("text", u""))
    if result == "":
        return JsonResponse({"result":False, })
    else:
        return JsonResponse({"result": True, "message": result})

def article_archive(request):

    articles  = Article.objects.filter(date_added__lte= timezone.now()-timedelta(days=7))
    paginator = Paginator(articles.order_by("-id"), 100)
    page_index = request.GET.get("page_index", 1)
    pager = paginator.page(page_index)

    return TemplateResponse(request, "article/article_archive.html", {"pager": pager})

@permission_required("article.set_channel", raise_exception=True)
def set_channel(request):
    if request.method == 'GET':
        article_id = request.GET.get('article_id')
        article = Article.objects.get(id=article_id)
        channels = ExternalChannel.objects.all()
        article_channels = ArticleChannel.objects.filter(article_id=article_id)
        return TemplateResponse(request, "article/set_channel.html", locals())
    else:
        article_id = request.POST.get('article_id')
        channel_ids = request.POST.getlist('channel_id')
        article = Article.objects.get(id = article_id)
        ArticleChannel.objects.filter(article_id=article_id).delete()
        for channel_id in channel_ids:
            article_channel = ArticleChannel()
            article_channel.article_id = article_id
            article_channel.author = article.author
            article_channel.channel_id = channel_id
            article_channel.create_by_id = request.user.id
            article_channel.save()
            bms_operation_log(request.user.id, "设置渠道", "文章ID%s"%article.id) #设置渠道记录日志
        return JsonResponse({"result": True, "message": u"保存成功"})

def black_red_list(request):
    if request.method == 'GET':
        article_id = request.GET.get('article_id')
        article = Article.objects.get(id=article_id)

        decide_list = ArticleLotteriesResult.objects.filter(article__id = article_id)
        return TemplateResponse(request, "article/black_red_list.html", locals())

def set_black_red(request):
    if request.method == 'GET':
        article_id = request.GET.get('article_id')
        article = Article.objects.get(id=article_id)

        matches = []
        for lott in article.lotteries.all():
            matches.append(lott.match)

        if request.GET.get('id', '') == '':
            pass
        else:
            article_lotteries_result = ArticleLotteriesResult.objects.get(id=request.GET.get('id'))
        return TemplateResponse(request, "article/set_black_red.html", locals())
    else:
        if request.POST.get('id', '') == '':
            article_lotteries_result = ArticleLotteriesResult()
            article_lotteries_result.article_id = request.POST.get('article_id')
            article_lotteries_result.league = request.POST.get('league')
            article_lotteries_result.match_name = (request.POST.get('match_name').encode('UTF-8')).upper()
            article_lotteries_result.match_time = request.POST.get('match_time')
            article_lotteries_result.playname = request.POST.get('playname')
            article_lotteries_result.score_prediction = request.POST.get('score_prediction')
            article_lotteries_result.score_practical = request.POST.get('score_practical')
            article_lotteries_result.black_red_decide = request.POST.get('black_red_decide')
            article_lotteries_result.comment = request.POST.get('comment')
            article_lotteries_result.user_id = request.user.id
            # 判断数据库是否存在同一篇文章的球队,玩法,预测结果都相同的数据
            articlelotteriesresults = ArticleLotteriesResult.objects.filter(article_id=request.POST.get('article_id')) \
                .filter(match_name=(request.POST.get('match_name').encode('UTF-8')).upper()) \
                .filter(playname=request.POST.get('playname')) \
                .filter(score_prediction=request.POST.get('score_prediction'))
            if articlelotteriesresults.count() > 0:
                return JsonResponse({"result": False, "message": u"保存失败,已存在相同判定记录"})
            else:
                article_lotteries_result.save()
                # 红黑判定保存记录日志
                bms_operation_log(request.user.id, "红黑判定保存", "文章ID%s" % str(article_lotteries_result.article_id))
                return JsonResponse({"result": True, "message": u"保存成功"})
        else:
            article_lotteries_result = ArticleLotteriesResult.objects.get(id = request.POST.get('id'))
            article_lotteries_result.article_id = request.POST.get('article_id')
            article_lotteries_result.league = request.POST.get('league')
            article_lotteries_result.match_name = (request.POST.get('match_name').encode('UTF-8')).upper()
            article_lotteries_result.match_time = request.POST.get('match_time')
            article_lotteries_result.playname = request.POST.get('playname')
            article_lotteries_result.score_prediction = request.POST.get('score_prediction')
            article_lotteries_result.score_practical = request.POST.get('score_practical')
            article_lotteries_result.black_red_decide = request.POST.get('black_red_decide')
            article_lotteries_result.comment = request.POST.get('comment')
            article_lotteries_result.user_id = request.user.id
            # 修改时过滤刨除自身
            articlelotteriesresults = ArticleLotteriesResult.objects.filter(article_id = request.POST.get('article_id')) \
                .filter(match_name=(request.POST.get('match_name').encode('UTF-8')).upper()) \
                .filter(playname=request.POST.get('playname')) \
                .filter(score_prediction=request.POST.get('score_prediction')).exclude(id=article_lotteries_result.id)
            if articlelotteriesresults.count() > 0 :
                return JsonResponse({"result": False, "message": u"保存失败,已存在相同判定记录"})
            else:
                article_lotteries_result.save()
                # 红黑判定修改记录日志
                bms_operation_log(request.user.id, "红黑判定修改", "文章ID%s" % str(article_lotteries_result.article_id))
                return JsonResponse({"result": True, "message": u"保存成功"})

def del_black_red(request):
    article_lotteries_result = ArticleLotteriesResult.objects.get(id=request.POST.get('id'))
    article_lotteries_result.delete()
    # 红黑判定删除记录日志
    bms_operation_log(request.user.id, "红黑判定删除", "文章ID%s" % str(article_lotteries_result.article_id))
    return JsonResponse({"result":True, "message": ''})

def black_red_search(request):
    articlelotteriesresults = ArticleLotteriesResult.objects.all()
    from_datestr = request.GET.get("from_date", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d") + " 00:00:00")
    to_datestr = request.GET.get("to_date", (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d") + " 23:59:59")

    from_date = datetime.strptime(from_datestr,"%Y-%m-%d %H:%M:%S")
    to_date = datetime.strptime(to_datestr,"%Y-%m-%d %H:%M:%S")

    articlelotteriesresults = articlelotteriesresults.filter(article__date_added__gte= from_date)
    articlelotteriesresults = articlelotteriesresults.filter(article__date_added__lte= to_date)
    allarticlelen= len(articlelotteriesresults)

    nickname = request.GET.get('nickname', '')
    if nickname != '':
        articlelotteriesresults = articlelotteriesresults.filter(article__author__nick_name__contains=nickname)

    article_id = request.GET.get('article_id', '')
    if article_id != '':
        articlelotteriesresults = articlelotteriesresults.filter(article_id=article_id)

    black_red_decide = int(request.GET.get('black_red_decide', -1))
    if black_red_decide == 0:
        articlelotteriesresults = articlelotteriesresults.filter(black_red_decide='红')
    elif  black_red_decide == 1:
        articlelotteriesresults = articlelotteriesresults.filter(black_red_decide='黑')
    elif  black_red_decide == 2:
        articlelotteriesresults = articlelotteriesresults.filter(black_red_decide='走水')

    article_language = int(request.GET.get('article_language', -1))
    if article_language == 0:
        articlelotteriesresults = articlelotteriesresults.filter(article__language='M')
    elif article_language == 1:
        articlelotteriesresults = articlelotteriesresults.filter(article__language='C')

    comment = request.GET.get('comment', '')
    if comment != '':
        articlelotteriesresults = articlelotteriesresults.filter(comment__contains=comment)

    #所有活动
    measuredactivities = MeasuredActivity.objects.all()
    #活动搜索过滤
    activity_id = int(request.GET.get("article_activity", -1))
    if activity_id > 0:
        articlelotteriesresults = articlelotteriesresults.filter(article__measuredactivityarticle__activity_id=activity_id)

    # 发布类型
    article_type = int(request.GET.get("article_type", -1))
    if article_type > 0:
        articlelotteriesresults = articlelotteriesresults.filter(article__type=article_type)

    allarticlelen = len(articlelotteriesresults)
    red_article = articlelotteriesresults.filter(black_red_decide='红')
    black_article = articlelotteriesresults.filter(black_red_decide='黑')
    red_article_len = len(red_article)
    black_article_len = len(black_article)
    if allarticlelen>0:
        red_dev_all = str(round(float(red_article_len) / float(allarticlelen), 3) * 100) + "%"
    else:
        red_dev_all=u"0.00%"

    if request.GET.get("for_export","")=="on":
        headers = [u"文章ID",u"上首页",u"标签",u"是否收费",u"作者",u"创建时间", u"联赛",u"赛队名称",u"比赛时间",u"玩法",u"预测结果",u"比分结果",u"红黑结果",u"备注",u"语言"]
        def genRows():
            articles = Article.objects.all()

            articles = articles.filter(date_added__gte = from_date)
            articles = articles.filter(date_added__lte = to_date)

            if article_language == 0:
               articles = articles.filter(language="M")
            elif article_language == 1:
               articles = articles.filter(language="C")

            if nickname != '':
                articles = articles.filter(author__nick_name__contains=nickname)

            articles = articles.order_by('-date_added')

            for article in articles:
                article_lottery_results = ArticleLotteriesResult.objects.filter(article = article)

                if black_red_decide == 0:
                    article_lottery_results = article_lottery_results.filter(black_red_decide='红')
                elif black_red_decide == 1:
                    article_lottery_results = article_lottery_results.filter(black_red_decide='黑')
                elif black_red_decide == 2:
                    article_lottery_results = article_lottery_results.filter(black_red_decide='走水')

                tags = " ".join([x.name for x in article.portal_tags.all()])
                if article_lottery_results.count() == 0:
                    yield [str(article.id),
                           u"是" if article.is_toppage else "",
                           tags or '',
                           u"收费" if article.chargeable else u"免费",
                           article.author.nick_name,
                           getLocalDateTime(article.date_added).strftime("%Y-%m-%d %H:%M:%S"),
                           "",
                           "",
                           "",
                           "",
                           "",
                           "",
                           "",
                           "",
                           u"国语" if article.language == 'M' else u"粤语"]
                else:
                    for result in article_lottery_results:
                     yield  [str(article.id),
                             u"是" if article.is_toppage else "",
                             tags or '',
                             u"收费" if article.chargeable else u"免费",
                             article.author.nick_name,
                             getLocalDateTime(article.date_added).strftime("%Y-%m-%d %H:%M:%S"),
                             ((result.league).strip()).replace('\t','').replace('\n','').replace(' ',''),
                             ((result.match_name).strip()).replace('\t','').replace('\n','').replace(' ',''),
                             getLocalDateTime(result.match_time).strftime("%Y-%m-%d %H:%M:%S"),
                             result.playname,
                             (("`" + result.score_prediction).strip()).replace('\t','').replace('\n','').replace(' ',''),
                             (("`" + result.score_practical).strip()).replace('\t','').replace('\n','').replace(' ',''),
                             result.black_red_decide,
                             ((result.comment).strip()).replace('\t','').replace('\n','').replace(' ','') or '',
                             u"国语" if article.language == 'M' else u"粤语"]
        # 文章红黑库导出记录日志
        bms_operation_log(request.user.id, "文章红黑库导出", "")
        return outputCSV(genRows(), "export_black_red_result.csv", headers)

    paginator = Paginator(articlelotteriesresults.order_by("-article__date_added"),30)
    page_index = request.GET.get("page_index",1)
    pager = paginator.page(page_index)

    for item in pager.object_list :
        item.article.tags = ",".join([x.name for x in item.article.portal_tags.all()])

    return TemplateResponse(request, "article/black_red_search.html", locals())

def redblack_options(request):
    articles = Article.objects.all()
    aword = request.GET.get("author_word", "")
    if aword != "":
        articles = articles.filter(author__nick_name__contains=aword)

    author_type = int(request.GET.get("author_type", -1))
    if author_type >= 0:
        articles = articles.filter(author__analyst_type=author_type)

    from_datestr = request.GET.get("from_date", (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00"))
    from_date = timezone.make_aware(datetime.strptime(from_datestr, "%Y-%m-%d %H:%M:%S"))
    # articles表的时间字段带时区,不用手动纠正
    articles = articles.filter(date_added__gte=from_date)

    to_datestr = request.GET.get("to_date", datetime.now().strftime("%Y-%m-%d 23:59:59"))
    to_date = timezone.make_aware(datetime.strptime(to_datestr, "%Y-%m-%d %H:%M:%S"))
    articles = articles.filter(date_added__lte=to_date)

    articleid = request.GET.get("articleid", "")
    if articleid != "":
        articles = articles.filter(id=articleid)

    is_toppage = int(request.GET.get("is_toppage", "-1"))
    if is_toppage >= 0:
        articles = articles.filter(is_toppage=bool(is_toppage))

    invisible = int(request.GET.get("invisible", "-1"))
    if invisible >= 0:
        articles = articles.filter(invisible=bool(invisible))

    chargeable = int(request.GET.get("chargeable", "-1"))
    if chargeable >= 0:
        articles = articles.filter(chargeable=bool(chargeable))
    key_word = request.GET.get("key_word", "")
    if key_word != "":
        words = key_word.strip().split(" ")
        conds = Q()
        for word in words:
            conds |= Q(text__contains=word)
        articles = articles.filter(conds)

    match_related = int(request.GET.get("match_related", -1))
    if match_related == 0:
        articles = articles.filter(lotteries=None)
    elif match_related == 1:
        articles = articles.exclude(lotteries=None)

    portal_tag = int(request.GET.get("portal_tag", -1))
    if portal_tag == 0:
        # 无标签
        articles = articles.filter(portal_tags=None)
    elif portal_tag > 0:
        articles = articles.filter(portal_tags=portal_tag)

    refund_red = int(request.GET.get("refund_red", -1))
    if refund_red == 0:
        refund_red_logs = ActionLog.objects.filter(action=RefundRed.action).values("target_id")
        article_ids = [x["target_id"] for x in refund_red_logs]
        articles = articles.exclude(id__in=article_ids)
    elif refund_red == 1:
        refund_red_logs = ActionLog.objects.filter(action=RefundRed.action).values("target_id")
        article_ids = [x["target_id"] for x in refund_red_logs]
        articles = articles.filter(id__in=article_ids)

    language = int(request.GET.get("language", -1))
    if language == 1:  # 国语
        articles = articles.filter(language='M')
    elif language == 0:  # 粤语
        articles = articles.filter(language='C')

    # 红黑结果数量
    articles = articles.annotate(articlelotteriesresult_count=Count('articlelotteriesresult'))
    # 红黑搜索过滤
    black_red_count = int(request.GET.get("black_red_count", -1))
    if black_red_count == 1:
        articles = articles.filter(articlelotteriesresult_count__gt=0)
    elif black_red_count == 0:
        articles = articles.filter(articlelotteriesresult_count__lte=0)

    # 所有活动
    measuredactivities = MeasuredActivity.objects.all()
    # 活动搜索过滤
    activity_id = int(request.GET.get("article_activity", -1))
    if activity_id > 0:
        articles = articles.filter(measuredactivityarticle__activity_id=activity_id)

    # 发布类型
    article_type = int(request.GET.get("article_type", -1))
    if article_type > 0:
        articles = articles.filter(type=article_type)

    if request.GET.get("for_export", "") == "on" and (from_datestr != "" or to_datestr != ""):

        headers = [u"文章ID", u"上首页", u"概要", u"作者", u"合作类型", u"收费", u"语言", u"创建时间", u"最后修改"]

        def genRows():
            analystTypeNames = [u"收费", u"免费", u"代发"]
            for article in articles.order_by("-date_added"):
                chargeable_words = ''
                if article.chargeable:
                    chargeable_words = str(article.price) if article.price else u'是'
                else:
                    chargeable_words = u'否'

                yield [str(article.id),
                       u"是" if article.is_toppage else u"否",
                       "None" if article.title == None else article.title,
                       article.author.nick_name,
                       analystTypeNames[article.author.analyst_type],
                       chargeable_words,
                       u"国语" if article.language == 'M' else u'粤语',
                       getLocalDateTime(article.date_added).strftime("%Y-%m-%d %H:%M:%S"),
                       getLocalDateTime(article.last_modified).strftime("%Y-%m-%d %H:%M:%S")]

        return outputCSV(genRows(), "articles.csv", headers)

    articles = articles.exclude(istop=True, top_time__gte=timezone.now())
    paginator = Paginator(articles.order_by("-last_modified"), 30)
    page_index = request.GET.get("page_index", 1)
    pager = paginator.page(page_index)

    digest_words = 40
    red_articles = {}
    for article in pager.object_list:
        article.tags = ",".join([x.name for x in article.portal_tags.all()])
        if article.chargeable and article.digest != None:
            article.digest = article.digest[:digest_words]
        else:
            article.digest = ' '.join(strip_tags(article.text)[:digest_words].split())
        # 是否小秘书收费文章
        if article.chargeable and is_xiaomishu(article.author.user.id):
            article.is_xms = True
            # 记录红单文章
            red_articles[article.id] = article
        article.istop = article.top_time > timezone.now() if article.top_time != None else False

    if refund_red in [0, 1]:
        # 已确定是否红单就不用查库了
        for article_id, article in red_articles.iteritems():
            article.has_refund_red = True
    else:
        # 查询是否有红单退款记录
        refund_red_logs = ActionLog.objects.filter(action=RefundRed.action, target_id__in=red_articles)
        for refund_red_log in refund_red_logs:
            article = red_articles.get(refund_red_log.target_id)
            article.has_refund_red = True

    portalTags = Portal.objects.filter(can_selected=True)

    # 查询置顶文章
    top_articles = Article.objects.filter(istop=True).filter(top_time__gte=timezone.now()).order_by("top_order",
                                                                                                    "-top_time")
    for article in top_articles:
        article.tags = ",".join([x.name for x in article.portal_tags.all()])
        if article.chargeable and article.digest != None:
            article.digest = article.digest[:digest_words]
        else:
            article.digest = ' '.join(strip_tags(article.text)[:digest_words].split())

    return TemplateResponse(request, "article/redblack_articles_list.html", locals())

# 文章上首页审核列表
def article_istoppage_list(request):

    article_examines = Article_Examine.objects.all()
    articles = Article.objects.all()

    aword = request.GET.get("author_word", "")
    if aword != "":
        articles = articles.filter(author__nick_name__contains=aword)

    author_type = int(request.GET.get("author_type", -1))
    if author_type >= 0:
        articles = articles.filter(author__analyst_type=author_type)

    from_datestr = request.GET.get("from_date", datetime.now().strftime("%Y-%m-%d 00:00:00"))
    from_date = timezone.make_aware(datetime.strptime(from_datestr, "%Y-%m-%d %H:%M:%S"))
    # articles表的时间字段带时区,不用手动纠正
    articles = articles.filter(date_added__gte=from_date)

    to_datestr = request.GET.get("to_date", datetime.now().strftime("%Y-%m-%d 23:59:59"))
    to_date = timezone.make_aware(datetime.strptime(to_datestr, "%Y-%m-%d %H:%M:%S"))
    articles = articles.filter(date_added__lte=to_date)

    articleid = request.GET.get("articleid", "")
    if articleid != "":
        articles = articles.filter(id=articleid)

    chargeable = int(request.GET.get("chargeable", "-1"))
    if chargeable >= 0:
        articles = articles.filter(chargeable=bool(chargeable))
    key_word = request.GET.get("key_word", "")
    if key_word != "":
        words = key_word.strip().split(" ")
        conds = Q()
        for word in words:
            conds |= Q(text__contains=word)
        articles = articles.filter(conds)

    match_related = int(request.GET.get("match_related", -1))
    if match_related == 0:
        articles = articles.filter(lotteries=None)
    elif match_related == 1:
        articles = articles.exclude(lotteries=None)

    portal_tag = int(request.GET.get("portal_tag", -1))
    if portal_tag == 0:
        # 无标签
        articles = articles.filter(portal_tags=None)
    elif portal_tag > 0:
        articles = articles.filter(portal_tags=portal_tag)

    refund_red = int(request.GET.get("refund_red", -1))
    if refund_red == 0:
        refund_red_logs = ActionLog.objects.filter(action=RefundRed.action).values("target_id")
        article_ids = [x["target_id"] for x in refund_red_logs]
        articles = articles.exclude(id__in=article_ids)
    elif refund_red == 1:
        refund_red_logs = ActionLog.objects.filter(action=RefundRed.action).values("target_id")
        article_ids = [x["target_id"] for x in refund_red_logs]
        articles = articles.filter(id__in=article_ids)

    language = int(request.GET.get("language", -1))
    if language == 1:  # 国语
        articles = articles.filter(language='M')
    elif language == 0:  # 粤语
        articles = articles.filter(language='C')

    # 发布类型
    article_type = int(request.GET.get("article_type", -1))
    if article_type > 0:
        articles = articles.filter(type=article_type)

    article_examines = article_examines.filter(article_id__in=articles.values('id'))

    status = request.GET.get("status", -1)
    if status == '10':
        article_examines = article_examines.filter(status='10')
    elif status == '20':
        article_examines = article_examines.filter(status='20')
    elif status == '90':
        article_examines = article_examines.filter(status='90')

    #导出
    if request.GET.get("for_export","")=="on":

        headers = [u"ID",u"上首页",u"收费",u"作者",u"语言", u"创建时间",u"状态",u"驳回原因"]
        def genRows():
            for article_examine in article_examines.order_by("status", "article_id"):
                if article_examine.status == '10':
                    status = u"待审核"
                elif article_examine.status == '20':
                    status = u"通过"
                elif article_examine.status == '90':
                    status = u"驳回"
                yield       [str(article_examine.article_id),
                             u"是" if article_examine.article.is_toppage else u"否",
                             # "" if article_examine.article.articleportaltags_set == None else article_examine.article.articleportaltags_set,
                             u"收费" if article_examine.article.chargeable else u"免费",
                             article_examine.article.author.nick_name,
                             u"国语" if article_examine.article.language == 'M' else u'粤语',
                             getLocalDateTime(article_examine.article.date_added).strftime("%Y-%m-%d %H:%M:%S"),
                             status or '',
                             article_examine.examine_opinion or '']

        bms_operation_log(request.user.id, "首页审核导出", "") # 首页审核导出记录日志
        return outputCSV(genRows(), "article_examines.csv", headers)

    paginator = Paginator(article_examines.order_by("status", "article_id"), 30)
    page_index = request.GET.get("page_index", 1)
    pager = paginator.page(page_index)

    digest_words = 40
    red_articles = {}
    for item in pager.object_list:
        article = item.article
        article.tags = ",".join([x.name for x in article.portal_tags.all()])
        if article.chargeable and article.digest != None:
            article.digest = article.digest[:digest_words]
        else:
            article.digest = ' '.join(strip_tags(article.text)[:digest_words].split())


    return TemplateResponse(request, "article/article_istoppage_list.html", locals())

# 文章上首页审核页面
def article_istoppage_examine_detail(request):

    article_id = request.GET.get('article_id')
    article = Article.objects.get(id=article_id)

    return TemplateResponse(request, "article/article_istoppage_examine_detail.html", locals())

# 文章上首页审核通过
def article_istoppage_examine_pass(request):
    article_examine = Article_Examine.objects.get(article_id=request.POST.get('article_id'))
    article_examine.article_id = request.POST.get('article_id')
    article_examine.examine_user_id = request.user.id
    article_examine.examine_time = datetime.now()
    article_examine.examine_opinion = ''
    article_examine.status = request.POST.get('examine_pass')  # 审核通过
    article_examine.save()
    examine_toppage_upset(article_examine)#修改redis
    bms_operation_log(request.user.id, "首页审核通过", "文章ID%s"%str(article_examine.article_id)) #审核通过记录日志
    return JsonResponse({"result": True, "message": u"保存成功"})

# 文章上首页审核不通过
def article_istoppage_examine_nopass(request):
    article_examine = Article_Examine.objects.get(article_id=request.POST.get('article_id'))
    article_examine.article_id = request.POST.get('article_id')
    article_examine.examine_user_id = request.user.id
    article_examine.examine_time = datetime.now()
    examine_reason = ' '.join(request.POST.getlist('reason'))
    examine_reason__custom = request.POST.get('reason_custom')
    article_examine.examine_opinion = examine_reason + ' ' +examine_reason__custom
    article_examine.status = request.POST.get('examine_no_pass')  # 审核不通过
    article_examine.save()
    examine_toppage_downset(article_examine) # 修改redis
    bms_operation_log(request.user.id, "首页审核驳回", "文章ID%s" % str(article_examine.article_id))  # 审核驳回记录日志
    return JsonResponse({"result": True, "message": u"保存成功"})
