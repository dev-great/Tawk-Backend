from django.contrib import admin
from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isPublish',
                    'scheduled_publish', 'created_on', 'updated_on')
    list_filter = ('isPublish', 'created_on')
    search_fields = ('title', 'author__username')
    readonly_fields = ('id', 'created_on', 'updated_on')

    fieldsets = (
        (None, {
            'fields': ('id', 'title', 'author', 'body', 'isPublish')
        }),
        ('Date Information', {
            'fields': ('scheduled_publish', 'created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )
