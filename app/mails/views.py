from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.core import management
from django.core.signals import request_started
from django.db.models import Count
from django.dispatch import receiver
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import generic
from mails.forms import RegistrationForm
from mails.models import Mail, Statistic, Due, Account, UserProfile
from mails import tools, imaphelper
from icalendar import Calendar, Event
from django.views.generic import FormView
from django.core.mail import send_mail
import re
import base64
import datetime
import logging
import hashlib

try:
    from django.utils.encoding import smart_bytes
except ImportError:
    from django.utils.encoding import smart_str as smart_bytes

logger = logging.getLogger('mails')


def page_not_found_view(request):
    return render(request, '404.html')


def staff_required(login_url=None):
    return user_passes_test(lambda u: u.is_staff, login_url=login_url)


class BaseView(generic.RedirectView):
    def get_redirect_url(self, **kwargs):
        next_url = self.request.GET.get('next', None)
        if self.request.user.is_authenticated:
            if next_url:
                return next_url
            else:
                return '/mails/'
        else:
            return '/home/'


class TermsView(generic.TemplateView):
    template_name = 'terms.html'


class HelpView(generic.TemplateView):
    template_name = 'help.html'

    def get_context_data(self, **kwargs):
        context = super(HelpView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            account = self.request.user.get_account()

            if account.anti_spam:
                context['key'] = '.%s' % account.key
            else:
                context['key'] = ''
        else:
            context['key'] = ''
        return context


class HomeView(generic.TemplateView):
    template_name = 'home.html'


class RegistrationView(FormView):
    template_name = 'registration.html'
    form_class = RegistrationForm
    success_url = '/registration_send_mail'

    def form_valid(self, form):
        email = form.data.get('email')
        password = form.data.get('password1')
        username = base64.urlsafe_b64encode(
            hashlib.sha1(smart_bytes(email)).digest()
        ).rstrip(b'=')

        user = User.objects.create_user(username, email, password)
        user.is_active = False
        user.save()

        if user is not None:
            self.generate_account(user)

        return super(RegistrationView, self).form_valid(form)

    def generate_account(self, user):
        account = Account(key=tools.generate_key())
        account.save()
        user_profile = UserProfile(
            user=user,
            account=account
        )
        user_profile.save()
        send_mail(
            'Rmd.io account confirmation',
            """
            Hello,

            please click this link to activate your rmd.io account:
            {0}/registration_done/{1}

            Sincerely,
            The rmd.io Team
            """.format(
              settings.SITE_URL,
              str(account.key, 'utf-8')
            ),
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )


class RegistrationDoneView(generic.TemplateView):
    template_name = 'registration_done.html'

    def get_context_data(request, key):
            matches = Account.objects.filter(key=key)
            if matches.exists():
                account = matches.first()
                user_profile = UserProfile.objects.get(account=account)
                if user_profile.user.is_active:
                    request.template_name = 'user_is_already_active.html'
                else:
                    user_profile.user.is_active = True
                    user_profile.user.save()
            else:
                request.template_name = 'registration_failed.html'


class RegistrationSendMailView(generic.TemplateView):
    template_name = 'registration_send_mail.html'


class MailView(generic.ListView):
    template_name = 'mails/mails.html'
    context_object_name = 'mails'

    @receiver(request_started)
    def import_mail(**kwargs):
        management.call_command('import', verbosity=1)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            mails = Mail.my_mails(self.request.user)
            return sorted(mails, key=lambda m: m.next_due().due)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MailView, self).dispatch(*args, **kwargs)


@login_required(login_url='/login/')
def mail_info_view(request, id):
    mail = get_object_or_404(Mail.my_mails(request.user), pk=id)
    return render(request, 'mails/mail_info.html', {'mail': mail})


def mail_edit_view(request, id):
    dues = Due.objects.filter(mail__id=id)
    return render(request, 'mails/mail_edit.html', {
        'dues': dues, 'mail_id': id
    })


