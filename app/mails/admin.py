from django.contrib import admin
from mails.models import Mail


class MailAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ["subject", "user"]}),
        ("Date Informations", {"fields": ["sent"], "classes": ["collapse"]}),
    )
    list_display = ("subject", "user", "sent")
    search_fields = ["subject"]


admin.site.register(Mail, MailAdmin)
