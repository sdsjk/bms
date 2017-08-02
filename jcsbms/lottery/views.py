# coding:utf-8
'''
Created on 2015-11-24

@author: stone
'''
import json
import chardet
from datetime import timedelta, datetime

import requests
from django.db.models import Q
from django.forms import model_to_dict
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required,permission_required
from django.template.response import TemplateResponse
from django.core.paginator import Paginator
from django.utils import timezone

from analyst.models import Analyst
from jcs.views import bms_operation_log
from jcsbms.utils import formerror_cat, validatePageIndex, DatetimeJsonEncoder
from lottery.forms import TeamNameForm, PrizeForm, TeamForm, FixtureForm, CupLeagueForm, RenXuanForm
from .models import Lotterytype,Lotto,Match,Lotteryentry, TeamName, Team, Prize, Fixture, CupLeague, RenXuan, \
    match_add_post, match_del_post, match_put_post, ScoutMatch, MatchLotterytypes
import hashlib
from django.db import transaction, connection
import logging
import time

logger = logging.getLogger("django")
# Create your views here.
@permission_required("article.junior_editor")
def index(request):

    if "lottery_type" not in request.GET:
        lottery_type = Lotterytype.objects.get(name=u"竞技彩")
    else:
        lottery_type = Lotterytype.objects.get(id=request.GET["lottery_type"])

    if lottery_type.parent == None:
        if lottery_type.name==u"数字彩":
            lottos=Lotto.objects.all()
        elif lottery_type.name==u"竞技彩":
            matches = Match.objects.all()
    else:
        if lottery_type.parent.name==u"数字彩":
            lottos  = Lotto.objects.filter(lottery_entry__type=lottery_type)
        else:
            matches = lottery_type.match_set.all()

    lottery_scope = int(request.GET.get("lottery_scope","1"))
    if lottery_scope == 1:
        from_datestr = datetime.now().strftime("%Y-%m-%d")
        to_datestr =request.GET.get("to_date", (datetime.now()+timedelta(days=7)).strftime("%Y-%m-%d"))
    else:
        from_datestr = request.GET.get("from_date", (datetime.now()-timedelta(days=7)).strftime("%Y-%m-%d"))
        to_datestr =request.GET.get("to_date", (datetime.now()+timedelta(days=7)).strftime("%Y-%m-%d"))

    from_date = datetime.strptime(from_datestr+" 00:00:00","%Y-%m-%d %H:%M:%S")
    to_date = datetime.strptime(to_datestr+" 23:59:59","%Y-%m-%d %H:%M:%S")

    project = int(request.GET.get("project", -1))
    if project == 0:
        matches = matches.filter(project='C')
    elif project == 1:
        matches = matches.filter(project='M')
    elif project == 2:
        matches = matches.filter(project='E')

    #只对竞技彩有效
    team = request.GET.get("team", "")
    cup_name = request.GET.get('cup_name', '')
    sport_type = int(request.GET.get('sport_type', "-1"))

    if lottery_scope == 1:
        #未过期的
        if lottery_type.name==u"数字彩"  or (lottery_type.parent!=None and lottery_type.parent.name == u"数字彩"):
            lottos = lottos.filter(end_time__gte=timezone.now(), end_time__lte=to_date)
            paginator = Paginator(lottos.order_by("-id"), 30)
        else:
            #竞技彩
            matches = matches.filter(start_time__gte=timezone.now(), start_time__lte=to_date)
            if team != "":
                matches = matches.filter(Q(home_team__contains=team) | Q(away_team__contains=team))
            if cup_name != '':
                matches = matches.filter(cup_name__contains=cup_name)
            if sport_type != -1:
                league_names = CupLeague.objects.filter(sport_type = sport_type).values_list('name')
                matches = matches.filter(cup_name__in=league_names)
            paginator = Paginator(matches.order_by("start_time"), 30)
    else:
        if lottery_type.name==u"数字彩"  or (lottery_type.parent!=None and lottery_type.parent.name == u"数字彩"):
            paginator = Paginator(lottos.filter(end_time__gte=from_date, end_time__lte=to_date).order_by("-id"), 30)
        else:
            #竞技彩
            if team != "":
                matches = matches.filter(Q(home_team__contains=team) | Q(away_team__contains=team))
            if cup_name != '':
                matches = matches.filter(cup_name__contains=cup_name)
            if sport_type != -1:
                league_names = CupLeague.objects.filter(sport_type = sport_type).values_list('name')
                matches = matches.filter(cup_name__in=league_names)
            paginator = Paginator(matches.filter(start_time__gte=from_date, start_time__lte=to_date).order_by("start_time"), 30)

    if lottery_type.name == u"数字彩" or (lottery_type.parent != None and lottery_type.parent.name == u"数字彩"):
        pass
    else:
        cup_name_list = []
        for match_item in paginator.object_list:
            cup_name_list.append(match_item.cup_name)
        cup_map_dict = {}

        for item in CupLeague.objects.filter(name__in=cup_name_list):
            if item.sport_type == 0:
                cup_map_dict[item.name] = u'足球'
            elif item.sport_type == 1:
                cup_map_dict[item.name] = u'篮球'
            else:
                cup_map_dict[item.name] = u'网球'

    page_index = request.GET.get("page_index",1)
    pager = paginator.page(page_index)
    return TemplateResponse(request, 'lottery/lottery_list.html', {
        "type":lottery_type.parent if lottery_type.parent else lottery_type,
        "actual_type":lottery_type,
        "pager":pager,
        "lottery_scope":lottery_scope,
        "from_datestr": from_datestr,
        "to_datestr": to_datestr,
        "team": team,
        "cup_name": cup_name,
        "sport_type": sport_type,
        "cup_map_dict": cup_map_dict,
        "project": project
    })




