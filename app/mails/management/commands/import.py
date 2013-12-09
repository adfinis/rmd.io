import re
import email
from django.contrib.auth.models import User
from django.utils import timezone
from mails.models import Mail, UserKey
from mails import tools
import datetime
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        imap = tools.imap_login()

        results, data = imap.search(None, 'UNFLAGGED')
        ids = data[0]
        mails = ids.split()

        parser = email.Parser.Parser()

        for mail in mails:
            results, data = imap.fetch(mail, 'RFC822')
            raw_email = data[0][1]
            msg = parser.parsestr(raw_email)
            try:
                sent_from = msg['return-path']
                sent_from = re.sub(r'([<>])', '', sent_from)
                subject = tools.subject_from_message(msg)
                sent = tools.parsedate(msg['date'])
                days = tools.delay_days_from_message(msg)
                due = sent + datetime.timedelta(days)
            except TypeError:
                # invalid email with no date header.
                # TODO: log error, delete mail
                continue

            try:
                user = User.objects.get(email=sent_from)
                user_key = UserKey.get_user_key(user)
                mail_key = tools.key_from_message(msg)

                if mail_key == user_key.key:
                    m = Mail(subject=subject, sent=sent, due=due, sent_from=sent_from)
                    m.save()
                    imap.store(mail, '+FLAGS', "MAILDELAY-%d" % m.id)
                    imap.store(mail, '+FLAGS', '\\Flagged')

                else:
                    imap.store(mail, '+FLAGS', '\\Deleted')
                    print "Mail from %s deleted: wrong recipient" % sent_from
                    continue

            except:
                imap.store(mail, '+FLAGS', '\\Deleted')
                print "%s: User not registered! Mail deleted." % sent_from
                continue

        imap.expunge()
