# coding:utf-8
import cStringIO
import codecs
from django.utils import timezone

from django.http import HttpResponse, StreamingHttpResponse
from mongoengine import connect

from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import connection
from datetime import datetime, date
import random, string,hashlib
import json
import urllib
import requests

from HTMLParser import HTMLParser
import re
import jpush
import os

from rong import ApiClient

from functools import wraps
from django.utils.decorators import available_attrs
from django.http import HttpResponseNotAllowed
from django.utils.html import strip_tags

from jcsbms.settings import ALIDAYU_APPKEY,ALIDAYU_SECRET, XIAOMISHU_AUTH_USER_IDS, PUSH_SERVICE_URL, YUEYU_JPUSH_KEY, \
    YUEYU_JPUSH_MASTER, AUTHOR_JPUSH_KEY, AUTHOR_JPUSH_MASTER, YUEYU_XIAOMISHU_AUTH_USER_IDS, TOKEN_M, \
    PUSH_SERVICE_URL_QM, jpush_app_key_qiumi, jpush_master_secret_qiumi, jpush_app_key_yiqiying, \
    jpush_master_secret_yiqiying, xpush_master_secret_yiqiying, hpush_appid_yiqiying, hpush_master_secret_yiqiying, \
    YQY_XIAOMISHU_AUTH_USER_IDS
from jcsbms.settings import jpush_app_key,jpush_master_secret, jmessage_admin
from jcsbms.jmessage import JMessage

from top.api import AlibabaAliqinFcSmsNumSendRequest
import top
import logging

import dateutil
from datetime import datetime
from django.db import models

logger = logging.getLogger("django")

is_connected = False
def connect_mongodb():
    global is_connected
    if not is_connected:
        try:
            connect("resultdb",username="jcuser", password="jc776", host="mongodb://jcuser:jc776@192.168.10.234:27017/resultdb")
        except Exception,e:
            print e
        is_connected = True


def strip_spaces(str1):
    str1 = str1.replace(unichr(32),u"")
    str1 = str1.replace(unichr(160),u"")
    str1 = str1.replace(chr(32),u"")
    return str1

def get_filename(user):
    now =datetime.now()
    md5 = hashlib.md5()
    md5.update(str(now))
    digest_str = md5.hexdigest()[8:-8]
    filename = digest_str+"_"+str(user.id)
    return filename

def jsend_mail(subject,message,recipient):
    smessage = u"Hi,您好：\r\n"
    smessage = smessage + message +u"\r\n"
    smessage = smessage + u"精彩说团队敬上"+u"\r\n"
    smessage = smessage + u""+str(datetime.now())+u"\r\n"
    smessage = smessage + u"(此为系统邮件，请勿直接回复)"+u"\r\n"

    send_mail(subject, smessage, u"no-reply@xycentury.com", [recipient])

def jsend_message():

    req=AlibabaAliqinFcSmsNumSendRequest()
    req.set_app_info(top.appinfo(ALIDAYU_APPKEY,ALIDAYU_SECRET))

    req.extend = "None"
    req.sms_type = "normal"
    req.sms_free_sign_name = u"精彩说".encode("utf-8")
    req.sms_param = '{"product":"精彩说","password":"12345678"}'
    req.rec_num = "13488816073"
    req.sms_template_code = "SMS_2865237"
    try:
        print(111)
        resp= req.getResponse()

        print(resp)

    except Exception as e:
        print(2222)
        print(e)

def random_string(length=18):
    a = list(string.ascii_letters+string.digits)
    random.shuffle(a)
    return ''.join(a[:length])

def verify_code(length=6):
    a = list(string.digits)
    random.shuffle(a)
    return ''.join(a[:length])


def get_userdir(user):
    now = datetime.now()

    md5 = hashlib.md5()
    md5.update(user.username + str(now))
    user_dir = md5.hexdigest()[8:-8]
    return user_dir

