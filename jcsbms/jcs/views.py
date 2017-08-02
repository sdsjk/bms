# coding:utf-8
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required,permission_required
from django.db import connection
from django.utils.html import strip_tags

from analyst.models import Analyst
from article.models import Articletimeline
from jcsbms.utils import formerror_cat, outputCSV, sendJMessage, is_xiaomishu, sendJMessageCantonese, sendAuthorJMessage, \
    is_yueyu_xiaomishu, sendJMessageqiumi, sendJMessageyiqiying, is_yqy_xiaomishu
from mobileapp.models import AppUser, Follow
from .models import Bulletin, Letter, letter_post, BannedLettor, LetterHide, BmsLog, get_system_config
from .forms import BulletinForm, LetterForm, XiaoMiShuLetterForm, XiaoMiShuNormalForm

from datetime import datetime, timedelta
from actions import DelLetter, RestoreLetter
from django.contrib.auth.models import User
import logging
logger = logging.getLogger("django")
# Create your views here.

@login_required
def home_index(request):
    bulletins = Bulletin.objects.all().order_by("-id")[0:6]
    return TemplateResponse(request, 'jcs/home_index.html',{"bulletins":bulletins})

@permission_required("article.operation_editor")
def post_bulletin(request):
    if request.method == "GET":
        if "id" not in request.GET:
            return TemplateResponse(request, 'jcs/post_bulletin.html')
        else:

            return TemplateResponse(request, 'jcs/post_bulletin.html',{'bulletin':Bulletin.objects.get(id = request.GET["id"])})
    elif request.method == "POST":
        if "id" not in request.POST:
            bulletin = Bulletin()
            bulletin.poster = request.user

            form =  BulletinForm(request.POST,instance=bulletin)
            if form.is_valid():
                form.save()
                # 发布公告记录日志
                bms_operation_log(request.user.id, "发布公告", "公告ID%s" % str(Bulletin.objects.all().latest('id').id))
                return JsonResponse({"result":True})
            else:
                return JsonResponse({"result":False,"message":formerror_cat(form)})
        else:
            bulletin = Bulletin.objects.get(id=request.POST["id"])
            form =  BulletinForm(request.POST,instance=bulletin)
            if form.is_valid():
                form.save()
                # 修改公告记录日志
                bms_operation_log(request.user.id, "修改公告", "公告ID%s" % str(bulletin.id))
                return  JsonResponse({"result":True})
            else:
                return JsonResponse({"result":False,"message":formerror_cat(form)})



@permission_required("article.operation_editor")
def bulletin_list(request):
    bulletins = Bulletin.objects.all()

    paginator = Paginator(bulletins.order_by("-id"),30)
    page_index = request.GET.get("page_index",1)
    pager = paginator.page(page_index)

    return TemplateResponse(request,"jcs/bulletin_list.html",{"pager":pager})

@login_required()
def bulletin_info(request):
    return TemplateResponse(request, 'jcs/bulletin_info.html',{'bulletin':Bulletin.objects.get(id = request.GET["id"])})



