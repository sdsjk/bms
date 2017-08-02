# coding:utf-8
'''
Created on 2015-11-10

@author: stone
'''
from django import template
from jcs.dfa import DFASearch
from django.utils.html import strip_tags
from jcsbms.settings import XIAOMISHU_AUTH_USER_IDS

register = template.Library()

@register.inclusion_tag('jcs/staff_side.html', takes_context=True)
def staff_side(context):

    request = context['request']
    is_xiaomishu = False
    c=[]
    if 1 != request.user.id :
        names = request.user._group_perm_cache
        c=[i for i in names]
    else:
        c=['suppor']
    if request.user.id in XIAOMISHU_AUTH_USER_IDS:
        is_xiaomishu = True

    return { 'user': request.user,
             'is_xiaomishu': is_xiaomishu,"perms":c}

@register.filter(name='dictvbyk')
def dictvbyk(value, arg):
    '''
        字典的Key最好是字符串
    '''
    return value.get(arg, "") if isinstance(value, dict) else value

@register.filter(name='notzdate')
def notzdate(value, arg="%Y-%m-%d %H:%M"):

    return value.strftime(arg)

@register.filter(name='listvbyi')
def listvbyi(value,arg):
    '''
        因为传入的arg一般是字符串,所以必须加这个int转换的方式
    '''
    return value[int(arg)]

@register.inclusion_tag('jcs/pager.html', takes_context=True)
def pager(context):
    request =context["request"]
    pager = context["pager"]
    query_dict = request.GET.copy()

    if pager.has_next():
        query_dict["page_index"] = pager.next_page_number()
        pager.next_url = request.path+"?"+query_dict.urlencode()
    if pager.has_previous():
        query_dict["page_index"] = pager.previous_page_number()
        pager.previous_url = request.path+"?"+query_dict.urlencode()
    begin_page=1
    end_page=1
    if pager.has_other_pages():

        if pager.number > 5:
            begin_page = pager.number - 4
            if (pager.number+4) <= pager.paginator.num_pages:
                end_page = pager.number+4
            else:
                end_page = pager.paginator.num_pages
        else:
            begin_page = 1
            if pager.paginator.num_pages>=9:
                end_page = 9
            else:
                end_page = pager.paginator.num_pages
    page_numbers = range(begin_page,end_page+1)
    pager.page_urls=[]
    for page_number in page_numbers:
        query_dict["page_index"] = page_number
        page_url = request.path+"?"+query_dict.urlencode()
        pager.page_urls.append(
            {
                "index":page_number,
                "url":page_url
            }
        )
    if "page_index" in query_dict:
        query_dict.pop("page_index")
    pager.nopageindex_url = request.path+"?"+query_dict.urlencode()
    return {"pager":pager}

@register.inclusion_tag('jcs/tablesorter.html')
def tablesorter():
    return {}

@register.filter(name="check_banned_words")
def checkBannedWords(value):
    ret = DFASearch.has_banned(strip_tags(value))
    if ret != "":
        value = value.replace(ret, "<em style='color:red'>%s</em>" % ret)
    return value

@register.filter(name="mysplit")
def mysplit(value, sep = " "):
    return value.split(sep)