@login_required
def lottery_search(request):
    '''
    清理赛队名称中的空格
    for match in Match.objects.all():

        if match.home_team.find(unichr(160))>=0 or match.away_team.find(unichr(160))>=0:
            print(match.home_team)
            match.home_team = match.home_team.replace(unichr(160),u"")
            match.away_team = match.away_team.replace(unichr(160),u"")
            print(match.home_team)
            match.save()
    '''

    lottery_type = Lotterytype.objects.get(id=request.GET["typeid"])
    result_list = []

    page_index = request.GET.get("page_index",1)

    source = request.GET.get('source', '')
    is_single_language = False #是否是单语言的老师
    single_language = 'M'
    if source == 'analyst':
        analyst = Analyst.objects.get(user=request.user)
        if analyst.is_mandarin_perm and analyst.is_cantonese_perm:
            is_single_language = False
        else:
            is_single_language = True
            if analyst.is_cantonese_perm:
                single_language = 'C'
            else:
                single_language = 'M'


    if lottery_type.name == u"数字彩":
        lottoes = Lotto.objects.filter(lottery_entry__type__parent=lottery_type,end_time__gte=timezone.now())
        #paginator = Paginator(lottoes,30)
        #pager = paginator.page(page_index)
        for lotto in lottoes:
            result_value = {}
            result_value["id"] = lotto.lottery_entry.id
            result_value["name"] = lotto.lottery_entry.type.name +":"+lotto.season
            result_list.append(result_value)
    elif lottery_type.name == u"竞技彩":
        matches = Match.objects.filter(lottery_entry__type__parent=lottery_type,start_time__gte=timezone.now()-timedelta(hours=7)).filter(Q(home_team__icontains=request.GET["teamword"]) | Q(away_team__icontains=request.GET["teamword"]))
        if is_single_language:
            matches = matches.filter(project=single_language)
        matches = matches.exclude(lottery_entry__type__in=(11,12))
        matches_notZC  = matches.exclude(lottery_entry__type=Lotterytype.objects.get(name=u"中超联赛"))
        match_set = set()
        for match in matches_notZC:
            result_value = {}
            result_value["id"] = match.lottery_entry.id

            result_value["name"] = timezone.localtime(match.start_time).strftime("%m-%d %H:%M")+":"+match.home_team+"VS"+match.away_team
            if not is_single_language:
                result_value['name'] = result_value['name'] + u'(' + (u'国语' if match.project == 'M' else u'粤语') + u')'
            if result_value["name"] not in match_set :
                match_set.add(result_value["name"])
                result_list.append(result_value)

        matches_inZC  = matches.filter(lottery_entry__type=Lotterytype.objects.get(name=u"中超联赛"),start_time__lte=timezone.now()+timedelta(days=12))
        for match in matches_inZC:
            result_value = {}
            result_value["id"] = match.lottery_entry.id
            result_value["name"] = timezone.localtime(match.start_time).strftime("%m-%d %H:%M")+":"+match.home_team+"VS"+match.away_team
            if not is_single_language:
                result_value['name'] = result_value['name'] + u'(' + (u'国语' if match.project == 'M' else u'粤语') + u')'
            if result_value["name"] not in match_set :
                match_set.add(result_value["name"])
                result_list.append(result_value)
    return JsonResponse(result_list,safe=False)

