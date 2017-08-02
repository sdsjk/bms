
from django.conf.urls import  url

from .views import index,lottery_search, teamname_list, put_teamname, post_standardname, prize_list, post_prize, euro, \
    euro_match, team_list, post_team, fixture_list, post_fixture,america,modifyMatchTime, cup_league, post_cup_league, edit_match, del_match, \
    rx9_list, edit_rx9, del_rx9

urlpatterns = [

    url(r'^$', index),
    url(r'^sousuo/', lottery_search),
    url(r'^duimingbiao/', teamname_list),
    url(r'^duimingbianji/', put_teamname),
    url(r'^post_standardname/', post_standardname),
    url(r'^jincaibiao/', prize_list),
    url(r'^jincaibianji/', post_prize),
    url(r'^ouguan/', euro),
    url(r'^saishi/', euro_match),
    url(r'^saiduibiao/', team_list),
    url(r'^saiduibianji/', post_team),
    url(r'^saichenbiao/', fixture_list),
    url(r'^saichenbianji/', post_fixture),
    url(r'^meizhoubei/', america),
    url(r'^modify_match_time/', modifyMatchTime),
    url(r'^cup_league/', cup_league),
    url(r'^edit_cup_league/', post_cup_league),
    url(r'^edit_match/', edit_match),
    url(r'^del_match/', del_match),
    url(r'^rx9/', rx9_list),
    url(r'^edit_rx9/', edit_rx9),
    url(r'^del_rx9/', del_rx9),
]