def formerror_cat(form):
    '''
    errorlist_list =[]
    for error_list in form.errors.values():
        errorlist_list.append(u"|".join(error_list))
    return u"|".join(errorlist_list)
    '''
    return form.errors.as_text()

def push_article(article):
    Jpush_Obj = jpush.JPush(jpush_app_key, jpush_master_secret)

    from mobileapp.models import Follow
    if Follow.objects.filter(author=article.author.id).count()==0:
        return

    push = Jpush_Obj.create_push()
    push.audience = jpush.audience(
            jpush.tag(str(article.author.id))
        )

    if article.chargeable:
        digest = strip_spaces(strip_tags(article.digest))[:20].encode("utf-8")
    else:
        digest = strip_spaces(strip_tags(article.text))[:20].encode("utf-8")

    author  = article.author.nick_name.encode("utf-8")
    title = author + ":" + digest
    article_key='articleId'
    ios_msg = jpush.ios(alert=title, badge="+1", sound="a.caf", extras={article_key:str(article.id)})
    android_msg = jpush.android(alert=u"新文章提醒",title=title,builder_id=None,extras={article_key:str(article.id)})
    push.notification = jpush.notification(alert=u"新文章提醒", android=android_msg, ios=ios_msg)
    push.options = {"time_to_live":86400, "sendno":article.id,"apns_production":True}#上线前需要更新为上线状态
    push.platform = jpush.all_
    push.send()

def push_article_new_ios(article):
    Jpush_Obj = jpush.JPush("99aa42175d87d853dd137d2a", "7fd39e0510d872dcd31668cc")

    from mobileapp.models import Follow
    if Follow.objects.filter(author=article.author.id).count()==0:
        return

    push = Jpush_Obj.create_push()
    push.audience = jpush.audience(
        jpush.tag(str(article.author.id))
    )

    if article.chargeable:
        digest = strip_spaces(strip_tags(article.digest))[:20].encode("utf-8")
    else:
        digest = strip_spaces(strip_tags(article.text))[:20].encode("utf-8")

    author  = article.author.nick_name.encode("utf-8")
    title = author + ":" + digest
    article_key='articleId'
    ios_msg = jpush.ios(alert=title, badge="+1", sound="a.caf", extras={article_key:str(article.id)})
    push.notification = jpush.notification(alert=u"新文章提醒", ios=ios_msg)
    push.options = {"time_to_live":86400, "sendno":article.id,"apns_production":True}#上线前需要更新为上线状态
    push.platform = jpush.all_
    push.send()

