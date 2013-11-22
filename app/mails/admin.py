from django.contrib import admin
from mails.models import Mail

class MailAdmin(admin.ModelAdmin):
    fieldsets = (
        (None,                {'fields' : ['subject', 'sent_from']}),
        ('Date Informations', {'fields' : ['sent', 'due'],
                               'classes': ['collapse']
                              }
        ),
    )
    list_display = ('subject', 'sent_from', 'sent', 'due')
    list_filter = ['due']
    search_fields = ['subject']

admin.site.register(Mail, MailAdmin)