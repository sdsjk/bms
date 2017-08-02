#-*- coding:utf-8 -*-
'''
author: zhaozhi
date: 2016-07-22 18:30
'''
from jcs.models import JcsAction
from models import Analyst, AnalystPriceRange

class BanFree(JcsAction):
    action = "ban_free"
    target_model = Analyst
    description = u"禁止发国语免费消息"

class BanLetter(JcsAction):
    action = "ban_letter"
    target_model = Analyst
    description = u"禁止发私信"

class BanChargeable(JcsAction):
    action = "ban_chargeable"
    target_model = Analyst
    description = u"禁止发国语收费消息"

class ChangePriceRange(JcsAction):
    action = "change_price_range"
    target_model = AnalystPriceRange
    description = u"修改定价区间"

class BanFreeCantonese(JcsAction):
    action = "ban_free_cantonese"
    target_model = Analyst
    description = u"禁止发粤语免费消息"

class BanChargeableCantonese(JcsAction):
    action = "ban_chargeable_cantonese"
    target_model = Analyst
    description = u"禁止发粤语收费消息"

class CanFree(JcsAction):
    action = "can_free"
    target_model = Analyst
    description = u"允许发国语免费消息"

class CanLetter(JcsAction):
    action = "can_letter"
    target_model = Analyst
    description = u"允许发私信"

class CanChargeable(JcsAction):
    action = "can_chargeable"
    target_model = Analyst
    description = u"允许发国语收费消息"

class CanFreeCantonese(JcsAction):
    action = "can_free_cantonese"
    target_model = Analyst
    description = u"允许发粤语免费消息"

class CanChargeableCantonese(JcsAction):
    action = "can_chargeable_cantonese"
    target_model = Analyst
    description = u"允许发粤语收费消息"
