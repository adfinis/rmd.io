import email
from django.contrib.auth.models import User
from mails.models import ImportLog
from mails.tools import Tools
from django.utils import timezone
import datetime
from lockfile import FileLock
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.tools = Tools()

    def import_mail(self, email_id):

        results, data = self.tools.imap.fetch(email_id, 'RFC822')
        raw_email     = data[0][1]
        msg           = email.message_from_string(raw_email)

        try:
            sender        = self.tools.get_sender_from_message(msg)
            recipients    = self.tools.get_recipients_from_message(msg)
            subject       = self.tools.get_subject_from_message(msg)
            sent_date     = self.tools.get_sent_date_from_message(msg)
            key           = self.tools.get_key_from_email_address(sender)
            delay_address = self.tools.get_delay_address_from_recipients(
                recipients
            )
            due_date      = sent_date + datetime.timedelta(
                self.tools.get_delay_days_from_email_address(delay_address)
            )
        except Exception as e:
            self.tools.delete_email_with_error(
                email_id,
                e.args[0],
                sender
            )
            return

        try:
            user = User.objects.get(
                email=sender,
                is_active=True
            )
            account = user.get_account()
        except:
            self.tools.delete_email_with_error(
                email_id,
                'User not registered',
                sender
            )
            self.tools.send_registration_mail(sender)

            return

        if account.anti_spam:
            if not key:
                self.tools.delete_email_with_error(
                    email_id,
                    'No key',
                    sender
                )
                self.tools.send_wrong_recipient_mail(sender)

                return
            elif key != account.key:
                self.tools.delete_email_with_error(
                    email_id,
                    'Wrong key',
                    sender,
                )

                return

        self.tools.save_mail(
            subject,
            recipients,
            user,
            sent_date,
            delay_address,
            due_date,
            email_id
        )

    def get_email_ids(self):
        results, data = self.tools.imap.search(None, 'UNFLAGGED')
        ids = data[0].split()

        return ids

    def handle(self, *args, **kwargs):

        lock = FileLock('/tmp/lockfile.tmp')
        with lock:

            last_import, created = ImportLog.objects.get_or_create()
            import_diff = timezone.now() - last_import.date

            if import_diff > datetime.timedelta(seconds=30):
                last_import.save()
            else:
                return

            email_ids = self.get_email_ids()

            for email_id in email_ids:
                self.import_mail(email_id)

            self.tools.imap.expunge()
