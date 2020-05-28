from django.utils.encoding import smart_bytes
from django.core.mail import send_mail
from mails import tools
import hashlib
import base64
import pytest


@pytest.mark.parametrize(
    "url, status_code",
    [
        ("/home/", 200),
        ("/login/", 200),
        ("/registration/", 200),
        ("/help/", 200),
        ("/terms/", 200),
        ("/password_reset/", 200),
        ("/password_change/", 302),
        ("/mails/", 302),
        ("/mails/delete/", 302),
        ("/admin/", 302),
        ("/statistic/", 302),
        ("/settings/", 302),
        ("/user/add/", 302),
        ("/user/delete/", 302),
        ("/user/activate/send/", 302),
        ("/download/maildelay.vcf", 302),
    ],
)
def test_page_status(url, status_code, client):
    response = client.get(url)
    assert response.status_code == status_code


@pytest.mark.parametrize(
    "url",
    [
        "/password_change/",
        "/mails/",
        "/mails/delete/",
        "/statistic/",
        "/settings/",
        "/user/add/",
        "/user/delete/",
        "/user/activate/send/",
        "/download/maildelay.vcf",
    ],
)
def test_redirection_for_login_required_pages(url, client, db):
    response = client.get(url, follow=True)
    redirect = "/login/?next=" + url
    assert response.redirect_chain[0][0] == redirect


def test_type_of_username_in_registration_view():
    test_email = "test@te.st"
    username = (
        base64.urlsafe_b64encode(hashlib.sha1(smart_bytes(test_email)).digest())
        .decode("utf-8")
        .rstrip("=")
    )
    assert type(username) is str


def test_type_of_key_generator_output():
    key = tools.generate_key()
    assert type(key) is str


def test_correct_get_delay_days_from_emai_address():
    delay = tools.get_delay_days_from_email_address("2w@rmd.io")
    expected = 14
    assert delay == expected


def test_wrong_get_delay_days_from_email_address():
    email = "29.02.2001t@rmd.io"
    with pytest.raises(Exception):
        tools.get_delay_days_from_email_address(email)


def test_send_mail(mailoutbox):
    send_mail("subject", "body", "from@example.com", ["to@example.com"])
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.subject == "subject"
    assert mail.body == "body"
    assert mail.from_email == "from@example.com"
    assert list(mail.to) == ["to@example.com"]
