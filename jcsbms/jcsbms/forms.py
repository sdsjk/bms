# coding:utf-8
'''
Created by dengel on 15/11/23.

@author: stone

'''
from django.core.exceptions import ValidationError
from django.forms import CharField
from django.utils.html import strip_tags
from lxml.html.clean import Cleaner
from lxml.html import defs

from jcs.dfa import DFASearch
import logging
logger = logging.getLogger("django")

cleaner = Cleaner()
cleaner.remove_tags=["font"]
cleaner.safe_attrs = defs.safe_attrs | set(['style'])

class RichTextField(CharField):
    def clean(self, value):
        value = super(RichTextField, self).clean(value)
        value = cleaner.clean_html(value)
        return value
    def validate(self, value):
        result = DFASearch.has_banned(strip_tags(value))
        if result != "":
            raise ValidationError(
                u'出现敏感词: %(value)s',
                params={'value': result},
            )