@permission_required("analyst.analyst_action")
def letters_search(request):

    action = request.GET.get("action","")
    if action =="unread":

        offset = 0
        if "offset" in request.GET:
            offset = int(request.GET["offset"])
            if offset < 0 :
                offset = 0
        cursor = connection.cursor()
        key_word = request.GET.get("key_word", "")
        if key_word != "":
            sql  = "select from_auser_id, max(id) as max_id, project from jcs_letter where (content LIKE %s"
            if key_word.isdigit():
                sql = sql + " or from_auser_id = %s"
            sql = sql + ") AND from_auser_id not in (select auser_id from jcs_bannedlettor where analyst_id = %s ) and to_user_id = %s and invisible = FALSE  group by from_auser_id, project order by max(cast(unread as int))  desc, max_id desc limit 21 offset %s;"
            if key_word.isdigit():
                cursor.execute(sql, ['%' + key_word +'%', key_word,request.user.analyst.id, request.user.id, offset])
            else:
                cursor.execute(sql, ['%' + key_word + '%', request.user.analyst.id, request.user.id, offset])
        else:
            sql  = "select from_auser_id, max(id) as max_id, project  from jcs_letter where from_auser_id not in (select auser_id from jcs_bannedlettor where analyst_id = %s ) and to_user_id = %s and invisible = FALSE  group by from_auser_id, project order by max(cast(unread as int))  desc, max_id desc limit 21 offset %s;"
            cursor.execute(sql,[request.user.analyst.id,request.user.id,offset])
        uinfos = cursor.fetchall()

        letter_list=[]
        for uinfo in uinfos:

            letter_value = {}
            uinfo_obj = AppUser.objects.get(userid =uinfo[0])
            letter  = Letter.objects.get(id=uinfo[1])
            letter_value["fromuser_id"] = uinfo_obj.userid
            letter_value["fromuser_name"] = "*******"+uinfo_obj.nickname[-4:] if is_xiaomishu(request.user.id) == False else uinfo_obj.nickname
            letter_value["content"] = strip_tags(letter.content)[:52].strip()
            if len(letter_value["content"]) == 0:
                letter_value["content"] = "[sys]空白消息"
            letter_value["timestamp"] = timezone.localtime(letter.date_added).strftime("%Y-%m-%d %H:%M")
            letter_value["unread"] = "info" if letter.unread else "default"
            letter_value["project"] = letter.project
            letter_value["project_c"] = Letter.PROJECT_CNAME[letter.project]
            letter_list.append(letter_value)

        return JsonResponse(letter_list,safe=False)
    elif action=="reading":
        from_auser = AppUser.objects.get(userid=request.GET["from_auser"])
        project = request.GET.get('project', 'M')
        letters = Letter.objects.filter(Q(to_user=request.user, from_auser=from_auser)|Q(to_auser=from_auser, from_user=request.user))\
            .filter(project=project).filter(invisible=False).order_by("-id")
        offset = 0
        if "offset" in request.GET:
            offset = int(request.GET["offset"])
            if offset < 0 :
                offset = 0
        letters = letters[offset:offset+21]

        letter_list=[]
        i=0
        for letter in letters[::-1] :
            if letter.to_user==request.user:
                letter_value = {}
                letter_value["from_auser_id"] = letter.from_auser.userid
                letter_value["from_user_name"] = "*******"+letter.from_auser.nickname[-4:] if is_xiaomishu(request.user.id) == False else letter.from_auser.nickname
                letter_value["content"] = letter.content
                letter_value["timestamp"] = timezone.localtime(letter.date_added).strftime("%Y-%m-%d %H:%M")
                letter_value["unread"] = "info" if letter.unread else "default"
                letter_value["project"] = letter.project
                letter_value["project_c"] = Letter.PROJECT_CNAME[letter.project]
                letter_list.append(letter_value)
            else:
                letter_value = {}
                letter_value["from_user_id"] = letter.from_user.id
                letter_value["from_user_name"] = letter.from_user.analyst.nick_name
                letter_value["content"] = letter.content
                letter_value["timestamp"] = timezone.localtime(letter.date_added).strftime("%Y-%m-%d %H:%M")
                letter_value["unread"] = "info" if letter.unread else "default"
                letter_value["project"] = letter.project
                letter_value["project_c"] = Letter.PROJECT_CNAME[letter.project]
                letter_list.append(letter_value)

            if (len(letters)>20 and i>0) or len(letters)<=20:
                if letter.unread==True and letter.to_user ==request.user :
                    letter.unread = False;
                    letter.save()
            i= i+1

        return JsonResponse(letter_list,safe=False)

@permission_required("analyst.analyst_action")
def letters_view(request):
    return TemplateResponse(request, 'jcs/letters_view.html', {"user":request.user, "is_xiaomishu": is_xiaomishu(request.user.id)})

