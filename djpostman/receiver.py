# -*- coding: utf-8 -*-
#
# ITerativ GmbH
# http://www.iterativ.ch/
#
# Copyright (c) 2012 ITerativ GmbH. All rights reserved.
#
# Created on May 7, 2012
# @author: maersu <me@maersu.ch>

# See:
# https://github.com/rossp/django-helpdesk/blob/e8ee39ddaad9b85bd935c651491ab172eba00a79/helpdesk/management/commands/get_email.py
# http://stackoverflow.com/questions/730573/django-to-send-and-receive-email

import imaplib
import email
import mimetypes
from email.header import decode_header
from django.conf import settings
from email.Utils import parseaddr, collapse_rfc2231_value, parsedate_tz, getaddresses, mktime_tz
import datetime
from datetime import date, timedelta
import hashlib
from djpostman.models import Message
from django.core.mail import EmailMultiAlternatives
from djangojames.string import strip_tags, strip_empty_tags
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from djpostman.utils import get_or_create_contact

class MailRecieverError(Exception):
    """Base class for exceptions in this module."""
    pass

def decodeUnknown(charset, string):
    if not charset:
        try:
            return string.decode('utf-8')
        except:
            return string.decode('iso8859-1')
    return unicode(string, charset)

def decode_mail_headers(string):
    decoded = decode_header(string)
    return u' '.join([unicode(msg, charset or 'utf-8') for msg, charset in decoded])

class ServerMessage(object):
    
    def __init__(self, message, hash_value, uid):
        self.hash_value = hash_value
        self.uid =  uid 
        message = email.message_from_string(message)

        def _get_header_data(key):
            value = message.get(key, '<unknown>')
            value = decode_mail_headers(decodeUnknown(message.get_charset(), value))
            return value
        
        self.subject = _get_header_data('subject').strip()
        self.sender =  parseaddr(message.get('from'))
        
        received = None
        date_str= message.get('date') 
        if date_str:
            date_tuple= parsedate_tz(date_str)
            if date_tuple:
                received=datetime.datetime.fromtimestamp(mktime_tz(date_tuple))
        self.received = received
    
        self.recipients = getaddresses(message.get_all('to', []) + message.get_all('cc', []) + message.get_all('resent-to', []) + message.get_all('resent-cc', []))
        counter = 0
        files = []
        
        body_plain, body_html = '', ''
        
        for part in message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            name = part.get_param("name")
            if name:
                name = collapse_rfc2231_value(name)
    
            if part.get_content_maintype() == 'text' and name == None:
                if part.get_content_subtype() == 'plain':
                    body_plain = decodeUnknown(part.get_content_charset(), part.get_payload(decode=True))
                else:
                    body_html = part.get_payload(decode=True)
            else:
                if not name:
                    ext = mimetypes.guess_extension(part.get_content_type())
                    name = "part-%i%s" % (counter, ext)
    
                files.append({
                    'filename': name,
                    'content': part.get_payload(decode=True),
                    'type': part.get_content_type()},
                    )
            counter += 1
            
        self.body_plain = body_plain
        self.body_html = mark_safe(strip_empty_tags(strip_tags(body_html, ['html', 'head', 'body', 'meta'])))
        self.files = files

    def get_sender(self, sender):
        sender_email = sender[1]
        
        if User.objects.filter(email=sender_email).exists():
            return User.objects.filter(email=sender_email).order_by('-last_login')[0]
    
    def get_recipients(self, recipients):
        return User.objects.filter(email__in=[r[1] for r in recipients])
    
    def save(self):            
        new_message = Message()
        new_message.subject = self.subject
        new_message.hash_value = self.hash_value
        new_message.uid = self.uid
        new_message.sender = self.get_sender(self.sender)
        
        store_email = EmailMultiAlternatives(new_message.subject, 
                                   self.body_plain, 
                                   self.sender[1], 
                                   [r[1] for r in self.recipients])
        
        if self.body_html:
            store_email.attach_alternative(self.body_html, "text/html")
        new_message.email = store_email
        new_message.save()        
        new_message.recipients = self.get_recipients(self.recipients)
        new_message.created = self.received
        new_message.sent = True
        new_message.save()

        get_or_create_contact(self.sender).emails_sent.add(new_message)
        for rec in self.recipients:
            get_or_create_contact(rec).emails_received.add(new_message)

