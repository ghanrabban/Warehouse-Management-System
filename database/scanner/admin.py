from django.contrib import admin
from .models import DailyRoster, BarcodeEvent

@admin.register(DailyRoster)
class DailyRosterAdmin(admin.ModelAdmin):
    list_display = ('date','shift','user_list')
    filter_horizontal = ('users',)

    def user_list(self, obj):
        return ", ".join(u.username for u in obj.users.all())
    user_list.short_description = 'Personnel'

@admin.register(BarcodeEvent)
class BarcodeEventAdmin(admin.ModelAdmin):
    list_display = ('code','source','user','shift','created_at')
    list_filter  = ('source','shift','created_at')
    search_fields = ('code','user__username')