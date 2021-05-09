from django.contrib import admin
from chat.models import Message, Thread
from django.contrib.admin.sites import AlreadyRegistered, site
from django.apps import apps


class MessageInline(admin.StackedInline):
    model = Message
    fields = ('sender', 'text')
    readonly_fields = ('sender', 'text')


class ThreadAdmin(admin.ModelAdmin):
    model = Thread
    inlines = (MessageInline,)

admin.site.register(Thread, ThreadAdmin)

for model in apps.get_app_config('chat').get_models():
    try:
        admin.site.register(model)
    except AlreadyRegistered as e:
        pass
