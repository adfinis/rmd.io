from django_browserid.signals import user_created
from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver
from mails.tools import Tools

tools = Tools()


class Mail(models.Model):
    subject   = models.CharField(max_length=200)
    sent      = models.DateTimeField()
    due       = models.DateTimeField()
    sender    = models.EmailField(max_length=75)

    @classmethod
    def my_mails(cls, request):
        addresses = tools.get_all_addresses(request)

        return cls.objects.filter(sender__in=addresses)


class Recipient(models.Model):
    mail  = models.ForeignKey(Mail)
    email = models.EmailField(max_length=75)
    name  = models.CharField(max_length=200, null=True)


class Identity(models.Model):
    key       = models.CharField(max_length=10, unique=True)
    anti_spam = models.BooleanField(default=False)


class UserIdentity(models.Model):
    user     = models.ForeignKey(User)
    identity = models.ForeignKey(Identity)

    class Meta:
        unique_together = ('user', 'identity')


class AddressLog(models.Model):
    reasons = (
        ('SPAM', 'Spam'),
        ('NREG', 'Not Registered')
    )

    email   = models.EmailField(max_length=75)
    reason  = models.CharField(max_length=4, choices=reasons)
    attempt = models.IntegerField()
    date    = models.DateTimeField(auto_now_add=True)


class Statistic(models.Model):
    types = (
        ('SENT', 'Sent'),
        ('REC',  'Received'),
        ('USER', 'User'),
        ('OBL',  'Oblivious'),
    )

    type  = models.CharField(max_length=4, choices=types)
    email = models.EmailField(null=True, max_length=75)
    date  = models.DateField(auto_now_add=True)


class LastImport(models.Model):
    date = models.DateTimeField(auto_now=True)


@receiver(user_created)
def generate_identity(user, **kwargs):
    identity = Identity(
        key = tools.generate_key(),
    )

    user_identity = UserIdentity(
        user=user,
        identity=identity
    )

    identity.save()
    user_identity.save()
