from django.urls import path
from authentication.views import SignUpView,index,loginpage

urlpatterns=[
    path("",index,name="homepage"),
    path("signup/",SignUpView.as_view(),name="registerpage"),
    path("login/",loginpage,name="loginpage"),
]