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
from django.utils.encoding import smart_str, force_unicode
import logging
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from html2text import HTML2Text
from djangojames.string import strip_tags, strip_empty_tags
from djpostman.models import Message
from django.contrib.auth.models import User
from djpostman.utils import get_or_create_contact
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

from_email = getattr(settings, 'FROM_EMAIL', settings.EMAIL_HOST_USER)


def render_to_send_multi_mail(subject, template, context, recipient_list,
                              from_email=from_email, names_dict=None):
    context['current_site'] = Site.objects.get_current()
    context['current_domain'] = getattr(settings, 'PROTOCOL', 'http://') + Site.objects.get_current().domain

    content = render_to_string(template, context)
    return send_multi_mail(subject, content, recipient_list, from_email, names_dict)


def send_multi_mail(subject, content, recipient_list,
                    from_email=from_email,
                    names_dict=None,
                    ignore_celery=False):
    def _add_name_dict(user):
        if not names_dict.get(user.email, None):
            names_dict[user.email] = user.get_full_name()

    if names_dict is None:
        names_dict = {}

    if not isinstance(recipient_list, list):
        recipient_list = [recipient_list]

    if len(recipient_list) == 0:
        return 0

    recipient_list = list(set(recipient_list))

    msg = Message()
    msg.subject = smart_str(subject)
    msg.save()
    for u in User.objects.filter(email=from_email):
        msg.sender = u
        _add_name_dict(u)

    recipient_list_str = []

    for recipient in recipient_list:
        if isinstance(recipient, User):
            msg.recipients.add(recipient)
            _add_name_dict(recipient)

            recipient_list_str.append(recipient.email)
        else:
            for u in User.objects.filter(email=recipient):
                _add_name_dict(u)
                msg.recipients.add(u)
            recipient_list_str.append(recipient)

    h = HTML2Text()
    h.ignore_images = True
    h.ignore_emphasis = True

    recipient_list_str = list(set(recipient_list_str))

    args = [smart_str(subject),
            smart_str(h.handle(force_unicode(strip_empty_tags(strip_tags(content, ['img', 'script', 'span']))))),
            from_email
    ]
    kwargs = {}
    if len(recipient_list_str) > 1:
        kwargs['to'] = [from_email]
        kwargs['bcc'] = recipient_list_str
    else:
        kwargs['to'] = recipient_list_str

    email = EmailMultiAlternatives(*args, **kwargs)
    email.attach_alternative(content, "text/html")

    msg.email = email
    msg.save()
    get_or_create_contact((names_dict.get(from_email), from_email)).emails_sent.add(msg)
    for rec in recipient_list_str:
        get_or_create_contact((names_dict.get(rec), rec)).emails_received.add(msg)

    send(msg, ignore_celery)

    return 1


def send(msg, ignore_celery=False):
    if getattr(settings, 'DJPOSTMAN_NO_EMAIL', False):
        logger.info('No mail sent: settings.DJPOSTMAN_NO_EMAIL is True')
        return 0

    if 'djcelery' in settings.INSTALLED_APPS and hasattr(settings, 'BROKER_URL') and not ignore_celery:
        try:
            send_mail_task.delay(msg.id)
        except:
            logger.exception('Could not use djcelery. Try fallback.')
            send_mail_task(msg.id)
    else:
        send_mail_task(msg.id)