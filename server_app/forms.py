from django import forms

class RegistrationForm(forms.Form):
    email = forms.EmailField()
    name = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class JobSubmitForm(forms.Form):
    func = forms.CharField(widget=forms.Textarea)
    args = forms.CharField(widget=forms.Textarea)
    ctx = forms.CharField(widget=forms.Textarea)



