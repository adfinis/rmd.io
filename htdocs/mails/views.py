from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.views import generic
from mails.models import Mail

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
