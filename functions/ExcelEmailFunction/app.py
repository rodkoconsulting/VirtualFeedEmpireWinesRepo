import os
import boto3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from botocore.exceptions import ClientError
import datetime
from dateutil import relativedelta


class Config:
    BUCKET_NAME = os.environ.get('BUCKET_NAME')
    FILE_NAME = os.environ.get('FILE_NAME')
    EMAIL_TO = os.environ.get('EMAIL_TO')
    EMAIL_CC = os.environ.get('EMAIL_CC')
    EMAIL_FROM = os.environ.get('EMAIL_FROM')
    EMAIL_SUBJECT = os.environ.get('EMAIL_SUBJECT')
    EMAIL_ATTACHMENT = os.environ.get('EMAIL_ATTACHMENT')
    CHARSET = 'utf-8'


def handle_errors(action):
    try:
        return action()
    except Exception as e:
        print(f'Error: {e}')
        raise


def get_next_month():
    next_month = datetime.date.today() + relativedelta.relativedelta(months=1)
    return next_month.strftime('%B')


def get_file_from_s3(bucket_name: str, file_name: str, file_path: str):
    s3 = boto3.client('s3')
    with open(file_path, 'wb') as f:
        s3.download_fileobj(bucket_name, file_name, f)


def compose_email(subject, body, from_email, to_email, cc_email, attachment_path, attachment_name):
    msg = MIMEMultipart('mixed')
    msg['Subject'] = f'{subject} - {get_next_month()}'
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Cc'] = cc_email
    msg_body = MIMEMultipart('alternative')
    email_text = MIMEText(body.encode(Config.CHARSET), 'plain', Config.CHARSET)
    msg_body.attach(email_text)
    att = MIMEApplication(open(attachment_path, 'rb').read())
    att.add_header('Content-Disposition', 'attachment', filename=attachment_name)
    msg.attach(att)
    msg.attach(msg_body)
    return msg


def send_email():
    ses = boto3.client('ses', region_name='us-east-1')
    email = compose_email(Config.EMAIL_SUBJECT, "", Config.EMAIL_FROM, Config.EMAIL_TO, Config.EMAIL_CC,
                          '/tmp/' + Config.FILE_NAME, Config.EMAIL_ATTACHMENT)

    try:
        response = ses.send_raw_email(
            Source=email['From'],
            Destinations=[email['To'], email['Cc']],
            RawMessage={'Data': email.as_string()}
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:", response['MessageId'])


def lambda_handler(event, context):
    handle_errors(lambda: email_file_from_s3())


def email_file_from_s3():
    get_file_from_s3(Config.BUCKET_NAME, Config.FILE_NAME, '/tmp/' + Config.FILE_NAME)
    send_email()
