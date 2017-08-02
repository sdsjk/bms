from django.contrib import admin
from models import BigVIP, LiveVedio, H5_article_fixtop, H5_author_list, AppUser, LetterHide, PushChannel, UsersConfig, \
    ExternalChannel, ExternalOrder


# Register your models here.

class BigVIPAdmin(admin.ModelAdmin):
    #list_display = ("name", "avatar")
    search_fields = ("name",)

class LiveVedioAdmin(admin.ModelAdmin):
    #list_display = ("match_name", "start_time", "end_time", "location")
    search_fields = ("match_name",)

class H5_article_fixtopAdmin(admin.ModelAdmin):
    search_fields = ("article_id",)

class H5_author_listAdmin(admin.ModelAdmin):
    list_display = ("author", "order_id", "type")
    search_fields = ("author__nick_name",)
    raw_id_fields = ("author",)

    # def order_id(self, obj):
    #     return obj.order_id
    # order_id.admin_order_field = "order_id"
class AppUserAdmin(admin.ModelAdmin):
    search_fields = ('userid', 'phonenumber', 'nickname',)
    list_display = ('userid', 'phonenumber', 'nickname',)
    fields = ('nickname',)

class LetterHideAdmin(admin.ModelAdmin):
    list_display = ('userid', 'authorid', 'cdate',)
    search_fields = ('userid','authorid',)

class PushChannelAdmin(admin.ModelAdmin):
    list_display = ('userid', 'type', 'token', 'cdate', 'appid')
    search_fields = ('userid',)

class UsersConfigAdmin(admin.ModelAdmin):
    list_display = ('users_id', 'start_hour', 'end_hour', 'start_minute', 'end_minute', 'notify_type', 'silence_type')
    search_fields = ('users_id',)

class ExternalChannelAdmin(admin.ModelAdmin):
    list_display = ('app_key','secret','code','mobile','email','name','expirey_date','status','create_time','last_update_time','create_by_id')
    search_fields = ('code','name',)

class ExternalOrderAdmin(admin.ModelAdmin):
    list_display = ('app_key','channel_id','channel_code','user_mobile','user_email','price','user_id','wx_id','wx_open_id','wx_uuid','create_time','last_update_time','status','article_id','order_sn')
    search_fields = ('article_id',)

admin.site.register(BigVIP, BigVIPAdmin)
admin.site.register(LiveVedio, LiveVedioAdmin)
admin.site.register(H5_article_fixtop, H5_article_fixtopAdmin)
admin.site.register(H5_author_list, H5_author_listAdmin)
admin.site.register(AppUser, AppUserAdmin)
admin.site.register(LetterHide, LetterHideAdmin)
admin.site.register(PushChannel, PushChannelAdmin)
admin.site.register(UsersConfig, UsersConfigAdmin)
admin.site.register(ExternalChannel, ExternalChannelAdmin)
admin.site.register(ExternalOrder, ExternalOrderAdmin)
