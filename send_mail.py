
from __future__ import print_function

from google_auth_oauthlib.flow import InstalledAppFlow

import base64
import mimetypes
import os
from email.message import EmailMessage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import pickle
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import smtplib
from os.path import basename
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


def send_email_using_smtp(recipients:list, subject:str, message_text:str, attachment_filename=None):
    """
    Send email using SMTP with port 465 and host smtp.dreamhost.com
    :param recipients: recipients list
    :param subject: email subject
    :param message_text: message text body
    :param attachment_filename: file path to attched if needed
    """
    #     create message
    from_addr = 'donotreply@allergyfood.my-new-vision.com'
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = ', '.join(recipients)
    msg.attach(MIMEText(message_text, 'html'))
    #     attach file if needed
    if attachment_filename:
        part = build_file_part(attachment_filename)
        msg.attach(part)
    #     connect to server
    server = smtplib.SMTP('smtp.dreamhost.com', 587)
    server.login(from_addr, 'xGR*N9fF')

    #     send message
    server.sendmail(msg=msg.as_bytes(),from_addr=from_addr, to_addrs=recipients)




def gmail_send_message(recipients, subject, message_text, attachment_filename=None):
    """Create and send an email message
    :param recipients: list of recipients
    :param subject: subject of the email
    :param message_text: message to be sent
    :param attachment_filename: file to be attached
    """
    # test if pickle file exists
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    else:

        SCOPES = [ 'https://mail.google.com/',
                                   'https://www.googleapis.com/auth/gmail.modify',
                                   'https://www.googleapis.com/auth/gmail.compose',
                                   'https://www.googleapis.com/auth/gmail.send']

        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret.json', SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)



    # creds = creds.with_subject('nirp0109@gmail.com')
    try:
        service = build('gmail', 'v1', credentials=creds)
        print('Gmail service created successfully')
        mime_message = EmailMessage()

        # headers
        mime_message['To'] = recipients
        mime_message['From'] = 'gduser2@workspacesamples.dev'
        mime_message['Subject'] = subject

        # text
        if "</html>" in message_text:
            # html
            mime_message.add_header('Content-Type', 'text/html')
            mime_message.set_payload(message_text)
        else:
            mime_message.set_content(
                message_text
            )


        # guessing the MIME type
        type_subtype, _ = mimetypes.guess_type(attachment_filename)
        maintype, subtype = type_subtype.split('/')

        with open(attachment_filename, 'rb') as fp:
            attachment_data = fp.read()

        mime_message.add_attachment(
            attachment_data,
            maintype=maintype,
            subtype=subtype,
            filename=os.path.basename(attachment_filename)
        )

        encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

        create_message = {
            'raw': encoded_message
        }


        # pylint: disable=E1101
        send_message = (service.users().messages().send
                        (userId="me", body=create_message).execute())
        print(F'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(F'An error occurred: {error}')
        send_message = None
    return send_message


def build_file_part(file):
    """Creates a MIME part for a file.

    Args:
      file: The path to the file to be attached.

    Returns:
      A MIME part that can be attached to a message.
    """
    content_type, encoding = mimetypes.guess_type(file)

    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    if main_type == 'text':
        with open(file, 'rb'):
            msg = MIMEText('r', _subtype=sub_type)
    elif main_type == 'image':
        with open(file, 'rb'):
            msg = MIMEImage('r', _subtype=sub_type)
    elif main_type == 'audio':
        with open(file, 'rb'):
            msg = MIMEAudio('r', _subtype=sub_type)
    else:
        with open(file, 'rb') as fp:
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
    filename = os.path.basename(file)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    return msg


if __name__ == '__main__':
    attach_file = 'GLN.csv'
    recipients = ['nirp0109@gmail.com', 'nirp_98@yahoo.com']
    # with open("whattoeat.png", 'rb') as f:
    #     data = f.read()
    # image_base64 = base64.b64encode(data).decode()
    # image_data = f"data:image/png;base64,{image_base64}"
    message =f"""<html><h1>Please do not reply.</h1><h2>this is only for reports</h2><div><p>Taken from wikpedia</p></div></html>"""
    print(message)
    # gmail_send_message(recipients=recipients, subject='test with attachment', message_text=message, attachment_filename=attach_file)
    send_email_using_smtp(recipients=recipients, subject='test with attachment', message_text=message, attachment_filename=attach_file)