from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from mails import views
from . import forms

handler404 = 'maildelay.views.page_not_found_view'

urlpatterns = [

    url(r'^$',       views.BaseView.as_view()),

    url(r'^help/$',  views.HelpView.as_view()),

    url(r'^home/$', views.HomeView.as_view()),

    url(r'^login/$', auth_views.login, {'authentication_form': forms.LoginForm},
        name='login'),

    url(r'^logout/$', auth_views.logout, {'next_page': '/'}, name='logout'),

    url(r'^admin/', admin.site.urls),

    url(r'^password_reset/$', auth_views.password_reset,
        name='password_reset'),

    url(r'^password_reset/done/$', auth_views.password_reset_done,
        name='password_reset_done'),

    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm, name='password_reset_confirm'),

    url(r'^reset/done/$', auth_views.password_reset_complete,
        name='password_reset_complete'),

    url(r'^password_change/$', auth_views.password_change,
        name='password_change'),

    url(r'^password_change_done/$',
        auth_views.password_change_done, name='password_change_done'),

    url(r'^registration/$', views.RegistrationView.as_view()),

    url(r'^registration_done/(?P<key>[\w\.-]+)/',
        views.RegistrationDoneView.as_view()),

    url(r'^registration_send_mail/$',
        views.RegistrationSendMailView.as_view()),

    url(r'^terms/$', views.TermsView.as_view()),

    url(r'^mails/$', views.MailView.as_view()),

    url(r'^mails/delete/$', views.mail_delete_view),

    url(
        r'^mails/delete/confirm/(?P<id>\d+)/$',
        views.mail_delete_confirm_view
    ),

    url(
        r'^mails/table/$',
        views.MailView.as_view(template_name="mails/mails_table.html")
    ),

    url(r'^mails/edit/(?P<id>\d+)/$', views.mail_edit_view),

    url(r'^mails/update/$', views.mail_update_view),

    url(r'^mails/info/(?P<id>\d+)/$', views.mail_info_view),

    url(r'^download/maildelay.vcf', views.download_vcard_view),

    url(r'^settings/$', views.settings_view),

    url(r'^calendar/(?P<secret>.+)/$', views.download_calendar_view),

    url(r'^statistic/$', views.statistic_view),

    url(r'^user/add/$', views.user_add_view),

    url(r'^user/delete/confirm/(?P<id>\d+)/$', views.user_delete_confirm_view),

    url(r'^user/delete/$', views.user_delete_view),

    url(r'^user/activate/send/$', views.user_send_activation_view),

    url(r'^user/activate/(?P<key>.+)/$', views.user_activate_view),

    url(r'^user/connect/(?P<account_id>\d+)/(?P<key>.+)/$',
        views.user_connect_view),

]
