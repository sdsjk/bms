#-*- coding:utf-8 -*-
'''
Created by dengel on 15/11/23.
refined by zhaozhi on 16/08/14

@author: stone, zhaozhi

'''
import sys
import json
import os
import django
import psycopg2
import time
import codecs
import pymongo
from pymongo import MongoClient
from datetime import datetime, timedelta


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) #manage.py的目录
sys.path.append("/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages")
os.environ['DJANGO_SETTINGS_MODULE'] = 'jcsbms.settings' #setting的目录
django.setup()

from lottery.models import MatchResult,Match,Lotterytype,Lotteryentry, TeamName
from django.utils import timezone
from jcsbms.utils import syncMatchSMS
from jcsbms.settings import EDITORS_CONTACT_INFO, DATABASES
from django.core.mail import send_mail
from django.template.loader import render_to_string
from jcsbms.utils import syncMatchSMS, getLocalDateTime


def standardizeTeamName(cup_name, team_name):
    #查找库里是否有抓取到的队名
    teamnames = TeamName.objects.filter(cup_name=cup_name, original_name=team_name)
    teamname = None
    ret_code = -1
    if not teamnames:
        teamname = TeamName()
        teamname.checked=False
        teamname.cup_name=cup_name
        teamname.original_name=team_name
        teamname.standard_name=None
        print (u"add new team:%s" % team_name).encode("utf-8")
        teamname.save()
    else:
        teamname = teamnames[0]

    if teamname.standard_name == None:
        std = TeamName.objects.filter(standard_name=team_name)
        if std:
            #自动标准化
            ret_code = 1
            teamname.checked = True
            teamname.standard_name = std[0].standard_name
            teamname.save()
    return teamname.standard_name, ret_code

def sendSyncResult(sync_result, contacts):
    #发送竞技彩同步结果
    non_synced_num = len(sync_result["non_synced"])
    problem_matches_num = len(sync_result["problem_matches"])
    if non_synced_num == 0 and problem_matches_num == 0:
        return
    emails = []
    phones = []
    for contact in contacts:
        if contact.get("email", "") != "":
            emails.append(contact["email"])
        if contact.get("phone", "") != "":
            phones.append(contact["phone"])
    email_content = render_to_string("email/sync_match_result.html", sync_result)
    send_mail(u"赛事同步结果", "", u"no-reply@xycentury.com", emails, html_message=email_content)
    if datetime.now().hour >= 7:
        #短信夜间免打扰
        syncMatchSMS(phones, sync_result["new_teams"], sync_result["auto_standardized"], non_synced_num, problem_matches_num)

def checkWrongTimeMatches(home_team, away_team, start_time):
    '''
    检查主客队相同,比赛时间不同,但是时间间隔在24小时以内的比赛,这种属于源数据错误
    :param home_team:
    :param away_team:
    :param start_time: datetime.datetime
    :return:
    '''
    #dict, 用于排重
    problem_matches = {}
    matches = Match.objects.filter(home_team=home_team, away_team=away_team, start_time__gte=start_time-timedelta(hours=24), start_time__lte=start_time+timedelta(hours=24))
    if matches.count() > 1:
        for match in matches:
            start_time = getLocalDateTime(match.start_time).strftime("%Y-%m-%d %H:%M")
            problem_matches[start_time] = match.cup_name
        #如果是多场时间一样的,认为没问题
        problem_matches = {} if len(problem_matches) == 1 else problem_matches
    return problem_matches

print("Sync begin::::::::::::::::::::")
print(datetime.now())


client = MongoClient(host="192.168.10.234", port=27017)
client.resultdb.authenticate("jcuser", "jc776", mechanism='MONGODB-CR')
db_config = DATABASES["default"]
conn = psycopg2.connect(database=db_config["NAME"],user=db_config["USER"],password=db_config["PASSWORD"],host=db_config["HOST"],port=db_config["PORT"])
cur = conn.cursor()

db = client["resultdb"]



'''
竞技彩同步开始
'''
#中文名需要在lotterytype表里先建好
project_typename = {"web_aicai_jczq_match":u"竞彩足球",
                    "web_trade500_bjdc_match":u"北京单场",
                    "web_trade500_match":u"传统足彩",
                    "web_aicai_jclq_match":u"竞彩篮球",
                    "match_web_163_zc":u"中超联赛",
                    "web_win007_match_single":u"全球的足球杯赛",
                    "web_win007_match_league_single":u"全球的足球联赛"
                    }

project_type={};
for key in project_typename.keys():
    project_type[key]=Lotterytype.objects.get(name=project_typename[key])

