# -*- coding: utf-8 -*-
#
# ITerativ GmbH
# http://www.iterativ.ch/
#
# Copyright (c) 2012 ITerativ GmbH. All rights reserved.
#
# Created on Oct 9, 2012
# @author: maersu <me@maersu.ch>

from djpostman.models import Contact
from django.contrib.auth.models import User
from email.Utils import parseaddr

def extract_name(email):
    name, email = parseaddr(email)
    if not name:   
        part = email.split('@')[0].lower()
        if part.find('.') >= 0 and not 'info' in part and not 'office' in part and not 'webmaster' in part and not 'admin' in part:
            new_names = []
            for n in part.replace('.', ' ').title().split(' '):
                if len(n) == 1:
                    new_names.append(n+'.')
                else:
                    new_names.append(n)
                    
            return ' '.join(new_names)
    else:
        return name.title()
        
def get_or_create_contact(contact_email):
    name, email = contact_email
    email=email.lower()
    names = []
    defaults={}
    if not name:
        name = extract_name(email)
    if name:
        names = name.split(' ')
    
    _name, email = parseaddr(email)
    
    if len(names) > 1:
        defaults['first_name'] = names[0]
        defaults['last_name'] = ' '.join(names[1:])
    
    try:
        contact = Contact.objects.get(email__iexact=email)
    except Contact.DoesNotExist:
        contact = Contact(email=email)
        contact.save()
    
    if not contact.user and User.objects.filter(email__iexact=email).exists():
        contact.user = User.objects.filter(email__iexact=email)[0]
        contact.save()
    
    if not contact.first_name and 'first_name' in defaults:
        contact.first_name = defaults.get('first_name')[:100]
    if not contact.last_name and 'last_name' in defaults:
        contact.last_name = defaults.get('last_name')[:100]
    contact.save()

    return contact    
