from django.shortcuts import render
from authentication.forms import SignUpForm,LoginForm
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView
from django.http import HttpResponseRedirect
from authentication.models import User
from django.contrib.auth import login, logout
# Create your views here.

def StartPage(request):
    return render(request,"start.html")

def Index(request):
    return render(request, "index.html")

class SignUpView(SuccessMessageMixin,CreateView):
    form_class=SignUpForm
    template_name='signup.html'
    success_message = " Account created "
    success_url = reverse_lazy('registerpage')


    def dispatch(self, *args, **kwargs):
        return super(SignUpView,self).dispatch(*args, **kwargs)

def loginpage(request):
    formobj = LoginForm(request.POST or None)
    if formobj.is_valid():
        username = formobj.cleaned_data.get("username")
        userobj = User.objects.get(username__iexact=username)
        login(request, userobj)
        return HttpResponseRedirect(reverse("homepage"))
    else:
        return render(request, "login.html", {"form": formobj})
