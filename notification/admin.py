from django.contrib import admin
from .models import *

# Register your models here.


class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'target', 'unread', ]
    list_per_number = 50
    list_filter = ['title', 'date', 'target', 'unread',]
    search_fields = ['title', 'date', 'target', 'unread',]


admin.site.register(NotificationPost, NotificationAdmin)
