import email
import email.utils
import email.header
import imaplib
import smtplib
import time
import datetime

def parsedate(datestr):
    dt_tuple = email.utils.parsedate(datestr)
    timestamp = time.mktime(dt_tuple)
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt

def count_days(mail_to_send):
    days = (mail_to_send.due - mail_to_send.sent).days
    print days
    return days
