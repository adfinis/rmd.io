from django.conf.urls import patterns, url
from mails import views

handler404 = 'maildelay.views.page_not_found'

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
        r'^mails/table/$',
        views.MailView.as_view(template_name="mails/mails_table.html")
    ),
    url(r'^mails/edit/(?P<id>\d+)/$', views.mail_edit),
    url(r'^mails/update/$', views.mail_update),
    url(r'^mails/info/(?P<id>\d+)/$', views.mail_info),
    url(r'^download/maildelay.vcf', views.download_vcard),
    url(r'^settings/$', views.settings_view),
    url(r'^calendar/(?P<secret>\w+)/$', views.calendar),
    url(r'^statistic/$', views.statistic_view),
    url(r'^user/add/$', views.add_user_view),
    url(r'^user/delete/confirm/(?P<id>\d+)/$', views.user_delete_confirm),
    url(r'^user/delete/$', views.user_delete),
    url(r'^user/activate/send/$', views.send_activation),
    url(r'^user/activate/(?P<key>\w+)/$', views.activate),
)
