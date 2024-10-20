# MIT License
#
# Copyright (c) 2024 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import smtplib


from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List


class EmailSender:

    def __init__(self, recipient_email: List[str]):
        self.recipient_email = recipient_email
        self.mime_msg = MIMEMultipart()

    def send_email(self, subject_msg, body: List[str]):
        send_from = "phracek@redhat.com"
        send_to = self.recipient_email
        print(body)
        msg = "<br>".join(body)
        print(msg)
        self.mime_msg["From"] = send_from
        self.mime_msg["To"] = ", ".join(send_to)
        self.mime_msg["Subject"] = subject_msg
        self.mime_msg.attach(MIMEText(msg, "html"))
        smtp = smtplib.SMTP("127.0.0.1")
        smtp.sendmail(send_from, send_to, self.mime_msg.as_string())
        smtp.close()
        print("Sending email finished")

