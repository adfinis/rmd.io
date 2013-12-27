import email.utils
import email.header
import imaplib
import smtplib
import time
import re
import datetime
from django.conf import settings
from email.mime.text import MIMEText
from django.template.loader import get_template
from django.template import Context

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
        print('Failed to login to SMTP server, aborting')


def imap_login():
    # Connects to IMAP server
    try:
        imap = imaplib.IMAP4_SSL(settings.EMAIL_SERVER)
        imap.login(settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
        imap.select(settings.FOLDER)
        return imap
    except:
        print('Failed to login to IMAP server, aborting')


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
                    return delay
                except:
                    return


def key_from_message(msg):
    # Gets the key of a message
    for key in recipient_headers:
        if key in msg:
            mailaddress = msg[key]
            if "@" in mailaddress:
                try:
                    key = re.findall(
                        '^\d+[dmw]\.([0-9a-z]{10})@',
                        mailaddress
                    )[0]
                    return key
                except:
                    return


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


def send_error_mail(subject, sender):
    # Sends an error mail to not registred users
    from mails.models import AddressLog

    if AddressLog.objects.all().filter(address=sender) is None:
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
        msg['Subject'] = 'Register at %s!' % (host)
        msg['From'] = settings.EMAIL_ADDRESS

        smtp.sendmail(settings.EMAIL_ADDRESS, sender, msg.as_string())
        smtp.quit()

        entry = AddressLog(address=sender)
        entry.save()

        print('Sent registration mail to %s') % sender

    return


def send_activation_mail(key, address, host):
    # Sends an activation mail for additional addresses
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
    msg['Subject'] = 'Activate your address on %s' % (host)
    msg['From'] = settings.EMAIL_ADDRESS

    smtp.sendmail(settings.EMAIL_ADDRESS, address, msg.as_string())
    smtp.quit()

    print('Sent activation mail to %s') % address

    return


def get_all_addresses(user):
    # Gets all addresses of an user
    from mails.models import AdditionalAddress

    addresses = []
    main_address = user.email
    additional_addresses = AdditionalAddress.objects.filter(
        user = user,
        is_activated = True
    )

    for additional_address in additional_addresses:
        addresses.append(additional_address.address)

    addresses.append(main_address)

    return addresses


def delete_mail_with_error(mail, reason, sent_from):
    # Deletes a mail (in IMAP) and prints out an error message
    imap = imap_login()
    imap.store(mail, '+FLAGS', '\\Deleted')
    print('Mail from %s deleted: %s') % (sent_from, reason)

    return
