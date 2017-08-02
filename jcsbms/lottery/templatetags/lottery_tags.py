# coding:utf-8
'''
Created on 2015-11-10

@author: stone
'''
from django import template
from ..models import Lotterytype, Team, Match
from django.utils import timezone


register = template.Library()
@register.inclusion_tag('lottery/analyst_lotterytype.html')
def analyst_lotterytype():

    return {"lottery_types":Lotterytype.objects.filter(parent__isnull=True)}

@register.inclusion_tag('lottery/lotterytype_selector.html')
def lotterytype_selector():

    return {"lottery_types":Lotterytype.objects.filter(parent__isnull=False)}
@register.inclusion_tag('lottery/lotterytype_selector.html')
def alllotterytype_selector(lottery_type_id):

    return {"lottery_types":Lotterytype.objects.all(), "lottery_type_id":lottery_type_id}


@register.inclusion_tag('lottery/lotterytype_selector.html')
def parentlotterytype_selector():

    return {"lottery_types":Lotterytype.objects.filter(parent__isnull=True)}

@register.inclusion_tag('lottery/lottery_select.html', takes_context=True)
def lottery_select(context):
    if "article" in context:
        lottery_list=[]
        for lottery in context["article"].lotteries.all():
            lottery_value = {}
            lottery_value["id"] = lottery.id
            if hasattr(lottery,"match"):
                match = lottery.match
                lottery_value["name"] = timezone.localtime(match.start_time).strftime("%m-%d %H:%M")+":\t"+"Cup:\t"+match.cup_name+";\t"+match.home_team+" \t VS \t"\
                                        +match.away_team
                                        #+"["+match.lottery_entry.type.name+"]"
            elif hasattr(lottery,"lotto"):
                lotto = lottery.lotto
                lottery_value["name"] = lottery.type.name +":"+lotto.season
            lottery_list.append(lottery_value)
        return {"lotteries":lottery_list,"lottery_types":Lotterytype.objects.filter(parent__isnull=True)}
    else:
        return {"lottery_types":Lotterytype.objects.filter(parent__isnull=True)}



@register.inclusion_tag('lottery/analystlottery_select.html', takes_context=True)
def analystlottery_select(context):
    if "article" in context:
        lottery_list=[]
        for lottery in context["article"].lotteries.all():
            lottery_value = {}
            lottery_value["id"] = lottery.id
            if hasattr(lottery,"match"):
                match = lottery.match
                lottery_value["name"] = timezone.localtime(match.start_time).strftime("%m-%d %H:%M")+":"+match.home_team+"VS"\
                                        +match.away_team
                                        #+"["+match.lottery_entry.type.name+"]"
            elif hasattr(lottery,"lotto"):
                lotto = lottery.lotto
                lottery_value["name"] = lottery.type.name +":"+lotto.season
            lottery_list.append(lottery_value)
        return {"lotteries":lottery_list,"lotterytype":Lotterytype.objects.get(name=u"竞技彩")}
    else:
        return {"lotterytype":Lotterytype.objects.get(name=u"竞技彩")}
@register.inclusion_tag('lottery/analystlottery_select.html', takes_context=True)
def prizematch_select(context):
    if "prize" in context:
        lottery_list=[]
        match = context["prize"].match
        match_value = {}
        match_value["id"] = match.lottery_entry.id


        match_value["name"] = timezone.localtime(match.start_time).strftime(
            "%m-%d %H:%M") + ":" + match.home_team + " VS " \
                                + match.away_team
                                #+ "[" + match.lottery_entry.type.name + "]"

        lottery_list.append(match_value)

        return {"lotteries":lottery_list,"lotterytype":Lotterytype.objects.get(name=u"竞技彩")}
    else:
        return {"lotterytype":Lotterytype.objects.get(name=u"竞技彩")}

@register.filter(name='lottery_name')
def lottery_name(lottery):
    '''
        因为传入的arg一般是字符串,所以必须加这个int转换的方式
    '''
    if hasattr(lottery, "match"):
        match = lottery.match
        return timezone.localtime(match.start_time).strftime(
            "%m-%d %H:%M") + ":" + match.home_team + "VS" \
                                + match.away_team
                                #+ "[" + match.lottery_entry.type.name + "]"
    elif hasattr(lottery, "lotto"):
        lotto = lottery.lotto
        return lottery.type.name + ":" + lotto.season

@register.filter(name='team_logo')
def team_logo(teamname):
    team = Team.objects.get(name=teamname,sport_type=Team.SPORT_TYPE_FOOTBALL)
    return team.logo