@permission_required("article.junior_editor")
def teamname_list(request):
    teamnames  = TeamName.objects.filter()

    original_name = request.GET.get("original_name","")
    if original_name != "":
        teamnames = teamnames.filter(original_name__contains=original_name)

    only_unmodified = True

    if "original_name" in request.GET and "only_unmodified" not in request.GET:
        only_unmodified = False

    if only_unmodified:
        teamnames = teamnames.filter(Q(standard_name__isnull=True)|Q(checked=False))

    paginator = Paginator(teamnames.order_by("-id"), 30)
    page_index = int(request.GET.get("page_index", 1) )
    page_index = validatePageIndex(page_index, paginator.num_pages)
    pager = paginator.page(page_index)

    return TemplateResponse(request, 'lottery/teamname_list.html', locals())

@permission_required("article.junior_editor")
def put_teamname(request):
    if request.method=="GET":
        teamname = TeamName.objects.get(id=request.GET["id"])
        return TemplateResponse(request, 'lottery/put_teamname.html', {"teamname":teamname})
    elif request.method=="POST":
        teamname = TeamName.objects.get(id=request.POST["id"])
        form = TeamNameForm(request.POST,instance=teamname)
        if form.is_valid():

            form.save()
            return JsonResponse({"result": True})
        else:
            return JsonResponse({"result": False, "message": formerror_cat(form)})

@permission_required("article.junior_editor")
def post_standardname(request):
    teamname = TeamName.objects.get(id=request.POST["id"])
    teamname.standard_name = request.POST["standard_name"]
    teamname.checked = True
    teamname.save()
    return JsonResponse({"result": True})

@permission_required("article.junior_editor")
def prize_list(request):
    prizes = Prize.objects.all()

    paginator = Paginator(prizes.order_by("-id"), 30)
    page_index = request.GET.get("page_index", 1)
    pager = paginator.page(page_index)

    return TemplateResponse(request, 'lottery/prize_list.html',{"pager":pager})

@permission_required("article.junior_editor")
def post_prize(request):
    if request.method == "GET":
        if "id" not in request.GET:
            return TemplateResponse(request, 'lottery/post_prize.html')
        else:
            prize = Prize.objects.get(id=request.GET["id"])
        return TemplateResponse(request, 'lottery/post_prize.html',{"prize":prize})

    elif request.method =="POST":
        if "id" not in request.POST:
            prize = Prize()
        else:
            prize = Prize.objects.get(id=request.POST["id"])

        prize.match = Match.objects.get(lottery_entry_id=request.POST["relLottery"])
        form = PrizeForm(request.POST,instance=prize)
        if form.is_valid():
            form.save()
            return JsonResponse({"result": True})
        else:
            return JsonResponse({"result": False, "message": formerror_cat(form)})
@permission_required("article.junior_editor")
def team_list(request):
    teams = Team.objects.all()

    name = request.GET.get("name","")
    if name!="":
        teams = teams.filter(name__contains=name)
    project = int(request.GET.get("project", -1))
    if project == 1:
        teams = teams.filter(project='M')
    elif project == 0:
        teams = teams.filter(project='C')
    sport_type = int(request.GET.get("sport_type", -1))
    if sport_type == 0:
        teams = teams.filter(sport_type=0)
    elif sport_type == 1:
        teams = teams.filter(sport_type=1)
    elif sport_type == 2:
        teams = teams.filter(sport_type=2)
    paginator = Paginator(teams.order_by('-id'), 30)
    page_index = request.GET.get("page_index", 1)
    pager = paginator.page(page_index)

    return TemplateResponse(request, 'lottery/team_list.html',locals())



def euro(request):
    fixtures = Fixture.objects.filter(cup_name=u"2016年法国欧洲杯")
    if "action" not in request.GET:
        today = datetime.now().strftime("%Y-%m-%d")
        today0hour = timezone.make_aware(datetime.strptime(today + " 00:00:00", "%Y-%m-%d %H:%M:%S"))
        today24hour = today0hour + timedelta(hours=24)
        todayfixtures = fixtures.filter(start_time__gte=today0hour, start_time__lt=today24hour)
        if todayfixtures:
            day0hour = today24hour
            dayfixtures = todayfixtures
        else:
            day = timezone.localtime(fixtures.filter(start_time__gte=timezone.now())[0].start_time).strftime("%Y-%m-%d")
            day0hour = timezone.make_aware(datetime.strptime(day + " 00:00:00", "%Y-%m-%d %H:%M:%S"))
            day24hour = day0hour + timedelta(hours=24)
            dayfixtures = fixtures.filter(start_time__gte=day0hour, start_time__lt=day24hour)
    else:
        action = request.GET["action"]
        today = timezone.make_aware(datetime.strptime(request.GET["date"] + " 00:00:00", "%Y-%m-%d %H:%M:%S"))
        if action == "prev":
            day0hour = today-timedelta(days=1)

        elif action == "next":
            day0hour = today + timedelta(days=1)

        day24hour = day0hour+timedelta(hours=24)
        dayfixtures = fixtures.filter(start_time__gte=day0hour, start_time__lt=day24hour)


    return TemplateResponse(request, "lottery/euro/euro.html", {"fixtures":dayfixtures, "day":day0hour})

