from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import get_template
from django.utils.encoding import smart_bytes
from django.utils import timezone
from hashlib import sha1
import base64
import datetime
import email.header
import email.utils
import imaplib
import logging
import pytz
import os
import re


class Tools():

    def __init__(self):
        self.email_folder = settings.EMAIL_FOLDER
        self.email_host   = settings.EMAIL_HOST
        self.email_pass   = settings.EMAIL_HOST_PASSWORD
        self.email_user   = settings.EMAIL_HOST_USER
        self.logger       = logging.getLogger('mails')
        self.url          = settings.SITE_URL
        self.host         = re.sub('https://', '', self.url)
        self.imap         = self.imap_login()

        self.recipient_headers = [
            'To',
            'Cc',
            'X-Original-To'
        ]

        self.multiplicate_number_with = {
            'd' : 1,
            'w' : 7,
            'm' : 30,
        }

        self.block_delays = {
            1 : datetime.timedelta(minutes=10),
            2 : datetime.timedelta(hours=1),
            3 : datetime.timedelta(1),
            4 : datetime.timedelta(3),
            5 : datetime.timedelta(7)
        }

    def imap_login(self):
        """Connects to IMAP server

        :rtype: imaplib.IMAP4_SSL
        """
        try:
            imap = imaplib.IMAP4_SSL(self.email_host)
            imap.login(self.email_user, self.email_pass)
            imap.select(self.email_folder)

            return imap
        except:
            self.logger.warning('Failed to login to IMAP server, aborting.')

    def parse_date_from_string(self, datestr):
        """Parses datestrings to datetime objects

        :param  datestr: date to parse as string
        :type   datestr: str
        :rtype:          datetime.datetime
        """
        dt_tuple  = email.utils.parsedate_tz(datestr)
        timestamp = email.utils.mktime_tz(dt_tuple)
        dt        = datetime.datetime.utcfromtimestamp(timestamp)

        return dt.replace(tzinfo=pytz.utc)

    def get_recipients_from_message(self, msg):
        """Parses recipients from message

        :param  msg: field type of field_string
        :type   msg: email.message.Message
        :rtype:      dict
        """
        recipients = {}

        for key in self.recipient_headers:
            try:
                recipient_list = email.utils.getaddresses(msg.get_all(key, []))
                for recipient in recipient_list:
                    if not recipient[1] in recipients:
                        recipients[recipient[1]] = {
                            'name'  : recipient[0],
                            'email' : recipient[1]
                        }
                    else:
                        continue
            except:
                raise Exception('Could not find any recipients')

        return recipients

    def get_sender_from_message(self, msg):
        """Parses sender from message

        :param  msg: field type of field_string
        :type   msg: email.message.Message
        :rtype:      string
        """
        try:
            return email.utils.getaddresses(msg.get_all('From', []))[0][1]
        except:
            raise Exception('Could not find a sender')

    def get_mail_by_db_id(self, mail_id):
        """Gets an imap mail by its database id

        :param  mail_id: database id of the mail
        :type   mail_id: int
        :rtype           list
        """
        results, data = self.imap.search(
            None,
            '(KEYWORD "MAILDELAY-%d")' % mail_id
        )
        ids = data[0].split()

        return ids

    def fix_header_encoding(self, headerpair):
        """Fixes encodings of a header

        :param  headerpair: headerpair to fix encoding
        :type   headerpair: tupel
        :rtype              str
        """
        if headerpair[1] is not None:
            return headerpair[0].decode(headerpair[1])

        return headerpair[0]

    def get_delay_days_from_email_address(self, email_address):
        """Gets the delay days from an email address

        :param  email_address: delay email address
        :type   email_address: str
        :rtype                 int
        """
        try:
            match = re.search('^(\d+)([dmw])', email_address).group()
            multiplicator = self.multiplicate_number_with[match[1]]
            delay = int(match[0]) * int(multiplicator)
            return delay
        except:
            raise Exception('Invalid delay')

    def get_delay_address_from_recipients(self, recipients):
        """Gets the delay days from a set of recipients

        :param  recipients: dict of recipients
        :type   recipients: dict
        :rtype:             int
        """
        for recipient in recipients:
            if re.search('^(\d+[dmw])', recipient):
                return recipient

        raise Exception('Could not find a delay address')

    def get_sent_date_from_message(self, msg):
        """Gets the sent date from a message

        :param  msg: message to parse
        :type   msg: email.message.Message
        :rtype:      datetime.datetime
        """
        try:
            return self.parse_date_from_string(msg['date'])
        except:
            raise Exception('Could not parse sent date')

    def get_key_from_email_address(self, email_address):
        """Get the key of an email address"""
        try:
            return re.search(
                '^\d+[dmw]\.([0-9a-z]{10})@',
                email_address
            ).group()
        except AttributeError:
            return None

    def get_subject_from_message(self, msg):
        """Gets the subject of a message

        :param  msg: message to parse
        :type   msg: email.message.Message
        :rtype:      str
        """
        try:
            subjects_raw = email.header.decode_header(msg['Subject'])

            header_texts = [
                self.fix_header_encoding(hdr)
                for hdr
                in subjects_raw
            ]

            subject = " ".join(header_texts)
            subject = re.sub(r'[\r\n]+[\t]*', '', subject)

            return subject

        except:
            raise Exception('Failed to parse subject')

    def delete_email(self, mail_id):
        """Deletes an email in imap

        :param  mail_id: database id of the mail to delete
        :type   mail_id: int
        """
        results, data = self.imap.search(
            None,
            '(KEYWORD "MAILDELAY-{0}")'.format(mail_id)
        )
        for imap_mail_id in data[0].split():
            self.imap.store(imap_mail_id, '+FLAGS', '\\Deleted')
        self.imap.expunge()

    def send_registration_mail(self, recipient):
        """Sends an error mail to not registred users and logs it

        :param  recipient: the email address of the recipient
        :type   recipient: str
        """
        from mails.models import AddressLog

        try:
            AddressLog.objects.get(email=recipient, reason='NREG')
            self.logger.warning(
                'No registration email was sent. %s is blocked'
                % (recipient)
            )
        except:
            tpl = get_template('mails/messages/not_registered_mail.txt')

            subject = 'Register at %s!' % self.host
            content = tpl.render(
                Context({
                    'recipient' : recipient,
                    'url'       : self.url,
                    'host'      : self.host
                })
            )

            msg = EmailMessage(
                subject,
                content,
                self.email_user,
                [recipient]
            )

            msg.send()

            log_entry = AddressLog(
                email=recipient,
                reason='NREG',
                attempt=1
            )
            log_entry.save()

    def send_wrong_recipient_mail(self, recipient):
        """Sends an error mail to not registred users

        :param  recipient: the email address of the recipient
        :type   recipient: str
        """
        from mails.models import AddressLog

        try:
            AddressLog.objects.get(email=recipient)
        except:
            tpl     = get_template('mails/messages/wrong_recipient_mail.txt')

            subject = 'Your mail on %s was deleted!' % self.host
            content = tpl.render(
                Context({
                    'recipient' : recipient,
                    'host'      : self.host
                })
            )
            msg = EmailMessage(
                subject,
                content,
                self.email_user,
                [recipient]
            )

            msg.send()

    def send_activation_mail(self, key, recipient):
        """Sends an activation mail for additional addresses

        :param  key:       the activation key
        :type   key:       str
        :param  recipient: the email address of the recipient
        :type   recipient: str
        """
        from mails.models import AddressLog

        subject = 'Activate your address on %s' % self.host
        tpl     = get_template('mails/messages/activation_mail.txt')
        content = tpl.render(
            Context({
                'recipient' : recipient,
                'key'       : key,
                'host'      : self.host
            })
        )

        msg = EmailMessage(
            subject,
            content,
            self.email_user,
            [recipient]
        )

        try:
            log_entry = AddressLog.objects.get(
                email=recipient,
                reason='SPAM'
            )

            if log_entry.date < timezone.now() or log_entry.attempt > 5:
                self.logger.warning(
                    'No registration email was sent. %s is blocked'
                    % (recipient)
                )
                return

            else:

                log_entry.attempt += 1
                log_entry.date = timezone.now() + self.get_block_delay(
                    log_entry.attempt
                )
                log_entry.save()

            msg.send()

        except:
            msg.send()

            log_entry = AddressLog(
                email=recipient,
                reason='SPAM',
                attempt=0,
                date=timezone.now()
            )
            log_entry.save()

    def get_block_delay(self, attempt):
        """Gets the block delay by attempt

        :param  attempt: the attempt to get the delay for
        :type   attempt: int
        """
        return self.block_delays.get(
            attempt,
            datetime.timedelta(7)
        )

    def save_mail(
        self,
        subject,
        recipients,
        user,
        sent_date,
        delay_address,
        due_date,
        email_id
    ):
        """Saves an email in database and logs statistics

        :param  subject:       the subject of the email
        :type   subject:       string
        :param  recipients:    the recipients of the email
        :type   recipients:    set
        :param  user:          the user of the email
        :type   user:          django.auth.models.User
        :param  sent_date:     the date, when the email was sent
        :type   sent_date:     datetime.datetime
        :param  delay_address: the delay address of the email
        :type   delay_address: string
        :param  due_date:      the date on which the email will be sent back
        :type   due_date:      datetime.datetime
        :param  email_id:      the imap id of the email
        :type   email_id:      int
        """
        from mails.models import Mail, Statistic, Recipient

        try:
            mail = Mail(
                subject=subject,
                sent=sent_date,
                due=due_date,
                user=user,
            )
            rec_stat = Statistic(
                type='REC',
                email=delay_address
            )
            user_stat = Statistic(
                type='USER',
                email=user.email,
            )
            mail.save()
            rec_stat.save()
            user_stat.save()

            for i in recipients:
                recipient = Recipient(
                    mail=mail,
                    email=recipients[i]['email'],
                    name=recipients[i]['name']
                )
                recipient.save()
                if recipients[i]['email'] != delay_address:
                    obl_stat = Statistic(
                        type='OBL',
                        email=recipients[i]['email']
                    )
                    obl_stat.save()
                else:
                    continue

            self.imap.store(email_id, '+FLAGS', "MAILDELAY-%d" % mail.id)
            self.imap.store(email_id, '+FLAGS', '\\Flagged')

        except:
            self.delete_email_with_error(
                email_id,
                'Could not save mail',
                user.email
            )

    def get_all_users_of_account(self, user):
        """Gets all users of the current users account

        :param  user: the user
        :type   user: models.User
        :rtype        list
        """
        return User.objects.filter(
                userprofile__account=user.get_account()
            ).order_by('-last_login')

    def delete_email_with_error(self, email_id, reason, sender):
        """Deletes an email and logs an error message

        :param  msg: message to parse
        :type   msg: email.message.Message
        :rtype:      datetime.datetime
        """
        self.imap.store(email_id, '+FLAGS', '\\Deleted')
        self.logger.warning('Mail from %s deleted: %s' % (sender, reason))

    def create_additional_user(self, email, request):
        """Creates an additional user with the same password and identity

        :param  email:   the email address of the new user
        :type   email:   string
        :param  request: http request
        :type   request: HttpRequest
        """
        from mails.models import UserProfile, AddressLog

        new_user = User(
            email = email,
            username = base64.urlsafe_b64encode(
                sha1(smart_bytes(email)).digest()
            ).rstrip(b'='),
            date_joined = timezone.now(),
            password = request.user.password,
            is_active = False
        )
        new_user.save()

        account = request.user.get_account()
        user_profile = UserProfile(
            user=new_user,
            account=account
        )

        user_profile.save()

        try:
            user_log_entry = AddressLog.objects.filter(
                email=request.user.email
            )
            user_log_entry.delete()
        except:
            pass

        self.send_activation_mail(
            recipient=email,
            key=base64.b16encode(new_user.username)
        )

    def delete_log_entries(self, email):
        from mails.models import AddressLog

        try:
            user_log_entry = AddressLog.objects.filter(
                email=email
            )
            user_log_entry.delete()
        except:
            pass

    def generate_key(self):
        """Generates an unique user key

        :rtype: string
        """
        return base64.b32encode(os.urandom(7))[:10].lower()
