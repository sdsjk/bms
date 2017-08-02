# coding:utf-8
'''
Created by dengel on 15/11/18.

@author: stone

'''

from django import  forms
from django.core.exceptions import ValidationError

from .models import Recharge, Banner, Portal


class RechargeForm(forms.ModelForm):
    gold_number = forms.IntegerField(min_value=1,max_value=10000)
    cost = forms.IntegerField(min_value=1,max_value=10000)
    class Meta:
        model = Recharge
        fields = ["gold_number","cost"]

class BannerForm(forms.ModelForm):

    class Meta:
        model = Banner
        fields = ["img_url","target_id","target_type", "target_url", "project"]

class PortalForm(forms.ModelForm):

    class Meta:
        model = Portal
        fields = ["img_url","name","can_selected", "target_url", "rank", "project",
                  'show_user_flag', 'show_user_value', 'show_channel_flag', 'show_channel_value']

class GiveGoldlForm(forms.Form):
    gold = forms.IntegerField(min_value=1)
    comment = forms.CharField(max_length=255)