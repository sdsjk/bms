# coding:utf-8
'''
Created on 2015-11-10

@author: stone
'''
from datetime import timedelta
from django import template
from django.utils import timezone

from ask.models import AnswerLevel, Question

register = template.Library()

@register.inclusion_tag('ask/answer_level.html', takes_context=True)
def answer_level(context):
    return {"answer_levels":AnswerLevel.objects.all().order_by("id")}

@register.filter(name='qunread')
def question_unread(question):
    if question.status == Question.STATUS_SUBMITED:
        if question.unread :
            return True
        elif question.reply_set.filter(poster=question.from_user,unread=True):
            return True
        else:
            return False
    else:
        return False

@register.inclusion_tag('ask/question_lefttime.html', takes_context=True)
def question_lefttime(context):
    question = context["question"]
    status = None
    left_count = Question.MAX_ANSWER_TIME
    lefttime = timedelta(seconds=0)
    if  question.status == Question.STATUS_SUBMITED:
        reply_count = question.reply_set.all().exclude(poster=question.from_user).count()
        if reply_count  == 0:
            status = 0
            lefttime = question.expire_date-timezone.now()
        else:
            status = 1
            lefttime = question.expire_date-timezone.now()
            left_count = Question.MAX_ANSWER_TIME-reply_count
    elif question.status == Question.STATUS_COMPLETED and question.pub_date!=None and question.pub_date>timezone.now():
        status = 2
        lefttime = question.pub_date - timezone.now()

    return {"status":status,"lefttime":lefttime,"left_count":left_count}