#球秘推送
def push_article_from_service_qiumi(article):
    # from mobileapp.models import Follow
    # if Follow.objects.filter(author=article.author.id).count()==0:
    #     return

    if article.chargeable:
        digest = strip_spaces(strip_tags(article.digest))[:20].encode("utf-8")
    else:
        digest = strip_spaces(strip_tags(article.text))[:20].encode("utf-8")

    author = article.author.nick_name.encode("utf-8")
    title = author + ":" + digest
    cursor = connection.cursor()
    cursor.execute("""SELECT
    	P .userid,
    	P .token,
    	P . TYPE,
    	f.authorid,
    	uu.silence_type,
    	uu.notify_type,
    	uu.start_hour,
    	uu.start_minute,
    	uu.end_hour,
    	uu.end_minute,
        uac."type" as "uactype"
    FROM
    	push_channel P
    LEFT JOIN users_config uu ON P .userid = uu.users_id
    LEFT JOIN users_config_analyst uac ON uac.users_id = P .userid
    AND uac.analyst_id = %d,
     follow f
    WHERE
    	f.userid = P .userid
    AND f.authorid = %d
    AND (
    	P .token <> ''
    	AND P .token IS NOT NULL
    )
    AND P .appid = '%s';
    """ % (article.author.id, article.author.id, "Z"))

    unionInfos = cursor.fetchall()


    now_time = datetime.now()

    jpushTokens = []
    huaweiTokens = []
    xiaomiTokens = []

    for unionInfo in unionInfos:
        # '1接收 0不接收'
        print '-----------------------------------'
        # print str(unionInfo)
        silence_type = unionInfo[4] or u'1'
        if silence_type != u'1':
            continue

        # '通知时间 10全天接收 20按时间段接收';
        notify_type = unionInfo[5] or u'10'
        if notify_type != u'10':
            startHour = unionInfo[6]
            startMinute = unionInfo[7]
            endHour = unionInfo[8]
            endMinute = unionInfo[9]
            if not isInZone(now_time.hour, now_time.minute, startHour, startMinute, endHour, endMinute):
                continue

        # '10全部接收 20只接收收费 30只接收免费';
        receive_type = unionInfo[10] or u'10'
        if (receive_type == u'20' and not article.chargeable) \
                or (receive_type == u'30' and article.chargeable):
            continue

        if unionInfo[2] == 0:
            jpushTokens.append(unionInfo[1])
        elif unionInfo[2] == 1:
            huaweiTokens.append(unionInfo[1])
        elif unionInfo[2] == 2:
            xiaomiTokens.append(unionInfo[1])

    params = {'title': title,
              'alert': '新文章提醒',
              'appid': article.language,
              'extras': '{"articleId":"%d"}' % (article.id)
              }

    if len(jpushTokens) > 0:
        params['pushChannel'] = '0';
        params['pushTokenList'] = ','.join(jpushTokens)
        sendPushRequest_qiumi(params)
    if len(huaweiTokens) > 0:
        params['pushChannel'] = '1';
        params['pushTokenList'] = ','.join(huaweiTokens)
        sendPushRequest_qiumi(params)
    if len(xiaomiTokens) > 0:
        params['pushChannel'] = '2';
        params['pushTokenList'] = ','.join(xiaomiTokens)
        sendPushRequest_qiumi(params)


#一起赢推送
def push_article_from_service_yiqiying(article):

    if article.chargeable:
        digest = strip_spaces(strip_tags(article.digest))[:20].encode("utf-8")
    else:
        digest = strip_spaces(strip_tags(article.text))[:20].encode("utf-8")

    author = article.author.nick_name.encode("utf-8")
    title = author + ":" + digest
    cursor = connection.cursor()
    cursor.execute("""SELECT
    	P .userid,
    	P .token,
    	P . TYPE,
    	f.authorid,
    	uu.silence_type,
    	uu.notify_type,
    	uu.start_hour,
    	uu.start_minute,
    	uu.end_hour,
    	uu.end_minute,
        uac."type" as "uactype"
    FROM
    	push_channel P
    LEFT JOIN users_config uu ON P .userid = uu.users_id
    LEFT JOIN users_config_analyst uac ON uac.users_id = P .userid
    AND uac.analyst_id = %d,
     follow f
    WHERE
    	f.userid = P .userid
    AND f.authorid = %d
    AND (
    	P .token <> ''
    	AND P .token IS NOT NULL
    )
    AND P .appid = '%s';
    """ % (article.author.id, article.author.id, "J"))

    unionInfos = cursor.fetchall()

    now_time = datetime.now()

    jpushTokens = []
    huaweiTokens = []
    xiaomiTokens = []

    for unionInfo in unionInfos:
        # '1接收 0不接收'
        # print '-----------------------------------'
        # print str(unionInfo)
        silence_type = unionInfo[4] or u'1'
        if silence_type != u'1':
            continue

        # '通知时间 10全天接收 20按时间段接收';
        notify_type = unionInfo[5] or u'10'
        if notify_type != u'10':
            startHour = unionInfo[6]
            startMinute = unionInfo[7]
            endHour = unionInfo[8]
            endMinute = unionInfo[9]
            if not isInZone(now_time.hour, now_time.minute, startHour, startMinute, endHour, endMinute):
                continue

        # '10全部接收 20只接收收费 30只接收免费';
        receive_type = unionInfo[10] or u'10'
        if (receive_type == u'20' and not article.chargeable) \
                or (receive_type == u'30' and article.chargeable):
            continue

        if unionInfo[2] == 0:
            jpushTokens.append(unionInfo[1])
        elif unionInfo[2] == 1:
            huaweiTokens.append(unionInfo[1])
        elif unionInfo[2] == 2:
            xiaomiTokens.append(unionInfo[1])

    params = {'title': title,
              'alert': '新文章提醒',
              'appid': article.language,
              'extraMap': {"articleId":str(article.id)}
              }

    if len(jpushTokens) > 0:
        params['pushChannel'] = '0';
        params['pushTokenList'] = jpushTokens
        sendJPushMessageWithKey(params)
    if len(huaweiTokens) > 0:
        params['pushChannel'] = '1';
        params['pushTokenList'] = huaweiTokens
        sendHPushMessageWithKey(params)
    if len(xiaomiTokens) > 0:
        params['pushChannel'] = '2';
        params['pushTokenList'] = xiaomiTokens
        sendXPushMessageWithKey(params)


