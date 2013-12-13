import email.utils
import email.header
import imaplib
import smtplib
import time
import re
import datetime
from django.conf import settings

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

    try:
        smtp = smtplib.SMTP(settings.EMAIL_SERVER)
        smtp.starttls()
        smtp.login(settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
        return smtp
    except:
        print "Connection to SMTP-Server failed"


def imap_login():

    try:
        imap = imaplib.IMAP4_SSL(settings.EMAIL_SERVER)
        imap.login(settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
        imap.select(settings.FOLDER)
        return imap
    except:
        print "Connection to IMAP4-Server failed"


def parsedate(datestr):
    dt_tuple = email.utils.parsedate(datestr)
    timestamp = time.mktime(dt_tuple)
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt


def mails_with_id(mail_id, imap):
    results, data = imap.search(None, '(KEYWORD "MAILDELAY-%d")' % mail_id)
    ids = data[0]
    return ids.split()


def fix_pair(headerpair):
    if headerpair[1] is not None:
        return headerpair[0].decode(headerpair[1])
    return headerpair[0]


def delay_days_from_message(msg):

    for key in recipient_headers:
        if key not in msg:
            continue
        else:
            mailaddress = msg[key]
            if "@" in mailaddress:
                if len(mailaddress) == 0:
                    continue
                try:
                    match = re.findall("^(\d+)([dmw])", mailaddress)[0]
                    multiplicator = multiplicate_number_with[match[1]]
                    days = int(match[0]) * int(multiplicator)
                    return days
                except:
                    print "wrong address"


def key_from_message(msg):

    for key in recipient_headers:
        if key not in msg:
            continue
        else:
            mailaddress = msg[key]
            if "@" in mailaddress:
                if len(mailaddress) == 0:
                    continue
            key = re.findall("^\d+[dmw]\.([0-9a-z]{10})@", mailaddress)[0]
            return key


def subject_from_message(msg):
    subject = msg['subject']
    subj_headers = email.header.decode_header(subject)

    header_texts = [
        fix_pair(hdr)
        for hdr
        in subj_headers
    ]

    subject = " ".join(header_texts)
    subject = re.sub(r'[\r\n]+[\t]*', '', subject)

    return subject


def delete_imap_mail(mail_id):
    imap = imap_login()
    results, data = imap.search(None, '(KEYWORD "MAILDELAY-%s")' % mail_id)
    imap_mail_id = data[0].split()
    for mailid in imap_mail_id:
        imap.store(mailid, '+FLAGS', '\\Deleted')
    imap.expunge()
