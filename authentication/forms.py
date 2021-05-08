from django import forms
from django.forms import ModelForm
from authentication.models import User

class SignUpForm(forms.ModelForm):
    first_name = forms.CharField(label="First Name", max_length=100)
    last_name = forms.CharField(label="Last Name", max_length=100)
    username=forms.CharField(label="Username",max_length=100)
    mobile = forms.CharField(max_length=13)
    email = forms.CharField(label="Email", max_length=100)
    password1=forms.CharField(label="Password",widget=forms.PasswordInput)
    password2=forms.CharField(label="Confirm password",widget=forms.PasswordInput)

    class Meta:
        model=User
        fields=('username','email','first_name','last_name','mobile')

    def clean_password2(self):
        pass1 = self.cleaned_data.get("password1")
        pass2 = self.cleaned_data.get("password2")
        if pass1 and pass2 and pass1 != pass2:
            raise forms.ValidationError("Password does not match or not enterted properly")
        return pass2

    def save(self, commit=True):
        userobj = super(SignUpForm, self).save(commit=False)
        userobj.set_password(self.cleaned_data["password2"])

        if commit:
            userobj.save()
        return userobj