def mail_update_view(request):
    mail = get_object_or_404(Mail.my_mails(request.user),
                             pk=request.POST['mail_id'])
    saved_dues = Due.objects.filter(mail=mail).values_list('id', flat=True)
    edited_dues = []

    dues = request.POST.lists()

    for due in dues:
        if due[0] == 'due-new':
            for dt in due[1]:
                if dt:
                    d = Due(mail=mail, due=dt)
                    d.save()
                    edited_dues.append(d.id)
                else:
                    messages.error(request, 'Please fill out the due date.')
        else:
            try:
                due_id = int(re.sub(r'due-', '', due[0]))
                d = Due.objects.get(mail=mail, pk=due_id)
                d.due = due[1][0]
                d.save()
                edited_dues.append(due_id)
            except:
                pass

    for saved_due in saved_dues:
        if saved_due not in edited_dues:
            d = Due.objects.get(mail=mail, pk=saved_due)
            d.delete()

    return HttpResponseRedirect('/mails/')


@login_required(login_url='/login/')
def mail_delete_confirm_view(request, id):
    mail = get_object_or_404(Mail.my_mails(request.user), pk=id)
    return render(request, 'mails/mail_delete_confirm.html', {'mail': mail})


@login_required(login_url='/login/')
def mail_delete_view(request):
    mail_id = request.POST.get('id')
    mail = get_object_or_404(Mail.my_mails(request.user), pk=mail_id)

    imap_conn = imaphelper.get_connection()
    imap_mail = imaphelper.IMAPMessage.from_dbid(mail_id, imap_conn)
    mail.delete()
    imap_mail.delete()

    return HttpResponseRedirect("/")


def download_calendar_view(request, secret):
    username = base64.urlsafe_b64decode(secret.encode('utf-8'))
    user = User.objects.get(username=username)
    dues = Due.objects.filter(mail__in=Mail.my_mails(user))
    cal = Calendar()
    cal.add('prodid', '-//rmd.io Events Calendar//%s//EN' % settings.SITE_URL)
    cal.add('version', '2.0')

    for due in dues:
        event = Event()
        event.add('summary', '%s [rmd.io]' %
                  tools.calendar_clean_subject(due.mail.subject))
        event.add('description', '%s/mails/' % settings.SITE_URL)
        event.add('dtstart', due.due)
        event.add('dtend', due.due)
        cal.add_component(event)

    response = HttpResponse(content=cal.to_ical(), content_type='text/calendar')
    response['Content-Disposition'] = 'attachment; filename=maildelay.ics'

    return response


@login_required(login_url='/login/')
def download_vcard_view(request):
    host = settings.EMAIL_HOST_USER.split('@')[1]
    account = request.user.get_account()

    if account.anti_spam:
        mail_template = '{delay}.{key}@{host}'
    else:
        mail_template = '{delay}@{host}'

    values = {
        'key': account.key or None,
        'host': host,
    }

    mail_addresses = [
        (
            '{1}'.format(*entry),
            mail_template.format(delay=entry[0], **values)
        )
        for entry
        in settings.MAILBOXES
    ]

    response = render(
        request,
        'mails/download/maildelay.vcf',
        {
            'mail_addresses': mail_addresses
        },
        content_type='text/x-vcard'
    )

    response['Content-disposition'] = 'attachment;filename=maildelay.vcf'
    return response


@login_required(login_url='/login/')
def user_activate_view(request, key):
    try:
        username = base64.urlsafe_b64decode(key.encode('utf-8'))
        user = User.objects.get(username=username)
        user.is_active = True
        user.save()
        messages.success(request, 'The user %s was successfully activated.'
                         % user.email)
        tools.delete_log_entries(user.email)
    except:
        messages.error(request, 'The user could not be activated.')

    return HttpResponseRedirect('/')


@login_required(login_url='/login/')
def user_connect_view(request, key, account_id):
    try:
        account = Account.objects.get(pk=account_id)
        username = base64.urlsafe_b64decode(key.encode('utf-8'))
        user = User.objects.get(username=username)
        old_account = user.userprofile.account
        user.userprofile.account = account
        user.userprofile.save()
        old_account.delete()
        messages.success(
            request,
            'The user %s was successfully connected with this account.'
            % user.email)
        tools.delete_log_entries(user.email)
    except:
        messages.error(request, 'The user could not be connected.')

    return HttpResponseRedirect('/')


