# -*- coding: utf-8 -*-
#
# ITerativ GmbH
# http://www.iterativ.ch/
#
# Copyright (c) 2012 ITerativ GmbH. All rights reserved.
#
# Created on May 8, 2012
# @author: maersu <me@maersu.ch>

from celery.task import task
from djpostman.receiver import ImapMailReceiver
import logging
from djpostman.models import Message
logger = logging.getLogger(__name__)

@task
def send_mail_task(msg_id):
    try:
        msg = Message.objects.get(id=msg_id)
        msg.email.send()
        msg.sent = True
        msg.save()
    except:
        logger.exception('could not send email')

@task(name="djpostman.fetch_mails")
def backend_cleanup():
    mr = ImapMailReceiver()
    mr.fetch_mail()
