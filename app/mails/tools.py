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
import logging
import os
import re


logger = logging.getLogger('mails')
host   = re.sub('https://', '', settings.SITE_URL)

def get_delay_days_from_email_address(email_address):
    '''Gets the delay days from an email address

    :param  email_address: delay email address
    :type   email_address: str
    :rtype                 int
    '''
    try:
        match = re.findall('^(\d+)([dmw])', email_address)[0]
        multiplicator = settings.EMAIL_SUFFIX_TO_DAY[match[1]]
        delay = int(match[0]) * int(multiplicator)
        return delay
    except:
        raise Exception('Invalid delay')

def get_delay_address_from_recipients(recipients):
    '''Gets the delay days from a set of recipients

    :param  recipients: dict of recipients
    :type   recipients: dict
    :rtype:             int
    '''
    for recipient in recipients:
        if re.search('^(\d+[dmw])', recipient):
            return recipient

    raise Exception('Could not find a delay address')

def get_key_from_email_address(email_address):
    '''Get the key of an email address'''
    try:
        return re.search(
            '^\d+[dmw]\.([0-9a-z]{10})@',
            email_address
        ).group(1)
    except AttributeError:
        return None

def send_registration_mail(recipient):
    '''Sends an error mail to not registred users and logs it

    :param  recipient: the email address of the recipient
    :type   recipient: str
    '''
    from mails.models import AddressLog

    try:
        AddressLog.objects.get(email=recipient, reason='NREG')
    except:
        tpl = get_template('mails/messages/not_registered_mail.txt')

        subject = 'Register at %s!' % host
        content = tpl.render(
            Context({
                'recipient' : recipient,
                'url'       : settings.SITE_URL,
                'host'      : host
            })
        )

        msg = EmailMessage(
            subject,
            content,
            settings.EMAIL_HOST_USER,
            [recipient]
        )

        msg.send()

        log_entry = AddressLog(
            email=recipient,
            reason='NREG',
            attempt=1
        )
        log_entry.save()

def send_wrong_recipient_mail(recipient):
    '''Sends an error mail to not registred users

    :param  recipient: the email address of the recipient
    :type   recipient: str
    '''
    from mails.models import AddressLog

    try:
        AddressLog.objects.get(email=recipient)
    except:
        tpl     = get_template('mails/messages/wrong_recipient_mail.txt')

        subject = 'Your mail on %s was deleted!' % host
        content = tpl.render(
            Context({
                'recipient' : recipient,
                'host'      : host
            })
        )
        msg = EmailMessage(
            subject,
            content,
            settings.EMAIL_HOST_USER,
            [recipient]
        )

        msg.send()


def send_activation_mail(key, recipient):
    '''Sends an activation mail for additional addresses

    :param  key:       the activation key
    :type   key:       str
    :param  recipient: the email address of the recipient
    :type   recipient: str
    '''
    from mails.models import AddressLog

    subject = 'Activate your address on %s' % host
    tpl     = get_template('mails/messages/activation_mail.txt')
    content = tpl.render(
        Context({
            'recipient' : recipient,
            'key'       : key,
            'host'      : host
        })
    )

    msg = EmailMessage(
        subject,
        content,
        settings.EMAIL_HOST_USER,
        [recipient]
    )

    try:
        log_entry = AddressLog.objects.get(
            email=recipient,
            reason='SPAM'
        )

        if log_entry.date < timezone.now() or log_entry.attempt > 5:
            logger.warning(
                'No registration email was sent. %s is blocked'
                % (recipient)
            )
            return

        else:

            log_entry.attempt += 1
            log_entry.date = timezone.now() + get_block_delay(
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

def get_block_delay(attempt):
    '''Gets the block delay by attempt

    :param  attempt: the attempt to get the delay for
    :type   attempt: int
    '''
    return settings.BLOCK_DELAYS.get(
        attempt,
        datetime.timedelta(7)
    )

def get_all_users_of_account(user):
    '''Gets all users of the current users account

    :param  user: the user
    :type   user: models.User
    :rtype        list
    '''
    return User.objects.filter(
            userprofile__account=user.get_account()
        ).order_by('-last_login')

def create_additional_user(email, request):
    '''Creates an additional user with the same password and identity

    :param  email:   the email address of the new user
    :type   email:   string
    :param  request: http request
    :type   request: HttpRequest
    '''
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

    send_activation_mail(
        recipient=email,
        key=base64.b16encode(new_user.username)
    )

def delete_log_entries(email):
    from mails.models import AddressLog

    try:
        user_log_entry = AddressLog.objects.filter(
            email=email
        )
        user_log_entry.delete()
    except:
        pass

def generate_key():
    '''Generates an unique user key

    :rtype: string
    '''
    return base64.b32encode(os.urandom(7))[:10].lower()
