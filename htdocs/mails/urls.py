from django.conf.urls import patterns, url
from mails import views

urlpatterns = patterns('',
    url(r'^$', views.MailView.as_view(), name='mailindex'),
    url(r'^error/$', views.ErrorView.as_view(), name='error'),
    url(r'^delete/(?P<pk>\d+)/$', views.DeleteMailView.as_view(), name='delete'),
    url(r'^update/(?P<pk>\d+)/$', views.UpdateMailView.as_view(), name='edit'),
)
