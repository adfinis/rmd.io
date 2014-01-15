from django import forms
from mails.models import Identity


class SettingsForm(forms.ModelForm):
    class Meta:
        model = Identity
        fields = ['anti_spam']
