from django.conf.urls import patterns, url
from mails import views

urlpatterns = patterns(
    '',
    url(r'^$', views.MailView.as_view()),
    url(r'^table/$', views.MailView.as_view(template_name="mails/table.html")),
    url(r'^delete_confirmation/(?P<mail_id>\d+)/$', views.delete_confirmation),
    url(r'^delete/$', views.delete),
    url(r'^update/(?P<pk>\d+)/$', views.UpdateMailView.as_view()),
    url(r'^maildelay.vcf', views.download_vcard),
    url(r'^terms/$', views.TermsView.as_view()),
    url(r'^settings/$', views.settings_view),
    url(r'^help/$', views.HelpView.as_view()),
    url(r'^activate/(?P<key>\w+)/$', views.activate),
    url(r'^successfully_activated/$', views.SuccessfullyActivated.as_view()),
    url(r'^activation_failed/$', views.ActivationFailed.as_view()),
    url(r'^already_exists/$', views.AlreadyExists.as_view()),
    url(r'^added_successfully/$', views.AddedSuccessfully.as_view()),
)
