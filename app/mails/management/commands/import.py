import re
import email
from django.contrib.auth.models import User
from mails.models import Mail, AdditionalAddresses
from mails import tools
import datetime
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
<<<<<<< Updated upstream
            imap.store(mail, '+FLAGS', '\\Deleted')
=======
            reason = 'Wrong header'
            tools.delete_mail_with_error(
                mail,
                reason,
                sent_from
            )
>>>>>>> Stashed changes
            return
        try:
            user = User.objects.get(email=sent_from)
        except:
            try:
                # If mail sent from an additional address
                user = AdditionalAddresses.objects.get(
                    address = sent_from,
                    is_activated = True
                ).user
            except:
                # No user with this email address found - deleting
                reason = 'User not registred'
                tools.delete_mail_with_error(
                    mail,
                    reason,
                    sent_from
                )
                tools.send_error_mail(
                    subject = subject,
                    sender = sent_from
                )
                return

        if user.settings.anti_spam:
            # If anti-spam is activated
            user_key = user.userkey.key
            try:
                mail_key = tools.key_from_message(msg)
                if mail_key == user_key.key:
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
                        sent_from
                    )
                    return
            except:
                # Anti-Spam activated but wrong recipient
                reason = 'Wrong recipient'
                tools.delete_mail_with_error(
                    mail,
                    reason,
                    sent_from
                )
                return

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

        imap = tools.imap_login()
        results, data = imap.search(None, 'UNFLAGGED')
        ids = data[0]
        mails = ids.split()

        for mail in mails:
            self.import_mail(mail, imap)

        imap.expunge()