@login_required(login_url='/login/')
def user_add_view(request):
    if request.POST:
        email = request.POST.get('email', False)
        try:
            user = User.objects.get(email=email)
            key = base64.urlsafe_b64encode(user.username)
            tools.send_connection_mail(account=request.user.get_account(),
                                       recipient=user.email, key=key)
        except:
            if email != '':
                tools.create_additional_user(
                    email=email,
                    user=request.user
                )

    users = tools.get_all_users_of_account(request.user)

    response = render(
        request,
        'mails/settings/user_table.html',
        {'users': users}
    )

    return response


@login_required(login_url='/login/')
def user_delete_confirm_view(request, id):
    users = tools.get_all_users_of_account(request.user)
    user = get_object_or_404(User, pk=id)
    if user in users:
        return render(
            request,
            'mails/settings/user_delete_confirm.html', {'user': user})
    else:
        return Http404


@login_required(login_url='/login/')
def user_delete_view(request):
    if request.POST:
        users = tools.get_all_users_of_account(request.user)
        user = User.objects.get(id=request.POST['id'])
        if user in users:
            user.delete()
            tools.delete_log_entries(user.email)
        else:
            return Http404
    return HttpResponseRedirect('/')


@login_required(login_url='/login/')
def user_send_activation_view(request):
    if request.POST:
        user = User.objects.get(id=request.POST['id'])
        email = user.email

        tools.send_activation_mail(
            recipient=email,
            key=base64.urlsafe_b64encode(user.username)
        )

    return HttpResponse('')


@login_required(login_url='/login/')
def settings_view(request):
    account = request.user.get_account()

    if request.method == 'POST':
        anti_spam = request.POST.get('anti_spam', False)
        if bool(anti_spam) != bool(account.anti_spam):
            account.anti_spam = bool(anti_spam)
            account.save()
            if bool(account.anti_spam) is True:
                messages.info(
                    request,
                    '''Antispam is now enabled.
                    Please use your key for every address.''')
            else:
                messages.info(
                    request,
                    '''Antispam is now disabled.
                    You can use your normal addresses.''')

        return HttpResponseRedirect("/")

    users = tools.get_all_users_of_account(request.user)

    response = render(
        request,
        'mails/settings/settings.html',
        {
            'anti_spam_enabled': account.anti_spam,
            'account': account,
            'users': users,
            'domain': settings.SITE_URL,
            'secret': base64.urlsafe_b64encode(request.user.username.encode()),
        }
    )

    return response


@login_required(login_url='/login/')
def statistic_view(request):
    if not request.user.is_staff:
        messages.error(request, 'Access denied!')
        return redirect('/')

    now = datetime.datetime.now()
    week = now - datetime.timedelta(7)
    month = now - datetime.timedelta(30)

    sent = Statistic.objects.filter(type='SENT')
    received = Statistic.objects.filter(type='REC')
    users = Statistic.objects.filter(type='USER').values(
        'email').annotate(Count('id')).order_by('-id__count')
    oblivious = Statistic.objects.filter(type='OBL').values(
        'email').annotate(Count('id')).order_by('-id__count').exclude(
        email__contains='rmd.io')
    addresses = Statistic.objects.filter(type='REC').values(
        'email').annotate(Count('id')).order_by('-id__count')

    return render(
        request,
        'mails/statistics/statistics.html',
        {
            'oblivious_alltime': oblivious[:10],
            'oblivious_month': oblivious.filter(date__gte=month)[:10],
            'oblivious_week': oblivious.filter(date__gte=week)[:10],
            'addresses_alltime': addresses[:10],
            'addresses_month': addresses.filter(date__gte=month)[:10],
            'addresses_week': addresses.filter(date__gte=week)[:10],
            'received_alltime': len(received),
            'received_month': len(received.filter(date__gte=month)),
            'received_week': len(received.filter(date__gte=week)),
            'users_alltime': users[:10],
            'users_month': users.filter(date__gte=month)[:10],
            'users_week': users.filter(date__gte=week)[:10],
            'sent_alltime': len(sent),
            'sent_month': len(sent.filter(date__gte=month)),
            'sent_week': len(sent.filter(date__gte=week))
        }
    )
