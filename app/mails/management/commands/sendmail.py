import smtplib
import logging
from django.utils import timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from mails.models import Statistic, Due
from mails import imaphelper
from django.core.management.base import BaseCommand
from django.conf import settings
from django.template.loader import get_template
from django.core.mail import EmailMessage


logger = logging.getLogger("mails")


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        smtp = connect_to_smtp()

        dues = Due.objects.filter(due__lte=timezone.now())

        for due in dues:
            mail = due.mail

            imap_conn = imaphelper.get_connection()
            try:
                message = imaphelper.IMAPMessage.from_dbid(mail.id, imap_conn)
            except IndexError:
                mail.delete()
                logger.warning(
                    "Imap message of mail {} could not be found".format(mail.id)
                )

                return

            recipients = mail.recipient_set
            tpl = get_template("mails/messages/mail_attachment.txt")
            text = tpl.render({"recipients": recipients})
            msg = None

            handle_mulitpart_message(message=message, mail=mail, text=text, msg=msg)

            try:
                handle_attachment(message=message, mail=mail, text=text, msg=msg)
            except:
                message.delete()
                print("Failed to write new header")
                break

            stats = Statistic(type="SENT", email=mail.user.email, date=timezone.now())
            stats.save()

            due.delete()

            if not mail.due_set.count():
                message.delete()
                mail.delete()

        smtp.quit()


def connect_to_smtp():
    try:
        smtp = smtplib.SMTP(settings.EMAIL_HOST)
        smtp.starttls()
        smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    except:
        return


def handle_mulitpart_message(message, mail, text, msg):
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


def handle_attachment(message, mail, text, msg):
    for i in message.msg.walk():
        if i.get_content_maintype() == "text":
            content = i.get_payload(decode=True)
            break

    attachments = []
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get("Content-Disposition") is None:
            continue
        attachments.append(part)

    email = EmailMessage(
        "Reminder from {}: {}".format(mail.sent.strftime("%b %d %H:%M"), mail.subject),
        content.decode("utf-8") + text,
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
