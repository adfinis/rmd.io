import email
import email.utils
import email.header
import imaplib
import smtplib
import time
import datetime
from django.utils import timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from mails.models import Mail
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        email_address = settings.EMAIL_ADDRESS
        email_password = settings.EMAIL_PASSWORD
        email_server = settings.EMAIL_SERVER
        mailbox = settings.MAILBOX

        try:
            smtp = smtplib.SMTP(email_server)
            smtp.starttls()
            smtp.login(email_address, email_password)
        except Exception, e:
            print "Connection to SMTP-Server failed: %s" % repr(e)

        try:
            imap = imaplib.IMAP4_SSL(email_server)
            imap.login(email_address, email_password)
            imap.select(mailbox)
        except Exception, e:
            print "Connection to IMAP4-Server failed: %s" % repr(e)

        parser = email.Parser.Parser()

        def mails_with_id(mail_id):
            results, data = imap.search(None, '(KEYWORD "MAILDELAY-%d")' % mail_id)
            ids = data[0]
            return ids.split()

        def parsedate(datestr):
            dt_tuple = email.utils.parsedate(datestr)
            timestamp = time.mktime(dt_tuple)
            dt = datetime.datetime.fromtimestamp(timestamp)
            return dt

        def count_days(mail_to_send):
            days = (mail_to_send.due - mail_to_send.sent).days
            print days
            return days

        mails_to_send = Mail.objects.filter(due__lte=timezone.now())

        for mail_to_send in mails_to_send:
            imap_mail_ids = mails_with_id(mail_to_send.id)

            for mail_in_imap in imap_mail_ids:
                results, data = imap.fetch(mail_in_imap, 'RFC822')
                raw_email = data[0][1]
                msg = parser.parsestr(raw_email)
                days = count_days(mail_to_send)

                if msg.is_multipart():
                    msg = msg.get_payload(0)
                else:
                    msg = MIMEText(msg.get_payload())

                try:
                    if days == '1':
                        msg['Subject'] = "Reminder after %s day: %s" % (days, mail_to_send.subject)
                    else:
                        msg['Subject'] = "Reminder after %s days: %s" % (days, mail_to_send.subject)
                    msg['From'] = email_address
                    msg['To'] = mail_to_send.sent_from
                except:
                    print "failed to write new header"

                smtp.sendmail(email_address, mail_to_send.sent_from, msg.as_string())
                imap.store(mail_in_imap, '+FLAGS', '\\Deleted')
                mail_to_send.delete()

        imap.expunge()

        smtp.quit()
