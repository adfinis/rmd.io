from django.conf.urls import patterns, url
from mails import views

urlpatterns = patterns(
    '',
    url(r'^$', views.MailView.as_view()),
    url(r'^table/$', views.MailView.as_view(template_name="mails/table.html")),
    url(r'^error/$', views.ErrorView.as_view(), name='error'),
    url(r'^delete_confirmation/(?P<mail_id>\d+)/$', views.delete_confirmation),
    url(r'^delete/$', views.delete),
    url(r'^update/(?P<pk>\d+)/$', views.UpdateMailView.as_view()),
    url(r'^maildelay.vcf/$', views.download_vcard),
    url(r'^terms/$', views.TermsView.as_view()),
    url(r'^settings/$', views.settings_view),
    url(r'^help/$', views.HelpView.as_view()),
)
