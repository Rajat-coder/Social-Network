from . import views
from django.conf.urls.static import static
from django.urls import path
from myproject import settings

urlpatterns = [
        path('signuppage', views.signuppage.as_view(), name="registerpage"),

]