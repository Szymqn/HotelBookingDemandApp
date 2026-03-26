from django import forms
from django.contrib.auth import authenticate
from .models import CustomUser


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username or email',
            'aria-label': 'Username'
        }),
        label='Username or Email'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'aria-label': 'Password'
        }),
        label='Password'
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            if not CustomUser.objects.filter(username=username).exists():
                raise forms.ValidationError('Invalid username or email.')
            
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError('Invalid password.')
        
        return cleaned_data


class SignUpForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
            'aria-label': 'Password'
        }),
        label='Password'
    )
    
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'username')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name',
                'aria-label': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name',
                'aria-label': 'Last Name'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email or username',
                'aria-label': 'Username or Email'
            }),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'username': 'Email or Username'
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