def euro_match(request):
    fixture = Fixture.objects.get(id=request.GET["id"])
    return TemplateResponse(request, "lottery/euro/match.html", {"fixture":fixture})

@permission_required("article.junior_editor")
def post_team(request):
    if request.method == "GET":
        if "id" not in request.GET:
            return TemplateResponse(request, 'lottery/post_team.html')
        else:
            team = Team.objects.get(id=request.GET["id"])
        return TemplateResponse(request, 'lottery/post_team.html',{"team":team})

    elif request.method =="POST":
        if "id" not in request.POST:
            team = Team()
        else:
            team = Team.objects.get(id=request.POST["id"])

        form = TeamForm(request.POST,instance=team)
        if form.is_valid():
            form.save()
            if "id" not in request.POST:
                # 新增赛队记录日志
                bms_operation_log(request.user.id, "新增赛队", "赛队ID%s" % str(Team.objects.all().latest('id').id))
            else:
                # 修改赛队记录日志
                bms_operation_log(request.user.id, "修改赛队", "赛队ID%s" % str(request.POST["id"]))
            return JsonResponse({"result": True})
        else:
            return JsonResponse({"result": False, "message": formerror_cat(form)})

@permission_required("article.junior_editor")
def fixture_list(request):
    fixtures = Fixture.objects.all()


    paginator = Paginator(fixtures.order_by("-id"), 30)
    page_index = request.GET.get("page_index", 1)
    pager = paginator.page(page_index)

    return TemplateResponse(request, 'lottery/fixture_list.html', {"pager": pager})

@permission_required("article.junior_editor")
def post_fixture(request):
    if request.method == "GET":
        if "id" not in request.GET:
            return TemplateResponse(request, 'lottery/post_fixture.html')
        else:
            fixture = Fixture.objects.get(id=request.GET["id"])
        return TemplateResponse(request, 'lottery/post_fixture.html', {"fixture": fixture})

    elif request.method == "POST":
        if "id" not in request.POST:
            fixture = Fixture()
        else:
            fixture = Fixture.objects.get(id=request.POST["id"])

        form = FixtureForm(request.POST, instance=fixture)
        if form.is_valid():
            form.save()
            return JsonResponse({"result": True})
        else:
            return JsonResponse({"result": False, "message": formerror_cat(form)})

def america(request):
    fixtures = Fixture.objects.filter(cup_name=u"2016年百年美洲杯")
    if "action" not in request.GET:
        today = datetime.now().strftime("%Y-%m-%d")
        today0hour = timezone.make_aware(datetime.strptime(today + " 00:00:00", "%Y-%m-%d %H:%M:%S"))
        today24hour = today0hour + timedelta(hours=24)
        todayfixtures = fixtures.filter(start_time__gte=today0hour, start_time__lt=today24hour)
        if todayfixtures:
            day0hour = today24hour
            dayfixtures = todayfixtures
        else:
            day = timezone.localtime(fixtures.filter(start_time__gte=timezone.now())[0].start_time).strftime("%Y-%m-%d")
            day0hour = timezone.make_aware(datetime.strptime(day + " 00:00:00", "%Y-%m-%d %H:%M:%S"))
            day24hour = day0hour + timedelta(hours=24)
            dayfixtures = fixtures.filter(start_time__gte=day0hour, start_time__lt=day24hour)
    else:
        action = request.GET["action"]
        today = timezone.make_aware(datetime.strptime(request.GET["date"] + " 00:00:00", "%Y-%m-%d %H:%M:%S"))
        if action == "prev":
            day0hour = today-timedelta(days=1)

        elif action == "next":
            day0hour = today + timedelta(days=1)

        day24hour = day0hour+timedelta(hours=24)
        dayfixtures = fixtures.filter(start_time__gte=day0hour, start_time__lt=day24hour)


    return TemplateResponse(request, "lottery/america/cup.html", {"fixtures":dayfixtures, "day":day0hour})

def america_match(request):
    return TemplateResponse(request, "lottery/america/match.html", {})

