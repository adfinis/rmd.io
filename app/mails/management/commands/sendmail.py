import email
import smtplib
from django.utils import timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from mails.models import Mail, Statistic
from mails.tools import Tools
from django.core.management.base import BaseCommand
from django.conf import settings
from django.template import Context
from django.template.loader import get_template


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.tools = Tools()
        self.smtp = smtplib.SMTP(settings.EMAIL_HOST)

    def handle(self, *args, **kwargs):
        try:
            self.smtp.starttls()
            self.smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            mails_to_send = Mail.objects.filter(due__lte=timezone.now())
        except:
            return

        for mail_to_send in mails_to_send:

            imap_mail_ids = self.tools.get_mail_by_db_id(mail_to_send.id)

            for mail_in_imap in imap_mail_ids:

                results, data = self.tools.imap.fetch(mail_in_imap, 'RFC822')
                raw_email = data[0][1]

                original_msg = email.message_from_string(raw_email)
                charset = original_msg.get_content_charset()
                recipients = mail_to_send.recipient_set
                tpl = get_template('mails/messages/mail_attachment.txt')
                text = tpl.render(
                    Context({
                        'recipients' : recipients
                    })
                )

                if original_msg.is_multipart():
                    add_text = MIMEText(text, 'plain', 'utf-8')
                    if original_msg.get_content_maintype == 'multipart/signed':
                        # If it's a signed message, only take first payload
                        msg = MIMEMultipart()
                        orig = original_msg.get_payload(0)
                        msg.attach(orig)
                        msg.attach(add_text)
                    else:
                        msg = MIMEMultipart()
                        msg.attach(original_msg)
                        msg.attach(add_text)

                else:
                    msg = MIMEText(
                        '\n\n'.join((original_msg.get_payload(), str(text))),
                        'plain',
                        charset
                    )

                try:
                    msg['Subject'] = "Reminder from %s: %s" % (
                        mail_to_send.sent.strftime('%b %d %H:%M'),
                        mail_to_send.subject
                    )
                    msg['From'] = settings.EMAIL_HOST_USER
                    msg['To'] = mail_to_send.user.email
                    msg['Date'] = email.utils.formatdate(localtime=True)
                    msg['References'] = original_msg['Message-ID']
                except:
                    self.tools.delete_email(mail_to_send.id)
                    print('Failed to write new header')
                    break

                self.smtp.sendmail(
                    settings.EMAIL_HOST_USER,
                    mail_to_send.user.email,
                    str(msg)
                )
                l = Statistic(
                    type='SENT',
                    date=timezone.now()
                )
                l.save()

            self.tools.delete_email(mail_to_send.id)
            mail_to_send.delete()

        self.smtp.quit()
        self.tools.imap.logout()
