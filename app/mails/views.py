from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.views import generic
from mails.models import Mail
from mails import tools
import imaplib
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)

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
            queryset = queryset.filter(pk=pk, sent_from=self.request.user.email)
        obj = queryset.get()
        return obj

class ErrorView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'mails/error.html'

class TermsView(generic.TemplateView):
    template_name = 'mails/terms.html'

@login_required(login_url="/")
def download_vcard(request):
    mail_addresses = [
        ('{2}'.format(*entry), '{0}@rmd.io'.format(*entry))
        for entry
        in settings.MAILBOXES
    ]
    response = render(request, 'mails/maildelay.vcf', { 'mail_addresses' : mail_addresses }, content_type='text/x-vcard')
    response['Content-disposition'] = 'attachment;filename=maildelay.vcf'
    return response

@login_required(login_url="/")
def delete_confirmation(request, mail_id):
    mail = get_object_or_404(Mail, pk=mail_id)
    return render(request, 'mails/delete_confirmation.html', {'mail' : mail})

@login_required(login_url="/")
def delete(request):
    mail_id = request.POST['id']
    mail = Mail.my_mails(self.request).filter(id=mail_id)
    mail.delete()
    tools.delete_imap_mail(mail_id)
    return HttpResponseRedirect("/")
