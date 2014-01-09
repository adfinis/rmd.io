from django import forms
from mails.models import Setting


class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        fields = ['anti_spam']
