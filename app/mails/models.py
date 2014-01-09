from mails.tools import get_all_addresses
from django.db import models
from django.contrib.auth.models import User
from django_browserid.signals import user_created
from django.dispatch import receiver
import base64
import os
from hashlib import md5


class Mail(models.Model):
    subject = models.CharField(max_length=200)
    sent = models.DateTimeField('Date sent')
    due = models.DateTimeField('Date due')
    sent_from = models.EmailField(max_length=75)
    sent_to = models.EmailField(max_length=75)

    @classmethod
    def my_mails(cls, request):
        addresses = get_all_addresses(request, 'only_actives')

        return cls.objects.filter(sent_from__in=addresses)


class UserKey(models.Model):
    key = models.CharField(max_length=10)
    user = models.OneToOneField(User, related_name="userkey")

    @classmethod
    def get_userkey(cls, user):
        try:
            key = user.userkey
        except:
            key = UserKey(
                key = base64.b32encode(os.urandom(7))[:10].lower(),
                user = user
            )
            key.save()
        return key.key


class Setting(models.Model):
    anti_spam = models.BooleanField(default=False)
    user = models.OneToOneField(User, related_name="settings", unique=True)


class Identity(models.Model):
    user = models.ForeignKey(User)
    identity = models.CharField(max_length=32)


class AddressLog(models.Model):
    address = models.EmailField(max_length=200)


class LastImport(models.Model):
    date = models.DateTimeField('Date of last import')


@receiver(user_created)
def generate_user(user, **kwargs):
    user_identity = Identity(
        identity=md5(os.urandom(10)).hexdigest(),
        user=user
    )
    user_key = UserKey(
        key=base64.b32encode(os.urandom(7))[:10].lower(),
        user=user
    )
    user_setting = Setting(user=user)
    user_log_entry = AddressLog.objects.filter(address=user.email)
    if user_log_entry.exists():
        user_log_entry.delete()
    user_identity.save()
    user_key.save()
    user_setting.save()
