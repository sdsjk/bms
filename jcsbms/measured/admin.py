# coding:utf-8
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.utils.html import strip_tags, format_html

from models import MeasuredActivity, MeasuredActivityAnalyst, MeasuredCard, MeasuredCardRules, MeasuredCardActivity, \
    MeasuredCardSale, MeasuredActivityArticle


# Register your models here.

class MeasuredActivityAdmin(admin.ModelAdmin):
    search_fields = ("activity_name",)
    list_display = ('activity_name',)


class MeasuredActivityAnalystAdmin(admin.ModelAdmin):
    list_filter = ('activity',)
    list_display = ('activity', 'analyst',)
    raw_id_fields = ('analyst',)

class MeasuredCardAdmin(admin.ModelAdmin):
    list_display = ('name',)


class MeasuredCardRulesAdmin(admin.ModelAdmin):
    search_fields = ("card__name", 'rule_value',)
    list_display = ('card', 'rule_key', 'rule_value',)
    list_filter = ('card', 'rule_key',)


class MeasuredCardActivityAdmin(admin.ModelAdmin):
    search_fields = ("card__name", 'activity__activity_name',)
    list_filter = ('activity',)
    list_display = ('activity', 'card',)


class MeasuredCardSaleAdmin(admin.ModelAdmin):
    search_fields = ("card__name", 'user__nickname', 'user__phonenumber',)
    list_filter = ('card', 'cdate',)
    list_display = ('card', 'user', 'user_nickname', 'user_phonenumber', 'start_time', 'end_time', 'usable', 'cdate', 'send_message',)
    raw_id_fields = ('user',)
    def user_nickname(self, obj):
        return obj.user.nickname
    def user_phonenumber(self, obj):
        return obj.user.phonenumber
    def send_message(self, obj):
        return format_html(
            u'<a href="http://www.jingcaishuo.com/send/message?productName={}&phoneNumber={}" target=_blank>发送</a>',
            obj.card.name,
            obj.user.phonenumber,
        )
    user_nickname.short_description = u'用户名称'
    # article_analyst_id.admin_order_field = 'article__author__id'
    user_phonenumber.short_description = u'用户电话号码'
    # article_analyst_id.admin_order_field = 'article__author__id'
    send_message.short_description = u'发送开通短信'


class MeasuredActivityArticleAdmin(admin.ModelAdmin):
    search_fields = ("article_analyst_nickname", 'activity__activity_name', )
    list_filter = ('activity', )
    list_display = ('activity', 'article_sid', 'article_analyst_nickname', 'article_digest',  'article_date_added',)
    raw_id_fields = ('article',)
    def article_analyst_id(self, obj):
        return obj.article.author.id
    def article_sid(self, obj):
        return obj.article.id
    def article_analyst_nickname(self, obj):
        return obj.article.author.nick_name
    def article_date_added(self, obj):
        return obj.article.date_added
    def article_digest(self, obj):
        if obj.article.chargeable:
            return obj.article.digest[:40]
        else:
            return ' '.join(strip_tags(obj.article.text)[:40].split())
    article_analyst_id.short_description = u'老师ID'
    article_analyst_id.admin_order_field = 'article__author__id'
    article_sid.short_description = u'文章ID'
    article_sid.admin_order_field = 'article__id'
    article_analyst_nickname.short_description  = u'老师名称'
    article_analyst_nickname.admin_order_field = 'article__author__nick_name'
    article_date_added.short_description = u'添加日期'
    article_date_added.admin_order_field = 'article__date_added'
    article_digest.short_description = u'摘要'



admin.site.register(MeasuredActivity, MeasuredActivityAdmin)
admin.site.register(MeasuredActivityAnalyst, MeasuredActivityAnalystAdmin)
admin.site.register(MeasuredCard, MeasuredCardAdmin)
admin.site.register(MeasuredCardRules, MeasuredCardRulesAdmin)
admin.site.register(MeasuredCardActivity, MeasuredCardActivityAdmin)
admin.site.register(MeasuredCardSale, MeasuredCardSaleAdmin)
admin.site.register(MeasuredActivityArticle, MeasuredActivityArticleAdmin)
