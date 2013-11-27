from django.db import models
from django.utils import timezone

class Mail(models.Model):
    subject = models.CharField(max_length=200)
    sent = models.DateTimeField('date sent')
    due = models.DateTimeField('date due')
    sent_from = models.CharField(max_length=200)

    @classmethod
    def my_mails(cls, request):
        return cls.objects.filter(sent_from=request.user.email)
