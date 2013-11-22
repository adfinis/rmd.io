from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.views import generic
from mails.models import Mail
from mails import tools
import imaplib
from django.conf import settings

class MailView(generic.ListView):
    template_name = 'mails/index.html'
    context_object_name = 'mails'

    def get_queryset(self):
        if self.request.user.is_authenticated():
            mails = Mail.objects.filter(sent_from=self.request.user.email)
            return mails.order_by('due')

def delete_confirmation(request, mail_id):
    mail = get_object_or_404(Mail, pk=mail_id)
    return render(request, 'mails/delete_confirmation.html', {'mail' : mail})

def delete(request):
    mail_id = request.POST['id']
    Mail.objects.get(id=mail_id).delete()
    tools.delete_imap_mail(mail_id)
    return HttpResponseRedirect('/')

class UpdateMailView(generic.UpdateView):
    model = Mail
    fields = ['due']
    success_url = '/'

class ErrorView(generic.TemplateView):
    template_name = 'mails/error.html'

class TermsView(generic.TemplateView):
    template_name = 'mails/terms.html'

def download_vcard(request):
    mail_addresses = [
        ('{2}'.format(*entry), '{0}@maildelay.tk'.format(*entry))
        for entry
        in settings.MAILBOXES
    ]
    response = render(request, 'mails/maildelay.vcf', { 'mail_addresses' : mail_addresses }, content_type='text/x-vcard')

    response['Content-disposition'] = 'attachment;filename=MailDelay.vcf'

    return response
