from django.conf.urls import patterns, url
from mails import views

urlpatterns = patterns('',
    url(r'^$', views.MailView.as_view(), name='mailindex'),
)
