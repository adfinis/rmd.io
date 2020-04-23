from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from mails.models import Mail, Statistic, Recipient, Due
from lockfile import FileLock
from mails import imaphelper, tools
from mails.models import ImportLog
import datetime
import logging
import re

logger = logging.getLogger("mails")


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.imported_mail_ids = []

    def import_mail(self, message):

        if message.msg["Message-ID"] in self.imported_mail_ids:
            message.delete()
            return

        sender = "<unknown>"

        try:
            sender = message.get_sender()
            recipients = message.get_recipients()
            subject = message.get_subject()
            sent_date = message.get_sent_date()
            delay_addresses = tools.get_delay_addresses_from_recipients(recipients)
            keys = [tools.get_key_from_email_address(x) for x in delay_addresses]
        except Exception as e:
            message.delete()
            logger.error(
                "Mail from %s deleted: Failed to parse header, %s" % (sender, e.args[0])
            )

            return

        try:
            user = User.objects.get(email=sender, is_active=True)
            account = user.get_account()
        except:
            message.delete()
            logger.error("Mail from %s deleted: User not registered" % sender)
            tools.send_registration_mail(sender)

            return

        if message_deleted_due_to_invalid_keys(
            keys=keys, sender=sender, message=message, account=account
        ):
            return

        try:
            mail = Mail(subject=subject, sent=sent_date, user=user)
            mail.save()

            save_received_statistic(
                delay_addresses=delay_addresses, mail=mail, sent_date=sent_date
            )

            user_stat = Statistic(type="USER", email=user.email,)
            user_stat.save()

            save_oblivious_statistic(
                recipients=recipients, mail=mail, delay_addresses=delay_addresses
            )

            message.flag(mail.id)
            self.imported_mail_ids.append(message.msg["Message-ID"])
        except Exception as e:
            message.delete()
            logger.error("Mail from %s deleted: Could not save mail" % sender)
            logger.error(e)

            return

    def handle(self, *args, **kwargs):

        lock = FileLock("/tmp/lockfile.tmp")
        with lock:

            last_import, created = ImportLog.objects.get_or_create()
            import_diff = timezone.now() - last_import.date

            if import_diff > datetime.timedelta(seconds=30):
                last_import.save()
            else:
                return

            imap_conn = imaphelper.get_connection()
            messages = imaphelper.get_unflagged(imap_conn)

            for message in messages:
                self.import_mail(message)

            imap_conn.expunge()


def message_deleted_due_to_invalid_keys(keys, sender, message, account):
    if account.anti_spam:
        if not len(keys):
            message.delete()
            logger.error("Mail from %s deleted: No key" % sender)
            tools.send_wrong_recipient_mail(sender)
            return
    elif not any(key == account.key for key in keys):
        message.delete()
        logger.error("Mail from %s deleted: Wrong key" % sender)
        return


def save_received_statistic(delay_addresses, mail, sent_date):
    for delay_address in delay_addresses:
        rec_stat = Statistic(
            type="REC",
            email=re.sub(r"(^\d+[dmw])(\.[0-9a-z]{10})", r"\1", delay_address),
        )
        due = Due(
            mail=mail,
            due=sent_date
            + datetime.timedelta(
                tools.get_delay_days_from_email_address(delay_address)
            ),
        )
        due.save()
        rec_stat.save()


def save_oblivious_statistic(recipients, mail, delay_addresses):
    for rec in recipients:
        recipient = Recipient(mail=mail, email=rec["email"], name=rec["name"])
        recipient.save()
        if rec["email"] not in delay_addresses:
            obl_stat = Statistic(type="OBL", email=rec["email"])
            obl_stat.save()
