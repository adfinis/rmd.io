from django.http import HttpResponseRedirect
from mails.forms import SettingsForm
from django.shortcuts import render, get_object_or_404
from django.views import generic
from mails.models import Mail, Settings, UserKey
from mails import tools
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import base64
import os


class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(
            LoginRequiredMixin,
            self
        ).dispatch(request, *args, **kwargs)


class MailView(generic.ListView):
    template_name = 'mails/index.html'
    context_object_name = 'mails'

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
                sent_from=self.request.user.email
            )
        obj = queryset.get()
        return obj


class ErrorView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'mails/error.html'


class TermsView(generic.TemplateView):
    template_name = 'mails/terms.html'


class HelpView(generic.TemplateView):
    template_name = 'mails/help.html'


@login_required(login_url="/")
def settings_view(request):
    template_name = 'mails/settings.html'
    row = Settings.objects.get(user=request.user)
    form = SettingsForm(request.POST or None, instance=row)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
        else:
            form.anti_spam = False
            form.save()
        return HttpResponseRedirect('/')

    response = render(
        request,
        template_name,
        {
            'form' : form
        }
    )

    return response


@login_required(login_url="/")
def download_vcard(request):
    host = settings.EMAIL_ADDRESS.split('@')[1]
    try:
        request.user.userkey
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
        'key' : request.user.userkey.key,
        'host' : host,
    }

    mail_addresses = [
        (
            '{2}'.format(*entry),
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

    response['Content-disposition'] = 'attachment;filename=Maildelay.vcf'
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
