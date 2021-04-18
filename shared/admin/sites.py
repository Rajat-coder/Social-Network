from django.urls import path
from django.contrib import admin

class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        return urls

site = CustomAdminSite()

from django.contrib.auth.models import Group
site.register(Group)

