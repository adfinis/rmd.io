from django.urls import re_path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from mails import views
from . import forms

handler404 = "mails.views.page_not_found_view"

urlpatterns = [
    re_path(r"^$", views.BaseView.as_view()),
    re_path(r"^help/$", views.HelpView.as_view()),
    re_path(r"^home/$", views.HomeView.as_view()),
    re_path(
        r"^login/$",
        auth_views.LoginView.as_view(authentication_form=forms.LoginForm),
        name="login",
    ),
    re_path(
        r"^logout/$", auth_views.LogoutView.as_view(), {"next_page": "/"}, name="logout"
    ),
    re_path(r"^admin/", admin.site.urls),
    re_path(
        r"^password_reset/$",
        auth_views.PasswordResetView.as_view(),
        name="password_reset",
    ),
    re_path(
        r"^password_reset/done/$",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    re_path(
        r"^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    re_path(
        r"^reset/done/$",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    re_path(
        r"^password_change/$",
        login_required(login_url="/login/")(auth_views.PasswordChangeView.as_view()),
        name="password_change",
    ),
    re_path(
        r"^password_change_done/$",
        auth_views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    re_path(r"^registration/$", views.RegistrationView.as_view()),
    re_path(
        r"^registration_done/(?P<key>[\w\.-]+)/", views.RegistrationDoneView.as_view()
    ),
    re_path(r"^registration_send_mail/$", views.RegistrationSendMailView.as_view()),
    re_path(r"^terms/$", views.TermsView.as_view()),
    re_path(r"^mails/$", login_required(login_url="/login/")(views.MailView.as_view())),
    re_path(r"^mails/delete/$", views.mail_delete_view),
    re_path(r"^mails/delete/confirm/(?P<id>\d+)/$", views.mail_delete_confirm_view),
    re_path(
        r"^mails/table/$",
        views.MailView.as_view(template_name="mails/mails_table.html"),
    ),
    re_path(r"^mails/edit/(?P<id>\d+)/$", views.mail_edit_view),
    re_path(r"^mails/update/$", views.mail_update_view),
    re_path(r"^mails/info/(?P<id>\d+)/$", views.mail_info_view),
    re_path(r"^download/maildelay.vcf", views.download_vcard_view),
    re_path(r"^settings/$", views.settings_view),
    re_path(r"^calendar/(?P<secret>.+)/$", views.download_calendar_view),
    re_path(r"^statistic/$", views.statistic_view),
    re_path(r"^user/add/$", views.user_add_view),
    re_path(r"^user/delete/confirm/(?P<id>\d+)/$", views.user_delete_confirm_view),
    re_path(r"^user/delete/$", views.user_delete_view),
    re_path(r"^user/activate/send/$", views.user_send_activation_view),
    re_path(r"^user/activate/(?P<key>.+)/$", views.user_activate_view),
    re_path(
        r"^user/connect/(?P<account_id>\d+)/(?P<key>.+)/$", views.user_connect_view
    ),
]
