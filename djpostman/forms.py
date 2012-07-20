# -*- coding: utf-8 -*-
#
# ITerativ GmbH
# http://www.iterativ.ch/
#
# Copyright (c) 2012 ITerativ GmbH. All rights reserved.
#
# Created on Jul 19, 2012
# @author: maersu <me@maersu.ch>

from django import forms
from django.utils.translation import ugettext_lazy as _
from djangojames.forms.base import BaseModelForm
from djpostman.models import Message
from django.core.validators import validate_email

TEXTILE_HELP = _(u'Du kannst den Text mit Hilfe von <a href="http://en.wikipedia.org/wiki/Textile_%28markup_language%29" target="_blank">Textile</a> formatieren')

class MessageForm(BaseModelForm):
    recipients_email = forms.CharField(label=_('Email Adressen'), 
                                       required=False, 
                                       help_text=_(u'E-Mail-Adressen weiterer Empfänger (kommasepariert)'),
                                       widget=forms.TextInput(attrs={'size': 60}))
    subject = forms.CharField(widget=forms.TextInput(attrs={'size': 60}))
    text = forms.CharField(widget=forms.Textarea(attrs={'cols': 60, "rows": 15}), 
                           help_text=TEXTILE_HELP)
    use_greeting = forms.BooleanField(label=_('Grussformel'), 
                                      required=False, 
                                      initial=True,
                                      help_text=_(u"Standart Grussformel verwenden"))
    
    def clean_recipients_email(self):
        data = self.cleaned_data['recipients_email'].strip()
        mails = []
        
        if len(data):
            try:
                for e in data.split(','):
                    e = e.strip()
                    validate_email(e)
                    mails.append(e)
            except:
                raise forms.ValidationError(u"Ungültige Adresse(n)")
    
        return mails
    
    class Meta:
        model = Message
        fields = (
            'recipients',
            'subject',
        )