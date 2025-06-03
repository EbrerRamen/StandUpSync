from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Team, Standup

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = ('username', 'email')

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