# coding:utf-8
'''
Created on 2015-11-10

@author: stone
'''
from django.db import models
from django.contrib.auth.models import User


from jcsbms.utils import random_string,jsend_mail

# Create your models here.


class Userinfo(models.Model):

    user = models.OneToOneField(User)
    user_dir = models.CharField(null=True,unique=True,max_length=20)
    avatar = models.CharField(max_length=120,default="img/default_avatar.png")

    def __unicode__(self):
        return "%s" % self.user.username

def send_notify(username,password,email):
    message = u"欢迎成为精彩说的签约分析师!\r\n"
    message = message + u"精彩说的发布后台地址为：http://bms.jingcaishuo.net \r\n"
    message = message + u"您的用户名为"+ username + "\r\n"
    message = message + u"您的初始密码为"+ password + "\r\n"
    message = message + u"登陆后点击网页右上角菜单修改密码 \r\n 如有任何疑问，可以联系客服：help@jingcaishuo.com\r\n 精彩说，一切为了彩民！\r\n"

    # jsend_mail(u"精彩说新建用户通知邮件",message,email)

def create_user(username,email):
    password = random_string(8)
    user = User.objects.create_user(username=username, email=email, password=password)
    userinfo = Userinfo(user=user)
    from jcsbms.utils import get_userdir
    dir_name = get_userdir(user)
    while(Userinfo.objects.filter(user_dir=dir_name)):
        dir_name = get_userdir(user)
    userinfo.user_dir = dir_name
    userinfo.save()
    send_notify(username,password,email)
    return user

def create_psUser():
    username = random_string(8)
    password = random_string(8)
    user = User.objects.create_user(username=username, password=password)
    user.is_active=False
    user.save()
    userinfo = Userinfo(user=user)
    from jcsbms.utils import get_userdir
    dir_name = get_userdir(user)
    while(Userinfo.objects.filter(user_dir=dir_name)):
        dir_name = get_userdir(user)
    userinfo.user_dir = dir_name
    userinfo.save()
    return user

