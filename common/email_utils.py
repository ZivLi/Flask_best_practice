# -*- coding: utf-8 -*-

import smtplib
import urllib.request
import re
import time
import logging
from urllib.parse import unquote

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import parseaddr, formataddr
from email.mime.application import MIMEApplication
from email.encoders import encode_base64


MAX_CONNECT_TIMES = 3


class MailConfig(object):

    MAIL_HOST = "smtp.partner.outlook.cn"
    MAIL_HOST = "{email_host}"
    MAIL_PORT = "{email_port}"


class OuterEmailConfig(MailConfig):
    """
    用户发送外部邮件
    """

    SERVICE_EMAIL_SENDER = "email_sender"
    SERVICE_SENDER_PWD = "email_sender_pwd"



class EmailSender:
    @classmethod
    def do_send_email(cls, EmailConfig=OuterEmailConfig, **kwargs):

        mail_sender = EmailConfig.SERVICE_EMAIL_SENDER
        mail_sender_pws = EmailConfig.SERVICE_SENDER_PWD
        receivers = kwargs.pop("receivers", None)
        mail_host = kwargs.pop("mail_host", None) or EmailConfig.MAIL_HOST
        mail_port = kwargs.pop("mail_port", None) or EmailConfig.MAIL_PORT
        subject = kwargs.pop("subject", None)
        body = kwargs.pop("body", None)
        file_name = kwargs.pop("file_name", None)
        file_obj = kwargs.pop("file_obj", None)
        html_body = kwargs.pop("html_body", None)

        message = MIMEMultipart()
        message["From"] = _format_addr("<%s>" % mail_sender)
        message["To"] = ",".join(
            [_format_addr("<%s>" % receiver) for receiver in receivers]
        )
        message["Subject"] = Header(subject, "utf-8").encode()

        if html_body:
            # 邮件正文是 html:
            text = MIMEText(html_body, "html", "utf-8")
        else:
            # 邮件正文是文本 string:
            text = MIMEText(body, "plain", "utf-8")
        # Content-Transfer-Encoding: base64 解决中文内容编码
        encode_base64(text)
        message.attach(text)

        if file_obj:
            if isinstance(file_obj, list):
                for _index, _file in enumerate(file_obj):
                    if isinstance(_file, bytes):
                        attach = MIMEApplication(_file)
                        attach.add_header(
                            "Content-Disposition",
                            "attachment",
                            filename=("gbk", "", file_name[_index]),
                        )
                        message.attach(attach)
                    elif _file.startswith("http"):
                        with urllib.request.urlopen(_file) as response:
                            _filename = unquote(_file.split("/")[-1])
                            attach = MIMEApplication(response.read())
                            attach.add_header(
                                "Content-Disposition",
                                "attachment",
                                filename=_filename,
                            )
                            message.attach(attach)
                    else:
                        with open(_file, "r") as tempfile:
                            attach = MIMEApplication(tempfile.read())
                            attach.add_header(
                                "Content-Disposition",
                                "attachment",
                                filename=("gbk", "", file_name[_index]),
                            )
                            message.attach(attach)
                            tempfile.close()
            else:
                xlsxpart = MIMEApplication(file_obj)
                xlsxpart.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=("gbk", "", file_name),
                )  # 注意：此处basename要转换为gbk编码，否则中文会有乱码。
                message.attach(xlsxpart)

        try:
            smtpObj = smtplib.SMTP(timeout=8)

            count = MAX_CONNECT_TIMES
            while count > 0:
                try:
                    smtpObj.connect(mail_host, mail_port)
                    break
                except Exception as e:
                    time.sleep(1)
                    logging.exception(
                        "smtp server connect error: {}".format(subject)
                    )
                    count -= 1

            smtpObj.ehlo()
            smtpObj.starttls()
            smtpObj.login(mail_sender, mail_sender_pws)

            smtpObj.sendmail(mail_sender, receivers, message.as_string())
            smtpObj.quit()
            return True
        except smtplib.SMTPException:
            logging.exception("SMTPException 无法发送邮件, {}".format(subject))
            return False
        except Exception as e:
            logging.exception("Exception 无法发送邮件, {}".format(subject))
            return False


def is_email(_in):
    p = r"^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}$"
    if re.match(p, _in):
        return True
    else:
        return False


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, "utf-8").encode(), addr))


DEMO_EMAIL = {
    "subject": "demo email subject",
    "html_body": """
        <!DOCTYPE html>
        <html>
            <head>
            </head>
            <body>
                <p>中文内容</p>
                <p>Hello {user_name}, </p>
                <p>This is only a demo email. Do nothing.</p>
                <p><br/></p>
            </body>
        </html>
    """,
}


if __name__ == "__main__":
    DEMO_EMAIL["receivers"] = ["demo@email.com"]
    EmailSender.do_send_email(**DEMO_EMAIL)