def push_article_from_service(article):
    # from mobileapp.models import Follow
    # if Follow.objects.filter(author=article.author.id).count()==0:
    #     return

    if article.chargeable:
        digest = strip_spaces(strip_tags(article.digest))[:20].encode("utf-8")
    else:
        digest = strip_spaces(strip_tags(article.text))[:20].encode("utf-8")

    author  = article.author.nick_name.encode("utf-8")
    title = author + ":" + digest

    cursor = connection.cursor()
    cursor.execute("""SELECT
	P .userid,
	P .token,
	P . TYPE,
	f.authorid,
	uu.silence_type,
	uu.notify_type,
	uu.start_hour,
	uu.start_minute,
	uu.end_hour,
	uu.end_minute,
    uac."type" as "uactype"
FROM
	push_channel P
LEFT JOIN users_config uu ON P .userid = uu.users_id
LEFT JOIN users_config_analyst uac ON uac.users_id = P .userid
AND uac.analyst_id = %d,
 follow f
WHERE
	f.userid = P .userid
AND f.authorid = %d
AND (
	P .token <> ''
	AND P .token IS NOT NULL
)
AND P .appid = '%s';
""" % (article.author.id, article.author.id, article.language))
    unionInfos = cursor.fetchall()

    now_time = datetime.now()

    jpushTokens = []
    huaweiTokens = []
    xiaomiTokens = []

    push_tasks = []

    for unionInfo in unionInfos:
        #'1接收 0不接收'
        silence_type = unionInfo[4] or u'1'
        if silence_type != u'1':
            continue

        #'通知时间 10全天接收 20按时间段接收';
        notify_type = unionInfo[5] or u'10'
        if notify_type != u'10':
            startHour = unionInfo[6]
            startMinute = unionInfo[7]
            endHour = unionInfo[8]
            endMinute = unionInfo[9]
            if not isInZone(now_time.hour, now_time.minute, startHour, startMinute, endHour, endMinute):
                continue

        #'10全部接收 20只接收收费 30只接收免费';
        receive_type = unionInfo[10] or u'10'
        if (receive_type == u'20' and not article.chargeable) \
            or (receive_type == u'30' and article.chargeable):
            continue

        push_info = {'article_id':article.id, 'user_id': unionInfo[0], 'token':unionInfo[1], 'author_id':article.author.id}

        if unionInfo[2] == 0:
            jpushTokens.append(unionInfo[1])
            push_info['push_type'] = 0
        elif unionInfo[2] == 1:
            huaweiTokens.append(unionInfo[1])
            push_info['push_type'] = 1
        elif unionInfo[2] == 2:
            xiaomiTokens.append(unionInfo[1])
            push_info['push_type'] = 2

        push_tasks.append(push_info)
    #文章消息监控app按文章语言添加token
    if article.language == 'M':
        jpushTokens.extend(TOKEN_M)
    elif article.language == 'C':
        pass

    params = {'title': title,
              'alert': '新文章提醒',
              'appid': article.language,
              'extras': '{"articleId":"%d"}' % (article.id)
              }

    if len(jpushTokens) > 0:
        params['pushChannel'] = '0';
        params['pushTokenList'] = ','.join(jpushTokens)
        sendPushRequest(params)
    if len(huaweiTokens) > 0:
        params['pushChannel'] = '1';
        params['pushTokenList'] = ','.join(huaweiTokens)
        sendPushRequest(params)
    if len(xiaomiTokens) > 0:
        params['pushChannel'] = '2';
        params['pushTokenList'] = ','.join(xiaomiTokens)
        sendPushRequest(params)

    return push_tasks #给周健统计入库使用


