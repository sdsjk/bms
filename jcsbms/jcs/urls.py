"""jcsbms URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from .views import post_bulletin,bulletin_list,bulletin_info,letters_view,letters_search,post_letter,letters_review,del_letter, \
restore_letter, ban_auser, send_letter, del_ban_auser, reply_letter_instead_analyst

urlpatterns = [
    url('^fabugonggao/$',post_bulletin),
    url('^gonggaoguanli/$',bulletin_list),
    url('^gonggao/$',bulletin_info),
    url('^wodexiaoxi/$', letters_view),
    url('^chaxiaoxi/$', letters_search),
    url('^faxiaoxi/$', post_letter),
    url('^sixinshencha/$', letters_review),
    url('^del_letter/$', del_letter),
    url('^restore_letter/$', restore_letter),
    url('^pingbi/$', ban_auser),
    url('^jiechupingbi/$', del_ban_auser),
    url('^send_letter/', send_letter),
    url('^daifaxiaoxi/', reply_letter_instead_analyst),
]
