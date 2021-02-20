from django.forms import ModelForm
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

class signupform(forms.ModelForm):
    username = forms.CharField(label="Username", max_length=100)
    email = forms.CharField(label="Email", max_length=100)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email',)

    def clean_password2(self):
        pass1 = self.cleaned_data.get("password1")
        pass2 = self.cleaned_data.get("password2")
        if pass1 and pass2 and pass1 != pass2:
            raise forms.ValidationError("Password does not match or not enterted properly")
        return pass2

    def save(self, commit=True):
        userobj = super(signupform, self).save(commit=False)
        userobj.set_password(self.cleaned_data["password2"])

        if commit:
            userobj.save()
        return userobj

class LoginForm(forms.Form):
    username = forms.CharField(label="Username")
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    def clean(self, *args, **kwargs):
        user1 = self.cleaned_data.get("username")
        pass1 = self.cleaned_data.get("password")

        user_obj = authenticate(username=user1, password=pass1)

        if not user_obj:
            raise forms.ValidationError("Wrong username / password ")

        return super(LoginForm, self).clean(*args, **kwargs)
