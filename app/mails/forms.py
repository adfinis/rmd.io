from django import forms
from mails.models import Account


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['anti_spam', 'key']
