from django.contrib import admin
from django.contrib.auth.models import Permission
from models import Userinfo
# Register your models here.

class UserinfoAdmin(admin.ModelAdmin):
    search_fields = ("user__username",)
    raw_id_fields = ("user",)

class PermissionAdmin(admin.ModelAdmin):
    search_fields = ("codename", "name")

admin.site.register(Userinfo, UserinfoAdmin)
admin.site.register(Permission, PermissionAdmin)
