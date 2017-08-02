
from django.conf.urls import url

from restapi.views import match_list, article_list, portal_list, article_detail, match_detail, analyst_list, \
    match_update, play_list, playdetail_list

urlpatterns = [

    url(r'^article/$', article_list),
    url(r'^article/(?P<pk>[0-9]+)/$', article_detail),
    url(r'^match/$', match_list),
    url(r'^match_update/$',match_update),
    url(r'^match/(?P<pk>[0-9]+)/$', match_detail),
    url(r'^port al/$', portal_list),
    url(r'^analyst/$', analyst_list),
    url(r'^play/$', play_list),
    url(r'^playdetail/$', playdetail_list),

]