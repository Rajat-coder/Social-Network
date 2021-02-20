from django.shortcuts import render
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView
from myapp.forms import *
from django.urls import reverse_lazy, reverse
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponseRedirect


# Create your views here.

def homepage(request):
    return render(request,"homepage.html")

class signuppage(SuccessMessageMixin,CreateView):
    form_class=signupform
    template_name='signup.html'
    success_message = "Your account has been created successfully"
    success_url = reverse_lazy('signup')


    def dispatch(self, *args, **kwargs):
        return super(signuppage,self).dispatch(*args, **kwargs)

def loginpage(request):
    formobj = LoginForm(request.POST or None)
    if formobj.is_valid():
        username = formobj.cleaned_data.get("username")
        userobj = User.objects.get(username__iexact=username)
        login(request, userobj)
        request.session["userid"] = userobj.id
        request.session["myusername"] = userobj.username
        request.session["myuseremail"] = userobj.email
        # request.session["joineddate"] = userobj.date_joined
        return HttpResponseRedirect(reverse("homepage"))
    else:
        return render(request, "login.html", {"form": formobj})
