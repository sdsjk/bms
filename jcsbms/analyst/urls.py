
from django.conf.urls import  url

from .views import index, post_analyst,analysts_search,deactivate_analyst,upload_avatar,my_articles, today_count, \
    make_toppage, cancel_toppage, agroup_list, post_agroup, lpriceplan_list, post_lpriceplan, group_prices, \
    group_delprice, group_addprice, ban_action, can_action
from .views import post_article,analyst_info,author_sousuo,activate_analyst,make_invisible,apply_search
from .views import priceplan_search,post_priceplan,apply_info,my_invited,analysts_winning_probability
urlpatterns = [

    url(r'^$', index),
    url(r'^probability/', analysts_winning_probability),
    url(r'^bianji/', post_analyst),
    url(r'^sousuo/', analysts_search),
    url(r'^wuxiao/', deactivate_analyst),
    url(r'^touxiang/', upload_avatar),
    url(r'^wodewenzhang/',my_articles),
    url(r'^fabu/',post_article),
    url(r'^xinxi/',analyst_info),
    url(r'^author_sousuo/',author_sousuo),
    url(r'^jihuo/',activate_analyst),
    url(r'^bukejian/', make_invisible),
    url(r'^shengqinbiao/',apply_search),
    url(r'^shenqing/',apply_info),
    url(r'^jiagebiao/',priceplan_search),
    url(r'^fabujiage/',post_priceplan),
    url(r'^yaoqing/',my_invited),
    url(r'^jinrifawen/',today_count),
    url(r'shangshouye/', make_toppage),
    url('^zubiao/$', agroup_list),
    url('^zu/$', post_agroup),
    url('^group_prices/$', group_prices),
    url('^zhibojiagebiao/$',lpriceplan_list),
    url('^fabuzhibojiage/$',post_lpriceplan),
    url('^group_delprice/$', group_delprice),
    url('^group_addprice/$', group_addprice),
    url('^jingzhicaozuo/$', ban_action),
    url('^yunxucaozuo/$', can_action),
    #url(r'xiashouye/', cancel_toppage),



]