@permission_required("article.junior_editor")
def modifyMatchTime(request):
    if request.method == "POST":
        entry_id = int(request.POST.get("entry_id", "0"))
        start_time = request.POST.get("start_time", "").strip()
        try:
            start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
        except Exception, e:
            return JsonResponse({"result": False, "message": u"合法的日期格式是yyyy-mm-dd HH:MM"})
        match = Match.objects.get(lottery_entry=entry_id)
        match.start_time = start_time
        match.save()
        return JsonResponse({"result": True, "message":u"修改成功!"})
    else:
        return JsonResponse({"result": False, "message":u"unsupport http method"})

@permission_required("article.junior_editor")
def post_cup_league(request):
    if request.method == 'POST':
        cup_league_obj = CupLeague()
        if "id" not in request.POST:
            cup_league_obj = CupLeague()
        else:
            cup_league_obj = CupLeague.objects.get(id=request.POST["id"])
        form = CupLeagueForm(request.POST, instance=cup_league_obj)
        if form.is_valid():
            form.save()
            if "id" not in request.POST:
                # 新增杯赛记录日志
                bms_operation_log(request.user.id, "新增杯赛", "杯赛ID%s" % str(CupLeague.objects.all().latest('id').id))
            else:
                # 修改杯赛记录日志
                bms_operation_log(request.user.id, "修改杯赛", "杯赛ID%s" % str(request.POST["id"]))
            return JsonResponse({"result": True, "message":u"修改成功!"})
        else:
            return JsonResponse({"result": False, "message":u"数据不合法!"})
    else:
        if "id" not in request.GET:
            return TemplateResponse(request, 'lottery/post_cup_league.html')
        else:
            cup_league = CupLeague.objects.get(id=request.GET["id"])
            return TemplateResponse(request, 'lottery/post_cup_league.html', {'cupLeague': cup_league})


@permission_required("article.junior_editor")
def cup_league(request):
    cup_league_names = CupLeague.objects.all()

    name = request.GET.get('name', '')
    sport_type = int(request.GET.get("sport_type", "-1"))
    if name != '':
        cup_league_names = cup_league_names.filter(name__contains=name)
    if sport_type != -1:
        cup_league_names = cup_league_names.filter(sport_type = sport_type)
    project = int(request.GET.get("project", -1))
    if project == 2:
        cup_league_names = cup_league_names.filter(project='E')
    elif project == 1:
        cup_league_names = cup_league_names.filter(project='M')
    elif project == 0:
        cup_league_names = cup_league_names.filter(project='C')

    paginator = Paginator(cup_league_names.order_by('-id'), 30)
    page_index = request.GET.get("page_index", 1)
    pager = paginator.page(page_index)
    return TemplateResponse(request, 'lottery/cup_league_list.html', locals())

