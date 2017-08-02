# coding:utf-8
'''
Created by dengel on 15/11/23.

@author: stone

'''
from django import  forms
from .models import Bulletin,Letter
from jcsbms.forms import RichTextField
from django.utils.html import strip_tags

class BulletinForm(forms.ModelForm):
    text =  RichTextField()
    class Meta:
        model = Bulletin
        fields = ["title","text"]

class LetterForm(forms.ModelForm):
    content = RichTextField()

    def clean_content(self):
        c = strip_tags(self.cleaned_data["content"])
        return c

    class Meta:
        model = Letter
        fields = ["to_auser","content","project"]

#小秘书不检查
class XiaoMiShuLetterForm(forms.ModelForm):

    class Meta:
        model = Letter
        fields = ["to_auser","content"]



#小秘书不检查
class XiaoMiShuNormalForm(forms.ModelForm):

    class Meta:
        model = Letter
        fields = ["to_auser","content","project"]



