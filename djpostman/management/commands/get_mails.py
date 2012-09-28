# -*- coding: utf-8 -*-
#
# ITerativ GmbH
# http://www.iterativ.ch/
#
# Copyright (c) 2012 ITerativ GmbH. All rights reserved.
#
# Created on May 7, 2012
# @author: maersu <me@maersu.ch>
from django.core.management.base import NoArgsCommand
from optparse import make_option

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--reset', '-r', action='store_true',
            help='reset last sync'),     
        make_option('--delete', '-d', action='store_true',
            help='delete all messages in db'),               
    )

    def handle_noargs(self, **options):
        from djpostman.models import EmailBox, Message, Contact
        from djpostman.receiver import ImapMailReceiver
        
        try:
            mr = ImapMailReceiver()
            print 'IMAP Sync: %s' % mr.get_connection()
            mr.connect()
            count = mr.fetch_mail()
            mr.disconnect()
            print '%s mails fetched' % count
        except Exception, e:
            print 'ERROR: %s' % str(e)
        
        
        if options.get('reset', False):
            print 'reset last sync'
            EmailBox.objects.update(last_sync=None)
        if options.get('delete', False):
            print 'delete all data'
            Message.objects.all().delete()
            Contact.objects.all().delete()
        
        for box in EmailBox.objects.all():
            try:
                print 'IMAP Sync: %s' % box
                print '%s mails fetched' % box.synchronize()
            except Exception, e:
                raise
                print 'ERROR: %s' % str(e)
        
        

