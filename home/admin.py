from django.contrib import admin
from .models import *


admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(FriendRequests)


class MessageContentInline(admin.TabularInline):
    model = MessageContent
    extra = 1


class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'message_count')
    inlines = [MessageContentInline]

    def message_count(self, obj):
        return obj.messagecontent_set.count()


admin.site.register(Message, MessageAdmin)
admin.site.register(MessageContent)
