import imapclient
import smtplib
import json
import docopt
import logging
import email
from email.utils import parseaddr
from pprint import pprint
from datetime import datetime
from mailprovider import *

class ImapListener:
    def __init__(self, cfg):
        self.config = cfg
        if self.config['last_check']:
            self.last_check = datetime.strptime(self.config['last_check'], "%Y-%m-%d %H:%M:%S.%f")
        else:
            self.last_check = None

    def connect(self):
        logging.debug( "Connecting to server {0} ussing SSL {1}".format(self.config['imap'], self.config['use_ssl']) )
        self.imap = imapclient.IMAPClient(self.config['imap'], ssl=self.config['use_ssl'])
        logging.debug( "Logging in with user {0}".format(self.config['username']) )
        self.imap.login(self.config['username'], self.config['password'])

    def update(self):
        logging.debug("Checking for new emails")
        retval = self.fetch_new_since( self.last_check )
        self.last_check = datetime.now()
        return retval

    def fetch_new_since(self, time):
        select_info = self.imap.select_folder('INBOX')
        logging.debug('%d messages in INBOX' % select_info['EXISTS'])

        if time: #CONFIG['last_check']:
            logging.info( "Last time checked {0}".format(self.last_check) )
            messages = self.imap.search([u'UNSEEN', u'SINCE', self.last_check])
        else:
            logging.info( "(!!!) Never checked before" )
            messages = self.imap.search([u'UNSEEN'])

        # fetch actual messages
        self.batch = self.imap.fetch(messages, ['INTERNALDATE', 'FLAGS', 'RFC822', 'BODY'])
        return self.batch.iteritems()


    def get_decoded_email_body(self, message_body):
        """ Decode email body.
        Detect character set if the header is not set.
        We try to get text/plain, but if there is not one then fallback to text/html.
        :param message_body: Raw 7-bit message body input e.g. from imaplib. Double encoded in quoted-printable and latin-1
        :return: Message body as unicode string
        """

        msg = email.message_from_string(message_body)

        text = ""
        if msg.is_multipart():
            html = None
            for part in msg.get_payload():
                #logging.debug("Found part %s, %s" % (part.get_content_type(), part.get_content_charset()) )
                if part.get_content_charset() is None:
                    # We cannot know the character set, so return decoded "something"
                    text = part.get_payload(decode=True)
                    continue

                charset = part.get_content_charset()

                if part.get_content_type() == 'text/plain':
                    text = unicode(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace')

                if part.get_content_type() == 'text/html':
                    html = unicode(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace')

            if text is not None:
                return text.strip()
            else:
                return html.strip()
        else:
            text = unicode(msg.get_payload(decode=True), msg.get_content_charset(), 'ignore').encode('utf8', 'replace')
            return text.strip()

    def get_email(self, msgid):
        return email.message_from_string(self.batch[msgid]['RFC822'])

    def get_body_as_text(self, msgid):
        msg = email.message_from_string(self.batch[msgid]['RFC822'])
        #print parseaddr(msg['from'])
        return self.get_decoded_email_body(self.batch[msgid]['RFC822'])


    def mark_as_read(self, msgid):
        # Mark messages as read
        self.imap.add_flags(msgid, ['SEEN'])

    def mark_as_unread(self, msgid):
        # Mark messages as unread
        self.imap.remove_flags(msgid, ['SEEN'])

    def reply_to_message(self, msgid, replybody):
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.message import MIMEMessage

        original = self.get_email(msgid)

        new = MIMEMultipart("mixed")
        body = MIMEMultipart("alternative")
        body.attach( MIMEText(replybody, "plain") )
        # body.attach( MIMEText("<html>reply body text</html>", "html") )
        new.attach(body)

        new["Message-ID"] = email.utils.make_msgid()
        new["In-Reply-To"] = original["Message-ID"]
        new["References"] = original["Message-ID"]
        new["Subject"] = "Re: "+original["Subject"]
        new["To"] = original["Reply-To"] or original["From"]
        new["From"] = self.config['reply_from']

        # attach original message
        new.attach( MIMEMessage(original) )

        logging.debug("Replying to message")

        # dispatch email
        s = smtplib.SMTP_SSL(self.config['smtp'], 465)
        s.login(self.config['username'], self.config['password'])
        s.sendmail(new["From"], [new["To"]], new.as_string())
        s.quit()