#文章上首页推送
def push_article_examine_toppage(article):

    if article.chargeable:
        digest = strip_spaces(strip_tags(article.digest))[:20].encode("utf-8")
    else:
        digest = strip_spaces(strip_tags(article.text))[:20].encode("utf-8")

    author = article.author.nick_name.encode("utf-8")
    title = author + ":" + digest

    cursor = connection.cursor()
    cursor.execute("""SELECT
	userid,
	token,
	type
FROM push_channel
WHERE userid
IN (28751);
""")

    unionInfos = cursor.fetchall()

    jpushTokens = []
    huaweiTokens = []
    xiaomiTokens = []

    for unionInfo in unionInfos:
        if unionInfo[2] == 0:
            jpushTokens.append(unionInfo[1])
        elif unionInfo[2] == 1:
            huaweiTokens.append(unionInfo[1])
        elif unionInfo[2] == 2:
            xiaomiTokens.append(unionInfo[1])

    #文章消息监控app按文章语言添加token
    if article.language == 'M':
        jpushTokens.extend(TOKEN_M)
    elif article.language == 'C':
        pass

    params = {'title': title,
              'alert': '文章上首页审核提醒',
              'appid': article.language,
              'extras': '{"articleId":"%d"}' % (article.id)
              }

    if len(jpushTokens) > 0:
        params['pushChannel'] = '0';
        params['pushTokenList'] = ','.join(jpushTokens)
        sendPushRequest(params)
    if len(huaweiTokens) > 0:
        params['pushChannel'] = '1';
        params['pushTokenList'] = ','.join(huaweiTokens)
        sendPushRequest(params)
    if len(xiaomiTokens) > 0:
        params['pushChannel'] = '2';
        params['pushTokenList'] = ','.join(xiaomiTokens)
        sendPushRequest(params)

def isInZone(nowHour, nowMinute, startHour, startMinute, endHour, endMinute):
    startPoint = startHour * 60 + startMinute;
    endPoint = endHour * 60 + endMinute;
    nowPoint = nowHour * 60 + nowMinute

    if startPoint <= endPoint:
        return nowPoint >= startPoint and nowPoint <= endPoint
    else:
        return nowPoint >= startPoint or nowPoint <= endPoint

def sendPushRequest_qiumi(params):
    f = urllib.urlopen(PUSH_SERVICE_URL_QM, urllib.urlencode(params))
    if f.getcode() != 200:
        res = json.load(f.read())
        logger.error("Send article message error %s", res.message)


def sendPushRequest(params):
    f = urllib.urlopen(PUSH_SERVICE_URL, urllib.urlencode(params))
    if f.getcode() != 200:
        res = json.load(f.read())
        logger.error("Send article message error %s", res.message)

