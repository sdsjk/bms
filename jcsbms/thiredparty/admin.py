# coding:utf-8
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.utils.html import strip_tags, format_html



# Register your models here.
from thiredparty.models import CrazySportAnalyst, CrazySportArticle, CrazySportMatch, CrazySportImportResult


class CrazySportAnalystAdmin(admin.ModelAdmin):
    # search_fields = ('expert_nick_name')
    list_display = ('expert_nick_name', 'expert_name')


class CrazySportArticleAdmin(admin.ModelAdmin):
    # search_fields = ("expert_nick_name")
    list_filter = ('expert_nick_name', )
    list_display = ('article_id', 'summary', 'expect_nick_name')

    def expect_nick_name(self, obj):
        return obj.expect.expert_nick_name

class CrazySportMatchAdmin(admin.ModelAdmin):
    search_fields = ("article_id", 'league_name', 'home_name', 'guest_name')
    list_filter = ('league_name', )
    list_display = ('article_id', 'league_name', 'home_name', 'guest_name',  'match_num')


class CrazySportImportResultAdmin(admin.ModelAdmin):

    list_display = ('crazy_article_id', 'jcs_article_id')



admin.site.register(CrazySportAnalyst, CrazySportAnalystAdmin)
admin.site.register(CrazySportArticle, CrazySportArticleAdmin)
admin.site.register(CrazySportMatch, CrazySportMatchAdmin)
admin.site.register(CrazySportImportResult, CrazySportImportResultAdmin)