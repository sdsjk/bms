# coding:utf-8
from django.db import models

# Create your models here.
from django_redis import get_redis_connection
from mongoengine import Document, ObjectIdField, StringField, FloatField, URLField

from jcsbms.utils import connect_mongodb, getLocalDateTime


class Lotterytype(models.Model):
    JINGCAI_FOOTBALL = 6
    BEIDAN_FOOTBALL = 7
    CHUANTONG_FOOTBALL = 8
    JINGCAI_BASKETBALL = 9
    QITA_SAISHI = 13

    name = models.CharField(max_length=16)
    parent = models.ForeignKey("Lotterytype",null=True)

    def __unicode__(self):
        return self.name

class Lotteryentry(models.Model):
    taskid = models.CharField(null=True,max_length=32,unique=True)
    type = models.ForeignKey(Lotterytype)

class MatchLotterytypes(models.Model):
    match_id = models.IntegerField()
    lotterytype = models.ForeignKey(Lotterytype)

    class Meta:
        db_table = 'lottery_match_lotterytypes'

class Team(models.Model):
    SPORT_TYPE_FOOTBALL   = 0
    SPORT_TYPE_BASKETBALL = 1

    sport_type = models.SmallIntegerField()
    name = models.CharField(max_length=16,db_index=True)
    logo = models.CharField(max_length=120,null=True)
    introduction = models.CharField(max_length=512,null=True)
    project = models.CharField(max_length=32, default='M')

    class Meta:
        unique_together = ("sport_type", "name", "project")


class CupLeague(models.Model):
    name=models.CharField()
    type=models.IntegerField()
    status=models.IntegerField()
    create_time=models.DateTimeField()
    update_time=models.DateTimeField()
    op_id=models.IntegerField()
    sport_type=models.IntegerField()
    project=models.CharField()
class Match(models.Model):
    lottery_entry = models.OneToOneField(Lotteryentry)
    cup_name = models.CharField(max_length=64)
    start_time = models.DateTimeField()
    home_team = models.CharField(max_length=64)
    away_team = models.CharField(max_length=64)
    match_id = models.CharField(max_length=32,null=True)
    lotterytypes = models.ManyToManyField(Lotterytype)
    project = models.CharField(max_length=32, default='M')
    scout_match_id = models.IntegerField()
    sport_type=models.IntegerField()
    syn_date=models.DateTimeField()
    def __unicode__(self):
        return u"%s: %sVS%s %s" % (self.cup_name, self.home_team, self.away_team, self.start_time.strftime("%Y-%m-%d %H:%M:%S") )

    def getDictForCache(self):
        return {"entry_id":self.lottery_entry_id, "cup_name":self.cup_name, "home_team":self.home_team, "away_team":self.away_team, "start_time":getLocalDateTime(self.start_time).strftime("%Y-%m-%d %H:%M:%S")}


class Lotto(models.Model):
    lottery_entry = models.OneToOneField(Lotteryentry)
    season = models.CharField(max_length=16)
    end_time = models.DateTimeField()





class TeamName(models.Model):
    cup_name = models.CharField(max_length=16)
    original_name = models.CharField(max_length=16)
    standard_name = models.CharField(max_length=16,null=True)
    checked = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together=("cup_name","original_name")



class MatchResult(Document):
    connect_mongodb()

    id = ObjectIdField("_id")
    result = StringField()
    updatetime = FloatField()
    taskid = StringField()
    project = StringField(null=True)
    url = URLField()
    meta = {
        'collection': 'all_matchs'
    }

class Prize(models.Model):
    match = models.ForeignKey(Match)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    reward = models.IntegerField()
    description = models.CharField(max_length=625)
    date_added = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)


class Fixture(models.Model):
    cup_name = models.CharField(max_length=16)
    start_time = models.DateTimeField()
    home_team = models.CharField(max_length=16)
    away_team = models.CharField(max_length=16)
    remark = models.CharField(max_length=100)
    match = models.ForeignKey(Match,null=True)

class CupLeague(models.Model):
    SPORT_TYPE_FOOTBALL   = 0
    SPORT_TYPE_BASKETBALL = 1

    sport_type = models.SmallIntegerField()
    name = models.CharField(max_length=64, default='')
    type = models.SmallIntegerField(default=0)
    status = models.SmallIntegerField(default=0)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    op_id = models.IntegerField(default=0)
    project = models.CharField(max_length=32, default='M')

    class Meta:
        db_table = 'lottery_cup_league'
        unique_together = ("sport_type", "name", "project")


class RenXuan(models.Model):

    issue = models.CharField(max_length = 30, unique=True)
    end_time = models.DateTimeField()
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    op_id = models.IntegerField(default=0)
    match1 = models.CharField(max_length=100)
    match2 = models.CharField(max_length=100)
    match3 = models.CharField(max_length=100)
    match4 = models.CharField(max_length=100)
    match5 = models.CharField(max_length=100)
    match6 = models.CharField(max_length=100)
    match7 = models.CharField(max_length=100)
    match8 = models.CharField(max_length=100)
    match9 = models.CharField(max_length=100)
    match10 = models.CharField(max_length=100)
    match11 = models.CharField(max_length=100)
    match12 = models.CharField(max_length=100)
    match13 = models.CharField(max_length=100)
    match14 = models.CharField(max_length=100)

    class Meta:
        db_table = 'lottery_ren_xuan'


