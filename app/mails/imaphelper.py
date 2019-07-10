from django.conf import settings
import datetime
import email
import imaplib
import pytz
import re


def get_connection():
    '''Gets an IMAP connection

    :rtype  imaplib.IMAP4_SSL
    '''
    imap_conn = imaplib.IMAP4_SSL(settings.EMAIL_HOST)
    imap_conn.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    imap_conn.select(settings.EMAIL_FOLDER)

    return imap_conn


def get_unflagged(imap_conn):
    '''Gets all unflagged mails of an IMAP connection

    :param  imap_conn: the IMAP connection to search through
    :type   imap_conn: imaplib.IMAP4_SSL
    :rtype  iterator
    '''
    results, data = imap_conn.uid('search', None, 'UNFLAGGED')
    uids = data[0].split()
    msgs = []

    for uid in uids:
        msgs.append(IMAPMessage.from_imapuid(imap_conn, uid))

    return iter(msgs)


class IMAPMessage(object):
    recipient_headers = [
        'To',
        'Cc',
        'X-Original-To'
    ]

    def __init__(self, imap_conn, imapuid, dbid=None):
        self.imap_conn = imap_conn
        self.imapuid = imapuid
        self.dbid = dbid
        self.msg = self._get_msg_from_imap()

    @classmethod
    def from_dbid(cls, dbid, imap_conn):
        '''Gets an IMAP mail by its database id

        :param  dbid: database id of the mail
        :type   dbid: int
        :rtype  IMAPMessage
        '''
        results, data = imap_conn.uid(
            'search',
            None,
            '(KEYWORD "MAILDELAY-%d")' % int(dbid)
        )
        imapuid = data[0].split()[0]

        self = cls.from_imapuid(imap_conn, imapuid)
        self.dbid = dbid

        return self

    @classmethod
    def from_imapuid(cls, imap_conn, imapuid):
        '''Gets an IMAP mail by its IMAP uid

        :param  imapuid: IMAP uid of the mail
        :type   imapuid: int
        :rtype  IMAPMessage
        '''
        return cls(imap_conn, imapuid)

    def _get_msg_from_imap(self):
        '''Gets the message of an IMAP mail

        :rtype  email.message.Message
        '''
        results, data = self.imap_conn.uid('fetch', self.imapuid, 'RFC822')
        import ipdb
        ipdb.set_trace()
        msg = email.message_from_string(
            str(
                data[0][1].decode("latin-1").encode("utf-8")
            )
        )

        return msg

    def _fix_header_encoding(self, headerpair):
        '''Fixes encodings of a header

        :param  headerpair: headerpair to fix encoding
        :type   headerpair: tupel
        :rtype  str
        '''
        if headerpair[1] is not None:
            return headerpair[0].decode(headerpair[1])

        return headerpair[0]

    def _parse_date_from_string(self, datestr):
        '''Parses datestrings to datetime objects

        :param  datestr: date to parse as string
        :type   datestr: str
        :rtype: datetime.datetime
        '''
        dt_tuple = email.utils.parsedate_tz(datestr)
        timestamp = email.utils.mktime_tz(dt_tuple)
        dt = datetime.datetime.utcfromtimestamp(timestamp)

        return dt.replace(tzinfo=pytz.utc)

    def flag(self, dbid):
        '''Flag the mail in IMAP as read and mark it with
        a unique maildelay flag

        :param  dbid: the mail id from the database
        :type   dbid: int
        '''
        self.imap_conn.uid(
            'store',
            self.imapuid,
            '+FLAGS',
            "(MAILDELAY-%d)" % dbid
        )
        self.imap_conn.uid('store', self.imapuid, '+FLAGS', '(\\Flagged)')

        self.dbid = dbid

    def delete(self):
        '''Deletes the mail in IMAP

        The IMAP connection needs to be expunged afterwards!

        :param  dbid: the mail id from the database
        :type   dbid: int
        '''
        self.imap_conn.uid('store', self.imapuid, '+FLAGS', '(\\Deleted)')

    def get_subject(self):
        '''Parses subject from message

        :rtype:      str
        '''
        try:
            subjects_raw = email.header.decode_header(self.msg['Subject'])

            header_texts = [
                self._fix_header_encoding(hdr)
                for hdr
                in subjects_raw
            ]

            subject = " ".join(header_texts)
            subject = re.sub(r'[\r\n]+[\t]*', '', subject)

            return subject

        except:
            raise ValueError('Invalid subject')

    def get_sender(self):
        '''Parses sender from message

        :rtype:      string
        '''
        try:
            return email.utils.getaddresses(self.msg.get_all('From', []))[0][1]
        except:
            raise ValueError('Invalid sender')

    def get_recipients(self):
        '''Parses recipients from message

        :rtype:      list
        '''
        recipients = []

        for key in self.recipient_headers:
            try:
                recipient_list = email.utils.getaddresses(
                    self.msg.get_all(key, [])
                )
                for recipient in recipient_list:
                    r = {
                        'name': recipient[0],
                        'email': recipient[1]
                    }
                    if r not in recipients:
                        recipients.append(r)
                    else:
                        continue
            except:
                raise ValueError('Invalid recipients')

        return recipients

    def get_sent_date(self):
        '''Parse from a message

        :rtype:      datetime.datetime
        '''
        try:
            return self._parse_date_from_string(self.msg['date'])
        except:
            raise ValueError('Invalid sent date')
