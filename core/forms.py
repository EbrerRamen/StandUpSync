from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Team, Standup

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'description']

class StandupForm(forms.ModelForm):
    class Meta:
        model = Standup
        fields = ['team', 'yesterday', 'today', 'blockers']
        widgets = {
            'yesterday': forms.Textarea(attrs={'rows': 5}),
            'today': forms.Textarea(attrs={'rows': 5}),
            'blockers': forms.Textarea(attrs={'rows': 3}),
        } 