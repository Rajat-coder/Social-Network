from django.urls import path
from SocialBackend import settings
from django.conf.urls.static import static
from authentication.views import SignUpView,Index,loginpage,StartPage

urlpatterns=[
    path("",StartPage,name="start"),
    path("homepage",Index,name="homepage"),
    path("signup/",SignUpView.as_view(),name="registerpage"),
    path("login/",loginpage,name="loginpage"),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)