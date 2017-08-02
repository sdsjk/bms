
from django.conf.urls import  url

from .views import index,result_view,author_search,del_result,sync_article,article_search,article_view, make_toppage, \
    cancel_toppage, atoday_count, has_banned, article_archive, redblack_options, article_istoppage_list, \
    article_istoppage_examine_detail, article_istoppage_examine_pass, article_istoppage_examine_nopass, \
    article_mobile_yqy, article_translate, article_view_translate, del_article_shouye, alldel_article

from .views import del_article,recover_article,article_mobile,redirect_orign,make_top,cancel_top,modify_article_top_order, \
    set_channel, black_red_list, set_black_red, del_black_red, black_red_search

urlpatterns = [

    url(r'^$', index),
    url('^pian/(\w{24})/$',result_view),
    url(r'authorsearch/', author_search),
    url(r'del_result/', del_result),
    url(r'tongbu/', sync_article),
    url(r'sousuo/',article_search),
    url(r'^translate/', article_translate),
    url(r'black_red_search/',black_red_search),
    url(r'redblack_options/',redblack_options),
    url(r'bianji/',article_view),
    url(r'viewtranslate/',article_view_translate),
    url(r'shanchu/',del_article),
    url(r'shanchuall/',alldel_article),
    url(r'shanchushoye/',del_article_shouye),
    url(r'huifu/',recover_article),
    url(r'fenxiang/',article_mobile),
    url(r'fenxiang_yqy/',article_mobile_yqy),
    url(r'yuantie/',redirect_orign),
    #url(r'upload/',upload_test),
    url(r'zhiding/',make_top),
    url(r'cancel_top/',cancel_top),
    url(r'shangshouye/', make_toppage),
    url(r'xiashouye/', cancel_toppage),
    url(r'^jinrifawen/', atoday_count),
    url(r'^has_banned/', has_banned),
    url(r'^guidang/', article_archive),
    url(r'^top_order/', modify_article_top_order),
    url(r'^set_channel/', set_channel),
    url(r'^black_red_list/', black_red_list),
    url(r'^set_black_red/', set_black_red),
    url(r'^del_black_red/', del_black_red),
    url(r'^shouyeshenhe/',article_istoppage_list),
    url(r'^article_istoppage_examine_detail/',article_istoppage_examine_detail),
    url(r'^article_istoppage_examine_pass/',article_istoppage_examine_pass),
    url(r'^article_istoppage_examine_nopass/',article_istoppage_examine_nopass),
]