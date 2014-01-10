import email.utils
import email.header
import imaplib
import smtplib
import time
import re
import base64
import datetime
from django.conf import settings
from email.mime.text import MIMEText
from django.template.loader import get_template
from django.template import Context
from django.utils import timezone
from hashlib import sha1
from django.contrib.auth.models import User
from django.utils.encoding import smart_bytes

recipient_headers = [
    'X-Original-To',
    'To'
]

multiplicate_number_with = {
    'd' : 1,
    'w' : 7,
    'm' : 30,
}

mailbox_to_days = {
    entry[0]: entry[1]
    for entry
    in settings.MAILBOXES
}


def smtp_login():
    # Connects to SMTP server
    try:
        smtp = smtplib.SMTP(settings.EMAIL_SERVER)
        smtp.starttls()
        smtp.login(settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
        return smtp
    except:
        print('Failed to login to SMTP server, aborting.')


def imap_login():
    # Connects to IMAP server
    try:
        imap = imaplib.IMAP4_SSL(settings.EMAIL_SERVER)
        imap.login(settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
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
                match = re.findall('^(\d+)([dmw])', mailaddress)[0]
                multiplicator = multiplicate_number_with[match[1]]
                delay = int(match[0]) * int(multiplicator)
                return delay


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


def delete_imap_mail(mail_id):
    # Deletes a mail in IMAP
    imap = imap_login()
    results, data = imap.search(None, '(KEYWORD "MAILDELAY-%s")' % mail_id)
    imap_mail_id = data[0].split()
    for mailid in imap_mail_id:
        imap.store(mailid, '+FLAGS', '\\Deleted')
    imap.expunge()


def send_registration_mail(subject, sender):
    # Sends an error mail to not registred users
    from mails.models import AddressLog

    if not AddressLog.objects.filter(email=sender, reason=1).exists():
        smtp = smtp_login()
        host = settings.EMAIL_ADDRESS.split('@')[1]
        content = get_template('mails/not_registred_mail.txt')
        parameters = Context(
            {
                'sender'    : sender,
                'host'      : host
            }
        )
        content = content.render(parameters)
        text_subtype = 'plain'
        charset = 'utf-8'
        msg = MIMEText(content.encode(charset), text_subtype, charset)
        msg['Subject'] = 'Register at %s!' % host
        msg['From'] = settings.EMAIL_ADDRESS
        msg['Date'] = email.utils.formatdate(localtime=True)

        smtp.sendmail(settings.EMAIL_ADDRESS, sender, msg.as_string())
        smtp.quit()

        log_entry = AddressLog(
            email=sender,
            reason=1,
            attempt=1,
            date=timezone.now()
        )
        log_entry.save()

        print('Sent registration mail to %s' % sender)


def send_error_mail(subject, sender):
    # Sends an error mail to not registred users
    from mails.models import AddressLog

    if not AddressLog.objects.filter(address=sender).exists():
        smtp = smtp_login()
        host = settings.EMAIL_ADDRESS.split('@')[1]
        content = get_template('mails/wrong_recipient_mail.txt')
        parameters = Context(
            {
                'sender'    : sender,
                'host'      : host
            }
        )
        content = content.render(parameters)
        text_subtype = 'plain'
        charset = 'utf-8'
        msg = MIMEText(content.encode(charset), text_subtype, charset)
        msg['Subject'] = 'Your mail on %s was deleted!' % host
        msg['From'] = settings.EMAIL_ADDRESS
        msg['Date'] = email.utils.formatdate(localtime=True)

        smtp.sendmail(settings.EMAIL_ADDRESS, sender, msg.as_string())
        smtp.quit()

        print('Sent error mail to %s') % sender


def send_activation_mail(key, address, host):
    # Sends an activation mail for additional addresses
    from mails.models import AddressLog

    delay1 = timezone.now() + datetime.timedelta(minutes=10)
    delay2 = timezone.now() + datetime.timedelta(hours=1)
    delay3 = timezone.now() + datetime.timedelta(1)
    delay4 = timezone.now() + datetime.timedelta(3)
    delay5 = timezone.now() + datetime.timedelta(7)

    smtp = smtp_login()
    content = get_template('mails/activation_mail.txt')
    parameters = Context(
        {
            'key'    : key,
            'host'   : host
        }
    )
    content = content.render(parameters)
    text_subtype = 'plain'
    charset = 'utf-8'
    msg = MIMEText(content.encode(charset), text_subtype, charset)
    msg['Subject'] = 'Activate your address on %s' % host
    msg['From'] = settings.EMAIL_ADDRESS
    msg['Date'] = email.utils.formatdate(localtime=True)

    try:
        log_entry = AddressLog.objects.get(
            email=address,
            reason=2
        )

        if log_entry.date < timezone.now() or log_entry.attempt > 5:
            print('Blocked address, no mail sent to %s' % address)
            smtp.quit()
            return

        elif log_entry.attempt == 1:
            log_entry.attempt = 2
            log_entry.date = delay1
            log_entry.save()

        elif log_entry.attempt == 2:
            log_entry.attempt = 3
            log_entry.date = delay2
            log_entry.save()

        elif log_entry.attempt == 3:
            log_entry.attempt = 4
            log_entry.date = delay3
            log_entry.save()

        elif log_entry.attempt == 4:
            log_entry.attempt = 5
            log_entry.date = delay4
            log_entry.save()

        elif log_entry.attempt == 5:
            log_entry.attempt = 6
            log_entry.date = delay5
            log_entry.save()

        smtp.sendmail(settings.EMAIL_ADDRESS, address, msg.as_string())

    except:
        smtp.sendmail(settings.EMAIL_ADDRESS, address, msg.as_string())

        log_entry = AddressLog(
            email=address,
            reason=2,
            attempt=1,
            date=timezone.now()
        )
        log_entry.save()

    smtp.quit()

    print('Sent activation mail to %s' % address)


def get_all_addresses(request, *args):
    # Gets all addresses of the users identity
    from mails.models import Identity

    identity = Identity.objects.get(user=request.user)
    users = get_all_users(identity.identity, *args)
    addresses = [user.email for user in users]

    return addresses


def get_all_users(identity_name, *args):
    # Gets all users of an identity
    from mails.models import Identity

    instances = Identity.objects.filter(identity=identity_name)
    if 'only_actives' in args:
        users = [
            instance.user
            for instance
            in instances
            if instance.user.is_active
        ]
    else:
        users = [instance.user for instance in instances]

    return users


def delete_mail_with_error(mail, reason, sent_from, imap):
    # Deletes a mail (in IMAP) and prints out an error message
    imap.store(mail, '+FLAGS', '\\Deleted')
    print('Mail from %s deleted: %s' % (sent_from, reason))


def create_additional_user(email, request):
    # Creates an additional user with the same password and identity
    from mails.models import Identity, UserKey, Setting, AddressLog

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
    user_identity = Identity(
        identity=Identity.objects.get(user=request.user).identity,
        user=new_user
    )
    user_key = UserKey(
        key=request.user.userkey.key,
        user=new_user
    )
    user_setting = Setting(user=new_user)

    try:
        user_log_entry = AddressLog.objects.filter(
            email=request.user.email,
            reason=1
        )
        user_log_entry.delete()
    except:
        pass

    send_activation_mail(
        address=email,
        key=base64.b16encode(new_user.username),
        host=request.get_host()
    )

    user_identity.save()
    user_key.save()
    user_setting.save()
