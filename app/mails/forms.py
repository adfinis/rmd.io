from django import forms
from mails.models import Settings

class SettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        fields = ['anti_spam']