def outputCSV(rows, fname="output.csv", headers=None):
    def getContent(fileObj):
        fileObj.seek(0)
        data = fileObj.read()
        fileObj.seek(0)
        fileObj.truncate()
        return data

    def genCSV(rows, headers):
        # 准备输出
        output = cStringIO.StringIO()
        # 写BOM
        output.write(bytearray([0xFF, 0xFE]))
        if headers != None and isinstance(headers, list):
            headers = codecs.encode("\t".join(headers) + "\n", "utf-16le")
            output.write(headers)
            yield getContent(output)
        for row in rows:
            rowData = codecs.encode("\t".join(row) + "\n", "utf-16le")
            output.write(rowData)
            yield getContent(output)
        output.close()
    resp = StreamingHttpResponse(genCSV(rows, headers))
    resp["Content-Type"] = "application/vnd.ms-excel; charset=utf-16le"
    resp["Content-Type"] = "application/octet-stream"
    resp["Content-Disposition"] = "attachment;filename=" + fname
    resp["Content-Transfer-Encoding"] = "binary"
    return resp


def outputdoc(rows, fname="output.doc"):

    resp = StreamingHttpResponse(rows)
    resp["Content-Type"] = "application/vnd.ms-excel; charset=utf-16le"
    resp["Content-Type"] = "application/octet-stream"
    resp["Content-Disposition"] = "attachment;filename=" + fname
    resp["Content-Transfer-Encoding"] = "binary"
    return resp

def getLocalDateTime(dateTimeObj):
    if dateTimeObj.tzinfo != None:
        #tzinfo不为None则不是本地时间
        return dateTimeObj.astimezone(dateutil.tz.tzlocal())
    return dateTimeObj

