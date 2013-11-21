from django.conf.urls import patterns, url
from mails import views

urlpatterns = patterns('',
    url(r'^$', views.MailView.as_view(), name='mailindex'),
    url(r'^error/$', views.ErrorView.as_view(), name='error'),
    url(r'^delete_confirmation/(?P<mail_id>\d+)/$', views.delete_confirmation, name='deleteconfirmation'),
    url(r'^delete/$', views.delete, name='delete'),
    url(r'^update/(?P<pk>\d+)/$', views.UpdateMailView.as_view(), name='update'),
)
