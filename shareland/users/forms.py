from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
import re
from .models import Profile


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    name = forms.CharField(max_length=100, required=True, label='Name')
    surname = forms.CharField(max_length=100, required=True, label='Surname')
    affiliation = forms.CharField(max_length=200, required=False, label='Affiliation')
    orcid = forms.CharField(
        max_length=19, 
        required=False, 
        label='ORCID',
        help_text='ORCID ID (e.g., 0000-0000-0000-0000). Optional.',
        widget=forms.TextInput(attrs={'placeholder': '0000-0000-0000-0000'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'name', 'surname', 'affiliation', 'orcid', 'password1', 'password2']
        
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if email:
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError('This email address is already registered. Please use a different email or try logging in.')
        return email
    
    def clean_orcid(self):
        orcid = self.cleaned_data.get('orcid', '').strip()
        if orcid:
            # Remove spaces and validate format
            orcid = orcid.replace(' ', '').replace('https://orcid.org/', '').replace('http://orcid.org/', '')
            # Validate ORCID format: 0000-0000-0000-0000 (last digit can be X)
            if not re.match(r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$', orcid):
                raise forms.ValidationError('ORCID must be in format 0000-0000-0000-0000')
        return orcid or None


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=False)
    first_name = forms.CharField(max_length=150, required=False, label='First Name')
    last_name = forms.CharField(max_length=150, required=False, label='Last Name')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'birth_date', 'qualification', 'affiliation', 'orcid', 'contact_email', 'user_roles']
        widgets = {
            'user_roles': forms.CheckboxSelectMultiple(),
        }