class ScoutFootballMatchInfo(models.Model):
    start_time = models.CharField(max_length=255)
    gb = models.CharField(max_length=255) #联赛杯赛简体中文名
    big = models.CharField(max_length=255) #联赛杯赛繁体中文名
    en = models.CharField(max_length=255)  # 联赛杯赛英文名
    home_team_gb = models.CharField(max_length=255) #主队简体中文名
    home_team_big = models.CharField(max_length=255) #主队繁体中文名
    guest_team_gb = models.CharField(max_length=255) #客队简体中文名
    guest_team_big = models.CharField(max_length=255) #客队繁体中文名
    home_team_en = models.CharField(max_length=255) #主队英文名
    guest_team_en = models.CharField(max_length=255) #客队英文名

    class Meta:
        db_table = 'scout_football_match_info'


class ScoutBasketballMatchInfo(models.Model):
    start_time = models.CharField(max_length=255)
    home_team_gb = models.CharField(max_length=255) #主队简体中文名
    home_team_big = models.CharField(max_length=255) #主队繁体中文名
    guest_team_gb = models.CharField(max_length=255) #客队简体中文名
    guest_team_big = models.CharField(max_length=255) #客队繁体中文名
    league_cup_name_gb = models.CharField(max_length=255) #联赛杯赛简体中文名
    league_cup_name_big = models.CharField(max_length=255) #联赛杯赛繁体中文名

    class Meta:
        db_table = 'scout_basketball_match_info'


class ScoutMatch(models.Model):
    match_id = models.IntegerField(primary_key=True)
    lottery_name = models.CharField(max_length=255)
    scene_id = models.CharField(max_length=32)
    create_time = models.DateTimeField()

    class Meta:
        db_table = 'scout_match'

class ScoutFootballMatchModify(models.Model):
    match_id = models.IntegerField(primary_key=True)
    type = models.CharField(max_length=255)
    match_time = models.CharField(max_length=255)
    create_time = models.DateTimeField()

    class Meta:
        db_table = 'scout_football_match_modify'

class ScoutBasketballMatchModify(models.Model):
    match_id = models.IntegerField(primary_key=True)
    type = models.CharField(max_length=255)
    match_time = models.CharField(max_length=255)
    create_time = models.DateTimeField()

    class Meta:
        db_table = 'scout_basketball_match_modify'

class ScoutFootballMatchScore(models.Model):
    match_id = models.IntegerField(primary_key=True)
    color = models.CharField(max_length=255)
    league_id = models.IntegerField()
    kind = models.CharField(max_length=255)
    level = models.CharField(max_length=255)
    gb = models.CharField(max_length=255) #联赛国语名全称
    big = models.CharField(max_length=255)#联赛繁体名全称
    en = models.CharField(max_length=255) #联赛英文名全称
    sub_league = models.CharField(max_length=255)
    sub_league_id = models.IntegerField()
    gameTime = models.DateTimeField() #比赛时间
    gameStartTime = models.DateTimeField() #开场时间
    home_team_gb = models.CharField(max_length=255) #主队球队简体名称
    home_team_big = models.CharField(max_length=255)#主队球队繁体名称
    home_team_en = models.CharField(max_length=255) #主队球队英文名称
    home_team_id = models.IntegerField()
    guest_team_gb = models.CharField(max_length=255) #客队球队简体名称
    guest_team_big = models.CharField(max_length=255)#客队球队繁体名称
    guest_team_en = models.CharField(max_length=255) #客队球队英文名称
    guest_team_id = models.IntegerField()
    home_team_score = models.CharField(max_length=255) #主队比分
    guest_team_score = models.CharField(max_length=255)#客队比分
    home_team_half_score = models.CharField(max_length=255) #主队半场比分
    guest_team_half_score = models.CharField(max_length=255)#客队半场比分
    home_team_red_card = models.CharField(max_length=255)
    guest_team_red_card = models.CharField(max_length=255)
    home_team_yellow_card = models.CharField(max_length=255)
    guest_team_yellow_card = models.CharField(max_length=255)
    home_team_rank = models.CharField(max_length=255)
    guest_team_rank = models.CharField(max_length=255)
    match_explain = models.CharField(max_length=255)
    match_explain2 = models.CharField(max_length=255)
    position_flag = models.CharField(max_length=255)
    match_status = models.CharField(max_length=255)
    live = models.CharField(max_length=255)
    lineup = models.CharField(max_length=255)
    home_team_corner = models.CharField(max_length=255) #主队角球
    guest_team_corner = models.CharField(max_length=255)#客队角球
    create_time = models.DateTimeField()
    end_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'scout_football_match_score'

# class RenXuanMatch(models.Model):
#     rx9 = models.ForeignKey(RenXuan, related_name='match_set')
#     match_name = models.CharField(max_length=100)
#     class Meta:
#         db_table = 'lottery_ren_xuan_match'

def article_del_post(article):
    con = get_redis_connection("default")
    con.publish("article_del", str(article.id))

def match_add_post(match):
    con = get_redis_connection("default")
    con.publish("match_add", str(match.id))

def match_put_post(match):
    con = get_redis_connection("default")
    con.publish("match_put", str(match.id))

def match_del_post(match):
    con = get_redis_connection("default")
    con.publish("match_del", str(match.id))

def portal_add_post(portal):
    con = get_redis_connection("default")
    con.publish("portal_add", str(portal.id))

def analyst_add_post(analyst):
    con = get_redis_connection("default")
    con.publish("analyst_add", str(analyst.id))