# coding:utf-8
from django.contrib import admin
from django.utils.html import strip_tags, format_html

# Register your models here.
from article.models import Channel, ArticleChannel
class ArticleChannelAdmin(admin.ModelAdmin):
    search_fields = ('channel__name', 'article_id')
    list_filter = ('channel', )
    list_display = ('id', 'channel', 'article_sid', 'article_analyst_nickname', 'article_digest',  'article_date_added',)
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

admin.site.register(Channel)
admin.site.register(ArticleChannel,ArticleChannelAdmin)

