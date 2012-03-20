# -*- coding: utf-8 -*-

from django.contrib import admin
from djpostman.models import Message

class MessageAdmin(admin.ModelAdmin):
    list_display = ('created', 'subject')
    change_form_template = 'admin/change_message_form.html'
    
admin.site.register(Message, MessageAdmin)