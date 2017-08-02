
from django.conf.urls import  url

from .views import login,upload_avatar,avatar_upload,index,set_password,upload_myavatar,login_out, user_info


urlpatterns = [

    url(r'^$', index),
    url('^denglu/$',login),
    url('^touxiang/$',upload_avatar),
    url('^avatar_upload/$',avatar_upload),
    url('^mima/$',set_password),
    #url('^wodetouxiang/$',upload_myavatar),
    url('^tuichu/$',login_out),
    url('info/$', user_info)


]