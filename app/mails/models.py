from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
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
    user = models.ForeignKey(User)

    @classmethod
    def get_user_key(cls, user):
        try:
            return cls.objects.get(user=user.id)
        except:
            key = cls()
            key.user = user
            key.key = base64.b32encode(os.urandom(7))[:10].lower()
            key.save()
            return key
