# -*- coding: utf-8 -*-
#
# ITerativ GmbH
# http://www.iterativ.ch/
#
# Copyright (c) 2012 ITerativ GmbH. All rights reserved.
#
# Created on Mar 19, 2012
# @author: github.com/maersu

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import TimeStampedModel
import base64
import pickle
from datetime import date
from django.conf import settings

def _pickle_email(email):
    return base64.encodestring(pickle.dumps(email))

def _unpickle_email(data):
    return pickle.loads(base64.decodestring(data))

class Contact(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    first_name = models.CharField(_('Vorname'), max_length=100, blank=True)
    last_name = models.CharField(_('Nachname'), max_length=100, blank=True)
    email = models.EmailField(_('Email Addresse'), blank=True, unique=True)
    emails_sent = models.ManyToManyField('djpostman.Message', related_name='contact_emails_sent')
    emails_received = models.ManyToManyField('djpostman.Message', related_name='contact_emails_received')

    def __unicode__(self):
        return '%s %s %s' %  (self.email, self.first_name, self.last_name)

    def emails_sent_count(self):
        return self.emails_sent.count() 

    def emails_received_count(self):
        return self.emails_received.count()

class Message(TimeStampedModel):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='user_messages', null=True, blank=True)
    subject= models.TextField()
    hash_value = models.CharField(max_length=255, null=True, blank=True, editable=False)
    uid = models.CharField(max_length=255, null=True, blank=True, editable=False)
    # The actual data - a pickled EmailMessage
    message_data = models.TextField(null=True, blank=True, editable=False)
    sent = models.BooleanField(_(u"Mail wurde gesendet"), default=False)
    
    class Meta(object):
        verbose_name = _('Email')
        verbose_name_plural = _("Emails")
        ordering = ['-created']
    
    def _get_email(self):
        try:
            return _unpickle_email(self.message_data)
        except:
            return '(email not readable)'
    
    def _set_email(self, val):
        self.message_data = _pickle_email(val)

    email = property(_get_email, _set_email)
    
    def __unicode__(self):
        return '%s' %  self.subject

class EmailBox(TimeStampedModel):
    host = models.CharField(max_length=255, help_text=_(u'Beispiel: imap.googlemail.com'))
    user = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    port = models.IntegerField(default=993)
    use_ssl = models.BooleanField(default=True)
    imap_folders = models.TextField(help_text=_(u'Ordner für die Synchronisation (kommasepariert)'))
    last_sync = models.DateField(help_text=_(u'Datum der letzten Synchronisation'), blank=True, null=True)
    boxes = models.TextField(help_text=_(u'Liste aller Order (dient nur zu Informationszwecken und hat keine Funktion)'), blank=True, null=True)
    
    class Meta(object):
        verbose_name = _('Email Box')
        verbose_name_plural = _("Email Boxen")
        ordering = ['-created']
        
    def __unicode__(self):
        return '%s - %s - %s' %  (self.user, self.host, self.imap_folders)
    
    def synchronize(self):
        from djpostman.receiver import ImapMailReceiver
        
        if self.last_sync:
            since_date = self.last_sync
        else:
            since_date = date(2000, 1, 1)
        
        mr = ImapMailReceiver(config=self, since_date=since_date)
        mr.connect()
        self.boxes = '\n'.join(mr.get_boxes())
        count = mr.fetch_mail()
        mr.disconnect()
        self.last_sync = date.today()
        self.save()
        
        return count


