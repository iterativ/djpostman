# -*- coding: utf-8 -*-
#
# ITerativ GmbH
# http://www.iterativ.ch/
#
# Copyright (c) 2012 ITerativ GmbH. All rights reserved.
#
# Created on May 7, 2012
# @author: maersu <me@maersu.ch>

from djpostman.receiver import ImapMailReceiver
from django.core.management.base import BaseCommand

class Command(BaseCommand):

    help = ''

    def handle(self, *args, **options):
        mr = ImapMailReceiver()
        count = mr.fetch_mail()
        
        print '\n%s mails fetched' % count

