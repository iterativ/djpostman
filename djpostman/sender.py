# -*- coding: utf-8 -*-
#
# ITerativ GmbH
# http://www.iterativ.ch/
#
# Copyright (c) 2012 ITerativ GmbH. All rights reserved.
#
# Created on Mar 19, 2012
# @author: github.com/maersu

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.encoding import force_unicode
import logging
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from html2text import HTML2Text
from djangojames.string import strip_tags, strip_empty_tags
from djpostman.models import Message
from django.contrib.auth.models import User
from djpostman.task import send_mail_task

logger = logging.getLogger(__name__)

# @todo add attachment 
# http://djangosnippets.org/snippets/1063/

# attach_file() creates a new attachment using a file from your filesystem.
# Call it with the path of the file to attach and, optionally, the MIME type 
# to use for the attachment. If the MIME type is omitted, it will be guessed from the filename. 
# The simplest use would be:
#
# message.attach_file('/images/weather_map.png')

def render_to_send_multi_mail(subject, template, context, recipient_list, 
                    from_email=settings.EMAIL_HOST_USER, 
                    store=True):

    context['current_site'] = Site.objects.get_current()
    context['current_domain'] = getattr(settings, 'PROTOCOL', 'http://')+Site.objects.get_current().domain
        
    content = render_to_string(template, context)
    return send_multi_mail(subject, content, recipient_list, from_email, store)

def send_multi_mail(subject, content, recipient_list, 
                    from_email=settings.EMAIL_HOST_USER, 
                    store=True):

    if not isinstance(recipient_list, list): 
        recipient_list = [recipient_list]
    
    if len(recipient_list) == 0:
        return 0
        
    if store:
        msg = Message()
        msg.subject = force_unicode(subject)
        msg.save()

    # any user?
    recipient_list_str = []
    
    for recipient in recipient_list:
        if isinstance(recipient, User):
            if store: msg.recipients.add(recipient)
            recipient_list_str.append(recipient.email)
        else:
            recipient_list_str.append(recipient)
    
    h = HTML2Text()
    h.ignore_images = True
    h.ignore_emphasis = True
    
    email = EmailMultiAlternatives(force_unicode(subject), 
                                   force_unicode(h.handle(strip_empty_tags(strip_tags(content, ['img', 'script', 'span'])))), 
                                   from_email, 
                                   recipient_list_str)
    email.attach_alternative(content, "text/html")
    if store: 
        msg.email = email
        msg.save()
    
    if 'djcelery' in settings.INSTALLED_APPS:
        send_mail_task.delay(email)
    else:
        send_mail_task(email)
    
    return 1