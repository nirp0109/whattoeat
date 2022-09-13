
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
        mime_message.set_content(
            message_text
        )

        # guessing the MIME type
        type_subtype, _ = mimetypes.guess_type(attachment_filename)
        maintype, subtype = type_subtype.split('/')

        with open(attachment_filename, 'rb') as fp:
            attachment_data = fp.read()
        mime_message.add_attachment(attachment_data, maintype, subtype)
        # encoded message
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


if __name__ == '__main__':
    attach_file = 'GLN.csv'
    recipients = ['nirp0109@gmail.com', 'nirp_98@yahoo.com']
    gmail_send_message(recipients=recipients, subject='test with attachment', message_text='Please do not reply.', attchment_file=attach_file)