class BaseMailReceiver(object):
    
    def __init__(self, since_date=None, msg_klass=ServerMessage):            
        if since_date is None:
            self.since_date = date.today()
        else:
            self.since_date = since_date
        self.since_date = self.since_date - timedelta (days = 1)
        self.old_hash_values = []
        
        self.msg_klass=msg_klass

    def fetch_mail(self):
        self.old_hash_values = list(Message.objects.filter(created__gte=self.since_date).values_list('hash_value', flat=True))
        
    def get_hash(self, message):
        hash_value = hashlib.md5()
        hash_value.update(message)
        return hash_value.hexdigest()        

class ImapConfig(object):
    password = getattr(settings, 'EMAIL_BOX_HOST_PASSWORD', '')
    user = getattr(settings, 'EMAIL_BOX_HOST_USER', '')
    port = getattr(settings, 'EMAIL_BOX_PORT', '')
    host = getattr(settings, 'EMAIL_BOX_HOST', '')
    use_ssl = getattr(settings, 'EMAIL_BOX_USE_SSL', '')
    imap_folders = getattr(settings, 'EMAIL_BOX_IMAP_FOLDER', '')
    
    def __str__(self):
        return '%s - %s - %s' %  (self.user, self.host, self.imap_folders)
    
    
class ImapMailReceiver(BaseMailReceiver):
 
    def __init__(self, config=None, **kwargs):
        super(ImapMailReceiver, self).__init__(**kwargs)
        if config is None:
            self.mb_config = ImapConfig()
        else:
            self.mb_config = config
        
        self.boxes = self.mb_config.imap_folders.split(',')
        self.messages = []
    
    def get_connection(self):
        return self.mb_config
    
    def connect(self):
        mb = self.mb_config
        if mb.use_ssl:
            if not mb.port: mb.port = 993
            self.server = imaplib.IMAP4_SSL(mb.host, int(mb.port))
        else:
            if not mb.port: mb.port = 143
            self.server = imaplib.IMAP4(mb.host, int(mb.port))
            
        self.server.login(mb.user, mb.password)
    
    def disconnect(self):
        try:
            self.server.expunge()
            self.server.close()
        except:
            pass
        self.server.logout()          

    def get_boxes(self):
        return [box for box in self.server.list()[1]]
        
    def fetch_mail(self):
        
        def _quote(box_folder):
            box_folder = box_folder.strip()
            if ' ' in box_folder: box_folder = '"%s"' % box_folder
            return box_folder
        
        super(ImapMailReceiver, self).fetch_mail()
        cnt = 0
        for folder in self.boxes:
            status, count = self.server.select(_quote(folder))
            
            if status != 'OK':
                raise MailRecieverError("Could not select Mailbox '%s'" % folder)
            
            status, email_ids = self.server.uid('search', None, '(SINCE "%s" NOT HEADER Subject "[Django] ERROR (EXTERNAL IP)")' % self.since_date.strftime("%d-%b-%Y"))
            
            if status != 'OK':
                raise MailRecieverError("Could not search Mailbox '%s' (Status: %s)" % (folder, status))
            
            fetch_ids = email_ids[0].split()
            
            if len(fetch_ids) > 0:
                status, alldata = self.server.uid('fetch', ','.join(fetch_ids), '(RFC822)')
                
                # clean up
                alldata = filter(lambda a: a != ')', alldata)
                
                for item in alldata:
                    # is it a valid message (not a flag)
                    if isinstance(item, tuple):
                        msg_uid, full_message = item
                        hash_value = self.get_hash(full_message)
                        if hash_value not in self.old_hash_values:
                            m = self.msg_klass(full_message, hash_value, msg_uid)
                            m.save()
                            self.old_hash_values.append(hash_value)
                            cnt += 1
        return cnt