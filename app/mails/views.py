from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from django.core import management
from django.core.signals import request_started
from django.db.models import Count
from django.dispatch import receiver
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from mails.models import Mail, UserIdentity, Statistic
from mails.forms import SettingsForm
from mails.tools import Tools
import base64
import datetime

tools = Tools()


class BaseView(generic.RedirectView):
    def get_redirect_url(self, **kwargs):
        if self.request.user.is_authenticated():
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
            mails = Mail.my_mails(self.request)
            return mails.order_by('due')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MailView, self).dispatch(*args, **kwargs)


class MailInfoView(generic.DetailView):
    model = Mail
    template_name = 'mails/mail_info.html'


@login_required()
def mail_update(request, id):
    due = request.POST['due']
    mail = get_object_or_404(Mail, pk=id)
    if mail.sender == request.user.email:
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
            identity = UserIdentity.objects.get(
                user=self.request.user
            ).identity
            if identity.anti_spam:
                context['key'] = '.%s' % identity.key
            else:
                context['key'] = ''
        else:
            context['key'] = ''
        return context


@login_required()
def download_vcard(request):
    host = settings.EMAIL_HOST_USER.split('@')[1]
    identity = UserIdentity.objects.get(user=request.user).identity
    key = identity.key

    if identity.anti_spam:
        mail_template = '{delay}.{key}@{host}'
    else:
        mail_template = '{delay}@{host}'

    values = {
        'key' : key or None,
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


@login_required()
def activate(request, key):
    try:
        user = User.objects.get(username=base64.b16decode(key))
        user.is_active = True
        user.save()
        tools.delete_log_entries(user.email)
        return HttpResponseRedirect('/activation_success/')
    except:
        return HttpResponseRedirect('/activation_fail/')


@login_required()
def statistic_view(request):
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


@login_required()
def mail_delete_confirm(request, id):
    mail = get_object_or_404(Mail, pk=id)
    return render(request, 'mails/mail_delete_confirm.html', {'mail' : mail})


@login_required()
def mail_delete(request):
    mail_id = request.POST['id']
    mail = Mail.my_mails(request).filter(id=mail_id)
    mail.delete()
    tools.delete_email(mail_id)
    return HttpResponseRedirect("/")


@login_required()
def settings_view(request):
    template_name = 'mails/settings/settings.html'

    identity = UserIdentity.objects.get(user=request.user).identity

    anti_spam = SettingsForm(request.POST or None, instance=identity)

    alerts = []

    if request.method == 'POST':
        try:
            user = User.objects.get(id=request.POST['user_id'])
            user.delete()
            tools.delete_log_entries(user.email)
        except:
            try:
                user_email = User.objects.get(email=request.POST['user_email'])
                tools.send_activation_mail(
                    email_to=user_email.email,
                    key=base64.b16encode(user_email.username)
                )
            except:
                anti_spam_new = request.POST['anti_spam']
                anti_spam_old = str(identity.anti_spam).lower()
                if anti_spam_old != anti_spam_new:
                    anti_spam.anti_spam = anti_spam_new
                    anti_spam.save()
                    if identity.anti_spam is True:
                        alerts.append('mails/anti_spam_on.html')
                    else:
                        alerts.append('mails/anti_spam_off.html')
                elif request.POST['address'] != '':
                    address = request.POST['address']
                    if User.objects.filter(email=address).exists():
                        alerts.append('mails/address_already_exists.html')
                    else:
                        tools.create_additional_user(
                            email=address,
                            request=request
                        )
                        alerts.append('mails/address_added.html')
                alerts.append('mails/settings_saved.html')

    additional_users = tools.get_all_users(request)
    additional_users.remove(request.user)

    response = render(
        request,
        template_name,
        {
            'anti_spam' : anti_spam,
            'alerts' : alerts,
            'identity' : identity,
            'additional_users' : additional_users,
            'main_user' : request.user
        }
    )

    return response
