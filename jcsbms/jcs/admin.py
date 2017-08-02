from django.contrib import admin
from .models import Letter, Bulletin, SystemConfig
from django.contrib.contenttypes.models import ContentType

# Register your models here.
class ContentTypeAdmin(admin.ModelAdmin):
    search_fields = ('app_label', 'model')
    list_display = search_fields


class SystemConfigAdmin(admin.ModelAdmin):
    search_fields = ('config_type', 'config_key', 'config_value')
    list_display = ('id','config_type', 'config_key', 'config_value')

admin.site.register(Letter)
admin.site.register(Bulletin)
admin.site.register(ContentType, ContentTypeAdmin)
admin.site.register(SystemConfig, SystemConfigAdmin)