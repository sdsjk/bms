# coding:utf-8
import sys,os,django
import redis

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) #manage.py的目录
#sys.path.append("/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages")
os.environ['DJANGO_SETTINGS_MODULE'] = 'jcsbms.settings' #setting的目录
django.setup()
from lottery.models import ScoutFootballMatchScore
import time
import datetime
from django.utils import timezone
from settings import REDIS_HOST, REDIS_PASSOWRD


class Task(object):
    def __init__(self):
        self.rcon = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0, password=REDIS_PASSOWRD)
        self.ps = self.rcon.pubsub()
        self.ps.subscribe('fb.score.instant.close.notify')

    def listen_task(self):

        for i in self.ps.listen():
            print str(i)
            if i['type'] == 'message' and i['channel'] == 'fb.score.instant.close.notify':
                try:
                    print str(datetime.datetime.now())+"::"+"have score match get", i['data']
                    today = datetime.date.today().strftime("%Y%m%d")
                    yesterday = str(int(datetime.date.today().strftime("%Y%m%d"))-1)
                    redis_name_today = "fb.score.today." + today
                    redis_name_yesterday = "fb.score.today." + yesterday
                    data_list = list(eval(i['data']))
                    for key in data_list:
                        data = self.rcon.hget(redis_name_today, key)
                        if not data:
                            data = eval(self.rcon.hget(redis_name_yesterday, key))
                        else:
                            data = eval(self.rcon.hget(redis_name_today, key))
                        sfms = ScoutFootballMatchScore()
                        # 时间格式转化
                        timestrp1 = time.strptime(data['gameTime'], '%Y/%m/%d %H:%M:%S')
                        y1, m1, d1, H1, M1, S1 = timestrp1[0:6]
                        gameTime = datetime.datetime(y1, m1, d1, H1, M1, S1)

                        timestrp2 = time.strptime(datetime.datetime.fromtimestamp(float(str(data['createTime'])[:-3])).strftime('%Y/%m/%d %H:%M:%S'), '%Y/%m/%d %H:%M:%S')
                        y2, m2, d2, H2, M2, S2 = timestrp2[0:6]
                        create_time = datetime.datetime(y2, m2, d2, H2, M2, S2)

                        if data.get('gameStartTime','') != '':
                            timestrp3 = time.strptime(data['gameStartTime'], '%Y/%m/%d %H:%M:%S')
                            y3, m3, d3, H3, M3, S3 = timestrp3[0:6]
                            gameStartTime = datetime.datetime(y3, m3, d3, H3, M3, S3)
                            sfms.gameStartTime = gameStartTime

                        sfms.match_id = int(data['matchId'])
                        sfms.color = data.get('color',None)
                        sfms.league_id = int(data.get('leagueId')) if data.get('leagueId',None) else None
                        sfms.kind = data.get('kind',None)
                        sfms.level = data.get('level',None)
                        sfms.gb = data['gb']
                        sfms.big = data['big']
                        sfms.en = data['en']
                        sfms.sub_league = data.get('subLeague',None)
                        sfms.sub_league_id = int(data.get('subLeagueId')) if data.get('subLeagueId',None) else None
                        sfms.gameTime = gameTime
                        sfms.home_team_gb = data['homeTeamGb']
                        sfms.home_team_big = data['homeTeamBig']
                        sfms.home_team_en = data['homeTeamEn']
                        sfms.home_team_id = int(data['homeTeamId'])
                        sfms.guest_team_gb = data['guestTeamGb']
                        sfms.guest_team_big = data['guestTeamBig']
                        sfms.guest_team_en = data['guestTeamEn']
                        sfms.guest_team_id = int(data['guestTeamId'])
                        sfms.home_team_score = data.get('homeTeamScore',None)  #主队比分
                        sfms.guest_team_score = data.get('guestTeamScore',None)#客队比分
                        sfms.home_team_half_score = data.get('homeTeamHalfScore',None)  #主队半场比分
                        sfms.guest_team_half_score = data.get('guestTeamHalfScore',None)#客队半场比分
                        sfms.home_team_red_card = data.get('homeTeamRedCard',None)
                        sfms.guest_team_red_card = data.get('guestTeamRedCard',None)
                        sfms.home_team_yellow_card = data.get('homeTeamYellowCard',None)
                        sfms.guest_team_yellow_card = data.get('guestTeamYellowCard',None)
                        sfms.home_team_rank = data.get('homeTeamRank',None)
                        sfms.guest_team_rank = data.get('guestTeamRank',None)
                        sfms.match_explain = data.get('matchExplain',None)
                        sfms.match_explain2 = data.get('matchExplain2',None)
                        sfms.position_flag = data.get('positionFlag',None)
                        sfms.match_status = data.get('matchStatus',None)
                        sfms.live = data.get('live',None)
                        sfms.lineup = data.get('lineUp',None)
                        sfms.home_team_corner = data.get('homeTeamCorner',None)
                        sfms.guest_team_corner = data.get('guestTeamCorner',None)
                        sfms.create_time = create_time
                        sfms.save()

                except Exception as e:
                    print e.message

if __name__ == '__main__':

    print str(datetime.datetime.now())+"::"+'start listen'
    Task().listen_task()