@permission_required("article.junior_editor")
def edit_match(request):
    if request.method == 'POST':
        project = request.POST.get('project')
        cup_league = request.POST.get('cup_league')
        start_time = request.POST.get('start_time')
        home_team = request.POST.get('home_team')
        away_team = request.POST.get('away_team')
        lottery_types = request.POST.getlist('lottery_types')
        match_id = request.POST.get('match_id')

        if CupLeague.objects.filter(name = cup_league,project = project).count() == 0:
            return JsonResponse({"result": False, "message": u"没有符合该语种的杯赛名称，请核对!"})
        if Team.objects.filter(name = home_team,project = project).count() == 0:
            return JsonResponse({"result": False, "message": u"没有符合该语种的主队名称，请核对!"})
        if Team.objects.filter(name = away_team,project = project).count() == 0:
            return JsonResponse({"result": False, "message": u"没有符合该语种的客队名称，请核对!"})

        if 'id' not in request.POST:
            start_time =  timezone.make_aware(datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S"))
            #判断有无临近日期的赛事,避免录错
            has_matches = Match.objects.filter(home_team=home_team,away_team=away_team,start_time__gte=start_time-timedelta(hours=12), start_time__lte=start_time+timedelta(hours=12),project = project).count()
            if has_matches > 0:
                return JsonResponse({"result":False, "message":u"开赛时间前后12小时内已有%d场比赛!" % has_matches})

            try:
                with transaction.atomic():
                    #伪造一个entry
                    m = hashlib.md5()
                    m.update(str(datetime.now()))
                    taskid = m.hexdigest()
                    entry = Lotteryentry(taskid=taskid, type_id=lottery_types[0])
                    entry.save()
                    #保存match
                    match = Match(home_team=home_team, away_team=away_team, start_time=start_time, lottery_entry=entry, cup_name=cup_league, match_id=match_id,project=project)
                    match.save()
                    for ltype in lottery_types:
                        match.lotterytypes.add(ltype)
                match_add_post(match) # 发缓存消息
                # 新增赛事记录日志
                bms_operation_log(request.user.id, "新增赛事", "赛事ID%s" % str(match.id))
                return JsonResponse({"result": True})
            except Exception, e:
                logger.error("add match error: %s", e)
                return JsonResponse({"result": False, "message": str(e)})
        else:
            match = Match.objects.get(id=request.POST.get('id'))
            match.home_team = home_team
            match.away_team = away_team
            match.start_time = timezone.make_aware(datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S"))
            match.cup_name = cup_league
            match.match_id = match_id
            match.project = project
            try:
                match.save()
                match_put_post(match)  # 发缓存消息
                match.lotterytypes.clear()
                for ltype in lottery_types:
                    match.lotterytypes.add(ltype)

                return JsonResponse({"result": True})
            except Exception, e:
                logger.error("update match %d error: %s", match.id, str(e))
                return JsonResponse({"result": False, "message": str(e)})
    else:
        cup_leagues = CupLeague.objects.all()
        # teams = Team.objects.all()
        lottery_types = Lotterytype.objects.filter(parent__name=u'竞技彩')
        if 'id' in request.GET:
            match = Match.objects.get(id=request.GET.get('id'))
            match.lottery_types = []
            match.cup_league = match.cup_name
            for t in match.lotterytypes.all():
                match.lottery_types.append(t.id)
        return TemplateResponse(request, 'lottery/post_lottery.html', locals())

@permission_required("article.junior_editor")
def del_match(request):
    if request.method == 'POST':
        match_id = request.POST.get('match_id')
        if match_id == None:
            return JsonResponse({"result":False, "message": u"需要match_id"})
        match = Match.objects.get(id=match_id)
        try:
            with transaction.atomic():
                match.lottery_entry.delete()
                match.lotterytypes.clear()
                match.delete()
                match_del_post(match) #删除赛事往消息队列里扔消息
                # 删除赛事记录日志
                bms_operation_log(request.user.id, "删除赛事", "赛事ID%s" % str(match_id))
                return JsonResponse({"result":True, "message": u'删除成功'})
        except Exception,e:
            logger.error("delete match %d error: %s", match.id, e)
            return JsonResponse({"result":False, "message": str(e)})
    return JsonResponse({"result":False, "message": "invalid request!"})

@permission_required("article.junior_editor")
def rx9_list(request):
    ren_xuans = RenXuan.objects.all()
    issue = request.GET.get("issue", '')
    if issue != '':
        ren_xuans = ren_xuans.filter(issue__contains=issue)

    paginator = Paginator(ren_xuans.order_by('-id'), 30)
    page_index = request.GET.get("page_index", 1)
    pager = paginator.page(page_index)
    return TemplateResponse(request, 'lottery/ren_xuan_list.html', locals())

@permission_required("article.junior_editor")
def edit_rx9(request):
    if request.method == 'POST':
        issue = request.POST.get('issue')
        end_time = request.POST.get('end_time')

        if "id" not in request.POST:
            ren_xuan_obj = RenXuan()
        else:
            ren_xuan_obj = RenXuan.objects.get(id=request.POST["id"])
        form = RenXuanForm(request.POST, instance=ren_xuan_obj)
        if form.is_valid():
            form.save()
            return JsonResponse({"result": True, "message":u"修改成功!"})
        else:
            return JsonResponse({"result": False, "message":u"数据不合法!"})

    else:
        ren_xuans = RenXuan.objects.all()
        if 'id' in request.GET:
            renXuan = RenXuan.objects.get(id=request.GET.get('id'))

        return TemplateResponse(request, 'lottery/post_ren_xuan.html', locals())

@permission_required("article.junior_editor")
def del_rx9(request):
    if request.method == 'POST':
        ren_xuan_id = request.POST.get('id')
        if ren_xuan_id == None:
            return JsonResponse({"result":False, "message": u"需要id"})
        ren_xuan = RenXuan.objects.get(id=ren_xuan_id)
        try:
            with transaction.atomic():
                ren_xuan.delete()
                return JsonResponse({"result":True, "message": u'删除成功'})
        except Exception,e:
            logger.error("delete renxuan %d error: %s", ren_xuan_id, e)
            return JsonResponse({"result":False, "message": str(e)})
    return JsonResponse({"result":False, "message": "invalid request!"})

def insert_match_from_football(scout_football_match_info,project):
    match = Match()
    match.scout_match_id = scout_football_match_info[0]
    # 时间格式转化
    timestrp = time.strptime(scout_football_match_info[1], '%Y/%m/%d %H:%M:%S')
    y, m, d, H, M, S = timestrp[0:6]
    start_time = datetime(y, m, d, H, M, S)
    match.start_time = start_time
    match.match_id = ''
    type_ids = []
    entry_type_id = Lotterytype.QITA_SAISHI #默认为其他赛事
    if scout_football_match_info[0] in ScoutMatch.objects.all().values_list('match_id', flat=True): #如果该赛事在ScoutMatch关联表中
        scout_matches = ScoutMatch.objects.filter(match_id=scout_football_match_info[0]) #取出关联数据,可能多条
        for scout_matche in scout_matches:
            if scout_matche.lottery_name == u'竞彩足球':
                entry_type_id = Lotterytype.JINGCAI_FOOTBALL
                match.match_id = scout_matche.scene_id #只有竞彩足球才显示彩期
                if Lotterytype.JINGCAI_FOOTBALL not in type_ids:
                    type_ids.append(Lotterytype.JINGCAI_FOOTBALL)
            elif scout_matche.lottery_name == u'北京单场胜负过关':
                entry_type_id = Lotterytype.BEIDAN_FOOTBALL
                if Lotterytype.BEIDAN_FOOTBALL not in type_ids:
                    type_ids.append(Lotterytype.BEIDAN_FOOTBALL)
            else:
                entry_type_id = Lotterytype.CHUANTONG_FOOTBALL #传统足球
                if Lotterytype.CHUANTONG_FOOTBALL not in type_ids:
                    type_ids.append(Lotterytype.CHUANTONG_FOOTBALL)

    m = hashlib.md5()
    m.update(str(datetime.now()))
    taskid = m.hexdigest()
    entry = Lotteryentry(taskid=taskid, type_id=entry_type_id)
    entry.save()
    match.lottery_entry = entry

    if project == 'M':
        match.cup_name = scout_football_match_info[2]
        match.home_team = scout_football_match_info[4]
        match.away_team = scout_football_match_info[6]
        match.project = project
    elif project == 'C':
        match.cup_name = scout_football_match_info[3]
        match.home_team = scout_football_match_info[5]
        match.away_team = scout_football_match_info[7]
        match.project = project
    elif project == 'E':
        match.cup_name = scout_football_match_info[8]
        match.home_team = scout_football_match_info[9]
        match.away_team = scout_football_match_info[10]
        match.project = project

    match.save()
    match_add_post(match)  # 发缓存消息,给推推同步赛事用

    if len(type_ids) == 0:
        type_ids.append(Lotterytype.QITA_SAISHI)

    for type_id in type_ids:
        match_lotterytype = MatchLotterytypes()
        match_lotterytype.match_id = match.id
        match_lotterytype.lotterytype_id = type_id
        match_lotterytype.save()


def insert_match_from_basketball(scout_basketball_match_info,project):
    match = Match()
    match.scout_match_id = scout_basketball_match_info[0]
    # 时间格式转化
    timestrp = time.strptime(scout_basketball_match_info[1], '%Y/%m/%d %H:%M:%S')
    y, m, d, H, M, S = timestrp[0:6]
    start_time = datetime(y, m, d, H, M, S)
    match.start_time = start_time
    match.match_id = ''
    type_ids = []
    entry_type_id = Lotterytype.QITA_SAISHI
    if scout_basketball_match_info[0] in ScoutMatch.objects.all().values_list('match_id', flat=True):
        scout_matches = ScoutMatch.objects.filter(match_id=scout_basketball_match_info[0])
        for scout_matche in scout_matches:
            if scout_matche.lottery_name == u'竞彩篮球':
                entry_type_id = Lotterytype.JINGCAI_BASKETBALL
                match.match_id = scout_matche.scene_id  # 只有竞彩篮球才显示彩期
                if Lotterytype.JINGCAI_BASKETBALL not in type_ids:
                    type_ids.append(Lotterytype.JINGCAI_BASKETBALL)

    m = hashlib.md5()
    m.update(str(datetime.now()))
    taskid = m.hexdigest()
    entry = Lotteryentry(taskid=taskid, type_id=entry_type_id)
    entry.save()
    match.lottery_entry = entry

    if project == 'M':
        match.cup_name = scout_basketball_match_info[2]
        match.home_team = scout_basketball_match_info[4]
        match.away_team = scout_basketball_match_info[6]
        match.project = project
    elif project == 'C':
        match.cup_name = scout_basketball_match_info[3]
        match.home_team = scout_basketball_match_info[5]
        match.away_team = scout_basketball_match_info[7]
        match.project = project
    elif project == 'E':
        match.cup_name = scout_basketball_match_info[8]
        match.home_team = scout_basketball_match_info[9]
        match.away_team = scout_basketball_match_info[10]
        match.project = project

    match.save()
    match_add_post(match)

    if len(type_ids) == 0:
        type_ids.append(Lotterytype.QITA_SAISHI)

    for type_id in type_ids:
        match_lotterytype = MatchLotterytypes()
        match_lotterytype.match_id = match.id
        match_lotterytype.lotterytype_id = type_id
        match_lotterytype.save()

def insert_cupleague_from_football(scout_football_match_info, project):
    cup_league = CupLeague()
    cup_league.type = 0
    cup_league.status = 0
    cup_league.op_id = 0
    cup_league.sport_type = 0
    cup_league.project = project
    if project == 'M':
        cup_league.name = scout_football_match_info[2]
    elif project == 'C':
        cup_league.name = scout_football_match_info[3]
    elif project == 'E':
        cup_league.name = scout_football_match_info[8]
    if CupLeague.objects.filter(name=cup_league.name,project=project).count() == 0:
        cup_league.save()
        # 国语杯赛调推推杯赛接口
        if project == 'M':
            url = "http://bms.tuisaishi.com/restapi/cup/"
            data = model_to_dict(cup_league)
            headers = {"Content-Type": "application/json"}
            requests.post(url=url, headers=headers, data=json.dumps(data, default=DatetimeJsonEncoder))

def insert_cupleague_from_basketball(scout_basketball_match_info, project):
    cup_league = CupLeague()
    cup_league.type = 0
    cup_league.status = 0
    cup_league.op_id = 0
    cup_league.sport_type = 1
    cup_league.project = project
    if project == 'M':
        cup_league.name = scout_basketball_match_info[2]
    elif project == 'C':
        cup_league.name = scout_basketball_match_info[3]
    elif project == 'E':
        cup_league.name = scout_basketball_match_info[8]
    if CupLeague.objects.filter(name=cup_league.name,project=project).count() == 0:
        cup_league.save()
        if project == 'M':
            url = "http://bms.tuisaishi.com/restapi/cup/"
            data = model_to_dict(cup_league)
            headers = {"Content-Type": "application/json"}
            requests.post(url=url, headers=headers, data=json.dumps(data, default=DatetimeJsonEncoder))

# 更新赛事表开赛时间
def update_match_start_time(table_modify):
    matches = Match.objects.filter(scout_match_id=table_modify.match_id)  # 过滤有更新的赛事,含国语和粤语
    for match in matches:
        if table_modify.type == 'modify':
            timestrp = time.strptime(table_modify.match_time, '%Y/%m/%d %H:%M:%S')
            y, m, d, H, M, S = timestrp[0:6]
            start_time = datetime(y, m, d, H, M, S)
            match.start_time = start_time
            match.save()
        elif table_modify.type == 'delete':
            match.delete()

def select_scout_match_sql(table, from_date, to_date):
    if table == 'scout_football_match_info':
        cursor = connection.cursor()
        cursor.execute("""SELECT
                SFMI.id,
                SFMI.start_time,
                SFMI.gb,
                SFMI.big,
                SFMI.home_team_gb,
                SFMI.home_team_big,
                SFMI.guest_team_gb,
                SFMI.guest_team_big,
                SFMI.en,
                SFMI.home_team_en,
                SFMI.guest_team_en
            FROM scout_football_match_info SFMI
            WHERE
                to_timestamp(SFMI.start_time, 'YYYY/MM/DD HH24:MI:SS') >= '%s'
            AND
                to_timestamp(SFMI.start_time, 'YYYY/MM/DD HH24:MI:SS') <= '%s'
            """ % (from_date, to_date))
        return cursor.fetchall()
    elif table == 'scout_basketball_match_info':
        cursor = connection.cursor()
        cursor.execute("""SELECT
                SBMI.id,
                SBMI.start_time,
                SBMI.league_cup_name_gb,
                SBMI.league_cup_name_big,
                SBMI.home_team_gb,
                SBMI.home_team_big,
                SBMI.guest_team_gb,
                SBMI.guest_team_big,
                SBL.en,
                SBTI1.en as "home_team_en",
                SBTI2.en as "guest_team_en"
            FROM scout_basketball_match_info SBMI, scout_basketball_team_info SBTI1,
                 scout_basketball_team_info SBTI2, scout_basketball_league SBL
            WHERE
                SBMI.home_team_id = SBTI1.id AND SBMI.guest_team_id = SBTI2.id
            AND
                SBMI.league_cup_id = SBL.id
            AND
                to_timestamp(SBMI.start_time, 'YYYY/MM/DD HH24:MI:SS') >= '%s'
            AND
                to_timestamp(SBMI.start_time, 'YYYY/MM/DD HH24:MI:SS') <= '%s'
            """ % (from_date, to_date))
        return cursor.fetchall()