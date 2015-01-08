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
from mails.models import Mail, Statistic
from mails import tools, imaphelper
import base64
import datetime


def page_not_found(request):
    return render(request, '404.html')


def staff_required(login_url=None):
    return user_passes_test(lambda u: u.is_staff, login_url=login_url)


class BaseView(generic.RedirectView):
    def get_redirect_url(self, **kwargs):
        next_url = self.request.GET.get('next', None)
        if self.request.user.is_authenticated():
            if next_url:
                return next_url
            else:
                return '/mails/'
        else:
            return '/login/'


class LoginView(generic.TemplateView):
    template_name = 'login.html'


class MailView(generic.ListView):
    template_name = 'mails/mails.html'
    context_object_name = 'mails'

    @receiver(request_started)
    def import_mail(**kwargs):
        management.call_command('import', verbosity=1)

    def get_queryset(self):
        if self.request.user.is_authenticated():
            mails = Mail.my_mails(self.request.user)
            return sorted(mails, key=lambda m: m.next_due().due)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MailView, self).dispatch(*args, **kwargs)


@login_required(login_url='/login/')
def mail_info(request, id):
    mail = get_object_or_404(Mail.my_mails(request.user), pk=id)
    return render(request, 'mails/mail_info.html', {'mail' : mail})


@login_required(login_url='/login/')
def mail_update(request, id):
    due = request.POST['due']
    mail = get_object_or_404(Mail.my_mails(request.user), pk=id)
    mail.due = due
    mail.save()
    return redirect('/mails/')


class TermsView(generic.TemplateView):
    template_name = 'terms.html'


class HelpView(generic.TemplateView):
    template_name = 'help.html'

    def get_context_data(self, **kwargs):
        context = super(HelpView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated():
            account = self.request.user.get_account()

            if account.anti_spam:
                context['key'] = '.%s' % account.key
            else:
                context['key'] = ''
        else:
            context['key'] = ''
        return context


@login_required(login_url='/login/')
def download_vcard(request):
    host = settings.EMAIL_HOST_USER.split('@')[1]
    account = request.user.get_account()

    if account.anti_spam:
        mail_template = '{delay}.{key}@{host}'
    else:
        mail_template = '{delay}@{host}'

    values = {
        'key' : account.key or None,
        'host' : host,
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
            'mail_addresses' : mail_addresses
        },
        content_type='text/x-vcard'
    )

    response['Content-disposition'] = 'attachment;filename=maildelay.vcf'
    return response


@login_required(login_url='/login/')
def activate(request, key):
    try:
        user = User.objects.get(username=base64.b16decode(key))
        user.is_active = True
        user.save()
        messages.success(request, 'The user %s was successfully activated.' % user.email)
        tools.delete_log_entries(user.email)
    except:
        messages.error(request, 'The user could not be activated.')

    return HttpResponseRedirect('/')


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
            'oblivious_alltime' : oblivious[:10],
            'oblivious_month' : oblivious.filter(date__gte=month)[:10],
            'oblivious_week' : oblivious.filter(date__gte=week)[:10],
            'addresses_alltime' : addresses[:10],
            'addresses_month' : addresses.filter(date__gte=month)[:10],
            'addresses_week' : addresses.filter(date__gte=week)[:10],
            'received_alltime' : len(received),
            'received_month' : len(received.filter(date__gte=month)),
            'received_week' : len(received.filter(date__gte=week)),
            'users_alltime' : users[:10],
            'users_month' : users.filter(date__gte=month)[:10],
            'users_week' : users.filter(date__gte=week)[:10],
            'sent_alltime' : len(sent),
            'sent_month' : len(sent.filter(date__gte=month)),
            'sent_week' : len(sent.filter(date__gte=week))
        }
    )


@login_required(login_url='/login/')
def mail_delete_confirm(request, id):
    mail = get_object_or_404(Mail.my_mails(request.user), pk=id)
    return render(request, 'mails/mail_delete_confirm.html', {'mail' : mail})


@login_required(login_url='/login/')
def mail_delete(request):
    mail_id = request.POST.get('id')
    mail = get_object_or_404(Mail.my_mails(request.user), pk=mail_id)

    mail.delete()
    imap_mail = imaphelper.IMAPMessage.from_dbid(mail_id)
    imap_mail.delete()

    return HttpResponseRedirect("/")


@login_required(login_url='/login/')
def settings_view(request):
    account = request.user.get_account()

    if request.method == 'POST':
        anti_spam = request.POST.get('anti_spam', False)
        if bool(anti_spam) != bool(account.anti_spam):
            account.anti_spam = anti_spam
            account.save()
            if bool(account.anti_spam) is True:
                messages.info(request, 'Antispam is now enabled. Please use your key for every address.')
            else:
                messages.info(request, 'Antispam is now disabled. You can use your normal addresses.')

        return HttpResponseRedirect("/")

    users = tools.get_all_users_of_account(request.user)

    response = render(
        request,
        'mails/settings/settings.html',
        {
            'anti_spam_enabled' : account.anti_spam,
            'account' : account,
            'users' : users
        }
    )

    return response


@login_required(login_url='/login/')
def add_user_view(request):
    if request.POST:
        email = request.POST.get('email', False)
        if User.objects.filter(email=email).exists():
            messages.warning(request, "The user '%s' already exists." % email)
        elif email != '':
            tools.create_additional_user(
                email=email,
                request=request
            )

    users = tools.get_all_users_of_account(request.user)

    response = render(
        request,
        'mails/settings/user_table.html',
        {'users' : users}
    )

    return response


@login_required(login_url='/login/')
def user_delete_confirm(request, id):
    users = tools.get_all_users_of_account(request.user)
    user = get_object_or_404(User, pk=id)
    if user in users:
        return render(request, 'mails/settings/user_delete_confirm.html', {'user' : user})
    else:
        return Http404


@login_required(login_url='/login/')
def user_delete(request):
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
def send_activation(request):
    if request.POST:
        user = User.objects.get(id=request.POST['id'])
        email = user.email

        tools.send_activation_mail(
            recipient = email,
            key = base64.b16encode(user.username)
        )

    return HttpResponse('')
