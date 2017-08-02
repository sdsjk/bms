# coding:utf-8
import sys,os,django
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) #manage.py的目录
os.environ['DJANGO_SETTINGS_MODULE'] = 'jcsbms.settings' #setting的目录
django.setup()
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from lottery.views import update_match_start_time
from lottery.models import ScoutFootballMatchModify, Match, ScoutBasketballMatchModify, ScoutMatch, MatchLotterytypes


def match_update():

    start_time = time.clock()
    print 'start match update at ', datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    from_date =  datetime.datetime.strptime(str(datetime.date.today()) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    to_date = datetime.datetime.strptime(str(datetime.date.today()) + " 23:59:59", "%Y-%m-%d %H:%M:%S")

    football_match_modifys = ScoutFootballMatchModify.objects.filter(create_time__gte=from_date, create_time__lte=to_date)
    for football_match_modify in football_match_modifys:
        update_match_start_time(football_match_modify)

    basketball_match_modifys = ScoutBasketballMatchModify.objects.filter(create_time__gte=from_date, create_time__lte=to_date)
    for basketball_match_modify in basketball_match_modifys:
        update_match_start_time(basketball_match_modify)

    end_time = time.clock()
    print 'Running time: %s Seconds' % (end_time - start_time)
    print '-----------------------------------------------------------------------'

def match_lottery_update():

    count = 0
    start_time = time.clock()
    print 'start update match lotterytype at ', datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    from_date = datetime.datetime.strptime(str(datetime.date.today()) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    to_date = datetime.datetime.strptime(str(datetime.date.today()) + " 23:59:59", "%Y-%m-%d %H:%M:%S")

    scoutmatches = ScoutMatch.objects.filter(create_time__gte=from_date, create_time__lte=to_date)
    for scoutmatch in scoutmatches:
        if scoutmatch.lottery_name == u"竞彩足球":
            lotterytype_id = 6
        elif scoutmatch.lottery_name == u'竞彩篮球':
            lotterytype_id = 9
        elif scoutmatch.lottery_name == u'北京单场胜负过关':
            lotterytype_id = 7
        else:
            lotterytype_id = 8 # 传统足球

        matches = Match.objects.filter(scout_match_id=scoutmatch.match_id)
        if matches.count() > 0:#赛事存在才保存赛事彩种
            for match in matches:
                match_lotterytypes_ids = MatchLotterytypes.objects.filter(match_id=match.id).values_list('lotterytype_id',flat=True) #赛事的关联彩种id
                if lotterytype_id not in match_lotterytypes_ids:
                    MatchLotterytypes(
                        match_id = match.id,
                        lotterytype_id = lotterytype_id
                    ).save()
                    count += 1
                    if lotterytype_id == 6:
                        match.match_id = scoutmatch.scene_id
                        match.save()

    end_time = time.clock()
    print 'Running time: %s Seconds'%(end_time-start_time)
    print 'Update match lotterytype %d rows'%count
    print '-----------------------------------------------------------------------'

if __name__ == '__main__':

    scheduler = BlockingScheduler()
    scheduler.add_job(match_update, 'interval', hours=1)
    scheduler.add_job(match_lottery_update, 'interval', minutes=5)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()