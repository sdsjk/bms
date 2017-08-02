# coding:utf-8
'''
Created by dengel on 15/11/18.

@author: stone

'''
import re

from django import  forms
from django.core.exceptions import ValidationError

from .models import Analyst,Priceplan,Apply, AnalystGroup, LivePriceplan


class AnalystForm(forms.ModelForm):
    class Meta:
        model = Analyst
        fields = ["analyst_type","nick_name","brief","lottery_type","level",
                  "answer_level","analyst_group", "is_mandarin_perm", "is_cantonese_perm"]
        # fields = ["analyst_type", "nick_name", "lottery_type", "level",
        #           "answer_level", "analyst_group", "is_mandarin_perm", "is_cantonese_perm"]

class UsernameForm(forms.Form):
    username = forms.CharField(required=True,max_length=32)
    email = forms.EmailField()

    def clean_username(self):
        if len(self.cleaned_data['username'])<6:
            raise ValidationError(u"用户名字数必须大于6")
        if len(self.cleaned_data['username'])>30:
            raise ValidationError(u"用户名字数最多为30")
        # if not re.match('^[a-zA-Z][a-zA-Z0-9_]+$', self.cleaned_data['username']):
        #     raise forms.ValidationError(u"用户名只能包括字母数字或下划线且必须以字母开头")
        return self.cleaned_data['username'].lower()

class AnalystinfoForm(forms.ModelForm):
    class Meta:
        model = Analyst
        fields = ["real_name","id_number","bank_branch","card_number","weichat",
                  "mobile","address","post_code"]

class ActivateAnalystForm(forms.Form):
    username = forms.CharField(min_length=6,max_length=30)
    mobile = forms.CharField(max_length=11,min_length=11,required=False)
    email = forms.EmailField()
    analyst_type = forms.IntegerField()

    def clean_username(self):
        if len(self.cleaned_data['username'])<6:
            raise ValidationError(u"用户名字数必须大于6")
        if len(self.cleaned_data['username'])>30:
            raise ValidationError(u"用户名字数最多为30")
        if not re.match('^[a-zA-Z][a-zA-Z0-9_]+$', self.cleaned_data['username']):
            raise forms.ValidationError(u"用户名只能包括字母数字或下划线且必须以字母开头")
        return self.cleaned_data['username'].lower()

    def clean_mobile_number(self):
        pattern = re.compile("^1([358][0-9]|45|47)[0-9]{8}$")
        if not pattern.match(self.cleaned_data['mobile']):
            raise ValidationError(u'手机号码数据格式错误！')
        else:
            return self.cleaned_data['mobile']

class PriceplanForm(forms.ModelForm):
    cost = forms.IntegerField(min_value=1,max_value=1000)
    class Meta:
        model = Priceplan
        fields = ["cost"]

class ApplyResultForm(forms.ModelForm):
    handle_result = forms.CharField(min_length=2,max_length=100)
    class Meta:
        model = Apply
        fields = ["handle_result"]

class AnalystGroupForm(forms.ModelForm):
    class Meta:
        model = AnalystGroup
        fields = ["level_number","name"]

class LivePriceplanForm(forms.ModelForm):

    class Meta:
        model = LivePriceplan
        fields = ["days","cost","period_name"]