@permission_required("analyst.analyst_action")
def post_letter(request):
    analyst = request.user.analyst
    if analyst.ban_letter and timezone.now() < analyst.banletter_time:
        return JsonResponse({"result": False, "message": u"你目前被禁止发送私信"})
    letter = Letter()
    letter.from_user = request.user
    letter.to_analyst = request.user.analyst

    if is_xiaomishu(request.user.id):
        form = XiaoMiShuNormalForm(request.POST, instance=letter)
    else:
        form = LetterForm(request.POST,instance=letter)
        auser_id = int(request.POST.get('to_auser', 0))
        if Follow.objects.filter(author=analyst, user_id=auser_id).count() == 0:
            return JsonResponse({"result": False, "message": u'发送失败：用户已取消对您的关注，私信无法发送。'})
    if form.is_valid():
        form.save()
        letter_post(letter)
        if letter.project == 'M':
            try:
                ret = sendJMessage(letter.to_auser_id, analyst.id, analyst.nick_name, letter.content)
                if ret.err != 0:
                    logger.error("send jmessage error %s", ret)
            except Exception as e:
                pass
            try:
                ret_qiumi=sendJMessageqiumi(letter.to_auser_id, analyst.id, analyst.nick_name, letter.content)
                if ret_qiumi.err != 0:
                    logger.error("send jmessage to Qiumi error %s", ret_qiumi)
            except Exception as e:
                pass
            try:
                ret_yiqiying=sendJMessageyiqiying(letter.to_auser_id, analyst.id, analyst.nick_name, letter.content)
                if ret_yiqiying.err != 0:
                    logger.error("send jmessage to yiqiying error %s", ret_yiqiying)
            except Exception as e:
                pass
        else:
            ret = sendJMessageCantonese(letter.to_auser_id, analyst.id, analyst.nick_name, letter.content)
            if ret.err != 0:
                logger.error("send jmessage to Cantonese error %s", ret)
        return JsonResponse({"result": True})
    else:
        return JsonResponse({"result": False, "message": formerror_cat(form)})

@permission_required("analyst.analyst_action")
def send_letter(request):
    analyst = request.user.analyst
    cellphones = request.POST.get("cellphones", "").strip()
    content = request.POST.get("content", "")
    if cellphones != "":
        cellphones = cellphones.split(" ")
        # 将用户手机号改为用户id过滤
        users = AppUser.objects.filter(userid__in=cellphones)
        failed_phones = []
        for user in users:
            letter = Letter()
            letter.from_user = request.user
            letter.to_analyst = request.user.analyst
            if is_yueyu_xiaomishu(request.user.id):
                letter.project = 'C'
            if is_yqy_xiaomishu(request.user.id):
                letter.project = 'J'
            form = XiaoMiShuLetterForm({"to_auser":str(user.userid), "content":content}, instance=letter)
            if form.is_valid():
                form.save()
                letter_post(letter)
                LetterHide.objects.filter(user=user, author=analyst).delete()
                #添加粤语小秘书判断
                if not is_yueyu_xiaomishu(request.user.id):
                    ret = sendJMessage(letter.to_auser_id, analyst.id, analyst.nick_name, letter.content)
                    if ret.err != 0:
                        logger.error("send jmessage error %s", ret)
                else:
                    ret = sendJMessageCantonese(letter.to_auser_id, analyst.id, analyst.nick_name, letter.content)
                    if ret.err != 0:
                        logger.error("send jmessage to Cantonese error %s", ret)
            else:
                failed_phones.append(str(user.userid))
        if len(failed_phones) == 0:
            return JsonResponse({"result": True})
        else:
            return JsonResponse({"result": False, "message": u"发送失败的用户ID:" + ",".join(failed_phones)})
    else:
        return JsonResponse({"result": False, "message": u"用户ID不能为空"})

