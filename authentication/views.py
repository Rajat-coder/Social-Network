from django.shortcuts import render
from authentication.forms import SignUpForm
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView
from django.http import HttpResponseRedirect
# Create your views here.

class SignUpView(SuccessMessageMixin,CreateView):
    form_class=SignUpForm
    template_name='signup.html'
    success_message = "Your account has been created successfully"
    success_url = reverse_lazy('registerpage')


    def dispatch(self, *args, **kwargs):
        return super(SignUpView,self).dispatch(*args, **kwargs)
