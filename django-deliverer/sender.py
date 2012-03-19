# -*- coding: utf-8 -*-
#
# ITerativ GmbH
# http://www.iterativ.ch/
#
# Copyright (c) 2012 ITerativ GmbH. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# Created on Mar 19, 2012
# @author: github.com/maersu

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.utils.encoding import force_unicode
from mailer import send_mail, PRIORITY_MAPPING
from mailer.models import make_message
import logging
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from html2text import HTML2Text
from djangojames.string import strip_tags, strip_empty_tags

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
                    priority="medium"):

    context['current_site'] = Site.objects.get_current()
    context['current_domain'] = settings.PROTOCOL+Site.objects.get_current().domain
        
    content = render_to_string(template, context)
    return send_multi_mail(subject, content, recipient_list, from_email, priority)

def send_multi_mail(subject, content, recipient_list, 
                    from_email=settings.EMAIL_HOST_USER, 
                    priority="medium"):

    if not isinstance(recipient_list, list): 
        recipient_list = [recipient_list]
            
    priority = PRIORITY_MAPPING[priority]
    
    h = HTML2Text()
    h.ignore_images = True
    h.ignore_emphasis = True
        
    msg = make_message(subject=force_unicode(subject),
                       body=force_unicode(h.handle(strip_empty_tags(strip_tags(content, ['img', 'script', 'span'])))),
                       from_email=from_email,
                       to=recipient_list,
                       priority=priority)
    email = msg.email
    email = EmailMultiAlternatives(email.subject, email.body, email.from_email, email.to)
    email.attach_alternative(content, "text/html")

    msg.email = email
    msg.save()
    email.send()
    return 1