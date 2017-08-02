from django.contrib import admin

from .models import Analyst,Analystlevel,Priceplan, LivePriceplan, AnalystGroup,GroupLivePrices, AnalystChannel, \
    AnalystConfig


# Register your models here.
class AnalystlevelAdmin(admin.ModelAdmin):
    search_fields = ('name',)

class AnalystAdmin(admin.ModelAdmin):
    search_fields = ('nick_name',)

class AnalystChannelAdmin(admin.ModelAdmin):
    search_fields = ('channel_name',)

class AnalystConfigAdmin(admin.ModelAdmin):
    list_display = ('analyst_id', 'key', 'value',)

admin.site.register(Analystlevel, AnalystlevelAdmin)
admin.site.register(Analyst, AnalystAdmin)
admin.site.register(Priceplan)


admin.site.register(LivePriceplan)
admin.site.register(AnalystGroup)
admin.site.register(GroupLivePrices)
admin.site.register(AnalystChannel, AnalystChannelAdmin)
admin.site.register(AnalystConfig, AnalystConfigAdmin)
