# coding:utf-8
'''
Created by dengel on 15/11/17.

@author: stone

'''

from django import  forms

class LoginForm(forms.Form):
    username = forms.CharField(max_length=32)
    password = forms.CharField(max_length=32)