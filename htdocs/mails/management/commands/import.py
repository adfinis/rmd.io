import email
import re
import datetime
import time
import email.utils
import email.header
import imaplib
import smtplib
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from mails.models import Mail
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

        results, data = imap.search(None, 'UNFLAGGED')
        ids = data[0]
        mails = ids.split()
        parser = email.Parser.Parser()

        mailbox_to_days = {
            '1d' : 1,
            '2d' : 2,
            '3d' : 3,
            '4d' : 4,
            '5d' : 5,
            '6d' : 6,
            '1w' : 7,
            '2w' : 14,
            '3w' : 21,
            '4w' : 28,
        }

        recipient_headers = [
            'X-Original-To',
            'To'
        ]

        def parsedate(datestr):
            dt_tuple = email.utils.parsedate(datestr)
            timestamp = time.mktime(dt_tuple)
            dt = datetime.datetime.fromtimestamp(timestamp)
            return dt


        def fix_pair(headerpair):
            if headerpair[1] is not None:
                return headerpair[0].decode(headerpair[1])
            return headerpair[0]

        def delay_days_from_message(msg):
            for key in recipient_headers:
                if key not in msg:
                    continue
                else:
                    mailaddress = msg[key]
                    if "@" in mailaddress:
                        address = re.findall("([\da-z]+)@", mailaddress)
                        if len(address) == 0:
                            continue
                        mailbox_key = address[0]
                        if mailbox_key not in mailbox_to_days:
                            continue
                        return mailbox_to_days[mailbox_key]

        for mail in mails:
            results, data = imap.fetch(mail, 'RFC822')
            raw_email = data[0][1]
            msg = parser.parsestr(raw_email)
            subject = msg['subject']
            subj_headers = email.header.decode_header(subject)
            sent_from = msg['return-path']
            sent_from = re.sub(r'([<>])', '', sent_from)
            days = delay_days_from_message(msg)

            header_texts = [
                fix_pair(hdr)
                for hdr
                in subj_headers
            ]

            subject = " ".join(header_texts)
            subject = re.sub(r'[\r\n]+[\t]*', '', subject)

            try:
                sent = parsedate(msg['date'])
                due = sent + datetime.timedelta(delay_days_from_message(msg))
            except TypeError:
                # invalid email with no date header.
                # TODO: log error, delete mail
                continue
            user_count = User.objects.filter(email=sent_from).count()
            if user_count != 1:
                imap.store(mail, '+FLAGS', '\\Deleted')
                print "%s: User not registered! Mail deleted." % sent_from
                continue
            else:
                m = Mail(subject=subject, sent=sent, due=due, sent_from=sent_from, days=days)
                m.save()
                imap.store(mail, '+FLAGS', "MAILDELAY-%d" % m.id)
                imap.store(mail, '+FLAGS', '\\Flagged')

        imap.expunge()
