from django.urls import path
from usersearch.views import UserSearch, DayitvaListView

app_name="usersearch"

urlpatterns=[
    path('list/', UserSearch.as_view()),
    path('sanghdayitva/', DayitvaListView.as_view()),
]
