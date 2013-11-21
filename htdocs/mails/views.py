from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.views import generic
from mails.models import Mail
import imaplib
from django.conf import settings

class MailView(generic.ListView):
    template_name = 'mails/index.html'
    context_object_name = 'mails'

    def get_queryset(self):
        if self.request.user.is_authenticated():
            mails = Mail.objects.filter(sent_from=self.request.user.email)
            if 'search' in self.request.GET:
                search = self.request.GET['search'] + '%'
                mails = mails.filter(subject__contains = search)

            return mails.order_by("due")

def delete_confirmation(request, mail_id):
    mail = get_object_or_404(Mail, pk=mail_id)
    return render(request, 'mails/delete_confirmation.html', {'mail' : mail})

def delete(request):
    mail_id = request.POST['id']
    Mail.objects.get(id=mail_id).delete()
    return HttpResponseRedirect("/")

class DeleteMailView(generic.DeleteView):
    model = Mail
    template_name = 'mails/delete.html'
    success_url = "/"

class UpdateMailView(generic.UpdateView):
    model = Mail
    fields = ['due']
    success_url = "/"

class ErrorView(generic.TemplateView):
    template_name = 'mails/error.html'
