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


@task
def send_mail_task(msq):
    msq.send()
    
@task(name="djpostman.fetch_mails")
def backend_cleanup():
    mr = ImapMailReceiver()
    mr.fetch_mail()
