from django.conf.urls import patterns, url
from mails import views

urlpatterns = patterns(
    '',
    url(r'^$',       views.BaseView.as_view()),
    url(r'^help/$',  views.HelpView.as_view()),
    url(r'^login/$', views.LoginView.as_view()),
    url(r'^terms/$', views.TermsView.as_view()),
    url(r'^mails/$', views.MailView.as_view()),
    url(r'^mails/delete/$', views.mail_delete),
    url(
        r'^mails/delete/confirm/(?P<id>\d+)/$',
        views.mail_delete_confirm
    ),
    url(
        r'^mails/info/(?P<pk>\d+)/$',
        views.MailInfoView.as_view()
    ),
    url(
        r'^mails/table/$',
        views.MailView.as_view(template_name="mails/mails_table.html")
    ),
    url(r'^mails/update/(?P<id>\d+)/$', views.mail_update),
    url(r'^download/maildelay.vcf', views.download_vcard),
    url(r'^settings/$', views.settings_view),
    url(r'^statistic/$', views.statistic_view),
    url(r'^user/add/$', views.add_user_view),
    url(r'^user/delete/$', views.delete_user_view),
    url(r'^user/activate/(?P<key>\w+)/$', views.activate),
)
