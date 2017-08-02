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
from .views import my_quesions,quesion_info, quesion_replies,post_reply,set_pubdate
urlpatterns = [
    url('^wode/$',my_quesions),
    url('^wenti/$',quesion_info),
    url('^chahuifu/$', quesion_replies),
    url('^huifu/$', post_reply),
    #url('^set_pubdate/$', set_pubdate),

]
