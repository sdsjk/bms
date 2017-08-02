# coding:utf-8
'''
Created by dengel on 15/11/23.

@author: stone

'''
import re

from django import  forms
from .models import  Reply
from jcsbms.forms import RichTextField



class ReplyForm(forms.ModelForm):
    content = forms.CharField(min_length=10,max_length=1000)
    class Meta:
        model = Reply
        fields = ["content"]







