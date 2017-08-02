# coding:utf-8
'''
Created on 2015-11-18

@author: stone
'''
from django import template

from jcs.models import Letter
from jcsbms.settings import LOGIN_OUT_URL

register = template.Library()


@register.inclusion_tag('jauth/user_info.html', takes_context=True)
def user_info(context):
    login_out_url = LOGIN_OUT_URL
    if context['user'] and context['user'].is_authenticated() :
        user  = context['user']
        letters=[]
        if hasattr(user, "analyst"):
            letters  = Letter.objects.filter(unread=True,to_user= context['user'],invisible=False).exclude(from_auser__in=user.analyst.banned_lettors.all())
        return {"user":user,"letters":letters,"login_out_url":login_out_url}
    else:
        return {"user":None}

@register.inclusion_tag('jauth/user_side.html', takes_context=True)
def user_side(context):
    return {}