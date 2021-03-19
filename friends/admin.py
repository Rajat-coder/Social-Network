from django.contrib import admin
from .models import FriendList, FriendRequest

# Register your models here.
admin.site.register(FriendRequest)
admin.site.register(FriendList)
