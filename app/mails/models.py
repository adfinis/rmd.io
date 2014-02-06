from mails.tools import get_all_addresses
from django.db import models
from django.contrib.auth.models import User
from django_browserid.signals import user_created
from django.dispatch import receiver
import base64
import os


class Mail(models.Model):
    subject = models.CharField(max_length=200)
    sent = models.DateTimeField('Date sent')
    due = models.DateTimeField('Date due')
    sent_from = models.EmailField(max_length=75)
    sent_to = models.EmailField(max_length=75)

    @classmethod
    def my_mails(cls, request):
        addresses = get_all_addresses(request)

        return cls.objects.filter(sent_from__in=addresses)


class Identity(models.Model):
    key = models.CharField(max_length=10, unique=True)
    anti_spam = models.BooleanField(default=False)


class UserIdentity(models.Model):
    user = models.ForeignKey(User)
    identity = models.ForeignKey(Identity)

    class Meta:
        unique_together = ('user', 'identity')


class AddressLog(models.Model):
    email = models.EmailField(max_length=75)
    reason = models.IntegerField()
    attempt = models.IntegerField()
    date = models.DateTimeField('Date of last attempt')


class SentStatistic(models.Model):
    date = models.DateField('Date sent')


class ReceivedStatistic(models.Model):
    email = models.EmailField(max_length=75)
    count = models.IntegerField(default=0)


class UserStatistic(models.Model):
    email = models.EmailField(max_length=75)
    count = models.IntegerField(default=0)


class ObliviousStatistic(models.Model):
    email = models.EmailField(max_length=75)
    count = models.IntegerField(default=0)


class LastImport(models.Model):
    date = models.DateTimeField('Date of last import')


@receiver(user_created)
def generate_user(user, **kwargs):
    identity = Identity(
        key = base64.b32encode(os.urandom(7))[:10].lower(),
    )
    identity.save()
    user_identity = UserIdentity(
        user=user,
        identity=identity
    )
    user_identity.save()
