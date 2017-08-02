# coding:utf-8
import json

from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_redis import get_redis_connection


class AnswerLevel(models.Model):
    level_number = models.SmallIntegerField(unique=True)
    name = models.CharField(max_length=16)
    cost = models.SmallIntegerField(unique=True)

class Question(models.Model):
    MAX_ANSWER_TIME = 5
    STATUS_SAVED = -1  # 问题已保存但未支付
    STATUS_SUBMITED  = 0 #问题已支付完成提交状态
    STATUS_CLOSED    = 1 #异常关闭
    STATUS_COMPLETED = 2 #正常结束的

    content = models.TextField(max_length=500)
    from_user = models.ForeignKey(User)
    from_auser = models.ForeignKey("mobileapp.AppUser",null=True)
    to_analyst = models.ForeignKey("analyst.Analyst")
    expire_date = models.DateTimeField()#过期以后金币返回
    pub_date = models.DateTimeField(null=True)#赋值一次再也不能改
    status = models.SmallIntegerField(default=STATUS_SUBMITED)
    unread = models.BooleanField(default=True)

    grade = models.SmallIntegerField(null=True)#评级
    review = models.CharField(null=True,max_length=200)#评论文字

    date_added = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)


class Reply(models.Model):
    question = models.ForeignKey(Question)
    content = models.TextField(max_length=1018)
    poster = models.ForeignKey(User)
    unread = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)

def question_completed(question):
    con = get_redis_connection("default")
    con.publish("question_complete",str(question.id))

def reply_post(question):
    con = get_redis_connection("default")
    con.publish("reply_post",str(question.id)+"_"+str(question.from_auser_id)+"_"+str(question.to_analyst_id))

@receiver(post_save,sender=AnswerLevel)
def articlelottery_post_del(sender, **kwargs):
    answerlevel = kwargs["instance"]
    analysts = answerlevel.analyst_set.all()
    id_list=[]
    if analysts:
        for analyst in analysts:
            id_list.append(analyst.id)

    con = get_redis_connection("default")
    con.publish("authors_info_changed", json.dumps(id_list))
