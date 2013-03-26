# -*- coding: utf-8 -*-
#
# ITerativ GmbH
# http://www.iterativ.ch/
#
# Copyright (c) 2012 ITerativ GmbH. All rights reserved.
#

from django.contrib import admin
from djpostman.models import Message, EmailBox, Contact
from django.template.response import TemplateResponse
from django.conf.urls.defaults import *
from djpostman.forms import MessageForm
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
import re
import logging
from djpostman.sender import send
logger = logging.getLogger(__name__)

def sync_box(modeladmin, request, queryset):
    count = 0
    try:
        for config in queryset.all():
            count += config.synchronize()            
        messages.success(request, _(u"%s Emails synchronisiert") % count)
    except Exception, e:
        logger.exception('Could not sync Email')
        messages.error(request, _(u"Emails konnten nicht synchronisiert werden: %s") % str(e))
    
sync_box.short_description = _(u"Ausgewählte Email Boxen synchronisieren")

class EmailBoxAdmin(admin.ModelAdmin):
    list_display = ('user', 'host', 'imap_folders', 'last_sync')
    actions = [sync_box]
    
admin.site.register(EmailBox, EmailBoxAdmin)

class ContactAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user', 'emails_sent_count', 'emails_received_count', 'created')
    search_fields = ('email', 'first_name', 'last_name', 'user__first_name', 'user__first_name')
    
admin.site.register(Contact, ContactAdmin)

def resend(modeladmin, request, queryset):
    try:
        for msg in queryset:
            send(msg)
        messages.success(request, _(u"%s Emails gesendet") % len(queryset))
    except Exception, e:
        logger.exception('Could not resend email')
        messages.error(request, _(u"Emails konnten nicht gesendet werden: %s") % str(e))
resend.short_description = _(u"Ausgewählte Emails nocheinmal senden")

content_re = re.compile("<body>(?P<content>.*)</body>",re.IGNORECASE|re.MULTILINE|re.DOTALL)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('created', 'subject', 'uid', 'sent')
    search_fields = ('subject', 'uid')
    list_filter = ('sent',)
    actions = [resend]
    
    change_form_template = 'admin/djpostman/message_change_form.html'
    change_list_template = 'admin/djpostman/message_change_list.html'

    def get_urls(self):
        urls = super(MessageAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^send/$', self.sendmail, name="sendmail")
        )
        return my_urls + urls

    def change_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}
    
        obj = self.get_object(request, object_id)
        
        alternatives = []
        for text, t in obj.email.alternatives:

            match = content_re.search(text)
            if match:
                text = match.group("content")
            alternatives.append(text)
        
        extra_context['alternatives'] = alternatives
        
        return super(MessageAdmin, self).change_view(request, object_id,
                                                     extra_context=extra_context)

    def sendmail(self, request, form_url=None, extra_content=None):
        if request.method == 'POST':
            form = MessageForm(request.POST)
            if form.is_valid():
                from djpostman.sender import render_to_send_multi_mail
                recipient_list=form.cleaned_data['recipients_email'] + [u.email for u in form.cleaned_data['recipients']]
                subject = form.cleaned_data['subject']
                
                render_to_send_multi_mail(subject=subject,
                                          template='mail/manual_mail.html',
                                          context={'text': form.cleaned_data['text'],
                                                   'use_greeting': form.cleaned_data['use_greeting'],
                                                   'user': request.user.get_full_name() or request.user},
                                          recipient_list=recipient_list)
                
                messages.success(request, _(u"Das Email '%s' wurde an '%s' versendet") % (subject, ','.join(recipient_list)))
                return redirect('admin:djpostman_message_changelist')
        else:
            form = MessageForm()
        return TemplateResponse(request, 'admin/djpostman/sendmail_form.html', {'form': form})

admin.site.register(Message, MessageAdmin)
