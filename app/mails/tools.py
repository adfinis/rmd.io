import email.utils
import email.header
import imaplib
import time
import re
import base64
import datetime
from django.conf import settings
from django.template.loader import get_template
from django.template import Context
from django.utils import timezone
from hashlib import sha1
from django.contrib.auth.models import User
from django.utils.encoding import smart_bytes
from django.core.mail import EmailMessage

# Hostname
host = re.sub('https://', '', settings.SITE_URL)

# Default email from address
email_from = settings.EMAIL_HOST_USER

# Recipient header keys
recipient_headers = [
    'X-Original-To',
    'To'
]

# Character / days mapping
multiplicate_number_with = {
    'd' : 1,
    'w' : 7,
    'm' : 30,
}

# Log delay definitions
delays = {
    '1' : datetime.timedelta(minutes=10),
    '2' : datetime.timedelta(hours=1),
    '3' : datetime.timedelta(1),
    '4' : datetime.timedelta(3),
    '5' : datetime.timedelta(7)
}


def imap_login():
    # Connects to IMAP server
    try:
        imap = imaplib.IMAP4_SSL(settings.EMAIL_HOST)
        imap.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        imap.select(settings.FOLDER)
        return imap
    except:
        print('Failed to login to IMAP server, aborting.')


def parsedate(datestr):
    # Parses dates to datetime objects
    dt_tuple = email.utils.parsedate(datestr)
    timestamp = time.mktime(dt_tuple)
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt


def mails_with_id(mail_id, imap):
    # Gets a mail by id
    results, data = imap.search(None, '(KEYWORD "MAILDELAY-%d")' % mail_id)
    ids = data[0]
    return ids.split()


def fix_subject(headerpair):
    # Fixes encodings of subject
    if headerpair[1] is not None:
        return headerpair[0].decode(headerpair[1])
    return headerpair[0]


def fix_recipient(hdr, recipients_list):
    # Fixes encodings of recipients
    if hdr[0][1] is not None:
        recipient_decoded = hdr[0][0].decode(hdr[0][1])
        recipients_list.append(recipient_decoded)
    else:
        recipients_list.append(hdr[0][0])
    return recipients_list


def delay_days_from_message(msg):
    # Gets the delay from the address
    for key in recipient_headers:
        if key in msg:
            mailaddress = msg[key]
            if "@" in mailaddress:
                try:
                    match = re.findall('^(\d+)([dmw])', mailaddress)[0]
                    multiplicator = multiplicate_number_with[match[1]]
                    delay = int(match[0]) * int(multiplicator)
                except:
                    delay = 0

                return delay


def get_delay_address(msg):
    # Gets the delay from the address
    for key in recipient_headers:
        if key in msg:
            mailaddress = msg[key]
            if "@" in mailaddress:
                dropped = re.sub(r'\..*@', '@', mailaddress)

                return dropped


def key_from_message(msg):
    # Gets the key of a message
    for key in recipient_headers:
        if key in msg:
            mailaddress = msg[key]
            if "@" in mailaddress:
                key = re.findall(
                    '^\d+[dmw]\.([0-9a-z]{10})@',
                    mailaddress
                )[0]
                return key


def subject_from_message(msg):
    # Gets the subjects from a message
    subject = msg['subject']
    subj_headers = email.header.decode_header(subject)

    header_texts = [
        fix_subject(hdr)
        for hdr
        in subj_headers
    ]

    subject = " ".join(header_texts)
    subject = re.sub(r'[\r\n]+[\t]*', '', subject)

    return subject


def recipients_from_message(msg):
    # Gets all recipients from a message
    raw = msg['to']
    raw = re.sub(r'( <.*>)', '', raw)
    raw = re.sub(r'[\r\n]+[\t]*', '', raw)
    raw = raw.split(', ')
    recipients_list = []
    for recipient in raw:
        hdr = email.header.decode_header(recipient)
        fix_recipient(hdr, recipients_list)

    recipients = ', '.join(recipients_list)
    return recipients


def recipients_email_from_message(msg):
    # Gets all recipients email from a message
    raw = msg.get_all('to', [])
    recs = []
    recipients = email.utils.getaddresses(raw)
    for recipient in recipients:
        recs.append(recipient[1])

    return recs


def delete_imap_mail(mail_id):
    # Deletes a mail in IMAP
    imap = imap_login()
    results, data = imap.search(
        None,
        '(KEYWORD "MAILDELAY-{0}")'.format(mail_id)
    )
    for imap_mail_id in data[0].split():
        imap.store(imap_mail_id, '+FLAGS', '\\Deleted')
    imap.expunge()


