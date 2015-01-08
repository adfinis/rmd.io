import email
import smtplib
from django.utils import timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from mails.models import Mail, Statistic
from mails import imaphelper
from django.core.management.base import BaseCommand
from django.conf import settings
from django.template import Context
from django.template.loader import get_template


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        try:
            smtp = smtplib.SMTP(settings.EMAIL_HOST)
            smtp.starttls()
            smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        except:
            return

        mails = Mail.objects.filter(due__lte=timezone.now())

        for mail in mails:

            imap_conn = imaphelper.get_connection()
            message = imaphelper.IMAPMessage.from_dbid(mail.id, imap_conn)

            charset = message.msg.get_content_charset()
            recipients = mail.recipient_set
            tpl = get_template('mails/messages/mail_attachment.txt')
            text = tpl.render(
                Context({
                    'recipients' : recipients
                })
            )

            if message.msg.is_multipart():
                add_text = MIMEText(text, 'plain', 'utf-8')
                if message.msg.get_content_maintype == 'multipart/signed':
                    # If it's a signed message, only take first payload
                    msg = MIMEMultipart()
                    orig = message.msg.get_payload(0)
                    msg.attach(orig)
                    msg.attach(add_text)
                else:
                    msg = MIMEMultipart()
                    msg.attach(message.msg)
                    msg.attach(add_text)

            else:
                msg = MIMEText(
                    '\n\n'.join((message.msg.get_payload(), str(text))),
                    'plain',
                    charset
                )

            try:
                msg['Subject'] = "Reminder from %s: %s" % (
                    mail.sent.strftime('%b %d %H:%M'),
                    mail.subject
                )
                msg['From'] = settings.EMAIL_HOST_USER
                msg['To'] = mail.user.email
                msg['Date'] = email.utils.formatdate(localtime=True)
                msg['References'] = message.msg['Message-ID']
            except:
                message.delete()
                print('Failed to write new header')
                break

            smtp.sendmail(
                settings.EMAIL_HOST_USER,
                mail.user.email,
                str(msg)
            )
            l = Statistic(
                type='SENT',
                date=timezone.now()
            )
            l.save()

            message.delete()
            mail.delete()

        smtp.quit()
