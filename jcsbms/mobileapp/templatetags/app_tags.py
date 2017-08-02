# coding:utf-8
'''
Created on 2015-11-30

@author: stone
'''
from django import template

from analyst.models import Analyst
from article.models import Article
from jcs.models import get_system_config
from mobileapp.models import Purchase, Charge, Portal, Period
from jcsbms.settings import SERVER_HOST
register = template.Library()
@register.filter(name='payinfo_name')
def payinfo_name(value):
    names=[u"普通",u"单次",u"包月"]
    return names[int(value)]

@register.filter(name='paytype_name')
def paytype_name(value):
    value = int(value)
    value = value if value !=3 else 5
    return Purchase.PAY_TYPE_NAMES [int(value)-1]

@register.filter(name='get_teacher')
def get_teacher(value):
    if value!=None:
        analyst=Analyst.objects.get(id=value)
        return analyst.nick_name
    else:
        return ""
@register.filter(name='charge_type')
def charge_type(value):

    return Charge.CHARGE_TYPE_NAMES[int(value)-1]

@register.filter(name='centesimal')
def centesimal(value):

    return float(value)/100

@register.inclusion_tag('mobileapp/exportlink.html', takes_context=True)
def export_link(context):
    request = context["request"]
    query_dict = request.GET.copy()
    #print query_dict
    query_dict["for_export"] ="on"
    export_url = request.path+"?"+query_dict.urlencode()
    return {"export_url":export_url}

@register.filter(name='purchasetarget_name')
def purchasetarget_name(purchase):
    if purchase.purchasetype == Purchase.PURCHASE_TYPE_ASK:
        return Purchase.PURCHASE_TYPE_NAMES[purchase.purchasetype]+":"+str(purchase.target)
    elif purchase.purchasetype == Purchase.PURCHASE_TYPE_ARTICLE:
        try:
            article = Article.objects.get(id=purchase.target)
            return '<a target="_blank" href="'+ SERVER_HOST + '/wenzhang/fenxiang/?key='+article.sign_key+'">'+Purchase.PURCHASE_TYPE_NAMES[purchase.purchasetype]+":"+str(purchase.target)+"</a>"
        except Article.DoesNotExist, e:
            return u"不存在"
    elif purchase.purchasetype == Purchase.PURCHASE_TYPE_MONTH:
        period = Period.objects.get(id=purchase.target)
        return (period.enddate-period.startdate).days

@register.inclusion_tag('mobileapp/portal_checks.html', takes_context=True)
def portal_checks(context):
    if context['user'] and context['user'].is_authenticated():
        user = context['user']
    portals = Portal.objects.filter(can_selected=True)
    yqy_push_analyst_ids = get_system_config('YQY_PUSH_ANALYST_IDS')
    can_push_analyst = True
    if hasattr(user, 'analyst'):
        can_push_analyst = str(user.analyst.id) in yqy_push_analyst_ids.split(',')  # 判断登录讲师是否是一起赢讲师
    return {"portals":portals,"can_push_analyst":can_push_analyst}
