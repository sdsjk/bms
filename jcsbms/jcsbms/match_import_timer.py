# coding:utf-8
import sys,os,django
from datetime import timedelta,datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) #manage.py的目录
os.environ['DJANGO_SETTINGS_MODULE'] = 'jcsbms.settings' #setting的目录
django.setup()
from apscheduler.schedulers.blocking import BlockingScheduler
from lottery.views import insert_match_from_football, select_scout_match_sql, insert_match_from_basketball, \
    insert_cupleague_from_football, insert_cupleague_from_basketball
from lottery.models import Match, CupLeague


def scout_match_import():

    print 'start import match at ', datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    from_date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    to_date = (datetime.now() + timedelta(hours=48)).strftime("%Y/%m/%d %H:%M:%S")

    scout_football_match_infos = select_scout_match_sql('scout_football_match_info', from_date, to_date) #使用sql按指定时间查询球探足球表
    scout_basketball_match_infos = select_scout_match_sql('scout_basketball_match_info', from_date, to_date)

    scout_match_id_list = Match.objects.filter(scout_match_id__isnull=False).values_list('scout_match_id', flat=True) #match表scout_match_id不为空
    cup_league_name_foot_man_list = list(CupLeague.objects.filter(project='M', sport_type= 0).values_list('name', flat=True))
    cup_league_name_foot_cant_list = list(CupLeague.objects.filter(project='C', sport_type= 0).values_list('name', flat=True))
    cup_league_name_foot_en_list = list(CupLeague.objects.filter(project='E', sport_type=0).values_list('name', flat=True))
    cup_league_name_basket_man_list = list(CupLeague.objects.filter(project='M', sport_type= 1).values_list('name', flat=True))
    cup_league_name_basket_cant_list = list(CupLeague.objects.filter(project='C', sport_type= 1).values_list('name', flat=True))
    cup_league_name_basket_en_list = list(CupLeague.objects.filter(project='E', sport_type=1).values_list('name', flat=True))

    #足球
    for scout_football_match_info in scout_football_match_infos:
        # 如果对象不在Match表中,则开始新建数据
        if scout_football_match_info[0] not in scout_match_id_list:
            insert_match_from_football(scout_football_match_info,project='M') #插入国语赛事,from scout_football_match_info
            insert_match_from_football(scout_football_match_info,project='C') #插入粤语赛事,from scout_football_match_info
            insert_match_from_football(scout_football_match_info, project='E')#插入英语赛事,from scout_football_match_info
        if scout_football_match_info[2] not in cup_league_name_foot_man_list:
            insert_cupleague_from_football(scout_football_match_info, project='M') #插入国语杯赛, to lottery_cup_league
            cup_league_name_foot_man_list.append(scout_football_match_info[2])
        if scout_football_match_info[3] not in cup_league_name_foot_cant_list:
            insert_cupleague_from_football(scout_football_match_info, project='C') #插入粤语杯赛, to lottery_cup_league
            cup_league_name_foot_cant_list.append(scout_football_match_info[3])
        if scout_football_match_info[8] not in cup_league_name_foot_en_list:
            insert_cupleague_from_football(scout_football_match_info, project='E') #插入英语杯赛, to lottery_cup_league
            cup_league_name_foot_en_list.append(scout_football_match_info[8])


    #篮球
    for scout_basketball_match_info in scout_basketball_match_infos:
        if scout_basketball_match_info[0] not in scout_match_id_list:
            insert_match_from_basketball(scout_basketball_match_info,project='M')
            insert_match_from_basketball(scout_basketball_match_info,project='C')
            insert_match_from_basketball(scout_basketball_match_info, project='E')
        if scout_basketball_match_info[2] not in cup_league_name_basket_man_list:
            insert_cupleague_from_basketball(scout_basketball_match_info,project='M')
            cup_league_name_basket_man_list.append(scout_basketball_match_info[2])
        if scout_basketball_match_info[3] not in cup_league_name_basket_cant_list:
            insert_cupleague_from_basketball(scout_basketball_match_info, project='C')
            cup_league_name_basket_cant_list.append(scout_basketball_match_info[3])
        if scout_basketball_match_info[8] not in cup_league_name_basket_en_list:
            insert_cupleague_from_basketball(scout_basketball_match_info, project='E')
            cup_league_name_basket_en_list.append(scout_basketball_match_info[8])

    print 'import match over at', datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    print '-----------------------------------------------------------------------'

if __name__ == '__main__':

    scheduler = BlockingScheduler()
    scheduler.add_job(scout_match_import, 'cron', hour=12)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()