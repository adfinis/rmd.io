import os
import base64
from hashlib import md5
from mails import tools
from django.views import generic
from django.conf import settings
from django.core import management
from django.http import HttpResponseRedirect
from mails.forms import SettingForm, AddressForm
from django.utils.decorators import method_decorator
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from mails.models import Mail, Setting, UserKey, AdditionalAddress
from django.core.signals import request_started
from django.dispatch import receiver


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
                sent_from__in=tools.get_all_addresses(self.request.user)
            )
        obj = queryset.get()
        return obj


class TermsView(generic.TemplateView):
    template_name = 'mails/terms.html'


class HelpView(generic.TemplateView):
    template_name = 'mails/help.html'


class ActivationFail(generic.TemplateView):
    template_name = 'mails/address_activation_failed.html'


class ActivationSuccess(generic.TemplateView):
    template_name = 'mails/address_activated.html'


@login_required(login_url="/")
def settings_view(request):
    template_name = 'mails/settings.html'

    user = Setting.objects.get(user=request.user)
    anti_spam = SettingForm(request.POST or None, instance=user)

    additional_addresses = AdditionalAddress.objects.filter(
        user=request.user
    )
    addresses_form = AddressForm(request.POST or None, instance=request.user)

    alerts = []

    if request.method == 'POST':
        try:
            a = AdditionalAddress.objects.get(
                id = request.POST['address_id']
            )
            a.delete()
        except:
            anti_spam.anti_spam = request.POST['anti_spam']
            anti_spam.save()
            anti_spam_setting = request.user.settings.anti_spam
            if anti_spam_setting is True:
                alerts.append('mails/anti_spam_on.html')
            else:
                alerts.append('mails/anti_spam_off.html')
            if request.POST['address'] != '':
                address = request.POST['address']
                if AdditionalAddress.objects.filter(address=address).exists():
                    alerts.append('mails/address_already_exists.html')
                else:
                    address = AdditionalAddress(
                        user = request.user,
                        activation_key = md5(
                            os.urandom(7)
                        ).hexdigest(),
                        address = address
                    )
                    address.save()
                    key = address.activation_key
                    host = request.get_host()
                    tools.send_activation_mail(key, address.address, host)
                    alerts.append('mails/address_added.html')
            alerts.append('mails/settings_saved.html')

    response = render(
        request,
        template_name,
        {
            'anti_spam' : anti_spam,
            'additional_addresses' : additional_addresses,
            'addresses_form' : addresses_form,
            'alerts' : alerts,
            'user_key' : UserKey.get_userkey(request.user),
        }
    )

    return response


@login_required(login_url="/")
def download_vcard(request):
    host = settings.EMAIL_ADDRESS.split('@')[1]
    try:
        user_key = UserKey.get_userkey(request.user)
    except:
        key = UserKey(key=base64.b32encode(
            os.urandom(7))[:10].lower(),
            user=request.user
        )
        key.save()
    if request.user.settings.anti_spam:
        mail_template = '{delay}.{key}@{host}'
    else:
        mail_template = '{delay}@{host}'

    values = {
        'key' : user_key or None,
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
        address = AdditionalAddress.objects.get(activation_key=key)
        address.is_activated = True
        address.save()
        return HttpResponseRedirect('/activation_success/')
    except:
        return HttpResponseRedirect('/activation_fail/')
