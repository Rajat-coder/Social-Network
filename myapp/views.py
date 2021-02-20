from django.shortcuts import render
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView
from myapp.forms import *
from django.urls import reverse_lazy, reverse


# Create your views here.

class signuppage(SuccessMessageMixin,CreateView):
    form_class=signupform
    template_name='signup.html'
    success_message = "Your account has been created successfully"
    success_url = reverse_lazy('registerpage')


    def dispatch(self, *args, **kwargs):
        return super(signuppage,self).dispatch(*args, **kwargs)