def getClientIp(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def getUserAgent(request):
    return request.META.get("HTTP_USER_AGENT", "")

def sysMonitorSMS(phoneNumbers, errorMsg=""):
    data = {"reason": errorMsg, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    return alidayuSMS(phoneNumbers, "SMS_34820134", data)

def syncMatchSMS(phone_numbers, new_teams, auto_standardized_teams, non_synced_matches, problem_matches):
    data = {"new_teams":str(new_teams), "auto_standardized":str(auto_standardized_teams), "non_synced":str(non_synced_matches), "problem_matches":str(problem_matches)}
    return alidayuSMS(phone_numbers, "SMS_34930103", data)

def alidayuSMS(phone_numbers, template_code, params):
    req=AlibabaAliqinFcSmsNumSendRequest()
    req.set_app_info(top.appinfo(ALIDAYU_APPKEY,ALIDAYU_SECRET))

    req.extend = "None"
    req.sms_type = "normal"
    req.sms_free_sign_name = u"北京信盈世纪科技".encode("utf-8")
    req.sms_param = params
    req.rec_num = ",".join(phone_numbers)
    req.sms_template_code = template_code
    try:
        resp= req.getResponse()
        return resp["success"]
    except Exception as e:
        print(e)
    return False


def validatePageIndex(pageIndex, maxPages):
    if pageIndex <= 0:
        pageIndex = 1
    elif pageIndex > maxPages:
        pageIndex = maxPages
    return pageIndex

class SettablePaginator(Paginator):

    def __init__(self, object_list, per_page, orphans=0,
                 allow_empty_first_page=True):
        '''see Paginator for args'''
        super(SettablePaginator, self).__init__(object_list, per_page, orphans,
                 allow_empty_first_page)

    def _set_count(self, count):
        self._count = count
    count = property(Paginator._get_count, _set_count)

    def _set_num_pages(self, num_pages):
        self._num_pages = num_pages
    num_pages = property(Paginator._get_num_pages, _set_num_pages)

def sendJMessageqiumi(userid, author_id, author_name, text):
    jm = JMessage(jpush_app_key_qiumi, jpush_master_secret_qiumi)
    return jm.sendMessage(target_type="single", target_id="user%s" % userid, target_name=None, from_type="admin", from_id=jmessage_admin["username"], from_name=author_name, text=text, extras={"author_id": str(author_id)})

def sendJMessageyiqiying(userid, author_id, author_name, text):
    jm = JMessage(jpush_app_key_yiqiying, jpush_master_secret_yiqiying)
    return jm.sendMessage(target_type="single", target_id="user%s" % userid, target_name=None, from_type="admin", from_id=jmessage_admin["username"], from_name=author_name, text=text, extras={"author_id": str(author_id)})


def sendJMessage(userid, author_id, author_name, text):
    jm = JMessage(jpush_app_key, jpush_master_secret)
    return jm.sendMessage(target_type="single", target_id="user%s" % userid, target_name=None, from_type="admin", from_id=jmessage_admin["username"], from_name=author_name, text=text, extras={"author_id": str(author_id)})

def sendJMessageCantonese(userid, author_id, author_name, text):
    jm = JMessage(YUEYU_JPUSH_KEY, YUEYU_JPUSH_MASTER)
    return jm.sendMessage(target_type="single", target_id="user%s" % userid, target_name=None, from_type="admin", from_id=jmessage_admin["username"], from_name=author_name, text=text, extras={"author_id": str(author_id)})

def sendAuthorJMessage(author_id, userid, user_name, text, project):
    jm = JMessage(AUTHOR_JPUSH_KEY, AUTHOR_JPUSH_MASTER)
    return jm.sendMessage(target_type="single", target_id="author%s" % author_id, target_name=None, from_type="admin", from_id=jmessage_admin["username"], from_name=user_name, text=text, extras={"user_id": str(userid), "language": project})

def is_xiaomishu(user_id):
    return user_id in XIAOMISHU_AUTH_USER_IDS

def is_yueyu_xiaomishu(user_id):
    return user_id in YUEYU_XIAOMISHU_AUTH_USER_IDS

def is_yqy_xiaomishu(user_id):
    return user_id in YQY_XIAOMISHU_AUTH_USER_IDS

def DatetimeJsonEncoder(obj):
    if isinstance(obj, datetime):
        return timezone.localtime(obj).strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(obj, date):
        return timezone.localtime(obj).strftime('%Y-%m-%d')
    else:
        raise TypeError('%r is not JSON serializable' % obj)

def sendJPushMessageWithKey(params):
    headers = {"Content-Type": "application/json"}
    data = {
        'appKey': jpush_app_key_yiqiying,
        'appSecret':jpush_master_secret_yiqiying,
        'title': params['title'],
        'content': params['alert'],
        'tokenList': params['pushTokenList'],
        'paramMap': params['extraMap'],
    }
    # resp = requests.post(url='http://123.57.59.76:9999/ji-guang/push', headers=headers, json=data) #测试环境
    resp = requests.post(url='http://10.141.70.77:9999/ji-guang/push', headers=headers, json=data) #正式环境

def sendHPushMessageWithKey(params):
    headers = {"Content-Type": "application/json"}
    data = {
        'appId':hpush_appid_yiqiying,
        'appSecret': hpush_master_secret_yiqiying,
        'title': params['title'],
        'content': params['alert'],
        'icon':'',
        'appPackageName':'com.xycentury.jcs.yqyand',
        'tokenList': params['pushTokenList'],
        'paramMap': params['extraMap'],
    }
    # resp = requests.post(url='http://123.57.59.76:9999/hua-wei/push', headers=headers, json=data)
    resp = requests.post(url='http://10.141.70.77:9999/hua-wei/push', headers=headers, json=data)

def sendXPushMessageWithKey(params):
    headers = {"Content-Type": "application/json"}
    data = {
        'appSecret': xpush_master_secret_yiqiying,
        'appPackageName': 'com.xycentury.jcs.yqyand',
        'title': params['title'],
        'payload': params['alert'],
        'description':'小米推送',
        'tokenList': params['pushTokenList'],
        'paramMap': params['extraMap'],
    }
    # resp = requests.post(url='http://123.57.59.76:9999/xiao-mi/push', headers=headers, json=data)
    resp = requests.post(url='http://10.141.70.77:9999/xiao-mi/push', headers=headers, json=data)