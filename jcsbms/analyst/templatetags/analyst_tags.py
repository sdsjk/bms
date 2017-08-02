# coding:utf-8
'''
Created on 2015-11-18

@author: stone
'''
from django import template

from ask.models import Question
from jcs.models import Letter
from ..models import Analystlevel, LivePriceplan, AnalystGroup

register = template.Library()


@register.inclusion_tag('analyst/analyst_level.html', takes_context=True)
def analyst_level(context):

    return {"analyst_levels":Analystlevel.objects.all()}

@register.filter(name='analyst_typename')
def analyst_typename(value):
    names=[u"收费",u"免费",u"代发"]
    return names[int(value)]

@register.inclusion_tag('analyst/analyst_side.html', takes_context=True)
def analyst_side(context):
    if context['user'] and context['user'].is_authenticated():
        user = context['user']
        letters =[]

        letters = Letter.objects.filter(unread=True,to_user= context['user'],invisible=False).exclude(from_auser__in=user.analyst.banned_lettors.all())
        question_count = Question.objects.filter(unread=True,to_analyst=context['user'].analyst,status=Question.STATUS_SUBMITED).count()
        return {"user": user, "letters": letters,"question_count":question_count}
    else:
        return {}
@register.inclusion_tag('analyst/lprice_select.html', takes_context=True)
def lprice_select(context):
    return  {"liveprices":LivePriceplan.objects.all().order_by("id")}

@register.inclusion_tag('analyst/group_select.html', takes_context=True)
def analyst_group(context):
    return {"analyst_groups":AnalystGroup.objects.all().order_by("id")}