import base64
import datetime
from mails import tools
from django.views import generic
from django.conf import settings
from django.core import management
from django.http import HttpResponseRedirect
from mails.forms import SettingsForm
from django.utils.decorators import method_decorator
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from mails.models import Mail, UserIdentity, ObliviousStatistic
from mails.models import SentStatistic, ReceivedStatistic, UserStatistic
from django.core.signals import request_started
from django.dispatch import receiver
from django.db.models import Count
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required


class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(
            LoginRequiredMixin,
            self
        ).dispatch(request, *args, **kwargs)


class MailView(generic.ListView):
    context_object_name = 'mails'

    @receiver(request_started)
    def import_mail(**kwargs):
        management.call_command('import', verbosity=1)

    def get_queryset(self):
        if self.request.user.is_authenticated():
            mails = Mail.my_mails(self.request)
            return mails.order_by('due')


class UpdateMailView(LoginRequiredMixin, generic.UpdateView):
    model = Mail
    fields = ['due']
    success_url = "/"

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is not None:
            queryset = queryset.filter(
                pk=pk,
                sent_from__in=tools.get_all_addresses(self.request)
            )
        obj = queryset.get()
        return obj


class TermsView(generic.TemplateView):
    template_name = 'mails/terms.html'


class HelpView(generic.TemplateView):
    template_name = 'mails/help.html'

    def get_context_data(self, **kwargs):
        context = super(HelpView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated():
            identity = UserIdentity.objects.get(
                user=self.request.user
            ).identity
            if identity.anti_spam:
                context['key'] = '.' + identity.key
            else:
                context['key'] = ''
        else:
            context['key'] = ''
        return context


class ActivationFail(generic.TemplateView):
    template_name = 'mails/address_activation_failed.html'


class LoginFailed(generic.TemplateView):
    template_name = 'mails/login_failed.html'


class ActivationSuccess(generic.TemplateView):
    template_name = 'mails/address_activated.html'


@login_required(login_url="/")
def settings_view(request):
    template_name = 'mails/settings.html'

    identity = UserIdentity.objects.get(user=request.user).identity

    anti_spam = SettingsForm(request.POST or None, instance=identity)

    alerts = []

    if request.method == 'POST':
        try:
            user_id = User.objects.get(id=request.POST['user_id'])
            user_id.delete()
        except:
            try:
                user_email = User.objects.get(email=request.POST['user_email'])
                tools.send_activation_mail(
                    address=user_email.email,
                    key=base64.b16encode(user_email.username),
                    host=request.get_host()
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


@login_required(login_url="/")
def download_vcard(request):
    host = settings.EMAIL_ADDRESS.split('@')[1]
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
        'mails/maildelay.vcf',
        {
            'mail_addresses' : mail_addresses
        },
        content_type='text/x-vcard'
    )

    response['Content-disposition'] = 'attachment;filename=maildelay.vcf'
    return response


@login_required(login_url="/")
def delete_confirmation(request, mail_id):
    mail = get_object_or_404(Mail, pk=mail_id)
    return render(request, 'mails/delete_confirmation.html', {'mail' : mail})


@login_required(login_url="/")
def delete(request):
    mail_id = request.POST['id']
    mail = Mail.my_mails(request).filter(id=mail_id)
    mail.delete()
    tools.delete_imap_mail(mail_id)
    return HttpResponseRedirect("/")


@login_required(login_url="/")
def activate(request, key):
    try:
        user = User.objects.get(username=base64.b16decode(key))
        user.is_active = True
        user.save()
        return HttpResponseRedirect('/activation_success/')
    except:
        return HttpResponseRedirect('/activation_fail/')


@staff_member_required
def statistics(request):
    now = datetime.datetime.now()
    week = now - datetime.timedelta(7)
    month = now - datetime.timedelta(30)

    sent = SentStatistic.objects.all()
    received = ReceivedStatistic.objects.all()
    users = UserStatistic.objects.values(
        'email').annotate(Count('id')).order_by('-id__count')
    oblivious = ObliviousStatistic.objects.values(
        'email').annotate(Count('id')).order_by('-id__count').exclude(
        email__contains='rmd.io')
    addresses = ReceivedStatistic.objects.values(
        'email').annotate(Count('id')).order_by('-id__count')

    return render(
        request,
        'mails/statistic.html',
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
