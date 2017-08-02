#-*- coding:utf-8 -*-

'''
author: zhaozhi
date: 2016-07-22 19:30
'''

from jcs.models import JcsAction
from models import Letter

class DelLetter(JcsAction):
    action = "del_letter"
    target_model = Letter
    description = "未审核私信"

class RestoreLetter(JcsAction):
    action = "restore_letter"
    target_model = Letter
    description = "审核私信"