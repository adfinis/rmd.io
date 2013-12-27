from django import forms
from mails.models import Settings, AdditionalAddresses


class SettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        fields = ['anti_spam']


class AddressesForm(forms.ModelForm):
    class Meta:
        model = AdditionalAddresses
        fields = ['address']
