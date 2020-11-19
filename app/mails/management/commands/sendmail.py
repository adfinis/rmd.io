import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.template.loader import get_template
from django.utils import timezone
from mails import imaphelper
from mails.models import Due, Statistic

logger = logging.getLogger("mails")


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        dues = Due.objects.filter(due__lte=timezone.now())

        for due in dues:
            mail = due.mail

            imap_conn = imaphelper.get_connection()
            try:
                message = imaphelper.IMAPMessage.from_dbid(mail.id, imap_conn)
            except IndexError:
                logger.warning(
                    "Imap message of mail {} could not be found".format(mail.id)
                )
                mail.delete()

                return

            recipients = mail.recipient_set
            tpl = get_template("mails/messages/mail_attachment.txt")
            text = tpl.render({"recipients": recipients})

            try:
                send_email_with_attachments(message=message, mail=mail, text=text)
            except Exception as exc:
                message.delete()
                logger.error("Failed to write new header")
                logger.exception(exc)
                continue

            stats = Statistic(type="SENT", email=mail.user.email, date=timezone.now())
            stats.save()

            due.delete()

            if not mail.due_set.count():
                message.delete()
                mail.delete()


def attach_MIMEText_to_mulitpart_messages(message, text):
    charset = message.msg.get_content_charset()

    if message.msg.is_multipart():
        add_text = MIMEText(text, "plain", "utf-8")
        if message.msg.get_content_maintype == "multipart/signed":
            # If it's a signed message, only take first payload
            msg = MIMEMultipart()
            orig = message.msg.get_payload(0)
            msg.attach(orig)
            msg.attach(add_text)
        else:
            msg = MIMEMultipart()
            msg.attach(message.msg)
            msg.attach(add_text)

    else:
        msg = MIMEText(
            "\n\n".join((message.msg.get_payload(), str(text))), "plain", charset,
        )
    return msg


def send_email_with_attachments(message, mail, text):
    for i in message.msg.walk():
        if i.get_content_maintype() == "text":
            content = i.get_payload(decode=True)
            break

    attachments = []
    msg = attach_MIMEText_to_mulitpart_messages(message, text)
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get("Content-Disposition") is None:
            continue
        attachments.append(part)

    email = EmailMessage(
        "Reminder from {}: {}".format(mail.sent.strftime("%b %d %H:%M"), mail.subject),
        content + text.encode(),
        settings.EMAIL_HOST_USER,
        [mail.user.email],
    )
    for attachment in attachments:
        email.attach(
            attachment.get_filename(),
            attachment.get_payload(decode=True),
            attachment.get_content_type(),
        )
    email.send()
