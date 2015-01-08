from django_browserid.signals import user_created
from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver
from mails import tools


class Mail(models.Model):
    user    = models.ForeignKey(User)
    subject = models.CharField(max_length=200)
    sent    = models.DateTimeField()

    @classmethod
    def my_mails(cls, user):
        users = tools.get_all_users_of_account(user)
        return cls.objects.filter(user__in=users)

    def next_due(self):
        return Due.objects.filter(mail=self).order_by('due')[0]


class Account(models.Model):
    key       = models.CharField(max_length=10, unique=True)
    anti_spam = models.BooleanField(default=False)


class UserProfile(models.Model):
    user    = models.OneToOneField(User)
    account = models.ForeignKey(Account)


class Recipient(models.Model):
    mail  = models.ForeignKey(Mail)
    name  = models.CharField(max_length=200, blank=True)
    email = models.EmailField(max_length=75, blank=True)


class Due(models.Model):
    mail = models.ForeignKey(Mail)
    due  = models.DateTimeField()


class Statistic(models.Model):
    types = (
        ('SENT', 'Sent'),
        ('REC',  'Received'),
        ('USER', 'User'),
        ('OBL',  'Oblivious'),
    )

    type  = models.CharField(max_length=4, choices=types)
    email = models.EmailField(blank=True, max_length=75)
    date  = models.DateField(auto_now_add=True)


class AddressLog(models.Model):
    reasons = (
        ('SPAM', 'Spam'),
        ('NREG', 'Not Registered')
    )

    email   = models.EmailField(max_length=75)
    reason  = models.CharField(max_length=4, choices=reasons)
    attempt = models.IntegerField()
    date    = models.DateTimeField(auto_now_add=True)


class ImportLog(models.Model):
    date = models.DateTimeField(auto_now=True)


def get_account(self):
    return self.userprofile.account

@receiver(user_created)
def generate_account(user, **kwargs):
    account = Account(key=tools.generate_key())
    account.save()
    user_profile = UserProfile(
        user=user,
        account=account
    )
    user_profile.save()

User.add_to_class('get_account', get_account)
