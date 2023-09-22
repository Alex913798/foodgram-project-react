from django.contrib import admin

from .models import Follow


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'following')
    search_fields = ('user', 'following')
    list_filter = ('user', 'following')
    empty_value_display = '-пусто-'
