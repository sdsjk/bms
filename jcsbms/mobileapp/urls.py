
from django.conf.urls import  url

from .views import user_search,followers,follow_analysts,deactivate_user,activate_user,purchase_search,charge_search, \
    banner_list, post_banner, down_banner, online_banner, portal_list, post_portal, online_portal, down_portal, \
    give_gold, channel_users, monthpurchase_search, comment_list, new_comments, verify_comment, deny_comment, \
    wx_checkorder, bms_log_search, present_search, analyst_present_search, deduct_gold, redis_operation, del_article_redis, \
    del_redis_hash, del_redis_zset, update_redis_hash, del_user_redis, push_article_redis, batch_set_toppage_count, pullnew, \
    article_log, traslate_balance

from .views import recharge_list,post_recharge,analyst_purchases,analyst_revenue,charge_rank,money_changes,batch_refund,cheat_monitor, refund_red, refund_red_log, user_last_active_time
urlpatterns = [
    url(r'^users/', user_search),
    url(r'^followers/', followers),
    url(r'^follow_analysts/', follow_analysts),
    url(r'^wuxiao/', deactivate_user),
    url(r'^youxiao/', activate_user),
    url(r'^zhifu/', purchase_search),
    url(r'^zengsong/', present_search),
    url(r'^chongzhi/', charge_search),
    url(r'^wx_checkorder', wx_checkorder),
    url(r'^chongzhiplan/', recharge_list),
    url(r'^fabuchongzhi/', post_recharge),
    url(r'^laoshizhangmu/', analyst_purchases),
    url(r'^laoshizengsong/', analyst_present_search),
    url(r'^laoshishouru/', analyst_revenue),
    url(r'^article_log/', article_log),
    url(r'^chongzhipaihang/',charge_rank),
    url(r'^xianjingliushui/', money_changes),
    url(r'^guanggaobiao/', banner_list),
    url(r'^bianjiguanggao/', post_banner),
    url(r'^online_banner/', online_banner),
    url(r'^down_banner/', down_banner),
    url(r'^rukouguanli/', portal_list),
    url(r'^bianjirukou/', post_portal),
    url(r'^online_portal/', online_portal),
    url(r'^down_portal/', down_portal),
    url(r'^songjinbi/', give_gold),
    url(r'^deduct/', deduct_gold),
    url(r'^qudaoyonghu/',channel_users),
    url(r'^baoyuegoumai/',monthpurchase_search),
    url(r'^daishenliebiao/',comment_list),
    url(r'^xinpinglun/',new_comments),
    url(r'^verify/',verify_comment),
    url(r'^deny/',deny_comment),
    url(r'^piliangtuifei/', batch_refund),
    url(r'^pullnew/', pullnew),
    url(r'^cheat_monitor/', cheat_monitor),
    url(r'^refund_red/', refund_red),
    url(r'^refund_red_log/', refund_red_log),
    url(r'^user_last_active/', user_last_active_time),
    url(r'^rizhi/', bms_log_search),
    url(r'^huancuncaozuo/', redis_operation),
    url(r'^del_article_redis/',  del_article_redis),
    url(r'^push_article_redis/',  push_article_redis),
    url(r'^del_user_redis/',  del_user_redis),
    url(r'^shanchuhash/',  del_redis_hash),
    url(r'^shanchuzset/',  del_redis_zset),
    url(r'^xiugaihash/',  update_redis_hash),
    url(r'^batch_set_toppage_count/',  batch_set_toppage_count),
url(r'^traslate_balance/',traslate_balance)
]