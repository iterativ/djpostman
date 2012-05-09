# -*- coding: utf-8 -*-
#
# ITerativ GmbH
# http://www.iterativ.ch/
#
# Copyright (c) 2012 ITerativ GmbH. All rights reserved.
#

from django.contrib import admin
from djpostman.models import Message

class MessageAdmin(admin.ModelAdmin):
    list_display = ('created', 'subject')
    change_form_template = 'admin/change_message_form.html'
    
admin.site.register(Message, MessageAdmin)