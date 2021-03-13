from . import views
from django.conf.urls.static import static
from django.urls import path
from myproject import settings

urlpatterns = [
        path('', views.homepage, name="homepage"),
        path('signup/page/', views.signuppage.as_view(), name="signup"),
        path('login/page/', views.loginpage, name="loginpage"),

]