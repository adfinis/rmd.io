import email
from django.utils import timezone
from email.mime.text import MIMEText
from mails.models import Mail
from mails import tools
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        imap = tools.imap_login()
        smtp = tools.smtp_login()

        parser = email.Parser.Parser()
        mails_to_send = Mail.objects.filter(due__lte=timezone.now())

        for mail_to_send in mails_to_send:

            imap_mail_ids = tools.mails_with_id(mail_to_send.id, imap)

            for mail_in_imap in imap_mail_ids:

                results, data = imap.fetch(mail_in_imap, 'RFC822')
                raw_email = data[0][1]
                msg = parser.parsestr(raw_email)

                if msg.is_multipart():
                    msg = msg.get_payload(0)
                else:
                    msg = MIMEText(msg.get_payload())

                try:
                    msg['Subject'] = "Reminder from %s: %s" % (
                        mail_to_send.sent.strftime('%b %d %H:%M'),
                        mail_to_send.subject
                    )
                    msg['From'] = settings.EMAIL_ADDRESS
                    msg['To'] = mail_to_send.sent_from
                    msg['Date'] = email.utils.formatdate(localtime=True)
                except:
                    print('Failed to write new header')
                    break

                smtp.sendmail(
                    settings.EMAIL_ADDRESS,
                    mail_to_send.sent_from,
                    msg.as_string()
                )
                tools.delete_imap_mail(mail_in_imap)

            mail_to_send.delete()

        smtp.quit()
