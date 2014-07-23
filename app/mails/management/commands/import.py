import re
import email
from django.contrib.auth.models import User
from mails.models import LastImport, UserIdentity
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
            sent_from = re.sub(r'([<>])', '', msg['return-path']).lower()
            sent_to = tools.recipients_from_message(msg).lower()
            subject = tools.subject_from_message(msg)
            sent = tools.parsedate(msg['date'])
            delay = tools.delay_days_from_message(msg)
            due = sent + datetime.timedelta(delay)
            delay_address = tools.get_delay_address(msg)
            recipients = tools.recipients_email_from_message(msg)
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
            identity = UserIdentity.objects.get(user=user).identity
        except:
            # No user with this email address found - deleting
            reason = 'User not registred'
            tools.delete_mail_with_error(
                mail,
                reason,
                sent_from,
                imap
            )
            tools.send_registration_mail(sent_from)

            return

        if identity.anti_spam:
            # If anti-spam is activated
            try:
                mail_key = tools.key_from_message(msg)
                if mail_key == identity.key:
                    tools.save_mail(
                        subject,
                        sent_to,
                        sent_from,
                        delay_address,
                        due,
                        sent,
                        imap,
                        mail,
                        recipients
                    )
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
                tools.delete_mail_with_error(
                    mail,
                    reason,
                    sent_from,
                    imap
                )
                tools.send_wrong_recipient_mail(sent_from)

        else:
            # If anti-spam isn't activated
            tools.save_mail(
                subject,
                sent_to,
                sent_from,
                delay_address,
                due,
                sent,
                imap,
                mail,
                recipients
            )

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
