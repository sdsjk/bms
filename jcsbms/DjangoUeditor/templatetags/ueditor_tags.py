#coding:utf-8
'''
Created on 2013-7-4

@author: hulda
'''
from django import template

register = template.Library()

@register.inclusion_tag('ueditor.djhtml', takes_context=True)
def ueditor(context):
    
    #request = context['request']
    #userinfo = Userinfo.objects.get(user=request.user)
    return {}
