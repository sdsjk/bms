#-*- coding:utf-8 -*-

'''
author: zhaozhi
date: 2016-07-22 19:30
'''
from article.models import Article
from jcs.models import JcsAction

class DelArticle(JcsAction):
    action = "del_article"
    target_model = Article
    description = "删除文章"

class RestoreArticle(JcsAction):
    action = "restore_article"
    target_model = Article
    description = "恢复文章"