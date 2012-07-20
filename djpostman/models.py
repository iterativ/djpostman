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

def _pickle_email(email):
    return base64.encodestring(pickle.dumps(email))

def _unpickle_email(data):
    return pickle.loads(base64.decodestring(data))

class Message(TimeStampedModel):
    
    sender = models.ForeignKey('auth.User', null=True, blank=True)
    recipients = models.ManyToManyField('auth.User', related_name='user_messages', null=True, blank=True)
    
    subject= models.TextField()
    hash_value = models.CharField(max_length=255, null=True, blank=True, editable=False)
    
    # The actual data - a pickled EmailMessage
    message_data = models.TextField(null=True, blank=True, editable=False)

    class Meta(object):
        verbose_name = _('Email')
        verbose_name_plural = _("Emails")
        ordering = ['-created']
    
    def _get_email(self):
        return _unpickle_email(self.message_data)
    
    def _set_email(self, val):
        self.message_data = _pickle_email(val)

    email = property(_get_email, _set_email)
    
    def __unicode__(self):
        return '%s' %  self.subject
    
