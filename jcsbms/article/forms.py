# coding:utf-8
'''
Created by dengel on 15/11/23.

@author: stone

'''
import re

from django import  forms
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

from jcs.dfa import DFASearch
from .models import Article
from analyst.models import AnalystPriceRange

from jcsbms.forms import RichTextField


class ResultForm(forms.Form):
    title = forms.CharField(max_length=100)
    text = RichTextField()

class ArticleSyncForm(forms.ModelForm):
    text =  RichTextField()
    class Meta:
        model = Article
        fields = ["taskid","title","text"]

class ArticleForm(forms.ModelForm):
    text = RichTextField()

    class Meta:
        model = Article
        fields = ["title","text"]
class ChargeableAnalystArticleForm(forms.ModelForm):
    text = RichTextField()
    chargeable = forms.BooleanField(required=False)
    digest = forms.CharField(max_length=300,required=False)
    price = forms.IntegerField(required=False)

    def clean_digest(self):
        charge = self.cleaned_data['chargeable']
        if charge != None and charge ==True:
            result = DFASearch.has_banned(strip_tags(self.cleaned_data['digest'])).encode("utf-8")
            if result != "":
                raise ValidationError(
                    u'摘要出现敏感词: %(value)s',
                    params={'value': result.decode("utf-8")},
                )
            if self.cleaned_data['digest']==None or len(self.cleaned_data['digest'])==0:
                raise ValidationError(u'收费文章必须得有摘要')
            return self.cleaned_data['digest']
        else:
            if "text" in self.cleaned_data:#for text validate error
                return strip_tags(self.cleaned_data['text'])[:100]

    def clean_text(self):
        if self.instance.id == None:
            article = Article.objects.filter(author=self.instance.author).order_by("id").last()
            if  article !=None and article.text == self.cleaned_data["text"]:
                raise ValidationError(u'本文内容和您前一篇文章内容完全重复')
        return self.cleaned_data["text"]
    
    def clean_price(self):
        price = self.cleaned_data["price"]
        if price < 1:
            price = None

        try:
            price_range = AnalystPriceRange.objects.get(analyst=self.instance.author, status=AnalystPriceRange.VALID_STATUS)
            if price < price_range.low_price or price > price_range.high_price:
                raise ValidationError( u"文章定价超出了定价区间!")
        except AnalystPriceRange.DoesNotExist:
            pass
        return price

    class Meta:
        model = Article
        fields = ["text","chargeable","digest", "price"]

class FreeAnalystArticleForm(forms.ModelForm):
    text = RichTextField()
    digest = forms.CharField(max_length=300,required=False)

    def clean_digest(self):
        #如果text未通过敏感词检查, self.cleaned_data["text"]不存在
        if "text" in self.cleaned_data:
            return strip_tags(self.cleaned_data['text'])[:100]
        return ""

    def clean_text(self):
        if self.instance.id == None:
            article = Article.objects.filter(author=self.instance.author).order_by("id").last()
            if article !=None and article.text == self.cleaned_data["text"]:
                raise ValidationError(u'本文内容和您前一篇文章内容完全重复')
        return self.cleaned_data["text"]
    class Meta:
        model = Article
        fields = ["text","digest"]
class ModifyAnalystArticleForm(forms.ModelForm):
    text = RichTextField()
    digest = forms.CharField(max_length=300,required=False)


    def clean_digest(self):
        if self.instance.chargeable == True:
            result = DFASearch.has_banned(strip_tags(self.cleaned_data['digest']))
            if result != "":
                raise ValidationError(
                    u'摘要出现敏感词: %(value)s',
                    params={'value': result},
                )
            if self.cleaned_data['digest'] == None or len(self.cleaned_data['digest']) == 0:
                raise ValidationError(u'收费文章必须得有摘要')
            return self.cleaned_data['digest']
        else:
            if "text" in self.cleaned_data:  # for text validate error
                return strip_tags(self.cleaned_data['text'])[:100]
    class Meta:
        model = Article
        fields = ["text","digest"]




