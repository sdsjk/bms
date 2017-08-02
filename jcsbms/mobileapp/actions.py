#-*- coding:utf-8 -*-

'''
author: zhaozhi
date: 2016-10-09 15:34
'''

from jcs.models import JcsAction
from article.models import Article

class RefundRed(JcsAction):
    action = "refund_red"
    target_model = Article
    description = "红单退款"