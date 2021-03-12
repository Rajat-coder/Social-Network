from django.conf.urls import url
from django.urls import path, include
from rest_framework import views

from chat.api import Chatview
from chat.views import ThreadView


urlpatterns = [
    path('<str:username>/', ThreadView.as_view()),
    path('api/chatlist/', Chatview.as_view()),
]