#同步几小时内抓取的比赛
within_hours = 8
start_ts = time.time() - 3600 * within_hours
sync_result = {"new_teams": 0, "auto_standardized":0, "non_synced":[], "problem_matches":{}}
i=0
for project in db.collection_names():
    if not project in project_type:
        continue
    for matchresult in db[project].find({"updatetime":{"$gte": start_ts}}).sort("updatetime", pymongo.DESCENDING):

        taskid = str(matchresult["taskid"])
        result = json.loads(matchresult["result"])
        cup_name = result["cupName"]
        matchId = result["mattchId"]
        teamVs = result["teamVs"]
        teams = teamVs.split("VS")
        home_team = teams[0].strip()
        away_team = teams[1].strip()
        home_team = home_team.replace(unichr(32),u"")
        away_team = away_team.replace(unichr(32),u"")
        home_team = home_team.replace(unichr(160),u"")
        away_team = away_team.replace(unichr(160),u"")
        time_str = result["endTime"]
        start_time =  timezone.make_aware(datetime.strptime(time_str, "%Y-%m-%d %H:%M"))

        match_flag = 0
        #查找库里是否有抓取到的主队队名
        home_team_std, ret_code = standardizeTeamName(cup_name, home_team)
        if home_team_std != None:
            home_team = home_team_std
            match_flag = match_flag+1
            if ret_code == 1:
                sync_result["auto_standardized"] += 1
                sync_result["new_teams"] += 1
        else:
            sys.stdout.write(codecs.encode("%s %s miss standard name\n" % (cup_name, home_team), "utf-8"))
            sync_result["new_teams"] += 1

        away_team_std, ret_code = standardizeTeamName(cup_name, away_team)
        if away_team_std != None:
            away_team = away_team_std
            match_flag = match_flag+2
            if ret_code == 1:
                sync_result["auto_standardized"] += 1
                sync_result["new_teams"] += 1
        else:
            sys.stdout.write(codecs.encode("%s %s miss standard name\n" % (cup_name, away_team), "utf-8"))
            sync_result["new_teams"] += 1

        if match_flag<3:
            print "match_flag: %d, team name is not enough" % match_flag
            reason = ""
            if home_team_std != None:
                reason = u"客队名称不标准"
            elif away_team_std != None:
                reason = u"主队名称不标准"
            else:
                reason = u"两队名称不标准"
            sync_result["non_synced"].append({"cup_name":cup_name, "home_team":home_team, "away_team":away_team, "reason":reason, "start_time":time_str, "match_flag": match_flag})
            continue;

        matchs = Match.objects.filter(home_team=home_team,away_team=away_team,start_time=start_time)
        has_entry = Lotteryentry.objects.filter(taskid=taskid).count() > 0
        match = None
        if matchs and has_entry :
            print("update::"+project+":"+taskid)
            match= matchs[0]
            if project_typename[project] == u"竞彩足球":
                match.match_id = matchId

        elif not has_entry:
            #有比赛,无entry,不同源的赛事
            print("insert::"+project+":"+taskid)
            entry = Lotteryentry()
            entry.type = project_type[project]
            entry.taskid=taskid
            entry.save()
            match = Match()
            match.lottery_entry=entry
            match.cup_name = cup_name
            match.start_time = start_time
            match.home_team = home_team
            match.away_team = away_team
            if project_typename[project]==u"竞彩足球":
                match.match_id = matchId
        else:
            #无比赛,有entry,被人为修正的
            print (u"match %s vs %s %s already exists, but corrected" % (home_team, away_team, start_time.strftime("%Y-%m-%d %H:%M")) ).encode("utf-8")
        if match != None:
            match.save()
            print match.id
            match.lotterytypes.add(project_type[project])
        #记录时间有问题的赛事
        pblm = checkWrongTimeMatches(home_team=home_team, away_team=away_team, start_time=start_time)
        if len(pblm) > 0:
            key = home_team + "_" + away_team
            if key not in sync_result["problem_matches"]:
                sync_result["problem_matches"][key] = pblm
            else:
                sync_result["problem_matches"][key].update(pblm)

#数字彩同步开始


matchs =  db["web_trade500_ssq_dlt_match"]
#matchs.update_many({"is_synced":True},{'$unset':{'is_synced': 1}})
cur.execute("select id from lottery_lotterytype where name = %s;",(u"双色球",))
ssq_id = int(cur.fetchone()[0])
cur.execute("select id from lottery_lotterytype where name = %s;",(u"大乐透",))
dlt_id = int(cur.fetchone()[0])
for doc in matchs.find({"is_synced":{"$exists":False}}):
    '''
    #taskid = models.CharField(null=True,max_length=32,unique=True)
    #season = models.CharField(max_length=16)
    #end_time = models.DateTimeField()
    #type = models.ForeignKey(Lotterytype)
    '''
    taskid = str(doc["_id"])
    print(taskid)
    result = json.loads(doc["result"])
    season = result["season"]
    cup_name = result["cupName"]
    if cup_name==u"双色球":
        type_id = ssq_id
    elif cup_name == u"大乐透":
        type_id = dlt_id
    time_str = result["lastTime"]

    end_time = timezone.make_aware(datetime.strptime(time_str, "%Y-%m-%d %H:%M"))

    cur.execute("INSERT INTO lottery_lotteryentry (taskid,type_id) VALUES(%s,%s) RETURNING id",(taskid,type_id))
    entry_id = cur.fetchone()[0]
    cur.execute("INSERT INTO lottery_lotto(season,end_time,lottery_entry_id) VALUES(%s,%s,%s);",
                (season,end_time,entry_id))
    matchs.find_one_and_update({"_id":doc["_id"]},{'$set':{'is_synced': True}})

    print(str(type_id)+":"+taskid)
    conn.commit()

cur.close()
conn.close()
client.close()

print("Sync end::::::::::::::::::::")
print(datetime.now())

#sendSyncResult(sync_result, [{"email":"zhaozhi@xycentury.com", "phone":"18611243186"}])
sendSyncResult(sync_result, EDITORS_CONTACT_INFO)