@permission_required("article.junior_editor")
def letters_review(request):
    letters = Letter.objects.all()

    from_datestr = request.GET.get("from_date", (datetime.now()-timedelta(days=1)).strftime("%Y-%m-%d"))
    to_datestr =request.GET.get("to_date", datetime.now().strftime("%Y-%m-%d"))

    from_date = datetime.strptime(from_datestr+" 00:00:00","%Y-%m-%d %H:%M:%S")
    to_date = datetime.strptime(to_datestr+" 23:59:59","%Y-%m-%d %H:%M:%S")

    letters = letters.filter(date_added__gte=from_date, date_added__lte=to_date)

    keywords = request.GET.get("keywords", "")
    if keywords != "":
        words = keywords.strip().split(" ")
        conds = Q()
        for word in words:
            conds |= Q(content__contains=word)
        letters = letters.filter(conds)

    nick_name = request.GET.get("nick_name","")
    if nick_name!="":
        letters = letters.filter(Q(from_user__analyst__nick_name=nick_name)|Q(to_user__analyst__nick_name=nick_name))

    auser_nickname = request.GET.get("auser_nickname", "")
    if auser_nickname  != "":
        letters = letters.filter(Q(from_auser__nickname=auser_nickname ) | Q(to_auser__nickname=auser_nickname) |
                                 Q(from_auser__userid=auser_nickname) | Q(to_auser__userid = auser_nickname))

    invisible = int(request.GET.get("invisible", -1))
    if invisible >= 0:
        letters = letters.filter(invisible=bool(invisible))

    project = request.GET.get("project", -1)
    if project == 'M': #国语
        letters = letters.filter(project = 'M')
    elif project == 'C': #粤语
        letters = letters.filter(project = 'C')
    elif project == 'J': #一起赢
        letters = letters.filter(project = 'J')

    letterIds = letters.values("id")
    actionLogs = []
    actionLogDict = {}
    if len(letterIds) > 0:
        letterIds = [str(x["id"]) for x in letterIds]
        cursor = connection.cursor()
        cursor.execute("select t1.id, t1.user_id, t1.action, t1.date_added, t1.description, t1.target_id from jcs_actionlog as t1 join (select target_id, max(id) as id from jcs_actionlog where target_model='Letter' and target_id in ( %s ) group by target_id) as t2 on t1.id=t2.id" % (",".join(letterIds)) )
        actionLogs = cursor.fetchall()
    if len(actionLogs) > 0:
        userIds = set([x[1] for x in actionLogs])
        users = User.objects.filter(id__in=userIds)
        userDict = {}
        for u in users:
            userDict[u.id] = u
        for alog in actionLogs:
            actionLogDict[alog[5]] = {"user": userDict[alog[1]].username, "date_added":alog[3], "description":alog[4]}

    can_revert_letter_ids = get_system_config('CAN_REVERT_LETTER_IDS')
    can_revert_letter = str(request.user.id) in can_revert_letter_ids.split(',')

    if request.GET.get("for_export","")=="on" and (from_datestr!="" or to_datestr!=""):

        headers = [u"ID",u"发信人",u"收信人",u"发信时间",u"内容",u"已读",u"已删除", u"最后操作", u"操作时间"]
        def genRows():
            for letter in letters.order_by("-date_added"):
                from_user = ""
                to_user = ""
                last_action = ""
                last_action_time = ""
                if letter.from_user:
                    from_user = u"老师:" + letter.from_user.analyst.nick_name
                elif letter.from_auser:
                    from_user = u"app用户" + str(letter.from_auser.userid)
                if letter.to_user:
                    to_user = u"老师:" + letter.to_user.analyst.nick_name
                elif letter.to_auser:
                    to_user = u"app用户" + str(letter.to_auser.userid)

                if letter.id in actionLogDict:
                    info = actionLogDict[letter.id]
                    last_action = info["user"] + ":" + info["description"]
                    last_action_time = (info["date_added"] + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

                yield           [str(letter.id),
                                 from_user,
                                 to_user,
                                 timezone.localtime(letter.date_added).strftime("%Y-%m-%d %H:%M:%S"),
                                 letter.content.replace('\n', ' ').replace('\r', ' '),
                                 u"是" if letter.unread == False else u"否",
                                 u"是" if letter.invisible else u"否",
                                 last_action,
                                 last_action_time
                                 ]

        # 私信审核通过记录日志
        bms_operation_log(request.user.id, "私信导出", "")
        return outputCSV(genRows(), "letters.csv", headers)

    paginator = Paginator(letters.order_by("-id"),30)
    page_index = request.GET.get("page_index",1)
    pager = paginator.page(page_index)

    return TemplateResponse(request, "jcs/letters_reiview.html", locals())

@permission_required("article.junior_editor")
def del_letter(request):
    letter = Letter.objects.get(id=request.POST["id"])
    letter.invisible=True
    letter.save()
    # 私信审核取消记录日志
    bms_operation_log(request.user.id, "私信审核取消", "私信ID%s" % str(letter.id))
    DelLetter().makeLog(request.user, request.POST["id"])
    return JsonResponse({"result": True})

@permission_required("article.junior_editor")
def restore_letter(request):
    letter = Letter.objects.get(id=request.POST["id"])
    letter.invisible=False
    letter.save()
    # 私信审核通过记录日志
    bms_operation_log(request.user.id, "私信审核通过", "私信ID%s" % str(letter.id))
    RestoreLetter().makeLog(request.user, request.POST["id"])
    if letter.to_user:
        ret = sendAuthorJMessage(letter.to_analyst.user_id, letter.to_auser_id, letter.to_auser.userid, letter.content, letter.project)
        if ret.err != 0:
            logger.error("send author jmessage error %s", ret)

    return JsonResponse({"result": True})

@permission_required("analyst.analyst_action")
def ban_auser(request):
    auser = AppUser.objects.get(userid = request.POST["auserid"])
    BannedLettor.objects.create(auser=auser,analyst = request.user.analyst)
    return JsonResponse({"result": True})

# @permission_required("analyst.analyst_action")
def del_ban_auser(request):
    bannedlettors = BannedLettor.objects.filter(analyst_id=request.POST.get('analyst_id')).filter(auser_id=request.POST.get('auser_id'))
    bannedlettors.delete()
    # 解除粉丝屏蔽状态记录日志
    bms_operation_log(request.user.id, "解除粉丝屏蔽状态", "用户ID%s" % str(request.POST.get('auser_id')))
    return JsonResponse({"result":True, "message": ''})

#bms后台日志记录
def bms_operation_log(operator_id,even_name,even_message):
    bmslog = BmsLog()
    bmslog.operator_id = operator_id
    bmslog.even_name = even_name
    bmslog.even_message = even_message
    bmslog.cdate = datetime.now()
    bmslog.save()
def article_time_line_cut(article_id,m_date,cut_date,cut_author,teacher_id):
    articletimeline=Articletimeline()
    if Articletimeline.objects.filter(article_id=article_id).count()==0:
        articletimeline.article_id=article_id
        articletimeline.m_cdate=m_date
        articletimeline.cut_cdate=cut_date
        articletimeline.cut_author=cut_author
        articletimeline.teacher_id=teacher_id
        articletimeline.save()
def article_time_line_translate(article_id,translate_date,translate_author,teacher_thai):
    if Articletimeline.objects.filter(article_id=article_id).count()>0:
        articletimeline = Articletimeline.objects.get(article_id=article_id)
        articletimeline.translate_cdate=translate_date
        articletimeline.translate_author=translate_author
        articletimeline.teacher_thai=teacher_thai
        articletimeline.save()

def reply_letter_instead_analyst(request):
    analyst = Analyst.objects.get(id=request.POST["to_anaylst"])
    if analyst.ban_letter and timezone.now() < analyst.banletter_time:
        return JsonResponse({"result": False, "message": u"你目前被禁止发送私信"})
    letter = Letter()
    letter.from_user = analyst.user
    letter.to_analyst = analyst
    form = LetterForm(request.POST,instance=letter)
    if form.is_valid():
        form.save()
        letter_post(letter)
        if letter.project == 'M':
            ret = sendJMessage(letter.to_auser_id, analyst.id, analyst.nick_name, letter.content)
            ret_qiumi=sendJMessageqiumi(letter.to_auser_id, analyst.id, analyst.nick_name, letter.content)
            ret_yiqiying=sendJMessageyiqiying(letter.to_auser_id, analyst.id, analyst.nick_name, letter.content)
            if ret.err != 0:
                logger.error("send jmessage error %s", ret)
            if ret_qiumi.err != 0:
                logger.error("send jmessage error %s", ret_qiumi)
            if ret_yiqiying.err != 0:
                logger.error("send jmessage error %s", ret_yiqiying)
        else:
            ret = sendJMessageCantonese(letter.to_auser_id, analyst.id, analyst.nick_name, letter.content)
            if ret.err != 0:
                logger.error("send jmessage to Cantonese error %s", ret)
        return JsonResponse({"result": True})
    else:
        return JsonResponse({"result": False, "message": formerror_cat(form)})