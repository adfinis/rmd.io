from django.conf.urls import patterns, url
from mails import views

urlpatterns = patterns('',
    url(r'^$', views.MailView.as_view(), name='mailindex'),
    url(r'^table/$', views.MailView.as_view(template_name="mails/table.html"), name='mailtable'),
    url(r'^error/$', views.ErrorView.as_view(), name='error'),
    url(r'^delete_confirmation/(?P<mail_id>\d+)/$', views.delete_confirmation, name='deleteconfirmation'),
    url(r'^delete/$', views.delete, name='delete'),
    url(r'^download/$', views.download_vcard, name='download'),
    url(r'^terms/$', views.TermsView.as_view(), name='terms'),
    url(r'^update/(?P<pk>\d+)/$', views.UpdateMailView.as_view(), name='update'),
)
