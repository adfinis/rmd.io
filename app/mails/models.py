from django.db import models
from django.contrib.auth.models import User
from django_browserid.signals import user_created
from django.dispatch import receiver
import base64
import os


class Mail(models.Model):
    subject = models.CharField(max_length=200)
    sent = models.DateTimeField('date sent')
    due = models.DateTimeField('date due')
    sent_from = models.CharField(max_length=200)
    sent_to = models.CharField(max_length=200)

    @classmethod
    def my_mails(cls, request):
        return cls.objects.filter(sent_from=request.user.email)


class UserKey(models.Model):
    key = models.CharField(max_length=10)
    user = models.OneToOneField(User, related_name="userkey")


class Settings(models.Model):
    anti_spam = models.BooleanField(default=False)
    user = models.OneToOneField(User, related_name="settings")


@receiver(user_created)
def generate_key(user, **kwargs):
    key = UserKey(key=base64.b32encode(os.urandom(7))[:10].lower(), user=user)
    anti_spam = Settings(user=user)
    key.save()
    anti_spam.save()
