from django import forms
from mails.models import Setting, AdditionalAddress


class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        fields = ['anti_spam']


class AddressForm(forms.ModelForm):
    class Meta:
        model = AdditionalAddress
        fields = ['address']
