# -*- coding: utf-8 -*-
#
# ITerativ GmbH
# http://www.iterativ.ch/
#
# Copyright (c) 2012 ITerativ GmbH. All rights reserved.
#

from django.contrib import admin
from djpostman.models import Message
from django.template.response import TemplateResponse
from django.conf.urls.defaults import *
from djpostman.forms import MessageForm
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

class MessageAdmin(admin.ModelAdmin):
    list_display = ('created', 'subject')
    change_form_template = 'admin/change_message_form.html'

    def get_urls(self):
        urls = super(MessageAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^send/$', self.sendmail, name="sendmail")
        )
        return my_urls + urls

    def sendmail(self, request, form_url=None, extra_content=None):
        if request.method == 'POST':
            form = MessageForm(request.POST)
            if form.is_valid():
                from djpostman.sender import send_multi_mail
                recipient_list=form.cleaned_data['recipients_email'] + [u.email for u in form.cleaned_data['recipients']]
                subject = form.cleaned_data['subject']
                
                send_multi_mail(subject=subject,
                                content=form.cleaned_data['text'],
                                recipient_list=recipient_list)
                
                messages.success(request, _(u"Das Email '%s' wurde an '%s' versendet" % (subject, ','.join(recipient_list))))
                return redirect('/admin/djpostman/message/send/')
        else:
            form = MessageForm()
        return TemplateResponse(request, 'admin/sendmail.html', {'form': form})

admin.site.register(Message, MessageAdmin)