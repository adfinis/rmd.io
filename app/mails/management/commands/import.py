import re
import email
from django.contrib.auth.models import User
from mails.models import Mail, UserKey, LastImport
from mails import tools
from django.utils import timezone
import datetime
from lockfile import FileLock
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def import_mail(self, mail, imap):
        parser = email.Parser.Parser()

        results, data = imap.fetch(mail, 'RFC822')
        raw_email = data[0][1]
        msg = parser.parsestr(raw_email)
        try:
            sent_from = re.sub(r'([<>])', '', msg['return-path'])
            sent_to = tools.recipients_from_message(msg)
            subject = tools.subject_from_message(msg)
            sent = tools.parsedate(msg['date'])
            delay = tools.delay_days_from_message(msg)
            due = sent + datetime.timedelta(delay)
        except TypeError:
            # invalid email with wrong header.
            # TODO: log error
            reason = 'Wrong header'
            tools.delete_mail_with_error(
                mail,
                reason,
                sent_from,
                imap
            )
            return

        try:
            user = User.objects.get(
                email=sent_from,
                is_active=True
            )
        except:
            # No user with this email address found - deleting
            reason = 'User not registred'
            tools.delete_mail_with_error(
                mail,
                reason,
                sent_from,
                imap
            )
            tools.send_registration_mail(
                subject = subject,
                sender = sent_from,
            )
            return

        if user.settings.anti_spam:
            # If anti-spam is activated
            user_key = UserKey.get_userkey(user)
            try:
                mail_key = tools.key_from_message(msg)
                if mail_key == user_key:
                    m = Mail(
                        subject=subject,
                        sent=sent,
                        due=due,
                        sent_from=sent_from,
                        sent_to=sent_to
                    )
                    m.save()
                    imap.store(mail, '+FLAGS', "MAILDELAY-%d" % m.id)
                    imap.store(mail, '+FLAGS', '\\Flagged')
                else:
                    # User key not equivalent with mail key
                    reason = 'Wrong key'
                    tools.delete_mail_with_error(
                        mail,
                        reason,
                        sent_from,
                        imap
                    )
            except:
                # Anti-Spam activated but wrong recipient
                reason = 'Wrong recipient'
                tools.delete_mail_with_error(
                    mail,
                    reason,
                    sent_from,
                    imap
                )
                tools.send_error_mail(
                    subject = subject,
                    sender = sent_from,
                )

        else:
            # If anti-spam isn't activated
            m = Mail(
                subject=subject,
                sent=sent,
                due=due,
                sent_from=sent_from,
                sent_to=sent_to
            )
            m.save()
            imap.store(mail, '+FLAGS', "MAILDELAY-%d" % m.id)
            imap.store(mail, '+FLAGS', '\\Flagged')

    def handle(self, *args, **kwargs):

        lock = FileLock('/tmp/lockfile.tmp')
        with lock:
            try:
                imap = tools.imap_login()
                results, data = imap.search(None, 'UNFLAGGED')
                ids = data[0]
                mails = ids.split()
            except:
                return

            try:
                last_import = LastImport.objects.get(id=1)
            except:
                last_import = LastImport(date=timezone.now())
                last_import.save()

            import_diff = timezone.now() - last_import.date

            if import_diff > datetime.timedelta(seconds=10):
                last_import.date = datetime.datetime.now()
                last_import.save()
            else:
                return

            for mail in mails:
                self.import_mail(mail, imap)

            imap.expunge()
            imap.logout()
