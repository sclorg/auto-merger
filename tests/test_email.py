#!/usr/bin/env python3

from flexmock import flexmock

from auto_merger.email import EmailSender


def test_create_email_no_recepients():
    es = EmailSender(recipient_email=[])
    es.create_email_msg("something important")
    assert es.mime_msg
    assert es.mime_msg["From"] == "phracek@redhat.com"
    assert "phracek@redhat.com" in es.mime_msg["To"]
    assert "sclorg@redhat.com" not in es.mime_msg["To"]
    assert es.mime_msg["Subject"] == "something important"


def test_create_email_with_recipients():
    es = EmailSender(recipient_email=["foo@bar.com"])
    es.create_email_msg("something important")
    assert es.mime_msg
    assert es.mime_msg["From"] == "phracek@redhat.com"
    assert "phracek@redhat.com" in es.mime_msg["To"]
    assert "sclorg@redhat.com" not in es.mime_msg["To"]
    assert "foo@bar.com" in es.mime_msg["To"]
    assert es.mime_msg["Subject"] == "something important"