def send_registration_mail(email_to):
    # Sends an error mail to not registred users
    from mails.models import AddressLog

    if not AddressLog.objects.filter(email=email_to, reason=1).exists():
        subject = 'Register at %s!' % host
        tpl = get_template('mails/not_registred_mail.txt')
        content = tpl.render(
            Context({
                'email' : email_to,
                'host'  : host
            })
        )

        msg = EmailMessage(
            subject,
            content,
            email_from,
            [email_to]
        )

        msg.send()

        log_entry = AddressLog(
            email=email_to,
            reason=1,
            attempt=1,
            date=timezone.now()
        )
        log_entry.save()


def send_wrong_recipient_mail(email_to):
    # Sends an error mail to not registred users
    from mails.models import AddressLog

    if not AddressLog.objects.filter(email=email_to).exists():
        subject = 'Your mail on %s was deleted!' % host
        tpl     = get_template('mails/wrong_recipient_mail.txt')
        content = tpl.render(
            Context({
                'email' : email_to,
                'host'  : host
            })
        )
        msg = EmailMessage(
            subject,
            content,
            email_from,
            [email_to]
        )

        msg.send()


def send_activation_mail(key, email_to):
    # Sends an activation mail for additional addresses
    from mails.models import AddressLog

    subject = 'Activate your address on %s' % host
    tpl     = get_template('mails/activation_mail.txt')
    content = tpl.render(
        Context({
            'email' : email_to,
            'key'   : key,
            'host'  : host
        })
    )

    msg = EmailMessage(
        subject,
        content,
        email_from,
        [email_to]
    )

    try:
        log_entry = AddressLog.objects.get(
            email=email_to,
            reason=2
        )

        if log_entry.date < timezone.now() or log_entry.attempt > 5:
            print('Blocked address, no mail sent to %s' % email_to)
            return

        else:
            log_entry.attempt += 1
            log_entry.date = timezone.now() + delays[log_entry.attempt]
            log_entry.save()

        msg.send()

    except:
        msg.send()

        log_entry = AddressLog(
            email=email_to,
            reason=2,
            attempt=0,
            date=timezone.now()
        )
        log_entry.save()


def save_mail(
    subject,
    sent_to,
    sent_from,
    delay_address,
    due,
    sent,
    imap,
    mail,
    recipients
):
    # Saves a mail in DB and logs stats
    from mails.models import ReceivedStatistic, UserStatistic
    from mails.models import Mail, ObliviousStatistic

    m = Mail(
        subject=subject,
        sent=sent,
        due=due,
        sent_from=sent_from,
        sent_to=sent_to
    )
    r = ReceivedStatistic(
        email=delay_address,
        date=timezone.now()
    )
    u = UserStatistic(
        email=sent_from,
        date=timezone.now()
    )
    for recipient in recipients:
        if host not in recipient:
            o = ObliviousStatistic(
                email=recipient,
                date=timezone.now()
            )
            o.save()
        else:
            continue
    r.save()
    u.save()
    m.save()
    imap.store(mail, '+FLAGS', "MAILDELAY-%d" % m.id)
    imap.store(mail, '+FLAGS', '\\Flagged')


def get_all_addresses(request):
    # Gets all addresses of the users identity
    from mails.models import UserIdentity

    identity = UserIdentity.objects.get(user=request.user).identity
    accounts = UserIdentity.objects.filter(identity=identity)
    addresses = [account.user.email for account in accounts]

    return addresses


def get_all_users(request):
    # Gets all addresses of the users identity
    from mails.models import UserIdentity

    identity = UserIdentity.objects.get(user=request.user).identity
    accounts = UserIdentity.objects.filter(identity=identity)
    addresses = [account.user for account in accounts]

    return addresses


def delete_mail_with_error(mail, reason, sent_from, imap):
    # Deletes a mail (in IMAP) and prints out an error message
    imap.store(mail, '+FLAGS', '\\Deleted')
    print('Mail from %s deleted: %s' % (sent_from, reason))


def create_additional_user(email, request):
    # Creates an additional user with the same password and identity
    from mails.models import UserIdentity, AddressLog

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

    identity = UserIdentity.objects.get(user=request.user).identity
    user_identity = UserIdentity(
        user=new_user,
        identity=identity
    )

    try:
        user_log_entry = AddressLog.objects.filter(
            email=request.user.email
        )
        user_log_entry.delete()
    except:
        pass

    send_activation_mail(
        email_to=email,
        key=base64.b16encode(new_user.username)
    )

    user_identity.save()
